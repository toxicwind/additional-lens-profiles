"""Test musepool async pool."""
import pytest
import asyncio
from musepool.pool import ProcessPool, MutativeScheduler


@pytest.mark.asyncio
async def test_scheduler_estimate():
    sched = MutativeScheduler(max_workers=2)
    cost = sched.estimate_cost("test", 1024 * 1024)
    assert cost > 0


@pytest.mark.asyncio
async def test_pool_map():
    def double(x):
        return x * 2

    async with ProcessPool(max_workers=2) as pool:
        results = await pool.map(double, [1, 2, 3, 4])
        assert len(results) == 4
        assert all(r.success for r in results)
        assert [r.result for r in results] == [2, 4, 6, 8]
