# # # import os
# # # from dotenv import load_dotenv
# # # load_dotenv()
# # # BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# # # DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "app.db"))
# # # DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
# # # UPLOAD_VIDEO_FOLDER = os.path.join(BASE_DIR, "uploads", "videos")
# # # UPLOAD_PLATES_FOLDER = os.path.join(BASE_DIR, "uploads", "plates")
# # # LIVE_PREVIEW_FOLDER = os.path.join(BASE_DIR, "live_preview")
# # # OUTPUT_VIDEO_FOLDER = os.path.join(BASE_DIR, "processed_output", "videos")
# # # TEMP_FRAME_FOLDER = os.path.join(BASE_DIR, "temp_frames")
# # # ALLOWED_VIDEO_EXTENSIONS = (".mp4", ".mov", ".avi", ".mkv")
# # # DETECTIONS_DIR = os.path.join(BASE_DIR, "detections")
# # # VIDEO_CLIPS_DIR = os.path.join(BASE_DIR, "video_clips")
# # # LOGS_DIR = os.path.join(BASE_DIR, "logs")
# # # LOG_FRAME_PATH = os.path.join(LOGS_DIR, "violence_frame.jpg")

# # # for _directory in (
# # #     UPLOAD_VIDEO_FOLDER,
# # #     UPLOAD_PLATES_FOLDER,
# # #     LIVE_PREVIEW_FOLDER,
# # #     OUTPUT_VIDEO_FOLDER,
# # #     TEMP_FRAME_FOLDER,
# # #     DETECTIONS_DIR,
# # #     VIDEO_CLIPS_DIR,
# # #     LOGS_DIR,
# # # ):
# # #     os.makedirs(_directory, exist_ok=True)

# # # # ---------------------------------------------------------
# # # # Auth / JWT (was inline in auth.py)
# # # # ---------------------------------------------------------
# # # SECRET_KEY = os.getenv("SECRET_KEY")
# # # ALGORITHM = os.getenv("ALGORITHM", "HS256")
# # # ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
# # # ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
# # # ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# # # # ---------------------------------------------------------
# # # # Live surveillance / detection tuning (unchanged from config.py)
# # # # ---------------------------------------------------------
# # # PRE_EVENT_BUFFER_FRAMES = 60   # ~2 sec at 30 FPS
# # # POST_EVENT_DURATION = 5        # seconds
# # # FPS = 30

# # # MODEL_NAME = "yolov8n.pt"
# # # CONFIDENCE_THRESHOLD = 0.40
# # # IOU_THRESHOLD = 0.45
# # # MAX_DETECTIONS = 100
# # # USE_GPU = True
# # # USE_HALF_PRECISION = True
# # # TRACKER_TYPE = "bytetrack.yaml"
# # # TRACK_HIGH_THRESH = 0.5
# # # TRACK_LOW_THRESH = 0.1

# # # CAMERA_INDEX = 0
# # # FRAME_WIDTH = 1280
# # # FRAME_HEIGHT = 720
# # # CAMERA_FPS = 30
# # # SKIP_FRAMES = 1

# # # TARGET_CLASSES = None  # None => detect ALL classes
# # # MIN_DETECTION_DURATION = 2.0
# # # ALERT_COOLDOWN = 60          # seconds, per tracked object
# # # MIN_BBOX_AREA = 1500

# # # RECORD_VIDEO = True
# # # VIDEO_DURATION = 15
# # # VIDEO_PRE_BUFFER = 5
# # # VIDEO_CODEC = "mp4v"
# # # VIDEO_FPS = 20
# # # AUTO_RECORD_ON_DETECTION = True

# # # SAVE_SNAPSHOTS = True
# # # SNAPSHOT_QUALITY = 95
# # # SAVE_ANNOTATED_FRAMES = True

# # # # ===== Email (credentials read from .env, never hardcoded) =====
# # # ENABLE_EMAIL = True
# # # EMAIL_USER = os.environ.get("EMAIL_USER", "")
# # # EMAIL_PASS = os.environ.get("EMAIL_PASS", "")
# # # EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER", "")
# # # EMAIL_SUBJECT = "AI Surveillance Alert"
# # # EMAIL_ATTACH_SNAPSHOT = True

