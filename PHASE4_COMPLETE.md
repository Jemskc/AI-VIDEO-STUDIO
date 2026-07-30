# AI Movie Studio - Phase 4 Complete
## AI Infrastructure Layer Implementation Guide

---

## 🎯 Phase 4 Summary

**Status:** ✅ COMPLETE

This phase has built the complete **AI Execution Platform** - the "operating system" that will run all future AI models. No specific AI models were integrated; instead, we created a modular, provider-agnostic infrastructure.

---

## 📁 New Directory Structure

```
backend/app/
├── providers/           # NEW - Abstract provider interfaces
│   ├── __init__.py
│   └── base.py          # BaseProvider, ImageProvider, VideoProvider, etc.
│
├── gpu/                 # NEW - GPU management
│   ├── __init__.py
│   └── manager.py       # GPUMonitor, GPUManager, MemoryReservation
│
├── orchestrator/        # NEW - Task orchestration
│   ├── __init__.py
│   └── engine.py        # Orchestrator, Task, ExecutionPlan
│
├── workers/             # NEW - Generic worker framework
│   ├── __init__.py
│   └── base.py          # BaseWorker, LLMWorker, ImageWorker, etc.
│
├── events/              # NEW - Event bus system
│   ├── __init__.py
│   └── bus.py           # EventBus, EventType, Event
│
├── cache/               # NEW - Caching layer
│   ├── __init__.py
│   └── manager.py       # CacheManager, BlueprintCache, PromptCache
│
├── plugins/             # NEW - Plugin system
│   ├── __init__.py
│   ├── manager.py       # PluginManager for dynamic loading
│   └── image_flux.py    # Example plugin template
│
└── api/
    └── ai_infrastructure.py  # NEW - API endpoints for AI platform
```

---

## 🔧 Core Components Implemented

### 1. Provider Interfaces (`app/providers/base.py`)

**Abstract base classes that all AI models must implement:**

| Provider | Purpose | GPU Required | Memory |
|----------|---------|--------------|--------|
| `BaseProvider` | Base interface | No | - |
| `LLMProvider` | Text generation | Optional | 8GB |
| `ImageProvider` | Image generation | Yes | 12GB |
| `VideoProvider` | Video generation | Yes | 16GB |
| `VoiceProvider` | TTS/Voice cloning | Yes | 6GB |
| `MusicProvider` | Music generation | Yes | 8GB |
| `EmbeddingProvider` | Vector embeddings | No | 4GB |

**Key Methods:**
```python
async def initialize(model_name: str, **kwargs) -> bool
async def shutdown() -> None
async def generate(request: GenerationRequest) -> GenerationResponse
async def generate_stream(request) -> AsyncIterator[ProgressUpdate]
async def validate_request(request) -> tuple[bool, Optional[str]]
```

### 2. GPU Manager (`app/gpu/manager.py`)

**Manages NVIDIA GPU resources:**

- **GPUMonitor**: Detects GPUs, monitors VRAM, temperature, utilization
- **GPUManager**: Reserves/releases GPU memory for tasks
- **MemoryReservation**: Tracks which task owns which GPU memory

**Features:**
- Automatic GPU detection via `pynvml`
- Mock mode for development without GPU
- Memory reservation with automatic cleanup
- Multi-GPU support ready
- Temperature and utilization monitoring

**Usage:**
```python
gpu_manager = get_gpu_manager()
await gpu_manager.initialize()

# Reserve GPU for a task
reservation = await gpu_manager.reserve_gpu(
    task_id="task_123",
    model_name="flux-dev",
    required_memory_mb=12000
)

# Release when done
await gpu_manager.release_reservation(reservation.reservation_id)
```

### 3. Orchestrator (`app/orchestrator/engine.py`)

**Central coordinator for AI execution:**

- Receives production blueprints from Phase 3
- Splits into executable tasks
- Manages dependencies between tasks
- Schedules tasks to appropriate workers
- Tracks progress and handles failures

