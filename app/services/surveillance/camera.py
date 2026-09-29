# ==========================================================
# Webcam / video-file input handler for the live surveillance
# pipeline. Unchanged logic from the original camera.py.
# ==========================================================
import cv2
from tkinter import Tk, filedialog

from app.core import config


class CameraHandler:
    """Manage Webcam or Video File operations"""

    def __init__(self, camera_index=None):
        self.camera_index = camera_index if camera_index is not None else config.CAMERA_INDEX
        self.cap = None
        self.frame_count = 0
        self.source_type = None
        self.video_path = None
        self._initialize_source()

    def _initialize_source(self):
        print("\n========== INPUT SOURCE ==========")
        print("1. Webcam")
        print("2. Video File")
        print("==================================")
        choice = input("Select option (1/2): ").strip()
        if choice == "2":
            self._initialize_video()
        else:
            self._initialize_camera()

    def _initialize_camera(self):
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            raise Exception(f"[CAMERA ERROR] Camera {self.camera_index} not detected!")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.source_type = "webcam"
        print(f"[CAMERA] Opened webcam {self.camera_index}")
        print(f"[CAMERA] Resolution: {actual_width}x{actual_height}")

    def _initialize_video(self):
        root = Tk()
        root.withdraw()
        video_path = filedialog.askopenfilename(
            title="Select CCTV Video",
            filetypes=[("Video Files", "*.mp4 *.avi *.mov *.mkv"), ("All Files", "*.*")],
        )
        root.destroy()
        if not video_path:
            raise Exception("[VIDEO ERROR] No video selected.")
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise Exception(f"[VIDEO ERROR] Failed to open:\n{video_path}")
        self.video_path = video_path
        self.source_type = "video"
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        print(f"[VIDEO] Loaded: {video_path}")
        print(f"[VIDEO] Resolution: {width}x{height}")
        print(f"[VIDEO] FPS: {fps:.2f}")

    def read_frame(self):
        if self.cap is None:
            return False, None
        ret, frame = self.cap.read()
        if ret:
            self.frame_count += 1
        return ret, frame

    def should_skip_frame(self):
        return self.frame_count % config.SKIP_FRAMES != 0

    def get_frame_size(self):
        if self.cap is None:
            return 0, 0
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return width, height

    def is_opened(self):
        return self.cap is not None and self.cap.isOpened()

    def release(self):
        if self.cap:
            self.cap.release()
        if self.source_type == "video":
            print("[VIDEO] Released")
        else:
            print("[CAMERA] Released")