# # # LOG_TO_DATABASE = True
# # # MAX_DB_ENTRIES = 10000
# # # AUTO_CLEANUP_DATABASE = True

# # # SHOW_LIVE_FEED = True
# # # DISPLAY_FPS = True
# # # DISPLAY_CONFIDENCE = True
# # # DISPLAY_TRACK_ID = True
# # # DISPLAY_CLASS_NAME = True
# # # DISPLAY_TOTAL_COUNT = True
# # # WINDOW_NAME = "AI Surveillance System"

# # # BOX_COLOR = (0, 255, 0)
# # # TEXT_COLOR = (255, 255, 255)
# # # ALERT_COLOR = (0, 0, 255)
# # # BOX_THICKNESS = 2
# # # FONT_SCALE = 0.6

# # # PRINT_ALERTS = True
# # # CONSOLE_LOGGING = True
# # # ENABLE_SOUND_ALERT = False
# # # ENABLE_PERFORMANCE_LOGS = True
# # # SHOW_PROCESSING_TIME = False

# # # ENABLE_FACE_RECOGNITION = False
# # # ENABLE_ANOMALY_DETECTION = False
# # # ENABLE_ZONE_MONITORING = False
# # # ENABLE_INTRUSION_DETECTION = False

# # # # ===== Fire / Smoke Detection (Roboflow hosted model) =====
# # # ENABLE_FIRE_DETECTION = True
# # # ENABLE_VOILENCE_DETECTION = True
# # # ROBOFLOW_API_KEY = os.environ.get("ROBOFLOW_API_KEY", "")
# # # ROBOFLOW_API_URL = "https://serverless.roboflow.com"
# # # ROBOFLOW_MODEL_ID = "fire-detection-g9ebb/10"
# # # ROBOFLOW_WORKFLOW_ID = "general-segmentation-api-12"
# # # FIRE_CONFIDENCE_THRESHOLD = 0.45
# # # ROBOFLOW_WORKSPACE = "ayush-tiwari-mh18r"
# # # VOILENCE_CONFIDENCE_THRESHOLD = 0.70
# # # VOILENCE_CHECK_INTERVAL = 5
# # # ROBOFLOW_VOILENCE_MODEL_ID = "violence-not_violence-ziv7b/2"
# # # VOILENCE_ALERT_COOLDOWN = 15
# # # # network call to a hosted API -> don't run it every frame
# # # FIRE_CHECK_INTERVAL = 1        # kept for backward compat / other callers of FireDetector.should_run()
# # # FIRE_ALERT_COOLDOWN = 120      # seconds between fire emails
# # # FIRE_BOX_COLOR = (0, 0, 255)   # red boxes for fire/smoke

# # # # Time-based throttle for the background fire/violence workers
# # # # (services/surveillance/background_worker.py). Unlike the old
# # # # frame-count based FIRE_CHECK_INTERVAL, this doesn't drift if the
# # # # main loop's fps changes -- it's a real wall-clock minimum gap
# # # # between Roboflow calls. Tune this up if you still see latency;
# # # # tune it down (min 0.5-1.0s) if you want fire/violence caught faster
# # # # and your Roboflow plan/latency can take the extra calls.
# # # FIRE_CHECK_INTERVAL_SECONDS = 2.0
# # # VOILENCE_CHECK_INTERVAL_SECONDS = 1.0

# # # # Number-plate detector uses its own workspace/workflow ids -- kept
# # # # distinct from the fire detector's values above, exactly as in the
# # # # original Number_plate_detector.py (do not merge these).
# # # ROBOFLOW_PLATE_WORKSPACE = "ayush-tiwari-mh18r"
# # # ROBOFLOW_PLATE_WORKFLOW_ID = "general-segmentation-api"

