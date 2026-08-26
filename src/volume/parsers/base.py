"""Base parser interface."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ParsedBook:
    title: str = ""
    language: str = "en"
    authors: list[str] = field(default_factory=list)
    chapters: list[dict] = field(default_factory=list)
    images: dict[str, bytes] = field(default_factory=dict)
    styles: list[bytes] = field(default_factory=list)
    fonts: list[bytes] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    has_mathml: bool = False
    total_bytes: int = 0


class BaseParser(ABC):
    @abstractmethod
    def parse(self, path: str) -> ParsedBook:
        ...
