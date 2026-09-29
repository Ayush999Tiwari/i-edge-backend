# ==========================================================
# Live surveillance orchestrator (person + fire + violence + crowd,
# on a webcam/video feed). This is the SurveillanceSystem class that
# used to live directly inside main.py.
#
# Frame-processing logic (detection, drawing, alerting, rule
# evaluation) is UNCHANGED. Three real changes vs. the original:
#
# 1. Person-detection alerts used to be written via database.py's raw
#    sqlite3 DatabaseManager.log_event(); they now go through the
#    shared SQLAlchemy database as a SurveillanceEvent row, per the
#    "one database only" requirement. Nothing about *when* an alert
#    fires, its cooldown, or its content was changed.
#
# 2. Fire and violence detection (both hosted Roboflow API calls) no
#    longer run synchronously inside process_frame(). They now run on
#    AsyncDetectorWorker background threads (see background_worker.py)
#    so a slow/blocked network call can never stall frame reads. The
#    detection algorithms/thresholds themselves are untouched -- only
#    *when* the call happens (background thread, latest-frame-only,
#    time-throttled) changed. See background_worker.py's docstring
#    for exactly what guarantees this gives.
#
# 3. No persistent detections/ or video_clips/ folder. Incident video
#    clip recording (IncidentRecorder) and person-alert snapshots are
#    removed entirely -- a person-tracking alert now just logs the
#    event with no image. A fire/crowd/violence INCIDENT still gets a
#    snapshot, because the email alert needs a file to attach, but
#    that snapshot is now a short-lived Python tempfile (auto-cleaned
#    right after the email is sent), not a file kept in a project-
#    managed folder.
# ==========================================================
import os
import tempfile
from datetime import datetime

import cv2

from app.core import config
from app.database import SessionLocal
from app.models import SurveillanceEvent
from app.detector.person_detector import PersonDetector
from app.detector.fire_detector import FireDetector
from app.detector.violence_detector import VoilenceDetector
from app.services.surveillance.camera import CameraHandler
from app.services.surveillance.rule_engine import RuleEngine
from app.services.surveillance.tracker import DetectionTracker
from app.services.surveillance.email_alert import EmailAlertManager
from app.services.surveillance.event_gate import EventGate
from app.services.surveillance.background_worker import AsyncDetectorWorker


def _log_surveillance_event(event_type, confidence, clip_path=None, person_id=None, duration=0.0):
    if not config.LOG_TO_DATABASE:
        return
    db = SessionLocal()
    try:
        db.add(SurveillanceEvent(
            event_type=event_type,
            confidence=confidence or 0.0,
            clip_path=clip_path,
            person_id=person_id,
            duration=duration or 0.0,
        ))
        db.commit()
    finally:
        db.close()


