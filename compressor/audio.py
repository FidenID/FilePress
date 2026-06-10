"""
Audio compression module — uses FFmpeg for transcoding / bitrate reduction.
"""

from pathlib import Path
import shutil
import subprocess


SUPPORTED_FORMATS = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma", ".opus"}

# quality 1–100 → bitrate in kbps (MP3/AAC range)
def _quality_to_bitrate(quality: int) -> str:
    kbps = round(32 + (quality / 100) * (320 - 32))
    # Round to common bitrate steps
    for step in [32, 48, 64, 96, 128, 160, 192, 224, 256, 320]:
        if kbps <= step:
            return f"{step}k"
    return "320k"


def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


CODEC_MAP = {
    ".mp3":  ("libmp3lame", "mp3"),
    ".aac":  ("aac",        "adts"),
    ".m4a":  ("aac",        "ipod"),
    ".ogg":  ("libvorbis",  "ogg"),
    ".opus": ("libopus",    "opus"),
    ".flac": ("flac",       "flac"),
    ".wav":  ("pcm_s16le",  "wav"),
    ".wma":  ("wmav2",      "asf"),
}


def compress(
    input_path: Path,
    output_path: Path,
    quality: int = 75,
    sample_rate: int = None,
    channels: int = None,
    **_kwargs,
) -> dict:
    """
    Compress/transcode an audio file using FFmpeg.

    Args:
        input_path:  Source audio file path.
        output_path: Destination audio file path.
        quality:     1–100 (mapped to bitrate 32–320 kbps).
        sample_rate: Override sample rate (e.g. 44100, 22050).
        channels:    Override channels (1=mono, 2=stereo).

    Returns:
        dict with keys: original_size, compressed_size, savings_pct, bitrate
    """
    if not _ffmpeg_available():
        raise RuntimeError(
            "FFmpeg is required for audio compression.\n"
            "  macOS:   brew install ffmpeg\n"
            "  Ubuntu:  sudo apt install ffmpeg\n"
            "  Windows: https://www.gyan.dev/ffmpeg/builds/"
        )

    original_size = input_path.stat().st_size
    output_path.parent.mkdir(parents=True, exist_ok=True)

    ext = output_path.suffix.lower()
    codec, fmt = CODEC_MAP.get(ext, ("libmp3lame", "mp3"))
    bitrate = _quality_to_bitrate(quality)

    cmd = ["ffmpeg", "-y", "-i", str(input_path), "-c:a", codec]

    # FLAC and WAV are lossless — bitrate doesn't apply
    if codec not in ("flac", "pcm_s16le"):
        cmd += ["-b:a", bitrate]

    if sample_rate:
        cmd += ["-ar", str(sample_rate)]

    if channels:
        cmd += ["-ac", str(channels)]

    cmd += ["-f", fmt, str(output_path)]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error:\n{result.stderr[-1000:]}")

    compressed_size = output_path.stat().st_size
    savings = round((1 - compressed_size / original_size) * 100, 1) if original_size else 0

    return {
        "original_size": original_size,
        "compressed_size": compressed_size,
        "savings_pct": savings,
        "bitrate": bitrate,
    }
