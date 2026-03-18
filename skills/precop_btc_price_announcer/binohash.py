import json
import hashlib
from typing import Any, Dict

def compute_binohash(data: Dict[str, Any]) -> str:
    """
    Computes a deterministic SHA256 hash (Binohash) for a dictionary.
    Ensures that keys are sorted for reproducibility across systems.
    
    This hash serves as an integrity proof for the PRECOP L1 truth.
    """
    # Deterministic serialization: sort_keys=True is critical
    canonical_json = json.dumps(data, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(canonical_json).hexdigest()

def verify_binohash(data: Dict[str, Any], expected_hash: str) -> bool:
    """Verifies that the data matches the provided Binohash."""
    # We remove the binohash key if it's already in the dict for verification
    clean_data = {k: v for k, v in data.items() if k != 'binohash'}
    return compute_binohash(clean_data) == expected_hash
