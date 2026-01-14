# Credlyse Backend 🎓

**Credlyse** is an intelligent educational platform backend that transforms YouTube playlists into structured courses with AI-generated quizzes, real-time progress tracking, and automated certification.

Built with **FastAPI**, **PostgreSQL**, **SQLAlchemy (Async)**, and **OpenAI/Gemini**.

---

## 🚀 Features

### 1. 🔐 Authentication & Roles
- **JWT Authentication**: Secure access with access tokens.
- **Role-Based Access Control (RBAC)**:
  - `STUDENT`: Can enroll, watch videos, take quizzes, claim certificates.
  - `CREATOR`: Can import playlists, publish courses, view analytics.
  - `ADMIN`: System management.

### 2. 📚 Course Management
- **YouTube Integration**: Import entire playlists just by providing the YouTube Playlist ID.
- **Metadata Sync**: Automatically fetches video titles, descriptions, durations, and thumbnails.
- **Publishing Workflow**: Draft -> Published states.

### 3. 🧠 Content Intelligence (AI)
- **Transcript Analysis**: Fetches transcripts using `youtube-transcript-api`.
- **Hybrid AI Pipeline**:
  - **Primary**: Uses **OpenAI (GPT-4o-mini)** to generate quizzes from transcripts.
  - **Fallback**: Uses **Google Gemini 2.0 Flash** to analyze video content directly if transcripts are missing.
- **Quiz Generation**: Automatically creates 5-question multiple-choice quizzes for educational content.

### 4. 📈 Student Progress Tracking
- **Real-time Tracking**: Designed for Chrome Extension integration.
- **Heartbeat System**: Updates watch time every 30 seconds.
- **Strict Completion**:
  - Must watch 98% of the video.
  - Must pass the quiz (score ≥ 75%) to mark as complete.

### 5. 🏆 Certification
- **Eligibility Engine**: Strict checks (Enrollment + 100% Watched + All Quizzes Passed).
- **PDF Generation**: Auto-generates professional PDF certificates using `reportlab`.
- **Verification**: Public endpoint to verify certificate validity via QR code.

### 6. 📊 Creator Analytics
- **Dashboard**: Detailed insights for creators.
- **Metrics**: Student enrollment date, completion %, average quiz scores.

---

## 🛠️ Tech Stack

- **Framework**: FastAPI (Python 3.12+)
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy (Async) + Alembic (Migrations)
- **AI/LLM**: OpenAI API, Google Gemini (via LangChain)
- **PDF**: ReportLab
- **Validation**: Pydantic
- **Testing**: Pytest

---

## 📂 Project Structure

```
credlyse-backend/
├── app/
│   ├── api/            # API Endpoints (v1)
│   │   └── v1/endpoints/
│   │       ├── auth.py         # Login/Signup
│   │       ├── courses.py      # Playlist management
│   │       ├── analysis.py     # AI processing
│   │       ├── progress.py     # Student tracking
│   │       ├── certificates.py # PDF generation
│   │       └── analytics.py    # Creator dashboard
│   ├── core/           # Config & Database setup
│   ├── models/         # SQLAlchemy Database Models
│   ├── schemas/        # Pydantic Schemas (Request/Response)
│   ├── services/       # Business Logic Layer
│   │   ├── ai_service.py          # OpenAI/Gemini logic
│   │   ├── course_service.py      # YouTube API logic
│   │   ├── processing_service.py  # Background tasks
│   │   ├── progress_service.py    # Grading & Tracking
│   │   └── certificate_service.py # PDF generation
│   └── main.py         # App Entry Point
├── static/             # Generated Certificates
├── alembic/            # Database Migrations
└── requirements.txt    # Dependencies
```

---

## 🗄️ Database Schema

### Users & Profiles
- **User**: `id`, `email`, `password_hash`, `role` (STUDENT/CREATOR)
- **CreatorProfile**: `user_id`, `bio`, `social_links`

### Content
- **Playlist**: `id`, `youtube_id`, `title`, `creator_id`, `is_published`
- **Video**: `id`, `playlist_id`, `youtube_id`, `transcript`, `quiz_data` (JSON)

### Progress & Enrollment
- **Enrollment**: `user_id`, `playlist_id`, `is_completed`, `certificate_url`
- **VideoProgress**: `enrollment_id`, `video_id`, `watch_status`, `quiz_score`
- **Certificate**: `id` (UUID), `user_id`, `playlist_id`, `pdf_url`

---

## 🔌 API Endpoints

### Authentication
- `POST /auth/signup`: Register new user.
- `POST /auth/login`: Get JWT access token.

### Courses (Creator)
- `POST /courses/import`: Import YouTube playlist.
- `POST /courses/{id}/analyze`: Trigger AI analysis (Background task).
- `POST /courses/{id}/publish`: Make course public.
- `GET /courses/{id}/analytics`: View student stats.

### Student Experience
- `POST /progress/start`: Start watching a video (Enrolls user).
- `POST /progress/heartbeat`: Update watch time (sent by Extension).
- `POST /progress/complete`: Mark video as watched.
- `POST /progress/quiz/submit`: Submit quiz answers.
- `POST /courses/{id}/claim-certificate`: Generate PDF if eligible.

---

## 🚦 How to Run

### 1. Prerequisites
- Python 3.10+
- PostgreSQL
- API Keys: OpenAI, Google Gemini, YouTube Data API

### 2. Setup
```bash
# Clone repo
git clone <repo-url>
cd credlyse-backend

# Create virtual env
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
Create `.env` file:
```ini
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/credlyse_db
SECRET_KEY=your_secret_key
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
YOUTUBE_API_KEY=...
```

### 4. Database Migrations
```bash
# Run migrations
alembic upgrade head
```

### 5. Start Server
```bash
uvicorn app.main:app --reload
```
Visit `http://localhost:8000/docs` for Swagger UI.

---

## 🧪 Testing Flow

1.  **Signup** as a Creator (`POST /auth/signup`).
2.  **Import** a Playlist (`POST /courses/import` with YouTube Playlist ID).
3.  **Analyze** the Course (`POST /courses/{id}/analyze`). Wait for AI to generate quizzes.
4.  **Publish** the Course (`POST /courses/{id}/publish`).
5.  **Signup** as a Student (new account).
6.  **Start Watching** (`POST /progress/start`).
7.  **Simulate Watch** (`POST /progress/heartbeat` -> `POST /progress/complete`).
8.  **Take Quiz** (`POST /progress/quiz/submit`).
9.  **Repeat** for all videos.
10. **Claim Certificate** (`POST /courses/{id}/claim-certificate`).
11. **Verify** (`GET /certificates/{id}`).

---

## 📜 License
MIT License.
