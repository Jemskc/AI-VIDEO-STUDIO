"""
FFmpeg-based final video renderer.

Concatenates the scene video clips produced by the video provider into a
single output file. In the mock pipeline these clips are placeholders, but
this proves the actual FFmpeg subprocess path end to end so swapping in real
generated clips later requires no changes here.
"""
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


def render_final_video(scene_video_paths: List[str], output_path: str) -> str:
    """Concatenate scene video files (in order) into a single output file via ffmpeg."""
    if not scene_video_paths:
        raise ValueError("No scene video paths to render")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for path in scene_video_paths:
            f.write(f"file '{Path(path).resolve()}'\n")
        filelist_path = f.name

    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", filelist_path, "-c", "copy", str(output),
            ],
            check=True, capture_output=True, text=True,
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"ffmpeg concat failed: {e.stderr}")
        raise
    finally:
        Path(filelist_path).unlink(missing_ok=True)

    return str(output)
