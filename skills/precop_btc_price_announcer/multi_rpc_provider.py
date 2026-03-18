import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import httpx

logger = logging.getLogger("precop.rpc")

@dataclass
class RPCNode:
    url: str
    weight: int = 1
    failures: int = 0
    last_success: float = 0.0


class MultiRPCProvider:
    """
    Professional Multi-RPC Provider — Blockstream-grade.
    Smart rotation, automatic retry, light health check, and circuit breaker.
    """

    def __init__(self, rpc_urls: List[str], max_failures: int = 3, cooldown_seconds: int = 30):
        self.nodes: List[RPCNode] = [RPCNode(url=url.strip()) for url in rpc_urls if url.strip()]
        self.max_failures = max_failures
        self.cooldown_seconds = cooldown_seconds
        self.current_index = 0
        self.clients: Dict[str, httpx.AsyncClient] = {
            node.url: httpx.AsyncClient(timeout=12.0) for node in self.nodes
        }

    async def call(self, method: str, params: Optional[List] = None) -> Any:
        """JSON-RPC call with smart rotation and retry."""
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []}

        for _ in range(len(self.nodes) * 2):  # Max 2 full loops
            node = self.nodes[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.nodes)

            # Simple circuit breaker
            if node.failures >= self.max_failures:
                if time.time() - node.last_success < self.cooldown_seconds:
                    continue  # Skip temporarily

            client = self.clients[node.url]

            try:
                r = await client.post(node.url, json=payload)
                r.raise_for_status()
                result = r.json()

                if "error" in result and result["error"]:
                    raise Exception(result["error"])

                # Reset failure counter
                node.failures = 0
                node.last_success = time.time()

                return result["result"]

            except Exception as e:
                node.failures += 1
                logger.warning(f"RPC failed ({node.url}): {e} — failures: {node.failures}/{self.max_failures}")
                continue

        raise Exception("All RPC providers failed after retries and rotation.")

    # Bitcoin-specific methods
    async def getblockcount(self) -> int:
        return await self.call("getblockcount")

    async def getblockhash(self, height: int) -> str:
        return await self.call("getblockhash", [height])

    async def getblock(self, block_hash: str, verbosity: int = 2) -> Any:
        return await self.call("getblock", [block_hash, verbosity])

    async def getblockheader(self, block_hash: str, verbose: bool = True) -> Any:
        return await self.call("getblockheader", [block_hash, verbose])

    async def getblock_raw(self, block_hash: str) -> bytes:
        import binascii
        hex_data = await self.call("getblock", [block_hash, 0])
        return binascii.unhexlify(hex_data)

    async def close(self):
        """Gracefully closes all clients."""
        for client in self.clients.values():
            await client.aclose()
        logger.info("All RPC clients closed.")
