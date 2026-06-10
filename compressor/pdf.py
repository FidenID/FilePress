"""
PDF compression module — uses Ghostscript when available, falls back to pikepdf.
"""

from pathlib import Path
import shutil
import subprocess


SUPPORTED_FORMATS = {".pdf"}

# Ghostscript preset → target DPI / compression trade-off
GS_PRESETS = {
    "screen":   72,   # lowest quality, smallest file (screen viewing)
    "ebook":    150,  # good for e-readers
    "printer":  300,  # high quality (printing)
    "prepress": 300,  # very high quality (professional prepress)
}

QUALITY_TO_PRESET = {
    range(1,  30): "screen",
    range(30, 60): "ebook",
    range(60, 85): "printer",
    range(85, 101): "prepress",
}


def _get_gs_preset(quality: int) -> str:
    for rng, preset in QUALITY_TO_PRESET.items():
        if quality in rng:
            return preset
    return "ebook"


def _ghostscript_available() -> bool:
    return shutil.which("gs") is not None or shutil.which("gswin64c") is not None


def _gs_executable() -> str:
    return shutil.which("gs") or shutil.which("gswin64c") or "gs"


def _compress_with_ghostscript(input_path: Path, output_path: Path, quality: int) -> bool:
    """Returns True on success."""
    preset = _get_gs_preset(quality)
    cmd = [
        _gs_executable(),
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS=/{preset}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={output_path}",
        str(input_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=120)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _compress_with_pikepdf(input_path: Path, output_path: Path, quality: int) -> bool:
    """Returns True on success."""
    try:
        import pikepdf
        with pikepdf.open(input_path) as pdf:
            pdf.save(
                output_path,
                compress_streams=True,
                recompress_flate=True,
                object_stream_mode=pikepdf.ObjectStreamMode.generate,
            )
        return True
    except ImportError:
        raise RuntimeError(
            "PDF compression requires either Ghostscript (recommended) or pikepdf.\n"
            "  Install pikepdf:     pip install pikepdf\n"
            "  Install Ghostscript: https://www.ghostscript.com/download.html"
        )
    except Exception as e:
        raise RuntimeError(f"pikepdf compression failed: {e}")


def compress(
    input_path: Path,
    output_path: Path,
    quality: int = 72,
    **_kwargs,
) -> dict:
    """
    Compress a PDF file.

    Args:
        input_path:  Source PDF file path.
        output_path: Destination PDF file path.
        quality:     1–100 — mapped to Ghostscript PDFSETTINGS preset.

    Returns:
        dict with keys: original_size, compressed_size, savings_pct, method
    """
    original_size = input_path.stat().st_size
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if _ghostscript_available():
        ok = _compress_with_ghostscript(input_path, output_path, quality)
        method = "ghostscript"
        if not ok:
            # Fallback to pikepdf
            _compress_with_pikepdf(input_path, output_path, quality)
            method = "pikepdf"
    else:
        _compress_with_pikepdf(input_path, output_path, quality)
        method = "pikepdf"

    # If output is larger or equal, copy original (nothing gained)
    compressed_size = output_path.stat().st_size
    if compressed_size >= original_size:
        import shutil as _shutil
        _shutil.copy2(input_path, output_path)
        compressed_size = original_size

    savings = round((1 - compressed_size / original_size) * 100, 1) if original_size else 0

    return {
        "original_size": original_size,
        "compressed_size": compressed_size,
        "savings_pct": savings,
        "method": method,
    }
