import hashlib

cnet_id = "sareneac"
target = int("0000000fffffffffffffffffffffffffffffffffffffffffffffffffffffffff", 16)

nonce = 0
while True:
    s = cnet_id + str(nonce)
    h = hashlib.sha256(s.encode("utf-8")).hexdigest()
    if int(h, 16) < target:
        print("nonce =", nonce)
        print("string =", s)
        print("hash =", h)
        break
    nonce += 1