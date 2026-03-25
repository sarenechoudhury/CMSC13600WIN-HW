import hashlib
import string
from pathlib import Path
from collections import defaultdict

PUZZLE_FILE = "PUZZLE"
CORPUS_FILE = "corpus.txt"

# ---------- load puzzle ----------
TARGETS = [line.strip() for line in Path(PUZZLE_FILE).read_text().splitlines() if line.strip()]
TARGET_LEN = len(TARGETS)


def h_with_prefix(prefix: bytes, word: str) -> str:
    return hashlib.sha256(prefix + word.encode("utf-8")).hexdigest()


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


def find_misspelling(prefix: bytes, correct_word: str, target_hash: str):
    for cand in edits1(correct_word):
        if hashlib.sha256(prefix + cand.encode("utf-8")).hexdigest() == target_hash:
            return cand
    return None


def best_windows(tokens, n=66, min_score=1, top_k=10):
    results = []
    for i in range(len(tokens) - n + 1):
        window = tokens[i:i + n]
        pat = repetition_pattern(window)
        score = score_pattern(pat, TARGET_PATTERN)
        if score >= min_score:
            results.append((score, i, window, pat))
    results.sort(reverse=True, key=lambda x: (x[0], -x[1]))
    return results[:top_k]


def choose_anchor_indices(words):
    # Prefer words that are longer and unique within the candidate window.
    counts = defaultdict(int)
    for w in words:
        counts[w] += 1

    scored = []
    for i, w in enumerate(words):
        unique_bonus = 100 if counts[w] == 1 else 0
        punct_bonus = 10 if any(ch in w for ch in ".,;:!?()") else 0
        score = unique_bonus + punct_bonus + len(w)
        scored.append((score, i))

    scored.sort(reverse=True)

    anchors = []
    used_buckets = set()

    # Spread anchors out across the text so a near-miss candidate fails quickly.
    for _, i in scored:
        bucket = i * 8 // len(words)  # 8 rough regions
        if bucket not in used_buckets:
            anchors.append(i)
            used_buckets.add(bucket)
        if len(anchors) >= 8:
            break

    # Fallback if not enough spread
    if len(anchors) < 8:
        for _, i in scored:
            if i not in anchors:
                anchors.append(i)
            if len(anchors) >= 8:
                break

    return sorted(anchors)


def check_candidate_for_key(prefix: bytes, words, anchors):
    # Fast filter: all anchors must match exactly.
    for idx in anchors:
        if hashlib.sha256(prefix + words[idx].encode("utf-8")).hexdigest() != TARGETS[idx]:
            return None

    # Full check: allow at most one mismatch.
    bad = []
    for i, w in enumerate(words):
        if hashlib.sha256(prefix + w.encode("utf-8")).hexdigest() != TARGETS[i]:
            bad.append((i, w))
            if len(bad) > 1:
                return None
    return bad


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

    anchors = choose_anchor_indices(words)
    print("Using anchor indices:", anchors)
    print("Anchor words:", [words[i] for i in anchors])
    print()

    for key_num in range(1_000_000_000):
        if key_num % 1_000_000 == 0:
            print("checked", key_num, flush=True)

        prefix = f"{key_num:09d}".encode("utf-8")
        bad = check_candidate_for_key(prefix, words, anchors)

        if bad is not None:
            print("FOUND KEY")
            print("puzzle_key =", key_num)
            print("bad positions =", bad)

            if len(bad) == 1:
                idx = bad[0][0]
                typo = find_misspelling(prefix, words[idx], TARGETS[idx])
                print("correct word =", words[idx])
                print("puzzle_misspell =", typo)
            else:
                print("No mismatches found.")
            return

    print("No key found for this candidate.")


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


CANDIDATE_TEXT = """
that a good Christian can sometimes learn also from the infidels, and when I asked him to let me taste it, he replied that herbs that are good for an old Franciscan are not good for a young Benedictine. During our time together we did not have occasion to lead a very regular life: even at the abbey we remained up at night and collapsed wearily
""".strip()


if __name__ == "__main__":
    if CANDIDATE_TEXT:
        test_candidate()
    else:
        main()