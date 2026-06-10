"""
Image compression module — supports JPEG, PNG, WebP, GIF, BMP, TIFF.
"""

from pathlib import Path
from typing import Optional
from PIL import Image


SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff", ".tif"}

FORMAT_MAP = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".webp": "WEBP",
    ".gif": "GIF",
    ".bmp": "BMP",
    ".tiff": "TIFF",
    ".tif": "TIFF",
}


def compress(
    input_path: Path,
    output_path: Path,
    quality: int = 75,
    max_width: Optional[int] = None,
    max_height: Optional[int] = None,
    output_format: Optional[str] = None,
) -> dict:
    """
    Compress an image file.

    Args:
        input_path:    Source image file path.
        output_path:   Destination file path.
        quality:       Compression quality 1–100 (default 75).
        max_width:     Resize if wider than this value (preserves aspect ratio).
        max_height:    Resize if taller than this value (preserves aspect ratio).
        output_format: Force output format ('JPEG', 'PNG', 'WEBP', etc.).

    Returns:
        dict with keys: original_size, compressed_size, width, height, savings_pct
    """
    original_size = input_path.stat().st_size

    with Image.open(input_path) as img:
        # Convert palette / RGBA for JPEG output
        if output_format == "JPEG" or (
            output_format is None and output_path.suffix.lower() in (".jpg", ".jpeg")
        ):
            if img.mode in ("RGBA", "P", "LA"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                mask = img.convert("RGBA").split()[3] if img.mode != "P" else None
                background.paste(img.convert("RGBA"), mask=mask)
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")

        # Resize if needed
        orig_w, orig_h = img.size
        new_w, new_h = orig_w, orig_h

        if max_width and new_w > max_width:
            ratio = max_width / new_w
            new_w = max_width
            new_h = int(new_h * ratio)

        if max_height and new_h > max_height:
            ratio = max_height / new_h
            new_h = max_height
            new_w = int(new_w * ratio)

        if (new_w, new_h) != (orig_w, orig_h):
            img = img.resize((new_w, new_h), Image.LANCZOS)

        # Determine format
        fmt = output_format or FORMAT_MAP.get(output_path.suffix.lower(), "JPEG")

        save_kwargs = {}
        if fmt == "JPEG":
            save_kwargs = {"quality": quality, "optimize": True, "progressive": True}
        elif fmt == "PNG":
            # PNG compression level 0–9; map quality 1–100 → level 9–0
            level = max(0, min(9, 9 - round(quality / 11)))
            save_kwargs = {"optimize": True, "compress_level": level}
        elif fmt == "WEBP":
            save_kwargs = {"quality": quality, "method": 6}
        elif fmt == "GIF":
            save_kwargs = {"optimize": True}

        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, format=fmt, **save_kwargs)

    compressed_size = output_path.stat().st_size
    savings = round((1 - compressed_size / original_size) * 100, 1) if original_size else 0

    return {
        "original_size": original_size,
        "compressed_size": compressed_size,
        "original_dimensions": (orig_w, orig_h),
        "new_dimensions": (new_w, new_h),
        "savings_pct": savings,
    }
