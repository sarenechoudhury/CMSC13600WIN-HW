import hashlib

with open("PUZZLE") as f:
    puzzle = set(line.strip() for line in f if line.strip())

word = "degradation,"

for key in range(1_000_000_000):
    k = f"{key:09d}"

    s = word + k   # <-- KEY INSIGHT

    h = hashlib.sha256(s.encode()).hexdigest()

    if h in puzzle:
        print("\n🔥 FOUND KEY:", k)
        print("match string:", s)
        break

    if key % 1_000_000 == 0:
        print("checked", k)