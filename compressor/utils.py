"""
Utility functions — file routing, size formatting, progress helpers.
"""

from pathlib import Path
from typing import Optional
from . import image, pdf, video, audio, archive


# ── File-type registry ──────────────────────────────────────────────────────

MODULES = {
    "image":   image,
    "pdf":     pdf,
    "video":   video,
    "audio":   audio,
    "archive": archive,
}

EXT_TO_TYPE: dict[str, str] = {}
for _type, _module in MODULES.items():
    for _ext in _module.SUPPORTED_FORMATS:
        EXT_TO_TYPE[_ext] = _type


def detect_type(path: Path) -> Optional[str]:
    """Return media type string for the given file extension, or None."""
    return EXT_TO_TYPE.get(path.suffix.lower())


def all_supported_extensions() -> list[str]:
    return sorted(EXT_TO_TYPE.keys())


# ── Size / savings helpers ───────────────────────────────────────────────────

def human_size(n_bytes: int) -> str:
    """Format byte count as a human-readable string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n_bytes) < 1024.0:
            return f"{n_bytes:.1f} {unit}"
        n_bytes /= 1024.0
    return f"{n_bytes:.1f} PB"


def savings_str(original: int, compressed: int) -> str:
    """Return a formatted savings/increase string."""
    if original == 0:
        return "N/A"
    pct = (1 - compressed / original) * 100
    if pct >= 0:
        return f"↓ {pct:.1f}% smaller"
    else:
        return f"↑ {abs(pct):.1f}% larger"


# ── Output path helper ───────────────────────────────────────────────────────

def build_output_path(
    input_path: Path,
    output_dir: Optional[Path] = None,
    suffix: Optional[str] = None,
    prefix: str = "",
    name_suffix: str = "_compressed",
) -> Path:
    """
    Derive a sensible output path from an input path.

    Priority:
      1. output_dir  → place file in that directory
      2. suffix      → change the file extension
      3. name_suffix → append to the stem (e.g. 'photo_compressed.jpg')
    """
    stem = input_path.stem
    ext  = suffix if suffix else input_path.suffix

    new_name = f"{prefix}{stem}{name_suffix}{ext}"

    if output_dir:
        return output_dir / new_name
    return input_path.parent / new_name


# ── Dispatch ─────────────────────────────────────────────────────────────────

def compress_file(
    input_path: Path,
    output_path: Path,
    quality: int = 75,
    **kwargs,
) -> dict:
    """
    Dispatch compression to the correct module based on file type.

    Returns a result dict (keys vary by module, always has
    original_size, compressed_size, savings_pct).
    """
    file_type = detect_type(input_path)
    if file_type is None:
        raise ValueError(
            f"Unsupported file type: '{input_path.suffix}'\n"
            f"Supported extensions: {', '.join(all_supported_extensions())}"
        )

    module = MODULES[file_type]
    result = module.compress(input_path, output_path, quality=quality, **kwargs)
    result["file_type"] = file_type
    result["input_path"] = input_path
    result["output_path"] = output_path
    return result
