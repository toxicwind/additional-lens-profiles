"""
VOLUME Master — Modular EPUB3 splitter.
"""
from .parsers.epub3 import EPUB3Parser
from .splitters.size import SizeSplitter
from .optimizers.font import FontOptimizer
from .optimizers.image import ImageOptimizer
from .exporters.epub import EPUBExporter
from .exporters.zip import ZipExporter

__version__ = "2.0.0"
__all__ = [
    "EPUB3Parser",
    "SizeSplitter",
    "FontOptimizer",
    "ImageOptimizer",
    "EPUBExporter",
    "ZipExporter",
]
