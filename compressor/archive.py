"""
Archive compression module — ZIP, GZIP, BZIP2, XZ, TAR, 7Z.
Also handles generic files/folders via ZIP or tar.
"""

from pathlib import Path
import gzip
import bz2
import lzma
import shutil
import zipfile
import tarfile


SUPPORTED_FORMATS = {".zip", ".gz", ".bz2", ".xz", ".tar", ".7z", ".zst"}

# Map output suffix → handler
COMPRESS_DISPATCH = {
    ".zip":  "_zip",
    ".gz":   "_gzip",
    ".bz2":  "_bzip2",
    ".xz":   "_xz",
    ".tar":  "_tar",
}


def _quality_to_zip_level(quality: int) -> int:
    """Map quality 1–100 → ZIP compression level 1–9."""
    return max(1, min(9, round(quality / 100 * 9)))


def _zip(input_path: Path, output_path: Path, quality: int):
    level = _quality_to_zip_level(quality)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=level) as zf:
        if input_path.is_dir():
            for f in input_path.rglob("*"):
                if f.is_file():
                    zf.write(f, f.relative_to(input_path.parent))
        else:
            zf.write(input_path, input_path.name)


def _gzip(input_path: Path, output_path: Path, quality: int):
    level = _quality_to_zip_level(quality)
    if input_path.is_dir():
        raise ValueError("GZIP cannot compress directories — use .tar.gz instead.")
    with open(input_path, "rb") as f_in, gzip.open(output_path, "wb", compresslevel=level) as f_out:
        shutil.copyfileobj(f_in, f_out)


def _bzip2(input_path: Path, output_path: Path, quality: int):
    level = max(1, min(9, round(quality / 100 * 9)))
    if input_path.is_dir():
        raise ValueError("BZIP2 cannot compress directories — use .tar.bz2 instead.")
    with open(input_path, "rb") as f_in, bz2.open(output_path, "wb", compresslevel=level) as f_out:
        shutil.copyfileobj(f_in, f_out)


def _xz(input_path: Path, output_path: Path, quality: int):
    preset = max(0, min(9, round(quality / 100 * 9)))
    if input_path.is_dir():
        raise ValueError("XZ cannot compress directories — use .tar.xz instead.")
    with open(input_path, "rb") as f_in, lzma.open(output_path, "wb", preset=preset) as f_out:
        shutil.copyfileobj(f_in, f_out)


def _tar(input_path: Path, output_path: Path, quality: int):
    """Creates a plain tar (no compression). For compressed tar, use .tar.gz etc."""
    with tarfile.open(output_path, "w") as tf:
        tf.add(input_path, arcname=input_path.name)


_HANDLERS = {
    ".zip": _zip,
    ".gz":  _gzip,
    ".bz2": _bzip2,
    ".xz":  _xz,
    ".tar": _tar,
}


def compress(
    input_path: Path,
    output_path: Path,
    quality: int = 75,
    **_kwargs,
) -> dict:
    """
    Compress a file or directory into an archive.

    Args:
        input_path:  Source file or directory path.
        output_path: Destination archive path (extension determines format).
        quality:     1–100 compression level.

    Returns:
        dict with keys: original_size, compressed_size, savings_pct
    """
    original_size = (
        sum(f.stat().st_size for f in input_path.rglob("*") if f.is_file())
        if input_path.is_dir()
        else input_path.stat().st_size
    )

    # Handle compound extensions like .tar.gz
    suffixes = output_path.suffixes
    ext = "".join(suffixes[-2:]) if len(suffixes) >= 2 else output_path.suffix.lower()

    # Compound tar formats
    tar_mode_map = {
        ".tar.gz":  "w:gz",
        ".tar.bz2": "w:bz2",
        ".tar.xz":  "w:xz",
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if ext in tar_mode_map:
        with tarfile.open(output_path, tar_mode_map[ext]) as tf:
            tf.add(input_path, arcname=input_path.name)
    else:
        handler = _HANDLERS.get(output_path.suffix.lower())
        if not handler:
            raise ValueError(
                f"Unsupported archive format: {output_path.suffix}\n"
                f"Supported: {', '.join(sorted(_HANDLERS.keys()))}"
            )
        handler(input_path, output_path, quality)

    compressed_size = output_path.stat().st_size
    savings = round((1 - compressed_size / original_size) * 100, 1) if original_size else 0

    return {
        "original_size": original_size,
        "compressed_size": compressed_size,
        "savings_pct": savings,
    }
