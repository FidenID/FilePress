#!/usr/bin/env python3
"""
FilePress — Universal File Compressor CLI
"""

import sys
import argparse
import traceback
from pathlib import Path
from typing import Optional

from compressor import __version__
from compressor.utils import (
    compress_file,
    build_output_path,
    human_size,
    savings_str,
    detect_type,
    all_supported_extensions,
)

# ── Optional rich output ─────────────────────────────────────────────────────
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
    from rich.panel import Panel
    from rich import print as rprint
    RICH = True
    console = Console()
except ImportError:
    RICH = False
    console = None


# ── Helpers ──────────────────────────────────────────────────────────────────

def _print_banner():
    if RICH:
        console.print(
            Panel.fit(
                f"[bold green]FilePress[/bold green] [dim]v{__version__}[/dim]  "
                "— Universal File Compressor\n"
                "[dim]Supports: Images · PDF · Video · Audio · Archives[/dim]",
                border_style="green",
            )
        )
    else:
        print(f"\n  FilePress v{__version__} — Universal File Compressor")
        print("  Supports: Images · PDF · Video · Audio · Archives\n")


def _print_result(result: dict, verbose: bool = False):
    orig = result["original_size"]
    comp = result["compressed_size"]
    inp  = result["input_path"]
    out  = result["output_path"]
    pct  = result.get("savings_pct", 0)

    if RICH:
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(style="dim", width=18)
        table.add_column()

        table.add_row("Input",       str(inp))
        table.add_row("Output",      str(out))
        table.add_row("Original",    human_size(orig))
        table.add_row("Compressed",  human_size(comp))
        color = "green" if pct >= 0 else "red"
        table.add_row("Savings",     f"[{color}]{savings_str(orig, comp)}[/{color}]")

        if verbose:
            for k, v in result.items():
                if k not in ("original_size","compressed_size","savings_pct",
                             "input_path","output_path","file_type"):
                    table.add_row(k.replace("_"," ").title(), str(v))

        console.print(table)
    else:
        print(f"  Input     : {inp}")
        print(f"  Output    : {out}")
        print(f"  Original  : {human_size(orig)}")
        print(f"  Compressed: {human_size(comp)}")
        print(f"  Savings   : {savings_str(orig, comp)}")


def _resolve_files(paths: list[str], recursive: bool) -> list[Path]:
    """Expand paths, resolve globs, recurse directories."""
    result = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            if recursive:
                result.extend(f for f in p.rglob("*") if f.is_file())
            else:
                result.extend(f for f in p.iterdir() if f.is_file())
        elif p.exists():
            result.append(p)
        else:
            # Try glob
            matched = list(Path(".").glob(raw))
            if matched:
                result.extend(f for f in matched if f.is_file())
            else:
                print(f"  Warning: '{raw}' not found — skipping.", file=sys.stderr)
    return result


