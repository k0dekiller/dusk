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
                create_conflict: type[Exception] | None = None,
                create_constraint: type[Exception] | None = None
            ) -> None:
            self.not_found = not_found
            self.conflict = conflict
            self.constraint = constraint
            self.create_conflict = create_conflict if create_conflict is not None else conflict
            self.create_constraint = create_constraint if create_constraint is not None else constraint
    class Utils:
        type optdefault = str | bool | None
        type LiveQuery[R] = Callable[Concatenate[str, Any, ...], R]
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
        def exec(self, query: str, *v: Any, fetch: None) -> int: ...
        def exec(self, query: str, *v: Any, fetch: Literal["one", "all"] | int | None = None) -> list[Row] | Row | int | None:
            @self().run
            def op(c: Cursor) -> list[Row] | Row | int | None:
                c.execute(query, v)
                match fetch:
                    case "one": return c.fetchone()
                    case "all": return c.fetchall()
                    case None: return c.rowcount
                    case _: return c.fetchmany()
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
                        raise self.errors.create_conflict from e
                    raise self.errors.create_constraint(e.args) from e
                    
                raise
        def get(self, q: str | None = None, *v: Any) -> Row | None:
            return self.exec(
                f"SELECT * FROM {self().name}{self.where(q)}",
                *v, fetch="one"
            )
        def any(self, q: str | None = None, *v: Any) -> bool:
            return self.get(q, *v) is not None
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
        def get_sv(self, sv: tuple[str, Any], q: str | None = None, *v: Any, arch: optdefault = None) -> Row | None:
            return self.sv(self.get, sv, q, *v, arch=arch)
        def any_sv(self, sv: tuple[str, Any], q: str | None = None, *v: Any, arch: optdefault = None) -> bool:
            return self.sv(self.any, sv, q, *v, arch=arch)
        def delete_sv(self, sv: tuple[str, Any], hard: bool = False, q: str | None = None, *v: Any, arch: optdefault = None) -> None:
            return self.sv(self.delete(hard=hard), sv, q, *v, arch=arch)
        def set_sv(self, sv: tuple[str, Any], set: dict[str, Any], q: str | None = None, *v: Any, arch: optdefault = None) -> None:
            return self.sv(self.set(set), sv, q, *v, arch=arch)
    name: str
    class ResourceNotFoundError(NoRowsAffectedError):
        pass
    class ResourceAlreadyExistsError(NoRowsAffectedError):
        pass
    class ResourceConstraintError(NoRowsAffectedError):
        pass
    def __init__(self, conn: Connector, errors: Errors | None = None) -> None:
        self.conn = conn
        if errors is None: errors = self.Errors(
            self.ResourceNotFoundError,
            self.ResourceAlreadyExistsError,
            self.ResourceConstraintError
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