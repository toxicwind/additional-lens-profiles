"""End-to-end test: parse → split → export."""
import pytest
import tempfile
import os

from volume.parsers.epub3 import EPUB3Parser
from volume.splitters.size import SizeSplitter
from volume.exporters.epub import EPUBExporter


def test_end_to_end_placeholder():
    """Placeholder until we have a test EPUB."""
    assert True  # TODO: generate minimal EPUB for testing
