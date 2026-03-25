import subprocess

BASE_TEXT = """
being a degradation, of the family obstacles which judgment had always opposed to inclination, were dwelt on with a warmth which seemed due to the consequence he was wounding, but was very unlikely to recommend his suit. In spite of her deeply-rooted dislike, she could not be insensible to the compliment of such a man’s affection, and though her intentions did not vary for an instant, she was at first sorry for the pain he was to receive; till roused to resentment by his subsequent language, she lost all compassion in anger. She tried, however, to compose herself to answer him with patience, when he should have done. He concluded with representing to her the strength of that attachment which
""".strip()

words = BASE_TEXT.split()
WINDOW = 116
TIME_LIMIT = 20  # seconds per window

print("Testing sliding windows...")

for i in range(0, len(words) - WINDOW + 1):
    candidate = " ".join(words[i:i + WINDOW])

    print(f"\n--- Testing window starting at offset {i} ---")

    with open("temp_candidate.txt", "w", encoding="utf-8") as f:
        f.write(candidate)

    try:
        result = subprocess.run(
            ["python3", "test_candidate_file.py"],
            capture_output=True,
            text=True,
            timeout=TIME_LIMIT,
        )

        if "FOUND" in result.stdout:
            print("SUCCESS at offset", i)
            print(result.stdout)
            break
        else:
            print("No match in time window.")

    except subprocess.TimeoutExpired:
        print(f"Timed out after {TIME_LIMIT}s, moving on.")