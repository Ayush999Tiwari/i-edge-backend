# ==========================================================
# Fire/smoke detector (Roboflow-hosted workflow). Same throttling
# (should_run), same confidence threshold, same bbox math as the
# original -- the ONLY behavior change is where the temp JPEG for
# the Roboflow call gets written (see _TEMP_DIR below), to cut
# per-call latency without touching detection logic.
# ==========================================================
import cv2
import os
import tempfile

from app.core import config

# The original wrote the temp frame with tempfile's default dir,
# which is real disk. On Linux, /dev/shm is a RAM-backed tmpfs --
# writing/reading there is effectively free compared to a physical
# disk write, and it's a same-machine, single-call optimization with
# no change to what gets sent to Roboflow. Falls back to the normal
# system temp dir on platforms without /dev/shm (e.g. Windows), so
# this can never break anything, only speed it up where available.
_TEMP_DIR = "/dev/shm" if os.path.isdir("/dev/shm") else tempfile.gettempdir()

try:
    from inference_sdk import InferenceHTTPClient
except ImportError:
    InferenceHTTPClient = None


class FireDetector:

    def __init__(self):
        self.enabled = config.ENABLE_FIRE_DETECTION
        self.client = None
        self.frame_counter = 0

        if not self.enabled:
            print("[FIRE] Disabled")
            return

        if InferenceHTTPClient is None:
            print("[FIRE ERROR] pip install inference-sdk")
            self.enabled = False
            return

        try:
            self.client = InferenceHTTPClient(
                api_url=config.ROBOFLOW_API_URL,
                api_key=config.ROBOFLOW_API_KEY
            )

            print("[FIRE] Roboflow workflow ready")
            print(f"[FIRE] Workspace : {config.ROBOFLOW_WORKSPACE}")
            print(f"[FIRE] Workflow  : {config.ROBOFLOW_WORKFLOW_ID}")

        except Exception as e:
            print(e)
            self.enabled = False

    def should_run(self):
        self.frame_counter += 1
        return self.frame_counter % config.FIRE_CHECK_INTERVAL == 0

    def detect(self, frame):

        if not self.enabled:
            return []

        temp_path = None

        try:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False, dir=_TEMP_DIR) as f:
                temp_path = f.name

            cv2.imwrite(temp_path, frame)

            result = self.client.run_workflow(
                workspace_name=config.ROBOFLOW_WORKSPACE,
                workflow_id=config.ROBOFLOW_WORKFLOW_ID,
                images={"image": temp_path},
                parameters={"classes": "Fire, fire"},
                use_cache=False
            )

            return self.parse(result)

        except Exception as e:
            print(f"[FIRE ERROR] {e}")
            return []

        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    def parse(self, result):

        detections = []

        if isinstance(result, list):
            result = result[0]

        preds = result.get("predictions", {}).get("predictions", [])

        for p in preds:

            conf = float(p.get("confidence", 0))

            if conf < config.FIRE_CONFIDENCE_THRESHOLD:
                continue

            x = p["x"]
            y = p["y"]
            w = p["width"]
            h = p["height"]

            detections.append({
                "class": p.get("class", "fire"),
                "confidence": conf,
                "bbox": [
                    x - w / 2,
                    y - h / 2,
                    x + w / 2,
                    y + h / 2
                ]
            })

        return detections