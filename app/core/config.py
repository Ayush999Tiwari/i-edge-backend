import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

# ---------------------------------------------------------
# Database
# ---------------------------------------------------------
DATABASE_PATH = os.environ.get(
    "DATABASE_PATH",
    os.path.join(BASE_DIR, "app.db"),
)

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


# ---------------------------------------------------------
# Filesystem layout
# ---------------------------------------------------------
UPLOAD_VIDEO_FOLDER = os.path.join(
    BASE_DIR,
    "uploads",
    "videos",
)

UPLOAD_PLATES_FOLDER = os.path.join(
    BASE_DIR,
    "uploads",
    "plates",
)

OUTPUT_VIDEO_FOLDER = os.path.join(
    BASE_DIR,
    "processed_output",
    "videos",
)

ALLOWED_VIDEO_EXTENSIONS = (
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
)


# ---------------------------------------------------------
# Home-surveillance video pipeline
# ---------------------------------------------------------
SURVEILLANCE_UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads",
    "surveillance_videos",
)

SURVEILLANCE_OUTPUT_FOLDER = os.path.join(
    BASE_DIR,
    "processed_output",
    "surveillance",
)

# Incident snapshots generated during surveillance processing
# by surveillance_service.py
DETECTIONS_DIR = os.path.join(
    SURVEILLANCE_OUTPUT_FOLDER,
    "detections",
)

# Process every Nth frame for fire/crowd/violence during
# uploaded-video scanning.
SURVEILLANCE_VIDEO_FRAME_SKIP = 5


# ---------------------------------------------------------
# Custom ByteTrack config for vehicle tracking
# ---------------------------------------------------------
VEHICLE_TRACKER_CONFIG = os.path.join(
    BASE_DIR,
    "custom_bytetrack.yaml",
)


# ---------------------------------------------------------
# Vehicle plate de-duplication
# ---------------------------------------------------------
DUPLICATE_PLATE_TIME_WINDOW_SECONDS = 6.0
DUPLICATE_PLATE_MAX_EDIT_DISTANCE = 2


# ---------------------------------------------------------
# Create required directories
# ---------------------------------------------------------
for _directory in (
    UPLOAD_VIDEO_FOLDER,
    UPLOAD_PLATES_FOLDER,
    OUTPUT_VIDEO_FOLDER,
    SURVEILLANCE_UPLOAD_FOLDER,
    SURVEILLANCE_OUTPUT_FOLDER,
    DETECTIONS_DIR,
):
    os.makedirs(_directory, exist_ok=True)


# ---------------------------------------------------------
# Auth / JWT
# ---------------------------------------------------------
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "change-this-secret-key",
)

ALGORITHM = os.getenv(
    "ALGORITHM",
    "HS256",
)

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "60",
    )
)


# ---------------------------------------------------------
# Admin
# ---------------------------------------------------------
ADMIN_EMAIL = os.getenv(
    "ADMIN_EMAIL",
    "",
)

ADMIN_PASSWORD = os.getenv(
    "ADMIN_PASSWORD",
    "",
)


# ---------------------------------------------------------
# Google OAuth
# ---------------------------------------------------------
GOOGLE_CLIENT_ID = os.getenv(
    "GOOGLE_CLIENT_ID",
    "",
)

GOOGLE_CLIENT_SECRET = os.getenv(
    "GOOGLE_CLIENT_SECRET",
    "",
)

GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI",
    "http://localhost:3000/api/v1/auth/google/callback",
)


# ---------------------------------------------------------
# GitHub OAuth
# ---------------------------------------------------------
GITHUB_CLIENT_ID = os.getenv(
    "GITHUB_CLIENT_ID",
    "",
)

GITHUB_CLIENT_SECRET = os.getenv(
    "GITHUB_CLIENT_SECRET",
    "",
)

GITHUB_REDIRECT_URI = os.getenv(
    "GITHUB_REDIRECT_URI",
    "http://localhost:3000/api/v1/auth/github/callback",
)


# ---------------------------------------------------------
# Frontend
# ---------------------------------------------------------
FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173",
)


# ---------------------------------------------------------
# Live surveillance / detection tuning
# ---------------------------------------------------------
FPS = 30

MODEL_NAME = "yolov8n.pt"

CONFIDENCE_THRESHOLD = 0.40
IOU_THRESHOLD = 0.45
MAX_DETECTIONS = 100

USE_GPU = True
USE_HALF_PRECISION = True

