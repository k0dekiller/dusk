# pyright: reportUnusedClass = false

from collections.abc import Callable
from sqlite3 import Row
from typing import Any, cast
from functools import wraps
from flask import Flask, jsonify

from . import rest
from .rest import response
from . import db
from .key import key
from . import validator as v

def mkpath(path: str = "") -> Callable[[str], str]:
    """Returns a function that appends a subpath to `path`."""
    def p(subpath: str = "") -> str:
        return f"{path}/{subpath}"
    return p

def row(row: Any) -> Row:
    """Casts `Any` to `Row`."""
    return row

def app(db_path: str = "data.db") -> Flask:
    """App factory; configures and returns a new `Flask` app."""
    app = Flask(__name__)
    app.config["DB_CONN"]           = conn          = db.Connector(db_path)
    app.config["DB_USERS"]          = users         = db.Users(conn)
    app.config["DB_INVITES"]        = invites       = db.Invites(conn)
    app.config["DB_RELATIONSHIPS"]  = relationships = db.Relationships(conn)
    app.config["DB_TOKENS"]         = tokens        = db.Tokens(conn)
    app.config["SECRET_KEY"]        = key

    class err:
        """The namespace that contains all the error functions."""
        @staticmethod
        def invalid(param: str | None) -> response:
            """Returns an error response specifying that its cause is in the given parameters."""
            return jsonify(rest.error(
                rest.err.param.value.invalid,
                desc=f"Invalid parameters",
                params=param
            )), 400
        @staticmethod
        def username_taken() -> response:
            """Returns an error response specifying that the specified username already exists."""
            return jsonify(rest.error(
                rest.err.param.value.not_unique,
                desc=f"Username taken",
                params="username"
            )), 400
        @staticmethod
        def wrong_login() -> response:
            """Returns an error response specifying that the specified username and password don't match an existing user."""
            return jsonify(rest.error(
                rest.err.param.value.invalid,
                desc=f"Wrong username or password",
                params=["username", "password"]
            )), 400
        @staticmethod
        def invalid_login() -> response:
            """Returns an error response specifying that the specified username and password are not valid."""
            return jsonify(rest.error(
                rest.err.param.value.invalid,
                desc=f"Invalid username or password",
                params=["username", "password"]
            )), 400
        @staticmethod
        def invalid_token() -> response:
            """Returns an error response specifying that the specified token doesn't exist."""
            return jsonify(rest.error(
                rest.err.param.value.invalid,
                desc=f"Invalid token",
                params="token"
            ))
        @staticmethod
        def invalid_invite() -> response:
            """Returns an error response specifying that the specified invite doesn't exist."""
            return jsonify(rest.error(
                rest.err.param.value.invalid,
                desc=f"Invalid invite code",
                params="invite"
            )), 400
    def success(data: rest.body | None = None) -> response:
        """Returns a successful response with optional additional data."""
        return jsonify(rest.success(data)), 200

    def token[**P, R](f: Callable[P, R]) -> Callable[P, R | response]:
        """Checks if the function `f`'s `token` is valid before running it and returning the result."""
        @wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | response:
            token: str = cast(str, kwargs["token"])
            if not tokens.valid(token=token):
                return err.invalid_token()
            return f(*args, **kwargs)
        return wrapper

    class Root:
        """Defines the endpoint handlers for `/`."""
        path = mkpath()
        @classmethod
        def sub(cls, path: str = "") -> Callable[[str], str]:
            """Returns a function that appends a subpath to this class' path plus a the subpath `path`."""
            return mkpath(cls.path(path))

        @app.post(path("login"))
        @rest.require("username", "password")
        @staticmethod
        def login(username: str, password: str) -> response:
            """Handles user login."""
            if not (v.username(username) and v.password(password)):
                return err.invalid_login()
            if not users.login(username, password):
                return err.wrong_login()
            info = row(users.get(username=username))
            id: int = info["id"]
            token = tokens.create(id)
            return success({"token": token})

        @app.post(path("signup"))
        @rest.require("username", "password", "invite")
        @staticmethod
        def signup(username: str, password: str, invite: str) -> response:
            """Handles user signup."""
            # check if username and password are valid
            if not (v.username(username) and v.password(password)):
                return err.invalid_login()
            # check if invite is valid
            if not (invites.valid(code=invite)):
                return err.invalid_invite()
            # check if username is taken
            if users.exists(username=username):
                return err.username_taken()

            # get invite info
            info = row(invites.get(code=invite))
            id: int = info["id"]
            count: int = info["use_count"]
            max: int | None = info["max_uses"]

            # consume the invite
            count += 1
            invites.set(code=invite, use_count=count)
            if max is not None and count >= max:
                invites.delete(code=invite)

            # create the user
            users.create(username, password, (id, count))

            return success()

    class Users(Root):
        """Defines the endpoint handlers for `/users`."""
        path = Root.sub("users")
        @app.post(path("<receiver>/requests"))
        @rest.require("token")
        @token
        @staticmethod
        def requests(token: str, receiver: str) -> response:
            """Handles user friend requests."""
            return success({"token": token, "receiver": receiver})

    return app

if __name__ == "__main__":
    app().run(debug=True, host="localhost", port=8080)