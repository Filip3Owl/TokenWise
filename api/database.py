"""
SQLite persistence layer for per-client API tokens.

Tokens are stored as SHA-256 hashes — the plaintext is returned only once at
creation time and never persisted. Only the first 8 characters (token_prefix)
are stored for display purposes in list/get responses.

Uses stdlib sqlite3 and hashlib — no additional dependencies required.
The DB file lives next to the project root (tokenwise.db).
"""

import hashlib
import os
import secrets
import sqlite3
from pathlib import Path

# TOKENWISE_DB_PATH env var allows Docker to point the DB to a mounted volume directory
DB_PATH = Path(os.environ.get("TOKENWISE_DB_PATH", Path(__file__).parent.parent / "tokenwise.db"))

_PLAN_LIMITS = {"basic": 60, "pro": 300}


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def init_db() -> None:
    """Create the clients table if it does not exist. Auto-migrates old schema."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        # If the table exists with the old schema (no token_hash column), drop and recreate
        columns = {row[1] for row in conn.execute("PRAGMA table_info(clients)")}
        if columns and "token_hash" not in columns:
            conn.execute("DROP TABLE clients")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                name         TEXT    NOT NULL,
                token_hash   TEXT    UNIQUE NOT NULL,
                token_prefix TEXT    NOT NULL,
                plan         TEXT    NOT NULL DEFAULT 'basic',
                rate_limit   INTEGER NOT NULL DEFAULT 60,
                is_active    INTEGER NOT NULL DEFAULT 1,
                created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        """)


def _row_to_dict(row: sqlite3.Row) -> dict:
    """Returns the record with the token masked to its prefix for safe display."""
    return {
        "id": row["id"],
        "name": row["name"],
        "token": row["token_prefix"] + "...",
        "plan": row["plan"],
        "rate_limit": row["rate_limit"],
        "is_active": bool(row["is_active"]),
        "created_at": row["created_at"],
    }


def create_client(name: str, plan: str = "basic", rate_limit: int | None = None) -> dict:
    """
    Insert a new client and return the full record.
    The plaintext token is included in the return value only here — it is never stored.
    """
    if plan not in _PLAN_LIMITS:
        raise ValueError(f"Unknown plan '{plan}'. Valid plans: {list(_PLAN_LIMITS)}")
    effective_limit = rate_limit if rate_limit is not None else _PLAN_LIMITS[plan]
    token = secrets.token_urlsafe(32)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO clients (name, token_hash, token_prefix, plan, rate_limit) VALUES (?, ?, ?, ?, ?)",
            (name, _hash_token(token), token[:8], plan, effective_limit),
        )
    record = get_client_by_token(token)
    record["token"] = token  # expose plaintext once, at creation only
    return record


def get_client_by_token(token: str) -> dict | None:
    """Hash the token and return the matching active client record, or None."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM clients WHERE token_hash = ? AND is_active = 1",
            (_hash_token(token),),
        ).fetchone()
    return _row_to_dict(row) if row else None


def list_clients() -> list[dict]:
    """Return all client records ordered by creation date (newest first)."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM clients ORDER BY created_at DESC"
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def update_client(token: str, plan: str | None = None, rate_limit: int | None = None) -> dict | None:
    """
    Update plan and/or rate_limit for a client identified by plaintext token.
    If only plan is changed and rate_limit is not given, resets rate_limit to the plan default.
    Returns the updated record, or None if the token was not found.
    """
    parts, values = [], []
    if plan is not None:
        if plan not in _PLAN_LIMITS:
            raise ValueError(f"Unknown plan '{plan}'. Valid plans: {list(_PLAN_LIMITS)}")
        parts.append("plan = ?")
        values.append(plan)
        if rate_limit is None:
            parts.append("rate_limit = ?")
            values.append(_PLAN_LIMITS[plan])
    if rate_limit is not None:
        parts.append("rate_limit = ?")
        values.append(rate_limit)
    if not parts:
        return get_client_by_token(token)
    values.append(_hash_token(token))
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(f"UPDATE clients SET {', '.join(parts)} WHERE token_hash = ?", values)
    return get_client_by_token(token)


def revoke_client(token: str) -> bool:
    """Soft-delete a client by marking it inactive. Returns True if a row was updated."""
    with sqlite3.connect(DB_PATH) as conn:
        result = conn.execute(
            "UPDATE clients SET is_active = 0 WHERE token_hash = ? AND is_active = 1",
            (_hash_token(token),),
        )
    return result.rowcount > 0
