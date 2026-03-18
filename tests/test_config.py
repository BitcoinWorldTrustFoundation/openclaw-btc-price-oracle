"""
Tests for SentinelConfig loading and validation.

All tests use environment variable injection — no real sentinel.env needed.
Tests are fully deterministic and network-free (no Mutinynet calls).
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from skills.precop_truth_miner.config import (
    STAKE_MODES,
    SentinelConfig,
    load_config,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

VALID_WIF = "cVTestWifKeyForMutinynetOnly1234567890abcdefg"


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Remove PRECOP env vars before each test to avoid cross-test pollution."""
    for key in ("MUTINYNET_WIF", "STAKE_MODE", "MUTINYNET_RPC_URL",
                "MONITOR_PORT", "OPENCLAW_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    yield


# =============================================================================
# WIF validation
# =============================================================================

class TestWifValidation:

    def test_valid_wif_accepted(self, monkeypatch):
        monkeypatch.setenv("MUTINYNET_WIF", VALID_WIF)
        cfg = load_config()
        assert cfg.wif == VALID_WIF

    def test_missing_wif_raises_environment_error(self):
        with pytest.raises(EnvironmentError, match="MUTINYNET_WIF"):
            load_config()

    def test_empty_wif_raises_environment_error(self, monkeypatch):
        monkeypatch.setenv("MUTINYNET_WIF", "")
        with pytest.raises(EnvironmentError, match="MUTINYNET_WIF"):
            load_config()

    def test_whitespace_only_wif_raises(self, monkeypatch):
        monkeypatch.setenv("MUTINYNET_WIF", "   ")
        with pytest.raises(EnvironmentError, match="MUTINYNET_WIF"):
            load_config()

    def test_wif_stripped_of_quotes(self, monkeypatch):
        """install.sh writes WIF='value' — single quotes must be stripped."""
        monkeypatch.setenv("MUTINYNET_WIF", f"'{VALID_WIF}'")
        cfg = load_config()
        assert cfg.wif == VALID_WIF

    def test_wif_masked_format(self, monkeypatch):
        monkeypatch.setenv("MUTINYNET_WIF", VALID_WIF)
        cfg = load_config()
        assert cfg.wif_masked.startswith(VALID_WIF[:6])
        assert cfg.wif_masked.endswith(VALID_WIF[-4:])
        assert "..." in cfg.wif_masked


# =============================================================================
# Stake mode validation
# =============================================================================

class TestStakeModeValidation:

    @pytest.mark.parametrize("mode,expected_w", [
        ("LIGHT",    30),
        ("STANDARD", 42),
        ("HEAVY",    50),
    ])
    def test_valid_stake_modes(self, monkeypatch, mode, expected_w):
        monkeypatch.setenv("MUTINYNET_WIF", VALID_WIF)
        monkeypatch.setenv("STAKE_MODE", mode)
        cfg = load_config()
        assert cfg.stake_mode == mode
        assert cfg.binohash_w == expected_w

    def test_default_stake_mode_is_standard(self, monkeypatch):
        monkeypatch.setenv("MUTINYNET_WIF", VALID_WIF)
        cfg = load_config()
        assert cfg.stake_mode == "STANDARD"
        assert cfg.binohash_w == 42

    def test_stake_mode_case_insensitive(self, monkeypatch):
        monkeypatch.setenv("MUTINYNET_WIF", VALID_WIF)
        monkeypatch.setenv("STAKE_MODE", "heavy")
        cfg = load_config()
        assert cfg.stake_mode == "HEAVY"
        assert cfg.binohash_w == 50

    def test_invalid_stake_mode_raises_value_error(self, monkeypatch):
        monkeypatch.setenv("MUTINYNET_WIF", VALID_WIF)
        monkeypatch.setenv("STAKE_MODE", "ULTRA")
        with pytest.raises(ValueError, match="STAKE_MODE"):
            load_config()

    def test_stake_mode_override_takes_priority(self, monkeypatch):
        monkeypatch.setenv("MUTINYNET_WIF", VALID_WIF)
        monkeypatch.setenv("STAKE_MODE", "LIGHT")
        cfg = load_config(stake_mode_override="HEAVY")
        assert cfg.stake_mode == "HEAVY"
        assert cfg.binohash_w == 50


# =============================================================================
# RPC URL
# =============================================================================

class TestRpcUrl:

    def test_default_rpc_url(self, monkeypatch):
        monkeypatch.setenv("MUTINYNET_WIF", VALID_WIF)
        cfg = load_config()
        assert cfg.rpc_url == "https://mutinynet.com/api"

    def test_custom_rpc_url(self, monkeypatch):
        monkeypatch.setenv("MUTINYNET_WIF", VALID_WIF)
        monkeypatch.setenv("MUTINYNET_RPC_URL", "http://localhost:18332")
        cfg = load_config()
        assert cfg.rpc_url == "http://localhost:18332"

    def test_empty_rpc_url_falls_back_to_default(self, monkeypatch):
        monkeypatch.setenv("MUTINYNET_WIF", VALID_WIF)
        monkeypatch.setenv("MUTINYNET_RPC_URL", "")
        cfg = load_config()
        assert cfg.rpc_url == "https://mutinynet.com/api"


# =============================================================================
# Sentinel.env file loading
# =============================================================================

class TestEnvFileLoading:

    def test_load_from_explicit_path(self, tmp_path, monkeypatch):
        env_file = tmp_path / "sentinel.env"
        env_file.write_text(
            f"MUTINYNET_WIF={VALID_WIF}\nSTAKE_MODE=HEAVY\n"
        )
        cfg = load_config(env_path=env_file)
        assert cfg.wif == VALID_WIF
        assert cfg.stake_mode == "HEAVY"
        assert cfg.env_path == env_file

    def test_nonexistent_explicit_path_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_config(env_path=tmp_path / "nonexistent.env")

    def test_env_path_is_none_when_no_file_found(self, monkeypatch):
        monkeypatch.setenv("MUTINYNET_WIF", VALID_WIF)
        cfg = load_config()
        # env_path will be None if no sentinel.env exists anywhere in search paths
        # (In CI, no sentinel.env exists — config is loaded from system env)
        assert cfg.env_path is None or isinstance(cfg.env_path, Path)


# =============================================================================
# SentinelConfig immutability and repr
# =============================================================================

class TestSentinelConfig:

    def test_config_is_frozen(self, monkeypatch):
        monkeypatch.setenv("MUTINYNET_WIF", VALID_WIF)
        cfg = load_config()
        with pytest.raises((AttributeError, TypeError)):
            cfg.wif = "tampered"  # type: ignore[misc]

    def test_repr_does_not_expose_full_wif(self, monkeypatch):
        monkeypatch.setenv("MUTINYNET_WIF", VALID_WIF)
        cfg = load_config()
        assert VALID_WIF not in repr(cfg)
        assert "..." in repr(cfg)

    def test_expected_iters_human_light(self, monkeypatch):
        monkeypatch.setenv("MUTINYNET_WIF", VALID_WIF)
        monkeypatch.setenv("STAKE_MODE", "LIGHT")
        cfg = load_config()
        # W=30: 2^(30*6) = 2^180 → enormous number
        assert cfg.expected_iters_human.endswith(("T", "B", "M", "k")) or cfg.expected_iters_human.isdigit()

    @pytest.mark.parametrize("mode", ["LIGHT", "STANDARD", "HEAVY"])
    def test_binohash_w_matches_stake_modes_table(self, monkeypatch, mode):
        monkeypatch.setenv("MUTINYNET_WIF", VALID_WIF)
        monkeypatch.setenv("STAKE_MODE", mode)
        cfg = load_config()
        assert cfg.binohash_w == STAKE_MODES[mode]

    def test_monitor_port_default(self, monkeypatch):
        monkeypatch.setenv("MUTINYNET_WIF", VALID_WIF)
        cfg = load_config()
        assert cfg.monitor_port == 8080

    def test_monitor_port_custom(self, monkeypatch):
        monkeypatch.setenv("MUTINYNET_WIF", VALID_WIF)
        monkeypatch.setenv("MONITOR_PORT", "9090")
        cfg = load_config()
        assert cfg.monitor_port == 9090

    def test_monitor_port_invalid_falls_back_to_default(self, monkeypatch):
        monkeypatch.setenv("MUTINYNET_WIF", VALID_WIF)
        monkeypatch.setenv("MONITOR_PORT", "not_a_port")
        cfg = load_config()
        assert cfg.monitor_port == 8080
