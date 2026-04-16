### CLIエントリーポイント

import argparse
import sys
from datetime import date

from .models import (
    add_asset, get_asset, list_assets, update_asset, delete_asset,
    lend_asset, return_asset, list_loans, export_csv, VALID_STATUSES
)


def _print_assets(assets):
    if not assets:
        print("該当する機器はありません。")
        return
    fmt = "{:<4} {:<20} {:<10} {:<15} {:<8} {:<12} {}"
    print(fmt.format("ID", "機器名", "種別", "シリアル番号", "ステータス", "設置場所", "購入日"))
    print("-" * 90)
    for a in assets:
        print(fmt.format(
            a.id, a.name, a.asset_type, a.serial_number or '-',
            a.status, a.location or '-', a.purchased_at or '-'
        ))


def cmd_add(args):
    asset = add_asset(
        name=args.name,
        asset_type=args.type,
        serial_number=args.serial,
        status=args.status,
        location=args.location,
        purchased_at=args.purchased_at,
        notes=args.notes,
    )
    print(f"登録しました: [ID={asset.id}] {asset.name}")


def cmd_list(args):
    assets = list_assets(status=args.status, keyword=args.keyword)
    _print_assets(assets)


def cmd_show(args):
    asset = get_asset(args.id)
    if asset is None:
        print(f"ID {args.id} の機器が見つかりません。")
        sys.exit(1)
    print(f"ID          : {asset.id}")
    print(f"機器名      : {asset.name}")
    print(f"種別        : {asset.asset_type}")
    print(f"シリアル番号: {asset.serial_number or '-'}")
    print(f"ステータス  : {asset.status}")
    print(f"設置場所    : {asset.location or '-'}")
    print(f"購入日      : {asset.purchased_at or '-'}")
    print(f"備考        : {asset.notes or '-'}")

    loans = list_loans(asset_id=args.id)
    if loans:
        print("\n--- 貸出履歴 ---")
        for ln in loans:
            ret = ln.returned_at or "未返却"
            print(f"  {ln.loaned_at} ~ {ret}  {ln.borrower_name}")


def cmd_update(args):
    kwargs = {}
    if args.name:
        kwargs['name'] = args.name
    if args.type:
        kwargs['asset_type'] = args.type
    if args.serial:
        kwargs['serial_number'] = args.serial
    if args.status:
        kwargs['status'] = args.status
    if args.location:
        kwargs['location'] = args.location
    if args.notes:
        kwargs['notes'] = args.notes
    asset = update_asset(args.id, **kwargs)
    if asset is None:
        print(f"ID {args.id} の機器が見つかりません。")
        sys.exit(1)
    print(f"更新しました: [ID={asset.id}] {asset.name}  ステータス={asset.status}")


def cmd_delete(args):
    ok = delete_asset(args.id)
    if ok:
        print(f"ID {args.id} を削除しました。")
    else:
        print(f"ID {args.id} の機器が見つかりません。")
        sys.exit(1)


def cmd_lend(args):
    loaned_at = args.date or str(date.today())
    loan = lend_asset(args.id, args.to, loaned_at)
    print(f"貸出登録しました: [LoanID={loan.id}] ID={args.id} → {args.to}  ({loaned_at})")


def cmd_return(args):
    returned_at = args.date or str(date.today())
    loan = return_asset(args.id, returned_at)
    print(f"返却登録しました: [LoanID={loan.id}] ID={args.id}  返却日={returned_at}")


def cmd_export(args):
    export_csv(args.output)
    print(f"CSVをエクスポートしました: {args.output}")


def build_parser():
    parser = argparse.ArgumentParser(
        prog='asset-manager',
        description='資産台帳管理ツール CLI'
    )
    sub = parser.add_subparsers(dest='command', required=True)

    # add
    p_add = sub.add_parser('add', help='機器を登録する')
    p_add.add_argument('--name', required=True, help='機器名')
    p_add.add_argument('--type', required=True, help='種別 (PC, モニター, …)')
    p_add.add_argument('--serial', default=None, help='シリアル番号')
    p_add.add_argument('--status', default='保管中',
                       choices=VALID_STATUSES, help='初期ステータス')
    p_add.add_argument('--location', default=None, help='設置場所')
    p_add.add_argument('--purchased-at', default=None, dest='purchased_at', help='購入日 (YYYY-MM-DD)')
    p_add.add_argument('--notes', default=None, help='備考')

    # list
    p_list = sub.add_parser('list', help='機器一覧を表示する')
    p_list.add_argument('--status', default=None, choices=VALID_STATUSES, help='ステータスで絞り込み')
    p_list.add_argument('--keyword', default=None, help='キーワード検索')

    # show
    p_show = sub.add_parser('show', help='機器の詳細を表示する')
    p_show.add_argument('--id', required=True, type=int, help='機器ID')

    # update
    p_upd = sub.add_parser('update', help='機器情報を更新する')
    p_upd.add_argument('--id', required=True, type=int, help='機器ID')
    p_upd.add_argument('--name', default=None)
    p_upd.add_argument('--type', default=None)
    p_upd.add_argument('--serial', default=None)
    p_upd.add_argument('--status', default=None, choices=VALID_STATUSES)
    p_upd.add_argument('--location', default=None)
    p_upd.add_argument('--notes', default=None)

    # delete
    p_del = sub.add_parser('delete', help='機器を削除する')
    p_del.add_argument('--id', required=True, type=int, help='機器ID')

    # lend
    p_lend = sub.add_parser('lend', help='機器を貸し出す')
    p_lend.add_argument('--id', required=True, type=int, help='機器ID')
    p_lend.add_argument('--to', required=True, help='借用者名')
    p_lend.add_argument('--date', default=None, help='貸出日 (YYYY-MM-DD、省略時=今日)')

    # return
    p_ret = sub.add_parser('return', help='機器を返却する')
    p_ret.add_argument('--id', required=True, type=int, help='機器ID')
    p_ret.add_argument('--date', default=None, help='返却日 (YYYY-MM-DD、省略時=今日)')

    # export
    p_exp = sub.add_parser('export', help='CSVにエクスポートする')
    p_exp.add_argument('--output', default='assets_export.csv', help='出力ファイルパス')

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    dispatch = {
        'add': cmd_add,
        'list': cmd_list,
        'show': cmd_show,
        'update': cmd_update,
        'delete': cmd_delete,
        'lend': cmd_lend,
        'return': cmd_return,
        'export': cmd_export,
    }
    try:
        dispatch[args.command](args)
    except ValueError as e:
        print(f"エラー: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
