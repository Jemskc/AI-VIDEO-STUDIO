# AI Movie Studio - Implementation & Handover Guide

## 🚀 System Status: READY FOR PHASE 5 (AI Integration)

**Current State:**
- ✅ **Frontend (Phase 1):** Complete Next.js application with premium UI.
- ✅ **Backend (Phase 2):** Complete FastAPI, PostgreSQL, Redis, Celery, Auth.
- ✅ **Intelligence Layer (Phase 3):** Complete Movie Planning, Story, Scene, Character engines.
- ✅ **Infrastructure (Phase 4):** Complete Orchestrator, Worker Framework, GPU Manager, Plugin System.
- ⏳ **AI Models (Phase 5):** **PENDING IMPLEMENTATION.**

---

## 🖥️ Target Environment: ARC A100 GPU System

This system is designed to run on a single NVIDIA A100 GPU (40GB/80GB) within the ARC infrastructure.

### Prerequisites for Claude Code Agent
1.  **Access:** You are logged into the ARC system with the A100 GPU available.
2.  **Repository:** This codebase is cloned locally.
3.  **Goal:** Implement the **Provider Interfaces** defined in Phase 4 to connect real Open Source AI models.

---

## 🏗️ Architecture Overview

### 1. Directory Structure
```text
ai-movie-studio/
├── frontend/                 # Next.js App (Phase 1)
│   ├── app/                  # Pages & Routing
│   ├── components/           # UI Components
│   └── store/                # Zustand State
├── backend/                  # FastAPI App (Phases 2-4)
│   ├── app/
│   │   ├── api/              # REST Endpoints
│   │   ├── core/             # Config & Security
│   │   ├── db/               # Database Models & Session
│   │   ├── services/         # Business Logic
│   │   │   ├── planning/     # Phase 3: Movie Intelligence
│   │   │   ├── orchestrator/ # Phase 4: Task Orchestration
│   │   │   └── workers/      # Phase 4: Generic Workers
│   │   ├── providers/        # ⚠️ PHASE 5: AI MODEL PLUGINS GO HERE
│   │   │   ├── base.py       # Abstract Base Classes
│   │   │   ├── image.py      # Interface for Image Models
│   │   │   ├── video.py      # Interface for Video Models
│   │   │   ├── audio.py      # Interface for Voice/Music
│   │   │   └── llm.py        # Interface for LLMs
│   │   ├── gpu/              # Phase 4: GPU Management
│   │   └── main.py           # Application Entry Point
│   ├── alembic/              # DB Migrations
│   ├── tests/                # Unit Tests
│   └── requirements.txt      # Python Dependencies
├── docker-compose.yml        # Orchestration (DB, Redis, API, Worker)
└── IMPLEMENTATION_GUIDE.md   # THIS FILE
```

### 2. The "Plugin Pattern" (Critical for Phase 5)

**DO NOT** modify the `orchestrator` or `worker` logic to add new models.
**INSTEAD**, implement the **Provider Interfaces**.

#### How to Add a New Model (e.g., FLUX for Images):
1.  Navigate to `backend/app/providers/`.
2.  Create a new file `flux_provider.py`.
3.  Inherit from `ImageProvider` (defined in `base.py`).
4.  Implement the `generate()` method using the model's specific library (e.g., `diffusers`).
5.  Register the provider in `backend/app/core/registry.py`.

**Example Skeleton:**
```python
# backend/app/providers/flux_provider.py
from app.providers.base import ImageProvider
from app.schemas.tasks import ImageGenerationTask
from app.schemas.results import GenerationResult

class FluxImageProvider(ImageProvider):
    model_name = "FLUX.1-dev"
    required_vram = "24GB"

    async def generate(self, task: ImageGenerationTask) -> GenerationResult:
        # 1. Load Model (handled by GPU Manager)
        # 2. Run Inference
        # 3. Save Output to Storage
        # 4. Return Result
        pass
```

---

## 📋 Phase 5 Implementation Checklist

Claude Code Agent, please execute the following steps in order:

### Step 1: Environment Verification
- [ ] Verify NVIDIA A100 GPU is detected (`nvidia-smi`).
- [ ] Verify Docker & Docker Compose are running.
- [ ] Verify PostgreSQL and Redis containers are up.
- [ ] Install Python dependencies (`pip install -r backend/requirements.txt`).
- [ ] Run Database Migrations (`alembic upgrade head`).

