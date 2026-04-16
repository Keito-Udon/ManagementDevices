### Web UI

import io
import os
from datetime import date
from flask import (Flask, render_template, request, redirect, url_for,
                   flash, send_file)

from .models import (
    add_asset, get_asset, list_assets, update_asset, delete_asset,
    lend_asset, return_asset, list_loans, export_csv, VALID_STATUSES
)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')


# デバイス一覧

@app.route('/')
def index():
    status = request.args.get('status', '')
    keyword = request.args.get('keyword', '')
    assets = list_assets(
        status=status if status else None,
        keyword=keyword if keyword else None,
    )
    return render_template('index.html',
                           assets=assets,
                           statuses=VALID_STATUSES,
                           selected_status=status,
                           keyword=keyword)


# デバイス登録

@app.route('/assets/new', methods=['GET', 'POST'])
def new_asset():
    if request.method == 'POST':
        try:
            add_asset(
                name=request.form['name'],
                asset_type=request.form['asset_type'],
                serial_number=request.form.get('serial_number') or None,
                status=request.form['status'],
                location=request.form.get('location') or None,
                purchased_at=request.form.get('purchased_at') or None,
                notes=request.form.get('notes') or None,
            )
            flash('機器を登録しました。', 'success')
            return redirect(url_for('index'))
        except ValueError as e:
            flash(str(e), 'danger')
    return render_template('asset_form.html', asset=None, statuses=VALID_STATUSES)


# デバイス詳細

@app.route('/assets/<int:asset_id>')
def asset_detail(asset_id):
    asset = get_asset(asset_id)
    if asset is None:
        flash('機器が見つかりません。', 'warning')
        return redirect(url_for('index'))
    loans = list_loans(asset_id=asset_id)
    return render_template('asset_detail.html', asset=asset, loans=loans)


# 編集

@app.route('/assets/<int:asset_id>/edit', methods=['GET', 'POST'])
def edit_asset(asset_id):
    asset = get_asset(asset_id)
    if asset is None:
        flash('機器が見つかりません。', 'warning')
        return redirect(url_for('index'))
    if request.method == 'POST':
        try:
            update_asset(
                asset_id,
                name=request.form['name'],
                asset_type=request.form['asset_type'],
                serial_number=request.form.get('serial_number') or None,
                status=request.form['status'],
                location=request.form.get('location') or None,
                purchased_at=request.form.get('purchased_at') or None,
                notes=request.form.get('notes') or None,
            )
            flash('機器情報を更新しました。', 'success')
            return redirect(url_for('asset_detail', asset_id=asset_id))
        except ValueError as e:
            flash(str(e), 'danger')
    return render_template('asset_form.html', asset=asset, statuses=VALID_STATUSES)


# 削除

@app.route('/assets/<int:asset_id>/delete', methods=['POST'])
def delete_asset_view(asset_id):
    delete_asset(asset_id)
    flash('機器を削除しました。', 'info')
    return redirect(url_for('index'))


# 貸出

@app.route('/assets/<int:asset_id>/lend', methods=['GET', 'POST'])
def lend_asset_view(asset_id):
    asset = get_asset(asset_id)
    if asset is None:
        flash('機器が見つかりません。', 'warning')
        return redirect(url_for('index'))
    if request.method == 'POST':
        try:
            lend_asset(
                asset_id=asset_id,
                borrower_name=request.form['borrower_name'],
                loaned_at=request.form['loaned_at'] or str(date.today()),
            )
            flash('貸出登録しました。', 'success')
            return redirect(url_for('asset_detail', asset_id=asset_id))
        except ValueError as e:
            flash(str(e), 'danger')
    return render_template('lend_form.html', asset=asset, today=str(date.today()))


# 返却

@app.route('/assets/<int:asset_id>/return', methods=['POST'])
def return_asset_view(asset_id):
    returned_at = request.form.get('returned_at') or str(date.today())
    try:
        return_asset(asset_id, returned_at)
        flash('返却登録しました。', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    return redirect(url_for('asset_detail', asset_id=asset_id))


# CSVエクスポート

@app.route('/export')
def export():
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
        tmp_path = tmp.name
    export_csv(tmp_path)
    return send_file(
        tmp_path,
        as_attachment=True,
        download_name=f'assets_{date.today()}.csv',
        mimetype='text/csv',
    )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
