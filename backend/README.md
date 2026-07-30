# AI Movie Studio Backend

A production-ready backend for AI-powered filmmaking platform. Built with FastAPI, PostgreSQL, Redis, and Celery.

## Features

- **Authentication**: JWT-based authentication with refresh tokens
- **Project Management**: CRUD operations for movie projects
- **Character Management**: Create and manage character profiles
- **Scene Management**: Manage scenes with prompts, camera settings, and more
- **Storyboard**: Organize scenes in storyboards
- **Asset Library**: Upload and manage images, videos, audio files
- **Render Queue**: Job queue system for render tasks (mock implementation)
- **AI Models Registry**: Register and track AI models (placeholder)
- **Notifications**: Real-time notifications system
- **User Settings**: Customizable user preferences
- **WebSocket Support**: Real-time updates for job progress
- **Celery Workers**: Background task processing

## Technology Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL
- **Cache/Queue**: Redis
- **Task Queue**: Celery
- **ORM**: SQLAlchemy 2.x
- **Validation**: Pydantic v2
- **Authentication**: JWT (python-jose)
- **Password Hashing**: bcrypt/passlib
- **Containerization**: Docker, Docker Compose

## Project Structure

```
backend/
├── app/
│   ├── api/v1/           # API routes
│   │   ├── auth/         # Authentication endpoints
│   │   ├── projects/     # Project management
│   │   ├── characters/   # Character management
│   │   ├── scenes/       # Scene management
│   │   ├── assets/       # Asset library
│   │   ├── render/       # Render queue
│   │   ├── models/       # AI models
│   │   ├── notifications/# Notifications
│   │   └── settings/     # User settings
│   ├── core/             # Core configuration
│   ├── database/         # Models and schemas
│   ├── workers/          # Celery tasks
│   ├── websocket/        # WebSocket handlers
│   ├── storage/          # File storage
│   └── main.py           # Application entry point
├── tests/                # Unit tests
├── docker/               # Docker configuration
├── alembic/              # Database migrations
├── requirements/         # Python dependencies
├── docker-compose.yml    # Docker services
└── .env.example          # Environment variables template
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.12+ (for local development)

### Using Docker Compose (Recommended)

1. Clone the repository

2. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

3. Start all services:
   ```bash
   docker-compose up -d
   ```

4. Access the API:
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements/requirements.txt
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   ```

3. Start PostgreSQL and Redis (using Docker):
   ```bash
   docker-compose up -d postgres redis
   ```

4. Run the application:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. Start Celery worker (optional):
   ```bash
   celery -A app.workers.celery_app worker --loglevel=info
   ```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user
- `POST /api/v1/auth/logout` - Logout

### Projects
- `GET /api/v1/projects/` - List projects
- `POST /api/v1/projects/` - Create project
- `GET /api/v1/projects/{id}` - Get project
- `PUT /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project
- `POST /api/v1/projects/{id}/archive` - Archive project
- `POST /api/v1/projects/{id}/duplicate` - Duplicate project
- `POST /api/v1/projects/{id}/favorite` - Toggle favorite

### Characters
- `GET /api/v1/characters/` - List characters
- `POST /api/v1/characters/` - Create character
- `GET /api/v1/characters/{id}` - Get character
- `PUT /api/v1/characters/{id}` - Update character
- `DELETE /api/v1/characters/{id}` - Delete character

### Scenes
- `GET /api/v1/scenes/` - List scenes
- `POST /api/v1/scenes/` - Create scene
- `GET /api/v1/scenes/{id}` - Get scene
- `PUT /api/v1/scenes/{id}` - Update scene
- `DELETE /api/v1/scenes/{id}` - Delete scene
- `POST /api/v1/scenes/reorder` - Reorder scenes

### Assets
- `POST /api/v1/assets/upload` - Upload asset
- `GET /api/v1/assets/` - List assets
- `GET /api/v1/assets/{id}` - Get asset
- `GET /api/v1/assets/{id}/download` - Download asset
- `DELETE /api/v1/assets/{id}` - Delete asset

### Render Jobs
- `POST /api/v1/render/jobs` - Create render job
- `GET /api/v1/render/jobs` - List render jobs
- `GET /api/v1/render/jobs/{id}` - Get job
- `PUT /api/v1/render/jobs/{id}` - Update job
- `POST /api/v1/render/jobs/{id}/cancel` - Cancel job
- `POST /api/v1/render/jobs/{id}/pause` - Pause job
- `POST /api/v1/render/jobs/{id}/resume` - Resume job
- `GET /api/v1/render/queue/status` - Queue status

### AI Models
- `GET /api/v1/models/` - List models
- `GET /api/v1/models/{id}` - Get model
- `POST /api/v1/models/` - Create model
- `PUT /api/v1/models/{id}` - Update model
- `POST /api/v1/models/{id}/install` - Install model
- `DELETE /api/v1/models/{id}` - Delete model
- `GET /api/v1/models/categories` - Get categories

### Notifications
- `GET /api/v1/notifications/` - List notifications
- `POST /api/v1/notifications/` - Create notification
- `PUT /api/v1/notifications/{id}/read` - Mark as read
- `PUT /api/v1/notifications/read-all` - Mark all as read
- `DELETE /api/v1/notifications/{id}` - Delete notification
- `GET /api/v1/notifications/unread/count` - Unread count

### Settings
- `GET /api/v1/settings/` - Get settings
- `PUT /api/v1/settings/` - Update settings
- `GET /api/v1/settings/keyboard-shortcuts` - Get shortcuts
- `PUT /api/v1/settings/keyboard-shortcuts` - Update shortcuts

### WebSocket
- `WS /ws` - General WebSocket connection
- `WS /ws/jobs` - Job updates channel

## Testing

Run tests with pytest:

```bash
pytest tests/ -v
```

## Database Migrations

Using Alembic for database migrations:

```bash
# Initialize (already done)
alembic init alembic

# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Future Phases

This backend is designed to be extended with:

- **AI Video Generation**: Integrate video generation models
- **AI Image Generation**: Connect image generation pipelines
- **Voice/TTS**: Text-to-speech integration
- **Music Generation**: AI music composition
- **S3 Storage**: Cloud storage integration
- **Real GPU Workers**: Actual rendering infrastructure

## License

MIT
