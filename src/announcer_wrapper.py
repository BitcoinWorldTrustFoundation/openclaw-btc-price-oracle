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
        """Run the oracle synchronously (blocking)."""
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        print("Starting PRECOP BTC Price Announcer (Mainnet)...")
        print(f"Polling Interval: {self.config.poll_interval_sec}s")
        print(f"Target Window: {self.config.price_window_blocks} blocks")
        
        try:
            asyncio.run(self._lifecycle())
        except KeyboardInterrupt:
            print("\nShutdown signal received.")

if __name__ == "__main__":
    wrapper = BtcPriceAnnouncerWrapper()
    wrapper.run_sync()
