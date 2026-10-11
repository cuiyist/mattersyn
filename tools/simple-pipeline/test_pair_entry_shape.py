"""Malformed pass entries cannot become evidence or block later papers."""
import argparse
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import mattersyn_simple as runtime


class PairShapeTest(unittest.TestCase):
    def check_invalid(self, value):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            work, out = root / 'work', root / 'pairs'
            work.mkdir(); out.mkdir()
            good = {'doi': '10.9999/synthetic', 'pairs': []}
            for name in ('paper', 'later'):
                (work / f'{name}.text.txt').write_text('[page 1]\nSynthetic fixture only.\n', encoding='utf8')
                for letter in ('A', 'B'):
                    doc = dict(good)
                    if name == 'paper' and letter == 'B':
                        doc['pairs'] = [value]
                    (work / f'{name}.pass{letter}.json').write_text(json.dumps(doc), encoding='utf8')
            (out / 'paper.pairs.json').write_text('{"synthetic_stale":true}', encoding='utf8')
            before = {p.name: p.read_bytes() for p in work.iterdir()}
            log = io.StringIO()
            with contextlib.redirect_stdout(log):
                runtime.cmd_check(argparse.Namespace(work=str(work), out=str(out)))
            total = json.loads(log.getvalue().split('\nTOTAL ', 1)[1])
            self.assertEqual(total['papers'], 2)
            self.assertEqual(total['papers_failed'], 1)
            self.assertEqual(total['papers_failed_pass_files'], 1)
            self.assertFalse((out / 'paper.pairs.json').exists())
            self.assertTrue((out / 'left-out/paper.pairs.json').exists())
            self.assertTrue((out / 'later.pairs.json').exists())
            self.assertEqual(before, {p.name: p.read_bytes() for p in work.iterdir()})

    def test_string(self):
        self.check_invalid('synthetic invalid pair')

    def test_null(self):
        self.check_invalid(None)

    def test_list(self):
        self.check_invalid([])


if __name__ == '__main__':
    unittest.main()
