"""Generated UTF-8 bytes are portable; audited input bytes are never normalized."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_atlas
import build_dataset
import build_paper_reviews
import build_reader_metadata
import build_reader_views
import generate_release_metadata


class GeneratedNewlines(unittest.TestCase):
    def test_actual_json_writers_emit_utf8_lf_and_preserve_values(self):
        value = {'label': 'Synthetic \u00c5 fixture', 'source_text': 'a\r\nb', 'number': 0.25}
        expected_pretty = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
        expected_compact = (json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8')
        with tempfile.TemporaryDirectory() as directory:
            for name, writer, expected in [
                ('dataset', build_dataset.dump, expected_pretty),
                ('review', build_paper_reviews.write, expected_pretty),
                ('atlas', build_atlas.write, expected_compact),
                ('release', generate_release_metadata.dump, expected_pretty),
            ]:
                with self.subTest(writer=name):
                    target = Path(directory) / name / 'out.json'
                    writer(target, value)
                    self.assertEqual(target.read_bytes(), expected)
                    self.assertEqual(json.loads(target.read_bytes()), value)

    def test_reader_wrapper_emits_lf_without_touching_existing_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / 'templates').mkdir(); (root / 'dist').mkdir()
            (root / 'templates/material-reader.html').write_bytes(b'<main{{READER_CONTEXT}}>\r\nbody\r\n</main>\r\n')
            evidence = root / 'dist/archived-evidence.html'; evidence.write_bytes(b'<pre>source\r\n</pre>\r\n')
            with patch.object(build_reader_views, 'ROOT', root):
                build_reader_views.write_reader_entrypoints(root / 'dist')
            self.assertEqual((root / 'dist/material.html').read_bytes(), b'<main >\nbody\n</main>\n')
            self.assertEqual(evidence.read_bytes(), b'<pre>source\r\n</pre>\r\n')

    def test_unchanged_reader_sidecar_keeps_audited_crlf_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path in ('data/records', 'dist/data/materials'): (root / path).mkdir(parents=True)
            source = root / 'data/reader-presentation-reviewed.json'
            raw = b'{\r\n  "records": {},\r\n  "materials": {}\r\n}\r\n'
            source.write_bytes(raw)
            with patch.object(build_reader_metadata, 'ROOT', root):
                build_reader_metadata.main()
            self.assertEqual((root / 'dist/data/reader-presentation.json').read_bytes(), raw)

    def test_transformed_reader_output_is_lf_without_rewriting_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path in ('data/records', 'dist/data/materials'): (root / path).mkdir(parents=True)
            source = root / 'data/reader-presentation-reviewed.json'
            raw = b'{\r\n  "records": {},\r\n  "materials": {}\r\n}\r\n'; source.write_bytes(raw)
            transformed = {'records': {}, 'materials': {}, 'display': 'Synthetic \u00c5'}
            with patch.object(build_reader_metadata, 'ROOT', root), patch.object(build_reader_metadata, 'display_view', return_value=transformed):
                build_reader_metadata.main()
            self.assertEqual(source.read_bytes(), raw)
            expected = (json.dumps(transformed, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
            self.assertEqual((root / 'dist/data/reader-presentation.json').read_bytes(), expected)


if __name__ == '__main__':
    unittest.main()
