import os
import traceback

from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core import config
from app.database import get_db
from app.schemas import VideoStatusResponse, VideoUploadResponse
from app.services import vehicle_service

router = APIRouter(prefix="/api/vehicle", tags=["Vehicle Intelligence"])


@router.post("/detect", response_model=VideoUploadResponse)
async def detect(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        save_path = vehicle_service.save_uploaded_video(file.filename, file.file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        job = vehicle_service.create_job(db, file.filename, save_path)
    except Exception as e:
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    background_tasks.add_task(_run_pipeline_task, job.id, save_path)
    return VideoUploadResponse(id=job.id, vehicle_id=job.vehicle_id, status=job.status)


def _run_pipeline_task(job_id: int, video_path: str):
    """Background task entry point -- opens its own DB session, same
    as the original main.py's _run_pipeline()."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        vehicle_service.run_pipeline(db, job_id, video_path)
    finally:
        db.close()


@router.post("/plate")
async def detect_plate(file: UploadFile = File(...)):
    os.makedirs(config.UPLOAD_PLATES_FOLDER, exist_ok=True)
    temp_path = os.path.join(config.UPLOAD_PLATES_FOLDER, file.filename)
    with open(temp_path, "wb") as buffer:
        buffer.write(await file.read())

    try:
        return vehicle_service.read_plate_from_image(temp_path)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def history(db: Session = Depends(get_db)):
    logs = vehicle_service.get_history(db)
    return [
        {
            "id": log.id,
            "vehicle_id": log.vehicle_id,
            "vehicle_type": log.vehicle_type,
            "plate_number": log.plate_number,
            "confidence": log.confidence,
            "timestamp": log.timestamp,
        }
        for log in logs
    ]


@router.get("/analytics/{job_id}")
async def analytics(job_id: int, db: Session = Depends(get_db)):
    result = vehicle_service.get_analytics(db, job_id)
    if result is None:
        raise HTTPException(404, "Job not found")
    return result


@router.get("/status/{job_id}", response_model=VideoStatusResponse)
async def status(job_id: int, db: Session = Depends(get_db)):
    job = vehicle_service.get_job(db, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return VideoStatusResponse(
        id=job.id,
        original_filename=job.original_filename,
        input_path=job.input_path,
        output_path=job.output_path,
        status=job.status,
        confidence_score=job.confidence_score,
        created_at=job.created_at,
        plate_number=job.plate_number,
        confidence=job.confidence_score,
        vehicle_id=job.vehicle_id,
        vehicles_detected=job.vehicles_detected,
        detail=job.error_message,
    )


@router.get("/video/{job_id}")
async def get_processed_video(job_id: int, db: Session = Depends(get_db)):
    job = vehicle_service.get_job(db, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if not job.output_path or not os.path.exists(job.output_path):
        raise HTTPException(404, "Processed video unavailable")
    return FileResponse(job.output_path, media_type="video/mp4", filename=os.path.basename(job.output_path))


@router.get("/download/{job_id}")
async def download_plate(job_id: int, db: Session = Depends(get_db)):
    job = vehicle_service.get_job(db, job_id)
    if not job or not job.output_path:
        raise HTTPException(404, "No processed file available")
    return FileResponse(job.output_path)
