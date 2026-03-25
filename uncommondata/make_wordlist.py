# make_wordlist.py
import re
import requests

URLS = [
    "https://www.gutenberg.org/files/1342/1342-0.txt",  # Pride and Prejudice
    "https://www.gutenberg.org/files/2701/2701-0.txt",  # Moby-Dick
    "https://www.gutenberg.org/files/11/11-0.txt",      # Alice in Wonderland
    "https://www.gutenberg.org/files/1661/1661-0.txt",  # Sherlock Holmes
    "https://www.gutenberg.org/files/84/84-0.txt",      # Frankenstein
    "https://www.gutenberg.org/files/98/98-0.txt",      # Tale of Two Cities
    "https://www.gutenberg.org/files/74/74-0.txt",      # Tom Sawyer
]

WORD_RE = re.compile(r"[A-Za-z']+")

def fetch_text(url: str) -> str:
    print("Fetching", url)
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.text

def build_wordlist():
    vocab = set()
    for url in URLS:
        txt = fetch_text(url)
        for w in WORD_RE.findall(txt):
            vocab.add(w.lower())
    print("Total distinct words:", len(vocab))
    with open("wordlist.txt", "w", encoding="utf-8") as f:
        for w in sorted(vocab):
            f.write(w + "\n")

if __name__ == "__main__":
    build_wordlist()
