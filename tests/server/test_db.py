from pytest import raises, fixture
from src.server.db import Connector, Table, Users, Invites, Tokens
from sqlite3 import Cursor

import os

@fixture(scope="session")
def conn() -> Connector:
    file = "test_db.db"
    if os.path.exists(file): os.remove(file)
    return Connector(file)

class TestUtils:
    pass

@fixture(scope="session")
def table(conn: Connector) -> Table:
    return Table(conn)
class TestTable:
    def test_run_success(self, table: Table) -> None:
        @table.run
        def op(c: Cursor) -> None:
            pass
    def test_run_fail(self, table: Table) -> None:
        with raises(Exception):
            @table.run
            def op(c: Cursor) -> None:
                raise Exception

@fixture(scope="session")
def users(conn: Connector) -> Users:
    return Users(conn)
class TestUsers:
    def test_create_valid(self, users: Users) -> None:
        users.create("test1", "password1")

    def test_create_username_taken(self, users: Users) -> None:
        with raises(users.UserAlreadyExistsError):
            users.create("test1", "password1")

    def test_create_invite_valid(self, users: Users) -> None:
        users.create("test2", "password2", (1, 1))

    def test_create_invite_id_invalid(self, users: Users) -> None:
        users.create("test3", "password3", (None, 1))

    def test_create_invite_n_invalid(self, users: Users) -> None:
        with raises(users.UserConstraintError):
            users.create("test3", "password3", (1, None))

    def test_info_valid(self, users: Users) -> None:
        info = users.get(username="test1")
        assert info != None
        assert info["id"] == 1

    def test_info_invalid(self, users: Users) -> None:
        assert users.get(username="invalid") is None

    def test_exists_valid(self, users: Users) -> None:
        assert users.exists(username="test1") is True

    def test_exists_invalid(self, users: Users) -> None:
        assert users.exists(username="invalid") is False

    def test_valid_valid(self, users: Users) -> None:
        assert users.valid(username="test1") is True

    def test_valid_invalid(self, users: Users) -> None:
        assert users.valid(username="invalid") is False

    def test_archived_valid(self, users: Users) -> None:
        assert users.archived(username="test1") is False

    def test_archived_invalid(self, users: Users) -> None:
        assert users.archived(username="invalid") is False

    def test_login_incorrect(self, users: Users) -> None:
        assert users.login("test1", "wrong1") is False

    def test_login_correct(self, users: Users) -> None:
        assert users.login("test1", "password1") is True

    def test_archive_valid(self, users: Users) -> None:
        users.delete(username="test1")

    def test_archive_invalid(self, users: Users) -> None:
        with raises(users.UserNotFoundError):
            users.delete(username="invalid")

    def test_login_archived(self, users: Users) -> None:
        assert users.login("test1", "password1") is False

    def test_exists_archived(self, users: Users) -> None:
        assert users.exists(username="test1") is True

    def test_valid_archived(self, users: Users) -> None:
        assert users.valid(username="test1") is False

    def test_archived_archived(self, users: Users) -> None:
        assert users.archived(username="test1") is True

    def test_delete_valid(self, users: Users) -> None:
        users.delete(username="test1", hard=True)

    def test_delete_invalid(self, users: Users) -> None:
        with raises(users.UserNotFoundError):
            users.delete(username="invalid", hard=True)

    def test_login_correct_deleted(self, users: Users) -> None:
        assert users.login("test1", "password1") is False

    def test_exists_deleted(self, users: Users) -> None:
        assert users.exists(username="test1") is False

    def test_valid_deleted(self, users: Users) -> None:
        assert users.valid(username="test1") is False

    def test_archived_deleted(self, users: Users) -> None:
        assert users.archived(username="test1") is False

@fixture(scope="session")
def invites(conn: Connector) -> Invites:
    return Invites(conn)
