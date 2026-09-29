# ==========================================================
# Correlates fire / violence / crowd detections into incidents,
# with cooldowns per incident type. Unchanged from Rule_engine.py.
# ==========================================================
import time

from app.core import config


class RuleEngine:
    def __init__(self):
        self.last_fire_alert = None
        self.last_crowd_alert = None
        self.last_voilence_alert = 0

    def evaluate(self, object_detections, fire_detections, voilence_detections):
        """
        Returns a list of incidents to act on, e.g.:
        [{"type": "fire", "severity": "critical", "person_count": 5,
          "fire_detections": [...]}]

        Fire always takes priority over a plain crowd incident, and a
        fire detected alongside a crowd is escalated to "critical".
        """
        incidents = []
        current_time = time.time()
        person_count = sum(1 for d in object_detections if d["class"] == "person")

        fire_present = len(fire_detections) > 0
        if fire_present:
            if self._cooldown_passed(self.last_fire_alert, config.FIRE_ALERT_COOLDOWN, current_time):
                severity = "critical" if person_count >= config.CROWD_THRESHOLD else "high"
                incidents.append({
                    "type": "fire",
                    "severity": severity,
                    "person_count": person_count,
                    "fire_detections": fire_detections
                })
                self.last_fire_alert = current_time

        voilence_present = len(voilence_detections) > 0
        if voilence_present:
            if self._cooldown_passed(self.last_voilence_alert, config.VOILENCE_ALERT_COOLDOWN, current_time):
                severity = "critical" if person_count >= 2 else "high"
                incidents.append({
                    "type": "voilence",
                    "severity": severity,
                    "person_count": person_count,
                    "fire_detections": [],
                    "voilence_detections": voilence_detections
                })
                self.last_voilence_alert = current_time
            return incidents
        elif person_count >= config.CROWD_THRESHOLD:
            if self._cooldown_passed(self.last_crowd_alert, config.CROWD_ALERT_COOLDOWN, current_time):
                incidents.append({
                    "type": "crowd",
                    "severity": "medium",
                    "person_count": person_count,
                    "fire_detections": []
                })
                self.last_crowd_alert = current_time

        return incidents

    @staticmethod
    def _cooldown_passed(last_time, cooldown, current_time):
        if last_time is None:
            return True
        return (current_time - last_time) > cooldown