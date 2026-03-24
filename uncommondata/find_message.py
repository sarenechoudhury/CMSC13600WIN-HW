from collections import defaultdict
from pathlib import Path

PUZZLE_FILE = "PUZZLE"
CORPUS_FILE = "corpus.txt"

def repetition_pattern(tokens):
    pos = defaultdict(list)
    for i, tok in enumerate(tokens, start=1):
        pos[tok].append(i)
    return sorted([v for v in pos.values() if len(v) > 1], key=lambda x: (len(x), x))

def hash_pattern(hashes):
    pos = defaultdict(list)
    for i, h in enumerate(hashes, start=1):
        pos[h].append(i)
    return sorted([v for v in pos.values() if len(v) > 1], key=lambda x: (len(x), x))

def score_pattern(candidate, target):
    cand_set = {tuple(x) for x in candidate}
    targ_set = {tuple(x) for x in target}
    return len(cand_set & targ_set)

hashes = [line.strip() for line in Path(PUZZLE_FILE).read_text().splitlines() if line.strip()]
target_len = len(hashes)
target_pattern = hash_pattern(hashes)

print("Target word count:", target_len)
print("Target repetition pattern:", target_pattern)

text = Path(CORPUS_FILE).read_text(errors="ignore")
tokens = text.split()

best = []

for i in range(len(tokens) - target_len + 1):
    window = tokens[i:i + target_len]
    pat = repetition_pattern(window)
    score = score_pattern(pat, target_pattern)

    if score > 0:
        best.append((score, i, " ".join(window), pat))

best.sort(reverse=True)

print("Windows with any overlap:", len(best))
print()

for score, i, passage, pat in best[:20]:
    print("Score:", score, "Start token:", i)
    print("Pattern:", pat)
    print(passage[:500])
    print()