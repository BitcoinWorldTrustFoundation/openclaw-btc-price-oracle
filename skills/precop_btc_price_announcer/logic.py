import json
import logging
import time
import asyncio
from pathlib import Path
from .utxoracle_engine import UTXOracleEngine, InsufficientEntropyError
from .utxoracle import UTXOracleError
from .telegram import TelegramAnnouncer
from .binohash import compute_binohash

logger = logging.getLogger("precop.logic")
STATE_FILE = Path("btc_price_state.json")

class PriceOracleLogic:
    def __init__(self, config):
        self.config = config
        self.engine = UTXOracleEngine(
            rpc_urls=config.bitcoin_rpc_urls,
            window_size=config.price_window_blocks,
            min_entropy=config.min_sample_entropy,
            max_expansion=config.max_expansion_blocks
        )
        self.telegram = TelegramAnnouncer(config)
        self.last_known_height = 0
        self.last_price_cents = 0
        self.running = False
        self._load_state()

    def _load_state(self):
        if STATE_FILE.is_file():
            try:
                with STATE_FILE.open() as f:
                    data = json.load(f)
                self.last_known_height = data.get("height", 0)
                self.last_price_cents = data.get("price_cents_uint64", 0)
                logger.info(f"État restauré : Bloc {self.last_known_height}")
            except Exception as e:
                logger.warning(f"Fichier d'état corrompu : {e}. Démarrage à zéro.")

    def _save_l1_state(self, price_cents: int, current_height: int, window: int):
        """Sauvegarde l'état au format strict et signé par un Binohash."""
        delta_pct = 0.0
        if self.last_price_cents > 0:
            delta_pct = round(((price_cents - self.last_price_cents) / self.last_price_cents) * 100, 3)

        # 🏗️ State Construction
        state = {
            "height": current_height,
            "price_cents_uint64": price_cents, 
            "delta_pct": delta_pct,
            "data_age_blocks": window,
            "timestamp": int(time.time()),
            "source": "UTXOracle_v9.1_Native"
        }
        
        # 🛡️ Binohash Proof (Truth Integrity Guard)
        state["binohash"] = compute_binohash(state)
        
        tmp_state = STATE_FILE.with_suffix(".tmp")
        with open(tmp_state, "w") as f:
            json.dump(state, f, indent=2)
        tmp_state.replace(STATE_FILE)
        
        self.last_price_cents = price_cents
        return state

    async def setup(self):
        logger.info("PRECOP BTC Price Oracle initialisé (Mode Thermodynamique L1)")
        self.running = True

    async def run(self):
        logger.info("Démarrage de la boucle RPC...")
        while self.running:
            try:
                await self._poll_and_process()
            except Exception as e:
                logger.error(f"Erreur critique dans la boucle : {e}", exc_info=True)
            await asyncio.sleep(self.config.poll_interval_sec)

    async def stop(self):
        self.running = False
        await self.engine.close()

    async def _poll_and_process(self):
        # 1. STRICTEMENT RPC (Zéro dépendance Web2)
        try:
            current_height = await self.engine.provider.getblockcount()
        except Exception as e:
            logger.error(f"Nœuds RPC injoignables : {e}")
            return

        if current_height <= self.last_known_height:
            return

        logger.info(f"Nouveau bloc Bitcoin L1 : {current_height}")

        try:
            # 2. EXTRACTION DU PRIX (12-step UTXOracle algo)
            price_cents, actual_window = await self.engine.get_price_for_consensus(current_height)
            
            # 3. EXPORT DU WITNESS STATE (Now with Binohash)
            state = self._save_l1_state(price_cents, current_height, actual_window)
            
            # 4. DIFFUSION SOCIALE
            await self.telegram.send_announcement_json(state)
            
            self.last_known_height = current_height

        except (UTXOracleError, InsufficientEntropyError) as e:
            logger.critical(f"ABORT CONSENSUS : {e}")
            self.last_known_height = current_height 
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction : {e}", exc_info=True)
            self.last_known_height = current_height 
