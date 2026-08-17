from collections.abc import Callable
import re

class NoMatchException(Exception):
    pass

class Validator:
    def __init__(self, r: str) -> None:
        self.r = r
        self.v: Callable[[str], bool] = lambda s: re.fullmatch(r, s) is not None
    def match(self, s: str) -> bool:
        return self.v(s)
    def check(self, s: str) -> None:
        if not self(s): raise NoMatchException(f"{repr(s)} doesn't match {self}")
    def __call__(self, s: str) -> bool:
        return self.match(s)
    def __repr__(self) -> str:
        return repr(self.r)

username = Validator(r"[a-z][0-9a-z_]{3,15}")
password = Validator(r".{8,}")