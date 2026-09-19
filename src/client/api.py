from typing import Any, Never, overload
import requests as rq

class RequestError(Exception):
    def __init__(self, code: int, desc: Any) -> None:
        self.code = code
        self.desc = desc

class Client:
    class endpoints:
        login = "login"
        signup = "signup"
        class users:
            @staticmethod
            def requests(username: str) -> str:
                return f"users/{username}/requests"
    class Users:
        def __init__(self, client: Client) -> None:
            self.client = client
        def __call__(self) -> Client:
            return self.client
        def send_request(self, username: str) -> None:
            r = self().check(rq.post(
                self().path(self().endpoints.users.requests(username)), json={
                "token": self().token
            }))
            print(r.status_code, r.json())
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
        self.users = self.Users(self)
    def path(self, s: str | None = None) -> str:
        return self.server + ("" if self.server.endswith("/") else "/") + (s if s is not None else "")
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
        self.check(rq.post(self.path(self.endpoints.signup), json={
            "invite": invite,
            "username": self.username,
            "password": self.password
        }))

    def login(self) -> str:
        r = self.check(rq.post(self.path(self.endpoints.login), json={
            "username": self.username,
            "password": self.password
        }))
        self.token = r.json()["data"]["token"]
        return self.token