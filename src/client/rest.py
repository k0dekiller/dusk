from functools import wraps
from typing import Final
from collections.abc import Callable
import requests as rq

type token = str

class NoConnectionException(Exception):
    pass

server: str = ""
def connect(_server: str | None) -> None:
    global server
    server = _server if _server is not None else ""

def connected[**P, R](f: Callable[P, R]) -> Callable[P, R]:
    @wraps(f)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        if server == "": raise NoConnectionException("This function requires connecting to a server with `.connect()`")
        return f(*args, **kwargs)
    return wrapper

class endpoints:
    login: Final = "/login"

@connected
def link(s: str) -> str:
    return server + s

@connected
def login(username: str | None, password: str | None) -> token:
    r = rq.post(f"{server}{endpoints.login}", json={
        "username": username,
        "password": password
    })
    
    print(r.status_code, r.json())