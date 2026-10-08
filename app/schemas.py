from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class DetectionItem(BaseModel):
    vehicle_type: str
    vehicle_id: str
    plate_number: str
    confidence: float
    timestamp: float


class AnalyticsResponse(BaseModel):
    vehicle_count: int
    plates_recognized: int
    detections: List[DetectionItem]


class VideoStatusResponse(BaseModel):
    id: int
    original_filename: str
    input_path: str
    output_path: Optional[str]
    status: str
    confidence_score: float
    created_at: datetime
    plate_number: Optional[str] = None
    confidence: Optional[float] = None
    vehicle_id: Optional[str] = None
    vehicles_detected: Optional[int] = None
    detail: Optional[str] = None

    class Config:
        from_attributes = True


class VideoUploadResponse(BaseModel):
    id: int
    vehicle_id: str
    status: str


# ==========================================================
# AUTH
# ==========================================================

class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)

    # Frontend sends one of these depending on authMethod.
    email: Optional[str] = None
    phone_number: Optional[str] = None

    password: str = Field(min_length=8)

    def validate_identifier(self):
        if not self.email and not self.phone_number:
            raise ValueError("Email or phone number is required.")

        if self.email:
            self.email = self.email.strip().lower()

        if self.phone_number:
            self.phone_number = self.phone_number.strip()

        return self


class LoginRequest(BaseModel):
    identifier: str
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: "UserResponse"


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: Optional[str] = None
    phone_number: Optional[str] = None
    auth_provider: str

    class Config:
        from_attributes = True
