### ユニットテスト

import os
import sys
import pytest

# テスト用DBを一時ファイルに向ける
import tempfile

_tmpdir = tempfile.mkdtemp()
_db_path = os.path.join(_tmpdir, 'test_assets.db')

# DB_PATH をテスト用に差し替え
import app.db as db_module
db_module.DB_PATH = _db_path

from app.models import (
    add_asset, get_asset, list_assets, update_asset, delete_asset,
    lend_asset, return_asset, list_loans, VALID_STATUSES
)


@pytest.fixture(autouse=True)
def clean_db():
    """各テスト前後でDBを初期化する"""
    if os.path.exists(_db_path):
        os.remove(_db_path)
    db_module.init_db()
    yield
    if os.path.exists(_db_path):
        os.remove(_db_path)


# ---------- 機器 CRUD ----------

class TestAssetCRUD:
    def test_add_asset_basic(self):
        a = add_asset(name='ThinkPad X1', asset_type='PC', serial_number='SN-001', status='使用中')
        assert a.id is not None
        assert a.name == 'ThinkPad X1'
        assert a.status == '使用中'

    def test_add_asset_defaults(self):
        a = add_asset(name='マウス', asset_type='周辺機器')
        assert a.status == '保管中'
        assert a.serial_number is None

    def test_add_asset_invalid_status(self):
        with pytest.raises(ValueError):
            add_asset(name='X', asset_type='PC', status='不明')

    def test_get_asset_not_found(self):
        assert get_asset(9999) is None

    def test_list_assets_empty(self):
        assert list_assets() == []

    def test_list_assets_filter_status(self):
        add_asset('PC1', 'PC', status='使用中')
        add_asset('PC2', 'PC', status='保管中')
        result = list_assets(status='使用中')
        assert len(result) == 1
        assert result[0].name == 'PC1'

    def test_list_assets_keyword(self):
        add_asset('ThinkPad X1', 'PC')
        add_asset('Dell Monitor', 'モニター')
        result = list_assets(keyword='Think')
        assert len(result) == 1
        assert result[0].name == 'ThinkPad X1'

    def test_update_asset(self):
        a = add_asset('OldName', 'PC')
        updated = update_asset(a.id, name='NewName', status='修理中')
        assert updated.name == 'NewName'
        assert updated.status == '修理中'

    def test_update_asset_invalid_status(self):
        a = add_asset('PC', 'PC')
        with pytest.raises(ValueError):
            update_asset(a.id, status='存在しない')

    def test_delete_asset(self):
        a = add_asset('ToDelete', 'PC')
        assert delete_asset(a.id) is True
        assert get_asset(a.id) is None

    def test_delete_nonexistent(self):
        assert delete_asset(9999) is False


# ---------- 貸出・返却 ----------

class TestLoan:
    def test_lend_and_return(self):
        a = add_asset('ThinkPad', 'PC', status='保管中')
        loan = lend_asset(a.id, '田中 太郎', '2025-04-01')
        assert loan.borrower_name == '田中 太郎'
        assert loan.returned_at is None

        updated_asset = get_asset(a.id)
        assert updated_asset.status == '貸出中'

        returned = return_asset(a.id, '2025-04-10')
        assert returned.returned_at == '2025-04-10'

        updated_asset2 = get_asset(a.id)
        assert updated_asset2.status == '保管中'

    def test_lend_废弃_asset(self):
        a = add_asset('古いPC', 'PC', status='廃棄済み')
        with pytest.raises(ValueError):
            lend_asset(a.id, '田中', '2025-04-01')

    def test_return_without_loan(self):
        a = add_asset('PC', 'PC')
        with pytest.raises(ValueError):
            return_asset(a.id, '2025-04-01')

    def test_list_loans(self):
        a = add_asset('PC', 'PC')
        lend_asset(a.id, '山田', '2025-03-01')
        return_asset(a.id, '2025-03-10')
        lend_asset(a.id, '佐藤', '2025-04-01')

        loans = list_loans(asset_id=a.id)
        assert len(loans) == 2

        active = list_loans(asset_id=a.id, active_only=True)
        assert len(active) == 1
        assert active[0].borrower_name == '佐藤'
