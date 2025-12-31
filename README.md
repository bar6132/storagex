# 🚀 StorageX — Distributed Video Transcoding System

**StorageX** is a full-stack, distributed video management platform designed to handle high-definition video uploads and processing at scale.  
Instead of blocking the user during heavy video operations, StorageX offloads processing to background workers, ensuring a smooth and responsive user experience.

The system is built using a **microservices architecture**, making it scalable, resilient, and production-ready.

---

## 💡 Problem & Solution

High-quality video processing is expensive and slow when handled synchronously in the browser or API layer.

**StorageX solves this by:**

1. Uploading raw video files to private S3-compatible storage.
2. Queuing a background job using RabbitMQ.
3. Transcoding videos asynchronously (720p / H.264) using FFmpeg.
4. Delivering the optimized video through a secure, high-performance player.

This approach eliminates long upload waits and enables horizontal scaling.

## ✨ Key Features

- **Real-Time Updates (WebSockets):** The dashboard updates instantly when a video finishes processing—no page refreshes required. The backend pushes events directly to the client.
- **Smart Storage Quotas:** - Regular users get a **500MB** free tier limit with visual usage tracking.
  Admins have **unlimited** storage and can manage all user content.
- **Dynamic Quality Selection:** Users can choose their target resolution (1080p, 720p, 480p) before uploading. The worker dynamically adjusts the FFmpeg transcoding parameters.
- **Admin "Super View":** Special admin accounts can see every video in the system, monitor global usage, and perform hard deletions to clean up storage.

## 🛠 Technology Stack

### Frontend
- **Next.js 16** — React framework for dashboard, authentication, and routing  
- **TypeScript** — Type-safe API communication  
- **Tailwind CSS** — High-contrast *Neo-brutalism* design (Black / White / Bold)

### Backend (API & Workers)
- **FastAPI** — High-performance Python API  
- **SQLAlchemy** — ORM for PostgreSQL  
- **Pydantic** — Data validation & schemas  
- **FFmpeg** — Video transcoding engine

### DevOps & Infrastructure
- **Docker & Docker Compose** — Full stack orchestration (7 containers)  
- **RabbitMQ** — Message broker for background jobs  
- **MinIO** — High-performance, S3-compatible object storage  
- **PostgreSQL** — Relational database for users & video metadata  

---

## 🧠 System Architecture & Logic

### Authentication
- JWT-based authentication  
- Secure password hashing with **Bcrypt**

### Role-Based Access Control (RBAC)
- **Users**
  - Upload videos
  - View their own library
  - Delete their own content
- **Admins**
  - View and manage all videos across the system


🔄 Event-Driven Worker Lifecycle

1. **Ingest:** API receives upload -> Saves raw file to MinIO -> Pushes task to RabbitMQ.
2. **Process:** Worker consumes task -> Downloads video -> Transcodes via FFmpeg.
3. **Notify:** - Worker sends a webhook to the API (`/internal/notify`).
   - API pushes a **WebSocket event** to the specific connected user.
   - Frontend creates a "Toast" notification or updates the video card status instantly.

---

## 🚀 Getting Started

### Requirements
- Docker Desktop (Windows / macOS / Linux)
- Git

### Installation
Clone the repository:
git clone https://github.com/your-username/storagex.git
cd storagex

## 🚀 Running the Full Stack
Start the entire StorageX stack using Docker Compose:
docker-compose up --build -d

## 🌐 Access Points
Once the stack is running, you can access the following services locally:

- **Frontend (Dashboard):**
  - http://localhost:3000

- **API Documentation (Swagger):**
  - http://localhost:8000/docs

- **MinIO Console:**
  - http://localhost:9001
  - Username: minioadmin
  - Password: minioadmin

## 🔐 Default Admin Account
On first launch, StorageX automatically seeds a Super Admin account:
Email: <your-email>
Password: <your-password>

## 🔐 ⚠️ Security Notice:
These credentials are intended for local development only.
Always change or disable default credentials in production environments.

## 📁 Project Structure
```
    .
    ├── backend/
    │   ├── routers/        # API Endpoints (Users, Videos)
    │   ├── models.py       # SQLAlchemy Database Models
    │   ├── schemas.py      # Pydantic Data Models
    │   ├── worker.py       # FFmpeg Background Worker
    │   ├── main.py         # FastAPI Entry Point & Startup Seeding
    │   └── Dockerfile
    ├── frontend/
    │   ├── app/            # Next.js Pages (Dashboard, Login, Register)
    │   ├── lib/            # API Service Layer
    │   └── Dockerfile
    └── docker-compose.yml  # Infrastructure Orchestration
```
