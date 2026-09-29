# ==========================================================
# Pre/post-event incident clip recorder. Unchanged from
# incident_recorder.py.
# ==========================================================
import cv2
import os
import time
from collections import deque

from app.core import config


class IncidentRecorder:
    def __init__(self):
        self.buffer = deque(maxlen=config.PRE_EVENT_BUFFER_FRAMES)
        self.recording = False
        self.out = None
        self.start_time = None
        self.filename = None

    def add_frame(self, frame):
        self.buffer.append(frame.copy())

    def start(self, frame_shape, incident_type):
        if self.recording:
            return self.filename
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        os.makedirs(config.VIDEO_CLIPS_DIR, exist_ok=True)
        self.filename = os.path.join(config.VIDEO_CLIPS_DIR, f"{incident_type}_{timestamp}.mp4")
        h, w = frame_shape[:2]
        self.out = cv2.VideoWriter(
            self.filename, cv2.VideoWriter_fourcc(*"mp4v"), config.FPS, (w, h)
        )
        for buffered_frame in self.buffer:
            self.out.write(buffered_frame)
        self.recording = True
        self.start_time = time.time()
        print(f"[RECORDER] Started incident recording: {self.filename}")
        return self.filename

    def write(self, frame):
        if self.recording and self.out:
            self.out.write(frame)

    def should_stop(self):
        if not self.recording:
            return False
        elapsed = time.time() - self.start_time
        return elapsed >= config.POST_EVENT_DURATION

    def stop(self):
        if self.recording:
            if self.out:
                self.out.release()
            print(f"[RECORDER] Saved incident clip: {self.filename}")
            saved_file = self.filename
            self.recording = False
            self.out = None
            self.filename = None
            self.start_time = None
            return saved_file
        return None

    def cleanup(self):
        if self.out:
            self.out.release()
        self.recording = False
        self.out = None

    @property
    def current_file(self):
        return self.filename