class TestInvites:
    @fixture(scope="session")
    def invite(self, invites: Invites) -> str:
        return invites.create(2)

    def test_create_owner_invalid(self, invites: Invites) -> None:
        with raises(invites.OwnerNotFoundError):
            invites.create(0)

    def test_info_valid(self, invites: Invites, invite: str) -> None:
        info = invites.get(code=invite)
        assert info != None
        assert info["id"] == 1

    def test_info_invalid(self, invites: Invites) -> None:
        assert invites.get(code="invalid") is None

    def test_exists_valid(self, invites: Invites, invite: str) -> None:
        assert invites.exists(code=invite) is True

    def test_exists_invalid(self, invites: Invites) -> None:
        assert invites.exists(code="invalid") is False

    def test_valid_valid(self, invites: Invites, invite: str) -> None:
        assert invites.valid(code=invite) is True

    def test_valid_invalid(self, invites: Invites) -> None:
        assert invites.valid(code="invalid") is False

    def test_archived_valid(self, invites: Invites, invite: str) -> None:
        assert invites.archived(code=invite) is False

    def test_archived_invalid(self, invites: Invites) -> None:
        assert invites.archived(code="invalid") is False

    def test_archive_valid(self, invites: Invites, invite: str) -> None:
        invites.delete(code=invite)

    def test_archive_invalid(self, invites: Invites) -> None:
        with raises(invites.InviteNotFoundError):
            invites.delete(code="invalid")

    def test_exists_archived(self, invites: Invites, invite: str) -> None:
        assert invites.exists(code=invite) is True

    def test_valid_archived(self, invites: Invites, invite: str) -> None:
        assert invites.valid(code=invite) is False

    def test_archived_archived(self, invites: Invites, invite: str) -> None:
        assert invites.archived(code=invite) is True

    def test_delete_valid(self, invites: Invites, invite: str) -> None:
        invites.delete(code=invite, hard=True)

    def test_delete_invalid(self, invites: Invites) -> None:
        with raises(invites.InviteNotFoundError):
            invites.delete(code="invalid", hard=True)

    def test_exists_deleted(self, invites: Invites, invite: str) -> None:
        assert invites.exists(code=invite) is False

    def test_valid_deleted(self, invites: Invites, invite: str) -> None:
        assert invites.valid(code=invite) is False

    def test_archived_deleted(self, invites: Invites, invite: str) -> None:
        assert invites.archived(code=invite) is False

@fixture(scope="session")
def tokens(conn: Connector) -> Tokens:
    return Tokens(conn)
class TestTokens:
    @fixture(scope="session")
    def token(self, tokens: Tokens) -> str:
        return tokens.create(2)

    def test_create_owner_invalid(self, tokens: Tokens) -> None:
        with raises(tokens.OwnerNotFoundError):
            tokens.create(0)

    def test_info_valid(self, tokens: Tokens, token: str) -> None:
        info = tokens.get(token=token)
        assert info != None
        assert info["id"] == 1

    def test_info_invalid(self, tokens: Tokens) -> None:
        assert tokens.get(token="invalid") is None

    def test_exists_valid(self, tokens: Tokens, token: str) -> None:
        assert tokens.exists(token=token) is True

    def test_exists_invalid(self, tokens: Tokens) -> None:
        assert tokens.exists(token="invalid") is False

    def test_valid_valid(self, tokens: Tokens, token: str) -> None:
        assert tokens.valid(token=token) is True

    def test_valid_invalid(self, tokens: Tokens) -> None:
        assert tokens.valid(token="invalid") is False

    def test_archived_valid(self, tokens: Tokens, token: str) -> None:
        assert tokens.archived(token=token) is False

    def test_archived_invalid(self, tokens: Tokens) -> None:
        assert tokens.archived(token="invalid") is False

    def test_archive_token_valid(self, tokens: Tokens, token: str) -> None:
        tokens.delete(token=token)

    def test_archive_token_invalid(self, tokens: Tokens) -> None:
        with raises(tokens.TokenNotFoundError):
            tokens.delete(token="invalid")

    def test_exists_archived(self, tokens: Tokens, token: str) -> None:
        assert tokens.exists(token=token) is True

    def test_valid_archived(self, tokens: Tokens, token: str) -> None:
        assert tokens.valid(token=token) is False

    def test_archived_archived(self, tokens: Tokens, token: str) -> None:
        assert tokens.archived(token=token) is True

    def test_delete_token_valid(self, tokens: Tokens, token: str) -> None:
        tokens.delete(token=token, hard=True)

    def test_delete_token_invalid(self, tokens: Tokens) -> None:
        with raises(tokens.TokenNotFoundError):
            tokens.delete(token="invalid", hard=True)

    def test_exists_deleted(self, tokens: Tokens, token: str) -> None:
        assert tokens.exists(token=token) is False

    def test_valid_deleted(self, tokens: Tokens, token: str) -> None:
        assert tokens.valid(token=token) is False

    def test_archived_deleted(self, tokens: Tokens, token: str) -> None:
        assert tokens.archived(token=token) is False