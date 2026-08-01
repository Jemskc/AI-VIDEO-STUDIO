"""
Minimal local filesystem storage backend for AI-generated assets and final renders.

Resolves relative paths (e.g. "generated/<task_id>.png", "renders/<job_id>.mp4")
against a storage root shared by every provider/worker, so mocked outputs land
on disk at the same paths the rest of the pipeline already expects.
"""
from pathlib import Path

from app.core.config import settings


class LocalStorageBackend:
    def __init__(self, base_path: str = None):
        # settings.STORAGE_PATH is "./storage/uploads"; generated/render output
        # lives in sibling directories under the shared "./storage" root.
        self.base_path = Path(base_path or settings.STORAGE_PATH).parent
        self.base_path.mkdir(parents=True, exist_ok=True)

    def get_path(self, relative_path: str) -> Path:
        """Resolve a relative path against the storage root, creating parent dirs."""
        path = self.base_path / relative_path.lstrip("/")
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def save_bytes(self, relative_path: str, data: bytes) -> str:
        path = self.get_path(relative_path)
        path.write_bytes(data)
        return str(path)

    def save_file(self, relative_path: str, source_path: str) -> str:
        """Copy an existing file (e.g. a bundled placeholder) into storage."""
        path = self.get_path(relative_path)
        path.write_bytes(Path(source_path).read_bytes())
        return str(path)

    def exists(self, relative_path: str) -> bool:
        return self.get_path(relative_path).exists()


_default_backend: "LocalStorageBackend | None" = None


def get_storage_backend() -> LocalStorageBackend:
    global _default_backend
    if _default_backend is None:
        _default_backend = LocalStorageBackend()
    return _default_backend
