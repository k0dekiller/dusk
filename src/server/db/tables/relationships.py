from ..table import Table
from ..imports import *

class Relationships(Table):
    name = "relationships"
    class RelationshipNotFoundError(Table.ResourceNotFoundError):
        pass
    class RelationshipAlreadyExistsError(Table.ResourceAlreadyExistsError):
        pass
    class RelationshipConstraintError(Table.ResourceConstraintError):
        pass
    class ForeignConstraintError(Table.ForeignConstraintError):
        pass
    type rq_type = Literal["friend", "blocked"]
    def __init__(self, conn: Connector) -> None:
        super().__init__(conn, self.Errors(
            self.RelationshipNotFoundError,
            self.RelationshipAlreadyExistsError,
            self.RelationshipConstraintError,
            self.ForeignConstraintError
        ))
        self.init()
    def init(self) -> None:
        self.utils.init(
            id="INTEGER PRIMARY KEY AUTOINCREMENT",
            sender="INTEGER NOT NULL -> users(id) ON DELETE CASCADE",
            receiver="INTEGER NOT NULL -> users(id) ON DELETE CASCADE",
            created_at="TEXT NOT NULL",
            friend_since="TEXT",
            blocked_since="TEXT",
            unique="sender, receiver",
            check_sender_not_receiver="sender <> receiver"
        )
    @overload#1
    def create(self, sender: int, receiver: int, type: rq_type) -> None: ...
    @overload#2
    def create(self, sender: int, receiver: int) -> None: ...
    def create(self, sender: int, receiver: int, type: rq_type | None = None) -> None:
        self.utils.create(sender=sender, receiver=receiver, created_at=now(), **(over(
            friend_since=now()  if type == "friend"  else None,
            blocked_since=now() if type == "blocked" else None,
        )) if type is not None else {})
    @overload#1
    def get(self, *, id: int) -> Row | None: ...
    @overload#2
    def get(self, *, sender: int, receiver: int) -> Row | None: ...
    @overload#3
    def get(self, *, sender: int) -> list[Row]: ...
    @overload#4
    def get(self, *, receiver: int) -> list[Row]: ...
    def get(self, *,
            id: int | None = None,
            sender: int | None = None,
            receiver: int | None = None
        ) -> list[Row] | Row | None:
        if id is not None:
            return self.utils.get(over(id=id))
        if sender is not None and receiver is not None:
            return self.utils.get(over(sender=sender, receiver=receiver))
        return self.utils.get(over(sender=sender, receiver=receiver), fetch="all")
    @overload#1
    def exists(self, *, id: int) -> bool: ...
    @overload#2
    def exists(self, *, sender: int, receiver: int) -> bool: ...
    def exists(self, *, id: int | None = None, sender: int | None = None, receiver: int | None = None) -> bool:
        return self.utils.any(over(id=id, sender=sender, receiver=receiver))
    @overload#1
    def set(self, *, id: int, **kwargs: Any) -> None: ...
    @overload#2
    def set(self, *, sender: int, receiver: int, **kwargs: Any) -> None: ...
    def set(self, *, id: int | None = None, sender: int | None = None, receiver: int | None = None, **kwargs: Any) -> None:
        self.utils.set(over(id=id, sender=sender, receiver=receiver), kwargs)
    def set_friend(self, sender: int, receiver: int, friend: bool) -> None:
        if self.exists(sender=sender, receiver=receiver):
            self.set(sender=sender, receiver=receiver, friend_since=now() if friend else None)
        else:
            self.create(sender=sender, receiver=receiver, type="friend")
    def set_blocked(self, sender: int, receiver: int, blocked: bool) -> None:
        if self.exists(sender=sender, receiver=receiver):
            self.set(sender=sender, receiver=receiver, blocked_since=now() if blocked else None)
        else:
            self.create(sender=sender, receiver=receiver, type="blocked")