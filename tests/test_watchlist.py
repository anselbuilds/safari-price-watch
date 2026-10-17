"""Observable CLI/state tests. No Safari, network, or personal registry access."""
import copy
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/price-watch/scripts/watchlist.py'
FIXTURE = ROOT / 'skills/price-watch/examples/demo-contract.json'


class WatchlistTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='.test-price-watch-', dir=ROOT)
        self.root = Path(self.tmp.name)
        self.db = self.root / 'state/watchlist.sqlite3'
        self.contract = json.loads(FIXTURE.read_text())
        self.env = dict(os.environ, PRICE_WATCH_DB=str(self.root / 'unused.sqlite3'))

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args, contract=None, ok=True, db=True, script=SCRIPT, env=None):
        argv = [sys.executable, str(script)]
        if db:
            argv += ['--db', str(self.db)]
        argv += list(args)
        if contract is not None:
            argv += ['--file', '-']
        proc = subprocess.run(argv, input=json.dumps(contract) if contract else None,
                              text=True, capture_output=True, env=env or self.env)
        self.assertEqual(proc.returncode, 0 if ok else 2, proc.stderr)
        return json.loads(proc.stdout) if proc.returncode == 0 and args[0] != 'prompt' else proc

    def add(self, watch_id='demo', contract=None):
        return self.run_cli('add', watch_id, contract=contract or self.contract)

    def activate(self):
        return self.run_cli('record-native', 'demo', '--status', 'active', '--evidence',
                            'user-confirmed: synthetic settings checked; not actual Safari evidence')

    def test_add_remains_draft_and_delivery_unverified(self):
        row = self.add()
        self.assertEqual(row['status'], 'draft')
        self.assertIsNone(row['verified_at'])
        self.assertIsNone(row['delivery_verified_at'])

    def test_handoff_does_not_modify_watch_or_events(self):
        self.add()
        before = self.run_cli('show', 'demo')
        card = self.run_cli('handoff', 'demo')
        self.assertEqual(card['action'], 'setup')
        self.assertFalse(card['native_action_performed'])
        self.assertEqual(before, self.run_cli('show', 'demo'))

    def test_revise_keeps_old_conditions_and_clears_verifications(self):
        self.add(); self.activate()
        self.run_cli('record-delivery', 'demo', '--evidence', 'synthetic delivery record')
        newer = copy.deepcopy(self.contract); newer['target'] = '70'
        row = self.run_cli('revise', 'demo', contract=newer)
        self.assertEqual(row['status'], 'needs_attention')
        self.assertIsNone(row['verified_at']); self.assertIsNone(row['delivery_verified_at'])
        event = self.run_cli('show', 'demo')['events'][-1]
        payload = json.loads(event['payload'])
        self.assertEqual(payload['before']['target'], '80.00')
        self.assertEqual(payload['after']['target'], '70')

    def test_stop_requires_pending_and_is_not_canceled_by_activation(self):
        self.add(); self.activate()
        self.run_cli('record-native', 'demo', '--status', 'stopped', '--evidence', 'x', ok=False)
        self.assertEqual(self.run_cli('request-stop', 'demo')['status'], 'stop_pending')
        self.run_cli('record-native', 'demo', '--status', 'active', '--evidence', 'x', ok=False)
        self.run_cli('record-native', 'demo', '--status', 'needs_attention', '--evidence', 'x', ok=False)
        row = self.run_cli('record-native', 'demo', '--status', 'stopped', '--evidence', 'synthetic removal')
        self.assertEqual(row['status'], 'stopped')
        self.run_cli('revise', 'demo', contract=self.contract, ok=False)
        self.assertEqual(self.run_cli('handoff', 'demo')['action'], 'none')

    def test_duplicate_live_identity_rolls_back_without_event(self):
        self.add()
        self.run_cli('add', 'second', contract=self.contract, ok=False)
        self.assertEqual(len(self.run_cli('list')), 1)
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM events').fetchone()[0], 1)

    def test_new_id_can_reuse_stopped_identity(self):
        self.add(); self.run_cli('request-stop', 'demo')
        self.run_cli('record-native', 'demo', '--status', 'stopped', '--evidence', 'synthetic removal')
        self.assertEqual(self.add('second')['status'], 'draft')

    def test_delivery_requires_active_setup(self):
        self.add()
        self.run_cli('record-delivery', 'demo', '--evidence', 'synthetic receipt', ok=False)
        active = self.activate(); self.assertIsNone(active['delivery_verified_at'])
        self.assertIsNotNone(self.run_cli('record-delivery', 'demo', '--evidence', 'synthetic receipt')['delivery_verified_at'])

    def test_expiry_is_only_a_warning_and_prevents_activation(self):
        c = copy.deepcopy(self.contract); c['expires_at'] = '2001-01-01T00:00:00+00:00'
        row = self.add(contract=c)
        self.assertTrue(row['expiry_due']); self.assertEqual(row['status'], 'draft')
        self.run_cli('record-native', 'demo', '--status', 'active', '--evidence', 'x', ok=False)
        self.assertEqual(self.run_cli('show', 'demo')['status'], 'draft')

    def test_invalid_money_does_not_create_database(self):
        for value in ('NaN', 'Infinity', '-1', 80):
            with self.subTest(value=value):
                c = copy.deepcopy(self.contract); c['target'] = value
                self.run_cli('add', 'demo', contract=c, ok=False)
                self.assertFalse(self.db.exists())

    def test_invalid_identity_and_timezone_are_rejected(self):
        for key, value in [('quantity', True), ('timezone', 'Not/AZone'), ('currency', 'usd')]:
            c = copy.deepcopy(self.contract); c[key] = value
            self.run_cli('add', 'demo', contract=c, ok=False)
        self.run_cli('add', '../escape', contract=self.contract, ok=False)

    def test_credentials_and_session_urls_are_rejected(self):
        for url in ('http://example.com/item', 'https://name:pass@example.com/item',
                    'https://example.com/item?session=synthetic', 'https://example.com/item?token=synthetic'):
            c = copy.deepcopy(self.contract); c['url'] = url
            self.run_cli('add', 'demo', contract=c, ok=False)

    def test_future_and_timezone_free_baselines_are_rejected(self):
        for value in ('2999-01-01T00:00:00+00:00', '2020-01-01T00:00:00'):
            c = copy.deepcopy(self.contract); c['baseline']['observed_at'] = value
            self.run_cli('add', 'demo', contract=c, ok=False)

    def test_untrusted_text_is_data_not_shell_code(self):
        sentinel = self.root / 'should-not-exist'
        c = copy.deepcopy(self.contract); c['title'] = '$(touch ' + str(sentinel) + ')'
        row = self.add(contract=c)
        self.assertEqual(row['contract']['title'], c['title'])
        self.run_cli('prompt', 'demo')
        self.assertFalse(sentinel.exists())

    def test_blank_evidence_is_rejected(self):
        self.add()
        self.run_cli('record-native', 'demo', '--status', 'active', '--evidence', '  ', ok=False)

    def test_explicit_db_overrides_environment(self):
        self.add()
        self.assertTrue(self.db.exists())
        self.assertFalse(Path(self.env['PRICE_WATCH_DB']).exists())

    def test_environment_db_works(self):
        self.run_cli('list', db=False)
        self.assertTrue(Path(self.env['PRICE_WATCH_DB']).exists())
        self.assertFalse(self.db.exists())

    def test_global_install_defaults_outside_skill(self):
        # Mock Path.home in an isolated child; leave the real HOME unchanged.
        installed = self.root / 'home/.codex/skills/price-watch/scripts/watchlist.py'
        installed.parent.mkdir(parents=True); shutil.copyfile(SCRIPT, installed)
        env = dict(os.environ, XDG_STATE_HOME=str(self.root / 'state'))
        env.pop('PRICE_WATCH_DB', None)
        code = ('from pathlib import Path; from unittest.mock import patch; import runpy, sys; '
                'sys.argv=[sys.argv[1], "list"]; '
                'home=Path(sys.argv[0]).parents[4]; '
                'p=patch("pathlib.Path.home", return_value=home); p.start(); '
                'runpy.run_path(sys.argv[0], run_name="__main__")')
        proc = subprocess.run([sys.executable, '-c', code, str(installed)],
                              capture_output=True, text=True, env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        expected = self.root / ('home/Library/Application Support/price-watch/watchlist.sqlite3'
                                if sys.platform == 'darwin' else 'state/price-watch/watchlist.sqlite3')
        self.assertTrue(expected.exists())
        self.assertFalse(list(installed.parent.parent.rglob('*.sqlite3')))

    def test_private_database_permissions_on_posix(self):
        if os.name != 'posix':
            self.skipTest('POSIX mode bits only')
        self.add()
        self.assertEqual(self.db.stat().st_mode & 0o777, 0o600)


if __name__ == '__main__':
    unittest.main()
