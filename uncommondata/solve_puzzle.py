import hashlib
import string

with open("PUZZLE", "r") as f:
    TARGETS = [line.strip() for line in f if line.strip()]

def h(key_num: int, word: str) -> str:
    key = f"{key_num:09d}"
    return hashlib.sha256(key.encode("utf-8") + word.encode("utf-8")).hexdigest()

def check_quote(key_num: int, words: list[str], allow_one_mismatch: bool = True):
    if len(words) != len(TARGETS):
        return None

    bad = []
    for i, (w, target) in enumerate(zip(words, TARGETS)):
        if h(key_num, w) != target:
            bad.append((i, w))
            if not allow_one_mismatch or len(bad) > 1:
                return None
    return bad

alphabet = string.ascii_letters

def edits1(word: str):
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

candidate_text = """
that a good Christian can sometimes learn also from the infidels, and when I asked him to let me taste it, he replied that herbs that are good for an old Franciscan are not good for a young Benedictine. During our time together we did not have occasion to lead a very regular life: even at the abbey we remained up at night and collapsed wearily
""".strip()

candidate_words = candidate_text.split()
print("candidate word count:", len(candidate_words))

for key_num in range(0, 1_000_000_000):
    bad = check_quote(key_num, candidate_words, allow_one_mismatch=True)
    if bad is not None:
        print("candidate key:", key_num)
        print("bad positions:", bad)
        if len(bad) == 1:
            idx = bad[0][0]
            correct_word = candidate_words[idx]
            typo = find_misspelling(key_num, correct_word, TARGETS[idx])
            print("correct word:", correct_word)
            print("misspelled word:", typo)
        break