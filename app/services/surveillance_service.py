import threading
import os
import shutil
import traceback
from typing import Optional, List

import cv2
import numpy as np
from sqlalchemy.orm import Session

from app.core import config
from app.models import SurveillanceEvent, SurveillanceJob
from app.detector.person_detector import PersonDetector
from app.detector.fire_detector import FireDetector
from app.detector.violence_detector import VoilenceDetector
from app.detector.crowd_detector import detect_crowd
from app.services.surveillance.live_system import SurveillanceSystem
from app.services.surveillance.email_alert import EmailAlertManager


_live_system: Optional[SurveillanceSystem] = None
_live_system_lock = threading.Lock()

_person_detector: Optional[PersonDetector] = None
_fire_detector: Optional[FireDetector] = None
_violence_detector: Optional[VoilenceDetector] = None
_detectors_lock = threading.Lock()

_email_manager: Optional[EmailAlertManager] = None
_email_manager_lock = threading.Lock()


def get_live_system() -> SurveillanceSystem:
    """Lazily builds the live camera SurveillanceSystem on first use."""
    global _live_system

    with _live_system_lock:
        if _live_system is None:
            _live_system = SurveillanceSystem()

        return _live_system


def _get_person_detector() -> PersonDetector:
    global _person_detector

    with _detectors_lock:
        if _person_detector is None:
            _person_detector = PersonDetector()

        return _person_detector


def _get_fire_detector() -> FireDetector:
    global _fire_detector

    with _detectors_lock:
        if _fire_detector is None:
            _fire_detector = FireDetector()

        return _fire_detector


def _get_violence_detector() -> VoilenceDetector:
    global _violence_detector

    with _detectors_lock:
        if _violence_detector is None:
            _violence_detector = VoilenceDetector()

        return _violence_detector


def _get_email_manager() -> EmailAlertManager:
    global _email_manager

    with _email_manager_lock:
        if _email_manager is None:
            _email_manager = EmailAlertManager()

        return _email_manager


def _decode_image(image_bytes: bytes):
    array = np.frombuffer(image_bytes, dtype=np.uint8)
    frame = cv2.imdecode(array, cv2.IMREAD_COLOR)

    if frame is None:
        raise ValueError("Could not decode uploaded image")

    return frame


def _log_event(db: Session, event_type: str, confidence: float) -> None:
    db.add(
        SurveillanceEvent(
            event_type=event_type,
            confidence=confidence or 0.0,
        )
    )
    db.commit()


def analyze_fire(db: Session, image_bytes: bytes) -> List[dict]:
    frame = _decode_image(image_bytes)

    detector = _get_fire_detector()
    detections = detector.detect(frame)

    if detections:
        top = max(d["confidence"] for d in detections)
        _log_event(db, "fire", top)

    return detections


def analyze_violence(db: Session, image_bytes: bytes) -> dict:
    frame = _decode_image(image_bytes)

    detector = _get_violence_detector()
    result = detector.detect_snapshot(frame)

    if result.get("detected"):
        _log_event(
            db,
            "voilence",
            result.get("confidence", 0.0),
        )

    return result


def analyze_person(db: Session, image_bytes: bytes) -> List[dict]:
    frame = _decode_image(image_bytes)

    detector = _get_person_detector()
    results = detector.detect_and_track(frame)
    detections = detector.get_detections(results)

    serializable = [
        {
            "id": d["id"],
            "class": d["class"],
            "confidence": d["confidence"],
            "bbox": [float(v) for v in d["bbox"]],
        }
        for d in detections
    ]

    for d in serializable:
        if d["class"] == "person":
            _log_event(
                db,
                "person",
                d["confidence"],
            )

    return serializable


def analyze_crowd(db: Session, image_bytes: bytes) -> dict:
    frame = _decode_image(image_bytes)

    detector = _get_person_detector()
    result = detect_crowd(frame, detector)

    if result["crowd_detected"]:
        _log_event(db, "crowd", 1.0)

    result.pop("detections", None)

    return result


def get_incidents(
    db: Session,
    limit: int = 100,
) -> List[SurveillanceEvent]:
    return (
        db.query(SurveillanceEvent)
        .order_by(SurveillanceEvent.id.desc())
        .limit(limit)
        .all()
    )


