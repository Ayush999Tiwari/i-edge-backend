from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    UniqueConstraint,
)

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String, nullable=False)

    email = Column(
        String,
        unique=True,
        index=True,
        nullable=True,
    )

    phone_number = Column(
        String,
        unique=True,
        index=True,
        nullable=True,
    )

    password_hash = Column(
        String,
        nullable=True,
    )

    auth_provider = Column(
        String,
        default="password",
        nullable=False,
    )

    provider_id = Column(
        String,
        nullable=True,
        index=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    __table_args__ = (
        UniqueConstraint(
            "auth_provider",
            "provider_id",
            name="uq_user_provider",
        ),
    )


class VehicleDetection(Base):
    __tablename__ = "vehicle_detections"

    id = Column(Integer, primary_key=True, index=True)

    vehicle_type = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)

    plate_number = Column(String, nullable=True)

    timestamp = Column(
        DateTime,
        default=datetime.utcnow,
    )


class VideoJob(Base):
    __tablename__ = "video_jobs"

    id = Column(Integer, primary_key=True, index=True)

    original_filename = Column(String)
    input_path = Column(String)

    output_path = Column(
        String,
        nullable=True,
    )

    status = Column(
        String,
        default="uploaded",
    )

    error_message = Column(
        String,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )


class SurveillanceEvent(Base):
    __tablename__ = "surveillance_events"

    id = Column(Integer, primary_key=True, index=True)

    event_type = Column(String)

    confidence = Column(Float)

    clip_path = Column(
        String,
        nullable=True,
    )

    person_id = Column(
        Integer,
        nullable=True,
    )

    duration = Column(
        Float,
        nullable=True,
    )

    timestamp = Column(
        DateTime,
        default=datetime.utcnow,
    )

    job_id = Column(
        Integer,
        nullable=True,
        index=True,
    )


class SurveillanceJob(Base):
    __tablename__ = "surveillance_jobs"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    original_filename = Column(String)

    input_path = Column(String)

    output_path = Column(
        String,
        nullable=True,
    )

    status = Column(
        String,
        default="uploaded",
    )

    # ---------------- Detection results ----------------

    fire_detected = Column(
        Boolean,
        default=False,
    )

    fire_events = Column(
        Integer,
        default=0,
    )

    max_fire_confidence = Column(
        Float,
        default=0.0,
    )

    crowd_detected = Column(
        Boolean,
        default=False,
    )

    crowd_events = Column(
        Integer,
        default=0,
    )

    max_person_count = Column(
        Integer,
        default=0,
    )

    violence_detected = Column(
        Boolean,
        default=False,
    )

    violence_events = Column(
        Integer,
        default=0,
    )

    max_violence_confidence = Column(
        Float,
        default=0.0,
    )

    # ---------------- Email alert tracking ----------------

    # Email of the authenticated user who started this scan.
    # This is populated by the backend from the JWT user,
    # never from frontend input.
    alert_email = Column(
        String,
        nullable=True,
    )

    # Number of emails that were actually sent successfully.
    email_alerts_sent = Column(
        Integer,
        default=0,
    )

    # ---------------- Errors ----------------

    error_message = Column(
        String,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )