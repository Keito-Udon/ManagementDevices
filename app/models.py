### DBモデル定義 — ASSETS / LOANS テーブルのCRUD

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from .db import get_connection, init_db

VALID_STATUSES = ('使用中', '保管中', '貸出中', '修理中', '廃棄済み')


@dataclass
class Asset:
    id: Optional[int]
    name: str
    asset_type: str
    serial_number: Optional[str]
    status: str
    location: Optional[str]
    purchased_at: Optional[str]
    notes: Optional[str]


@dataclass
class Loan:
    id: Optional[int]
    asset_id: int
    borrower_name: str
    loaned_at: str
    returned_at: Optional[str]


# Asset CRUD
def add_asset(name: str, asset_type: str, serial_number: str = None,
              status: str = '保管中', location: str = None,
              purchased_at: str = None, notes: str = None) -> Asset:
    init_db()
    if status not in VALID_STATUSES:
        raise ValueError(f"無効なステータス: {status}")
    conn = get_connection()
    with conn:
        cur = conn.execute(
            """INSERT INTO assets (name, asset_type, serial_number, status,
               location, purchased_at, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (name, asset_type, serial_number, status, location, purchased_at, notes)
        )
        asset_id = cur.lastrowid
    conn.close()
    return get_asset(asset_id)


def get_asset(asset_id: int) -> Optional[Asset]:
    init_db()
    conn = get_connection()
    row = conn.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return Asset(**dict(row))


def list_assets(status: str = None, keyword: str = None) -> list[Asset]:
    init_db()
    query = "SELECT * FROM assets WHERE 1=1"
    params: list = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if keyword:
        query += " AND (name LIKE ? OR asset_type LIKE ? OR serial_number LIKE ? OR location LIKE ?)"
        like = f"%{keyword}%"
        params.extend([like, like, like, like])
    query += " ORDER BY id"
    conn = get_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [Asset(**dict(r)) for r in rows]


def update_asset(asset_id: int, **kwargs) -> Optional[Asset]:
    init_db()
    if 'status' in kwargs and kwargs['status'] not in VALID_STATUSES:
        raise ValueError(f"無効なステータス: {kwargs['status']}")
    allowed = {'name', 'asset_type', 'serial_number', 'status',
               'location', 'purchased_at', 'notes'}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return get_asset(asset_id)
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [asset_id]
    conn = get_connection()
    with conn:
        conn.execute(f"UPDATE assets SET {set_clause} WHERE id = ?", values)
    conn.close()
    return get_asset(asset_id)


def delete_asset(asset_id: int) -> bool:
    """物理削除（ローン履歴も一緒に消える）"""
    init_db()
    conn = get_connection()
    with conn:
        conn.execute("DELETE FROM loans WHERE asset_id = ?", (asset_id,))
        cur = conn.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
    conn.close()
    return cur.rowcount > 0


# ---------- Loan CRUD ----------

def lend_asset(asset_id: int, borrower_name: str, loaned_at: str) -> Loan:
    init_db()
    asset = get_asset(asset_id)
    if asset is None:
        raise ValueError(f"ID {asset_id} の機器が見つかりません")
    if asset.status == '廃棄済み':
        raise ValueError("廃棄済みの機器は貸し出せません")
    conn = get_connection()
    with conn:
        cur = conn.execute(
            "INSERT INTO loans (asset_id, borrower_name, loaned_at) VALUES (?, ?, ?)",
            (asset_id, borrower_name, loaned_at)
        )
        loan_id = cur.lastrowid
        conn.execute("UPDATE assets SET status = '貸出中' WHERE id = ?", (asset_id,))
    conn.close()
    return get_loan(loan_id)


def return_asset(asset_id: int, returned_at: str) -> Optional[Loan]:
    init_db()
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM loans WHERE asset_id = ? AND returned_at IS NULL ORDER BY id DESC LIMIT 1",
        (asset_id,)
    ).fetchone()
    if row is None:
        conn.close()
        raise ValueError(f"ID {asset_id} の機器に未返却の貸出記録がありません")
    with conn:
        conn.execute("UPDATE loans SET returned_at = ? WHERE id = ?", (returned_at, row['id']))
        conn.execute("UPDATE assets SET status = '保管中' WHERE id = ?", (asset_id,))
    loan_id = row['id']
    conn.close()
    return get_loan(loan_id)


def get_loan(loan_id: int) -> Optional[Loan]:
    init_db()
    conn = get_connection()
    row = conn.execute("SELECT * FROM loans WHERE id = ?", (loan_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return Loan(**dict(row))


def list_loans(asset_id: int = None, active_only: bool = False) -> list[Loan]:
    init_db()
    query = "SELECT * FROM loans WHERE 1=1"
    params: list = []
    if asset_id:
        query += " AND asset_id = ?"
        params.append(asset_id)
    if active_only:
        query += " AND returned_at IS NULL"
    query += " ORDER BY id DESC"
    conn = get_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [Loan(**dict(r)) for r in rows]


# ---------- CSV エクスポート ----------

def export_csv(filepath: str):
    import csv
    assets = list_assets()
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', '機器名', '種別', 'シリアル番号',
                         'ステータス', '設置場所', '購入日', '備考'])
        for a in assets:
            writer.writerow([a.id, a.name, a.asset_type, a.serial_number or '',
                             a.status, a.location or '', a.purchased_at or '', a.notes or ''])
