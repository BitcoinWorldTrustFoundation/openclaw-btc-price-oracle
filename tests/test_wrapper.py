"""
Tests for SentinelWrapper — high-level programmatic API.

SentinelNode is mocked — no Mutinynet connection required.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

VALID_WIF = "cVTestWifKeyForMutinynetOnly1234567890abcdefg"


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.setenv("MUTINYNET_WIF", VALID_WIF)
    monkeypatch.setenv("STAKE_MODE", "STANDARD")
    for key in ("MUTINYNET_RPC_URL", "MONITOR_PORT", "OPENCLAW_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    yield


@pytest.fixture()
def mock_node():
    node = MagicMock()
    node.start = AsyncMock()
    node.stop  = AsyncMock()
    node.tick  = AsyncMock(return_value={"markets_scanned": 5, "votes_cast": 2})
    return node


@pytest.fixture()
def wrapper(mock_node):
    """SentinelWrapper with SentinelNode patched out."""
    with patch.dict("sys.modules", {
        "precop_oracleclaw":        MagicMock(),
        "precop_oracleclaw.engine": MagicMock(SentinelNode=MagicMock(return_value=mock_node)),
    }):
        from src.sentinel_wrapper import SentinelWrapper
        w = SentinelWrapper()
        yield w, mock_node


# =============================================================================
# Status
# =============================================================================

class TestStatus:

    def test_initial_state_is_idle(self, wrapper):
        w, _ = wrapper
        assert w.status()["state"] == "IDLE"

    def test_status_contains_expected_keys(self, wrapper):
        w, _ = wrapper
        s = w.status()
        assert set(s.keys()) == {
            "state", "wif_masked", "stake_mode",
            "binohash_w", "expected_iters_human", "rpc_url"
        }

    def test_status_wif_is_masked(self, wrapper):
        w, _ = wrapper
        assert VALID_WIF not in w.status()["wif_masked"]

    def test_status_stake_mode_standard(self, wrapper):
        w, _ = wrapper
        assert w.status()["stake_mode"] == "STANDARD"
        assert w.status()["binohash_w"] == 42


# =============================================================================
# Async lifecycle
# =============================================================================

class TestAsyncLifecycle:

    @pytest.mark.asyncio
    async def test_start_sets_running_state(self, wrapper):
        w, _ = wrapper
        await w.start()
        assert w.status()["state"] == "RUNNING"

    @pytest.mark.asyncio
    async def test_start_twice_raises_runtime_error(self, wrapper):
        w, _ = wrapper
        await w.start()
        with pytest.raises(RuntimeError, match="Cannot start"):
            await w.start()

    @pytest.mark.asyncio
    async def test_stop_sets_stopped_state(self, wrapper):
        w, node = wrapper
        await w.start()
        await w.stop()
        assert w.status()["state"] == "STOPPED"
        node.stop.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_stop_before_start_is_safe(self, wrapper):
        w, _ = wrapper
        await w.stop()   # no node yet — should not raise

    @pytest.mark.asyncio
    async def test_run_once_calls_tick(self, wrapper):
        w, node = wrapper
        result = await w.run_once()
        node.tick.assert_awaited_once()
        assert result["votes_cast"] == 2

    @pytest.mark.asyncio
    async def test_run_once_auto_starts(self, wrapper):
        w, node = wrapper
        await w.run_once()
        assert w.status()["state"] == "RUNNING"

    @pytest.mark.asyncio
    async def test_run_forever_calls_node_start(self, wrapper):
        w, node = wrapper
        await w.start()
        await w.run_forever()
        node.start.assert_awaited_once()
        assert w.status()["state"] == "STOPPED"

    @pytest.mark.asyncio
    async def test_run_forever_handles_cancelled_error(self, wrapper):
        w, node = wrapper
        node.start.side_effect = asyncio.CancelledError()
        await w.run_forever()   # should not raise


# =============================================================================
# Reset
# =============================================================================

class TestReset:

    @pytest.mark.asyncio
    async def test_reset_after_stop_returns_to_idle(self, wrapper):
        w, _ = wrapper
        await w.start()
        await w.stop()
        w.reset()
        assert w.status()["state"] == "IDLE"

    @pytest.mark.asyncio
    async def test_reset_while_running_raises(self, wrapper):
        w, _ = wrapper
        await w.start()
        with pytest.raises(RuntimeError, match="stop\\(\\)"):
            w.reset()


# =============================================================================
# Context manager
# =============================================================================

class TestContextManager:

    @pytest.mark.asyncio
    async def test_async_context_manager_start_stop(self, wrapper):
        w, node = wrapper
        async with w:
            assert w.status()["state"] == "RUNNING"
        assert w.status()["state"] == "STOPPED"
        node.stop.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_async_context_manager_stop_on_exception(self, wrapper):
        w, node = wrapper
        with pytest.raises(ValueError):
            async with w:
                raise ValueError("test error")
        node.stop.assert_awaited_once()


# =============================================================================
# Repr
# =============================================================================

class TestRepr:

    def test_repr_contains_state_and_mode(self, wrapper):
        w, _ = wrapper
        r = repr(w)
        assert "IDLE" in r
        assert "STANDARD" in r
        assert "42" in r
