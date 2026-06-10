"""
Tests for FilePress compressor modules.
Run with: pytest tests/ -v
"""

import io
import sys
import pytest
from pathlib import Path
from PIL import Image


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def sample_jpeg(tmp_path):
    """Create a simple JPEG test image."""
    img = Image.new("RGB", (800, 600), color=(180, 100, 60))
    path = tmp_path / "sample.jpg"
    img.save(path, "JPEG", quality=95)
    return path


@pytest.fixture
def sample_png(tmp_path):
    """Create a simple PNG test image with transparency."""
    img = Image.new("RGBA", (400, 300), color=(50, 120, 200, 200))
    path = tmp_path / "sample.png"
    img.save(path, "PNG")
    return path


@pytest.fixture
def sample_text_file(tmp_path):
    """Create a plain text file for archive testing."""
    p = tmp_path / "sample.txt"
    p.write_text("Hello, FilePress!\n" * 500)
    return p


# ── Image tests ───────────────────────────────────────────────────────────────

class TestImageCompression:

    def test_jpeg_basic(self, sample_jpeg, tmp_dir):
        from compressor.image import compress
        out = tmp_dir / "out.jpg"
        result = compress(sample_jpeg, out, quality=60)

        assert out.exists()
        assert result["original_size"] > 0
        assert result["compressed_size"] > 0
        assert "savings_pct" in result

    def test_jpeg_resize(self, sample_jpeg, tmp_dir):
        from compressor.image import compress
        out = tmp_dir / "out_small.jpg"
        result = compress(sample_jpeg, out, quality=75, max_width=400)

        assert result["new_dimensions"][0] <= 400
        # Height should scale proportionally
        assert result["new_dimensions"][1] == 300  # 600 * (400/800)

    def test_png_to_webp(self, sample_png, tmp_dir):
        from compressor.image import compress
        out = tmp_dir / "out.webp"
        result = compress(sample_png, out, quality=80, output_format="WEBP")

        assert out.exists()
        assert result["compressed_size"] > 0

    def test_rgba_to_jpeg_no_error(self, sample_png, tmp_dir):
        """RGBA PNG converted to JPEG should not raise — alpha channel handled."""
        from compressor.image import compress
        out = tmp_dir / "out.jpg"
        result = compress(sample_png, out, quality=75)
        assert out.exists()

    def test_no_upscale(self, tmp_path, tmp_dir):
        """max_width larger than image width should not upscale."""
        from compressor.image import compress
        img = Image.new("RGB", (200, 150), "blue")
        p = tmp_path / "tiny.jpg"
        img.save(p, "JPEG", quality=90)

        out = tmp_dir / "out.jpg"
        result = compress(p, out, quality=75, max_width=1920)
        assert result["new_dimensions"] == (200, 150)


# ── Archive tests ─────────────────────────────────────────────────────────────

class TestArchiveCompression:

    def test_zip(self, sample_text_file, tmp_dir):
        from compressor.archive import compress
        out = tmp_dir / "out.zip"
        result = compress(sample_text_file, out, quality=75)

        assert out.exists()
        assert result["compressed_size"] < result["original_size"]

    def test_gzip(self, sample_text_file, tmp_dir):
        from compressor.archive import compress
        out = tmp_dir / "out.gz"
        result = compress(sample_text_file, out, quality=75)

        assert out.exists()
        assert result["compressed_size"] > 0

    def test_xz(self, sample_text_file, tmp_dir):
        from compressor.archive import compress
        out = tmp_dir / "out.xz"
        result = compress(sample_text_file, out, quality=75)

        assert out.exists()
        assert result["compressed_size"] > 0

    def test_directory_to_zip(self, tmp_path, tmp_dir):
        from compressor.archive import compress
        # Create a small directory
        d = tmp_path / "mydir"
        d.mkdir()
        (d / "a.txt").write_text("hello " * 100)
        (d / "b.txt").write_text("world " * 100)

        out = tmp_dir / "mydir.zip"
        result = compress(d, out, quality=75)
        assert out.exists()
        assert result["compressed_size"] > 0

    def test_unsupported_format(self, sample_text_file, tmp_dir):
        from compressor.archive import compress
        out = tmp_dir / "out.unknownext"
        with pytest.raises(ValueError, match="Unsupported archive format"):
            compress(sample_text_file, out)


# ── Utils tests ───────────────────────────────────────────────────────────────

class TestUtils:

    def test_detect_type_image(self):
        from compressor.utils import detect_type
        assert detect_type(Path("photo.jpg")) == "image"
        assert detect_type(Path("photo.PNG")) == "image"
        assert detect_type(Path("anim.gif")) == "image"

    def test_detect_type_pdf(self):
        from compressor.utils import detect_type
        assert detect_type(Path("doc.pdf")) == "pdf"

    def test_detect_type_video(self):
        from compressor.utils import detect_type
        assert detect_type(Path("movie.mp4")) == "video"
        assert detect_type(Path("clip.mov")) == "video"

    def test_detect_type_audio(self):
        from compressor.utils import detect_type
        assert detect_type(Path("song.mp3")) == "audio"
        assert detect_type(Path("song.flac")) == "audio"

    def test_detect_type_unknown(self):
        from compressor.utils import detect_type
        assert detect_type(Path("file.docx")) is None
        assert detect_type(Path("script.py")) is None

    def test_human_size(self):
        from compressor.utils import human_size
        assert human_size(500) == "500.0 B"
        assert "KB" in human_size(2048)
        assert "MB" in human_size(2 * 1024 * 1024)

    def test_savings_str_positive(self):
        from compressor.utils import savings_str
        s = savings_str(1000, 700)
        assert "30.0%" in s
        assert "↓" in s

    def test_savings_str_negative(self):
        from compressor.utils import savings_str
        s = savings_str(700, 1000)
        assert "↑" in s

    def test_build_output_path_default(self):
        from compressor.utils import build_output_path
        p = build_output_path(Path("/home/user/photo.jpg"))
        assert p.name == "photo_compressed.jpg"
        assert p.parent == Path("/home/user")

    def test_build_output_path_with_dir(self, tmp_path):
        from compressor.utils import build_output_path
        p = build_output_path(Path("/home/user/photo.jpg"), output_dir=tmp_path)
        assert p.parent == tmp_path
        assert "compressed" in p.name

    def test_build_output_path_with_suffix(self):
        from compressor.utils import build_output_path
        p = build_output_path(Path("/home/user/photo.jpg"), suffix=".webp")
        assert p.suffix == ".webp"
