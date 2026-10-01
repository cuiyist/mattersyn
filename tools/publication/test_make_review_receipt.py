"""Tests for make_review_receipt.py using a throwaway Git repository (synthetic files only)."""
import hashlib, subprocess, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_review_receipt as mrr


def git(root, *args):
    subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True)


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory(); r = self.root = Path(self.t.name)
        git(r, 'init', '-q'); git(r, 'config', 'user.email', 'test@example.invalid'); git(r, 'config', 'user.name', 'test')
        (r / 'publication').mkdir()
        for name, text in {'keep.md': 'keep', 'change.md': 'old', 'remove.md': 'gone',
                           'publication/project-allowlist.json': '{}', 'publication/build-inputs.json': '{}'}.items():
            (r / name).write_text(text)
        git(r, 'add', '-A'); git(r, 'commit', '-qm', 'base')
    def tearDown(self): self.t.cleanup()

    def test_rows_bind_exact_changes(self):
        r = self.root
        (r / 'change.md').write_text('new'); (r / 'add.md').write_text('added'); (r / 'remove.md').unlink()
        (r / 'publication/build-inputs.json').write_text('{"generated": true}')
        git(r, 'add', '-A')
        rows = {x['path']: x for x in mrr.build_receipt(r, 'reviewer-x', at='2026-10-01T00:00:00+00:00')['files']}
        self.assertEqual(set(rows), {'change.md', 'add.md', 'remove.md'}, 'controls and unchanged files are excluded')
        self.assertEqual(rows['change.md']['before_sha256'], hashlib.sha256(b'old').hexdigest())
        self.assertEqual(rows['change.md']['sha256'], hashlib.sha256(b'new').hexdigest())
        self.assertEqual(rows['change.md']['bytes'], 3)
        self.assertIsNone(rows['add.md']['before_sha256'])
        self.assertEqual(rows['remove.md']['decision'], 'delete')
        self.assertEqual(rows['remove.md']['before_sha256'], hashlib.sha256(b'gone').hexdigest())
        self.assertTrue(all(x['review_status'] == 'approved' and x['reviewer'] == 'reviewer-x' for x in rows.values()))

    def test_nothing_staged_refused(self):
        with self.assertRaises(SystemExit): mrr.build_receipt(self.root, 'reviewer-x')

    def test_reviewer_required(self):
        (self.root / 'change.md').write_text('new'); git(self.root, 'add', '-A')
        with self.assertRaises(SystemExit): mrr.build_receipt(self.root, ' ')


if __name__ == '__main__':
    unittest.main()
