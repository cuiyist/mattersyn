"""Declared source tables must stay inside one paper's generated directory."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_paper_reviews as builder


class EvidenceStagingTests(unittest.TestCase):
    def test_declared_table_and_reader_sidecar_copy_exact_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'data/paper-evidence/example'
            source.mkdir(parents=True)
            files = {'runs.csv': b'run,value\r\n1,2\r\n',
                     'reader-sidecar.json': b'{"paper_id":"example"}\n'}
            for name, raw in files.items():
                (source / name).write_bytes(raw)
            with patch.object(builder, 'ROOT', root):
                builder.stage_reader_evidence({'paper_id': 'example', 'tables': [
                    {'source_data_path': 'data/paper-evidence/example/runs.csv'}]})
            for name, raw in files.items():
                self.assertEqual((root / 'dist/data/paper-evidence/example' / name).read_bytes(), raw)

    def test_traversal_absolute_and_cross_paper_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'data/paper-evidence/example'
            source.mkdir(parents=True)
            original = b'run,value\n1,2\n'
            (source / 'runs.csv').write_bytes(original)
            paths = [str(source / 'runs.csv'), (source / 'runs.csv').as_posix(),
                     'data/paper-evidence/example/../other/runs.csv',
                     'data/paper-evidence/other/runs.csv',
                     'data\\paper-evidence\\example\\runs.csv',
                     'C:/tmp/runs.csv', '/tmp/runs.csv']
            with patch.object(builder, 'ROOT', root):
                for path in paths:
                    with self.subTest(path=path), self.assertRaises(ValueError):
                        builder.stage_reader_evidence({'paper_id': 'example', 'tables': [
                            {'source_data_path': path}]})
            self.assertEqual((source / 'runs.csv').read_bytes(), original)
            self.assertFalse((root / 'dist').exists())
