from ..table import Table
from .users import Users
from ..imports import *

class Invites(Table):
    name = "invites"
    class InviteNotFoundError(Table.ResourceNotFoundError):
        pass
    class InviteAlreadyExistsError(Table.ResourceAlreadyExistsError):
        pass
    class InviteConstraintError(Table.ResourceConstraintError):
        pass
    class ForeignConstraintError(Table.ForeignConstraintError):
        pass
    class OwnerNotFoundError(Users.UserNotFoundError):
        pass
    def __init__(self, conn: Connector) -> None:
        super().__init__(conn, self.Errors(
            self.InviteNotFoundError,
            self.InviteAlreadyExistsError,
            self.InviteConstraintError,
            self.ForeignConstraintError,
            create_foreign_constraint=self.OwnerNotFoundError
        ))
        self.init()
    def init(self) -> None:
        self.utils.init(
            id="INTEGER PRIMARY KEY AUTOINCREMENT",
            code="TEXT NOT NULL UNIQUE",
            owner="INTEGER NOT NULL -> users(id) ON DELETE CASCADE",
            max_uses="INTEGER",
            created_at="TEXT NOT NULL",
            use_count="INTEGER NOT NULL DEFAULT 0",
            archived_at="TEXT"
        )
    def create(self, owner: int, max_uses: int | None = 1) -> str:
        code = secrets.token_urlsafe(10)
        self.utils.create(code=code, owner=owner, max_uses=max_uses, created_at=now())
        return code
    @overload#1
    def get(self, *, code: str) -> Row | None: ...
    @overload#2
    def get(self, *, id: int) -> Row | None: ...
    def get(self, *, code: str | None = None, id: int | None = None) -> Row | None:
        return self.utils.get_sv(over(code=code, id=id))
    @overload#1
    def exists(self, *, code: str) -> bool: ...
    @overload#2
    def exists(self, *, id: int) -> bool: ...
    def exists(self, *, code: str | None = None, id: int | None = None) -> bool:
        return self.utils.any_sv(over(code=code, id=id))
    @overload#1
    def valid(self, *, code: str) -> bool: ...
    @overload#2
    def valid(self, *, id: int) -> bool: ...
    def valid(self, *, code: str | None = None, id: int | None = None) -> bool:
        return self.utils.any_sv(over(code=code, id=id), arch=False)
    @overload#1
    def archived(self, *, code: str) -> bool: ...
    @overload#2
    def archived(self, *, id: int) -> bool: ...
    def archived(self, *, code: str | None = None, id: int | None = None) -> bool:
        return self.utils.any_sv(over(code=code, id=id), arch=True)
    @overload#1
    def set(self, *, code: str, **kwargs: Any) -> None: ...
    @overload#2
    def set(self, *, id: int, **kwargs: Any) -> None: ...
    def set(self, *, code: str | None = None, id: int | None = None, **kwargs: Any) -> None:
        self.utils.set_sv(over(code=code, id=id), kwargs)
    @overload#1
    def delete(self, *, code: str, hard: bool = False) -> None: ...
    @overload#2
    def delete(self, *, id: int, hard: bool = False) -> None: ...
    def delete(self, *, code: str | None = None, id: int | None = None, hard: bool = False) -> None:
        self.utils.delete_sv(over(code=code, id=id), hard=hard)