from typing import Any, Never, overload
import requests as rq

class RequestError(Exception):
    def __init__(self, code: int, desc: Any) -> None:
        self.code = code
        self.desc = desc

class Client:
    class Endpoints:
        def __init__(self, root: str | None = None) -> None:
            self.root = root
            self.login = self.path("/login")
            self.signup = self.path("/signup")
        @overload
        def path(self) -> str: ...
        @overload
        def path(self, s: str) -> str: ...
        def path(self, s: str | None = None) -> str:
            return (self.root if self.root is not None else "") + (s if s is not None else "")
    @overload
    def __init__(self, server: str, *, token: str) -> None: ...
    @overload
    def __init__(self, server: str, *, username: str, password: str) -> None: ...
    @overload
    def __init__(self, server: str) -> None: ...
    def __init__(
            self, server: str, *,
            token: str | None = None,
            username: str | None = None, password: str | None = None
        ) -> None:
        self.server = server
        self.username = username
        self.password = password
        self.token = token
        self.endpoints = self.Endpoints(self.server)
        self.path = self.endpoints.path
    def check[r: rq.Response](self, r: r) -> r:
        @overload
        def err() -> Never: ...
        @overload
        def err(error: Any) -> Never: ...
        def err(error: Any | None = None) -> Never:
            raise RequestError(r.status_code, error)
        try:
            json = r.json()
        except rq.exceptions.JSONDecodeError:
            err()
        try:
            if json["success"]: return r
            err(json["error"])
        except KeyError, TypeError:
            err(json)

    def connected(self) -> bool:
        try:
            rq.get(self.path())
            return True
        except rq.exceptions.ConnectionError:
            return False

    @overload
    def signup(self, invite: str) -> None: ...
    @overload
    def signup(self, invite: str | None) -> None: ...
    def signup(self, invite: str | None) -> None:
        r = self.check(rq.post(self.endpoints.signup, json={
            "invite": invite,
            "username": self.username,
            "password": self.password
        }))
        print(r.status_code, r.json())

    def login(self) -> None:
        r = self.check(rq.post(self.endpoints.login, json={
            "username": self.username,
            "password": self.password
        }))
        print(r.status_code, r.json())