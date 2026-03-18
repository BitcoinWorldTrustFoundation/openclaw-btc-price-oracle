"""
Tests for PRECOPTruthMiner async lifecycle (setup / run / stop).

SentinelNode is mocked — no Mutinynet connection required.
Tests verify the skill's state machine and error handling paths.
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
    """Inject a valid WIF and clean env before each test."""
    monkeypatch.setenv("MUTINYNET_WIF", VALID_WIF)
    monkeypatch.setenv("STAKE_MODE", "STANDARD")
    for key in ("MUTINYNET_RPC_URL", "MONITOR_PORT", "OPENCLAW_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    yield


@pytest.fixture()
def mock_sentinel_node():
    """Return a mock SentinelNode with async start() and stop()."""
    node = MagicMock()
    node.start = AsyncMock()
    node.stop  = AsyncMock()
    return node


@pytest.fixture()
def miner(mock_sentinel_node):
    """
    PRECOPTruthMiner with SentinelNode patched out.
    precop_oracleclaw.engine is mocked so no import is needed.
    """
    with patch.dict("sys.modules", {
        "precop_oracleclaw":        MagicMock(),
        "precop_oracleclaw.engine": MagicMock(SentinelNode=MagicMock(return_value=mock_sentinel_node)),
    }):
        # Re-import after patching
        from skills.precop_truth_miner.logic import PRECOPTruthMiner
        m = PRECOPTruthMiner()
        yield m, mock_sentinel_node


# =============================================================================
# setup()
# =============================================================================

class TestSetup:

    @pytest.mark.asyncio
    async def test_setup_sets_config(self, miner):
        m, _ = miner
        await m.setup()
        assert m._config is not None
        assert m._config.wif == VALID_WIF

    @pytest.mark.asyncio
    async def test_setup_instantiates_node(self, miner):
        m, node = miner
        await m.setup()
        assert m._node is node

    @pytest.mark.asyncio
    async def test_setup_raises_on_missing_wif(self, monkeypatch):
        monkeypatch.delenv("MUTINYNET_WIF", raising=False)
        with patch.dict("sys.modules", {
            "precop_oracleclaw":        MagicMock(),
            "precop_oracleclaw.engine": MagicMock(),
        }):
            from skills.precop_truth_miner.logic import PRECOPTruthMiner
            m = PRECOPTruthMiner()
            with pytest.raises(EnvironmentError, match="MUTINYNET_WIF"):
                await m.setup()

    @pytest.mark.asyncio
    async def test_setup_raises_on_invalid_stake_mode(self, monkeypatch):
        monkeypatch.setenv("STAKE_MODE", "TURBO")
        with patch.dict("sys.modules", {
            "precop_oracleclaw":        MagicMock(),
            "precop_oracleclaw.engine": MagicMock(),
        }):
            from skills.precop_truth_miner.logic import PRECOPTruthMiner
            m = PRECOPTruthMiner()
            with pytest.raises(ValueError, match="STAKE_MODE"):
                await m.setup()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("mode,expected_w", [
        ("LIGHT",    30),
        ("STANDARD", 42),
        ("HEAVY",    50),
    ])
    async def test_setup_binohash_w_per_mode(self, monkeypatch, miner, mode, expected_w):
        monkeypatch.setenv("STAKE_MODE", mode)
        m, _ = miner
        await m.setup()
        assert m._config.binohash_w == expected_w


# =============================================================================
# run()
# =============================================================================

class TestRun:

    @pytest.mark.asyncio
    async def test_run_calls_node_start(self, miner):
        m, node = miner
        await m.setup()
        await m.run()
        node.start.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_run_without_setup_raises_runtime_error(self, miner):
        m, _ = miner
        with pytest.raises(RuntimeError, match="setup\\(\\)"):
            await m.run()

    @pytest.mark.asyncio
    async def test_run_sets_running_flag(self, miner):
        m, node = miner
        await m.setup()
        await m.run()
        # After normal completion, _running was set True during run
        assert m._running is True

    @pytest.mark.asyncio
    async def test_run_handles_cancelled_error_gracefully(self, miner):
        m, node = miner
        node.start.side_effect = asyncio.CancelledError()
        await m.setup()
        # Should NOT raise — CancelledError is caught internally
        await m.run()

    @pytest.mark.asyncio
    async def test_run_propagates_unexpected_exceptions(self, miner):
        m, node = miner
        node.start.side_effect = RuntimeError("Mutinynet RPC unreachable")
        await m.setup()
        with pytest.raises(RuntimeError, match="Mutinynet RPC unreachable"):
            await m.run()


# =============================================================================
# stop()
# =============================================================================

class TestStop:

    @pytest.mark.asyncio
    async def test_stop_calls_node_stop(self, miner):
        m, node = miner
        await m.setup()
        await m.stop()
        node.stop.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_stop_sets_running_false(self, miner):
        m, node = miner
        await m.setup()
        m._running = True
        await m.stop()
        assert m._running is False

    @pytest.mark.asyncio
    async def test_stop_without_setup_does_not_raise(self, miner):
        m, _ = miner
        # stop() before setup() should be safe (no node to stop)
        await m.stop()

    @pytest.mark.asyncio
    async def test_stop_tolerates_node_exception(self, miner):
        m, node = miner
        node.stop.side_effect = Exception("Node already dead")
        await m.setup()
        # Warning should be logged but no exception propagated
        await m.stop()


# =============================================================================
# Full lifecycle
# =============================================================================

class TestFullLifecycle:

    @pytest.mark.asyncio
    async def test_setup_run_stop_completes_cleanly(self, miner):
        m, node = miner
        await m.setup()
        await m.run()
        await m.stop()
        node.start.assert_awaited_once()
        node.stop.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_config_is_immutable_after_setup(self, miner):
        m, _ = miner
        await m.setup()
        cfg = m._config
        with pytest.raises((AttributeError, TypeError)):
            cfg.wif = "hacked"  # type: ignore[misc]
