#!/usr/bin/env bash
# PRECOP BTC Price Oracle - Mainnet Launcher

ENV_FILE=".env"

if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  Configuration file not found: $ENV_FILE"
    echo "Please run ./install.sh first."
    exit 1
fi

source venv/bin/activate
export PYTHONPATH="$(dirname "$0")"

echo "🚀 Starting PRECOP BTC Price Oracle (Native UTXOracle)..."
python3 -m src.announcer_wrapper