# ==========================================================
# Combined video pipeline
# ==========================================================

def save_uploaded_video(filename: str, file_obj) -> str:
    if not filename.lower().endswith(
        config.ALLOWED_VIDEO_EXTENSIONS
    ):
        raise ValueError("Unsupported file format")

    save_path = os.path.join(
        config.SURVEILLANCE_UPLOAD_FOLDER,
        filename,
    )

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file_obj, buffer)

    return save_path


def create_video_job(
    db: Session,
    filename: str,
    input_path: str,
    alert_email: Optional[str] = None,
) -> SurveillanceJob:

    job = SurveillanceJob(
        original_filename=filename,
        input_path=input_path,
        status="uploaded",
        alert_email=alert_email,
        email_alerts_sent=0,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job


def get_video_job(
    db: Session,
    job_id: int,
) -> Optional[SurveillanceJob]:

    return (
        db.query(SurveillanceJob)
        .filter(SurveillanceJob.id == job_id)
        .first()
    )


def get_all_video_jobs(
    db: Session,
) -> List[SurveillanceJob]:

    return (
        db.query(SurveillanceJob)
        .order_by(SurveillanceJob.id.desc())
        .all()
    )


def _draw_fire_box(frame, fire: dict) -> None:
    x1, y1, x2, y2 = map(int, fire["bbox"])

    cv2.rectangle(
        frame,
        (x1, y1),
        (x2, y2),
        config.FIRE_BOX_COLOR,
        2,
    )

    cv2.putText(
        frame,
        f"fire {fire['confidence']:.2f}",
        (x1, y1 - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        config.FIRE_BOX_COLOR,
        2,
    )


def _save_incident_snapshot(
    job_id: int,
    incident_type: str,
    timestamp_sec: float,
    frame,
) -> str:

    os.makedirs(
        config.DETECTIONS_DIR,
        exist_ok=True,
    )

    path = os.path.join(
        config.DETECTIONS_DIR,
        f"job{job_id}_{incident_type}_{timestamp_sec}s.jpg",
    )

    cv2.imwrite(path, frame)

    return path


def process_video(
    db: Session,
    job_id: int,
    video_path: str,
) -> dict:

    """
    Runs person/crowd + fire + violence detection together.

    Email alerts are sent immediately when an incident is detected.
    The recipient is the email stored on the current surveillance job.
    """

    if not os.path.exists(video_path):
        raise RuntimeError(
            f"Video not found: {video_path}"
        )

    # ------------------------------------------------------
    # Get current job and its alert recipient
    # ------------------------------------------------------

    job = get_video_job(db, job_id)

    if not job:
        raise RuntimeError(
            f"Surveillance job {job_id} not found"
        )

    alert_email = getattr(
        job,
        "alert_email",
        None,
    )

    # ------------------------------------------------------
    # Open video
    # ------------------------------------------------------

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise RuntimeError(
            "Unable to open uploaded video"
        )

    fps = cap.get(cv2.CAP_PROP_FPS) or 25

    width = int(
        cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    )

    height = int(
        cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    )

    output_path = os.path.join(
        config.SURVEILLANCE_OUTPUT_FOLDER,
        f"job_{job_id}.mp4",
    )

    writer = cv2.VideoWriter(
        output_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )

    # ------------------------------------------------------
    # Detectors
    # ------------------------------------------------------

    person_detector = _get_person_detector()
    fire_detector = _get_fire_detector()
    violence_detector = _get_violence_detector()

    # ------------------------------------------------------
    # Email manager
    #
    # IMPORTANT:
    # If the logged-in account has no email, we do NOT send
    # the alert to the old hardcoded EMAIL_RECEIVER.
    # ------------------------------------------------------

    email = None

    if config.ENABLE_EMAIL and alert_email:
        email = _get_email_manager()

        print(
            f"[EMAIL] Surveillance alerts will be sent to: "
            f"{alert_email}"
        )

    elif config.ENABLE_EMAIL and not alert_email:
        print(
            "[EMAIL] No email associated with this account. "
            "Email alerts disabled for this job."
        )

    # ------------------------------------------------------
    # Counters
    # ------------------------------------------------------

    fire_events = 0
    crowd_events = 0
    violence_events = 0

    max_fire_conf = 0.0
    max_person_count = 0
    max_violence_conf = 0.0

    # Number of emails successfully sent for this job.
    email_alerts_sent = 0

    # ------------------------------------------------------
    # Per-job cooldown trackers
    # ------------------------------------------------------

    last_fire_alert_ts = None
    last_crowd_alert_ts = None
    last_violence_alert_ts = None

    frame_idx = 0

    try:

        while True:

            ok, frame = cap.read()

            if not ok:
                break

            if (
                frame_idx
                % config.SURVEILLANCE_VIDEO_FRAME_SKIP
                == 0
            ):

                timestamp_sec = round(
                    frame_idx / fps,
                    2,
                )

                # ==================================================
                # CROWD
                # ==================================================

                crowd_result = detect_crowd(
                    frame,
                    person_detector,
                )

                person_count = crowd_result[
                    "person_count"
                ]

                max_person_count = max(
                    max_person_count,
                    person_count,
                )

                if crowd_result["crowd_detected"]:

                    crowd_events += 1

                    db.add(
                        SurveillanceEvent(
                            event_type="crowd",
                            confidence=1.0,
                            job_id=job_id,
                        )
                    )

                    cv2.putText(
                        frame,
                        f"CROWD ({person_count})",
                        (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 165, 255),
                        2,
                    )

                    # --------------------------------------------------
                    # Crowd email
                    # --------------------------------------------------

                    if (
                        email
                        and alert_email
                        and (
                            last_crowd_alert_ts is None
                            or (
                                timestamp_sec
                                - last_crowd_alert_ts
                                > config.CROWD_ALERT_COOLDOWN
                            )
                        )
                    ):

                        snapshot_path = (
                            _save_incident_snapshot(
                                job_id,
                                "crowd",
                                timestamp_sec,
                                frame,
                            )
                        )

                        sent = email.send_crowd_alert(
                            snapshot_path,
                            person_count,
                            severity="medium",
                            recipient_email=alert_email,
                        )

                        if sent:
                            email_alerts_sent += 1

                            print(
                                f"[EMAIL] Crowd alert sent "
                                f"to {alert_email}"
                            )

                        last_crowd_alert_ts = (
                            timestamp_sec
                        )

                # ==================================================
                # FIRE
                # ==================================================

                fire_detections = (
                    fire_detector.detect(frame)
                )

                for fire in fire_detections:

                    fire_events += 1

                    max_fire_conf = max(
                        max_fire_conf,
                        fire["confidence"],
                    )

                    _draw_fire_box(
                        frame,
                        fire,
                    )

                    db.add(
                        SurveillanceEvent(
                            event_type="fire",
                            confidence=fire["confidence"],
                            job_id=job_id,
                        )
                    )

                # --------------------------------------------------
                # Fire email
                # --------------------------------------------------

                if (
                    fire_detections
                    and email
                    and alert_email
                    and (
                        last_fire_alert_ts is None
                        or (
                            timestamp_sec
                            - last_fire_alert_ts
                            > config.FIRE_ALERT_COOLDOWN
                        )
                    )
                ):

                    top_conf = max(
                        d["confidence"]
                        for d in fire_detections
                    )

                    severity = (
                        "critical"
                        if person_count
                        >= config.CROWD_THRESHOLD
                        else "high"
                    )

                    snapshot_path = (
                        _save_incident_snapshot(
                            job_id,
                            "fire",
                            timestamp_sec,
                            frame,
                        )
                    )

                    sent = email.send_fire_alert(
                        snapshot_path,
                        top_conf,
                        person_count,
                        severity,
                        recipient_email=alert_email,
                    )

                    if sent:
                        email_alerts_sent += 1

                        print(
                            f"[EMAIL] Fire alert sent "
                            f"to {alert_email}"
                        )

                    last_fire_alert_ts = (
                        timestamp_sec
                    )

                # ==================================================
                # VIOLENCE
                # ==================================================

                violence_result = (
                    violence_detector.detect_snapshot(
                        frame
                    )
                )

                if violence_result.get("detected"):

                    violence_events += 1

                    conf = violence_result.get(
                        "confidence",
                        0.0,
                    )

                    max_violence_conf = max(
                        max_violence_conf,
                        conf,
                    )

                    cv2.putText(
                        frame,
                        f"VIOLENCE {conf:.2f}",
                        (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 0, 255),
                        2,
                    )

                    db.add(
                        SurveillanceEvent(
                            event_type="voilence",
                            confidence=conf,
                            job_id=job_id,
                        )
                    )

                    # --------------------------------------------------
                    # Violence email
                    # --------------------------------------------------

                    if (
                        email
                        and alert_email
                        and (
                            last_violence_alert_ts is None
                            or (
                                timestamp_sec
                                - last_violence_alert_ts
                                > config.VOILENCE_ALERT_COOLDOWN
                            )
                        )
                    ):

                        severity = (
                            "critical"
                            if person_count >= 2
                            else "high"
                        )

                        snapshot_path = (
                            _save_incident_snapshot(
                                job_id,
                                "voilence",
                                timestamp_sec,
                                frame,
                            )
                        )

                        sent = email.send_voilence_alert(
                            snapshot_path,
                            conf,
                            person_count,
                            severity,
                            recipient_email=alert_email,
                        )

                        if sent:
                            email_alerts_sent += 1

                            print(
                                f"[EMAIL] Violence alert sent "
                                f"to {alert_email}"
                            )

                        last_violence_alert_ts = (
                            timestamp_sec
                        )

                # --------------------------------------------------
                # Save DB events
                # --------------------------------------------------

                if (
                    fire_detections
                    or crowd_result["crowd_detected"]
                    or violence_result.get("detected")
                ):
                    db.commit()

            writer.write(frame)

            frame_idx += 1

    finally:

        cap.release()
        writer.release()

    # ------------------------------------------------------
    # Final result
    # ------------------------------------------------------

    return {
        "output_path": output_path,

        "fire_detected": fire_events > 0,
        "fire_events": fire_events,
        "max_fire_confidence": max_fire_conf,

        "crowd_detected": crowd_events > 0,
        "crowd_events": crowd_events,
        "max_person_count": max_person_count,

        "violence_detected": violence_events > 0,
        "violence_events": violence_events,
        "max_violence_confidence": max_violence_conf,

        # Email information
        "alert_email": alert_email,
        "email_alerts_sent": email_alerts_sent,
    }


def run_video_pipeline(
    db: Session,
    job_id: int,
    video_path: str,
) -> None:

    """Background task for POST /api/surveillance/detect/{job_id}."""

    job = get_video_job(
        db,
        job_id,
    )

    if not job:
        return

    job.status = "processing"

    db.commit()

    try:

        result = process_video(
            db,
            job_id,
            video_path,
        )

        job.status = "completed"

        job.output_path = result[
            "output_path"
        ]

        job.fire_detected = result[
            "fire_detected"
        ]

        job.fire_events = result[
            "fire_events"
        ]

        job.max_fire_confidence = result[
            "max_fire_confidence"
        ]

        job.crowd_detected = result[
            "crowd_detected"
        ]

        job.crowd_events = result[
            "crowd_events"
        ]

        job.max_person_count = result[
            "max_person_count"
        ]

        job.violence_detected = result[
            "violence_detected"
        ]

        job.violence_events = result[
            "violence_events"
        ]

        job.max_violence_confidence = result[
            "max_violence_confidence"
        ]

        # --------------------------------------------------
        # Persist email result
        # --------------------------------------------------

        job.email_alerts_sent = result.get(
            "email_alerts_sent",
            0,
        )

        # Keep the email that was actually associated
        # with this job.
        job.alert_email = result.get(
            "alert_email"
        )

        print(
            f"[SURVEILLANCE] Job {job_id} completed. "
            f"Email alerts sent: "
            f"{job.email_alerts_sent}"
        )

    except Exception as e:

        traceback.print_exc()

        job.status = "failed"
        job.error_message = str(e)

    finally:

        db.commit()