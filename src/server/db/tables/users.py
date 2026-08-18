from ..table import Table
from ..imports import *

class Users(Table):
    name = "users"
    class UserNotFoundError(Table.ResourceNotFoundError):
        pass
    class UserAlreadyExistsError(Table.ResourceAlreadyExistsError):
        pass
    class UserConstraintError(Table.ResourceConstraintError):
        pass
    def __init__(self, conn: Connector) -> None:
        super().__init__(conn, self.Errors(
            self.UserNotFoundError,
            self.UserAlreadyExistsError,
            self.UserConstraintError
        ))
        self.init()
    def init(self) -> None:
        self.utils.init(
            id="INTEGER PRIMARY KEY AUTOINCREMENT",
            username="TEXT UNIQUE NOT NULL",
            password_hash="TEXT NOT NULL",
            archived_at="TEXT",
            created_at="TEXT NOT NULL",
            used_invite="INTEGER",# -> invites(id)
            used_invite_n="INTEGER",
            check_used_invite="(used_invite IS NULL) OR (used_invite_n IS NOT NULL)"
        )
    @overload#1
    def create(self, username: str, password: str) -> None: ...
    @overload#2
    def create(self, username: str, password: str, invite: tuple[int, int]) -> None: ...
    @overload#3
    def create(self, username: str, password: str, invite: tuple[int | None, int | None]) -> None: ...
    def create(self, username: str, password: str, invite: tuple[int | None, int | None] | None = None) -> None:
        if invite is None:
            self.utils.create(username=username, password_hash=hash(password), created_at=now())
        else:
            self.utils.create(username=username, password_hash=hash(password), created_at=now(),
                used_invite=invite[0], used_invite_n=invite[1]
            )
    @overload#1
    def get(self, *, username: str) -> Row | None: ...
    @overload#2
    def get(self, *, id: int) -> Row | None: ...
    def get(self, *, username: str | None = None, id: int | None = None) -> Row | None:
        return self.utils.get_sv(over(username=username, id=id))
    @overload#1
    def exists(self, *, username: str) -> bool: ...
    @overload#2
    def exists(self, *, id: int) -> bool: ...
    def exists(self, *, username: str | None = None, id: int | None = None) -> bool:
        return self.utils.any_sv(over(username=username, id=id))
    @overload#1
    def valid(self, *, username: str) -> bool: ...
    @overload#2
    def valid(self, *, id: int) -> bool: ...
    def valid(self, *, username: str | None = None, id: int | None = None) -> bool:
        return self.utils.any_sv(over(username=username, id=id), arch=False)
    @overload#1
    def archived(self, *, username: str) -> bool: ...
    @overload#2
    def archived(self, *, id: int) -> bool: ...
    def archived(self, *, username: str | None = None, id: int | None = None) -> bool:
        return self.utils.any_sv(over(username=username, id=id), arch=True)
    @overload#1
    def set(self, *, username: str, **kwargs: Any) -> None: ...
    @overload#2
    def set(self, *, id: int, **kwargs: Any) -> None: ...
    def set(self, *, username: str | None = None, id: int | None = None, **kwargs: Any) -> None:
        self.utils.set_sv(over(username=username, id=id), kwargs)
    @overload#1
    def delete(self, *, username: str, hard: bool = False) -> None: ...
    @overload#2
    def delete(self, *, id: int, hard: bool = False) -> None: ...
    def delete(self, *, username: str | None = None, id: int | None = None, hard: bool = False) -> None:
        self.utils.delete_sv(over(username=username, id=id), hard=hard)
    def login(self, username: str, password: str) -> bool:
        @self.run
        def op(c: Cursor) -> bool:
            c.execute(
                f"SELECT id FROM {self.name} WHERE username = ? AND password_hash = ? AND archived_at IS NULL",
                (username, hash(password))
            )
            return c.fetchone() is not None
        return op