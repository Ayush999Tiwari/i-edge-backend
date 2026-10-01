# ==========================================================
# Home Surveillance API
# ==========================================================

import os
import traceback
from typing import Optional
import uuid

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    BackgroundTasks,
    HTTPException,
    Depends,
    Header,
)

from fastapi.responses import (
    StreamingResponse,
    FileResponse,
)

from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.models import User
from app.core.security import decode_access_token
from app.services import surveillance_service


router = APIRouter(
    prefix="/api/surveillance",
    tags=["Home Surveillance"],
)

legacy_router = APIRouter()


# ==========================================================
# Authentication
# ==========================================================

def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Resolve the currently authenticated application user
    from the Bearer JWT.
    """

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header required",
        )

    parts = authorization.strip().split(" ", 1)

    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header",
        )

    token = parts[1].strip()

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Missing access token",
        )

    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")

    if user_id is None:
        user_id = payload.get("user_id")

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token",
        )

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid user identity",
        )

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    return user


# ==========================================================
# Image helper
# ==========================================================

async def _read_image(
    file: UploadFile,
) -> bytes:

    data = await file.read()

    if not data:
        raise HTTPException(
            status_code=400,
            detail="Empty file",
        )

    return data


# ==========================================================
# Upload video
# ==========================================================

@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:

        save_path = (
            surveillance_service.save_uploaded_video(
                file.filename,
                file.file,
            )
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    # Create the surveillance job.
    job = surveillance_service.create_video_job(
        db,
        file.filename,
        save_path,
    )

    # Recipient comes from the authenticated backend user.
    #
    # The frontend does NOT send the recipient email.
    # Therefore users cannot change another user's alert address.
    job.alert_email = current_user.email
    job.email_alerts_sent = 0

    db.commit()
    db.refresh(job)

    return {
        "id": job.id,
        "status": job.status,
        "alert_email": current_user.email,
    }


# ==========================================================
# Background pipeline
# ==========================================================

def _run_video_pipeline_task(
    job_id: int,
    video_path: str,
):
    """
    Background task gets its own database session.
    """

    db = SessionLocal()

    try:

        surveillance_service.run_video_pipeline(
            db,
            job_id,
            video_path,
        )

    except Exception:

        traceback.print_exc()

    finally:

        db.close()


# ==========================================================
# Start detection
# ==========================================================

@router.post("/detect/{job_id}")
async def run_detection(
    job_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    job = surveillance_service.get_video_job(
        db,
        job_id,
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    # Make sure the job belongs to the currently
    # authenticated email.
    if (
        job.alert_email
        and current_user.email
        and job.alert_email != current_user.email
    ):
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this job",
        )

    if job.status == "processing":

        raise HTTPException(
            status_code=409,
            detail="Detection already running for this job",
        )

    # If the account has no email, detection can still run.
    # Email alerts will simply be skipped by the service.
    if not current_user.email:
        print(
            "[EMAIL] Current user has no email address. "
            "Detection will continue without email alerts."
        )

    # In case the job was created before the email field
    # was populated.
    job.alert_email = current_user.email

    db.commit()

    background_tasks.add_task(
        _run_video_pipeline_task,
        job_id,
        job.input_path,
    )

    return {
        "id": job.id,
        "status": "processing",
        "alert_email": current_user.email,
    }


# ==========================================================
# Results
# ==========================================================

@router.get("/results")
async def get_results(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    jobs = surveillance_service.get_all_video_jobs(
        db
    )

    # Only return jobs belonging to this user.
    jobs = [
        j
        for j in jobs
        if (
            not j.alert_email
            or j.alert_email == current_user.email
        )
    ]

    return [
        {
            "id": j.id,
            "original_filename": j.original_filename,
            "status": j.status,

            "fire_detected": j.fire_detected,
            "fire_events": j.fire_events,
            "max_fire_confidence": j.max_fire_confidence,

            "crowd_detected": j.crowd_detected,
            "crowd_events": j.crowd_events,
            "max_person_count": j.max_person_count,

            "violence_detected": j.violence_detected,
            "violence_events": j.violence_events,
            "max_violence_confidence": (
                j.max_violence_confidence
            ),

            "alert_email": j.alert_email,
            "email_alerts_sent": (
                j.email_alerts_sent or 0
            ),

            "created_at": j.created_at,
            "error_message": j.error_message,
        }
        for j in jobs
    ]


# ==========================================================
# Job status
# ==========================================================

@router.get("/status/{job_id}")
async def get_job_status(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    job = surveillance_service.get_video_job(
        db,
        job_id,
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    # Protect another user's job.
    if (
        job.alert_email
        and current_user.email
        and job.alert_email != current_user.email
    ):
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this job",
        )

    return {
        "id": job.id,
        "status": job.status,
        "error_message": job.error_message,

        "alert_email": job.alert_email,

        "email_alerts_sent": (
            job.email_alerts_sent or 0
        ),

        "fire_detected": job.fire_detected,
        "crowd_detected": job.crowd_detected,
        "violence_detected": job.violence_detected,
    }


# ==========================================================
# Processed video
# ==========================================================

@router.get("/video/{job_id}")
async def get_processed_video(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    job = surveillance_service.get_video_job(
        db,
        job_id,
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    if (
        job.alert_email
        and current_user.email
        and job.alert_email != current_user.email
    ):
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this job",
        )

    if (
        not job.output_path
        or not os.path.exists(job.output_path)
    ):
        raise HTTPException(
            status_code=404,
            detail="Processed video unavailable",
        )

    return FileResponse(
        job.output_path,
        media_type="video/mp4",
        filename=os.path.basename(
            job.output_path
        ),
    )


# ==========================================================
# Single-image endpoints
# ==========================================================

@router.post("/fire")
async def detect_fire(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    try:

        image_bytes = await _read_image(file)

        detections = (
            surveillance_service.analyze_fire(
                db,
                image_bytes,
            )
        )

        return {
            "fire_detected": len(detections) > 0,
            "detections": detections,
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except Exception as e:

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.post("/crowd")
async def detect_crowd_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    try:

        image_bytes = await _read_image(file)

        return surveillance_service.analyze_crowd(
            db,
            image_bytes,
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except Exception as e:

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.post("/violence")
async def detect_violence(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    try:

        image_bytes = await _read_image(file)

        return surveillance_service.analyze_violence(
            db,
            image_bytes,
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except Exception as e:

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.post("/person")
async def detect_person(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    try:

        image_bytes = await _read_image(file)

        detections = (
            surveillance_service.analyze_person(
                db,
                image_bytes,
            )
        )

        return {
            "person_count": sum(
                1
                for d in detections
                if d["class"] == "person"
            ),
            "detections": detections,
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except Exception as e:

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# ==========================================================
# Incidents
# ==========================================================

@router.get("/incidents")
async def incidents(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    events = surveillance_service.get_incidents(
        db,
        limit,
    )

    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "confidence": e.confidence,
            "clip_path": e.clip_path,
            "person_id": e.person_id,
            "duration": e.duration,
            "timestamp": e.timestamp,
            "job_id": e.job_id,
        }
        for e in events
    ]


# ==========================================================
# LOW-LATENCY LIVE SURVEILLANCE
# ==========================================================

@router.post("/live/start")
async def start_live_surveillance(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Start a low-latency surveillance session from an uploaded video."""
    try:
        save_path = surveillance_service.save_uploaded_video(
            file.filename,
            file.file,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    session_id = uuid.uuid4().hex

    try:
        session = surveillance_service.create_live_session(
            source=save_path,
            session_id=session_id,
        )
        session.start()
    except Exception as e:
        traceback.print_exc()
        surveillance_service.remove_live_session(session_id)
        raise HTTPException(
            status_code=500,
            detail=f"Unable to start live surveillance: {e}",
        )

    return {"session_id": session_id, "status": "running"}


@router.get("/live/stream/{session_id}")
def live_stream(session_id: str):
    """Stream the latest annotated frame as an MJPEG stream."""
    session = surveillance_service.get_live_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Live session not found")

    def generate():
        while session.running or not session.finished:
            jpeg = session.get_jpeg()

            if jpeg is None:
                import time
                time.sleep(0.03)
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n"
                b"Content-Length: "
                + str(len(jpeg)).encode()
                + b"\r\n\r\n"
                + jpeg
                + b"\r\n"
            )

            import time
            time.sleep(0.03)

    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={"Cache-Control": "no-cache", "Pragma": "no-cache"},
    )


@router.get("/live/events/{session_id}")
async def live_events(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    session = surveillance_service.get_live_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Live session not found")

    return {
        "session_id": session_id,
        "events": session.get_events(),
        "status": session.get_status(),
    }


@router.get("/live/status/{session_id}")
async def live_status(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    session = surveillance_service.get_live_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Live session not found")

    return session.get_status()


@router.post("/live/stop/{session_id}")
async def stop_live_surveillance(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    session = surveillance_service.get_live_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Live session not found")

    surveillance_service.remove_live_session(session_id)

    return {"session_id": session_id, "status": "stopped"}


# ==========================================================
# Legacy live camera stream
# ==========================================================

@legacy_router.get("/video_feed")
def video_feed():

    system = surveillance_service.get_live_system()

    return StreamingResponse(
        system.generate_frames(),
        media_type=(
            "multipart/x-mixed-replace; "
            "boundary=frame"
        ),
    )