# 🐾 OpenClaw Skill: PRECOP BTC Price Oracle

> **The first 100% Native Bitcoin Price Oracle. No APIs. No OP_RETURN. Just Pure Code.**

Welcome to the **PRECOP Native Oracle**, a high-performance **OpenClaw Skill** designed to deliver trustless BTC pricing directly from the Bitcoin L1 blockchain. This isn't your average price feed—it's a thermodynamic engine that listens to the heartbeat of the network.

---

## 🧐 What is this?
Most oracles rely on "trusted" sources or simple relays. This skill implements the **UTXOracle v9.1** algorithm—a 12-step signal-processing engine that analyzes the frequency and value of Bitcoin transfers to derive the USD exchange rate **on-chain**. 

**Why it's better for the OpenClaw community:**
- **Sovereign**: Runs entirely on your own Bitcoin Node (RPC).
- **Anti-Fragile**: No dependency on Gecko, CoinMarketCap, or even Mempool APIs.
- **Truth Integrity**: Every state export is secured by a **Binohash** (deterministic SHA256) to prevent tampering.
- **Covenant-Ready**: Specifically built to power **BTCDAI Simplicity Covenants** via the IndexerClaw.

---

## 🛠️ Getting Started (The 30-Second Setup)

### 1. Simple Install
Run our setup wizard to handle the heavy lifting (virtual environment, dependencies, and settings):
```bash
git clone https://github.com/BitcoinWorldTrustfoundation/precop-openclaw-btc-price-oracle.git
cd precop-openclaw-btc-price-oracle
./install.sh
```

### 2. Configure your "Truth"
Open the `.env` file (created automatically from `.env.example`) and add your RPC credentials and Telegram details:
```bash
nano .env
```

### 3. Let it Claw! 🐾
Start the announcer and watch the thermodynamic extraction in real-time:
```bash
./go-announcer.sh
```

---

## 🛡️ Trust & Audits
We take security seriously because we are building the future of DeFi on Bitcoin.
- **Binohash Logic**: We use canonical JSON serialization to ensure that the "truth" exported by this oracle is verifiable by any third party.

---

## 📊 Technical "Cheat Sheet"
| Feature | Value |
| :--- | :--- |
| **Extraction Engine** | UTXOracle v9.1 (Native RPC) |
| **Integrity Guard** | Binohash (Deterministic SHA256) |
| **Consensus Guard** | 10,000 TX Threshold |
| **Safety Expansion** | Up to 144 Blocks |
| **Output Format** | Strict Cents (`uint64`) |

---

## 🤝 Contributing
Join the OpenClaw revolution! Check out [CONTRIBUTING.md](CONTRIBUTING.md) to see how you can help harden the oracle even further.

**Produced with ❤️ for the BitcoinWorldTrustfoundation.** 🛡️🌍
