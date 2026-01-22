# 🚀 StorageX — AI-Powered Distributed Video System

**StorageX** is a full-stack, distributed video management platform that goes beyond simple hosting. It combines high-performance transcoding with a **local generative AI pipeline** to automatically analyze, understand, and summarize video content.

Instead of just storing files, StorageX **watches** them. Using a multi-model AI approach, it identifies content (coding tutorials, gaming clips, nature vlogs) and generates concise, human-readable summaries—all running locally without external APIs.

The system relies on a **microservices architecture** to ensure scalability, resilience, and a smooth, non-blocking user experience.

---

## 💡 The Evolution: From Storage to Intelligence

High-quality video processing is resource-intensive. StorageX solves this by offloading work to background workers. But we didn't stop at processing; we solved **content discovery**:

1. **Ingest & Transcode:** Videos are uploaded to private S3 storage and processed asynchronously via **RabbitMQ** and **FFmpeg**.
2. **Visual Analysis (The Eyes):** A worker extracts keyframes and uses **Moondream** (Vision AI) to detect UI elements, code editors, game HUDs, or natural scenery.
3. **Contextual Synthesis (The Brain):** **Llama 3.2** aggregates these visual cues to write a coherent summary, distinguishing between a *"React Tutorial"* and a *"Minecraft Gameplay"* video.
4. **Zero-Hallucination Protocol:** We engineered neutral prompting strategies to prevent the AI from "guessing," ensuring accurate descriptions for both technical and non-technical content.

---

## ✨ Key Features & Improvements

### 🧠 Advanced AI Features
- **Multi-Model Local Pipeline:** Orchestrates **Moondream** (Vision) and **Llama 3.2** (Text) locally via **Ollama**.
- **Smart Regenerate:** Users can force-retry AI analysis if the initial result is unsatisfactory or an error occurs.
- **Hallucination Guard:** Custom prompt engineering prevents common AI errors (like seeing "robots" in nature videos).
- **Redis Caching:** AI summaries are cached for 24 hours to reduce load, with a "Force Refresh" override.

### 🎨 UX & Frontend
- **Sliding Insight Drawer:** A non-intrusive sidebar displays AI summaries without disrupting the video grid layout.
- **Neo-Brutalism Design:** High-contrast, bold UI built with **Next.js 16** and **Tailwind CSS**.
- **Smart State Management:** Real-time UI updates handle "Thinking," "View," and "Retry" states seamlessly via WebSockets.
- **Public Video Gallery:** A searchable, open-access feed with category filtering (Gaming, Tech, Music) and full-text search via **Elasticsearch**.

### 🛠️ Backend & Infrastructure
- **Cascading Cleanups:** Hard-delete logic ensures that when a video is removed, all associated AI summaries, thumbnails, and files are instantly wiped from the database and storage.
- **Dynamic Transcoding:** Workers automatically adjust FFmpeg parameters based on user-selected target resolution (1080p, 720p, 480p).
- **Smart Storage Quotas:** 500MB free tier for regular users with visual tracking; unlimited for Admins.

---

## 🛠 Technology Stack

### Frontend
- **Next.js 16** — React framework (App Router) for dashboard & auth.
- **TypeScript** — Strict type safety across the application.
- **Tailwind CSS** — High-contrast design system.
- **Framer Motion** — Smooth animations for sidebars and notifications.

### Backend (API & Intelligence)
- **FastAPI** — High-performance Python API.
- **Ollama** — Local AI Model Runner (Llama 3.2 + Moondream).
- **Redis** — High-speed caching for AI results and session data.
- **SQLAlchemy** — ORM for PostgreSQL.
- **FFmpeg** — Video transcoding engine.

### Infrastructure (DevOps)
- **Docker Compose** — Full stack orchestration (**9 containers**).
- **RabbitMQ** — Message broker for background jobs.
- **MinIO** — High-performance, S3-compatible object storage.
- **PostgreSQL** — Primary relational database.
- **Elasticsearch** — Full-text search engine.

---

## 🧠 System Architecture: "The Storyteller Pipeline"

1. **Ingest:** API receives upload -> Saves raw file to MinIO -> Pushes task to RabbitMQ.
2. **Process:** Worker consumes task -> Downloads video -> Transcodes via FFmpeg.
3. **Analyze:**
   - **Frame Extraction:** Snapshots taken at 20%, 50%, and 80%.
   - **Vision Pass:** Moondream identifies visual elements (e.g., "Code editor," "Forest").
   - **Reasoning Pass:** Llama 3.2 synthesizes cues into a summary (e.g., "User is debugging Python code").
4. **Index & Notify:** Public videos indexed in Elasticsearch. WebSockets notify the frontend.

---

## 🚀 Getting Started

### Requirements
- **Docker Desktop** (Windows / macOS / Linux) - *Must support Linux containers*
- **Git**
- **8GB+ RAM** (Recommended for running AI models locally)

### Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/your-username/storagex.git](https://github.com/your-username/storagex.git)
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

- **RabbitMQ Management:**
  - http://localhost:15672
  -	guest / guest

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
    |   ├── ai_utils.py     # AI Pipeline (Vision + Logic + Retry)
    │   ├── models.py       # SQLAlchemy Database Models
    │   ├── cache.py        # Redis Caching Layer
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
