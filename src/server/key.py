import os

class Key:
    """The class that allows for key management."""
    def __init__(self, file: str) -> None:
        self.file = file
        if not os.path.exists(self.file): self.gen()
        else: self.read()
    def gen(self) -> None:
        """Generates a new key and saves it in `self.file`."""
        self.key = os.urandom(32)
        with open(self.file, "wb") as f:
            f.write(self.key)
    def read(self) -> bytes:
        """Returns and updates `self.file` to the stored value."""
        with open(self.file, "rb") as f:
            k = f.read()
        if len(k) != 32: self.gen()
        else: self.key = k
        return self.key