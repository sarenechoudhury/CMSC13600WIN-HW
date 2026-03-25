# extract_candidates_lines.py

def extract_text_lines(src: str, dst: str):
    out_lines = []
    with open(src, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("text    :"):
                # keep everything after 'text    :'
                parts = line.split("text    :", 1)
                if len(parts) == 2:
                    text = parts[1].strip()
                    if text:
                        out_lines.append(text)

    with open(dst, "w", encoding="utf-8") as out:
        for t in out_lines:
            out.write(t + "\n")

    print(f"Wrote {len(out_lines)} lines to {dst}")

if __name__ == "__main__":
    extract_text_lines("candidates.txt", "candidates_lines.txt")
