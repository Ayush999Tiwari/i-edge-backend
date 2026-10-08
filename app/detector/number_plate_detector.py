import cv2
import os
import tempfile
import uuid
from inference_sdk import InferenceHTTPClient

from app.core import config

UPLOAD_FOLDER = config.UPLOAD_PLATES_FOLDER

client = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key=config.ROBOFLOW_API_KEY,
)


def _run_plate_workflow(image_path):
    try:
        result = client.run_workflow(
            workspace_name=config.ROBOFLOW_PLATE_WORKSPACE,
            workflow_id=config.ROBOFLOW_PLATE_WORKFLOW_ID,
            images={"image": image_path},
            parameters={"classes": "license plate"},
            use_cache=True,
        )
    except Exception as e:
        raise RuntimeError(f"Roboflow plate workflow call failed: {e}")

    predictions = []
    for item in result:
        preds = (
            item.get("predictions", {}).get("predictions", [])
            if isinstance(item.get("predictions"), dict)
            else item.get("predictions", [])
        )
        predictions.extend(preds)

    return [p for p in predictions if p.get("class") == "license plate" and p.get("confidence", 0) >= 0.40]


def detect_and_crop_plate(vehicle_image_path: str) -> list:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    predictions = _run_plate_workflow(vehicle_image_path)

    img = cv2.imread(vehicle_image_path)
    if img is None:
        print(f"[X] Could not read image: {vehicle_image_path}")
        return []
    if not predictions:
        return []

    best_pred = max(predictions, key=lambda p: p["confidence"])
    cx, cy, w, h = int(best_pred["x"]), int(best_pred["y"]), int(best_pred["width"]), int(best_pred["height"])
    x1, y1 = max(cx - w // 2, 0), max(cy - h // 2, 0)
    x2, y2 = min(cx + w // 2, img.shape[1]), min(cy + h // 2, img.shape[0])

    plate_crop = img[y1:y2, x1:x2]
    if plate_crop.size == 0:
        return []

    base_name = os.path.splitext(os.path.basename(vehicle_image_path))[0]
    save_path = os.path.join(UPLOAD_FOLDER, f"{base_name}_plate.jpg")
    cv2.imwrite(save_path, plate_crop)
    return [save_path]


def detect_plate_box(frame):
    """Runs plate detection on an in-memory frame, returns (x1, y1, x2, y2, confidence) or None.
    Uses the OS temp directory (not a project-managed folder) for the frame
    Roboflow needs a file path for -- deleted again right after the call."""
    temp_path = os.path.join(tempfile.gettempdir(), f"frame_{uuid.uuid4().hex}.jpg")
    try:
        cv2.imwrite(temp_path, frame)
        predictions = _run_plate_workflow(temp_path)
    except Exception as e:
        print(f"[detect_plate_box] failed, skipping this vehicle: {e}")
        return None
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass

    if not predictions:
        return None

    best_pred = max(predictions, key=lambda p: p["confidence"])
    cx, cy, w, h = int(best_pred["x"]), int(best_pred["y"]), int(best_pred["width"]), int(best_pred["height"])
    x1, y1 = max(cx - w // 2, 0), max(cy - h // 2, 0)
    x2, y2 = min(cx + w // 2, frame.shape[1]), min(cy + h // 2, frame.shape[0])

    return x1, y1, x2, y2, float(best_pred["confidence"])
