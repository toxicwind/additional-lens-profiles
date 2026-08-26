"""
musepool — Async-aware process pool with mutative scheduling.
Integrated into VOLUME Master for parallel EPUB chapter processing.
"""
from .pool import ProcessPool, MutativeScheduler
from .cdn import CDNResolver

__all__ = ["ProcessPool", "MutativeScheduler", "CDNResolver"]