TRACKER_TYPE = "bytetrack.yaml"

TRACK_HIGH_THRESH = 0.5
TRACK_LOW_THRESH = 0.1

CAMERA_INDEX = 0

FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
CAMERA_FPS = 30

SKIP_FRAMES = 1

TARGET_CLASSES = None  # None => detect ALL classes

MIN_DETECTION_DURATION = 2.0

ALERT_COOLDOWN = 60

MIN_BBOX_AREA = 1500


# ---------------------------------------------------------
# Email
# ---------------------------------------------------------
ENABLE_EMAIL = True
EMAIL_USER = os.environ.get("EMAIL_USER", "")
EMAIL_PASS = os.environ.get("EMAIL_PASS", "")
EMAIL_SUBJECT = "AI Surveillance Alert"
EMAIL_ATTACH_SNAPSHOT = True


# ---------------------------------------------------------
# Database logging
# ---------------------------------------------------------
LOG_TO_DATABASE = True

MAX_DB_ENTRIES = 10000

AUTO_CLEANUP_DATABASE = True


# ---------------------------------------------------------
# Live display
# ---------------------------------------------------------
SHOW_LIVE_FEED = True

DISPLAY_FPS = True
DISPLAY_CONFIDENCE = True
DISPLAY_TRACK_ID = True
DISPLAY_CLASS_NAME = True
DISPLAY_TOTAL_COUNT = True

WINDOW_NAME = "AI Surveillance System"


# ---------------------------------------------------------
# Display colors
# ---------------------------------------------------------
BOX_COLOR = (0, 255, 0)

TEXT_COLOR = (255, 255, 255)

ALERT_COLOR = (0, 0, 255)

BOX_THICKNESS = 2

FONT_SCALE = 0.6


# ---------------------------------------------------------
# Logging / alerts
# ---------------------------------------------------------
PRINT_ALERTS = True

CONSOLE_LOGGING = True

ENABLE_SOUND_ALERT = False

ENABLE_PERFORMANCE_LOGS = True

SHOW_PROCESSING_TIME = False


# ---------------------------------------------------------
# Optional features
# ---------------------------------------------------------
ENABLE_FACE_RECOGNITION = False

ENABLE_ANOMALY_DETECTION = False

ENABLE_ZONE_MONITORING = False

ENABLE_INTRUSION_DETECTION = False


# ---------------------------------------------------------
# Fire / Smoke Detection - Roboflow
# ---------------------------------------------------------
ENABLE_FIRE_DETECTION = True

ENABLE_VOILENCE_DETECTION = True

ROBOFLOW_API_KEY = os.environ.get(
    "ROBOFLOW_API_KEY",
    "",
)

ROBOFLOW_API_URL = "https://serverless.roboflow.com"

ROBOFLOW_MODEL_ID = "fire-detection-g9ebb/10"

ROBOFLOW_WORKFLOW_ID = "general-segmentation-api-12"

FIRE_CONFIDENCE_THRESHOLD = 0.45

ROBOFLOW_WORKSPACE = "ayush-tiwari-mh18r"

VOILENCE_CONFIDENCE_THRESHOLD = 0.70

VOILENCE_CHECK_INTERVAL = 5

ROBOFLOW_VOILENCE_MODEL_ID = "violence-not_violence-ziv7b/2"

VOILENCE_ALERT_COOLDOWN = 15


# Network call to hosted API.
# Kept for backward compatibility / other FireDetector callers.
FIRE_CHECK_INTERVAL = 1

FIRE_ALERT_COOLDOWN = 120

FIRE_BOX_COLOR = (0, 0, 255)


# ---------------------------------------------------------
# Time-based throttle for background workers
# ---------------------------------------------------------
FIRE_CHECK_INTERVAL_SECONDS = 2.0

VOILENCE_CHECK_INTERVAL_SECONDS = 1.0


# ---------------------------------------------------------
# Number-plate detector
# ---------------------------------------------------------
ROBOFLOW_PLATE_WORKSPACE = "ayush-tiwari-mh18r"

ROBOFLOW_PLATE_WORKFLOW_ID = "general-segmentation-api"


# ---------------------------------------------------------
# Rule Engine
# ---------------------------------------------------------
CROWD_THRESHOLD = 8

CROWD_ALERT_COOLDOWN = 300


# ---------------------------------------------------------
# Logging level
# ---------------------------------------------------------
LOG_LEVEL = "INFO"
