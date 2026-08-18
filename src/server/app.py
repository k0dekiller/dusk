from collections.abc import Callable
from sqlite3 import Row
from typing import Any, cast
from flask import Flask, jsonify

from . import rest
from .rest import response
from . import db
from .key import key
from . import validator as v

def mkpath(path: str = "") -> Callable[..., str]:
    def p(subpath: str = "") -> str:
        return f"{path}/{subpath}"
    return p

class err:
    @staticmethod
    def invalid(param: str | None) -> response:
        return jsonify(rest.error(
            rest.err.param.value.invalid,
            desc=f"Invalid parameters",
            params=param
        )), 400
    @staticmethod
    def username_taken() -> response:
        return jsonify(rest.error(
            rest.err.param.value.not_unique,
            desc=f"Username taken",
            params="username"
        )), 400
    @staticmethod
    def wrong_login() -> response:
        return jsonify(rest.error(
            rest.err.param.value.invalid,
            desc=f"Wrong username or password",
            params=["username", "password"]
        ))
    @staticmethod
    def invalid_login() -> response:
        return jsonify(rest.error(
            rest.err.param.value.invalid,
            desc=f"Invalid username or password",
            params=["username", "password"]
        )), 400
    @staticmethod
    def invalid_invite() -> response:
        return jsonify(rest.error(
            rest.err.param.value.invalid,
            desc=f"Invalid invite code",
            params="invite"
        )), 400
def success(data: rest.body | None = None) -> response:
    return jsonify(rest.success()), 200

def row(row: Any) -> Row: return cast(Row, row)

def app(db_path: str = "data.db") -> Flask:
    app = Flask(__name__)
    app.config["DB_CONN"] = conn = db.Connector(db_path)
    app.config["DB_USERS"] = users = db.Users(conn)
    app.config["DB_INVITES"] = invites = db.Invites(conn)
    app.config["DB_TOKENS"] = tokens = db.Tokens(conn)
    app.config["SECRET_KEY"] = key

    class Root:
        path = mkpath()
        @classmethod
        def sub(cls, path: str = "") -> Callable[..., str]:
            return mkpath(cls.path(path))

        @app.post(path("login"))
        @rest.require("username", "password")
        @staticmethod
        def login(username: str, password: str) -> response:
            if not (v.username(username) and v.password(password) and users.login(username, password)):
                return err.invalid_login()
            info = row(users.get(username=username))
            id: int = info["id"]
            token = tokens.create(id)
            return success({"token": token})

        @app.post(path("signup"))
        @rest.require("username", "password", "invite")
        @staticmethod
        def signup(username: str, password: str, invite: str) -> response:
            # check if invite is valid
            if not (invites.valid(code=invite)):
                return err.invalid_invite()
            # check if username and password are valid
            if not (v.username(username) and v.password(password)):
                return err.invalid_login()
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

    class Users(Root): # pyright: ignore[reportUnusedClass]
        path = Root.sub("users")
        ...

    return app

if __name__ == "__main__":
    app().run(debug=True, host="localhost", port=8080)