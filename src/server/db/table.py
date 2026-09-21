from ..utils import *
from .imports import *

class NoRowsAffectedError(Exception):
    """Raised according to the conventions defined in `/docs/database.md#Idempotency`."""

class Table:
    """The abstract class that provides tools to simplify database operations."""
    class Errors:
        """The class that holds the collection of custom errors raised by `Table` subclasses."""
        def __init__(self,
                not_found: type[Exception],
                conflict: type[Exception],
                constraint: type[Exception],
                foreign_constraint: type[Exception],
                *,
                create_conflict: type[Exception] | None = None,
                create_constraint: type[Exception] | None = None,
                create_foreign_constraint: type[Exception] | None = None
            ) -> None:
            self.not_found = not_found
            self.conflict = conflict
            self.constraint = constraint
            self.foreign_constraint = foreign_constraint
            self.create_conflict = default(create_conflict, conflict)
            self.create_constraint = default(create_constraint, constraint)
            self.create_foreign_constraint = default(create_foreign_constraint, constraint)
    class Utils:
        """Provides tools that simplify database queries."""
        type kwargs_t = dict[str, Any]
        type optdefault = str | bool | None
        type fetch_one = Literal["one"]
        type fetch_all = Literal["all"]
        type fetch_mode = fetch_one | fetch_all | int
        type fetch_result = list[Row] | Row | None
        type optfetch_mode = fetch_mode | None
        type optfetch_result = fetch_result | int
        type LiveQuery[R] = Callable[Concatenate[str | None, Any, ...], R]
        def __init__(self, _self: Table, errors: Table.Errors, arch: str = "archived_at") -> None:
            self._self = _self
            self.errors = errors
            self.arch = arch
            self.rows = -1
        def __call__(self) -> Table:
            return self._self
        def where(self, cond: str | None = None) -> str:
            """Returns the assembled `WHERE` clause with the condition `cond`, or an empty string if it's `None`."""
            return f" WHERE {cond}" if cond is not None else ""
        def assemble[R](
                self,
                func: LiveQuery[R],
                args: kwargs_t, q: str | None = None, *v: Any,
                arch: optdefault = None
            ) -> R:
            """Assembles a query depending on the given `LiveQuery` function `func`."""
            if isinstance(arch, bool): arch = f"{"!" if arch else ""}{self.arch}"
            if isinstance(arch, str) and arch.startswith("!"):
                arch = arch[1:]
                archinv = True
            else: archinv = False
            return func(""
                + (" AND ".join(f"{k} = ?" for k in args.keys()))
                + (f" AND {arch} IS {" NOT " if archinv else ""}NULL" if arch is not None else "")
                + (f" {q}" if q is not None else ""),
                *args.values(), *v
            )
        @overload
        def exec(self, query: str, *v: Any, fetch: Literal["one"]) -> Row | None:
            """Executes the query `query`, fetches one row and returns it."""
        @overload
        def exec(self, query: str, *v: Any, fetch: Literal["all"] | int) -> list[Row]:
            """Executes the query `query`, fetches all rows and returns them."""
        @overload
        def exec(self, query: str, *v: Any, fetch: None = None) -> int:
            """Executes the query `query` and returns the number of affected rows."""
        def exec(self, query: str, *v: Any, fetch: optfetch_mode = None) -> optfetch_result:
            """Executes the query `query` and returns the result according to the fetch mode `fetch`."""
            @self().run
            def op(c: Cursor) -> Table.Utils.optfetch_result:
                c.execute(query, v)
                match fetch:
                    case "one": return c.fetchone() # -> Row | None
                    case "all": return c.fetchall() # -> list[Row]
                    case None: return c.rowcount # -> int
                    case _: return c.fetchmany() # -> list[Row]
            return op
        def init(self, **kwargs: str) -> None:
            """
            Initializes a new table from the given `kwargs` with the following rules:

            1. `<key> = <value>` becomes `<key> <value>`;
            2. `<key> = <value> -> <foreign>` becomes `<key> <value>` and `FOREIGN KEY (<key>) REFERENCES <foreign>`;
            3. Prefixing a key with `check_` turns it into the constraint `CONSTRAINT <key> CHECK (<value>)`.
            """
            cols: list[str] = []
            foreign: list[str] = []
            check: list[str] = []
            for k, v in kwargs.items():
                s = v.split(" -> ")
                if len(s) > 1:
                    cols.append(f"{k} {s[0]}")
                    foreign.append(f"FOREIGN KEY ({k}) REFERENCES {s[1]}")
                    continue
                elif k.startswith("check_"):
                    check.append(f"CONSTRAINT {k} CHECK ({v})")
                    continue
                cols.append(f"{k} {v}")
            self.exec(f"CREATE TABLE IF NOT EXISTS {self().name} ({
                ", ".join(cols + foreign + check)
            })", fetch=None)
        def create(self, **kwargs: Any) -> None:
            """Inserts a row with the given `kwargs`."""
            k, v = zip(*kwargs.items())
            try: self.exec(
                    f"INSERT INTO {self().name} ({", ".join(k)}) VALUES ({", ".join(["?"]*len(kwargs))})",
                    *v, fetch=None
                )
            except sql.IntegrityError as e:
                if len(e.args) > 0:
                    desc: str = e.args[0]
                    if desc.startswith("UNIQUE constraint failed"):
                        raise self.errors.create_conflict(*e.args) from e
                    if desc.startswith("FOREIGN KEY constraint failed"):
                        raise self.errors.create_foreign_constraint(*e.args) from e
                    raise self.errors.create_constraint(*e.args) from e
                    
                raise
        @overload
        def _get(self, fetch: fetch_one = "one") -> LiveQuery[Row | None]: ...
        @overload
        def _get(self, fetch: fetch_all | int) -> LiveQuery[list[Row]]: ...
        def _get(self, fetch: fetch_mode = "one") -> LiveQuery[fetch_result]:
            def func(q: str | None = None, *v: Any) -> Table.Utils.fetch_result:
                return self.exec(
                    f"SELECT * FROM {self().name}{self.where(q)}",
                    *v, fetch=fetch
                )
            return func
        def _any(self, q: str | None = None, *v: Any) -> bool:
            return self._get(fetch="one")(q, *v) is not None
        def _set(self, set: kwargs_t) -> LiveQuery[None]:
            def func(q: str | None = None, *v: Any) -> None:
                self.exec(
                    f"UPDATE {self().name} SET {", ".join(f"{key} = ?" for key in set.keys())}{self.where(q)}",
                    *set.values(), *v, fetch=None
                )
            return func
        @overload
        def _delete(self, hard: Literal[True]) -> LiveQuery[None]: ...
        @overload
        def _delete(self, hard: Literal[False], arch: str | None = None) -> LiveQuery[None]: ...
        def _delete(self, hard: bool = False, arch: str | None = None) -> LiveQuery[None]:
            def func(q: str | None = None, *v: Any) -> None:
                nonlocal arch
                if arch is None: arch = self.arch
                if hard:
                    query = f"DELETE FROM {self().name}{self.where(q)}"
                    args = ()
                else:
                    query = f"UPDATE {self().name} SET {arch} = ?{self.where(q)} AND {arch} IS NULL"
                    args = (now(),)
                r = self.exec(query, *args, *v, fetch=None)
                if r == 0:
                    raise self.errors.not_found
            return func
        @overload
        def get(self, args: kwargs_t, fetch: fetch_one = "one", q: str | None = None, *v: Any, arch: optdefault = None) -> Row | None: ...
        @overload
        def get(self, args: kwargs_t, fetch: fetch_all | int, q: str | None = None, *v: Any, arch: optdefault = None) -> list[Row]: ...
        def get(self, args: kwargs_t, fetch: fetch_mode = "one", q: str | None = None, *v: Any, arch: optdefault = None) -> fetch_result:
            """Selects rows and returns the results."""
            return self.assemble(self._get(fetch), args, q, *v, arch=arch)
        def any(self, args: kwargs_t, q: str | None = None, *v: Any, arch: optdefault = None) -> bool:
            """Returns `True` if selecting rows returns at least one result."""
            return self.assemble(self._any, args, q, *v, arch=arch)
        def set(self, args: kwargs_t, set: kwargs_t, q: str | None = None, *v: Any, arch: optdefault = None) -> None:
            """Updates rows according to `set`."""
            return self.assemble(self._set(set), args, q, *v, arch=arch)
        @overload
        def delete(self, args: kwargs_t, hard: Literal[True] = True, q: str | None = None, *v: Any) -> None:
            """Deletes rows."""
        @overload
        def delete(self, args: kwargs_t, hard: Literal[False] = False, q: str | None = None, *v: Any, arch: optdefault = None) -> None:
            """Archives rows."""
        def delete(self, args: kwargs_t, hard: bool = False, q: str | None = None, *v: Any, arch: optdefault = None) -> None:
            """Deletes or archives rows."""
            return self.assemble(self._delete(hard=hard), args, q, *v, arch=arch)
    name: str
    class ResourceNotFoundError(NoRowsAffectedError):
        """Raised whenever a query doesn't affect any rows because the target resource doesn't exist."""
    class ResourceConstraintError(NoRowsAffectedError):
        """Raised whenever a query doesn't affect any rows because it doesn't satisfy a constraint."""
    class ForeignConstraintError(ResourceConstraintError):
        """Raised whenever a query doesn't affect any rows because it doesn't satisfy a foreign key constraint."""
    class ResourceAlreadyExistsError(ResourceConstraintError):
        """Raised whenever a query doesn't affect any rows because the inserted row already exists."""
    def __init__(self, conn: Connector, errors: Errors | None = None) -> None:
        self.conn = conn
        if errors is None: errors = self.Errors(
            self.ResourceNotFoundError,
            self.ResourceAlreadyExistsError,
            self.ResourceConstraintError,
            self.ForeignConstraintError
        )
        self.utils = self.Utils(self, errors)
    def run[R](self, f: Callable[[Cursor], R]) -> R:
        """Returns the result of the function `f` while managing its passed `sqlite3.Cursor` object."""
        conn = self.conn.new()
        c = conn.cursor()
        try:
            result = f(c)
            conn.commit()
            return result
        except:
            conn.rollback()
            raise
        finally:
            c.close()
            conn.close()