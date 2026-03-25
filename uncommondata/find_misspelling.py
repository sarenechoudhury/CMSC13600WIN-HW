import string

def edit_distance_1(word):
    """Generate all possible English-like misspellings with edit distance exactly 1"""
    variants = set()
    letters = string.ascii_lowercase
    
    # 1. Deletion: remove one character
    for i in range(len(word)):
        variants.add(word[:i] + word[i+1:])
    
    # 2. Insertion: add one character
    for i in range(len(word) + 1):
        for c in letters:
            variants.add(word[:i] + c + word[i:])
    
    # 3. Substitution: replace one character
    for i in range(len(word)):
        for c in letters:
            if c != word[i]:
                variants.add(word[:i] + c + word[i+1:])
    
    # 4. Transposition: swap two adjacent characters
    for i in range(len(word) - 1):
        variants.add(word[:i] + word[i+1] + word[i] + word[i+2:])
    
    # Also include the original word itself (for reference)
    variants.add(word)
    return sorted(variants)

# ======================  USE IT LIKE THIS  ======================

# Paste your decoded message here (as a list of words)
message_words = [
    "your", "decoded", "words", "go", "here", "from", "the", "puzzle",
    # ... add all words from the output of solve_puzzle.py
]

print("Full message:")
print(" ".join(message_words))
print("\nChecking each word for likely misspellings...\n")

for idx, w in enumerate(message_words):
    if len(w) < 3:          # skip very short words like "a", "the", "to"
        continue
    candidates = edit_distance_1(w.lower())
    print(f"Word {idx}: '{w}'  →  {len(candidates)} variants")
    # You can manually look for real English words among candidates
    # Or add a dictionary check if you want (see below)