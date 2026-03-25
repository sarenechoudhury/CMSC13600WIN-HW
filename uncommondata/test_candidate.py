import hashlib
import multiprocessing as mp
import string
import time

PUZZLE_FILE = "PUZZLE"

with open("temp_candidate.txt", "r", encoding="utf-8") as f:
    CANDIDATE_TEXT = f.read().strip()
LETTERS = string.ascii_lowercase


def load_hashes():
    with open(PUZZLE_FILE, "r") as f:
        return [line.strip() for line in f if line.strip()]


def sha_hex(key: int, word: str) -> str:
    s = f"{key:09d}{word}"
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def variants(word: str):
    out = set()

    bases = {word, word.lower(), word.capitalize()}
    prefixes = ["", "'", '"']
    suffixes = ["", ".", ",", ";", ":", "!", "?", "'", '"']

    for b in bases:
        for pre in prefixes:
            for suf in suffixes:
                out.add(pre + b + suf)

    return sorted(out)


def edits1(word: str):
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    deletes = [L + R[1:] for L, R in splits if R]
    transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
    replaces = [L + c + R[1:] for L, R in splits if R for c in LETTERS]
    inserts = [L + c + R for L, R in splits for c in LETTERS]
    return sorted(set(deletes + transposes + replaces + inserts))


def normalize_for_misspell_search(word: str):
    return word.strip(string.punctuation).lower()


def best_variant_for_position(key: int, raw_word: str, target_hash: str):
    for v in variants(raw_word):
        if sha_hex(key, v) == target_hash:
            return v
    return None


def recover_misspelling(key: int, intended_word: str, target_hash: str):
    for miss in edits1(intended_word):
        for v in variants(miss):
            if sha_hex(key, v) == target_hash:
                return v
    return None


def choose_anchor_positions(words):
    # Use a handful of short/common-looking positions first
    # to reject bad keys quickly.
    candidate_positions = []
    for i, w in enumerate(words):
        stripped = w.strip(string.punctuation)
        if 2 <= len(stripped) <= 5:
            candidate_positions.append(i)

    # fallback
    if len(candidate_positions) < 6:
        candidate_positions = list(range(min(6, len(words))))

    return candidate_positions[:6]


def worker(start, step, words, hashes, stop, outq):
    anchor_positions = choose_anchor_positions(words)
    anchor_variants = [variants(words[i]) for i in anchor_positions]

    key = start
    checked = 0

    while not stop.is_set():
        ok = True

        for pos, vv in zip(anchor_positions, anchor_variants):
            matched = False
            for v in vv:
                if sha_hex(key, v) == hashes[pos]:
                    matched = True
                    break
            if not matched:
                ok = False
                break

        if ok:
            resolved = list(words)
            mismatches = []

            for i, w in enumerate(words):
                found = best_variant_for_position(key, w, hashes[i])
                if found is not None:
                    resolved[i] = found
                else:
                    mismatches.append(i)
                    if len(mismatches) > 1:
                        break

            if len(mismatches) == 0:
                outq.put(("exact", key, resolved))
                stop.set()
                return

            if len(mismatches) == 1:
                bad_i = mismatches[0]
                intended = normalize_for_misspell_search(words[bad_i])
                miss = recover_misspelling(key, intended, hashes[bad_i])
                if miss is not None:
                    resolved[bad_i] = miss
                    outq.put(("misspell", key, bad_i, miss, resolved))
                    stop.set()
                    return

        key += step
        checked += 1

        if checked % 200000 == 0:
            outq.put(("progress", start, key))


def main():
    hashes = load_hashes()
    words = CANDIDATE_TEXT.split()

    if len(words) != len(hashes):
        print(f"Length mismatch: candidate has {len(words)} words, puzzle has {len(hashes)}")
        return

    nproc = mp.cpu_count() or 4
    stop = mp.Event()
    outq = mp.Queue()
    procs = []

    print(f"Testing candidate with {nproc} workers...")
    t0 = time.time()

    for start in range(nproc):
        p = mp.Process(target=worker, args=(start, nproc, words, hashes, stop, outq))
        p.start()
        procs.append(p)

    try:
        while True:
            msg = outq.get()

            if msg[0] == "progress":
                _, wid, key = msg
                elapsed = time.time() - t0
                print(f"worker {wid}: reached key {key:09d} after {elapsed:.1f}s")
                continue

            if msg[0] == "exact":
                _, key, resolved = msg
                print("\nFOUND EXACT MATCH")
                print("puzzle_key =", key)
                print("Recovered text:")
                print(" ".join(resolved))
                break

            if msg[0] == "misspell":
                _, key, bad_i, miss, resolved = msg
                print("\nFOUND MATCH WITH ONE MISSPELLING")
                print("puzzle_key =", key)
                print("misspelled position =", bad_i + 1)
                print("puzzle_misspell =", repr(miss))
                print("Recovered text:")
                print(" ".join(resolved))
                break

    finally:
        stop.set()
        for p in procs:
            p.terminate()
            p.join()


if __name__ == "__main__":
    main()