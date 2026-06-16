import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path


def get_connection(db_path: str = "data/cmdb.db") -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_connection(db_path: str = "data/cmdb.db"):
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: str = "data/cmdb.db") -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    schema_path = Path(__file__).parent / "schema.sql"
    sql = schema_path.read_text(encoding="utf-8")

    conn = get_connection(db_path)
    try:
        # executescript commits automatically; we run it outside the WAL context
        conn.executescript(sql)
    finally:
        conn.close()
