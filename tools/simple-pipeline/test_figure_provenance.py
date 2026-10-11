import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location('figure_metadata_simple', Path(__file__).with_name('mattersyn_simple.py'))
simple = importlib.util.module_from_spec(spec); spec.loader.exec_module(simple)


class FigureMetadataTest(unittest.TestCase):
    def test_crop_pins_match_original_pdf_render_and_saved_bytes(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            root = Path(tmp); pdf = root / 'fixture.pdf'; pdf.write_bytes(b'synthetic PDF fixture')
            crop_bytes = b'synthetic crop bytes'
            pixmap = SimpleNamespace(width=120, height=90, save=lambda target: Path(target).write_bytes(crop_bytes))
            page = SimpleNamespace(rect=SimpleNamespace(width=612, height=792), get_pixmap=mock.Mock(return_value=pixmap))
            doc = mock.MagicMock(); doc.__enter__.return_value = doc; doc.__getitem__.return_value = page
            fitz = ModuleType('pymupdf'); fitz.open = mock.Mock(return_value=doc)
            clip = [10.25, 200.5, 400.75, 500.25]
            with mock.patch.dict(sys.modules, {'pymupdf': fitz}), mock.patch.object(simple, 'find_figures', return_value=[(1, 'Chart 2', 'Synthetic caption', clip, True)]), mock.patch.object(simple, 'figure_categories', return_value=['property']):
                simple.cmd_figures(SimpleNamespace(papers=[pdf], out=root / 'work', model=None, dpi=180, all=False))
            fig = json.loads((root / 'work/fixture.figures.json').read_text())[0]
            self.assertEqual(fig['source_pdf_sha256'], hashlib.sha256(pdf.read_bytes()).hexdigest())
            self.assertEqual(fig['asset_sha256'], hashlib.sha256(crop_bytes).hexdigest())
            self.assertEqual(fig['crop_box_pdf_points'], clip)
            self.assertEqual(fig['page_size_pdf_points'], [612, 792])
            self.assertEqual(fig['pixel_size'], [120, 90])
            self.assertEqual(fig['render_dpi'], 180)
            self.assertEqual(fig['render_tool'], 'PyMuPDF automatic PDF figure-region crop')
            page.get_pixmap.assert_called_once_with(clip=clip, dpi=180)
            public = simple.public_document({'id': 'fixture', 'figures': [fig], 'pairs': []})
            self.assertEqual(public['figures'][0]['crop_box_pdf_points'], clip)
            self.assertNotIn('Synthetic caption', json.dumps(public))


if __name__ == '__main__': unittest.main()
