from pytest import fixture
from src.server.key import *
import os

@fixture(scope="session")
def key() -> Key:
    if os.path.exists("test.bin"):
        os.remove("test.bin")
    return Key("test.bin")

class TestKey:
    def test_gen(self, key: Key) -> None:
        key.gen()

    def test_read(self, key: Key) -> None:
        with open(key.file, "wb") as f:
            f.write(b"x")
        key.read()