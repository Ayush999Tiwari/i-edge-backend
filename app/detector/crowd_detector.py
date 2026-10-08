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
