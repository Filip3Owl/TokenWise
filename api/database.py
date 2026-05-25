"""
Camada de persistência SQLite para tokens de API por cliente.

Os tokens são armazenados como hashes SHA-256 — o texto é retornado apenas uma vez
no momento da criação e nunca persistido. Apenas os primeiros 8 caracteres (token_prefix)
são armazenados para fins de exibição nas respostas de listagem/consulta.

Usa stdlib sqlite3 e hashlib — sem dependências adicionais necessárias.
O arquivo de banco de dados fica na raiz do projeto (tokenwise.db).
"""

import hashlib
import os
import secrets
import sqlite3
from pathlib import Path

# A variável TOKENWISE_DB_PATH permite ao Docker apontar o banco para um diretório de volume montado
DB_PATH = Path(os.environ.get("TOKENWISE_DB_PATH", Path(__file__).parent.parent / "tokenwise.db"))

_PLAN_LIMITS = {"basic": 60, "pro": 300}


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def init_db() -> None:
    """Cria a tabela de clientes se não existir. Migra automaticamente esquemas antigos."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        # Se a tabela existir com o esquema antigo (sem coluna token_hash), dropa e recria
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
    """Retorna o registro com o token mascarado ao seu prefixo para exibição segura."""
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
    Insere um novo cliente e retorna o registro completo.
    O token em texto é incluído no retorno apenas aqui — nunca é armazenado.
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
    record["token"] = token  # expõe o texto uma única vez, apenas na criação
    return record


def get_client_by_token(token: str) -> dict | None:
    """Aplica hash no token e retorna o registro ativo correspondente, ou None."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM clients WHERE token_hash = ? AND is_active = 1",
            (_hash_token(token),),
        ).fetchone()
    return _row_to_dict(row) if row else None


def list_clients() -> list[dict]:
    """Retorna todos os registros de clientes ordenados por data de criação (mais recente primeiro)."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM clients ORDER BY created_at DESC"
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def update_client(token: str, plan: str | None = None, rate_limit: int | None = None) -> dict | None:
    """
    Atualiza plan e/ou rate_limit de um cliente identificado pelo token em texto.
    Se apenas o plan for alterado e rate_limit não for informado, redefine rate_limit para o padrão do plano.
    Retorna o registro atualizado, ou None se o token não for encontrado.
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
    """Soft-delete de um cliente marcando-o como inativo. Retorna True se uma linha foi atualizada."""
    with sqlite3.connect(DB_PATH) as conn:
        result = conn.execute(
            "UPDATE clients SET is_active = 0 WHERE token_hash = ? AND is_active = 1",
            (_hash_token(token),),
        )
    return result.rowcount > 0