### Step 2: Implement Image Provider (Priority 1)
- [ ] **Target Model:** `FLUX.1-dev` or `Stable Diffusion XL`.
- [ ] **File:** `backend/app/providers/flux_provider.py`.
- [ ] **Dependencies:** Add `diffusers`, `transformers`, `accelerate` to `requirements.txt`.
- [ ] **Logic:** Implement text-to-image generation using the prompt from the `Movie Blueprint`.
- [ ] **Registration:** Register in `ProviderRegistry`.

### Step 3: Implement Video Provider (Priority 2)
- [ ] **Target Model:** `Wan2.1`, `CogVideoX`, or `HunyuanVideo`.
- [ ] **File:** `backend/app/providers/wan_video_provider.py`.
- [ ] **Logic:** Implement image-to-video or text-to-video based on scene requirements.
- [ ] **Optimization:** Ensure VRAM cleanup after generation to prevent OOM errors.

### Step 4: Implement Audio Providers (Priority 3)
- [ ] **Voice:** `XTTS v2` (Coqui) for character dialogue.
- [ ] **Music:** `AudioCraft` (MusicGen) for background scores.
- [ ] **Files:** `backend/app/providers/xtts_provider.py`, `audiocraft_provider.py`.

### Step 5: Implement LLM Provider (Priority 4)
- [ ] **Target Model:** `Llama-3-70B` or `Qwen-72B` (via local inference or API).
- [ ] **File:** `backend/app/providers/llama_provider.py`.
- [ ] **Usage:** Refine scripts, generate dynamic dialogue, fix plot holes.

### Step 6: Render Engine Integration
- [ ] **Tool:** `FFmpeg`.
- [ ] **Logic:** Stitch generated images/videos/audio based on the `Timeline Engine` output.
- [ ] **File:** `backend/app/services/rendering/ffmpeg_renderer.py`.

### Step 7: End-to-End Test
- [ ] Start the system: `docker-compose up --build`.
- [ ] Access Frontend: `http://localhost:3000`.
- [ ] Create a Project -> Enter Prompt -> Generate Blueprint.
- [ ] Trigger "Render All".
- [ ] **Verify:** Watch logs in `docker-compose logs -f worker` to see tasks being picked up and executed by your new providers.

---

## 🔧 Configuration for ARC A100

### `.env` File Setup
Create `backend/.env` with the following (adjust paths for ARC filesystem):

```ini
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ai_movie_studio

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
JWT_SECRET=your-super-secret-jwt-key-change-this
ALGORITHM=HS256

# Storage (ARC Local Path)
STORAGE_PATH=/arc/data/ai-movie-studio/storage
TEMP_PATH=/arc/data/ai-movie-studio/temp

# GPU Settings
GPU_DEVICE_ID=0
MAX_VRAM_USAGE_PERCENT=90

# Model Paths (Local HuggingFace Cache)
MODEL_CACHE_PATH=/arc/data/models/cache

# Debug
DEBUG=True
LOG_LEVEL=INFO
```

### GPU Memory Management
The `GPUManager` class (`backend/app/gpu/manager.py`) is already implemented.
- It reserves VRAM before loading models.
- It unloads idle models automatically.
- **Action:** Ensure your provider implementations call `gpu_manager.load_model()` and `gpu_manager.unload_model()` correctly.

---

## 📞 Troubleshooting & Support

### Common Issues
1.  **OOM (Out of Memory):**
    - Check `GPUManager` logs.
    - Reduce batch size in provider config.
    - Ensure `unload_model()` is called immediately after inference.
2.  **Queue Stuck:**
    - Restart Celery Worker: `docker-compose restart worker`.
    - Check Redis: `redis-cli flushall` (Dev only).
3.  **Database Connection Error:**
    - Ensure Postgres container is healthy: `docker-compose ps`.

### Key Files to Read
- `backend/app/providers/base.py`: The contract you must follow.
- `backend/app/services/orchestrator/engine.py`: How tasks are dispatched.
- `backend/app/db/models.py`: Database schema reference.
- `frontend/app/dashboard/page.tsx`: How the UI triggers jobs.

---

## 🎯 Final Goal

By the end of this session, the system should transition from:
> "Blueprint Generated" (Mock)

To:
> "Rendering Complete" (Real Video File)

**You are now ready to begin coding Phase 5.**