# # # # ===== Rule Engine (crowd + incident correlation) =====
# # # CROWD_THRESHOLD = 8               # person count considered a "crowd"
# # # CROWD_ALERT_COOLDOWN = 300        # seconds between crowd-only emails
# # # LOG_LEVEL = "INFO"




# # # ==========================================================
# # # Central configuration for the Unified AI Surveillance & ANPR API
# # #
# # # This file merges:
# # #   - the original top-level config.py  (live surveillance tuning)
# # #   - the env vars that used to live inline in auth.py (JWT / admin login)
# # #   - the hardcoded Windows paths that used to live inline in
# # #     main.py / vehicle_detector.py / Number_plate_detector.py
# # #     (these are now relative to BASE_DIR so the project runs on
# # #     any machine / container, which is required to deploy to
# # #     Render or AWS -- this does NOT change any detection logic,
# # #     only where files are read from / written to)
# # # ==========================================================
# # import os
# # from dotenv import load_dotenv

# # load_dotenv()

# # # app/core/config.py -> project root is two levels up
# # BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# # # ---------------------------------------------------------
# # # Database (single SQLAlchemy DB - replaces db_manager.py's
# # # vehicle.db AND database.py's sqlite events.db)
# # # ---------------------------------------------------------
# # DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "app.db"))
# # DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# # # ---------------------------------------------------------
# # # Filesystem layout (was hardcoded C:\Users\ayvsh\... paths)
# # # ---------------------------------------------------------
# # UPLOAD_VIDEO_FOLDER = os.path.join(BASE_DIR, "uploads", "videos")
# # UPLOAD_PLATES_FOLDER = os.path.join(BASE_DIR, "uploads", "plates")
# # LIVE_PREVIEW_FOLDER = os.path.join(BASE_DIR, "live_preview")
# # OUTPUT_VIDEO_FOLDER = os.path.join(BASE_DIR, "processed_output", "videos")
# # TEMP_FRAME_FOLDER = os.path.join(BASE_DIR, "temp_frames")
# # ALLOWED_VIDEO_EXTENSIONS = (".mp4", ".mov", ".avi", ".mkv")

# # # Home-surveillance video pipeline (separate from the vehicle folders above)
# # SURVEILLANCE_UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads", "surveillance_videos")
# # SURVEILLANCE_OUTPUT_FOLDER = os.path.join(BASE_DIR, "processed_output", "surveillance")
# # # process every Nth frame for fire/crowd/violence during an uploaded-video
# # # scan -- these are expensive (2 hosted API calls + a YOLO pass) so we
# # # don't run them on every single frame of an offline video either.
# # SURVEILLANCE_VIDEO_FRAME_SKIP = 5

# # DETECTIONS_DIR = os.path.join(BASE_DIR, "detections")
# # VIDEO_CLIPS_DIR = os.path.join(BASE_DIR, "video_clips")
# # LOGS_DIR = os.path.join(BASE_DIR, "logs")
# # LOG_FRAME_PATH = os.path.join(LOGS_DIR, "violence_frame.jpg")

# # for _directory in (
# #     UPLOAD_VIDEO_FOLDER,
# #     UPLOAD_PLATES_FOLDER,
# #     LIVE_PREVIEW_FOLDER,
# #     OUTPUT_VIDEO_FOLDER,
# #     TEMP_FRAME_FOLDER,
# #     DETECTIONS_DIR,
# #     VIDEO_CLIPS_DIR,
# #     LOGS_DIR,
# #     SURVEILLANCE_UPLOAD_FOLDER,
# #     SURVEILLANCE_OUTPUT_FOLDER,
# # ):
# #     os.makedirs(_directory, exist_ok=True)

# # # ---------------------------------------------------------
# # # Auth / JWT (was inline in auth.py)
# # # ---------------------------------------------------------
# # SECRET_KEY = os.getenv("SECRET_KEY")
# # ALGORITHM = os.getenv("ALGORITHM", "HS256")
# # ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
# # ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
# # ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# # # ---------------------------------------------------------
# # # Live surveillance / detection tuning (unchanged from config.py)
# # # ---------------------------------------------------------
# # PRE_EVENT_BUFFER_FRAMES = 60   # ~2 sec at 30 FPS
# # POST_EVENT_DURATION = 5        # seconds
# # FPS = 30

