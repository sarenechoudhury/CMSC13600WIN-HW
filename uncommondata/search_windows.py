import hashlib
import string
from pathlib import Path
from collections import defaultdict

PUZZLE_FILE = "PUZZLE"
CORPUS_FILE = "corpus.txt"

# ---------- load puzzle ----------
TARGETS = [line.strip() for line in Path(PUZZLE_FILE).read_text().splitlines() if line.strip()]
TARGET_LEN = len(TARGETS)

def h(key_num: int, word: str) -> str:
    key = f"{key_num:09d}"
    return hashlib.sha256(key.encode("utf-8") + word.encode("utf-8")).hexdigest()

def repetition_pattern(tokens):
    pos = defaultdict(list)
    for i, tok in enumerate(tokens, start=1):
        pos[tok].append(i)
    return sorted([v for v in pos.values() if len(v) > 1], key=lambda x: (len(x), x))

def hash_pattern(hashes):
    pos = defaultdict(list)
    for i, hh in enumerate(hashes, start=1):
        pos[hh].append(i)
    return sorted([v for v in pos.values() if len(v) > 1], key=lambda x: (len(x), x))

TARGET_PATTERN = hash_pattern(TARGETS)

def score_pattern(candidate, target):
    cand_set = {tuple(x) for x in candidate}
    targ_set = {tuple(x) for x in target}
    return len(cand_set & targ_set)

def edits1(word: str):
    alphabet = string.ascii_letters
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    deletes = [L + R[1:] for L, R in splits if R]
    transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
    replaces = [L + c + R[1:] for L, R in splits if R for c in alphabet]
    inserts = [L + c + R for L, R in splits for c in alphabet]
    return set(deletes + transposes + replaces + inserts)

def find_misspelling(key_num: int, correct_word: str, target_hash: str):
    for cand in edits1(correct_word):
        if h(key_num, cand) == target_hash:
            return cand
    return None

def check_quote(key_num: int, words, allow_one_mismatch=True):
    bad = []
    for i, (w, target) in enumerate(zip(words, TARGETS)):
        if h(key_num, w) != target:
            bad.append((i, w))
            if not allow_one_mismatch or len(bad) > 1:
                return None
    return bad

def best_windows(tokens, n=66, min_score=1, top_k=10):
    results = []
    for i in range(len(tokens) - n + 1):
        window = tokens[i:i+n]
        pat = repetition_pattern(window)
        score = score_pattern(pat, TARGET_PATTERN)
        if score >= min_score:
            results.append((score, i, window, pat))
    results.sort(reverse=True, key=lambda x: (x[0], -x[1]))
    return results[:top_k]

def main():
    print("Target word count:", TARGET_LEN)
    print("Target repetition pattern:", TARGET_PATTERN)
    print()

    if not Path(CORPUS_FILE).exists():
        print(f"Missing {CORPUS_FILE}")
        return

    tokens = Path(CORPUS_FILE).read_text(errors="ignore").split()
    candidates = best_windows(tokens, n=TARGET_LEN, min_score=1, top_k=10)

    if not candidates:
        print("No candidate windows found.")
        return

    print("Top candidate windows:\n")
    for rank, (score, start, window, pat) in enumerate(candidates, start=1):
        print(f"#{rank} score={score} start={start}")
        print("pattern:", pat)
        print(" ".join(window))
        print()

    print("Copy one of the windows above into CANDIDATE_TEXT below and rerun.\n")

# ---------- second phase: paste one candidate here ----------
CANDIDATE_TEXT = """
""".strip()

def test_candidate():
    if not CANDIDATE_TEXT:
        return

    words = CANDIDATE_TEXT.split()
    print("Candidate word count:", len(words))
    print("Candidate repetition pattern:", repetition_pattern(words))
    print()

    if len(words) != TARGET_LEN:
        print("Wrong candidate length.")
        return

    for key_num in range(1_000_000_000):
        bad = check_quote(key_num, words, allow_one_mismatch=True)
        if bad is not None:
            print("FOUND KEY")
            print("puzzle_key =", key_num)
            print("bad positions =", bad)
            if len(bad) == 1:
                idx = bad[0][0]
                typo = find_misspelling(key_num, words[idx], TARGETS[idx])
                print("correct word =", words[idx])
                print("puzzle_misspell =", typo)
            return

if __name__ == "__main__":
    if CANDIDATE_TEXT:
        test_candidate()
    else:
        main()