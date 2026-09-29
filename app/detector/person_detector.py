# ==========================================================
# Person/object detector (YOLO + ByteTrack). Unchanged logic from
# the original person_detector.py -- same tracker args, same
# confidence/IOU/area filtering.
# ==========================================================
import torch
from ultralytics import YOLO

from app.core import config


class PersonDetector:
    def __init__(self):
        print(f"[DETECTOR] Loading model: {config.MODEL_NAME}")
        try:
            self.model = YOLO(config.MODEL_NAME)
        except Exception as e:
            raise Exception(f"Failed to load model: {e}")
        self.device = self._setup_device()
        print("[DETECTOR] Model loaded successfully")
        print(f"[DETECTOR] Device: {self.device}")
        if config.TARGET_CLASSES is None:
            print("[DETECTOR] Detecting ALL classes")
        else:
            print(f"[DETECTOR] Target classes: {config.TARGET_CLASSES}")

    def _setup_device(self):
        if config.USE_GPU and torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            print(f"[DETECTOR] GPU detected: {device_name}")
            if config.USE_HALF_PRECISION:
                print("[DETECTOR] FP16 inference enabled")
            return "cuda"
        print("[DETECTOR] Using CPU")
        return "cpu"

    def detect_and_track(self, frame):
        try:
            results = self.model.track(
                source=frame,
                persist=True,
                tracker=config.TRACKER_TYPE,
                conf=config.CONFIDENCE_THRESHOLD,
                iou=config.IOU_THRESHOLD,
                max_det=config.MAX_DETECTIONS,
                device=self.device,
                verbose=False,
                half=(config.USE_HALF_PRECISION and self.device == "cuda")
            )
            return results
        except Exception as e:
            print(f"[DETECTOR ERROR] Tracking failed: {e}")
            return []

    def detect_only(self, frame):
        try:
            results = self.model(
                source=frame,
                conf=config.CONFIDENCE_THRESHOLD,
                iou=config.IOU_THRESHOLD,
                max_det=config.MAX_DETECTIONS,
                device=self.device,
                verbose=False,
                half=(config.USE_HALF_PRECISION and self.device == "cuda")
            )
            return results
        except Exception as e:
            print(f"[DETECTOR ERROR] Detection failed: {e}")
            return []

    def get_detections(self, results):
        detections = []
        if not results or len(results) == 0 or results[0].boxes is None:
            return detections

        for box in results[0].boxes:
            try:
                cls_id = int(box.cls.item())
                class_name = self.model.names[cls_id]
                if config.TARGET_CLASSES is not None and class_name not in config.TARGET_CLASSES:
                    continue

                confidence = float(box.conf.item())
                bbox = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = bbox
                area = (x2 - x1) * (y2 - y1)

                if area < config.MIN_BBOX_AREA:
                    continue

                track_id = int(box.id.item()) if box.id is not None else None

                detections.append({
                    "id": track_id,
                    "class": class_name,
                    "confidence": confidence,
                    "bbox": bbox,
                    "area": area
                })
            except Exception as e:
                print(f"[DETECTOR WARNING] Failed parsing box: {e}")
        return detections

    def count_persons(self, detections: list) -> int:
        """Count detections where class is 'person'."""
        return sum(1 for d in detections if d["class"] == "person")

    def get_class_names(self):
        return self.model.names

    def print_supported_classes(self):
        print("\n===== Supported Classes =====")
        for idx, name in self.model.names.items():
            print(f"{idx:02d} -> {name}")
        print("=" * 35)

    def warmup(self):
        import numpy as np
        dummy = np.zeros((640, 640, 3), dtype=np.uint8)
        print("[DETECTOR] Running warmup...")
        self.detect_only(dummy)
        print("[DETECTOR] Warmup completed")