# # MODEL_NAME = "yolov8n.pt"
# # CONFIDENCE_THRESHOLD = 0.40
# # IOU_THRESHOLD = 0.45
# # MAX_DETECTIONS = 100
# # USE_GPU = True
# # USE_HALF_PRECISION = True
# # TRACKER_TYPE = "bytetrack.yaml"
# # TRACK_HIGH_THRESH = 0.5
# # TRACK_LOW_THRESH = 0.1

# # CAMERA_INDEX = 0
# # FRAME_WIDTH = 1280
# # FRAME_HEIGHT = 720
# # CAMERA_FPS = 30
# # SKIP_FRAMES = 1

# # TARGET_CLASSES = None  # None => detect ALL classes
# # MIN_DETECTION_DURATION = 2.0
# # ALERT_COOLDOWN = 60          # seconds, per tracked object
# # MIN_BBOX_AREA = 1500

# # RECORD_VIDEO = True
# # VIDEO_DURATION = 15
# # VIDEO_PRE_BUFFER = 5
# # VIDEO_CODEC = "mp4v"
# # VIDEO_FPS = 20
# # AUTO_RECORD_ON_DETECTION = True

# # SAVE_SNAPSHOTS = True
# # SNAPSHOT_QUALITY = 95
# # SAVE_ANNOTATED_FRAMES = True

# # # ===== Email (credentials read from .env, never hardcoded) =====
# # ENABLE_EMAIL = True
# # EMAIL_USER = os.environ.get("EMAIL_USER", "")
# # EMAIL_PASS = os.environ.get("EMAIL_PASS", "")
# # EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER", "")
# # EMAIL_SUBJECT = "AI Surveillance Alert"
# # EMAIL_ATTACH_SNAPSHOT = True

# # LOG_TO_DATABASE = True
# # MAX_DB_ENTRIES = 10000
# # AUTO_CLEANUP_DATABASE = True

# # SHOW_LIVE_FEED = True
# # DISPLAY_FPS = True
# # DISPLAY_CONFIDENCE = True
# # DISPLAY_TRACK_ID = True
# # DISPLAY_CLASS_NAME = True
# # DISPLAY_TOTAL_COUNT = True
# # WINDOW_NAME = "AI Surveillance System"

# # BOX_COLOR = (0, 255, 0)
# # TEXT_COLOR = (255, 255, 255)
# # ALERT_COLOR = (0, 0, 255)
# # BOX_THICKNESS = 2
# # FONT_SCALE = 0.6

# # PRINT_ALERTS = True
# # CONSOLE_LOGGING = True
# # ENABLE_SOUND_ALERT = False
# # ENABLE_PERFORMANCE_LOGS = True
# # SHOW_PROCESSING_TIME = False

# # ENABLE_FACE_RECOGNITION = False
# # ENABLE_ANOMALY_DETECTION = False
# # ENABLE_ZONE_MONITORING = False
# # ENABLE_INTRUSION_DETECTION = False

# # # ===== Fire / Smoke Detection (Roboflow hosted model) =====
# # ENABLE_FIRE_DETECTION = True
# # ENABLE_VOILENCE_DETECTION = True
# # ROBOFLOW_API_KEY = os.environ.get("ROBOFLOW_API_KEY", "")
# # ROBOFLOW_API_URL = "https://serverless.roboflow.com"
# # ROBOFLOW_MODEL_ID = "fire-detection-g9ebb/10"
# # ROBOFLOW_WORKFLOW_ID = "general-segmentation-api-12"
# # FIRE_CONFIDENCE_THRESHOLD = 0.45
# # ROBOFLOW_WORKSPACE = "ayush-tiwari-mh18r"
# # VOILENCE_CONFIDENCE_THRESHOLD = 0.70
# # VOILENCE_CHECK_INTERVAL = 5
# # ROBOFLOW_VOILENCE_MODEL_ID = "violence-not_violence-ziv7b/2"
# # VOILENCE_ALERT_COOLDOWN = 15
# # # network call to a hosted API -> don't run it every frame
# # FIRE_CHECK_INTERVAL = 1        # kept for backward compat / other callers of FireDetector.should_run()
# # FIRE_ALERT_COOLDOWN = 120      # seconds between fire emails
# # FIRE_BOX_COLOR = (0, 0, 255)   # red boxes for fire/smoke

