# pyright: reportUnusedClass = false

from collections.abc import Callable
from sqlite3 import Row
from typing import Any, Concatenate, cast
from functools import wraps
from flask import Flask, jsonify, request

from . import rest
from .rest import response
from . import db
from .key import Key
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
    app.config["SECRET_KEY_OBJ"]    = key           = Key("key.bin")
    app.config["SECRET_KEY"]        = key.read()

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
        def wrong_username() -> response:
            """Returns an error response specifying that the specified user doesn't exist."""
            return jsonify(rest.error(
                rest.err.param.value.invalid,
                desc=f"Wrong username",
                params="username"
            ))
        @staticmethod
        def wrong_login() -> response:
            """Returns an error response specifying that the specified username and password don't match an existing user."""
            return jsonify(rest.error(
                rest.err.param.value.invalid,
                desc=f"Wrong username or password",
                params=["username", "password"]
            )), 400
        @staticmethod
        def invalid_username() -> response:
            """Returns an error response specifying that the specified username is not valid."""
            return jsonify(rest.error(
                rest.err.param.value.invalid,
                desc=f"Invalid username",
                params="username"
            ))
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
                rest.err.header.value.invalid,
                desc=f"Invalid token",
                params="Authorization"
            ))
        @staticmethod
        def invalid_invite() -> response:
            """Returns an error response specifying that the specified invite doesn't exist."""
            return jsonify(rest.error(
                rest.err.param.value.invalid,
                desc=f"Invalid invite code",
                params="invite"
            )), 400
    def success(data: rest.body | list[Any] | None = None) -> response:
        """Returns a successful response with optional additional data."""
        return jsonify(rest.success(data)), 200

    def token[**P, R](f: Callable[Concatenate[str, P], R]) -> Callable[P, R | response]:
        """Checks if the `Authorization` header is a valid token."""
        @wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | response:
            def validate() -> str | None:
                token = request.headers.get("Authorization", None)
                if token is None: return
                token = token.removeprefix("Bearer").strip()
                if not tokens.valid(token=token): return
                return token
            if (token := validate()) is None:
                return err.invalid_token()
            return f(token, *args, **kwargs)
        return wrapper

    def user[**P, R](*usernames: str) -> Callable[[Callable[P, R]], Callable[P, R | response]]:
        """Checks if the function's specified arguments' values are valid users before running it and returning the result."""
        def w(f: Callable[P, R]) -> Callable[P, R | response]:
            @wraps(f)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | response:
                for username in usernames:
                    username = cast(str, kwargs[username])
                    # check if username is valid
                    if not v.username(username):
                        return err.invalid_username()
                    # check if username exists
                    if not users.valid(username=username):
                        return err.wrong_username()
                return f(*args, **kwargs)
            return wrapper
        return w

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

        @staticmethod
        def _relationship(token: str, receiver: str, action: str, value: bool, conflict_desc: str | None) -> response:
            s: int = row(tokens.get(token=token))["owner"]
            r: int = row(users.get(username=receiver))["id"]
            if s == r:
                return jsonify(rest.error(
                    rest.err.param.value.invalid,
                    desc=f"Sender can't also be receiver",
                    params="username"
                ))
            relationship = relationships.get(sender=s, receiver=r)
            if relationship is not None and relationship[f"{action}_since"] is not None:
                return jsonify(rest.error(
                    rest.err.resource.already_exists,
                    desc=conflict_desc,
                    params="<receiver>"
                )), 400
            relationships.set_friend(s, r, value)
            return success()

        @app.post(path("<receiver>/friend"))
        @rest.require("value")
        @token
        @user("receiver")
        @staticmethod
        def friend(token: str, receiver: str, value: bool) -> response:
            """Handles user friend settings."""
            return Users._relationship(
                token, receiver, "friend", value,
                "Receiver is already a friend"
            )

        @app.post(path("<receiver>/block"))
        @rest.require("value")
        @token
        @user("receiver")
        @staticmethod
        def block(token: str, receiver: str, value: bool) -> response:
            """Handles user block settings."""
            return Users._relationship(
                token, receiver, "blocked", value,
                "Receiver is already blocked"
            )

    return app

if __name__ == "__main__":
    app().run(debug=True, host="localhost", port=3050)