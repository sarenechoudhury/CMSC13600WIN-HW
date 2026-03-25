from collections import Counter, defaultdict

PUZZLE_FILE = "PUZZLE"   # rename if your file is named differently

with open(PUZZLE_FILE) as f:
    hashes = [line.strip() for line in f if line.strip()]

print("word count:", len(hashes))
print("distinct hashes:", len(set(hashes)))
print()

counts = Counter(hashes)
print("repeated hashes:")
for h, c in counts.most_common():
    if c > 1:
        print(c, h)

print()
print("positions of repeated words:")
pos = defaultdict(list)
for i, h in enumerate(hashes, start=1):
    pos[h].append(i)

for h, positions in sorted(pos.items(), key=lambda kv: (-len(kv[1]), kv[1])):
    if len(positions) > 1:
        print(len(positions), positions)

print()
print("pattern ids:")
idmap = {}
next_id = 1
pattern = []
for h in hashes:
    if h not in idmap:
        idmap[h] = next_id
        next_id += 1
    pattern.append(idmap[h])

print(pattern)