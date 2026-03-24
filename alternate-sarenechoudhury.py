from sys import argv, exit

try:
    if argv[1] == "-n":
        n = int(argv[2])
        filename = argv[3]
    else:
        n = 2
        filename = argv[1]

    with open(filename) as f:
        print(*list(f)[1::n], end='')

except (IndexError, ValueError):
    exit("Usage: python alternate-sarenechoudhury.py [-n N] <filename>")

