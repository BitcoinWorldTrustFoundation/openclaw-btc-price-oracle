# OpenClaw Skill: PRECOP BTC Price Oracle

The first 100% Native Bitcoin Price Oracle. No APIs. No OP_RETURN. Just Pure Code.

## 1. Overview
The PRECOP Native Oracle is a high-performance OpenClaw Skill delivering trustless Bitcoin pricing directly from the L1 blockchain. Unlike traditional oracles that relay external data, this engine derives the USD exchange rate on-chain by analyzing the thermodynamic frequency of Bitcoin transfers (UTXOracle v9.1 algorithm).

## 2. Key Technical Features
- **Sovereignty**: Operates exclusively via Bitcoin Core RPC. Zero dependency on external price APIs.
- **Binohash Integrity Guard**: Every price export is secured by a Proof-of-Work (PoW) grinding process. The resulting Binohash contains a `nonce` that proves the computational work performed to secure the truth.
- **Fail-Safe Mechanism**: Includes an automated "Catch-up" logic. If the oracle goes offline, it will batch-process all missing blocks upon restart to ensure a continuous price history for your records.
- **Covenant Integration**: Engineered specifically to provide the necessary "Witness State" for BTCDAI Simplicity Covenants.

## 3. Getting Started

### Installation
Clone the repository and run the automated installation script:
```bash
git clone https://github.com/BitcoinWorldTrustFoundation/precop-openclaw-btc-price-oracle.git
cd precop-openclaw-btc-price-oracle
./install.sh
```

### Configuration
Configure your credentials in the `.env` file (generated automatically from `.env.example`). You can specify the Proof-of-Work difficulty (W) here:

```env
# Multi-RPC Public Endpoints
BITCOIN_RPC_URLS=https://bitcoin-rpc.publicnode.com

# Binohash Difficulty (Hex Zeros)
BINOHASH_DIFFICULTY=2 
```

### Launch
Start the announcer and monitor the thermodynamic extraction:
```bash
./go-announcer.sh
```

## 4. Output Specification
The exported `btc_price_state.json` provides the following schema:

```json
{
  "height": 941195,
  "price_cents_uint64": 7136298,
  "delta_pct": -0.024,
  "data_age_blocks": 36,
  "timestamp": 1773910022,
  "source": "UTXOracle_v9.1_Native",
  "nonce": 699,
  "binohash": "00ea6ab3fb12b8bfa1f58211cabbdf467e48eee58bb8af77548198eed6e8b7e0"
}
```

- **nonce**: The Proof-of-Work value used to satisfy the Binohash difficulty.
- **binohash**: The resulting cryptographically secure integrity string.
- **price_cents_uint64**: The USD price in cents (no floats, cross-multiplication ready).

## 5. Technical Cheat Sheet
| Feature | Value |
| :--- | :--- |
| **Extraction Engine** | UTXOracle v9.1 (Native RPC) |
| **Integrity Guard** | Binohash Proof (PoW-based SHA256) |
| **Consensus Guard** | 10,000 TX Threshold |
| **Safety Expansion** | Up to 144 Blocks |
| **State Tracking** | Automated Batch Catch-up |

Produced by **BitcoinWorldTrustfoundation**.
