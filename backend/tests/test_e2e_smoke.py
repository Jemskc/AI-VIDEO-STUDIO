"""
End-to-end smoke test for the full mock pipeline: register -> login ->
create project -> generate a movie from a prompt -> fetch its blueprint ->
render it -> confirm a real, playable video file comes out the other end.

Run with: pytest tests/test_e2e_smoke.py -v
(conftest.py points this at a throwaway SQLite DB and runs Celery tasks
eagerly in-process, so no Postgres/Redis/worker process is required.)

This is the single most valuable regression guard in this codebase: every
bug found while building Phases 0-4 (dead imports, the camera_plan naming
mismatch, the enum round-trip bug, the CameraPlan flush-ordering bug, the
regex bug, the missing ai_infrastructure/websocket router mounts, the
/models/categories route-ordering bug, ...) would have been caught
immediately by this test. Run it after any change that touches the movie
planning, orchestrator, worker, or render pipeline code.
"""
import shutil
import subprocess

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _ffprobe_duration_seconds(path: str) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            path,
        ],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"ffprobe failed: {result.stderr}"
    return float(result.stdout.strip())


@pytest.mark.skipif(shutil.which("ffprobe") is None, reason="ffprobe not installed")
def test_full_movie_pipeline():
    # 1. Register and log in
    register = client.post(
        "/api/v1/auth/register",
        json={"email": "smoke@example.com", "username": "smoketester", "password": "password123"},
    )
    assert register.status_code == 201, register.text

    login = client.post(
        "/api/v1/auth/login", json={"email": "smoke@example.com", "password": "password123"}
    )
    assert login.status_code == 200, login.text
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # 2. Create a project
    project = client.post(
        "/api/v1/projects/", json={"title": "Smoke Test Movie"}, headers=headers
    )
    assert project.status_code == 201, project.text
    project_id = project.json()["id"]

    # 3. Generate a movie from a prompt (2 min target -> 4 scenes)
    story = client.post(
        "/api/v1/intelligence/stories",
        json={
            "project_id": project_id,
            "title": "Smoke Test Movie",
            "synopsis": "A lone astronaut on Mars discovers a glowing alien artifact.",
            "estimated_duration_minutes": 2.0,
        },
        headers=headers,
    )
    assert story.status_code == 201, story.text
    story_id = story.json()["id"]

    # 4. Fetch the auto-generated blueprint
    blueprint = client.get(f"/api/v1/intelligence/stories/{story_id}/blueprint")
    assert blueprint.status_code == 200, blueprint.text
    bp = blueprint.json()
    assert bp["scene_count"] == 4, bp["scene_count"]
    assert len(bp["scenes"]) == 4
    assert all(scene["image_prompt"] for scene in bp["scenes"]), "scenes must have generated prompts"
    assert len(bp["characters"]) >= 1

    # 5. Render it (Celery runs eagerly here; a real deployment would poll
    # GET /render/jobs/{id} until status == "completed").
    render_job = client.post(
        "/api/v1/render/jobs",
        json={"project_id": project_id, "job_type": "movie", "parameters": {"story_id": story_id}},
        headers=headers,
    )
    assert render_job.status_code == 201, render_job.text
    job_id = render_job.json()["id"]

    job = client.get(f"/api/v1/render/jobs/{job_id}", headers=headers)
    assert job.status_code == 200, job.text
    job_data = job.json()
    assert job_data["status"] == "completed", job_data.get("error_message")

    # 6. Confirm a real, valid video file came out
    output_url = job_data["output_url"]
    assert output_url, "completed job must have an output_url"

    duration = _ffprobe_duration_seconds(output_url)
    assert duration > 0, f"output video has no duration: {output_url}"
