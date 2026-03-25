# hash_utils.py
import hashlib

def load_hashes(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def hashes_to_set(hex_list):
    return {bytes.fromhex(h) for h in hex_list}

def sha256_bytes(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()

def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()
