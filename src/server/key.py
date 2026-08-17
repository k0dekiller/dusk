import os

class KeyNotFoundError(Exception):
    pass

file = f"{os.path.dirname(os.path.abspath(__file__))}/key.bin"
key = b""

def gen() -> None:
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