**Task Types:**
- `GENERATE_STORY` - LLM-based story refinement
- `GENERATE_CHARACTER` - Character image generation
- `GENERATE_IMAGE` - Scene image generation
- `GENERATE_VIDEO` - Scene video generation
- `GENERATE_VOICE` - Dialogue voice synthesis
- `GENERATE_MUSIC` - Background music creation
- `RENDER` - Final video composition

**Execution Flow:**
```
Blueprint → Orchestrator → Task Graph → Worker Queue → Execution
                ↓
         Dependency Resolution
                ↓
         Progress Tracking
```

### 4. Worker Framework (`app/workers/base.py`)

**Model-agnostic workers that execute tasks:**

| Worker | Handles | Provider Used |
|--------|---------|---------------|
| `LLMWorker` | Story, dialogue | LLMProvider |
| `ImageWorker` | Characters, scenes | ImageProvider |
| `VideoWorker` | Scene videos | VideoProvider |
| `VoiceWorker` | Speech synthesis | VoiceProvider |
| `MusicWorker` | Music/SFX | MusicProvider |
| `RenderWorker` | FFmpeg composition | N/A |

**Worker Lifecycle:**
1. Initialize (load provider, reserve GPU)
2. Poll orchestrator for tasks
3. Execute task via provider interface
4. Report completion/failure
5. Return to idle

### 5. Event Bus (`app/events/bus.py`)

**Publish/subscribe system for loose coupling:**

**Event Types:**
- Task events: `TASK_STARTED`, `TASK_COMPLETED`, `TASK_FAILED`
- Worker events: `WORKER_ONLINE`, `WORKER_OFFLINE`
- Model events: `MODEL_LOADED`, `MODEL_UNLOADED`
- Render events: `RENDER_PROGRESS`, `RENDER_COMPLETED`
- System events: `SYSTEM_STARTUP`, `GPU_WARNING`

**Usage:**
```python
from app.events.bus import publish_event, EventType

await publish_event(
    event_type=EventType.TASK_COMPLETED,
    payload={"task_id": "123", "result": "..."},
    source="image_worker"
)
```

### 6. Cache Manager (`app/cache/manager.py`)

**Caching layer for performance:**

- TTL-based expiration
- LRU eviction
- Namespace support (blueprints, prompts, models)
- Statistics tracking

**Specialized Caches:**
- `BlueprintCache` - Movie production blueprints
- `PromptCache` - Generated prompts (deduplication)
- `ModelCache` - Model metadata and status

### 7. Plugin System (`app/plugins/manager.py`)

**Dynamic plugin loading for AI providers:**

- Discovers plugins in `app/plugins/` directory
- Loads/unloads at runtime
- Version tracking
- Enable/disable without restart

**Plugin Structure:**
```
app/plugins/
├── image_flux/
│   ├── __init__.py
│   ├── provider.py      # FluxImageProvider implementation
│   └── plugin.json      # Manifest
└── video_wan/
    ├── __init__.py
    ├── provider.py      # WanVideoProvider implementation
    └── plugin.json
```

### 8. Example Plugin (`app/plugins/image_flux.py`)

**Template showing how to implement an image provider:**

- Implements `ImageProvider` interface
- Shows where to add actual FLUX model code
- Includes validation, progress streaming
- Mock mode for testing

---

## 🌐 API Endpoints

New endpoints added in `/api/v1/ai/`:

### GPU Management
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/gpu/status` | GET | Get GPU system status |
| `/gpu/reservations` | GET | List active GPU reservations |

### Workers
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/workers` | GET | List all workers |
| `/workers/{worker_type}` | POST | Create new worker |

### Tasks
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tasks/{task_id}` | GET | Get task details |
| `/tasks/{task_id}/cancel` | POST | Cancel a task |

### Execution Plans
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/plans/{plan_id}` | GET | Get execution plan |
| `/projects/{project_id}/progress` | GET | Get project progress |

### Cache
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/cache/stats` | GET | Cache statistics |
| `/cache/keys` | GET | List cache keys |
| `/cache/{namespace}` | DELETE | Clear namespace |
| `/cache/cleanup` | POST | Cleanup expired entries |

### Events
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/events` | GET | Get recent events |