# # # Time-based throttle for the background fire/violence workers
# # # (services/surveillance/background_worker.py). Unlike the old
# # # frame-count based FIRE_CHECK_INTERVAL, this doesn't drift if the
# # # main loop's fps changes -- it's a real wall-clock minimum gap
# # # between Roboflow calls. Tune this up if you still see latency;
# # # tune it down (min 0.5-1.0s) if you want fire/violence caught faster
# # # and your Roboflow plan/latency can take the extra calls.
# # FIRE_CHECK_INTERVAL_SECONDS = 2.0
# # VOILENCE_CHECK_INTERVAL_SECONDS = 1.0

# # # Number-plate detector uses its own workspace/workflow ids -- kept
# # # distinct from the fire detector's values above, exactly as in the
# # # original Number_plate_detector.py (do not merge these).
# # ROBOFLOW_PLATE_WORKSPACE = "ayush-tiwari-mh18r"
# # ROBOFLOW_PLATE_WORKFLOW_ID = "general-segmentation-api"

# # # ===== Rule Engine (crowd + incident correlation) =====
# # CROWD_THRESHOLD = 8               # person count considered a "crowd"
# # CROWD_ALERT_COOLDOWN = 300        # seconds between crowd-only emails

# # LOG_LEVEL = "INFO"




# import os
# from dotenv import load_dotenv
 
# load_dotenv()
 
# # app/core/config.py -> project root is two levels up
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
 
# # ---------------------------------------------------------
# # Database (single SQLAlchemy DB - replaces db_manager.py's
# # vehicle.db AND database.py's sqlite events.db)
# # ---------------------------------------------------------
# DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "app.db"))
# DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
 
# # ---------------------------------------------------------
# # Filesystem layout (was hardcoded C:\Users\ayvsh\... paths)
# # ---------------------------------------------------------
# UPLOAD_VIDEO_FOLDER = os.path.join(BASE_DIR, "uploads", "videos")
# UPLOAD_PLATES_FOLDER = os.path.join(BASE_DIR, "uploads", "plates")
# LIVE_PREVIEW_FOLDER = os.path.join(BASE_DIR, "live_preview")
# OUTPUT_VIDEO_FOLDER = os.path.join(BASE_DIR, "processed_output", "videos")
# TEMP_FRAME_FOLDER = os.path.join(BASE_DIR, "temp_frames")
# ALLOWED_VIDEO_EXTENSIONS = (".mp4", ".mov", ".avi", ".mkv")
 
# # Home-surveillance video pipeline (separate from the vehicle folders above)
# SURVEILLANCE_UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads", "surveillance_videos")
# SURVEILLANCE_OUTPUT_FOLDER = os.path.join(BASE_DIR, "processed_output", "surveillance")
# # process every Nth frame for fire/crowd/violence during an uploaded-video
# # scan -- these are expensive (2 hosted API calls + a YOLO pass) so we
# # don't run them on every single frame of an offline video either.
# SURVEILLANCE_VIDEO_FRAME_SKIP = 5
 
# # Custom ByteTrack config for vehicle tracking (see the file for why) --
# # ultralytics' default track_buffer was too short for this footage and
# # was causing track-id churn / duplicate vehicle saves.
# VEHICLE_TRACKER_CONFIG = os.path.join(BASE_DIR, "custom_bytetrack.yaml")
 
