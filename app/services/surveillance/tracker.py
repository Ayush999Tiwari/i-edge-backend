# ==========================================================
# Per-object alert-cooldown tracker. Unchanged from tracker.py.
# ==========================================================
import time
from collections import defaultdict

from app.core import config


class DetectionTracker:
    """Track detections and manage alert cooldowns"""

    def __init__(self):
        self.person_timers = defaultdict(lambda: {
            "first_seen": None,
            "last_alerted": None,
            "total_frames": 0
        })
        self.active_persons = set()

    def update(self, person_id):
        current_time = time.time()
        if self.person_timers[person_id]["first_seen"] is None:
            self.person_timers[person_id]["first_seen"] = current_time
        self.person_timers[person_id]["total_frames"] += 1
        self.active_persons.add(person_id)
        duration = current_time - self.person_timers[person_id]["first_seen"]
        return duration

    def should_alert(self, person_id, duration):
        current_time = time.time()
        last_alert = self.person_timers[person_id]["last_alerted"]
        if duration < config.MIN_DETECTION_DURATION:
            return False
        if last_alert is None or (current_time - last_alert) > config.ALERT_COOLDOWN:
            self.person_timers[person_id]["last_alerted"] = current_time
            return True
        return False

    def cleanup_inactive(self, active_ids):
        inactive = self.active_persons - active_ids
        for person_id in inactive:
            if person_id in self.person_timers:
                del self.person_timers[person_id]
        self.active_persons = active_ids

    def get_stats(self, person_id):
        if person_id in self.person_timers:
            return {
                "total_frames": self.person_timers[person_id]["total_frames"],
                "first_seen": self.person_timers[person_id]["first_seen"],
                "last_alerted": self.person_timers[person_id]["last_alerted"]
            }
        return None

    def reset(self):
        self.person_timers.clear()
        self.active_persons.clear()