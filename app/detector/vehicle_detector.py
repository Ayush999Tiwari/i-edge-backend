# ==========================================================
# Vehicle detector: YOLO tracking across a video + OCR voting on
# the best crop per tracked vehicle.
#
# This used to be one function, process_video(), which ALSO wrote
# the recognized plate straight to the database (a detector file
# doing DB writes -- one of the architecture issues called out in
# the refactor). It's now split in two, with identical thresholds
# and control flow, just re-drawn across a layer boundary:
#
#   track_vehicles()  - AI-only: runs YOLO+ByteTrack over the video,
#                        writes the annotated output video, returns
#                        the best crop / timestamp per tracked
#                        vehicle. No DB access, no persistent
#                        live-preview folder (removed).
#   ocr_vote()         - AI-only: unchanged 5-way image-enhancement
#                        OCR voting.
#
# services/vehicle_service.py now owns the loop that calls
# detect_plate_box() + ocr_vote() per track and persists results --
# see that file for the part that used to live at the bottom of the
# original process_video().
# ==========================================================
import cv2
import os
import threading
from collections import Counter
from ultralytics import YOLO

from app.core import config
from app.detector.number_plate_detector import detect_plate_box  # noqa: F401 (re-exported for the service)

VALID_CLASSES = [
    "car",
    "motorcycle",
    "truck",
    "bus",
    "mini trucks",
    "tractor",
    "tempo",
]

CONF_THRESHOLD = 0.5

model = YOLO("yolo11n.pt")

_ocr_reader = None
_ocr_lock = threading.Lock()


# ------------------------------------------------ #
# OCR Loader
# ------------------------------------------------ #
def _get_ocr_reader():
    global _ocr_reader
    with _ocr_lock:
        if _ocr_reader is None:
            from app.detector.ocr_reader import OCRReader
            _ocr_reader = OCRReader()
        return _ocr_reader


# ------------------------------------------------ #
# Sharpness
# ------------------------------------------------ #
def calculate_sharpness(image):
    if image is None or image.size == 0:
        return 0
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


# ------------------------------------------------ #
# Best Crop
# ------------------------------------------------ #
def _update_best_crop(frame, box, track_id, cls_name, cache):
    x1, y1, x2, y2 = box
    crop = frame[y1:y2, x1:x2]
    if crop.size == 0:
        return

    area = (x2 - x1) * (y2 - y1)
    score = (area * 0.001) + calculate_sharpness(crop)

    prev = cache.get(track_id)
    if prev is None or score > prev["best_score"]:
        cache[track_id] = {
            "vehicle_type": cls_name,
            "best_crop": crop.copy(),
            "best_score": score,
        }


# ------------------------------------------------ #
# OCR Voting
# ------------------------------------------------ #
def ocr_vote(plate_crop):
    reader = _get_ocr_reader()

    versions = [
        plate_crop,
        cv2.convertScaleAbs(plate_crop, alpha=1.2, beta=10),
        cv2.convertScaleAbs(plate_crop, alpha=1.5, beta=20),
        cv2.GaussianBlur(plate_crop, (3, 3), 0),
        cv2.detailEnhance(plate_crop, sigma_s=10, sigma_r=0.15),
    ]

    votes = []
    for img in versions:
        result = reader.extract_text(img)
        if result["plate_text"]:
            votes.append((result["plate_text"], result.get("confidence", 0.5)))

    if not votes:
        return None, 0

    texts = [v[0] for v in votes]
    winner = Counter(texts).most_common(1)[0][0]
    scores = [c for t, c in votes if t == winner]
    return winner, sum(scores) / len(scores)


# ------------------------------------------------ #
# MAIN TRACKING PIPELINE (AI only -- no DB writes)
# ------------------------------------------------ #
def track_vehicles(video_path: str, job_id: int) -> dict:
    """Runs YOLO+ByteTrack over the uploaded video, writes the
    annotated output video, and returns the best crop + first-seen
    timestamp for every tracked vehicle. Callers are responsible for
    running plate detection/OCR and persisting results."""

    if not os.path.exists(video_path):
        raise RuntimeError(f"Video not found: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("Unable to open uploaded video")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    os.makedirs(config.OUTPUT_VIDEO_FOLDER, exist_ok=True)
    output_video_path = os.path.join(config.OUTPUT_VIDEO_FOLDER, f"job_{job_id}.mp4")

    writer = cv2.VideoWriter(
        output_video_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )

    track_cache = {}
    track_timestamps = {}
    frame_count = 0

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            results = model.track(
                source=frame,
                persist=True,
                tracker=config.VEHICLE_TRACKER_CONFIG,
                conf=CONF_THRESHOLD,
                imgsz=1280,
                verbose=False,
            )

            for r in results:
                if r.boxes is None:
                    continue
                for box in r.boxes:
                    cls = model.names[int(box.cls[0])]
                    if cls not in VALID_CLASSES or box.id is None:
                        continue

                    track_id = int(box.id[0])
                    if track_id not in track_timestamps:
                        track_timestamps[track_id] = round(frame_count / fps, 2)

                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    _update_best_crop(frame, (x1, y1, x2, y2), track_id, cls, track_cache)

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"{cls} #{track_id}", (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)

            writer.write(frame)
            frame_count += 1

    finally:
        cap.release()
        writer.release()

    if not track_cache:
        raise RuntimeError("No vehicles detected in this video.")

    print(f"\n[INFO] {len(track_cache)} vehicle(s) captured\n")

    return {
        "processed_video": output_video_path,
        "track_cache": track_cache,
        "track_timestamps": track_timestamps,
    }