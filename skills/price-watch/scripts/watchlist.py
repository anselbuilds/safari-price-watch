#!/usr/bin/env python3
"""Local registry only; never controls Safari, schedules jobs or sends alerts."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit, parse_qsl
from zoneinfo import ZoneInfo

def default_db():
    override = os.environ.get('PRICE_WATCH_DB')
    if override:
        return Path(override).expanduser()
    skill_dir = Path(__file__).resolve().parent.parent
    if skill_dir.parent.name == 'skills' and skill_dir.parent.parent.name == '.agents':
        return skill_dir.parent.parent.parent / 'runtime/price-watch/watchlist.sqlite3'
    # Shared/global installs must not write beside the installed skill or into /Users.
    if sys.platform == 'darwin':
        return Path.home() / 'Library/Application Support/price-watch/watchlist.sqlite3'
    return Path(os.environ.get('XDG_STATE_HOME') or Path.home() / '.local/state') / 'price-watch/watchlist.sqlite3'

DEFAULT_DB = default_db()

def now():
    return datetime.now(timezone.utc).isoformat()

def require(ok, message):
    if not ok:
        raise ValueError(message)

def timestamp(value):
    require(isinstance(value, str), 'Timestamp must be an ISO 8601 string')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(parsed.tzinfo is not None, 'Timestamp requires timezone')
    return parsed

def money(value):
    require(isinstance(value, str), 'Money must be a decimal string')
    number = Decimal(value)
    require(number.is_finite() and number >= 0, 'Money must be finite and nonnegative')
    return format(number, 'f')

def validate(c):
    fields = {'url','title','variant','seller','condition','quantity','region','currency',
              'target','operator','price_basis','stock_rule','schedule','timezone','expires_at','baseline','purpose'}
    require(isinstance(c, dict) and set(c) == fields, 'Contract fields must match registry.md')
    for key in fields - {'quantity','expires_at','baseline'}:
        require(isinstance(c[key], str) and bool(c[key].strip()), f'{key} must be nonempty text')
    u = urlsplit(c['url'])
    require(u.scheme == 'https' and u.hostname and not u.username and not u.password,
            'Use a public HTTPS product URL without credentials')
    require(not any(re.search(r'token|secret|password|session|auth|signature', k, re.I)
                    for k, _ in parse_qsl(u.query)), 'Remove credential/session query parameters')
    require(type(c['quantity']) is int and c['quantity'] > 0, 'quantity must be a positive integer')
    require(bool(re.fullmatch('[A-Z]{3}', c['currency'])), 'Use a three-letter currency code')
    c['target'] = money(c['target'])
    require(c['operator'] in ('lt','lte'), 'operator must be lt or lte')
    require(c['price_basis'] in ('listed','all_in'), 'price_basis must be listed or all_in')
    require(c['stock_rule'] in ('in_stock','any'), 'stock_rule must be in_stock or any')
    ZoneInfo(c['timezone'])
    if c['expires_at'] is not None:
        timestamp(c['expires_at'])
    b = c['baseline']
    require(isinstance(b, dict) and set(b) == {'price','observed_at','stock','evidence'}, 'Invalid baseline fields')
    b['price'] = money(b['price'])
    require(timestamp(b['observed_at']) <= datetime.now(timezone.utc), 'Baseline cannot be in the future')
    require(b['stock'] in ('in_stock','out_of_stock','unknown'), 'Invalid stock state')
    require(isinstance(b['evidence'], str) and bool(b['evidence'].strip()), 'Baseline requires observed evidence')
    return c

def identity(c):
    return hashlib.sha256(json.dumps([c[k] for k in
        ('url','variant','seller','condition','quantity','region')], ensure_ascii=False).encode()).hexdigest()

def connect(path):
    path = Path(path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    db = sqlite3.connect(path)
    os.chmod(path, 0o600)
    db.execute('PRAGMA busy_timeout=5000')
    db.executescript('''
      CREATE TABLE IF NOT EXISTS watches(id TEXT PRIMARY KEY, identity TEXT NOT NULL,
        status TEXT NOT NULL, contract TEXT NOT NULL, native_evidence TEXT, verified_at TEXT,
        delivery_evidence TEXT, delivery_verified_at TEXT, updated_at TEXT NOT NULL);
      CREATE UNIQUE INDEX IF NOT EXISTS one_live_watch ON watches(identity) WHERE status != 'stopped';
      CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY, watch_id TEXT NOT NULL,
        at TEXT NOT NULL, action TEXT NOT NULL, payload TEXT NOT NULL);
    ''')
    db.row_factory = sqlite3.Row
    return db

def get(db, watch_id):
    row = db.execute('SELECT * FROM watches WHERE id=?', (watch_id,)).fetchone()
    require(row is not None, 'Unknown watch id')
    out = dict(row)
    out['contract'] = json.loads(out['contract'])
    expiry = out['contract']['expires_at']
    out['expiry_due'] = bool(expiry and timestamp(expiry) <= datetime.now(timezone.utc) and out['status'] != 'stopped')
    return out

def event(db, watch_id, action, payload):
    db.execute('INSERT INTO events(watch_id,at,action,payload) VALUES(?,?,?,?)',
               (watch_id, now(), action, json.dumps(payload, ensure_ascii=False)))

def prompt(c):
    op = '低於' if c['operator'] == 'lt' else '不高於'
    basis = '頁面一般標價（不含未列明運費）' if c['price_basis'] == 'listed' else '包含必要運費、稅費的總價'
    stock = '且有現貨可購買' if c['stock_rule'] == 'in_stock' else '（庫存不作限制）'
    return (f"只監控此頁的 {c['title']}，規格 {c['variant']}，賣家 {c['seller']}，"
            f"{c['condition']}，數量 {c['quantity']}，地區 {c['region']}。"
            f"當{basis}{op} {c['currency']} {c['target']} {stock}才通知。"
            '不要將其他容量、其他賣家、分期每期金額、會員限定價、回饋或未確認折價券當成價格。'
            '無法確認規格、幣別或必要費用時不要判定達標；沒有符合條件的變動時不要通知。')

def handoff(watch):
    c = watch['contract']
    action = {'draft': 'setup', 'needs_attention': 'edit', 'active': 'inspect',
              'stop_pending': 'stop', 'stopped': 'none'}[watch['status']]
    steps = {
        'setup': ['在 Safari 開啟商品網址，Page Menu → Notify Me。',
                  '貼上 native_condition；用 Edit 設定頻率與時間，再儲存。',
                  '重新打開設定核對條件、頻率與時間，回報結果。'],
        'edit': ['開啟原商品頁的既有 Notify Me → Edit；若找不到，先確認原任務狀態。',
                 '改為 native_condition 及指定頻率／時間，儲存後重新打開核對。'],
        'inspect': ['這是本機最後記錄。只有需要核對即時狀態時，才開啟原頁 Notify Me → Edit。'],
        'stop': ['開啟原商品頁既有 Notify Me → Edit → Delete。',
                 '確認該頁已無監控，回報停止結果；關閉分頁不等於停止。'],
        'none': ['本機已記錄停止；此設定卡不會重新建立監控。']
    }
    return {'id': watch['id'], 'action': action, 'local_status': watch['status'],
            'last_verified_at': watch['verified_at'], 'url': c['url'],
            'native_condition': prompt(c), 'schedule': c['schedule'], 'timezone': c['timezone'],
            'expires_at': c['expires_at'], 'expiry_due': watch['expiry_due'],
            'steps': steps[action], 'native_action_performed': False,
            'notes': ['此卡不操作 Safari、不建立排程、不改變本機狀態。',
                      '排程時區以 Mac／Safari 實際設定為準；與指定時區不同時先換算。',
                      '到期日僅是本機提醒，未確認 Safari 支援前不會自動停止。',
                      '可回報人工核對結果，證據須標明 user-confirmed；不能冒充 agent 親自觀察。']}

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db', type=Path, default=DEFAULT_DB)
    subs = p.add_subparsers(dest='cmd', required=True)
    subs.add_parser('list')
    for name in ('show','prompt','handoff','request-stop'):
        subs.add_parser(name).add_argument('id')
    for name in ('add','revise'):
        s = subs.add_parser(name); s.add_argument('id'); s.add_argument('--file', required=True)
    s = subs.add_parser('record-native'); s.add_argument('id')
    s.add_argument('--status', choices=('active','needs_attention','stopped'), required=True)
    s.add_argument('--evidence', required=True)
    s = subs.add_parser('record-delivery'); s.add_argument('id'); s.add_argument('--evidence', required=True)
    a = p.parse_args(argv)
    if hasattr(a, 'id'):
        require(bool(re.fullmatch('[a-z0-9][a-z0-9-]{0,63}', a.id)), 'Invalid watch id')
    if hasattr(a, 'evidence'):
        require(bool(a.evidence.strip()), 'Observed evidence cannot be blank')
    c = None
    if a.cmd in ('add','revise'):
        c = validate(json.loads(sys.stdin.read() if a.file == '-' else Path(a.file).read_text()))
    db = connect(a.db)
    with db:
        db.execute('BEGIN IMMEDIATE')
        if a.cmd == 'list':
            result = [get(db, r[0]) for r in db.execute('SELECT id FROM watches ORDER BY id')]
        elif a.cmd == 'add':
            db.execute('INSERT INTO watches(id,identity,status,contract,updated_at) VALUES(?,?,?,?,?)',
                       (a.id, identity(c), 'draft', json.dumps(c, ensure_ascii=False), now()))
            event(db, a.id, 'add', c); result = get(db, a.id)
        else:
            old = get(db, a.id)
            if a.cmd == 'show':
                result = old
                result['events'] = [dict(r) for r in db.execute('SELECT at,action,payload FROM events WHERE watch_id=? ORDER BY seq', (a.id,))]
            elif a.cmd == 'prompt':
                print(prompt(old['contract'])); return
            elif a.cmd == 'handoff':
                result = handoff(old)
            elif a.cmd == 'revise':
                require(old['status'] not in ('stopped','stop_pending'), 'Stop must be resolved before revision')
                db.execute("UPDATE watches SET identity=?,contract=?,status='needs_attention',native_evidence=NULL,"
                           'verified_at=NULL,delivery_evidence=NULL,delivery_verified_at=NULL,updated_at=? WHERE id=?',
                           (identity(c), json.dumps(c, ensure_ascii=False), now(), a.id))
                event(db, a.id, 'revise', {'before': old['contract'], 'after': c}); result = get(db, a.id)
            elif a.cmd == 'request-stop':
                require(old['status'] != 'stopped', 'Already recorded as stopped')
                db.execute("UPDATE watches SET status='stop_pending',updated_at=? WHERE id=?", (now(), a.id))
                event(db, a.id, 'request-stop', {'note': 'Safari stop is still required'}); result = get(db, a.id)
            elif a.cmd == 'record-native':
                require(old['status'] != 'stopped', 'Stopped records are immutable; create a new watch')
                if a.status == 'active':
                    require(old['status'] != 'stop_pending' and not old['expiry_due'], 'Cannot activate pending-stop or expired watch')
                if a.status == 'stopped':
                    require(old['status'] == 'stop_pending', 'Call request-stop first')
                if old['status'] == 'stop_pending':
                    require(a.status == 'stopped', 'Keep stop_pending until Safari stop is verified')
                db.execute('UPDATE watches SET status=?,native_evidence=?,verified_at=?,updated_at=? WHERE id=?',
                           (a.status, a.evidence, now(), now(), a.id))
                event(db, a.id, 'record-native', {'status': a.status, 'evidence': a.evidence}); result = get(db, a.id)
            elif a.cmd == 'record-delivery':
                require(old['status'] == 'active', 'Native setup must be verified before delivery verification')
                db.execute('UPDATE watches SET delivery_evidence=?,delivery_verified_at=?,updated_at=? WHERE id=?',
                           (a.evidence, now(), now(), a.id))
                event(db, a.id, 'record-delivery', {'evidence': a.evidence}); result = get(db, a.id)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, OSError, sqlite3.Error, InvalidOperation) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        sys.exit(2)
