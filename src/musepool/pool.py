"""
Async process pool with mutative scheduling for VOLUME.
Uses nest_asyncio to handle nested event loops (Jupyter/agent runtimes).
"""
from __future__ import annotations

import asyncio
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, TypeVar

try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass  # Not in nested loop environment

T = TypeVar("T")


@dataclass
class TaskResult:
    task_id: str
    success: bool
    result: Any = None
    error: str | None = None
    latency_ms: float = 0.0


class MutativeScheduler:
    """Schedules tasks based on estimated cost and worker affinity.
    Mutative = adapts scheduling based on previous task performance."""

    def __init__(self, max_workers: int = mp.cpu_count()):
        self.max_workers = max_workers
        self.history: dict[str, list[float]] = {}

    def estimate_cost(self, task_name: str, payload_size: int) -> float:
        """Estimate task cost based on history and payload size."""
        if task_name not in self.history:
            return payload_size / (1024 * 1024)  # MB as baseline
        avg_latency = sum(self.history[task_name]) / len(self.history[task_name])
        return avg_latency * (payload_size / (1024 * 1024))

    def record(self, task_name: str, latency_ms: float):
        """Record task performance for future scheduling."""
        self.history.setdefault(task_name, []).append(latency_ms)
        # Keep last 20 samples
        self.history[task_name] = self.history[task_name][-20:]

    def schedule(self, tasks: list[tuple[str, Callable, tuple, dict]]) -> list[list]:
        """Group tasks into batches for optimal worker utilization."""
        scored = []
        for name, fn, args, kwargs in tasks:
            payload_size = len(str(args)) + len(str(kwargs))
            cost = self.estimate_cost(name, payload_size)
            scored.append((cost, name, fn, args, kwargs))

        scored.sort(reverse=True)

        bins: list[list] = [[] for _ in range(self.max_workers)]
        for i, (_, name, fn, args, kwargs) in enumerate(scored):
            bins[i % self.max_workers].append((name, fn, args, kwargs))

        return bins


class ProcessPool:
    """Async process pool with mutative scheduling.
    Safe for nested event loops (Jupyter, agent runtimes)."""

    def __init__(self, max_workers: int | None = None, scheduler: str = "mutative"):
        self.max_workers = max_workers or mp.cpu_count()
        self.scheduler = MutativeScheduler(self.max_workers) if scheduler == "mutative" else None
        self._executor: ProcessPoolExecutor | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    async def __aenter__(self):
        # Handle nested event loops
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

        self._executor = ProcessPoolExecutor(max_workers=self.max_workers)
        return self

    async def __aexit__(self, *args):
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None

    async def map(
        self,
        fn: Callable[..., T],
        items: list[Any],
        *args,
        **kwargs,
    ) -> list[TaskResult]:
        """Map function over items using process pool."""
        if self._executor is None:
            raise RuntimeError("Pool not entered. Use 'async with ProcessPool() as pool:'")

        loop = self._loop or asyncio.get_event_loop()
        tasks = [
            (f"{fn.__name__}_{i}", fn, (item, *args), kwargs)
            for i, item in enumerate(items)
        ]

        if self.scheduler:
            bins = self.scheduler.schedule(tasks)
        else:
            bins = [tasks[i::self.max_workers] for i in range(self.max_workers)]

        results: list[TaskResult] = []

        async def run_bin(bin_tasks: list):
            for task_id, fn, args, kwargs in bin_tasks:
                try:
                    start = loop.time()
                    if asyncio.iscoroutinefunction(fn):
                        result = await fn(*args, **kwargs)
                    else:
                        result = await loop.run_in_executor(
                            self._executor, lambda: fn(*args, **kwargs)
                        )
                    latency = (loop.time() - start) * 1000
                    if self.scheduler:
                        self.scheduler.record(fn.__name__, latency)
                    results.append(TaskResult(task_id, True, result, latency_ms=latency))
                except Exception as e:
                    results.append(TaskResult(task_id, False, error=str(e)))

        await asyncio.gather(*[run_bin(b) for b in bins])
        return results

    async def submit(self, fn: Callable[..., T], *args, **kwargs) -> TaskResult:
        """Submit single task."""
        results = await self.map(fn, [args[0]], *args[1:], **kwargs)
        return results[0]
