from typing import Any, Never, overload
import requests as rq

class RequestError(Exception):
    """Raised whenever a `Client`'s request doesn't return a `2xx` status code."""
    def __init__(self, code: int, desc: Any) -> None:
        self.code = code
        self.desc = desc
class LoginRequiredError(Exception):
    """Raised whenever a `Client`'s request cannot be fulfilled because logging in is required."""

class Client:
    """The class used to communicate with the backend's REST API."""
    class endpoints:
        """The namespace that contains all the endpoints."""
        login = "login"
        signup = "signup"
        class users:
            """The namespace that contains all the endpoints in the /users directory."""
            @staticmethod
            def friend(username: str) -> str:
                """Returns the endpoint for setting the user `username`'s friend status."""
                return f"users/{username}/friend"
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
    def path(self, s: str | None = None) -> str:
        """Returns the assembled path by merging `self.server` with `s`."""
        return self.server + ("" if self.server.endswith("/") else "/") + (s if s is not None else "")
    def check[r: rq.Response](self, r: r) -> r:
        """Checks and returns `r` if it's a valid JSON object, otherwise it raises a `RequestError`."""
        # error definitions
        @overload
        def err() -> Never: ...
        @overload
        def err(error: Any) -> Never: ...
        def err(error: Any | None = None) -> Never:
            raise RequestError(r.status_code, error)
        # JSON validation
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
        """Returns `False` if getting `/` in the current server `self.server` raises a `requests.exceptions.ConnectionError`."""
        try:
            rq.get(self.path())
            return True
        except rq.exceptions.ConnectionError:
            return False

    @overload
    def signup(self, invite: str) -> None:
        """Signs up `self` by consuming a specified `invite`."""
    @overload
    def signup(self) -> None:
        """Signs up `self` without consuming an invite."""
    def signup(self, invite: str | None = None) -> None:
        """Signs up `self`."""
        self.check(rq.post(self.path(self.endpoints.signup), json={
            "invite": invite,
            "username": self.username,
            "password": self.password
        }))

    def login(self) -> str:
        """Logs in `self` and returns the resulting `self.token`."""
        r = self.check(rq.post(self.path(self.endpoints.login), json={
            "username": self.username,
            "password": self.password
        }))
        self.token = r.json()["data"]["token"]
        return self.token

    def require_token(self) -> None:
        """Raises `LoginRequiredError` if `self.token` is `None`."""
        if self.token is None:
            raise LoginRequiredError

    def friend(self, username: str, v: bool) -> None:
        """Sets the user `username` as a friend if `value` is `True`, or removes it otherwise."""
        self.require_token()
        self.check(rq.post(self.path(self.endpoints.users.friend(username)), json={
            "token": self.token,
            "value": v
        }))