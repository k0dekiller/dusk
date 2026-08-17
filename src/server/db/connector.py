import sqlite3 as sql

class Connector:
    def __init__(self, file: str) -> None:
        self.file = file
    def new(self) -> sql.Connection:
        conn = sql.connect(self.file)
        conn.row_factory = sql.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn