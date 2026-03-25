from collections import Counter, defaultdict

TEXT = """
You don't like them. You don't really know why you don't like them. All you know is you find them repulsive.

Consequently, a German soldier conducts a search of a house suspected of hiding Jews. Where does the hawk look? He looks in the barn, he looks in the attic, he looks in the cellar
, he looks everywhere he would hide, but there's so many places it would never occur to a hawk to hide. However, the reason the Führer's brought me off my Alps in Austria
 and placed me in French cow country today because it does occur to me. Because I'm aware what tremendous feats human beings are capable of once they abandon
""".strip()

def analyze_words(words):
    counts = Counter(words)

    print("word count:", len(words))
    print("distinct words:", len(set(words)))
    print()

    print("repeated words:")
    for w, c in counts.most_common():
        if c > 1:
            print(c, repr(w))

    print()
    print("positions of repeated words:")
    pos = defaultdict(list)
    for i, w in enumerate(words, start=1):
        pos[w].append(i)

    for w, positions in sorted(pos.items(), key=lambda kv: (-len(kv[1]), kv[1])):
        if len(positions) > 1:
            print(len(positions), positions, repr(w))

    print()
    print("pattern ids:")
    idmap = {}
    next_id = 1
    pattern = []
    for w in words:
        if w not in idmap:
            idmap[w] = next_id
            next_id += 1
        pattern.append(idmap[w])
    print(pattern)

words = TEXT.split()
analyze_words(words)