🚀 StorageX: Distributed Video Transcoding System
StorageX is a full-stack, distributed video management platform. It allows users to upload high-definition videos, which are then processed asynchronously by background workers to ensure a smooth viewing experience. The architecture is built for scale, using a microservices approach.

💡 The Idea
The core problem StorageX solves is the "heavy lift" of video processing. Instead of making a user wait for a video to upload and convert in their browser, StorageX:

Ingests the raw file to private S3 storage.

Queues a job in RabbitMQ.

Processes the video (transcoding to 720p/H.264) on a separate worker node using FFmpeg.

Delivers the processed video via a secure, high-speed player.

🛠 Technology Stack
Frontend
Next.js 16: React framework for the dashboard and authentication.

Tailwind CSS: High-contrast, "Neo-brutalism" design (Black/White/Bold).

TypeScript: Type-safe API interactions.

Backend (API & Worker)
FastAPI: High-performance Python API.

SQLAlchemy: ORM for PostgreSQL database management.

FFmpeg: The engine used by workers to transcode and compress video.

Pydantic: Data validation and schemas.

DevOps & Infrastructure
Docker & Docker Compose: Orchestrates the entire 7-container stack.

RabbitMQ: Message broker for handling the background task queue.

MinIO: High-performance, S3-compatible object storage.

PostgreSQL: Relational database for user data and video metadata.

🧠 System Logic & Architecture
Auth Layer: Uses JWT (JSON Web Tokens) with Bcrypt password hashing.

Role-Based Access (RBAC):

Users: Can upload, view, and delete their own videos.

Admins: Can view and manage the entire library across all users.

Storage Logic: Uses a partitioned folder structure:

raw/user\_{id}/: Original uploads.

processed/user\_{id}/: Final, optimized versions.

Worker Lifecycle:

The worker listens for video_tasks.

Downloads from the "Raw" bucket -> Transcodes locally -> Uploads to "Processed" bucket -> Updates Database status to completed.

🚀 How to Use
Requirements
Docker Desktop (Windows/Mac/Linux)

Git

Installation
Clone the repository:

Bash

git clone https://github.com/your-username/storagex.git
cd storagex
Start the entire stack:

Bash

docker-compose up --build -d
Access the application:

Frontend: http://localhost:3000

API Docs (Swagger): http://localhost:8000/docs

MinIO Console: http://localhost:9001 (User: minioadmin | Pass: minioadmin)

Default Admin Account
The system automatically seeds a Super Admin account on the first launch:

Email: <write youre email>

Password: <write youre password>

📁 Project Structure
Plaintext

.
├── backend/
│ ├── routers/ # API Endpoints (Users, Videos)
│ ├── models.py # SQLAlchemy Database Models
│ ├── schemas.py # Pydantic Data Models
│ ├── worker.py # FFmpeg Background Worker
│ ├── main.py # FastAPI Entry Point & Startup Seeding
│ └── Dockerfile
├── frontend/
│ ├── app/ # Next.js Pages (Dashboard, Login, Register)
│ ├── lib/ # API Service Layer
│ └── Dockerfile
└── docker-compose.yml # Infrastructure Orchestration
