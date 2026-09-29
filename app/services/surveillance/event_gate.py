# ==========================================================
# Event-gated trigger for the violence detector (avoids calling the
# hosted violence model every frame). Unchanged from event_gate.py.
# ==========================================================
import logging

logger = logging.getLogger(__name__)


class EventGate:
    """
    Manages event-based violence detection triggers.
    Ensures only one API call per crowd event and waits for scene clearance.
    """

    def __init__(self, trigger_frames=15, reset_frames=30):
        self.trigger_frames = trigger_frames      # ~0.5s at 30FPS
        self.reset_frames = reset_frames          # ~1s at 30FPS

        self.consecutive_person_frames = 0
        self.empty_frames = 0
        self.event_active = False
        self.snapshot_taken = False
        self.best_frame = None                    # numpy array, not file path

    def update(self, person_count: int, frame):
        """Update gate state based on current frame's person count."""
        if person_count >= 2:
            self.consecutive_person_frames += 1
            self.empty_frames = 0

            if not self.event_active and not self.snapshot_taken:
                self.best_frame = frame.copy()

            if self.consecutive_person_frames >= self.trigger_frames:
                self.event_active = True

        else:
            self.consecutive_person_frames = 0

            if self.event_active or self.consecutive_person_frames > 0:
                self.empty_frames += 1

            if self.empty_frames >= self.reset_frames:
                self.reset()

    def should_trigger(self) -> bool:
        """Returns True only once per event when threshold is first met."""
        if self.event_active and not self.snapshot_taken:
            return True
        return False

    def get_snapshot(self):
        """Returns the captured numpy frame for API processing."""
        if self.best_frame is None:
            logger.warning("[EVENT_GATE] No snapshot available despite trigger")
            return None
        return self.best_frame

    def mark_snapshot_sent(self):
        """Call this after successfully sending snapshot to prevent duplicates."""
        self.snapshot_taken = True
        logger.info("[EVENT_GATE] Snapshot sent. Waiting for scene clearance.")

    def reset(self):
        """Reset all state to allow new events."""
        self.consecutive_person_frames = 0
        self.empty_frames = 0
        self.event_active = False
        self.snapshot_taken = False
        self.best_frame = None
        logger.debug("[EVENT_GATE] State reset. Ready for new event.")