# ── CLI definition ───────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="filepress",
        description="FilePress — compress images, PDFs, videos, audio, and archives.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  filepress photo.jpg
  filepress photo.jpg -q 60 -o compressed/
  filepress document.pdf -q 50
  filepress video.mp4 -q 70 --max-width 1280
  filepress audio.wav -o audio.mp3 -q 80
  filepress *.png -o output/ -q 65 --format webp
  filepress folder/ -r -o compressed/ -q 75
        """,
    )

    parser.add_argument("files", nargs="+", metavar="FILE", help="Input file(s) or directory/directories")
    parser.add_argument("-o", "--output", metavar="PATH",
                        help="Output file or directory (default: <stem>_compressed.<ext> next to input)")
    parser.add_argument("-q", "--quality", type=int, default=75, metavar="1-100",
                        help="Compression quality 1–100 (default: 75)")
    parser.add_argument("--format", metavar="EXT",
                        help="Force output format/extension, e.g. webp, mp3, zip")
    parser.add_argument("--max-width", type=int, metavar="PX",
                        help="[Image/Video] Resize if wider than PX (preserves aspect ratio)")
    parser.add_argument("--max-height", type=int, metavar="PX",
                        help="[Image] Resize if taller than PX (preserves aspect ratio)")
    parser.add_argument("--audio-bitrate", default="128k", metavar="BITRATE",
                        help="[Video] Audio bitrate (default: 128k)")
    parser.add_argument("-r", "--recursive", action="store_true",
                        help="Recurse into directories")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Show extra compression details")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be compressed without doing it")
    parser.add_argument("--list-formats", action="store_true",
                        help="List all supported file extensions and exit")
    parser.add_argument("--version", action="version", version=f"FilePress {__version__}")

    return parser


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.list_formats:
        exts = all_supported_extensions()
        print("\n  Supported extensions:\n")
        col = 8
        for i in range(0, len(exts), col):
            print("  " + "  ".join(f"{e:10}" for e in exts[i:i+col]))
        print()
        return

    _print_banner()

    # Validate quality
    if not (1 <= args.quality <= 100):
        print("  Error: --quality must be between 1 and 100.", file=sys.stderr)
        sys.exit(1)

    # Resolve input files
    input_files = _resolve_files(args.files, args.recursive)
    # Filter to supported types only
    supported = [f for f in input_files if detect_type(f) is not None]
    skipped   = [f for f in input_files if detect_type(f) is None]

    if not supported:
        print("  No supported files found.", file=sys.stderr)
        print(f"  Run 'filepress --list-formats' to see what's supported.")
        sys.exit(1)

    if skipped:
        for f in skipped:
            print(f"  Skipping unsupported: {f}", file=sys.stderr)

    # Determine output directory vs single-file output
    output_arg = Path(args.output) if args.output else None
    output_is_dir = (
        output_arg is not None and (output_arg.is_dir() or (
            len(supported) > 1 and not output_arg.suffix
        ))
    )

    # Force output format
    suffix = None
    if args.format:
        suffix = args.format if args.format.startswith(".") else f".{args.format}"

    total_orig = 0
    total_comp = 0
    errors = 0
    success = 0

    if RICH:
        progress_ctx = Progress(
            SpinnerColumn(),
            TextColumn("[bold]{task.description}"),
            BarColumn(),
            TextColumn("[dim]{task.completed}/{task.total}"),
            TimeElapsedColumn(),
            console=console,
        )
    else:
        progress_ctx = None

    def process_files():
        nonlocal total_orig, total_comp, errors, success

        for i, inp in enumerate(supported, 1):
            # Build output path
            if output_arg and not output_is_dir and len(supported) == 1:
                out = output_arg
                if suffix:
                    out = out.with_suffix(suffix)
            else:
                out = build_output_path(
                    inp,
                    output_dir=output_arg if output_is_dir else None,
                    suffix=suffix,
                )

            if args.dry_run:
                print(f"  [DRY RUN] {inp}  →  {out}")
                continue

            try:
                result = compress_file(
                    inp, out,
                    quality=args.quality,
                    max_width=args.max_width,
                    max_height=args.max_height,
                    audio_bitrate=args.audio_bitrate,
                )
                total_orig += result["original_size"]
                total_comp += result["compressed_size"]
                success += 1

                if RICH:
                    console.rule(f"[dim]{i}/{len(supported)}[/dim] {inp.name}")
                else:
                    print(f"\n  [{i}/{len(supported)}] {inp.name}")

                _print_result(result, verbose=args.verbose)

            except Exception as e:
                errors += 1
                msg = f"  Error compressing '{inp}': {e}"
                if RICH:
                    console.print(f"[red]{msg}[/red]")
                else:
                    print(msg, file=sys.stderr)
                if args.verbose:
                    traceback.print_exc()

    process_files()

    if args.dry_run:
        return

    # Summary
    if len(supported) > 1:
        print()
        if RICH:
            console.rule("[bold green]Summary[/bold green]")
            console.print(
                f"  Files processed: [green]{success}[/green]  "
                f"Errors: [red]{errors}[/red]\n"
                f"  Total original:   [bold]{human_size(total_orig)}[/bold]\n"
                f"  Total compressed: [bold]{human_size(total_comp)}[/bold]\n"
                f"  Overall savings:  [bold green]{savings_str(total_orig, total_comp)}[/bold green]"
            )
        else:
            print(f"  Files processed : {success}  Errors: {errors}")
            print(f"  Total original  : {human_size(total_orig)}")
            print(f"  Total compressed: {human_size(total_comp)}")
            print(f"  Overall savings : {savings_str(total_orig, total_comp)}")

    sys.exit(0 if errors == 0 else 1)


if __name__ == "__main__":
    main()
