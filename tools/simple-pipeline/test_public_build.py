import copy
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

spec = importlib.util.spec_from_file_location('simple_public_build', Path(__file__).with_name('mattersyn_simple.py'))
simple = importlib.util.module_from_spec(spec)
spec.loader.exec_module(simple)


class PublicBuildTest(unittest.TestCase):
    def test_recursive_quotes_removed_without_mutation(self):
        data = {'quote': 'first key "quoted"', 'items': [{'value': 4, 'quote': 'second'}, ['x', {'quotes': ['third']}]], 'value': 'quoted-looking text'}
        before = copy.deepcopy(data)
        self.assertEqual(simple.without_quotes(data), {'items': [{'value': 4}, ['x', {}]], 'value': 'quoted-looking text'})
        self.assertEqual(data, before)

    def fixture(self):
        return {'id': 'fixture', 'doi': '10.1234/fixture', 'title': 'Bibliographic title',
                'page_count': 3, 'pages_read': [1, 3], 'pdf_path': 'C:/private/paper.pdf',
                'source_metadata': {'path': '/private/source'},
                'figures': [{'file': 'C:\\private\\figure-1.png', 'figure': 'Figure 1', 'page': 3,
                             'caption': 'PRIVATE VERBATIM CAPTION', 'categories': ['structure'],
                             'source_pdf': 'C:/private/paper.pdf'}],
                'pairs': [{'product': 'ZnS', 'structure': {'size': {'value': 4, 'unit': 'nm', 'quote': 'PRIVATE QUOTATION'}},
                           'recipe': {'steps': [{'action': 'heat', 'description': 'Heat the solution', 'quote': 'PRIVATE QUOTATION'}]}}]}

    def test_public_document_page_locators_and_generic_figures(self):
        data = self.fixture()
        public = simple.public_document(data)
        self.assertEqual(public['pages_read'], [1, 3])
        self.assertEqual(public['figures'][0]['file'], 'figure-1.png')
        self.assertEqual(public['figures'][0]['page'], 3)
        self.assertIn('Automatic caption-based category: structure', public['figures'][0]['caption'])
        self.assertIn('no sample match is asserted', public['figures'][0]['caption'])
        serialized = json.dumps(public)
        for forbidden in ('PRIVATE', '/private/', 'C:', 'pdf_path', 'source_metadata', 'source_pdf', '"quote"'):
            self.assertNotIn(forbidden, serialized)
        self.assertIn('PRIVATE VERBATIM CAPTION', data['figures'][0]['caption'])

    def test_build_public_export_has_no_quote_caption_or_path(self):
        with TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            work = Path(tmp) / 'pairs'; work.mkdir()
            source = work / 'fixture.pairs.json'
            source.write_text(json.dumps(self.fixture()), encoding='utf-8')
            original = source.read_bytes()
            out = Path(tmp) / 'public'
            simple.cmd_build(SimpleNamespace(pairs=work, out=out, label='Source-extracted', quotes=False))
            for target in (out / 'pairs.json', out / 'p/fixture.html'):
                text = target.read_text(encoding='utf-8')
                for forbidden in ('PRIVATE', '/private/', 'C:', '"quote"'):
                    self.assertNotIn(forbidden, text)
            self.assertEqual(source.read_bytes(), original)

    def test_nested_private_annotations_removed_and_all_factual_locators_kept(self):
        data = self.fixture(); pair = data['pairs'][0]
        pair['private_pair_path'] = 'C:/private/pair.json'
        pair['structure']['private_input'] = {'file': 'C:/private/input.pdf'}
        pair['structure']['size'].update(page=3, source_path='C:/private/page.txt', private={'quotes': ['PRIVATE']})
        pair['recipe']['chemicals'] = [{'name': 'zinc acetate', 'role': 'metal source', 'amount': 0.4, 'unit': 'mmol', 'page': 2,
                                        'quote': 'PRIVATE', 'source_pdf': 'C:/private/input.pdf', 'annotations': {'path': '/private'}}]
        pair['recipe']['steps'][0].update(page=2, temperature=250, temperature_unit='°C', time=5, time_unit='min', uses=['zinc acetate'],
                                          source_text_path='C:/private/page.txt', model_payload={'quote': 'PRIVATE'})
        original = copy.deepcopy(data)
        public = simple.public_document(data); exported = public['pairs'][0]
        self.assertEqual(exported['structure']['size'], {'value': 4, 'unit': 'nm', 'page': 3})
        self.assertEqual(exported['recipe']['chemicals'][0], {'name': 'zinc acetate', 'role': 'metal source', 'amount': 0.4, 'unit': 'mmol', 'page': 2})
        self.assertEqual(exported['recipe']['steps'][0]['temperature'], 250)
        self.assertEqual(exported['recipe']['steps'][0]['time'], 5)
        self.assertEqual(exported['recipe']['steps'][0]['page'], 2)
        self.assertEqual(exported['recipe']['steps'][0]['uses'], ['zinc acetate'])
        for private in ('PRIVATE', '/private', 'C:', 'source_pdf', 'source_path', 'annotations', 'model_payload', 'private_pair_path'):
            self.assertNotIn(private, json.dumps(public))
        self.assertEqual(data, original)

    def test_all_figure_provenance_pins_survive_public_build(self):
        data = self.fixture()
        pins = {'source_pdf_sha256': 'a' * 64, 'asset_sha256': 'b' * 64,
                'render_tool': 'PyMuPDF automatic PDF figure-region crop', 'render_dpi': 200,
                'page_size_pdf_points': [595.2, 841.8], 'crop_box_pdf_points': [10.5, 21.0, 500.2, 760.4], 'pixel_size': [1361, 2054]}
        data['figures'][0].update(pins)
        with TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            source = Path(tmp) / 'pairs'; source.mkdir()
            (source / 'fixture.pairs.json').write_text(json.dumps(data), encoding='utf-8')
            out = Path(tmp) / 'public'
            simple.cmd_build(SimpleNamespace(pairs=source, out=out, label='Source-extracted', quotes=False))
            figure = json.loads((out / 'pairs.json').read_text(encoding='utf-8'))[0]['figures'][0]
            self.assertEqual({k: figure[k] for k in pins}, pins)
            self.assertEqual(figure['page'], 3)
            self.assertEqual(figure['file'], 'figure-1.png')
            self.assertNotIn('PRIVATE', figure['caption'])

    def test_explicit_quotes_export_keeps_original_document(self):
        with TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            work = Path(tmp) / 'pairs'; work.mkdir()
            data = self.fixture()
            (work / 'fixture.pairs.json').write_text(json.dumps(data), encoding='utf-8')
            out = Path(tmp) / 'private'
            simple.cmd_build(SimpleNamespace(pairs=work, out=out, label='Private preview', quotes=True))
            self.assertEqual(json.loads((out / 'pairs.json').read_text(encoding='utf-8')), [data])
            self.assertIn('PRIVATE VERBATIM CAPTION', (out / 'p/fixture.html').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
