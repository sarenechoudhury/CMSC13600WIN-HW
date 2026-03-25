# quick_check.py
import hashlib
from typing import Iterable

with open("PUZZLE") as f:
    PUZZLE_HASHES_HEX = [line.strip() for line in f if line.strip()]
PUZZLE_HASHES = {bytes.fromhex(h) for h in PUZZLE_HASHES_HEX}

def sha256_bytes(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()

def quick_check_line(line: str, key_range: Iterable[int]) -> bool:
    for key in key_range:
        key_str = f"{key:09d}"
        h = sha256_bytes((key_str + line).encode())
        if h in PUZZLE_HASHES:
            print("MATCH in small range:", "key=", key, "hash=", h.hex())
            return True
    print("No match for this line in tested key range")
    return False

if __name__ == "__main__":
    candidate_line = (
        "its being a degradation, of the family obstacles which judgment had always "
        "opposed to inclination, were dwelt on with a warmth which seemed due to the "
        "consequence he was wounding, but was very unlikely to recommend his suit. "
        "In spite of her deeply-rooted dislike, she could not be insensible to the "
        "compliment of such a man’s affection, and though her intentions did not "
        "vary for an instant, she was at first sorry for the pain he was to receive; "
        "till roused to resentment by his subsequent language, she lost all "
        "compassion in anger. She tried, however, to compose herself to answer him "
        "with patience, when he should have done. He concluded with representing to "
        "her the strength of that attachment which"
    )

    # Try a small range first, e.g. keys 0..100000
    quick_check_line(candidate_line, range(0, 100000))
