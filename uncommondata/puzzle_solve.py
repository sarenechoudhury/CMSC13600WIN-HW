# puzzle_solve.py
from typing import Iterable, List, Tuple
from hash_utils import load_hashes, hashes_to_set, sha256_bytes

# ---------- load PUZZLE hashes ----------
PUZZLE_HEX = load_hashes("PUZZLE")
PUZZLE_SET = hashes_to_set(PUZZLE_HEX)


def quick_check_line(line: str, key_range: Iterable[int]) -> int | None:
    for key in key_range:
        key_str = f"{key:09d}"
        h = sha256_bytes((key_str + line).encode())
        if h in PUZZLE_SET:
            print("  MATCH in small range:", "key=", key, "hash=", h.hex())
            return key
    return None


def try_key_for_candidate_lines(key: int, lines: List[str]) -> bool:
    key_str = f"{key:09d}"
    for line in lines:
        h = sha256_bytes((key_str + line).encode())
        if h not in PUZZLE_SET:
            return False
    return True


def brute_keys_for_known_quote(lines: List[str], start: int, end: int) -> int | None:
    for key in range(start, end):
        if try_key_for_candidate_lines(key, lines):
            print("FOUND KEY:", key)
            return key
    print("No key found in range", start, "to", end)
    return None


def load_candidates_from_file(path: str) -> List[Tuple[int, str]]:
    """
    Parse candidates.txt blocks and return list of (index, text).
    Expects lines like:
      #1
      ...
      text    : some text here
    """
    candidates: List[Tuple[int, str]] = []
    current_idx = None
    current_text = None

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("#"):
                # start of new block
                if current_idx is not None and current_text is not None:
                    candidates.append((current_idx, current_text))
                try:
                    current_idx = int(line[1:].strip())
                except ValueError:
                    current_idx = None
                current_text = None
            elif line.startswith("text    :"):
                # extract text after colon
                parts = line.split("text    :", 1)
                if len(parts) == 2:
                    current_text = parts[1].strip()
    # add last block
    if current_idx is not None and current_text is not None:
        candidates.append((current_idx, current_text))

    return candidates


if __name__ == "__main__":
    # 1) Load candidates from candidates.txt
    candidates = load_candidates_from_file("candidates.txt")
    print(f"Loaded {len(candidates)} candidates from candidates.txt")

    # 2) Quick-check each candidate in a modest key range
    small_range = range(0, 500_000)
    promising: List[Tuple[int, str, int]] = []  # (idx, text, small_key)

    for idx, text in candidates:
        print(f"\n=== Quick-checking candidate #{idx} ===")
        small_key = quick_check_line(text, small_range)
        if small_key is not None:
            print(f"-> Candidate #{idx} produced a match in small range (key={small_key})")
            promising.append((idx, text, small_key))
        else:
            print(f"-> Candidate #{idx} found no key in small range")

    if not promising:
        print("\nNo candidates matched in the small key range.")
        exit(0)

    # 3) For the first promising candidate, run full key search (you can adjust this)
    idx, line, small_key = promising[0]
    print(f"\nRunning full key search for candidate #{idx}...")
    full_key = brute_keys_for_known_quote([line], start=0, end=1_000_000_000)
    print("Final key for candidate", idx, ":", full_key)

    # After this, you can reconstruct the message and run misspelling search




