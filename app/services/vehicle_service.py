import os
import re
import shutil
import uuid
import json
import traceback
from typing import Optional, List

import cv2
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core import config
from app.models import VehicleDetection, VideoJob
from app.detector import vehicle_detector
from app.detector.number_plate_detector import detect_plate_box

# thresholds from the original (active) process_video() -- unchanged
PLATE_CONF_THRESHOLD = 0.30
OCR_CONF_THRESHOLD = 0.40


# ---------------- Indian plate validator (unchanged from db_manager.py) ---------------- #

LETTER_FIX = {"0": "O", "1": "I", "2": "Z", "5": "S", "6": "G", "8": "B"}
DIGIT_FIX = {"O": "0", "Q": "0", "D": "0", "I": "1", "L": "1", "Z": "2", "S": "5", "B": "8", "G": "6"}
VALID_STATES = {
    "AN", "AP", "AR", "AS", "BR", "CG", "CH", "DD", "DL", "DN",
    "GA", "GJ", "HP", "HR", "JH", "JK", "KA", "KL", "LA", "LD",
    "MH", "ML", "MN", "MP", "MZ", "NL", "OD", "PB", "PY", "RJ",
    "SK", "TN", "TR", "TS", "UK", "UP", "WB",
}


def normalize_indian_plate(raw):
    if not raw:
        return None

    text = re.sub(r"[^A-Z0-9]", "", raw.upper())
    if len(text) < 8:
        return None

    for series_len in (1, 2, 3):
        expected = 2 + 2 + series_len + 4
        if len(text) != expected:
            continue

        chars = list(text)
        state, ok = "", True
        for i in range(2):
            c = LETTER_FIX.get(chars[i], chars[i])
            if not c.isalpha():
                ok = False
                break
            state += c
        if not ok or state not in VALID_STATES:
            continue

        rto = ""
        for i in range(2, 4):
            c = DIGIT_FIX.get(chars[i], chars[i])
            if not c.isdigit():
                ok = False
                break
            rto += c
        if not ok:
            continue

        series = ""
        for i in range(4, 4 + series_len):
            c = LETTER_FIX.get(chars[i], chars[i])
            if not c.isalpha():
                ok = False
                break
            series += c
        if not ok:
            continue

        number = ""
        for i in range(4 + series_len, expected):
            c = DIGIT_FIX.get(chars[i], chars[i])
            if not c.isdigit():
                ok = False
                break
            number += c
        if not ok:
            continue

        plate = f"{state}{rto}{series}{number}"
        if re.fullmatch(r"^[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{4}$", plate):
            return plate

    return None


def save_vehicle_detection(
    db: Session,
    vehicle_id: str,
    plate_number: str,
    confidence: float,
    image_path: str,
    vehicle_type: str,
    timestamp: float,
) -> VehicleDetection:
    """Unchanged validation/persistence logic from db_manager.py's
    save_vehicle_log(), now writing through the shared Session."""
    normalized = normalize_indian_plate(plate_number)
    if normalized is None:
        raise ValueError(f"'{plate_number}' is not a valid Indian registration")

    try:
        log = VehicleDetection(
            vehicle_id=vehicle_id,
            plate_number=normalized,
            vehicle_type=vehicle_type,
            confidence=confidence,
            image_path=image_path,
            timestamp=timestamp,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    except IntegrityError as e:
        db.rollback()
        raise ValueError(str(e))


# ---------------- Upload handling ---------------- #

def save_uploaded_video(filename: str, file_obj) -> str:
    if not filename.lower().endswith(config.ALLOWED_VIDEO_EXTENSIONS):
        raise ValueError("Unsupported file format")

    save_path = os.path.join(config.UPLOAD_VIDEO_FOLDER, filename)
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file_obj, buffer)
    return save_path


def create_job(db: Session, filename: str, input_path: str) -> VideoJob:
    job = VideoJob(original_filename=filename, input_path=input_path, status="processing")
    db.add(job)
    db.commit()
    db.refresh(job)
    job.vehicle_id = f"VEH-{job.id}"
    db.commit()
    return job


# ---------------- Detection + OCR + persistence pipeline ---------------- #
# This is the part that used to be the second half of
# vehicle_detector.process_video() -- same crop-size checks, same
# thresholds, same skip/continue behavior, just calling the detector
# functions instead of being inlined inside the detector.

