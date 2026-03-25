# pow_search.py
import hashlib
from random import randrange

cnet_id = "sareneac"
TARGET_HEX = "0000000fffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
TARGET_INT = int(TARGET_HEX, 16)

def sha256_int(s: str) -> int:
    return int(hashlib.sha256(s.encode()).hexdigest(), 16)

def search_nonce(start=0, step=1):
    best = None
    n = start
    while True:
        h_int = sha256_int(f"{cnet_id}{n}")
        if best is None or h_int < best[1]:
            best = (n, h_int)
            print("best so far:", best[0], hex(best[1]))
        if h_int < TARGET_INT:
            print("FOUND:", n, hex(h_int))
            return n
        n += step

if __name__ == "__main__":
    # Try different start/step in parallel shells for faster search
    # e.g., one terminal with start=0,step=4; next with start=1,step=4, etc.
    search_nonce(start=0, step=1)