# # A plate saved for this job within this many seconds of a very similar
# # plate is treated as the SAME physical vehicle re-read under a new
# # (churned) track id, not a second vehicle -- see save de-duplication
# # in services/vehicle_service.py.
# DUPLICATE_PLATE_TIME_WINDOW_SECONDS = 6.0
# DUPLICATE_PLATE_MAX_EDIT_DISTANCE = 2
 
# DETECTIONS_DIR = os.path.join(BASE_DIR, "detections")
# VIDEO_CLIPS_DIR = os.path.join(BASE_DIR, "video_clips")
# LOGS_DIR = os.path.join(BASE_DIR, "logs")
# LOG_FRAME_PATH = os.path.join(LOGS_DIR, "violence_frame.jpg")
 
# for _directory in (
#     UPLOAD_VIDEO_FOLDER,
#     UPLOAD_PLATES_FOLDER,
#     LIVE_PREVIEW_FOLDER,
#     OUTPUT_VIDEO_FOLDER,
#     TEMP_FRAME_FOLDER,
#     DETECTIONS_DIR,
#     VIDEO_CLIPS_DIR,
#     LOGS_DIR,
#     SURVEILLANCE_UPLOAD_FOLDER,
#     SURVEILLANCE_OUTPUT_FOLDER,
# ):
#     os.makedirs(_directory, exist_ok=True)
 
# # ---------------------------------------------------------
# # Auth / JWT (was inline in auth.py)
# # ---------------------------------------------------------
# SECRET_KEY = os.getenv("SECRET_KEY")
# ALGORITHM = os.getenv("ALGORITHM", "HS256")
# ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
# ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
# ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
 
# # ---------------------------------------------------------
# # Live surveillance / detection tuning (unchanged from config.py)
# # ---------------------------------------------------------
# PRE_EVENT_BUFFER_FRAMES = 60   # ~2 sec at 30 FPS
# POST_EVENT_DURATION = 5        # seconds
# FPS = 30
 
# MODEL_NAME = "yolov8n.pt"
# CONFIDENCE_THRESHOLD = 0.40
# IOU_THRESHOLD = 0.45
# MAX_DETECTIONS = 100
# USE_GPU = True
# USE_HALF_PRECISION = True
# TRACKER_TYPE = "bytetrack.yaml"
# TRACK_HIGH_THRESH = 0.5
# TRACK_LOW_THRESH = 0.1
 
# CAMERA_INDEX = 0
# FRAME_WIDTH = 1280
# FRAME_HEIGHT = 720
# CAMERA_FPS = 30
# SKIP_FRAMES = 1
 
# TARGET_CLASSES = None  # None => detect ALL classes
# MIN_DETECTION_DURATION = 2.0
# ALERT_COOLDOWN = 60          # seconds, per tracked object
# MIN_BBOX_AREA = 1500
 
# RECORD_VIDEO = True
# VIDEO_DURATION = 15
# VIDEO_PRE_BUFFER = 5
# VIDEO_CODEC = "mp4v"
# VIDEO_FPS = 20
# AUTO_RECORD_ON_DETECTION = True
 
# SAVE_SNAPSHOTS = True
# SNAPSHOT_QUALITY = 95
# SAVE_ANNOTATED_FRAMES = True
 
# # ===== Email (credentials read from .env, never hardcoded) =====
# ENABLE_EMAIL = True
# EMAIL_USER = os.environ.get("EMAIL_USER", "")
# EMAIL_PASS = os.environ.get("EMAIL_PASS", "")
# EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER", "")
# EMAIL_SUBJECT = "AI Surveillance Alert"
# EMAIL_ATTACH_SNAPSHOT = True
 
# LOG_TO_DATABASE = True
# MAX_DB_ENTRIES = 10000
# AUTO_CLEANUP_DATABASE = True
 
# SHOW_LIVE_FEED = True
# DISPLAY_FPS = True
# DISPLAY_CONFIDENCE = True
# DISPLAY_TRACK_ID = True
# DISPLAY_CLASS_NAME = True
# DISPLAY_TOTAL_COUNT = True
# WINDOW_NAME = "AI Surveillance System"
 
