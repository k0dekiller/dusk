from pytest import raises
from src.server.utils import *

class TestUtils:
    def test_hash_str(self) -> None:
        assert hash("test") == "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"

    def test_hash_none(self) -> None:
        assert hash(None) == None

    def test_over_1_valid(self) -> None:
        assert over(a=1, b=None) == ("a", 1)

    def test_over_2_valid(self) -> None:
        assert over(a=None, b=2) == ("b", 2)

    def test_over_invalid(self) -> None:
        with raises(UnknownOverloadException):
            over(a=None, b=None)