import re
import requests
from collections import Counter

# Your puzzle fingerprint
TARGET_LEN = 116
TARGET_DISTINCT = 85
TARGET_PROFILE = [9, 5, 4, 3, 3, 3, 3, 3, 3, 2, 2, 2, 2]

# A small starter set of public-domain plain-text sources.
# You can add more Gutenberg txt.utf-8 URLs later.
URLS = [
    # Jane Austen
    "https://www.gutenberg.org/files/1342/1342-0.txt",   # Pride and Prejudice
    "https://www.gutenberg.org/files/158/158-0.txt",     # Emma
    "https://www.gutenberg.org/files/161/161-0.txt",     # Sense and Sensibility
    "https://www.gutenberg.org/files/121/121-0.txt",     # Northanger Abbey
    "https://www.gutenberg.org/files/105/105-0.txt",     # Persuasion

    # Brontë / Gaskell
    "https://www.gutenberg.org/files/1260/1260-0.txt",   # Jane Eyre
    "https://www.gutenberg.org/files/768/768-0.txt",     # Wuthering Heights
    "https://www.gutenberg.org/files/1023/1023-0.txt",   # North and South

    # Dickens
    "https://www.gutenberg.org/files/98/98-0.txt",       # A Tale of Two Cities
    "https://www.gutenberg.org/files/1400/1400-0.txt",   # Great Expectations
    "https://www.gutenberg.org/files/730/730-0.txt",     # Oliver Twist
    "https://www.gutenberg.org/files/786/786-0.txt",     # David Copperfield

    # Other 19th‑century novels
    "https://www.gutenberg.org/files/174/174-0.txt",     # The Picture of Dorian Gray
    "https://www.gutenberg.org/files/145/145-0.txt",     # Middlemarch
    "https://www.gutenberg.org/files/43/43-0.txt",       # The Strange Case of Dr. Jekyll and Mr. Hyde
    "https://www.gutenberg.org/files/5230/5230-0.txt",   # The Jungle (Upton Sinclair, 1906)

    # Existing ones you already had / used
    "https://www.gutenberg.org/files/2701/2701-0.txt",   # Moby-Dick
    "https://www.gutenberg.org/files/11/11-0.txt",       # Alice in Wonderland
    "https://www.gutenberg.org/files/1661/1661-0.txt",   # Sherlock Holmes (Adventures)
    "https://www.gutenberg.org/files/84/84-0.txt",       # Frankenstein
    "https://www.gutenberg.org/files/74/74-0.txt",       # Tom Sawyer
]



WORD_RE = re.compile(r"\S+")

def tokenize(text: str):
    # Keep punctuation attached, like the assignment likely did with split()
    return WORD_RE.findall(text)

def repetition_profile(words):
    counts = Counter(words)
    profile = sorted([c for c in counts.values() if c > 1], reverse=True)
    return len(set(words)), profile

PUNCT_CHARS = ",;.!?-\"'"

def punctuation_features(text: str):
    commas = text.count(",")
    semis = text.count(";")
    periods = text.count(".")
    qmarks = text.count("?")
    emdashes = text.count("—") + text.count("--")
    # rough sentence boundaries
    sentences = periods + qmarks
    return commas, semis, periods, qmarks, emdashes, sentences

# Rough expected punctuation stats for your target passage (tune if needed)
TARGET_COMMAs = 10
TARGET_SEMIS = 2
TARGET_PERIODS = 3
TARGET_SENTENCES = 3

def score_window(words):
    distinct, profile = repetition_profile(words)
    text = " ".join(words)

    # Base score: length and repetition profile
    score = 0
    score += abs(len(words) - TARGET_LEN) * 100
    score += abs(distinct - TARGET_DISTINCT) * 3

    max_len = max(len(profile), len(TARGET_PROFILE))
    for i in range(max_len):
        a = profile[i] if i < len(profile) else 0
        b = TARGET_PROFILE[i] if i < len(TARGET_PROFILE) else 0
        score += abs(a - b) * 5

    if profile:
        score += abs(profile[0] - 9) * 8

    # Punctuation features
    commas, semis, periods, qmarks, emdashes, sentences = punctuation_features(text)
    score += abs(commas - TARGET_COMMAs) * 4
    score += abs(semis - TARGET_SEMIS) * 6
    score += abs(periods - TARGET_PERIODS) * 6
    score += abs(sentences - TARGET_SENTENCES) * 3

    # Simple capitalization signal: how many words start with uppercase
    upper_initial = sum(1 for w in words if w[:1].isupper())
    # Expect mostly narrative prose: not too many capitalized words in a 116-word window
    TARGET_UPPER = 5
    score += abs(upper_initial - TARGET_UPPER) * 2

    return score, distinct, profile

def strip_gutenberg_boilerplate(text: str):
    start_markers = [
        "*** START OF THE PROJECT GUTENBERG EBOOK",
        "*** START OF THIS PROJECT GUTENBERG EBOOK",
    ]
    end_markers = [
        "*** END OF THE PROJECT GUTENBERG EBOOK",
        "*** END OF THIS PROJECT GUTENBERG EBOOK",
    ]

    start = 0
    end = len(text)

    for marker in start_markers:
        idx = text.find(marker)
        if idx != -1:
            nl = text.find("\n", idx)
            if nl != -1:
                start = nl + 1
            break

    for marker in end_markers:
        idx = text.find(marker)
        if idx != -1:
            end = idx
            break

    return text[start:end]

def best_windows_from_text(text: str, source_name: str, top_n: int = 20):
    words = tokenize(strip_gutenberg_boilerplate(text))
    results = []

    for i in range(0, len(words) - TARGET_LEN + 1):
        window = words[i:i + TARGET_LEN]
        score, distinct, profile = score_window(window)

        # cheap filter: discard obviously bad windows
        if distinct < 70 or distinct > 95:
            continue
        if not profile:
            continue
        if profile[0] < 5 or profile[0] > 12:
            continue


        results.append({
            "score": score,
            "distinct": distinct,
            "profile": profile,
            "start": i,
            "text": " ".join(window),
            "source": source_name,
        })

    results.sort(key=lambda x: x["score"])
    return results[:top_n]

def fetch_text(url: str):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.text

def main():
    all_results = []

    for url in URLS:
        print(f"Fetching {url}")
        try:
            text = fetch_text(url)
            best = best_windows_from_text(text, url, top_n=15)
            all_results.extend(best)
            print(f"  kept {len(best)} candidates")
        except Exception as e:
            print(f"  failed: {e}")

    all_results.sort(key=lambda x: x["score"])

    print("\nTOP CANDIDATES\n")
    for i, item in enumerate(all_results[:30], start=1):
        print(f"#{i}")
        print("score   :", item["score"])
        print("distinct:", item["distinct"])
        print("profile :", item["profile"])
        print("source  :", item["source"])
        print("start   :", item["start"])
        print("text    :", item["text"])
        print("-" * 80)

        # Save top 100 candidates to a file for later use
    with open("candidates.txt", "w", encoding="utf-8") as out:
        for i, item in enumerate(all_results[:100], start=1):
            out.write(f"#{i}\n")
            out.write(f"score   : {item['score']}\n")
            out.write(f"distinct: {item['distinct']}\n")
            out.write(f"profile : {item['profile']}\n")
            out.write(f"source  : {item['source']}\n")
            out.write(f"start   : {item['start']}\n")
            out.write(f"text    : {item['text']}\n")
            out.write("-" * 80 + "\n")


if __name__ == "__main__":
    main()