# BOX_COLOR = (0, 255, 0)
# TEXT_COLOR = (255, 255, 255)
# ALERT_COLOR = (0, 0, 255)
# BOX_THICKNESS = 2
# FONT_SCALE = 0.6
 
# PRINT_ALERTS = True
# CONSOLE_LOGGING = True
# ENABLE_SOUND_ALERT = False
# ENABLE_PERFORMANCE_LOGS = True
# SHOW_PROCESSING_TIME = False
 
# ENABLE_FACE_RECOGNITION = False
# ENABLE_ANOMALY_DETECTION = False
# ENABLE_ZONE_MONITORING = False
# ENABLE_INTRUSION_DETECTION = False
 
# # ===== Fire / Smoke Detection (Roboflow hosted model) =====
# ENABLE_FIRE_DETECTION = True
# ENABLE_VOILENCE_DETECTION = True
# ROBOFLOW_API_KEY = os.environ.get("ROBOFLOW_API_KEY", "")
# ROBOFLOW_API_URL = "https://serverless.roboflow.com"
# ROBOFLOW_MODEL_ID = "fire-detection-g9ebb/10"
# ROBOFLOW_WORKFLOW_ID = "general-segmentation-api-12"
# FIRE_CONFIDENCE_THRESHOLD = 0.45
# ROBOFLOW_WORKSPACE = "ayush-tiwari-mh18r"
# VOILENCE_CONFIDENCE_THRESHOLD = 0.70
# VOILENCE_CHECK_INTERVAL = 5
# ROBOFLOW_VOILENCE_MODEL_ID = "violence-not_violence-ziv7b/2"
# VOILENCE_ALERT_COOLDOWN = 15
# # network call to a hosted API -> don't run it every frame
# FIRE_CHECK_INTERVAL = 1        # kept for backward compat / other callers of FireDetector.should_run()
# FIRE_ALERT_COOLDOWN = 120      # seconds between fire emails
# FIRE_BOX_COLOR = (0, 0, 255)   # red boxes for fire/smoke
 
# # Time-based throttle for the background fire/violence workers
# # (services/surveillance/background_worker.py). Unlike the old
# # frame-count based FIRE_CHECK_INTERVAL, this doesn't drift if the
# # main loop's fps changes -- it's a real wall-clock minimum gap
# # between Roboflow calls. Tune this up if you still see latency;
# # tune it down (min 0.5-1.0s) if you want fire/violence caught faster
# # and your Roboflow plan/latency can take the extra calls.
# FIRE_CHECK_INTERVAL_SECONDS = 2.0
# VOILENCE_CHECK_INTERVAL_SECONDS = 1.0
 
# # Number-plate detector uses its own workspace/workflow ids -- kept
# # distinct from the fire detector's values above, exactly as in the
# # original Number_plate_detector.py (do not merge these).
# ROBOFLOW_PLATE_WORKSPACE = "ayush-tiwari-mh18r"
# ROBOFLOW_PLATE_WORKFLOW_ID = "general-segmentation-api"
 
# # ===== Rule Engine (crowd + incident correlation) =====
# CROWD_THRESHOLD = 4              # person count considered a "crowd"
# CROWD_ALERT_COOLDOWN = 300        # seconds between crowd-only emails
 
# LOG_LEVEL = "INFO"




# ==========================================================
# Central configuration for the Unified AI Surveillance & ANPR API
#
# This file merges:
#   - the original top-level config.py  (live surveillance tuning)
#   - the env vars that used to live inline in auth.py (JWT / admin login)
#   - the hardcoded Windows paths that used to live inline in
#     main.py / vehicle_detector.py / Number_plate_detector.py
#     (these are now relative to BASE_DIR so the project runs on
#     any machine / container, which is required to deploy to
#     Render or AWS -- this does NOT change any detection logic,
#     only where files are read from / written to)
# ==========================================================
import os
from dotenv import load_dotenv

load_dotenv()

# app/core/config.py -> project root is two levels up
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