### System
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Overall system health |

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Next.js)                      │
└─────────────────────┬───────────────────────────────────────┘
                      │ REST API / WebSocket
┌─────────────────────▼───────────────────────────────────────┐
│                    FastAPI Backend                           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              AI Infrastructure API                   │    │
│  └─────────────────────┬───────────────────────────────┘    │
│                        │                                     │
│  ┌─────────────────────▼───────────────────────────────┐    │
│  │                  Orchestrator                        │    │
│  │  • Parse Blueprints                                  │    │
│  │  • Create Task Graph                                 │    │
│  │  • Manage Dependencies                               │    │
│  └─────┬─────────────┬─────────────┬─────────────┬──────┘    │
│        │             │             │             │           │
│  ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐   │
│  │   LLM     │ │  Image    │ │  Video    │ │  Voice    │   │
│  │  Worker   │ │  Worker   │ │  Worker   │ │  Worker   │   │
│  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘   │
│        │             │             │             │           │
│  ┌─────▼─────────────▼─────────────▼─────────────▼─────┐   │
│  │              Provider Interfaces                     │   │
│  │  (LLMProvider, ImageProvider, VideoProvider, etc.)  │   │
│  └─────┬─────────────┬─────────────┬─────────────┬─────┘   │
│        │             │             │             │          │
└────────┼─────────────┼─────────────┼─────────────┼──────────┘
         │             │             │             │
┌────────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐
│   Plugin     │ │   GPU     │ │  Cache    │ │  Event    │
│   Manager    │ │  Manager  │ │  Manager  │ │   Bus     │
└──────────────┘ └─────┬─────┘ └───────────┘ └───────────┘
                       │
              ┌────────▼────────┐
              │  NVIDIA A100    │
              │  40GB VRAM      │
              └─────────────────┘
```

---

## 🚀 How to Use

### 1. Initialize the System

```python
from app.gpu.manager import initialize_gpu_manager
from app.orchestrator.engine import initialize_orchestrator
from app.cache.manager import initialize_cache_manager
from app.plugins.manager import initialize_plugin_manager

# Initialize all components
await initialize_gpu_manager()
await initialize_orchestrator()
await initialize_cache_manager()
await initialize_plugin_manager()
```

### 2. Create an Execution Plan

```python
from app.orchestrator.engine import get_orchestrator

orchestrator = get_orchestrator()

# Get blueprint from Phase 3
blueprint = {...}  # From movie planning engine

# Create execution plan
plan = await orchestrator.create_execution_plan(
    project_id="proj_123",
    blueprint_id="bp_456",
    blueprint_data=blueprint
)

print(f"Created {plan.total_tasks} tasks")
```

### 3. Start Workers

```python
from app.workers.base import create_worker, WorkerRegistry

# Create workers
image_worker = create_worker("image")
video_worker = create_worker("video")
voice_worker = create_worker("voice")

# Register and start
WorkerRegistry.register(image_worker)
await image_worker.start()  # Runs in loop
```

### 4. Monitor Progress

```python
# Via API
GET /api/v1/ai/projects/proj_123/progress

# Response:
{
  "status": "running",
  "plans_count": 1,
  "total_tasks": 25,
  "completed_tasks": 12,
  "failed_tasks": 0,
  "progress": 0.48
}
```

---

## 🔌 Adding a New AI Model (Phase 5)

To add a new model (e.g., CogVideoX for video):

### Step 1: Create Plugin

```python
# app/plugins/video_cogvideox.py
from app.providers.base import VideoProvider

class CogVideoXProvider(VideoProvider):
    provider_name = "video"
    supported_models = ["cogvideox-1b", "cogvideox-5b"]
    requires_gpu = True
    gpu_memory_mb = 16000
    
    async def initialize(self, model_name: str, **kwargs):
        # Load CogVideoX model
        from diffusers import CogVideoXPipeline
        self.model = CogVideoXPipeline.from_pretrained(...)
        return True
    
    async def generate_video(self, prompt: str, **kwargs):
        # Generate video
        video = self.model(prompt=prompt, ...)
        return save_video(video)
