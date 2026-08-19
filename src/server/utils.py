from typing import Any, overload
from datetime import datetime, timezone
import hashlib
import argon2.exceptions as argon2exc
from argon2 import PasswordHasher

class UnknownOverloadException(Exception):
    pass

ph = PasswordHasher()

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

@overload#1
def hash(s: str) -> str: ...
@overload#2
def hash(s: None) -> None: ...
def hash(s: str | None) -> str | None:
    if s is None: return
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

@overload#1
def argon_hash(s: str) -> str: ...
@overload#2
def argon_hash(s: None) -> None: ...
def argon_hash(s: str | None) -> str | None:
    if s is None: return
    return ph.hash(s)

def argon_verify(hash: str, s: str) -> bool:
    try:
        ph.verify(hash, s)
        return True
    except argon2exc.VerifyMismatchError:
        return False

def default[A, B](value: A | None, default: B) -> A | B:
    return value if value is not None else default

def over(**kwargs: Any) -> tuple[str, Any]:
    for k, v in kwargs.items():
        if v is None: continue
        return k, v
    raise UnknownOverloadException