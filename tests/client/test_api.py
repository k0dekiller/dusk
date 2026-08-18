from typing import Any
from collections.abc import Generator

from _pytest.raises import RaisesExc
from pytest import fixture, raises

from src.server.db import Connector, Users, Invites, Tokens
from threading import Thread
from werkzeug.serving import make_server
from src.server.app import app as flask

from src.client.api import Client, RequestError

import os

file = "test_api.db"
host, port = "localhost", 8181

if os.path.exists(file): os.remove(file)

# SERVER THREAD
class Server(Thread):
    def __init__(self) -> None:
        super().__init__(daemon=True)
        app = flask(file)
        app.config.update(TESTING=True) # type: ignore
        self.server = make_server(host, port, app)
        self.ctx = app.app_context()
        self.ctx.push()
    def run(self) -> None:
        self.server.serve_forever()
    def shutdown(self) -> None:
        self.server.shutdown()

# SERVER FIXTURES
@fixture(scope="session")
def server() -> Generator[Server, Any, None]:
    app = Server()
    app.start()
    yield app
    app.shutdown()
    app.join()
@fixture(scope="session")
def conn() -> Connector:
    return Connector(file)
@fixture(scope="session")
def users(conn: Connector) -> Users:
    return Users(conn)
@fixture(scope="session")
def invites(conn: Connector) -> Invites:
    return Invites(conn)
@fixture(scope="session")
def tokens(conn: Connector) -> Tokens:
    return Tokens(conn)
@fixture(scope="session")
def user(users: Users) -> int:
    username = "system"
    users.create(username, "password")
    info = users.get(username=username)
    assert info is not None
    return info["id"]
@fixture
def new_invite(invites: Invites, user: int) -> str:
    return invites.create(user)
@fixture(scope="session")
def invite(invites: Invites, user: int) -> str:
    return invites.create(user)

# CLIENT FIXTURES
@fixture(scope="session")
def username() -> str: return "test1"
@fixture(scope="session")
def password() -> str: return "password1"
def new_client(username: str, password: str) -> Client:
    return Client(f"http://{host}:{port}", username=username, password=password)
@fixture(scope="session")
def client(username: str, password: str) -> Client:
    return new_client(username, password)

# ERROR CHECKER
def error(code: str, params: list[str] | str) -> RaisesExc[RequestError]:
    def check(e: RequestError) -> bool:
        nonlocal params
        if isinstance(params, str):
            params = [params]
        return e.desc["code"] == code and e.desc["params"] == params
    return raises(RequestError, check=check)

# TESTS
def test_server_running(server: Server) -> None:
    assert server.is_alive() is True

def test_connected(client: Client) -> None:
    assert client.connected() is True

class TestSignup:
    def test_valid(self, client: Client, invite: str) -> None:
        client.signup(invite)

    def test_again(self, client: Client, new_invite: str) -> None:
        with error("param.value.not_unique", "username"):
            client.signup(new_invite)

    def test_limit(self, invite: str) -> None:
        with error("param.value.invalid", "invite"):
            new_client("test2", "password2").signup(invite)

    def test_invite_invalid(self, client: Client) -> None:
        with error("param.value.invalid", "invite"):
            client.signup("invalid")

    def test_username_invalid(self, new_invite: str) -> None:
        with error("param.value.invalid", ["username", "password"]):
            new_client("x", "password").signup(new_invite)

    def test_password_invalid(self, new_invite: str) -> None:
        with error("param.value.invalid", ["username", "password"]):
            new_client("username", "x").signup(new_invite)

class TestLogin:
    def test_valid(self, client: Client) -> None:
        client.login()

    def test_invalid(self) -> None:
        with error("param.value.invalid", ["username", "password"]):
            new_client("username", "password").login()