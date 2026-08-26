"""
Image optimizer — converts PNG/TIFF to WebP, resizes if needed.
"""
from __future__ import annotations

import io
from typing import Any

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class ImageOptimizer:
    """Optimize images for LMS delivery."""

    def __init__(self, max_dimension: int = 2048, quality: int = 85, format: str = "WEBP"):
        self.max_dimension = max_dimension
        self.quality = quality
        self.format = format

    def optimize(self, image_data: bytes, filename: str) -> bytes | None:
        """Optimize a single image."""
        if not PIL_AVAILABLE:
            return None

        try:
            img = Image.open(io.BytesIO(image_data))

            # Resize if too large
            if max(img.size) > self.max_dimension:
                ratio = self.max_dimension / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, Image.LANCZOS)

            # Convert to target format
            out = io.BytesIO()
            if self.format == "WEBP":
                img.save(out, "WEBP", quality=self.quality, method=6)
            elif self.format == "JPEG":
                img = img.convert("RGB")
                img.save(out, "JPEG", quality=self.quality, optimize=True)
            else:
                img.save(out, self.format)

            return out.getvalue()
        except Exception:
            return None

    def should_optimize(self, filename: str) -> bool:
        """Check if file should be optimized."""
        ext = filename.lower().split(".")[-1] if "." in filename else ""
        return ext in ("png", "tiff", "tif", "bmp", "jpg", "jpeg")
