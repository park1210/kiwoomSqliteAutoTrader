import sqlite3
from pathlib import Path

from config import DB_PATH, DATA_DIR


def get_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    schema_path = Path("app/database/schema.sql")

    if not schema_path.exists():
        raise FileNotFoundError(f"schema.sql 파일을 찾을 수 없습니다: {schema_path}")

    with get_connection() as conn:
        with open(schema_path, "r", encoding="utf-8") as f:
            conn.executescript(f.read())

        conn.commit()

    print(f"[DB] SQLite DB 초기화 완료: {DB_PATH}")