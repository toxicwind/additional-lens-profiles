#!/usr/bin/env python3
"""
Agentic orchestrator for VOLUME Master.
DAG: Researcher → Optimizer → Validator → Publisher
"""
from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass, field
from typing import Any

from rich.console import Console
from rich.progress import Progress

from volume.parsers.epub3 import EPUB3Parser
from volume.splitters.size import SizeSplitter
from volume.optimizers.font import FontOptimizer
from volume.optimizers.image import ImageOptimizer
from volume.exporters.epub import EPUBExporter
from volume.exporters.zip import ZipExporter
from musepool import ProcessPool

console = Console()


@dataclass
class AgentDecision:
    agent: str
    action: str
    params: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0


class ResearcherAgent:
    """Analyzes EPUB structure, identifies content types."""

    def analyze(self, book_path: str) -> dict[str, Any]:
        parser = EPUB3Parser()
        book = parser.parse(book_path)

        decisions = []

        # Decide if font optimization needed
        if len(book.fonts) > 0:
            decisions.append(AgentDecision(
                "researcher", "font_optimize",
                {"fonts": len(book.fonts), "reason": "Large font files detected"},
                0.9,
            ))

        # Decide if image optimization needed
        total_img_size = sum(len(d) for d in book.images.values())
        if total_img_size > 50 * 1024 * 1024:  # >50MB images
            decisions.append(AgentDecision(
                "researcher", "image_optimize",
                {"image_mb": total_img_size / (1024 * 1024)},
                0.95,
            ))

        # Decide split strategy
        if book.total_bytes > 100 * 1024 * 1024:
            decisions.append(AgentDecision(
                "researcher", "split",
                {"max_mb": 45, "reason": f"{book.total_bytes / (1024*1024):.0f}MB exceeds LMS limit"},
                1.0,
            ))

        return {
            "book": book,
            "decisions": decisions,
            "recommendations": [d.action for d in decisions],
        }


class OptimizerAgent:
    """Decides compression strategy based on researcher output."""

    async def optimize(self, analysis: dict[str, Any]) -> dict[str, Any]:
        book = analysis["book"]
        decisions = analysis["decisions"]

        config = {
            "split": False,
            "split_max_mb": 45,
            "optimize_fonts": False,
            "optimize_images": False,
            "image_format": "WEBP",
            "image_quality": 85,
        }

        for decision in decisions:
            if decision.action == "font_optimize":
                config["optimize_fonts"] = True
            elif decision.action == "image_optimize":
                config["optimize_images"] = True
                config["image_format"] = "WEBP"
            elif decision.action == "split":
                config["split"] = True
                config["split_max_mb"] = decision.params.get("max_mb", 45)

        return {"book": book, "config": config}


class ValidatorAgent:
    """Validates output against LMS requirements."""

    def validate(self, volume_paths: list[str], config: dict[str, Any]) -> dict[str, Any]:
        issues = []

        for path in volume_paths:
            size = os.path.getsize(path)
            if size > 50 * 1024 * 1024:
                issues.append(f"{os.path.basename(path)}: {size/(1024*1024):.1f}MB > 50MB LMS limit")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "volume_count": len(volume_paths),
        }


class PublisherAgent:
    """Packages and publishes final output."""

    def publish(self, volume_paths: list[str], out_dir: str) -> dict[str, Any]:
        zip_path = os.path.join(out_dir, "VOLUME_MASTER_OUTPUT.zip")
        ZipExporter().export(volume_paths, zip_path)

        manifest = {
            "version": "2.0.0",
            "volumes": [
                {"file": os.path.basename(p), "size_mb": os.path.getsize(p)/(1024*1024)}
                for p in volume_paths
            ],
            "total_size_mb": sum(os.path.getsize(p) for p in volume_paths) / (1024 * 1024),
        }

        manifest_path = os.path.join(out_dir, "manifest.json")
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        return {"zip": zip_path, "manifest": manifest_path}


async def run_agentic_pipeline(input_path: str, output_dir: str = "./data/output") -> dict[str, Any]:
    """Run the full agentic DAG."""
    os.makedirs(output_dir, exist_ok=True)

    console.print("[bold blue]VOLUME Master Agentic Pipeline[/bold blue]")

    # Researcher
    console.print("[cyan]→ Researcher[/cyan] analyzing EPUB...")
    researcher = ResearcherAgent()
    analysis = researcher.analyze(input_path)
    console.print(f"  Recommendations: {', '.join(analysis['recommendations'])}")

    # Optimizer
    console.print("[cyan]→ Optimizer[/cyan] deciding strategy...")
    optimizer = OptimizerAgent()
    optimized = await optimizer.optimize(analysis)
    config = optimized["config"]
    console.print(f"  Config: {json.dumps(config, indent=2)}")

    # Execute splitting
    book = analysis["book"]
    volume_paths = []

    if config["split"]:
        console.print("[cyan]→ Splitting[/cyan] into volumes...")
        splitter = SizeSplitter(max_mb=config["split_max_mb"])
        plans = splitter.plan(book)

        exporter = EPUBExporter()

        # Parallel processing with musepool
        async with ProcessPool() as pool:
            if config["optimize_images"] or config["optimize_fonts"]:
                await pool.map(SizeSplitter.split_chapter, book.chapters, book.images)

        for plan in plans:
            path = os.path.join(output_dir, f"VOLUME_Vol{plan.volume_index:02d}_of_{len(plans):02d}.epub")
            exporter.export(book, plan, len(plans), path)
            volume_paths.append(path)
    else:
        # Single volume
        path = os.path.join(output_dir, "VOLUME_Single.epub")
        exporter.export(book, SizeSplitter(max_mb=999).plan(book)[0], 1, path)
        volume_paths.append(path)

    # Validator
    console.print("[cyan]→ Validator[/cyan] checking LMS compliance...")
    validator = ValidatorAgent()
    validation = validator.validate(volume_paths, config)
    if not validation["valid"]:
        for issue in validation["issues"]:
            console.print(f"  [red]✗ {issue}[/red]")
    else:
        console.print("  [green]✓ All volumes pass LMS checks[/green]")

    # Publisher
    console.print("[cyan]→ Publisher[/cyan] packaging output...")
    publisher = PublisherAgent()
    published = publisher.publish(volume_paths, output_dir)
    console.print(f"  [green]✓[/green] ZIP: {published['zip']}")
    console.print(f"  [green]✓[/green] Manifest: {published['manifest']}")

    return {
        "volumes": volume_paths,
        "validation": validation,
        "published": published,
        "config": config,
    }


def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: volume-agent <input.epub> [output_dir]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./data/output"
    asyncio.run(run_agentic_pipeline(input_path, output_dir))


if __name__ == "__main__":
    main()
