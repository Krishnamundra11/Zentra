# 🌍 Zetra

**AI-powered tourist place recognition and travel planning platform.**

Upload a photo of any tourist destination → the system identifies it → an AI agent autonomously plans your entire trip with hotel recommendations, restaurants, attractions, and booking links.

---

## Table of Contents

1. [What This Does](#what-this-does)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Prerequisites](#prerequisites)
5. [PostgreSQL Setup](#postgresql-setup)
6. [Redis Setup](#redis-setup)
7. [Backend Setup](#backend-setup)
8. [Frontend Setup](#frontend-setup)
9. [Running the Full Stack](#running-the-full-stack)
10. [Seeding the Database](#seeding-the-database)
11. [API Overview](#api-overview)
12. [Environment Variables](#environment-variables)
13. [Architecture Summary](#architecture-summary)

---

## What This Does

| Step | What happens |
|------|-------------|
| 1 | User uploads a tourist place photo |
| 2 | CLIP model generates a 512-d image embedding |
| 3 | pgvector searches for visually similar known places |
| 4 | Claude Vision verifies the best match with confidence score |
| 5 | If unrecognised → similar places are suggested |
| 6 | Claude agentic loop calls tools (Google Places, Booking.com, etc.) |
| 7 | Full day-by-day itinerary delivered with hotel & booking links |
| 8 | WebSocket streams live progress to the UI throughout |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | Python 3.11 · FastAPI · Uvicorn |
| Task Queue | Celery · Redis |
| AI / Vision | Anthropic Claude (claude-opus-4-5) · CLIP (HuggingFace) |
| Database | PostgreSQL 15 · pgvector extension |
| Cache / Broker | Redis 7 |
| Frontend | React 18 · Vite · Zustand · Axios |
| Object Storage | AWS S3 (optional in dev) |

---

## Project Structure

```
Zetra/
│
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app factory, routers, CORS
│   │   ├── config.py                # All settings via pydantic-settings
│   │   ├── database.py              # Async SQLAlchemy engine + pgvector init
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── place.py             # User, Place, PlaceEmbedding, RecognitionEvent, Itinerary
│   │   │
│   │   ├── routers/
│   │   │   ├── auth.py              # POST /auth/register, /auth/login
│   │   │   ├── recognition.py       # POST /recognition/upload, WS /recognition/ws/{id}
│   │   │   ├── agent.py             # POST /agent/start, GET /agent/{id}/status
│   │   │   └── recommendations.py   # GET /recommend/attractions, /hotels, /food
│   │   │
│   │   ├── services/
│   │   │   ├── cv_pipeline.py       # CLIP embedding → pgvector search → Claude Vision
│   │   │   └── agent_service.py     # Claude tool-use agentic loop
│   │   │
│   │   ├── tasks/
│   │   │   ├── celery_app.py        # Celery factory + config
│   │   │   ├── cv_tasks.py          # @celery task: run_cv_task, run_agent_task
│   │   │   └── agent_tasks.py       # Re-export for Celery discovery
│   │   │
│   │   └── utils/
│   │       ├── cache.py             # Redis get/set helpers (async + sync)
│   │       └── s3.py                # S3 upload helper
│   │
│   ├── alembic/
│   │   └── env.py                   # Alembic async migration config
│   ├── alembic.ini
│   ├── seed_places.py               # Seed DB with known landmarks + embeddings
│   ├── .env.example                 # Copy to .env and fill in secrets
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── main.jsx                 # React entry point
    │   ├── App.jsx                  # Router + layout
    │   ├── index.css                # Global reset
    │   │
    │   ├── pages/
    │   │   ├── Home.jsx + Home.css          # Upload + preferences
    │   │   ├── Results.jsx + Results.css    # Recognition result + agent progress
    │   │   ├── Itinerary.jsx + Itinerary.css# Full travel plan with tabs
    │   │   └── Profile.jsx + Profile.css    # Saved trips
    │   │
    │   ├── components/
    │   │   ├── Navbar.jsx + Navbar.css
    │   │   ├── PlaceCard.jsx + PlaceCard.css
    │   │   ├── AgentProgress.jsx + AgentProgress.css
    │   │   └── RecoGrid.jsx + RecoGrid.css
    │   │
    │   ├── hooks/
    │   │   └── useRecognition.js    # Upload + WebSocket progress hook
    │   │
    │   ├── services/
    │   │   └── api.js               # Axios instance + all endpoint calls
    │   │
    │   └── store/
    │       └── useStore.js          # Zustand global state (auth, recognition, itinerary)
    │
    ├── index.html
    ├── vite.config.js
    ├── package.json
    └── .env.example
```

---

## Prerequisites

Install these on your machine before proceeding:

- **Python 3.11+** — https://python.org
- **Node.js 20+** — https://nodejs.org
- **PostgreSQL 15+** — https://postgresql.org/download
- **Redis 7+** — https://redis.io/download

Verify:
```bash
python --version       # Python 3.11.x
node --version         # v20.x.x
psql --version         # psql (PostgreSQL) 15.x
redis-cli --version    # Redis cli 7.x.x
```

---

## PostgreSQL Setup

### 1. Start PostgreSQL

**macOS (Homebrew):**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**Windows:**
Download installer from https://postgresql.org/download/windows and run it.
PostgreSQL will start as a Windows service automatically.

### 2. Create database and user

```bash
# macOS / Linux — connect as postgres superuser
sudo -u postgres psql

# Windows — open pgAdmin or run:
# psql -U postgres
```

Inside the psql shell:
```sql
CREATE DATABASE Zetra;
CREATE USER Zetra_user WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE Zetra TO Zetra_user;
\q
```

### 3. Install pgvector extension

**macOS (Homebrew):**
```bash
brew install pgvector
```
Then in psql:
```sql
\c Zetra
CREATE EXTENSION IF NOT EXISTS vector;
```

**Ubuntu/Debian:**
```bash
sudo apt install postgresql-15-pgvector
```
Then:
```sql
\c Zetra
CREATE EXTENSION IF NOT EXISTS vector;
```

**Windows:**
Download prebuilt binaries from https://github.com/pgvector/pgvector/releases
and follow the README installation steps. Then run `CREATE EXTENSION vector;` in psql.

---

## Redis Setup

**macOS (Homebrew):**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

**Windows:**
Download from https://github.com/tporadowski/redis/releases
Run `redis-server.exe` or install as a Windows service.

Verify Redis is running:
```bash
redis-cli ping
# should return: PONG
```

---

## Backend Setup

### 1. Create and activate a virtual environment

```bash
cd Zetra/backend

# Create venv
python -m venv venv

# Activate — macOS / Linux
source venv/bin/activate

# Activate — Windows (Command Prompt)
venv\Scripts\activate.bat

# Activate — Windows (PowerShell)
venv\Scripts\Activate.ps1
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

> **Note on PyTorch:** If you do not have a GPU, the CPU version of PyTorch is
> installed automatically. CLIP inference will be slower (~2–3 seconds per image)
> but fully functional. For GPU acceleration install the CUDA build:
> https://pytorch.org/get-started/locally/

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```env
DATABASE_URL=postgresql+asyncpg://Zetra_user:yourpassword@localhost:5432/Zetra
REDIS_URL=redis://localhost:6379/0
ANTHROPIC_API_KEY=sk-ant-your-key-here
GOOGLE_PLACES_API_KEY=your-google-places-key
JWT_SECRET_KEY=a-long-random-string
```

S3 credentials are optional during local development. Images will fail to upload
to S3 but the CV pipeline will still work if you pass image bytes directly.

### 4. Run database migrations

```bash
# Still inside backend/ with venv active
alembic upgrade head
```

This creates all tables and indexes (including the pgvector IVFFlat index).

### 5. Start the FastAPI server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at: http://localhost:8000/docs

### 6. Start the Celery worker (separate terminal)

```bash
# Open a new terminal, cd into backend/, activate venv

cd Zetra/backend
source venv/bin/activate      # or venv\Scripts\activate on Windows

celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2
```

> On Windows, Celery requires the `solo` pool due to multiprocessing limitations:
> ```
> celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
> ```

---

## Frontend Setup

### 1. Install Node dependencies

```bash
cd Zetra/frontend
npm install
```

### 2. Configure environment

```bash
cp .env.example .env
```

Default `.env`:
```env
VITE_API_URL=http://localhost:8000
```

### 3. Start the dev server

```bash
npm run dev
```

App available at: http://localhost:3000

---

## Running the Full Stack

You need **4 terminals** open simultaneously:

| Terminal | Directory | Command |
|----------|-----------|---------|
| 1 — API | `backend/` | `source venv/bin/activate && uvicorn app.main:app --reload --port 8000` |
| 2 — Worker | `backend/` | `source venv/bin/activate && celery -A app.tasks.celery_app worker --loglevel=info` |
| 3 — Frontend | `frontend/` | `npm run dev` |
| 4 — Redis (if not a service) | anywhere | `redis-server` |

Then open http://localhost:3000 in your browser.

---

## Seeding the Database

The CV pipeline requires known tourist places with pre-computed CLIP embeddings
in the `place_embeddings` table. Run the seed script once after migrations:

```bash
cd Zetra/backend
source venv/bin/activate
python seed_places.py
```

This seeds ~5 well-known landmarks. For production, build a richer dataset
by scraping Wikimedia Commons images for thousands of tourist destinations and
running them through `compute_clip_embedding()`.

---

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Get JWT tokens |
| POST | `/recognition/upload` | Upload image → get `task_id` |
| GET | `/recognition/{task_id}` | Poll recognition status |
| WS | `/recognition/ws/{task_id}` | WebSocket progress stream |
| POST | `/agent/start` | Start AI travel agent |
| GET | `/agent/{task_id}/status` | Agent run status |
| GET | `/agent/itinerary/{task_id}` | Fetch completed itinerary |
| GET | `/recommend/attractions` | Nearby attractions |
| GET | `/recommend/hotels` | Hotel recommendations |
| GET | `/recommend/food` | Restaurant recommendations |

Interactive docs: http://localhost:8000/docs

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ | AsyncPG PostgreSQL URL |
| `REDIS_URL` | ✅ | Redis connection URL |
| `ANTHROPIC_API_KEY` | ✅ | Claude API key (anthropic.com) |
| `GOOGLE_PLACES_API_KEY` | ✅ | For attractions + restaurants |
| `JWT_SECRET_KEY` | ✅ | Random secret for JWT signing |
| `AWS_ACCESS_KEY_ID` | ⬜ | S3 image storage (optional in dev) |
| `AWS_SECRET_ACCESS_KEY` | ⬜ | S3 image storage (optional in dev) |
| `S3_BUCKET` | ⬜ | S3 bucket name |
| `CLIP_MODEL` | ⬜ | Default: `openai/clip-vit-base-patch32` |
| `CV_STRONG_MATCH_THRESHOLD` | ⬜ | Default: `0.25` |
| `CLAUDE_CONFIDENCE_THRESHOLD` | ⬜ | Default: `0.75` |

### Frontend (`frontend/.env`)

| Variable | Description |
|----------|-------------|
| `VITE_API_URL` | Backend URL (default: `http://localhost:8000`) |

---

## Architecture Summary

```
Browser (React + Vite)
        │  REST + WebSocket
        ▼
FastAPI (Uvicorn, port 8000)
  ├── Auth router     (JWT)
  ├── Recognition     (upload → task_id → WS progress)
  ├── Agent router    (start planning → poll status)
  └── Recommend       (attractions / hotels / food)
        │
        ├── Celery Worker (background tasks)
        │     ├── CV Pipeline: CLIP → pgvector → Claude Vision
        │     └── Agent Loop: Claude tool-use → itinerary
        │
        ├── PostgreSQL + pgvector  (places, embeddings, users, itineraries)
        └── Redis  (task broker, result cache, WebSocket event queue)
```

### CV Pipeline Flow

```
Image upload
    → CLIP embedding (512-d vector)
    → pgvector cosine search (top-5 candidates)
    → Claude Vision verification (confidence score)
    → if confidence ≥ 0.75 → "matched"
    → if confidence ≥ 0.40 → "likely"
    → else → similar places fallback
```

### Agent Loop Flow

```
Confirmed place + user preferences
    → Claude claude-opus-4-5 with 6 tools
    → Tool calls: attractions / hotels / homestays / restaurants / travel_info / booking_links
    → Claude synthesises day-by-day itinerary JSON
    → Stored in Redis + PostgreSQL, delivered to frontend
```
