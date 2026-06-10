from setuptools import setup, find_packages
from pathlib import Path

long_description = (Path(__file__).parent / "README.md").read_text(encoding="utf-8")

setup(
    name="filepress",
    version="1.0.0",
    author="Your Name",
    author_email="you@example.com",
    description="Universal file compressor — images, PDFs, video, audio, archives",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/filepress",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "Pillow>=10.0",       # image compression
        "pikepdf>=8.0",       # PDF compression (fallback when Ghostscript absent)
        "rich>=13.0",         # pretty CLI output (optional but recommended)
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov",
            "black",
            "ruff",
            "mypy",
        ],
    },
    entry_points={
        "console_scripts": [
            "filepress=filepress:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia",
        "Topic :: Utilities",
    ],
    keywords="compress image pdf video audio archive cli tool",
)
