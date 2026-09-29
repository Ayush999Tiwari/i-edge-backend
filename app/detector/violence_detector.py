# ==========================================================
# Violence detector (Roboflow-hosted model). Unchanged logic from
# voilence_detector.py -- same parsing for classification / detection
# / nested-workflow response shapes, same confidence threshold.
#
# Renamed file for filename consistency. Class name (VoilenceDetector)
# and its public methods are kept exactly as-is since other modules
# reference them and renaming API surface isn't necessary. The
# tkinter-based `_run_standalone()` CLI test harness (image picker,
# `if __name__ == "__main__"`) was dropped: it was dead code never
# imported by the API, and importing tkinter in a server process is
# unwanted -- this does not touch any detection logic.
# ==========================================================
import cv2

from app.core import config

try:
    from inference_sdk import InferenceHTTPClient
except ImportError:
    InferenceHTTPClient = None


class VoilenceDetector:
    def __init__(self):
        self.enabled = config.ENABLE_VOILENCE_DETECTION
        self.client = None

        if not self.enabled:
            print("[VOILENCE] Detection disabled in config")
            return

        if InferenceHTTPClient is None:
            print("[VOILENCE ERROR] inference-sdk not installed")
            print("Run: pip install inference-sdk")
            self.enabled = False
            return

        if not config.ROBOFLOW_API_KEY:
            print("[VOILENCE ERROR] Missing ROBOFLOW_API_KEY")
            self.enabled = False
            return

        try:
            self.client = InferenceHTTPClient(
                api_url=config.ROBOFLOW_API_URL,
                api_key=config.ROBOFLOW_API_KEY
            )

            print("[VOILENCE] Roboflow client initialized")
            print(f"[VOILENCE] API URL : {config.ROBOFLOW_API_URL}")
            print(f"[VOILENCE] Model   : {config.ROBOFLOW_VOILENCE_MODEL_ID}")

        except Exception as e:
            print(f"[VOILENCE ERROR] Client init failed: {e}")
            self.enabled = False

    # -------------------------------------------------------
    # Normal detector
    # -------------------------------------------------------
    def detect(self, frame):
        if not self.enabled or self.client is None or frame is None:
            return []

        try:
            from PIL import Image
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(rgb)

            result = self.client.infer(
                image,
                model_id=config.ROBOFLOW_VOILENCE_MODEL_ID
            )

            return self._parse_predictions(result)

        except Exception as e:
            print(f"[VOILENCE ERROR] {e}")
            return []

    # -------------------------------------------------------
    # SNAPSHOT detector (used by the live surveillance pipeline)
    # -------------------------------------------------------
    def detect_snapshot(self, frame):
        """
        Returns:
        {
            "detected": bool,
            "confidence": float
        }
        """
        detections = self.detect(frame)

        if len(detections) == 0:
            return {"detected": False, "confidence": 0.0}

        best = max(detections, key=lambda x: x["confidence"])

        return {"detected": True, "confidence": float(best["confidence"])}

    # -------------------------------------------------------
    # Parse Roboflow response
    # -------------------------------------------------------
    def _parse_predictions(self, result):
        detections = []

        if isinstance(result, list):
            if not result:
                return detections
            result = result[0]

        # Classification format
        if "top" in result and "confidence" in result:
            if result["top"] == "violence":
                conf = float(result["confidence"])
                if conf >= config.VOILENCE_CONFIDENCE_THRESHOLD:
                    detections.append({"class": "violence", "confidence": conf})
            return detections

        predictions = result.get("predictions", {})

        # Detection list
        if isinstance(predictions, list):
            for pred in predictions:
                cls = pred.get("class", pred.get("class_name", ""))
                if cls == "violence":
                    conf = float(pred.get("confidence", 0))
                    if conf >= config.VOILENCE_CONFIDENCE_THRESHOLD:
                        detections.append({"class": "violence", "confidence": conf})
            return detections

        # Workflow nested response
        if isinstance(predictions, dict):
            nested = predictions.get("predictions")

            if isinstance(nested, list):
                for pred in nested:
                    cls = pred.get("class", pred.get("class_name", ""))
                    if cls == "violence":
                        conf = float(pred.get("confidence", 0))
                        if conf >= config.VOILENCE_CONFIDENCE_THRESHOLD:
                            detections.append({"class": "violence", "confidence": conf})
                return detections

            violence = predictions.get("violence")
            if violence:
                conf = float(violence.get("confidence", 0))
                if conf >= config.VOILENCE_CONFIDENCE_THRESHOLD:
                    detections.append({"class": "violence", "confidence": conf})

        return detections

    @staticmethod
    def _truncate_for_print(obj, max_len=120):
        if isinstance(obj, dict):
            return {k: VoilenceDetector._truncate_for_print(v, max_len) for k, v in obj.items()}
        if isinstance(obj, list):
            return [VoilenceDetector._truncate_for_print(v, max_len) for v in obj]
        if isinstance(obj, str) and len(obj) > max_len:
            return f"<{len(obj)} chars>"
        return obj