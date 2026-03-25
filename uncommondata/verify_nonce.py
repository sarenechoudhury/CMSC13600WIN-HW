import hashlib

cnet_id = "sareneac"
nonce = "201633913"

target = int("0000000fffffffffffffffffffffffffffffffffffffffffffffffffffffffff", 16)

h = hashlib.sha256((cnet_id + nonce).encode("utf-8")).hexdigest()

print("hash:", h)

value = int(h, 16)
print("value:", value)

if value < target:
    print("✅ VALID: hash is below target")
else:
    print("❌ INVALID: hash is NOT below target")