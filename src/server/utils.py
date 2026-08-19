from typing import Any, overload
from datetime import datetime, timezone
import hashlib

class UnknownOverloadException(Exception):
    pass

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

@overload#1
def hash(s: str) -> str: ...
@overload#2
def hash(s: None) -> None: ...
def hash(s: str | None) -> str | None:
    if s is None: return
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def default[A, B](value: A | None, default: B) -> A | B:
    return value if value is not None else default

def over(**kwargs: Any) -> tuple[str, Any]:
    for k, v in kwargs.items():
        if v is None: continue
        return k, v
    raise UnknownOverloadException