AI-Powered Surveillance & Vehicle Intelligence Platform
Backend Engineering Documentation
1. Business Requirements Document — BRD
1.1 Purpose

The system is an AI-powered video intelligence backend designed to transform conventional camera/video footage into actionable security and operational intelligence.

The backend provides two primary intelligence domains:

Vehicle Intelligence
Home/General Surveillance Intelligence

The platform allows authenticated users to upload and process video, execute AI detection pipelines, review detection results, and receive alerts for critical surveillance events.

1.2 Business Objectives

The platform aims to:

Automate vehicle detection from video.
Detect and identify vehicle number plates.
Extract number plates using OCR.
Detect fire/smoke events.
Detect abnormal crowd formation.
Detect violence/aggressive activity.
Maintain historical detection/event records.
Provide processed video evidence.
Notify the authenticated user when critical events occur.
Provide secure customer-specific access to surveillance jobs.
Support password and social authentication.
Provide a backend architecture suitable for cloud deployment.
1.3 Primary Users
User	Responsibilities
Customer	Upload videos, run detection, view results
Authenticated User	Access only their own processing jobs
System	Execute AI pipelines and persist results
AI Services	Perform detection/OCR/classification
Notification Service	Send critical-event alerts
1.4 Core Business Capabilities
Authentication
Registration using email or phone.
Login using email or phone.
Password authentication.
Google OAuth.
GitHub OAuth.
JWT-based session authentication.
Vehicle Intelligence
Vehicle detection.
Vehicle classification.
Number-plate detection.
Number-plate OCR.
Confidence tracking.
Duplicate detection handling.
Processed video generation.
Surveillance Intelligence
Fire detection.
Crowd detection.
Violence detection.
Event persistence.
Event confidence tracking.
Incident snapshots.
Processed video generation.
Notification

Critical events can trigger email alerts.

The recipient is dynamically determined from the currently authenticated user's registered email rather than from a globally configured customer email.

2. Functional Requirements
FR-01 — User Registration

The system shall allow a customer to register using:

Full Name
Email OR Phone Number
Password
Confirm Password

At least one identifier must be supplied.

FR-02 — User Login

The system shall allow authentication using:

Email + Password

or:

Phone + Password
FR-03 — Social Authentication

The system shall support:

Google OAuth
GitHub OAuth

OAuth-created users shall be associated with their respective provider identity.

FR-04 — Video Upload

Authenticated users shall be able to upload supported video formats.

Supported formats currently include:

.mp4
.mov
.avi
.mkv
FR-05 — Vehicle Detection

The system shall process uploaded vehicle footage and detect configured vehicle classes.

Detection information may include:

Vehicle Type
Confidence
Timestamp
FR-06 — Number Plate Intelligence

The system shall:

Detect number plates.
Extract plate regions.
Perform OCR.
Associate extracted plate information with detections.
FR-07 — Surveillance Detection

The surveillance pipeline shall support:

Fire
Crowd
Violence

Detection results are persisted against the corresponding surveillance job.

FR-08 — Alerting

When configured critical events occur, the system shall send an email alert to the authenticated user's registered email.

The system shall support event-specific cooldowns to avoid excessive notifications.

FR-09 — Job Tracking

Every uploaded video shall have a processing job.

The system shall expose job status such as:

uploaded
processing
completed
failed
FR-10 — Evidence

The system shall preserve references to:

processed video
incident snapshots
detection records
surveillance events

subject to the deployment/storage strategy.

3. Non-Functional Requirements
Performance

The backend should:

avoid unnecessary AI inference calls.
use frame sampling where configured.
apply cooldown mechanisms to external AI calls.
process long-running video jobs without blocking normal API requests where architecture permits.
Security

The backend must:

protect authenticated APIs.
hash passwords.
never store plaintext passwords.
use JWT authentication.
protect user-specific jobs from cross-user access.
keep API keys and credentials in environment variables.
Scalability

The architecture should allow:

API Server
      ↓
Job Processing
      ↓
AI Detection
      ↓
Database
      ↓
Notification

to be separated later without rewriting the entire application.

Availability

API failure should not corrupt previously persisted detection records.

Maintainability

AI models, API routes, services, repositories, configuration, authentication and database logic should remain separated.

