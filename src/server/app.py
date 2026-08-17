from collections.abc import Callable
from typing import cast

from flask import Flask, jsonify

from . import rest
from .rest import response
from . import db

db.connect("data.db")
users = db.Users()
tokens = db.Tokens()

def mkpath(path: str = "") -> Callable[..., str]:
    def p(subpath: str = "") -> str:
        return f"{path}/{subpath}"
    return p

app = Flask(__name__)
from .key import key
app.config["SECRET_KEY"] = key

class err:
    @staticmethod
    def invalid(param: str | None) -> response:
        return jsonify(rest.error(
            rest.err.param.value.invalid,
            desc=f"Invalid parameters",
            params=param
        ))
    @staticmethod
    def invalid_login() -> response:
        return jsonify(rest.error(
            rest.err.param.value.invalid,
            desc=f"Invalid username or password",
            params=["username", "password"]
        ))

class Root:
    path = mkpath()
    @classmethod
    def sub(cls, path: str = "") -> Callable[..., str]:
        return mkpath(cls.path(path))

    @app.post(path("login"))
    @rest.require("username", "password")
    @staticmethod
    def login(username: str, password: str) -> response:
        valid = users.login(username, password)
        if not valid: return err.invalid_login()
        id = cast(int, users.id(username))
        token = tokens.create(id)
        print(valid, id, token)
        return jsonify(token)

class Users(Root):
    path = Root.sub("users")
    
    @app.post(path(""))
    @rest.require()
    @staticmethod
    def root_post(username: str, password: str) -> response:
        ... # TODO

app.run(debug=True, host="localhost", port=8080)