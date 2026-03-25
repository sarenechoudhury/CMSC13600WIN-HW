import hashlib
from collections import defaultdict
import sys

with open("PUZZLE") as f:
    puzzle = [line.strip() for line in f if line.strip()]

with open("temp_candidate.txt") as f:
    words = f.read().split()

groups = defaultdict(list)
for i, h in enumerate(puzzle):
    groups[h].append(i)

# Only use repeated-hash groups
rep_pairs = []
for h, idxs in groups.items():
    if len(idxs) > 1:
        rep_pairs.append((words[idxs[0]], h, len(idxs), idxs))

word_to_counts = defaultdict(list)
for w, h, c, idxs in rep_pairs:
    word_to_counts[w].append(c)

bad = False
for w, counts in word_to_counts.items():
    if len(counts) > 1:
        print("BAD ALIGNMENT:", w, counts)
        bad = True

if bad:
    sys.exit("Stopping: candidate is misaligned.")

print("Using", len(rep_pairs), "repeated groups")
for w, h, c, idxs in sorted(rep_pairs, key=lambda x: -x[2]):
    print(c, w, idxs)

def matches_any_format(k: str, w: str, h: str) -> bool:
    return (
        hashlib.sha256((k + w).encode()).hexdigest() == h or
        hashlib.sha256((w + k).encode()).hexdigest() == h or
        hashlib.sha256((k + " " + w).encode()).hexdigest() == h or
        hashlib.sha256((w + " " + k).encode()).hexdigest() == h
    )

for key in range(1_000_000_000):
    k = f"{key:09d}"

    ok = True
    for w, h, _, _ in rep_pairs:
        if not matches_any_format(k, w, h):
            ok = False
            break

    if ok:
        print("\nFOUND KEY:", k)
        break

    if key % 1_000_000 == 0:
        print("checked", k)