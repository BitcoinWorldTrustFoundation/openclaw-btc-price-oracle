#!/usr/bin/env bash
# PRECOP BTC Price Oracle - Mainnet Setup Wizard

echo "========================================================="
echo "   PRECOP BTC Price Oracle (Mainnet v5.3) Setup Wizard"
echo "========================================================="

ENV_FILE=".env"

echo "📦 Setting up virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

if [ -f "$ENV_FILE" ]; then
    echo "✅ Configuration file already exists."
else
    if [ -f ".env.example" ]; then
        cp .env.example "$ENV_FILE"
        echo "✅ Configuration file created."
    fi
fi

echo ""
echo "Next steps:"
echo "1. Edit $ENV_FILE with your Telegram Bot Token and Chat ID"
echo "2. Run: ./go-announcer.sh"
echo ""
echo "The skill is now ready to mine truth for sats."
echo "========================================================="
