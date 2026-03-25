import hashlib
import time

start_time = time.time()

# Load puzzle hashes
puzzle_hashes = {line.strip() for line in open("PUZZLE") if line.strip()}
print(f"Loaded {len(puzzle_hashes)} unique hashes.")

# Use the fast common wordlist first (highly recommended)
with open("google-10000-english.txt", encoding="utf-8", errors="ignore") as f:
    wordlist = [w.strip() for w in f if 2 <= len(w.strip()) <= 20]

print(f"Loaded {len(wordlist):,} common words. Starting brute-force search...\n")

found_key = None
decoded_message = []
keys_tested = 0

for n in range(1_000_000_000):
    key = f"{n:09d}"
    keys_tested += 1

    # Progress update every 5000 keys (easy to read)
    if n % 5000 == 0 and n > 0:
        elapsed = time.time() - start_time
        speed = keys_tested / elapsed if elapsed > 0 else 0
        print(f"Tested {n:,} keys | Speed: {speed:,.0f} keys/sec | "
              f"Elapsed: {elapsed:.1f}s | Found words: {len(decoded_message)}")

    for word in wordlist:
        candidate = key + word                    # NO space between key and word
        h = hashlib.sha256(candidate.encode("utf-8")).hexdigest()

        if h in puzzle_hashes:
            if found_key is None:
                found_key = key
                print("\n" + "="*60)
                print(f"*** KEY FOUND: {key} ***")
                print(f"Example word : {word}")
                print(f"Time so far  : {time.time() - start_time:.1f} seconds")
                print("="*60 + "\n")

            decoded_message.append(word)
            puzzle_hashes.discard(h)

            # Stop once we have almost the full message
            if len(decoded_message) >= 45:
                print("\n" + "★" * 20)
                print("FULL MESSAGE DECODED SUCCESSFULLY!")
                print(" ".join(decoded_message))
                print("\n" + "★" * 20)
                print(f"\nTotal time     : {time.time() - start_time:.1f} seconds")
                print(f"Your puzzle_key = {found_key}")
                print(f"Number of words decoded: {len(decoded_message)}")
                exit(0)   # cleanly stop the program

print("Search completed without finding the key.")