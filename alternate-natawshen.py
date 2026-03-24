import sys

args = sys.argv[1:]

n = 2

if len(args) >= 2 and args[0] == "-n":
    n = int(args[1])
    filename = args[2]
else:
    filename = args[0]
    if len(args) >= 2:
        n = int(args[1])

with open(filename) as f:
    for line_num, text in enumerate(f, start=1):
        if line_num >= 2 and (line_num - 2) % n == 0:
            print(text, end="")