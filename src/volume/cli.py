#!/usr/bin/env python3
"""VOLUME Master CLI — split EPUBs from the command line."""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .parsers.epub3 import EPUB3Parser
from .splitters.size import SizeSplitter
from .exporters.epub import EPUBExporter
from .exporters.zip import ZipExporter
from musepool import ProcessPool

app = typer.Typer(help="VOLUME Master — EPUB3 splitter")
console = Console()


@app.command()
def split(
    input: str = typer.Argument(..., help="Input EPUB file"),
    max_mb: int = typer.Option(45, "--max-mb", "-m", help="Max MB per volume"),
    output: str = typer.Option("./data/output", "--output", "-o", help="Output directory"),
    optimize_fonts: bool = typer.Option(False, "--optimize-fonts", help="Subset fonts"),
    optimize_images: bool = typer.Option(False, "--optimize-images", help="Convert to WebP"),
    parallel: bool = typer.Option(True, "--parallel/--serial", help="Use musepool parallelism"),
):
    """Split an EPUB into LMS-ready volumes."""
    input_path = Path(input)
    if not input_path.exists():
        console.print(f"[red]File not found: {input}[/red]")
        raise typer.Exit(1)

    out_dir = Path(output)
    out_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"[bold blue]VOLUME Master[/bold blue] — splitting {input_path.name}")

    # Parse
    parser = EPUB3Parser()
    book = parser.parse(str(input_path))
    console.print(f"  Title: {book.title}")
    console.print(f"  Chapters: {len(book.chapters)} | Images: {len(book.images)} | MathML: {book.has_mathml}")

    # Plan
    splitter = SizeSplitter(max_mb=max_mb)
    plans = splitter.plan(book)
    console.print(f"  Split plan: {len(plans)} volume(s) @ {max_mb}MB max")

    # Export
    exporter = EPUBExporter()
    zip_exporter = ZipExporter()
    volume_paths = []

    async def do_export():
        if parallel and len(plans) > 1:
            async with ProcessPool() as pool:
                # Parallel chapter analysis (if optimizing)
                if optimize_images or optimize_fonts:
                    await pool.map(
                        SizeSplitter.split_chapter,
                        book.chapters,
                        book.images,
                    )

        for plan in plans:
            path = out_dir / f"VOLUME_Vol{plan.volume_index:02d}_of_{len(plans):02d}_{len(plan.chapters)}ch.epub"
            result = exporter.export(
                book, plan, len(plans), str(path),
                optimize_fonts=optimize_fonts,
                optimize_images=optimize_images,
            )
            volume_paths.append(str(path))
            console.print(f"  [green]✓[/green] Vol {plan.volume_index}: {result['size_mb']:.1f}MB")

    asyncio.run(do_export())

    # ZIP
    zip_path = out_dir / f"VOLUME_ALL_{len(plans)}_volumes.zip"
    zip_exporter.export(volume_paths, str(zip_path))
    console.print(f"  [green]✓[/green] ZIP: {zip_path.name}")

    # Summary table
    table = Table(title="Split Summary")
    table.add_column("Volume", style="cyan")
    table.add_column("Chapters", justify="right")
    table.add_column("Size (MB)", justify="right")
    for i, path in enumerate(volume_paths, 1):
        size = os.path.getsize(path) / (1024 * 1024)
        table.add_row(f"Vol {i}", str(plans[i-1].estimated_size), f"{size:.1f}")
    console.print(table)


@app.command()
def info(input: str = typer.Argument(..., help="Input EPUB file")):
    """Show EPUB metadata without splitting."""
    parser = EPUB3Parser()
    book = parser.parse(input)

    table = Table(title=f"EPUB Info: {book.title}")
    table.add_column("Property", style="cyan")
    table.add_column("Value")
    table.add_row("Title", book.title)
    table.add_row("Language", book.language)
    table.add_row("Authors", ", ".join(book.authors) or "Unknown")
    table.add_row("Chapters", str(len(book.chapters)))
    table.add_row("Images", str(len(book.images)))
    table.add_row("Fonts", str(len(book.fonts)))
    table.add_row("Styles", str(len(book.styles)))
    table.add_row("MathML", "Yes" if book.has_mathml else "No")
    table.add_row("Size (MB)", f"{book.total_bytes / (1024*1024):.1f}")
    console.print(table)


def main():
    app()


if __name__ == "__main__":
    main()
