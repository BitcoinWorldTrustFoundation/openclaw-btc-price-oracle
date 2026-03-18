import logging
from typing import Tuple
from .utxoracle import UTXOracleClient, UTXOracleError
from .multi_rpc_provider import MultiRPCProvider

logger = logging.getLogger("precop.price_oracle")

class InsufficientEntropyError(Exception):
    pass

class UTXOracleEngine:
    """
    VRAI Moteur UTXOracle v9.1.
    Ne lit AUCUN OP_RETURN. Analyse la distribution des montants des UTXOs réels
    pour trouver le centre de masse des paiements en fiat.
    """
    def __init__(
        self,
        rpc_urls: list[str],
        window_size: int = 36,
        min_entropy: int = 10000,
        max_expansion: int = 144
    ):
        self.provider = MultiRPCProvider(rpc_urls)
        self.base_window = window_size
        self.min_entropy = min_entropy
        self.max_expansion = max_expansion
        
        # On instancie le client core (vos 606 lignes de mathématiques pures)
        # Note: Le MultiRPCProvider expose une interface compatible avec le client core
        self.core_utxo_client = UTXOracleClient(rpc_client=self.provider)

    async def get_price_for_consensus(self, current_height: int) -> Tuple[int, int]:
        """
        Extrait le prix thermodynamique sur une fenêtre glissante.
        Étend la fenêtre vers le passé si l'entropie (nombre de TX L1) est trop faible.
        Retourne : (price_cents_uint64, blocks_scanned)
        """
        logger.info(f"Début extraction thermodynamique (Cible: {self.base_window} blocs depuis {current_height})...")
        
        blocks_scanned = self.base_window
        
        while blocks_scanned <= self.max_expansion:
            start_height = current_height - blocks_scanned + 1
            
            try:
                # 1. Vérification de l'entropie (le nombre de tx éligibles dans les blocs)
                entropy = await self.core_utxo_client.count_eligible_transactions(start_height, current_height)
                
                if entropy >= self.min_entropy:
                    logger.info(f"Entropie atteinte : {entropy} TXs éligibles sur {blocks_scanned} blocs.")
                    
                    # 2. Exécution de l'algorithme en 12 étapes de precop_core
                    # Retourne un float en USD (ex: 85412.50)
                    price_usd = await self.core_utxo_client.compute_price(start_height, current_height)
                    
                    # 3. Conversion stricte L1 (uint64 en centimes, aucun flottant)
                    price_cents_uint64 = int(price_usd * 100)
                    
                    logger.info(f"Prix validé par UTXOracle : {price_cents_uint64} cents.")
                    return price_cents_uint64, blocks_scanned
                
                else:
                    logger.warning(f"Entropie faible ({entropy}/{self.min_entropy}). Extension de la fenêtre (+6 blocs)...")
                    blocks_scanned += 6
                    
            except (UTXOracleError, Exception) as e:
                logger.error(f"Erreur d'extraction UTXOracle : {e}")
                raise

        raise InsufficientEntropyError(
            f"Impossible d'atteindre l'entropie requise ({self.min_entropy}) "
            f"même après {self.max_expansion} blocs. Marché illiquide ou attaqué."
        )

    async def close(self):
        await self.provider.close()
