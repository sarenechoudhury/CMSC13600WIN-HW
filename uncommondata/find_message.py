from pathlib import Path
from collections import defaultdict
import string

PUZZLE_FILE = "PUZZLE"
CORPUS_FILE = "corpus.txt"

# repeated-hash groups from PUZZLE, 1-based positions
TARGET_GROUPS = [
    [10, 57],
    [17, 38],
    [25, 49],
    [24, 45, 60],
    [36, 43, 51],
]

TARGET_LEN = 66
STRIP_CHARS = string.punctuation + "—“”‘’"

def norm(tok: str) -> str:
    return tok.strip(STRIP_CHARS).lower()

def group_match_score(window_tokens):
    """
    Score how well this 66-word window matches the repeated-word structure.
    Because one word in the true puzzle is misspelled, allow one group to fail.
    """
    nw = [norm(t) for t in window_tokens]
    matches = []
    for group in TARGET_GROUPS:
        vals = [nw[i - 1] for i in group]   # groups are 1-based
        ok = len(set(vals)) == 1
        matches.append((group, vals, ok))
    score = sum(ok for _, _, ok in matches)
    return score, matches

def main():
    text = Path(CORPUS_FILE).read_text(errors="ignore")
    tokens = text.split()

    # anchor on the phrase you already know is in the right neighborhood
    anchor = ["that", "a", "good", "Christian", "can", "sometimes", "learn"]
    anchor_norm = [norm(x) for x in anchor]
    tokens_norm = [norm(t) for t in tokens]

    hits = []
    for i in range(len(tokens_norm) - len(anchor_norm) + 1):
        if tokens_norm[i:i + len(anchor_norm)] == anchor_norm:
            hits.append(i)

    if not hits:
        print("Could not find anchor phrase in corpus.")
        return

    print("Anchor hits:", hits)
    print()

    candidates = []
    for hit in hits:
        # search nearby window starts around the known quote
        start_min = max(0, hit - 80)
        start_max = min(len(tokens) - TARGET_LEN, hit + 80)

        for start in range(start_min, start_max + 1):
            window = tokens[start:start + TARGET_LEN]
            score, matches = group_match_score(window)
            # keep everything with at least 2 satisfied repeated groups
            if score >= 2:
                candidates.append((score, start, window, matches))

    candidates.sort(key=lambda x: (-x[0], x[1]))

    print("Top nearby windows by repeated-group score:")
    print()

    for score, start, window, matches in candidates[:20]:
        print(f"Score: {score}  Start token: {start}")
        for group, vals, ok in matches:
            print(f"  {group}: {vals}  -> {'OK' if ok else 'NO'}")
        print("  Passage:")
        print(" ", " ".join(window))
        print()

if __name__ == "__main__":
    main()