def _levenshtein(a: str, b: str) -> int:
    """Small edit-distance helper (no extra dependency) used only for the
    duplicate-plate check below."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            curr[j] = min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost)
        prev = curr
    return prev[-1]


def _is_duplicate_of_recent(plate: str, timestamp: float, already_saved: list) -> bool:
    """A plate saved earlier IN THIS SAME JOB, within
    DUPLICATE_PLATE_TIME_WINDOW_SECONDS and DUPLICATE_PLATE_MAX_EDIT_DISTANCE
    characters of this one, is almost certainly the same physical vehicle
    re-read under a different (churned) track id -- not a second vehicle.
    custom_bytetrack.yaml reduces how often tracks churn in the first place;
    this catches whatever still slips through."""
    for prior in already_saved:
        if abs(prior["timestamp"] - timestamp) > config.DUPLICATE_PLATE_TIME_WINDOW_SECONDS:
            continue
        if _levenshtein(plate, prior["plate_number"]) <= config.DUPLICATE_PLATE_MAX_EDIT_DISTANCE:
            return True
    return False


def process_and_store(db: Session, job_id: int, video_path: str) -> dict:
    tracking_result = vehicle_detector.track_vehicles(video_path, job_id)
    track_cache = tracking_result["track_cache"]
    track_timestamps = tracking_result["track_timestamps"]

    os.makedirs(config.UPLOAD_PLATES_FOLDER, exist_ok=True)
    final = []

    for track_id, entry in track_cache.items():
        crop = entry["best_crop"]

        box = detect_plate_box(crop)
        if not box:
            print(f"[NO PLATE] Track {track_id}")
            continue

        px1, py1, px2, py2, plate_conf = box
        if plate_conf < PLATE_CONF_THRESHOLD:
            print(f"[LOW PLATE] Track {track_id}")
            continue

        plate_crop = crop[py1:py2, px1:px2]
        if plate_crop.shape[1] < 40 or plate_crop.shape[0] < 12:
            print(f"[SMALL PLATE] Track {track_id}")
            continue

        plate_crop = cv2.resize(plate_crop, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

        plate_text, ocr_conf = vehicle_detector.ocr_vote(plate_crop)
        print(f"[OCR] Track {track_id} -> {plate_text} ({ocr_conf:.2f})")

        if not plate_text:
            continue
        if ocr_conf < OCR_CONF_THRESHOLD:
            continue

        normalized_plate = normalize_indian_plate(plate_text)
        if normalized_plate is None:
            print(f"[SKIPPED] '{plate_text}' is not a valid Indian registration")
            continue

        timestamp = track_timestamps[track_id]
        if _is_duplicate_of_recent(normalized_plate, timestamp, final):
            print(f"[DUPLICATE] Track {track_id} -> {normalized_plate} looks like the "
                  f"same vehicle already saved a moment ago, skipping")
            continue

        image_path = os.path.join(config.UPLOAD_PLATES_FOLDER, f"{uuid.uuid4().hex}_plate.jpg")
        cv2.imwrite(image_path, plate_crop)

        vehicle_id = f"VEH-{job_id}-{track_id}"

        try:
            log = save_vehicle_detection(
                db,
                vehicle_id=vehicle_id,
                plate_number=normalized_plate,
                confidence=round(ocr_conf * 100, 1),
                image_path=image_path,
                vehicle_type=entry["vehicle_type"],
                timestamp=timestamp,
            )
            final.append({
                "vehicle_type": log.vehicle_type,
                "vehicle_id": log.vehicle_id,
                "plate_number": log.plate_number,
                "confidence": log.confidence,
                "image_path": log.image_path,
                "timestamp": log.timestamp,
            })
            print(f"[SAVED] {log.vehicle_type} | {log.plate_number} | {log.timestamp}s")
        except ValueError as e:
            print(f"[SKIPPED] {e}")
            continue

    print(f"\nCompleted : {len(final)} vehicle(s) stored.")

    return {
        "processed_video": tracking_result["processed_video"],
        "vehicles_detected": len(track_cache),
        "detections": final,
    }


def run_pipeline(db: Session, job_id: int, video_path: str) -> None:
    """Background task -- unchanged logic from main.py's _run_pipeline()."""
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    if not job:
        return
    try:
        result = process_and_store(db, job_id, video_path)
        job.status = "completed"
        job.output_path = result["processed_video"]
        job.vehicles_detected = result["vehicles_detected"]
        detections = result.get("detections", [])
        if detections:
            first = detections[0]
            job.plate_number = first["plate_number"]
            job.confidence_score = first["confidence"]
            job.vehicle_id = first["vehicle_id"]
        else:
            job.vehicle_id = f"VEH-{job.id}"
            job.plate_number = None
            job.confidence_score = 0
        job.error_message = json.dumps(detections)
    except Exception as e:
        traceback.print_exc()
        job.status = "failed"
        job.error_message = str(e)
    finally:
        db.commit()


# ---------------- Read helpers (used by GET routes) ---------------- #

def get_job(db: Session, job_id: int) -> Optional[VideoJob]:
    return db.query(VideoJob).filter(VideoJob.id == job_id).first()


def get_analytics(db: Session, job_id: int) -> Optional[dict]:
    job = get_job(db, job_id)
    if not job:
        return None
    detections = []
    if job.error_message:
        try:
            detections = json.loads(job.error_message)
        except Exception:
            detections = []
    return {
        "job_id": job.id,
        "vehicle_count": job.vehicles_detected or 0,
        "plates_recognized": len(detections),
        "processed_video": f"/api/vehicle/video/{job.id}",
        "detections": detections,
    }


def get_history(db: Session) -> List[VehicleDetection]:
    return db.query(VehicleDetection).order_by(VehicleDetection.id.desc()).all()


# ---------------- Single-image plate lookup (new POST /plate endpoint) ---------------- #
# Wraps the existing detect_and_crop_plate() + OCR reader on a single
# uploaded image -- no new detection algorithm, just exposing the
# already-existing functions as their own endpoint.

def read_plate_from_image(image_path: str) -> dict:
    from app.detector.number_plate_detector import detect_and_crop_plate

    crops = detect_and_crop_plate(image_path)
    if not crops:
        return {"plate_text": None, "confidence": 0.0, "crop_path": None, "message": "No plate detected"}

    crop_path = crops[0]
    plate_crop = cv2.imread(crop_path)
    plate_text, ocr_conf = vehicle_detector.ocr_vote(plate_crop)
    return {
        "plate_text": plate_text,
        "confidence": ocr_conf,
        "crop_path": crop_path,
        "message": "Success" if plate_text else "Plate not readable",
    }
