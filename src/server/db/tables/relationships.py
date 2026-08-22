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
            friends_since="TEXT",
            blocked_since="TEXT"
        )
    def create(self, sender: int, receiver: int) -> None:
        self.utils.create(sender=sender, receiver=receiver, created_at=now())
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
            return self.utils.get_sv(over(id=id))
        if sender is not None and receiver is not None:
            return self.utils.get_sv(over(sender=sender, receiver=receiver))
        return self.utils.get_sv(over(sender=sender, receiver=receiver), fetch="all")
    @overload#1
    def exists(self, *, id: int) -> bool: ...
    @overload#2
    def exists(self, *, sender: int, receiver: int) -> bool: ...
    def exists(self, *, id: int | None = None, sender: int | None = None, receiver: int | None = None) -> bool:
        return self.utils.any_sv(over(id=id, sender=sender, receiver=receiver))
    @overload#1
    def set(self, *, id: int, **kwargs: Any) -> None: ...
    @overload#2
    def set(self, *, sender: int, receiver: int, **kwargs: Any) -> None: ...
    def set(self, *, id: int | None = None, sender: int | None = None, receiver: int | None = None, **kwargs: Any) -> None:
        self.utils.set_sv(over(id=id, sender=sender, receiver=receiver), kwargs)