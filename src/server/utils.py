from typing import Any, overload
from datetime import datetime, timezone
import hashlib
import argon2.exceptions as argon2exc
from argon2 import PasswordHasher

class UnknownOverloadException(Exception):
    """Raised by `over` whenever all of the given `kwargs` are `None`."""

ph = PasswordHasher()

def now() -> str:
    """Returns the current ISO-formatted date and time."""
    return datetime.now(timezone.utc).isoformat()

@overload#1
def hash(s: str) -> str: ...
@overload#2
def hash(s: None) -> None: ...
def hash(s: str | None) -> str | None:
    """Hashes and returns the string `s`."""
    if s is None: return
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

@overload#1
def argon_hash(s: str) -> str: ...
@overload#2
def argon_hash(s: None) -> None: ...
def argon_hash(s: str | None) -> str | None:
    """Argon-hashes and returns the string `s`."""
    if s is None: return
    return ph.hash(s)

def argon_verify(hash: str, s: str) -> bool:
    """Verifies the argon-hashed string `hash` against the original string `s`."""
    try:
        ph.verify(hash, s)
        return True
    except argon2exc.VerifyMismatchError:
        return False

def default[A, B](value: A | None, default: B) -> A | B:
    """Returns `value` if it's not `None`, otherwise it returns `default`."""
    return value if value is not None else default

def over(**kwargs: Any) -> dict[str, Any]:
    """Returns the first argument in `kwargs` which doesn't have a value of `None`."""
    d: dict[str, Any] = {}
    for k, v in kwargs.items():
        if v is None: continue
        d[k] = v
    if d:
        return d
    raise UnknownOverloadException