# pyright: reportUnusedImport=false
from ..utils import now, hash, over
from typing import Concatenate, Literal, Self, Any, overload
from collections.abc import Callable
from functools import wraps
from sqlite3 import Row, Cursor
import sqlite3 as sql
from .connector import Connector
import secrets