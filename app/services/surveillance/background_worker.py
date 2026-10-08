import threading
import time
import traceback


class AsyncDetectorWorker:
    """Runs `detect_fn(frame) -> list[dict]` on a background thread,
    throttled to at most once every `min_interval_seconds`, always on
    the latest submitted frame."""

    def __init__(self, detect_fn, min_interval_seconds: float, name: str = "detector-worker"):
        self._detect_fn = detect_fn
        self._min_interval = max(min_interval_seconds, 0.0)
        self._name = name

        self._lock = threading.Lock()
        self._latest_frame = None          # next frame to process
        self._frame_available = threading.Event()
        self._stop_event = threading.Event()

        self._result_lock = threading.Lock()
        self._latest_result = None      # raw return value of detect_fn -- caller decides the "empty" shape
        self._result_version = 0        # bumped every time a NEW result is produced
        self._last_error: str = None
        self._last_run_time: float = 0.0

        self._thread = threading.Thread(target=self._run, name=name, daemon=True)
        self._thread.start()

    # ---------------- producer side (called from the main frame loop) ----------------

    def submit_frame(self, frame) -> None:
        """Non-blocking. Overwrites any not-yet-processed frame."""
        with self._lock:
            self._latest_frame = frame.copy()
        self._frame_available.set()

    def get_latest_result(self):
        """Non-blocking. Returns whatever detect_fn last returned
        (None if it hasn't run yet)."""
        with self._result_lock:
            return self._latest_result

    def get_latest_result_if_new(self, last_seen_version: int):
        """Non-blocking. Returns (is_new, result, version). Lets a
        caller that polls every frame process each worker result
        exactly once instead of re-handling the same result on every
        subsequent frame until the next one arrives."""
        with self._result_lock:
            if self._result_version != last_seen_version:
                return True, self._latest_result, self._result_version
            return False, None, last_seen_version

    def get_last_error(self):
        with self._result_lock:
            return self._last_error

    def stop(self, timeout: float = 2.0) -> None:
        self._stop_event.set()
        self._frame_available.set()  # wake the thread so it can exit
        self._thread.join(timeout=timeout)

    # ---------------- consumer side (the background thread) ----------------

    def _run(self) -> None:
        while not self._stop_event.is_set():
            # Block until a frame arrives (or stop() wakes us) -- no busy-waiting.
            self._frame_available.wait()
            if self._stop_event.is_set():
                break

            with self._lock:
                frame = self._latest_frame
                self._latest_frame = None
                self._frame_available.clear()

            if frame is None:
                continue

            # Time-based throttle: skip if we ran too recently, but
            # DON'T requeue this frame -- the next submit_frame() will
            # bring a fresher one anyway.
            elapsed = time.time() - self._last_run_time
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
                if self._stop_event.is_set():
                    break

            try:
                result = self._detect_fn(frame)
                with self._result_lock:
                    self._latest_result = result
                    self._result_version += 1
                    self._last_error = None
            except Exception as e:
                # Never let a bad API response / network blip kill the worker.
                traceback.print_exc()
                with self._result_lock:
                    self._last_error = str(e)
                    # Deliberately NOT bumping _result_version here -- a
                    # transient failure shouldn't be treated as "a new
                    # (empty) detection result" by a consumer using
                    # get_latest_result_if_new().
            finally:
                self._last_run_time = time.time()
