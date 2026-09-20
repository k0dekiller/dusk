import os

file = f"key.bin"
key = b""

def gen() -> None:
    """Generates a new key and saves it in `file`."""
    global key
    key = os.urandom(32)
    with open(file, "wb") as f:
        f.write(key)

if not os.path.exists(file): gen()
else:
    with open(file, "rb") as f:
        k = f.read()
        if len(k) != 32: gen()
        else: key = k