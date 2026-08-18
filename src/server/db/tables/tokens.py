from ..table import Table
from .users import Users
from ..imports import *

class Tokens(Table):
    name = "tokens"
    class TokenNotFoundError(Table.ResourceNotFoundError):
        pass
    class TokenAlreadyExistsError(Table.ResourceAlreadyExistsError):
        pass
    class OwnerNotFoundError(Users.UserNotFoundError):
        pass
    def __init__(self, conn: Connector) -> None:
        super().__init__(conn, self.Errors(
            self.TokenNotFoundError,
            self.TokenAlreadyExistsError,
            create_conflict=self.OwnerNotFoundError
        ))
        self.init()
    def init(self) -> None:
        self.utils.init(
            id="INTEGER PRIMARY KEY AUTOINCREMENT",
            owner="INTEGER NOT NULL -> users(id) ON DELETE CASCADE",
            archived_at="TEXT",
            token_hash="TEXT UNIQUE NOT NULL",
            created_at="TEXT NOT NULL",
            last_used_at="TEXT"
        )
    def create(self, owner: int) -> str:
        token = secrets.token_urlsafe(64)
        self.utils.create(owner=owner, token_hash=hash(token), created_at=now())
        return token
    @overload#1
    def get(self, *, token: str) -> Row | None: ...
    @overload#2
    def get(self, *, id: int) -> Row | None: ...
    def get(self, *, token: str | None = None, id: int | None = None) -> Row | None:
        return self.utils.get_sv(over(token_hash=hash(token), id=id))
    @overload#1
    def exists(self, *, token: str) -> bool: ...
    @overload#2
    def exists(self, *, id: int) -> bool: ...
    def exists(self, *, token: str | None = None, id: int | None = None) -> bool:
        return self.utils.any_sv(over(token_hash=hash(token), id=id))
    @overload#1
    def valid(self, *, token: str) -> bool: ...
    @overload#2
    def valid(self, *, id: int) -> bool: ...
    def valid(self, *, token: str | None = None, id: int | None = None) -> bool:
        return self.utils.any_sv(over(token_hash=hash(token), id=id), arch=False)
    @overload#1
    def archived(self, *, token: str) -> bool: ...
    @overload#2
    def archived(self, *, id: int) -> bool: ...
    def archived(self, *, token: str | None = None, id: int | None = None) -> bool:
        return self.utils.any_sv(over(token_hash=hash(token), id=id), arch=True)
    @overload#1
    def set(self, *, token: str, **kwargs: Any) -> None: ...
    @overload#2
    def set(self, *, id: int, **kwargs: Any) -> None: ...
    def set(self, *, token: str | None = None, id: int | None = None, **kwargs: Any) -> None:
        self.utils.set_sv(over(token_hash=hash(token), id=id), kwargs)
    @overload#1
    def delete(self, *, token: str, hard: bool = False) -> None: ...
    @overload#2
    def delete(self, *, id: int, hard: bool = False) -> None: ...
    def delete(self, *, token: str | None = None, id: int | None = None, hard: bool = False) -> None:
        self.utils.delete_sv(over(token_hash=hash(token), id=id), hard=hard)