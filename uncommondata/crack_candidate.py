import hashlib
import multiprocessing as mp
import string
import sys

PUZZLE_FILE = "PUZZLE"

# Paste your quote candidate here exactly as normal English text.
CANDIDATE_TEXT = """
PASTE THE SUSPECTED QUOTE HERE
""".strip()

LETTERS = string.ascii_lowercase


def sha_hex(key: int, word: str) -> str:
    s = f"{key:09d}{word}"
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def load_hashes():
    with open(PUZZLE_FILE) as f:
        return [line.strip() for line in f if line.strip()]


def tokenize(text: str):
    return text.split()


def variants(word: str):
    out = {word}

    base_forms = {
        word,
        word.lower(),
        word.capitalize(),
    }

    suffixes = ["", ".", ",", ";", ":", "!", "?", "\"", "'"]
    prefixes = ["", "\"", "'"]

    for b in base_forms:
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


def choose_anchor_positions(words):
    # Prefer repeated/common-looking short words as anchors
    # Here: choose a few short tokens to test early.
    scored = []
    for i, w in enumerate(words):
        score = (len(w), i)
        scored.append((score, i))
    scored.sort()
    return [i for _, i in scored[:5]]


def check_key(key, words, hashes):
    mismatches = []

    for i, word in enumerate(words):
        if sha_hex(key, word) != hashes[i]:
            mismatches.append(i)
            if len(mismatches) > 1:
                return False, mismatches

    return True, mismatches


def recover_misspelling(key, original_word, target_hash):
    for miss in edits1(original_word):
        for v in variants(miss):
            if sha_hex(key, v) == target_hash:
                return v
    return None


def worker(start, step, words, hashes, stop, outq):
    anchor_positions = choose_anchor_positions(words)
    anchor_variants = [variants(words[i]) for i in anchor_positions]

    key = start
    while not stop.is_set():
        # Early filter: candidate key must satisfy several anchor positions
        ok = True
        chosen_words = []

        for pos, vars_for_pos in zip(anchor_positions, anchor_variants):
            matched = None
            for v in vars_for_pos:
                if sha_hex(key, v) == hashes[pos]:
                    matched = v
                    break
            if matched is None:
                ok = False
                break
            chosen_words.append((pos, matched))

        if ok:
            # Reconstruct best candidate token list from anchors + defaults
            trial_words = words[:]
            for pos, matched in chosen_words:
                trial_words[pos] = matched

            # Allow variants for non-anchor words greedily
            mismatches = []
            for i in range(len(trial_words)):
                if sha_hex(key, trial_words[i]) != hashes[i]:
                    found_variant = None
                    for v in variants(words[i]):
                        if sha_hex(key, v) == hashes[i]:
                            found_variant = v
                            break
                    if found_variant is not None:
                        trial_words[i] = found_variant
                    else:
                        mismatches.append(i)
                        if len(mismatches) > 1:
                            break

            if len(mismatches) == 0:
                outq.put(("found_exact", key, trial_words, None))
                stop.set()
                return

            if len(mismatches) == 1:
                bad_i = mismatches[0]
                miss = recover_misspelling(key, words[bad_i].strip(string.punctuation).lower(), hashes[bad_i])
                if miss is not None:
                    outq.put(("found_misspell", key, trial_words, bad_i, miss))
                    stop.set()
                    return

        key += step


def main():
    hashes = load_hashes()
    words = tokenize(CANDIDATE_TEXT)

    if len(words) != len(hashes):
        print(f"Length mismatch: candidate has {len(words)} words, puzzle has {len(hashes)}")
        sys.exit(1)

    nproc = mp.cpu_count() or 4
    stop = mp.Event()
    outq = mp.Queue()
    procs = []

    print(f"Searching with {nproc} workers...")

    for start in range(nproc):
        p = mp.Process(target=worker, args=(start, nproc, words, hashes, stop, outq))
        p.start()
        procs.append(p)

    result = outq.get()

    stop.set()
    for p in procs:
        p.terminate()
        p.join()

    print()
    if result[0] == "found_exact":
        _, key, final_words, _ = result
        print("FOUND KEY:", key)
        print("No misspelling needed.")
        print("Recovered text:")
        print(" ".join(final_words))
    else:
        _, key, final_words, bad_i, miss = result
        print("FOUND KEY:", key)
        print("Misspelled word position:", bad_i + 1)
        print("Misspelled token:", miss)
        print("Recovered text:")
        final_words[bad_i] = miss
        print(" ".join(final_words))


if __name__ == "__main__":
    main()