# solve_puzzle_easy.py
from hash_utils import load_hashes, hashes_to_set, sha256_hex
import string

# Load PUZZLE_EASY
PUZZLE_EASY_HEX = load_hashes("PUZZLE_EASY")
PUZZLE_EASY_SET = hashes_to_set(PUZZLE_EASY_HEX)

def edits1(word: str):
    # Allow letters plus apostrophe; that makes it easier to hit "gardens" from "gadqens"
    alphabet = string.ascii_lowercase + string.ascii_uppercase + "'"
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    deletes = [L + R[1:] for L, R in splits if R]
    transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
    replaces = [L + c + (R[1:] if len(R) else "") for L, R in splits if R for c in alphabet]
    inserts = [L + c + R for L, R in splits for c in alphabet]
    return set(deletes + transposes + replaces + inserts)

def try_hash_patterns():
    key_str = "8983"
    misspell = "gadqens"
    candidates = []

    # Reasonable patterns to test
    patterns = [
        ("key+word",        key_str + misspell),
        ("word+key",        misspell + key_str),
        ("key+space+word",  key_str + " " + misspell),
        ("word+space+key",  misspell + " " + key_str),
        ("key+newline+word", key_str + "\n" + misspell),
        ("word+newline+key", misspell + "\n" + key_str),
        ("key+comma+word",  key_str + "," + misspell),
        ("word+comma+key",  misspell + "," + key_str),
    ]

    for name, s in patterns:
        h_hex = sha256_hex(s.encode("utf-8"))
        in_puzzle = bytes.fromhex(h_hex) in PUZZLE_EASY_SET
        print(f"{name:18} -> {h_hex}   in PUZZLE_EASY? {in_puzzle}")
        candidates.append((name, s, h_hex, in_puzzle))

    return candidates

def confirm_edits():
    misspell = "gadqens"
    cands = edits1(misspell)
    print("Total edits1(gadqens):", len(cands))
    print("gardens in edits1(gadqens)?", "gardens" in cands)

if __name__ == "__main__":
    print("=== Trying hash patterns around key=8983, word='gadqens' ===")
    try_hash_patterns()
    print("\n=== Checking edit-distance-1 candidates ===")
    confirm_edits()




