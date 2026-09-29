# ==========================================================
# Rolling pre-buffer video recorder. Unchanged from video_recorder.py.
# ==========================================================
import cv2
import time
from collections import deque
from datetime import datetime

from app.core import config


class VideoRecorder:
    """Manage video recording with pre-buffer"""

    def __init__(self):
        self.recording = False
        self.writer = None
        self.buffer = deque(maxlen=int(config.VIDEO_PRE_BUFFER * config.VIDEO_FPS))
        self.record_start_time = None
        self.current_filename = None

    def add_frame(self, frame):
        self.buffer.append(frame.copy())

    def start_recording(self, frame_shape):
        if self.recording:
            return self.current_filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_filename = f"{config.VIDEO_CLIPS_DIR}/clip_{timestamp}.mp4"
        fourcc = cv2.VideoWriter_fourcc(*config.VIDEO_CODEC)
        self.writer = cv2.VideoWriter(
            self.current_filename, fourcc, config.VIDEO_FPS, (frame_shape[1], frame_shape[0])
        )
        for buffered_frame in self.buffer:
            self.writer.write(buffered_frame)
        self.recording = True
        self.record_start_time = time.time()
        print(f"[VIDEO] Recording started: {self.current_filename}")
        return self.current_filename

    def write_frame(self, frame):
        if self.recording and self.writer:
            self.writer.write(frame)

    def should_stop(self):
        if not self.recording:
            return False
        return (time.time() - self.record_start_time) > config.VIDEO_DURATION

    def stop_recording(self):
        if self.recording and self.writer:
            self.writer.release()
            self.recording = False
            print(f"[VIDEO] Recording saved: {self.current_filename}")
            filename = self.current_filename
            self.current_filename = None
            return filename
        return None

    def cleanup(self):
        if self.writer:
            self.writer.release()
            self.writer = None