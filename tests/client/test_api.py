from typing import Any
from collections.abc import Generator

from _pytest.raises import RaisesExc
from pytest import fixture, raises

from src.server.db import Connector, Users, Invites
from threading import Thread
from werkzeug.serving import make_server
from src.server.app import app as flask

from src.client.api import Client, RequestError, LoginRequiredError

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
def user(users: Users) -> int:
    username = "system"
    users.create(username, "Password0!")
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
def username1() -> str:
    return "test1"
@fixture(scope="session")
def username2() -> str:
    return "test2"
@fixture(scope="session")
def password1() -> str:
    return "Password1!"
@fixture(scope="session")
def password2() -> str:
    return "Password2!"
def new_client(username: str, password: str) -> Client:
    return Client(f"http://{host}:{port}", username=username, password=password)
@fixture(scope="session")
def client1(username1: str, password1: str) -> Client:
    return new_client(username1, password1)
@fixture(scope="session")
def client2(username2: str, password2: str) -> Client:
    return new_client(username2, password2)

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

def test_connected(client1: Client) -> None:
    assert client1.connected() is True

def test_connected_invalid() -> None:
    assert Client("http://invalid").connected() is False

class TestSignup:
    def test_valid(self, client1: Client, client2: Client, invite: str, new_invite: str) -> None:
        client1.signup(invite)
        client2.signup(new_invite)

    def test_again(self, client1: Client, new_invite: str) -> None:
        with error("param.value.not_unique", "username"):
            client1.signup(new_invite)

    def test_limit(self, invite: str) -> None:
        with error("param.value.invalid", "invite"):
            new_client("test2", "Password2!").signup(invite)

    def test_invite_invalid(self, client1: Client) -> None:
        with error("param.value.invalid", "invite"):
            client1.signup("invalid")

    def test_username_invalid(self, new_invite: str) -> None:
        with error("param.value.invalid", ["username", "password"]):
            new_client("x", "password").signup(new_invite)

    def test_password_invalid(self, new_invite: str) -> None:
        with error("param.value.invalid", ["username", "password"]):
            new_client("username", "x").signup(new_invite)

class TestLogin:
    def test_valid(self, client1: Client) -> None:
        client1.login()

    def test_invalid(self) -> None:
        with error("param.value.invalid", ["username", "password"]):
            new_client("username", "password").login()

    def test_wrong(self) -> None:
        with error("param.value.invalid", ["username", "password"]):
            new_client("username", "Password1!").login()

class TestRelationships:
    def test_friend_token_missing(self, client2: Client) -> None:
        with raises(LoginRequiredError):
            client2.friend("test1", True)

    def test_friend_token_invalid(self, client2: Client) -> None:
        with error("header.value.invalid", "Authorization"):
            client2.token = "x"
            client2.friend("test1", True)

    def test_friend_username_invalid(self, client1: Client) -> None:
        with error("param.value.invalid", "username"):
            client1.friend("x", True)

    def test_friend_username_wrong(self, client1: Client) -> None:
        with error("param.value.invalid", "username"):
            client1.friend("test", True)

    def test_friend_username_self(self, client1: Client, username1: str) -> None:
        with error("param.value.invalid", "username"):
            client1.friend(username1, True)

    def test_friend_valid(self, client1: Client, username2: str) -> None:
        client1.friend(username2, True)

    def test_friend_again(self, client1: Client, username2: str) -> None:
        with error("param.resource.already_exists", "<receiver>"):
            client1.friend(username2, True)

    def test_block_valid(self, client1: Client, username2: str) -> None:
        client1.block(username2, True)