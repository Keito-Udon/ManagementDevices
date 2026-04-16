### DB接続・初期化モジュール

import sqlite3
import os

# データベースファイルのパス
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'assets.db')

# DB_PATHとsqlite3を接続
def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    with conn:
        # テーブル作成（デバイス用、貸出用）
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS assets (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT    NOT NULL,
                asset_type    TEXT    NOT NULL,
                serial_number TEXT,
                status        TEXT    NOT NULL DEFAULT '保管中',
                location      TEXT,
                purchased_at  TEXT,
                notes         TEXT
            );

            CREATE TABLE IF NOT EXISTS loans (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id      INTEGER NOT NULL REFERENCES assets(id),
                borrower_name TEXT    NOT NULL,
                loaned_at     TEXT    NOT NULL,
                returned_at   TEXT
            );
        """)
    conn.close()


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'init':
        init_db()
        print("データベースを初期化しました。")
