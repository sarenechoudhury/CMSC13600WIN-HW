from collections import Counter

with open("PUZZLE", "r") as f:
    hashes = [line.strip() for line in f if line.strip()]

print("number of words:", len(hashes))

counts = Counter(hashes)

print("\nrepeated hashes:")
for h, c in counts.items():
    if c > 1:
        positions = [i + 1 for i, x in enumerate(hashes) if x == h]
        print(c, positions)