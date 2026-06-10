"""
Video compression module — uses FFmpeg (must be installed separately).
"""

from pathlib import Path
import shutil
import subprocess


SUPPORTED_FORMATS = {".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm", ".m4v"}

# CRF: lower = better quality / larger file. Range: 0–51 for H.264
# quality 1–100 → CRF 51–18 (inverted scale)
def _quality_to_crf(quality: int) -> int:
    clamped = max(1, min(100, quality))
    return round(51 - (clamped / 100) * 33)


def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def compress(
    input_path: Path,
    output_path: Path,
    quality: int = 75,
    max_width: int = None,
    audio_bitrate: str = "128k",
    **_kwargs,
) -> dict:
    """
    Compress a video file using FFmpeg (H.264 / AAC).

    Args:
        input_path:    Source video file path.
        output_path:   Destination video file path.
        quality:       1–100 quality (mapped to H.264 CRF 51–18).
        max_width:     Scale down if wider than this (keeps aspect ratio).
        audio_bitrate: Audio bitrate string, e.g. '128k', '96k'.

    Returns:
        dict with keys: original_size, compressed_size, savings_pct
    """
    if not _ffmpeg_available():
        raise RuntimeError(
            "FFmpeg is required for video compression.\n"
            "  Install: https://ffmpeg.org/download.html\n"
            "  macOS:   brew install ffmpeg\n"
            "  Ubuntu:  sudo apt install ffmpeg\n"
            "  Windows: https://www.gyan.dev/ffmpeg/builds/"
        )

    original_size = input_path.stat().st_size
    output_path.parent.mkdir(parents=True, exist_ok=True)
    crf = _quality_to_crf(quality)

    # Video filter: scale down if needed
    vf_parts = []
    if max_width:
        vf_parts.append(f"scale='min({max_width},iw)':-2:flags=lanczos")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-c:v", "libx264",
        "-crf", str(crf),
        "-preset", "slow",          # better compression, a bit slower
        "-c:a", "aac",
        "-b:a", audio_bitrate,
        "-movflags", "+faststart",  # web-optimised streaming
    ]

    if vf_parts:
        cmd += ["-vf", ",".join(vf_parts)]

    cmd.append(str(output_path))

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error:\n{result.stderr[-1000:]}")

    compressed_size = output_path.stat().st_size
    savings = round((1 - compressed_size / original_size) * 100, 1) if original_size else 0

    return {
        "original_size": original_size,
        "compressed_size": compressed_size,
        "savings_pct": savings,
        "crf": crf,
    }
