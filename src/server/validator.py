"""Provides tools for regex-based string validation."""

from collections.abc import Callable
import re

class NoMatchException(Exception):
    """Raised whenever the `Validator.check` function fails a match."""

class Validator:
    """The class that allows for regex-based string validation."""
    def __init__(self, r: str) -> None:
        self.r = r
        self.v: Callable[[str], bool] = lambda s: re.fullmatch(r, s) is not None
    def match(self, s: str) -> bool:
        """Returns `True` if `s` matches `self.v`."""
        return self.v(s)
    def check(self, s: str) -> None:
        """Raises `NoMatchException` if `s` doesn't match `self.v`."""
        if not self(s): raise NoMatchException(f"{repr(s)} doesn't match {self}")
    def __call__(self, s: str) -> bool:
        return self.match(s)
    def __repr__(self) -> str:
        return repr(self.r)

username = Validator(r"[a-z][0-9a-z_]{3,15}")
password = Validator(r".{8,}")