```

### Step 2: Add Plugin Manifest

```json
// app/plugins/video_cogvideox/plugin.json
{
  "name": "cogvideox-video-provider",
  "version": "1.0.0",
  "provider_type": "video",
  "description": "CogVideoX video generation",
  "models": ["cogvideox-1b", "cogvideox-5b"]
}
```

### Step 3: That's It!

The plugin system automatically discovers and loads it. The orchestrator and workers use it through the `VideoProvider` interface - no other code changes needed.

---

## 📈 Testing

### Unit Tests Location
```
backend/tests/
├── test_providers.py
├── test_gpu_manager.py
├── test_orchestrator.py
├── test_workers.py
├── test_event_bus.py
├── test_cache_manager.py
└── test_plugins.py
```

### Run Tests
```bash
cd backend
pytest tests/test_*.py -v
```

### Test GPU Manager (Mock Mode)
```python
import asyncio
from app.gpu.manager import GPUManager

async def test_gpu():
    manager = GPUManager()
    await manager.initialize()
    
    status = await manager.get_system_status()
    print(f"GPUs: {status['gpu_count']}")
    print(f"Total VRAM: {status['total_memory_mb']}MB")
    
    # Reserve memory
    reservation = await manager.reserve_gpu(
        task_id="test_1",
        model_name="test-model",
        required_memory_mb=8000
    )
    print(f"Reserved: {reservation}")

asyncio.run(test_gpu())
```

---

## 🔒 Security Considerations

1. **GPU Isolation**: Each task gets isolated memory reservation
2. **Plugin Validation**: Plugins are validated before loading
3. **Input Validation**: All requests validated by providers
4. **Rate Limiting**: Implement at API level (future)
5. **Audit Logging**: All events logged via Event Bus

---

## 📝 Configuration

### Environment Variables

```bash
# GPU Settings
GPU_MEMORY_THRESHOLD=0.9      # Alert at 90% usage
GPU_TEMPERATURE_THRESHOLD=85  # Alert at 85°C

# Cache Settings
CACHE_MAX_SIZE=1000           # Max cached items
CACHE_DEFAULT_TTL=3600        # Default 1 hour

# Worker Settings
WORKER_HEARTBEAT_INTERVAL=30  # Seconds
WORKER_MAX_RETRIES=3          # Retry failed tasks

# Plugin Settings
PLUGINS_DIR=app/plugins       # Plugin directory
AUTO_LOAD_PLUGINS=true        # Auto-discover plugins
```

---

## 🎯 What's Ready for Phase 5

✅ **Provider Interfaces** - Ready for model implementations  
✅ **GPU Management** - Ready for real GPU allocation  
✅ **Task Orchestration** - Ready to schedule real tasks  
✅ **Worker Framework** - Ready to execute real models  
✅ **Plugin System** - Ready to load real plugins  
✅ **Event System** - Ready for real-time updates  
✅ **Caching** - Ready for performance optimization  
✅ **API Endpoints** - Ready for monitoring  

---

## 📋 Checklist for Phase 5

When integrating actual AI models:

- [ ] Install model dependencies (diffusers, transformers, etc.)
- [ ] Implement provider classes for each model
- [ ] Create plugin manifests
- [ ] Update GPU memory requirements per model
- [ ] Test with small inputs first
- [ ] Configure model download paths
- [ ] Set up model caching strategy
- [ ] Implement progress callbacks
- [ ] Add error handling for OOM scenarios
- [ ] Test multi-task concurrency
- [ ] Benchmark performance
- [ ] Document model-specific parameters

---

## 🏁 Conclusion

Phase 4 has created a **complete, production-ready AI execution platform**. The system is:

- **Modular**: Each component is independent and replaceable
- **Extensible**: New models added via plugins without core changes
- **Scalable**: Ready for multi-GPU and distributed execution
- **Observable**: Full visibility via events, logs, and APIs
- **Resilient**: Error handling, retries, and recovery built-in

**The platform is now ready for Phase 5: AI Model Integration.**

Any AI model (FLUX, Wan, CogVideoX, XTTS, etc.) can be integrated by simply implementing the provider interfaces and dropping the plugin into the plugins folder. The rest of the system requires zero changes.
