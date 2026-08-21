from ..utils import *
from .imports import *

class NoConnectionException(Exception):
    pass
class NoRowsAffectedError(Exception):
    pass

class Table:
    class Errors:
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
            return f" WHERE {cond}" if cond is not None else ""
        def sv[R](
                self,
                func: LiveQuery[R],
                sv: tuple[str, Any], q: str | None = None, *v: Any,
                arch: optdefault = None
            ) -> R:
            if isinstance(arch, bool): arch = f"{"!" if arch else ""}{self.arch}"
            if isinstance(arch, str) and arch.startswith("!"):
                arch = arch[1:]
                archinv = True
            else: archinv = False
            return func(
                f"{sv[0]} = ?"
                + (f" AND {arch} IS {" NOT " if archinv else ""}NULL" if arch is not None else "")
                + (f" {q}" if q is not None else ""),
                sv[1], *v
            )
        @overload
        def exec(self, query: str, *v: Any, fetch: Literal["one"]) -> Row | None: ...
        @overload
        def exec(self, query: str, *v: Any, fetch: Literal["all"] | int) -> list[Row]: ...
        @overload
        def exec(self, query: str, *v: Any, fetch: None = None) -> int: ...
        def exec(self, query: str, *v: Any, fetch: optfetch_mode = None) -> optfetch_result:
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
        def get(self, fetch: fetch_one = "one") -> LiveQuery[Row | None]: ...
        @overload
        def get(self, fetch: fetch_all | int) -> LiveQuery[list[Row]]: ...
        def get(self, fetch: fetch_mode = "one") -> LiveQuery[fetch_result]:
            def func(q: str | None = None, *v: Any) -> Table.Utils.fetch_result:
                return self.exec(
                    f"SELECT * FROM {self().name}{self.where(q)}",
                    *v, fetch=fetch
                )
            return func
        def any(self, q: str | None = None, *v: Any) -> bool:
            return self.get(fetch="one")(q, *v) is not None
        def set(self, set: dict[str, Any]) -> LiveQuery[None]:
            def func(q: str | None = None, *v: Any) -> None:
                self.exec(
                    f"UPDATE {self().name} SET {", ".join(f"{key} = ?" for key in set.keys())}{self.where(q)}",
                    *set.values(), *v, fetch=None
                )
            return func
        @overload
        def delete(self, hard: Literal[True]) -> LiveQuery[None]: ...
        @overload
        def delete(self, hard: Literal[False], arch: str | None = None) -> LiveQuery[None]: ...
        def delete(self, hard: bool = False, arch: str | None = None) -> LiveQuery[None]:
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
        def get_sv(self, sv: tuple[str, Any], fetch: fetch_one = "one", q: str | None = None, *v: Any, arch: optdefault = None) -> Row | None: ...
        @overload
        def get_sv(self, sv: tuple[str, Any], fetch: fetch_all | int, q: str | None = None, *v: Any, arch: optdefault = None) -> list[Row]: ...
        def get_sv(self, sv: tuple[str, Any], fetch: fetch_mode = "one", q: str | None = None, *v: Any, arch: optdefault = None) -> fetch_result:
            return self.sv(self.get(fetch), sv, q, *v, arch=arch)
        def any_sv(self, sv: tuple[str, Any], q: str | None = None, *v: Any, arch: optdefault = None) -> bool:
            return self.sv(self.any, sv, q, *v, arch=arch)
        def delete_sv(self, sv: tuple[str, Any], hard: bool = False, q: str | None = None, *v: Any, arch: optdefault = None) -> None:
            return self.sv(self.delete(hard=hard), sv, q, *v, arch=arch)
        def set_sv(self, sv: tuple[str, Any], set: dict[str, Any], q: str | None = None, *v: Any, arch: optdefault = None) -> None:
            return self.sv(self.set(set), sv, q, *v, arch=arch)
    name: str
    class ResourceNotFoundError(NoRowsAffectedError):
        pass
    class ResourceConstraintError(NoRowsAffectedError):
        pass
    class ForeignConstraintError(ResourceConstraintError):
        pass
    class ResourceAlreadyExistsError(ResourceConstraintError):
        pass
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
        conn = self.conn.new()
        c = conn.cursor()
        try:
            result = f(c)
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise
        finally:
            c.close()
            conn.close()