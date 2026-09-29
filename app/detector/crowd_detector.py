# ==========================================================
# "Crowd detection" was never a separate model in the original
# project -- it was a rule inside Rule_engine.py:
#     elif person_count >= config.CROWD_THRESHOLD: ... "crowd" incident
#
# The target API asks for a standalone POST /api/surveillance/crowd
# endpoint, so this module exposes that exact rule as a small,
# reusable function on top of the *unchanged* PersonDetector, rather
# than inventing a new detection algorithm.
# ==========================================================
from app.core import config
from app.detector.person_detector import PersonDetector


def detect_crowd(frame, person_detector: PersonDetector) -> dict:
    """Runs the same person detection used elsewhere, and applies the
    same CROWD_THRESHOLD rule the RuleEngine already used."""
    results = person_detector.detect_and_track(frame)
    detections = person_detector.get_detections(results)
    person_count = person_detector.count_persons(detections)

    return {
        "person_count": person_count,
        "crowd_detected": person_count >= config.CROWD_THRESHOLD,
        "threshold": config.CROWD_THRESHOLD,
        "detections": detections,
    }