4. High-Level Design — HLD
4.1 Architecture
                         ┌─────────────────────┐
                         │      Frontend       │
                         │ React / Vite        │
                         └──────────┬──────────┘
                                    │
                              HTTPS / REST
                                    │
                                    ▼
                    ┌────────────────────────────┐
                    │       FastAPI Backend      │
                    │                            │
                    │ API Layer                  │
                    │ Authentication             │
                    │ Authorization              │
                    │ Job Management             │
                    └─────────────┬──────────────┘
                                  │
                ┌─────────────────┼─────────────────┐
                │                 │                 │
                ▼                 ▼                 ▼
        ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
        │ Vehicle      │  │ Surveillance │  │ Auth         │
        │ Intelligence │  │ Intelligence │  │ Service      │
        └──────┬───────┘  └──────┬───────┘  └──────────────┘
               │                 │
               ▼                 ▼
        ┌──────────────┐  ┌──────────────┐
        │ YOLO         │  │ Fire Model   │
        │ Plate Model  │  │ Crowd Model  │
        │ OCR          │  │ Violence     │
        └──────────────┘  └──────┬───────┘
                                 │
                                 ▼
                         ┌──────────────┐
                         │ Notification │
                         │ Email        │
                         └──────────────┘

                         ┌──────────────┐
                         │ PostgreSQL   │
                         │ / Neon       │
                         └──────────────┘
5. Major Backend Components
5.1 API Layer

Responsible for:

HTTP endpoints
request validation
authentication dependencies
response serialization
HTTP error handling
5.2 Authentication Layer

Responsible for:

Registration
Login
Password hashing
JWT creation
JWT validation
Google OAuth
GitHub OAuth
Current-user resolution
5.3 Vehicle Intelligence Service

Responsible for orchestrating:

Video
 ↓
Vehicle Detector
 ↓
Plate Detector
 ↓
OCR
 ↓
Detection Persistence
 ↓
Processed Video
5.4 Surveillance Service

Responsible for:

Video
 ↓
Frame Sampling
 ↓
Fire Detection
 ↓
Crowd Detection
 ↓
Violence Detection
 ↓
Event Persistence
 ↓
Alerting
 ↓
Processed Evidence
6. Low-Level Design — LLD
6.1 Authentication Flow
Client
  │
  │ POST /auth/register
  ▼
Auth Router
  │
  ▼
Validate Request
  │
  ├── Email?
  └── Phone?
  │
  ▼
Check Existing User
  │
  ▼
Hash Password
  │
  ▼
Create User
  │
  ▼
Database
  │
  ▼
Generate JWT
  │
  ▼
Return Token + User
6.2 Login Flow
Client
   │
   │ identifier + password
   ▼
Auth API
   │
   ▼
Determine identifier
   │
   ├── Email
   │
   └── Phone
   │
   ▼
Find User
   │
   ▼
Verify Password
   │
   ▼
Create JWT
   │
   ▼
Return authenticated session
7. JWT Security Model

The frontend stores the JWT and sends:

Authorization: Bearer <token>

The backend:

Authorization Header
        ↓
Extract Bearer Token
        ↓
Decode JWT
        ↓
Read User ID
        ↓
Load User
        ↓
Authorize Request

Protected resources are therefore associated with the authenticated user.

8. Surveillance Processing Flow
POST /surveillance/upload
             │
             ▼
      Create Surveillance Job
             │
             ▼
       Store Uploaded Video
             │
             ▼
POST /surveillance/detect/{job_id}
             │
             ▼
       Validate Ownership
             │
             ▼
        Start Pipeline
             │
       ┌─────┼─────┐
       ▼     ▼     ▼
     Fire  Crowd Violence
       │     │     │
       └─────┼─────┘
             ▼
       Persist Events
             │
             ▼
       Critical Event?
          /       \
        Yes        No
         │          │
         ▼          ▼
       Email      Continue
         │
         ▼
   Processed Output
         │
         ▼
      Completed
9. Vehicle Processing Flow
Video Upload
     │
     ▼
Video Job
     │
     ▼
Frame Extraction
     │
     ▼
Vehicle Detection
     │
     ▼
Vehicle Tracking
     │
     ▼
Number Plate Detection
     │
     ▼
OCR
     │
     ▼
Duplicate Filtering
     │
     ▼
Database Persistence
     │
     ▼
Processed Video
10. Database Design

Current core entities include:

users
vehicle_detections
video_jobs
surveillance_events
surveillance_jobs
User
users
────────────────────────
id
full_name
email
phone_number
password_hash
auth_provider
provider_id
created_at
VideoJob
video_jobs
────────────────────────
id
original_filename
input_path
output_path
status
error_message
created_at
VehicleDetection
vehicle_detections
────────────────────────
id
vehicle_type
confidence
plate_number
timestamp
SurveillanceJob
surveillance_jobs
────────────────────────
id
original_filename
input_path
output_path
status

fire_detected
fire_events
max_fire_confidence

crowd_detected
crowd_events
max_person_count

violence_detected
violence_events
max_violence_confidence

alert_email
email_alerts_sent

error_message
created_at
SurveillanceEvent
surveillance_events
────────────────────────
id
event_type
confidence
clip_path
person_id
duration
timestamp
job_id
11. Database Relationship Model