class SurveillanceSystem:
    def __init__(self):
        self.print_banner()
        self.camera = CameraHandler()
        self.detector = PersonDetector()
        self.fire_detector = FireDetector() if config.ENABLE_FIRE_DETECTION else None
        self.rule_engine = RuleEngine()
        self.tracker = DetectionTracker()
        self.email = EmailAlertManager() if config.ENABLE_EMAIL else None
        self.paused = False
        self.frame_count = 0
        self.previous_time = datetime.now()
        self.print_settings()

        self.voilence_detector = VoilenceDetector() if config.ENABLE_VOILENCE_DETECTION else None
        self.event_gate = EventGate(
            trigger_frames=15,   # ~0.5 sec at 30 FPS
            reset_frames=30      # ~1.0 sec at 30 FPS
        ) if config.ENABLE_VOILENCE_DETECTION else None

        # Background workers -- see background_worker.py. Fire is
        # submitted every processed frame (the worker itself throttles
        # to FIRE_CHECK_INTERVAL_SECONDS); violence is only submitted
        # when the EventGate actually triggers, since that's already
        # a rare, gated call. Both are non-blocking either way.
        self._fire_worker = AsyncDetectorWorker(
            detect_fn=self.fire_detector.detect,
            min_interval_seconds=config.FIRE_CHECK_INTERVAL_SECONDS,
            name="fire-worker",
        ) if self.fire_detector and self.fire_detector.enabled else None
        self._fire_result_version = 0

        self._voilence_worker = AsyncDetectorWorker(
            detect_fn=self.voilence_detector.detect_snapshot,
            min_interval_seconds=config.VOILENCE_CHECK_INTERVAL_SECONDS,
            name="voilence-worker",
        ) if self.voilence_detector and self.voilence_detector.enabled else None
        self._voilence_result_version = 0

    def shutdown(self):
        """Stops the background workers cleanly. Call this if you ever
        tear down a SurveillanceSystem instance (e.g. on app shutdown)."""
        if self._fire_worker:
            self._fire_worker.stop()
        if self._voilence_worker:
            self._voilence_worker.stop()

    def print_banner(self):
        print("=" * 60)
        print("AI VIDEO SURVEILLANCE & PERSON/FIRE/VIOLENCE MODULE")
        print("=" * 60)

    def print_settings(self):
        print(f"[INIT] Model: {config.MODEL_NAME}")
        if config.TARGET_CLASSES is None:
            print("[INIT] Detecting: ALL OBJECTS")
        else:
            print(f"[INIT] Detecting: {config.TARGET_CLASSES}")
        print(f"[INIT] Fire Detection: {config.ENABLE_FIRE_DETECTION}")
        print(f"[INIT] Violence Detection: {config.ENABLE_VOILENCE_DETECTION} (Event-Gated)")
        print(f"[INIT] Email: {config.ENABLE_EMAIL}")
        print("=" * 60)

    def process_frame(self, frame):
        results = self.detector.detect_and_track(frame)
        detections = self.detector.get_detections(results)
        annotated_frame = frame.copy()
        active_ids = set()

        for detection in detections:
            obj_id = detection["id"]
            class_name = detection["class"]
            confidence = detection["confidence"]
            bbox = detection["bbox"]
            if obj_id is None:
                obj_id = -1
            active_ids.add(obj_id)
            duration = self.tracker.update(obj_id)
            self.draw_detection(annotated_frame, bbox, obj_id, class_name, confidence)
            if self.tracker.should_alert(obj_id, duration):
                self.handle_alert(obj_id, class_name, confidence, duration)

        self.tracker.cleanup_inactive(active_ids)

        # ---- Fire: submit every frame (non-blocking); the worker itself
        # throttles actual Roboflow calls to FIRE_CHECK_INTERVAL_SECONDS,
        # always working on the most recently submitted frame. ----
        fire_detections = []
        if self._fire_worker:
            self._fire_worker.submit_frame(frame)
            is_new, result, version = self._fire_worker.get_latest_result_if_new(self._fire_result_version)
            if is_new:
                self._fire_result_version = version
                fire_detections = result or []
            # NOTE: deliberately NOT reusing a stale (not-new) result on
            # frames between worker runs -- the original only treated a
            # frame as "fire present" on the exact check frame, and
            # RuleEngine.evaluate() is called every frame below. Reusing
            # a stale detection would make a fire that's no longer in
            # view look "present" for longer than it actually was.
            for fire in fire_detections:
                self.draw_fire_detection(annotated_frame, fire)

        # ---- Violence: EventGate decides WHEN to check (unchanged
        # gating logic); the actual Roboflow call now runs on the
        # background worker instead of blocking this frame. ----
        voilence_detections = []
        if self.voilence_detector and self.event_gate:
            person_count = self.detector.count_persons(detections)
            self.event_gate.update(person_count, frame)

            if self.event_gate.should_trigger():
                snapshot = self.event_gate.get_snapshot()
                if snapshot is not None and self._voilence_worker:
                    self._voilence_worker.submit_frame(snapshot)
                # Mark sent immediately, exactly like the original --
                # this is what stops the gate from submitting the same
                # event's snapshot again every subsequent frame.
                self.event_gate.mark_snapshot_sent()

            if self._voilence_worker:
                is_new, result, version = self._voilence_worker.get_latest_result_if_new(self._voilence_result_version)
                if is_new:
                    self._voilence_result_version = version
                    if result and result.get("detected", False):
                        voilence_detections.append({
                            "class": "violence",
                            "confidence": result["confidence"],
                            "bbox": None
                        })
                        print(f"[VIOLENCE] Event triggered! Confidence: {result['confidence']:.2f}")

        incidents = self.rule_engine.evaluate(detections, fire_detections, voilence_detections)
        for incident in incidents:
            self.handle_incident(incident, annotated_frame)

        return annotated_frame, len(detections)

    def draw_detection(self, frame, bbox, obj_id, class_name, confidence):
        x1, y1, x2, y2 = map(int, bbox)
        cv2.rectangle(frame, (x1, y1), (x2, y2), config.BOX_COLOR, config.BOX_THICKNESS)
        label = f"{class_name}"
        if config.DISPLAY_TRACK_ID:
            label += f" ID:{obj_id}"
        if config.DISPLAY_CONFIDENCE:
            label += f" {confidence:.2f}"
        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE, config.TEXT_COLOR, 2)

    def draw_fire_detection(self, frame, fire):
        x1, y1, x2, y2 = map(int, fire["bbox"])
        cv2.rectangle(frame, (x1, y1), (x2, y2), config.FIRE_BOX_COLOR, config.BOX_THICKNESS)
        label = f"{fire['class']} {fire['confidence']:.2f}"
        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE, config.FIRE_BOX_COLOR, 2)

    def handle_alert(self, obj_id, class_name, confidence, duration):
        """Person-tracking alert. No snapshot is kept for these (there's
        no persistent folder to keep it in, and nothing emails it) --
        just the event row itself."""
        _log_surveillance_event(
            event_type=class_name,
            confidence=confidence,
            clip_path=None,
            person_id=obj_id,
            duration=duration,
        )

        if config.PRINT_ALERTS:
            print(f"[ALERT] {class_name} (ID:{obj_id}) Conf:{confidence:.2f} Time:{duration:.1f}s")

    def handle_incident(self, incident, frame):
        incident_type = incident["type"]
        severity = incident["severity"]
        person_count = incident["person_count"]

        top_confidence = 0.0
        if incident.get("fire_detections"):
            top_confidence = max(d["confidence"] for d in incident["fire_detections"])
        elif incident.get("voilence_detections"):
            top_confidence = max(d["confidence"] for d in incident["voilence_detections"])

        # A snapshot is only needed if we're actually going to email it --
        # written to a short-lived tempfile, not a project-managed folder,
        # and cleaned up right after sending.
        snapshot_path = None
        if self.email:
            fd, snapshot_path = tempfile.mkstemp(suffix=f"_{incident_type}.jpg")
            os.close(fd)
            cv2.imwrite(snapshot_path, frame)

        _log_surveillance_event(
            event_type=incident_type,
            confidence=top_confidence,
            clip_path=None,
        )

        if self.email and snapshot_path:
            try:
                if incident_type == "fire":
                    self.email.send_fire_alert(snapshot_path, top_confidence, person_count, severity)
                elif incident_type == "crowd":
                    self.email.send_crowd_alert(snapshot_path, person_count, severity)
                elif incident_type == "voilence":
                    self.email.send_voilence_alert(snapshot_path, top_confidence, person_count, severity)
            except Exception as e:
                print(f"[EMAIL ERROR] Failed to send alert: {e}")
            finally:
                if os.path.exists(snapshot_path):
                    try:
                        os.remove(snapshot_path)
                    except OSError:
                        pass

        print(f"[INCIDENT] {incident_type} | severity={severity} | people={person_count}")

    def draw_system_info(self, frame, count):
        if config.DISPLAY_TOTAL_COUNT:
            cv2.putText(frame, f"Objects: {count}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        return frame

    def generate_frames(self):
        """MJPEG generator -- unchanged from main.py's generate_frames()."""
        while True:
            ret, frame = self.camera.read_frame()
            if not ret:
                continue
            self.frame_count += 1
            frame, count = self.process_frame(frame)
            frame = self.draw_system_info(frame, count)
            ok, buffer = cv2.imencode(".jpg", frame)
            if not ok:
                continue
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
            )