<div align="center">

# 🗜️ FilePress

**Universal File Compressor — Images · PDF · Video · Audio · Archives**

[![CI](https://github.com/yourusername/filepress/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/filepress/actions)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Compress almost any file from the command line — fast, local, no uploads, no subscriptions.

```
filepress photo.jpg -q 60                  # compress image at 60% quality
filepress doc.pdf -q 50 -o small.pdf       # compress PDF
filepress video.mp4 -q 70 --max-width 1280 # compress video
filepress *.png -o out/ --format webp      # batch convert to WebP
filepress folder/ -r -o compressed/        # recursively compress a folder
```

</div>

---

## ✨ Features

| Category | Formats | Engine |
|----------|---------|--------|
| 🖼️ **Images** | JPG, PNG, WebP, GIF, BMP, TIFF | Pillow |
| 📄 **PDF** | .pdf | Ghostscript / pikepdf |
| 🎬 **Video** | MP4, MOV, AVI, MKV, WMV, WebM, M4V | FFmpeg (H.264) |
| 🎵 **Audio** | MP3, WAV, FLAC, AAC, OGG, M4A, Opus | FFmpeg |
| 📦 **Archives** | ZIP, GZ, BZ2, XZ, TAR, TAR.GZ, TAR.BZ2, TAR.XZ | Python stdlib |

- **Batch processing** — compress dozens of files in one command
- **Smart routing** — auto-detects file type, picks the right engine
- **Resize on the fly** — `--max-width` / `--max-height` for images and video
- **Format conversion** — compress a PNG and output WebP in one step
- **Beautiful output** — progress bars and color summaries via `rich`
- **Recursive** — compress entire directory trees with `-r`
- **Dry run** — preview what would happen without touching files

---

## 📋 Requirements

### Python packages (auto-installed)
```
Pillow >= 10.0      # images
pikepdf >= 8.0      # PDF fallback
rich >= 13.0        # pretty output
```

### System tools (install separately — only needed for those file types)

| Tool | Used for | Install |
|------|----------|---------|
| **Ghostscript** | PDF compression (recommended) | [ghostscript.com](https://www.ghostscript.com/download.html) |
| **FFmpeg** | Video & audio compression | [ffmpeg.org](https://ffmpeg.org/download.html) |

> **Note:** You don't need all tools. FilePress gracefully skips video/audio if FFmpeg isn't installed, and falls back to `pikepdf` for PDFs if Ghostscript isn't found.

---

## 🚀 Installation

### Option 1 — Clone & install (recommended for development)

```bash
git clone https://github.com/yourusername/filepress.git
cd filepress
pip install -r requirements.txt
```

Run directly:
```bash
python filepress.py photo.jpg -q 75
```

### Option 2 — Install as CLI tool

```bash
pip install .
filepress photo.jpg -q 75
```

### Option 3 — Virtual environment (clean & isolated)

```bash
git clone https://github.com/yourusername/filepress.git
cd filepress
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python filepress.py --help
```

---

## 📖 Usage

```
usage: filepress [-h] [-o PATH] [-q 1-100] [--format EXT]
                 [--max-width PX] [--max-height PX]
                 [--audio-bitrate BITRATE] [-r] [-v] [--dry-run]
                 [--list-formats] [--version]
                 FILE [FILE ...]
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `-o`, `--output` | Output file or directory | `<stem>_compressed.<ext>` next to input |
| `-q`, `--quality` | Quality level 1–100 | `75` |
| `--format` | Force output extension (e.g. `webp`, `mp3`, `zip`) | same as input |
| `--max-width` | Resize if wider than N pixels (image / video) | — |
| `--max-height` | Resize if taller than N pixels (image only) | — |
| `--audio-bitrate` | Audio bitrate for video compression | `128k` |
| `-r`, `--recursive` | Recurse into directories | off |
| `-v`, `--verbose` | Show extra details per file | off |
| `--dry-run` | Preview actions without compressing | off |
| `--list-formats` | Print all supported extensions | — |

---

## 💡 Examples

### Images

```bash
# Basic JPEG compression
filepress photo.jpg -q 60

# Resize and convert to WebP
filepress photo.jpg --max-width 1280 --format webp -o out/

# Batch compress all PNGs in a folder, output to 'compressed/'
filepress *.png -o compressed/ -q 70

# Recursively compress all images under a directory
filepress pictures/ -r -o compressed/ -q 75
```

### PDF

```bash
# Compress a PDF (uses Ghostscript if installed, else pikepdf)
filepress report.pdf -q 50 -o report_small.pdf

# Lower quality = smaller file size (good for web sharing)
filepress thesis.pdf -q 30
```

### Video

```bash
# Compress MP4 with default quality
filepress video.mp4 -q 70

# Resize and compress
filepress 4k_video.mp4 --max-width 1920 -q 75 -o hd_video.mp4

# Compress with lower audio bitrate
filepress video.mp4 -q 70 --audio-bitrate 96k
```

### Audio

```bash
# Compress WAV to MP3
filepress recording.wav --format mp3 -q 70

# Convert FLAC to AAC
filepress music.flac --format m4a -q 80
```

### Archives

```bash
# Compress a file to ZIP
filepress bigfile.csv --format zip

# Compress a whole directory to tar.gz
filepress project/ --format .tar.gz -o project_backup.tar.gz

# Maximum compression (quality 1 = most compressed)
filepress data.json --format xz -q 5
```

### Dry run

```bash
# Preview what would be compressed without touching any file
filepress *.jpg -o out/ --dry-run
```

---

## 🧠 How quality maps to each engine

| File type | Quality 1–100 maps to |
|-----------|----------------------|
| **JPEG** | `quality` parameter (1–100) |
| **PNG** | compress level 9→0 (inverted: higher quality = less compression) |
| **WebP** | `quality` parameter (1–100) |
| **PDF** | Ghostscript preset: screen → ebook → printer → prepress |
| **Video** | H.264 CRF 51→18 (inverted: higher quality = lower CRF) |
| **Audio** | Bitrate 32→320 kbps |
| **ZIP/GZ/BZ2/XZ** | Compression level 1→9 |

---

## 🗂️ Project Structure

```
filepress/
├── compressor/
│   ├── __init__.py     # version, metadata
│   ├── image.py        # Image compression (Pillow)
│   ├── pdf.py          # PDF compression (Ghostscript / pikepdf)
│   ├── video.py        # Video compression (FFmpeg)
│   ├── audio.py        # Audio compression (FFmpeg)
│   ├── archive.py      # Archive compression (stdlib)
│   └── utils.py        # File routing, helpers, dispatch
├── tests/
│   └── test_compressor.py
├── .github/
│   └── workflows/
│       └── ci.yml      # GitHub Actions CI
├── filepress.py        # CLI entry point
├── setup.py
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
├── .gitignore
└── README.md
```

---

## 🧪 Development

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=compressor --cov-report=term-missing

# Format code
black compressor/ filepress.py

# Lint
ruff check compressor/ filepress.py

# Type check
mypy compressor/ --ignore-missing-imports
```

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/add-svg-support`)
3. Commit your changes (`git commit -m 'feat: add SVG compression'`)
4. Push to the branch (`git push origin feature/add-svg-support`)
5. Open a Pull Request

Please make sure tests pass and code is formatted with `black` before submitting.

---

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

<div align="center">
Made with ☕ and Python · <a href="https://github.com/yourusername/filepress/issues">Report a bug</a> · <a href="https://github.com/yourusername/filepress/issues">Request a feature</a>
</div>