Conceptually:

                ┌──────────────┐
                │    User      │
                └──────┬───────┘
                       │
                       │ owns
                       ▼
                ┌──────────────┐
                │ Video Job    │
                └──────────────┘


                ┌──────────────┐
                │ Surveillance │
                │     Job      │
                └──────┬───────┘
                       │
                       │ produces
                       ▼
                ┌──────────────┐
                │ Surveillance │
                │    Events    │
                └──────────────┘

For production, explicit user_id ownership relationships can be strengthened further if not already present in the final schema.

12. API Design
Authentication
POST /api/v1/auth/register
POST /api/v1/auth/login

GET /api/v1/auth/google
GET /api/v1/auth/google/callback

GET /api/v1/auth/github
GET /api/v1/auth/github/callback
Surveillance
POST /api/surveillance/upload

POST /api/surveillance/detect/{job_id}

GET /api/surveillance/status/{job_id}

GET /api/surveillance/results/{job_id}

GET /api/surveillance/video/{job_id}
API Request Example
Register
{
  "full_name": "John Doe",
  "email": "john@example.com",
  "password": "********"
}

Phone registration:

{
  "full_name": "John Doe",
  "phone_number": "+919999999999",
  "password": "********"
}
13. Detection Engine Architecture

The AI layer is intentionally separated from business/API logic.

                    AI Detection Layer
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
 Vehicle Detector     Plate Detector      OCR Reader
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                           ▼
                     Vehicle Service


                    Surveillance AI
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
   Fire Detector      Crowd Detector    Violence Detector
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                           ▼
                 Surveillance Service

This separation means the API layer does not need to know the internal implementation details of the models.

14. Alert Architecture
AI Detection
     │
     ▼
Event Detected
     │
     ▼
Threshold / Rule Check
     │
     ▼
Cooldown Check
     │
     ▼
Critical Event?
     │
     ▼
Email Alert Service
     │
     ▼
Current User Email

The sender is configured through:

EMAIL_USER
EMAIL_PASS

The recipient is derived from:

current_user.email

There should not be a global customer:

EMAIL_RECEIVER
15. Security Architecture
Password Security

Passwords are never stored directly.

Plain Password
      ↓
bcrypt
      ↓
password_hash
      ↓
Database

During login:

Password
   ↓
bcrypt verification
   ↓
Valid / Invalid
JWT

JWT contains the authenticated identity required to resolve the current user.

Protected endpoint:

Request
 ↓
Authorization Header
 ↓
JWT Validation
 ↓
User Lookup
 ↓
Ownership Check
 ↓
Controller
16. Authorization / Multi-Tenant Isolation

A customer must not be able to access another customer's processing job.

Example:

User A
 └── Job 101

User B
 └── Job 102

If User B requests:

GET /surveillance/video/101

the backend must verify ownership before returning the file.

This is particularly important because video and surveillance results can contain sensitive security footage.

17. Error Handling

The backend should return meaningful HTTP responses.

400 → Invalid request
401 → Authentication required / invalid token
403 → User does not own resource
404 → Resource not found
409 → Duplicate user / conflicting resource
422 → Validation error
500 → Internal processing failure

AI processing errors should also be persisted against the relevant job where possible.

18. Configuration Architecture

Runtime configuration is environment-driven.

Environment
     │
     ▼
app/core/config.py
     │
     ├── Database
     ├── JWT
     ├── OAuth
     ├── Email
     ├── AI APIs
     ├── Detection thresholds
     └── Storage paths

Secrets must remain outside source control.

19. Deployment Architecture

For the planned deployment:

                     INTERNET
                         │
              ┌──────────┴──────────┐
              │                     │
              ▼                     ▼
        Vercel Frontend        Render Backend
                                    │
                          ┌─────────┼─────────┐
                          │         │         │
                          ▼         ▼         ▼
                       FastAPI   AI Models  Email
                          │
                          ▼
                       Neon DB
                    PostgreSQL
20. Production Data Flow
User
 │
 ▼
Vercel Frontend
 │
 │ HTTPS
 ▼
FastAPI / Render
 │
 ├───────────────► Authentication
 │
 ├───────────────► PostgreSQL
 │
 ├───────────────► Vehicle AI
 │
 ├───────────────► Surveillance AI
 │
 ├───────────────► OCR
 │
 └───────────────► Email Provider
21. Deployment Considerations
Backend

Expected runtime:

uvicorn app.main:app --host 0.0.0.0 --port $PORT

Dependencies:

FastAPI
Uvicorn
SQLAlchemy
PostgreSQL driver
python-jose
passlib/bcrypt
python-dotenv
OpenCV
Ultralytics
PaddleOCR
Roboflow SDK

Actual requirements.txt should remain the authoritative dependency list.

22. Storage Architecture

Local development:

uploads/
processed_output/
detections/

For cloud production, local filesystem storage should not be treated as permanent storage.

