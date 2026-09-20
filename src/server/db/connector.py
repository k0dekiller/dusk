import sqlite3 as sql

class Connector:
    """The class that acts as an `sqlite3.Connection` factory."""
    def __init__(self, file: str) -> None:
        self.file = file
    def new(self) -> sql.Connection:
        """Returns a new initialized `sqlite3.Connection`."""
        conn = sql.connect(self.file)
        conn.row_factory = sql.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn