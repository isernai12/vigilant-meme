from __future__ import annotations

import os
import time
from typing import Any

import libsql

from app import config


_conn: libsql.Connection | None = None


def get_conn() -> libsql.Connection:
    global _conn
    if _conn is None:
        os.makedirs(os.path.dirname(config.LIBSQL_LOCAL_PATH), exist_ok=True)
        _conn = libsql.connect(
            config.LIBSQL_LOCAL_PATH,
            sync_url=config.LIBSQL_URL,
            auth_token=config.LIBSQL_AUTH_TOKEN,
            sync_interval=60,
        )
    return _conn


def init_db() -> None:
    conn = get_conn()
    exec_write(
        """
        CREATE TABLE IF NOT EXISTS admins (
            telegram_id INTEGER PRIMARY KEY,
            is_active INTEGER DEFAULT 1,
            created_at INTEGER
        )
        """
    )
    exec_write(
        """
        CREATE TABLE IF NOT EXISTS admin_otps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            code_hash TEXT,
            expires_at INTEGER,
            attempts INTEGER DEFAULT 0,
            created_at INTEGER
        )
        """
    )
    exec_write(
        """
        CREATE TABLE IF NOT EXISTS admin_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            session_hash TEXT,
            expires_at INTEGER,
            created_at INTEGER
        )
        """
    )
    exec_write(
        """
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NULL,
            question TEXT,
            a TEXT,
            b TEXT,
            c TEXT,
            d TEXT,
            correct TEXT,
            explanation TEXT NULL,
            is_active INTEGER DEFAULT 1,
            created_at INTEGER
        )
        """
    )
    now = int(time.time())
    for telegram_id in config.ADMIN_TELEGRAM_IDS:
        exec_write(
            """
            INSERT OR IGNORE INTO admins (telegram_id, is_active, created_at)
            VALUES (?, 1, ?)
            """,
            (telegram_id, now),
        )
    try:
        conn.sync()
    except Exception:
        pass


def exec_read(query: str, params: tuple[Any, ...] | None = None) -> list[tuple[Any, ...]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params or ())
    rows = cur.fetchall()
    return rows


def exec_write(query: str, params: tuple[Any, ...] | None = None) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params or ())
    conn.commit()
    try:
        conn.sync()
    except Exception:
        pass