A production storage architecture can evolve toward:

User Upload
     │
     ▼
Object Storage
     │
     ├── Original Videos
     ├── Processed Videos
     └── Incident Snapshots

while PostgreSQL stores metadata and references.

23. Observability

Recommended production observability:

API Logs
   │
   ├── Request
   ├── Response
   ├── Processing Time
   └── Error

AI Logs
   │
   ├── Model
   ├── Detection
   ├── Confidence
   └── Processing Time

Job Logs
   │
   ├── Uploaded
   ├── Processing
   ├── Completed
   └── Failed
24. Failure Scenarios
AI API unavailable
Roboflow unavailable
       ↓
Detection call fails
       ↓
Log error
       ↓
Persist job/event error
       ↓
Continue/terminate according to pipeline policy
Email unavailable

Email failure should not invalidate the underlying detection result.

Fire detected
    ↓
Database event saved
    ↓
Email attempt
    ↓
Email fails
    ↓
Detection remains persisted

This distinction is important:

Detection is the primary operation; notification is a secondary delivery mechanism.

25. Scalability Roadmap

Current architecture:

FastAPI
   │
   ├── API
   ├── AI Processing
   ├── Database
   └── Email

Future architecture:

                 API Gateway
                      │
             ┌────────┴────────┐
             ▼                 ▼
       Auth Service       Job Service
                              │
                              ▼
                         Job Queue
                              │
                 ┌────────────┼────────────┐
                 ▼            ▼            ▼
          Vehicle Worker  Fire Worker  Violence Worker
                 │            │            │
                 └────────────┼────────────┘
                              ▼
                         PostgreSQL
                              │
                              ▼
                        Object Storage
                              │
                              ▼
                      Notification Worker

Possible future infrastructure:

Redis
Celery / RQ
S3 / Cloudflare R2
PostgreSQL
Dedicated GPU Worker
26. System Design — Current vs Future
Current

Best suited for:

development
demonstration
initial deployment
limited concurrent users
Future

For larger workloads:

API ≠ AI Worker

The API should eventually submit:

Job → Queue → Worker

instead of performing heavy video inference inside the API process.

27. API Lifecycle
REQUEST
   │
   ▼
Middleware
   │
   ▼
Authentication
   │
   ▼
Validation
   │
   ▼
Router
   │
   ▼
Service
   │
   ▼
Repository / AI
   │
   ▼
Database
   │
   ▼
Response

This keeps responsibilities separated.

28. Backend Design Principles

The backend follows these architectural principles:

Separation of Concerns
Router
  ≠
Business Logic
  ≠
AI Logic
  ≠
Database Logic
Single Responsibility

Each service should have a clear responsibility.

Configuration Isolation

Secrets and environment-specific values remain outside application code.

Authentication First

Protected resources require an authenticated user.

Ownership Validation

Authentication alone is insufficient; resource ownership must also be checked.

AI Isolation

Model implementation should remain independent from API contracts.

Failure Isolation

Notification failure should not destroy successful detection results.

29. BRD → HLD → LLD Mapping
BUSINESS REQUIREMENT
        │
        ▼
     HLD
        │
        ▼
     SERVICES
        │
        ▼
      LLD
        │
        ▼
      APIs
        │
        ▼
    IMPLEMENTATION

Example:

Business Requirement:
"User should receive fire alerts."

        ↓

HLD:
Surveillance + Notification Service

        ↓

LLD:
Fire Detector
   ↓
Event Rule
   ↓
Cooldown
   ↓
Email Service
   ↓
Current User Email

        ↓

Implementation:
send_fire_alert(...)
30. Executive Summary

This backend provides a unified AI video intelligence platform combining secure customer authentication, vehicle intelligence, ANPR/OCR, surveillance analytics, event persistence, processed-video evidence and real-time email alerting.

The architecture separates:

API
Authentication
Business Services
AI Detection
Database
Notifications
Configuration

allowing the current system to operate as a unified backend while maintaining a clear migration path toward independently scalable AI workers, queues, object storage and dedicated inference infrastructure.

Recommended Documentation Structure in the GitHub Repo

Main README ko huge 30-page document mat bana dena. Repo mein ye professional structure rakh:

docs/
│
├── BRD.md
├── HLD.md
├── LLD.md
├── SYSTEM_DESIGN.md
├── API_DOCUMENTATION.md
├── DATABASE_DESIGN.md
├── SECURITY.md
├── DEPLOYMENT.md
└── ARCHITECTURE.md
│
README.md

Aur README.md mein sirf:

# AI-Powered Surveillance & Vehicle Intelligence Platform

## Overview

## Key Features

## Architecture

## Tech Stack

## Project Structure

## Authentication

## AI Pipelines

## API

## Database

## Local Development

## Environment Variables

## Deployment

## Security

## Future Architecture
