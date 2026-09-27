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
    class ForeignConstraintError(Table.ForeignConstraintError):
        pass
    def __init__(self, conn: Connector) -> None:
        super().__init__(conn, self.Errors(
            self.UserNotFoundError,
            self.UserAlreadyExistsError,
            self.UserConstraintError,
            self.ForeignConstraintError
        ))
        self.init()
    def init(self) -> None:
        self.utils.init(
            username="TEXT PRIMARY KEY",
            password_hash="TEXT NOT NULL",
            archived_at="TEXT",
            created_at="TEXT NOT NULL",
            used_invite="INTEGER",# -> invites(id)
            used_invite_n="INTEGER",
            check_used_invite="(used_invite IS NULL) OR (used_invite_n IS NOT NULL)"
        )
    @overload#1
    def create(self, username: str, password: str, /) -> None: ...
    @overload#2
    def create(self, username: str, password: str, invite: tuple[int, int], /) -> None: ...
    @overload#3
    def create(self, username: str, password: str, invite: tuple[int | None, int | None], /) -> None: ...
    def create(self, username: str, password: str, invite: tuple[int | None, int | None] | None = None, /) -> None:
        if invite is None:
            self.utils.create(username=username, password_hash=argon_hash(password), created_at=now())
        else:
            self.utils.create(username=username, password_hash=argon_hash(password), created_at=now(),
                used_invite=invite[0], used_invite_n=invite[1]
            )
    def get(self, username: str, /) -> Row | None:
        return self.utils.get(over(username=username))
    def exists(self, username: str, /) -> bool:
        return self.utils.any(over(username=username))
    def valid(self, username: str, /) -> bool:
        return self.utils.any(over(username=username), arch=False)
    def archived(self, username: str, /) -> bool:
        return self.utils.any(over(username=username), arch=True)
    def set(self, username: str, /, **kwargs: Any) -> None:
        self.utils.set(over(username=username), kwargs)
    def delete(self, username: str, /, *, hard: bool = False) -> None:
        self.utils.delete(over(username=username), hard=hard)
    def login(self, username: str, password: str, /) -> bool:
        row = self.utils.get(over(username=username), arch=False)
        if row is None: return False
        return argon_verify(row["password_hash"], password)