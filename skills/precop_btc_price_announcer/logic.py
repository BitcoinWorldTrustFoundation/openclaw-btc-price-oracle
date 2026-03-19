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
        
        # 🛡️ Binohash Proof (Truth Integrity Guard with Custom Difficulty)
        state["binohash"] = compute_binohash(state, difficulty=self.config.binohash_difficulty)
        
        tmp_state = STATE_FILE.with_suffix(".tmp")
        with open(tmp_state, "w") as f:
            json.dump(state, f, indent=2)
        tmp_state.replace(STATE_FILE)
        
        self.last_price_cents = price_cents
        return state

    async def setup(self):
        logger.info("🛡️ PRECOP BTC Price Oracle initialisé (Mode Thermodynamique L1)")
        if not self.config.telegram_enabled:
            logger.warning("📢 Telegram est DÉSACTIVÉ. Vérifiez votre config.")
        self.running = True

    async def run(self):
        logger.info("🚀 Démarrage de la boucle RPC...")
        while self.running:
            try:
                await self._poll_and_process()
            except Exception as e:
                logger.error(f"❌ Erreur critique dans la boucle : {e}", exc_info=True)
            await asyncio.sleep(self.config.poll_interval_sec)

    async def stop(self):
        self.running = False
        await self.engine.close()

    async def _poll_and_process(self):
        # 1. STRICTEMENT RPC (Zéro dépendance Web2)
        try:
            current_height = await self.engine.provider.getblockcount()
        except Exception as e:
            logger.error(f"📡 Noeuds RPC injoignables : {e}")
            return

        if current_height <= self.last_known_height:
            return

        # CATCH-UP LOGIC: On traite tous les blocs manquants (limité pour éviter le spam)
        missing_blocks = current_height - self.last_known_height
        catch_up_limit = 20
        
        target_heights = list(range(self.last_known_height + 1, current_height + 1))
        if len(target_heights) > catch_up_limit:
            logger.warning(f"⚠️ Retard de {missing_blocks} blocs. Récupération par lot de {catch_up_limit}...")
            target_heights = target_heights[:catch_up_limit] 

        for target_height in target_heights:
            logger.info(f"⛏️ Traitement du bloc Bitcoin L1 : {target_height}")

            try:
                # 2. EXTRACTION DU PRIX (12-step UTXOracle algo)
                price_cents, actual_window = await self.engine.get_price_for_consensus(target_height)
                
                # 3. EXPORT DU WITNESS STATE (Now with Binohash Proof)
                state = self._save_l1_state(price_cents, target_height, actual_window)
                
                # 4. DIFFUSION SOCIALE
                if len(target_heights) > 1:
                    await asyncio.sleep(1)

                await self.telegram.send_announcement_json(state)
                
                self.last_known_height = target_height

            except (UTXOracleError, InsufficientEntropyError) as e:
                logger.critical(f"🛑 ABORT CONSENSUS pour le bloc {target_height} : {e}")
                self.last_known_height = target_height 
            except Exception as e:
                logger.error(f"❌ Erreur lors de l'extraction (bloc {target_height}) : {e}", exc_info=True)
                break
