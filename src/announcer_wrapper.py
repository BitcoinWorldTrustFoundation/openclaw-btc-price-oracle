import asyncio
import logging
from contextlib import asynccontextmanager
from skills.precop_btc_price_announcer.config import load_config
from skills.precop_btc_price_announcer.logic import PriceOracleLogic

logger = logging.getLogger("precop")

class BtcPriceAnnouncerWrapper:
    """Wrapper to run the Price Oracle gracefully."""
    def __init__(self):
        self.config = load_config()
        self.logic = PriceOracleLogic(self.config)

    async def _lifecycle(self):
        try:
            await self.logic.setup()
            await self.logic.run()
        except asyncio.CancelledError:
            pass
        finally:
            await self.logic.stop()
            logger.info("Oracle wrapper shutdown complete.")

    def run_sync(self):
        """Run the oracle synchronously with a professional console output."""
        # 🧪 Professional Logging Configuration
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)-7s | %(name)-15s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # 🛡️ Professional Banner
        print("\n" + "="*60)
        print("  🐾 OPENCLAW SKILL | PRECOP BTC PRICE ORACLE".center(60))
        print("  Thermodynamic L1 Truth Engine v9.1".center(60))
        print("="*60)
        print(f"  > Polling Every:     {self.config.poll_interval_sec}s")
        print(f"  > Binary Window:     {self.config.price_window_blocks} blocks")
        print(f"  > Binohash Guard:    W={self.config.binohash_difficulty} (Hex Zeros)")
        print(f"  > Target Network:    Bitcoin Mainnet (RPC)")
        print("="*60 + "\n")
        
        try:
            asyncio.run(self._lifecycle())
        except KeyboardInterrupt:
            print("\n" + "-"*60)
            print("  🛑 Oracle shutdown signal received. Graceful exit...".center(60))
            print("-"*60 + "\n")

if __name__ == "__main__":
    wrapper = BtcPriceAnnouncerWrapper()
    wrapper.run_sync()
