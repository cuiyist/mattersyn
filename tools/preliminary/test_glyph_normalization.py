"""Synthetic engineering tests; visual assertions here grant no source credit."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import preliminary as p
import glyph_normalization as g
from test_preliminary import entry, evidence, synthetic_pdf


class GlyphTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write(self, name, value):
        path = self.root / name
        path.write_bytes(value if isinstance(value, bytes) else p.packed(value))
        return {'path': str(path), 'sha256': g.digest(path.read_bytes())}

    def fixture(self):
        e = entry(); e['outcome']['descriptors'][0]['reported'] = '~ 10 nm'
        ev, _ = evidence(e)
        c = next(c for c in ev['claims'] if c['pointer'] == '/outcome/descriptors/0/reported')
        c['quote'] = '/H1101110 nm'
        rawtext = ' '.join(c['quote'] for c in ev['claims'])
        raw = synthetic_pdf(rawtext)
        # Real local PDF parsing, explicitly synthetic font-name inventory.
        from pypdf import PdfReader, PdfWriter
        from pypdf.generic import NameObject, DictionaryObject, ArrayObject, NumberObject
        from io import BytesIO
        reader = PdfReader(BytesIO(raw), strict=True); writer = PdfWriter()
        font = reader.pages[0]['/Resources']['/Font']['/F1'].get_object()
        font[NameObject('/Encoding')] = DictionaryObject({NameObject('/Differences'): ArrayObject([NumberObject(1)] + [NameObject(s) for s in ['/H11011','/H20849','/H20850','/H20851','/H20852']])})
        writer.add_page(reader.pages[0]); out = BytesIO(); writer.write(out); raw = out.getvalue()
        e['document_sha256'] = g.digest(raw)
        texts = p.read_pdf_pages(raw, [1])[1]
        text = texts[1]
        pagepin = self.write('page.txt', text.encode('utf-8'))
        # Real minimal PNG bytes; fixture only, not a rendered scientific page.
        import base64
        image = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jR3sAAAAASUVORK5CYII=')
        render = self.write('synthetic.png', image)
        quote = '/H1101110 nm'; start = text.index(quote)
        visual = {'schema': g.VISUAL_SCHEMA, 'source_id': e['source_id'], 'source_pdf': {'sha256': e['document_sha256']}, 'independent_scientific_audit': False,
                  'pages': [{'page': 1, 'raw_text_path': pagepin['path'], 'raw_text_sha256': pagepin['sha256'], 'render_path': render['path'], 'render_sha256': render['sha256'], 'rendering': 'SYNTHETIC FIXTURE: no real visual source claim'}],
                  'mappings': [{'raw_code': '/H11011', 'visible_punctuation': '~', 'visual_status': 'confirmed', 'observed_in': ['test']}],
                  'quotes': {'test': {'page': 1, 'raw_text': quote, 'raw_character_start': start, 'raw_character_end': start + len(quote), 'raw_utf8_sha256': g.digest(quote.encode()), 'normalized_quote': quote, 'normalized_quote_sha256': g.digest(quote.encode())}}}
        spec = {'schema': g.SCHEMA, 'source_id': e['source_id'], 'document_sha256': e['document_sha256'], 'visual_evidence': self.write('visual.json', visual), 'pages': [{'page': 1, 'aliases': {'/H11011': '~'}}]}
        self.pins = {}
        def load(path, expected=None):
            b = path.read_bytes(); h = g.digest(b)
            if expected is not None and h != expected: raise ValueError('dependency hash mismatch')
            self.pins[str(path)] = h
            return b
        self.load = load
        return e, ev, raw, texts, spec, visual

    def prepare(self, values):
        e, ev, raw, texts, spec, visual = values
        spec['visual_evidence'] = self.write('visual.json', visual)
        return g.prepare(self.write('map.json', spec), e, raw, texts, Path, self.load)

    def test_real_pdf_font_inventory_and_exact_prefix(self):
        values = self.fixture(); ctx = self.prepare(values)
        p.validate_claims(values[0], values[1], values[3], glyph_context=ctx)
        self.assertEqual('~150 [111]', g.decode('/H11011150 /H20851111/H20852', {'/H11011','/H20851','/H20852'}, {'/H11011':'~','/H20851':'[','/H20852':']'}))
        self.assertEqual(4, len(self.pins))

    def test_no_map_retains_original_failure(self):
        e, ev, raw, texts, spec, visual = self.fixture()
        with self.assertRaises(ValueError): p.validate_claims(e, ev, texts)

    def test_complete_private_projection_binds_extra_dependencies(self):
        values = self.fixture(); e, ev, raw, texts, spec, visual = values
        spec['visual_evidence'] = self.write('visual.json', visual)
        ev.update(schema=p.EVIDENCE_SCHEMA, source_id=e['source_id'], document=self.write('source.pdf',raw), identity={'doi':e['doi'],'title':e['title'],'checked':True},
                  page_map=self.write('pages.json',{'schema':p.MAP_SCHEMA,'document_sha256':e['document_sha256'],'source_pages':1,'pages':[{'page':1,'text':texts[1]}]}),
                  glyph_normalization=self.write('map.json',spec))
        screen = self.write('screen.jsonl',(json.dumps({'decision':'pass','source_sha256':e['document_sha256']})+'\n').encode())
        ev['screened_pass'] = dict(screen,line_number=1)
        ep = self.write(e['source_id']+'.json', ev)
        e['evidence_fingerprint'] = ep['sha256']; pins = {}
        self.assertEqual([],p.validate_private(e,Path(ep['path']),pins_out=pins))
        self.assertEqual(8,len(pins))
        before = copy.deepcopy(e)
        p.project({'schema':p.SCHEMA,'entries':[e]},self.root)
        self.assertEqual(before,e)
        Path(visual['pages'][0]['render_path']).write_bytes(b'tampered')
        self.assertIn('dependency hash mismatch',p.validate_private(e,Path(ep['path']))[0])

    def test_digits_letters_units_empty_or_multi_symbol_rejected(self):
        for value in ['150', 'A', 'nm', '°C', '', '~1', '~~', '.', '−']:
            with self.subTest(value=value):
                values = self.fixture(); values[4]['pages'][0]['aliases']['/H11011'] = value
                with self.assertRaisesRegex(ValueError, 'punctuation'): self.prepare(values)

    def test_fabricated_or_prefix_code_rejected(self):
        for code in ['/H1101', '/H11011150', '/H99999']:
            values = self.fixture(); values[4]['pages'][0]['aliases'] = {code:'~'}
            with self.assertRaisesRegex(ValueError, 'font names'): self.prepare(values)

    def test_unknown_code_in_used_quote_rejected(self):
        values = self.fixture(); ctx = self.prepare(values)
        for quote in ['/H99999150 nm', '/H20849150 nm', '/H9251150 nm']:
            with self.assertRaisesRegex(ValueError, 'unknown'): g.quote(quote, 1, ctx)

    def test_mapping_does_not_authorize_unseen_occurrences(self):
        values = self.fixture(); ctx = self.prepare(values)
        ctx['texts'][1] += ' Another /H1101120 nm.'
        with self.assertRaisesRegex(ValueError, 'visual observation'): g.quote('Another /H1101120 nm.', 1, ctx)
        ctx['texts'][1] += ' /H1101110 nm'
        with self.assertRaisesRegex(ValueError, 'ambiguous'): g.quote('/H1101110 nm', 1, ctx)

    def test_wrong_document_and_page_rejected(self):
        values = self.fixture(); values[4]['document_sha256'] = 'f'*64
        with self.assertRaisesRegex(ValueError, 'identity'): self.prepare(values)
        values = self.fixture(); values[4]['pages'][0]['page'] = 2
        with self.assertRaisesRegex(ValueError, 'page'): self.prepare(values)

    def test_malformed_visual_source_identity_fails_closed(self):
        values = self.fixture(); values[5]['source_pdf'] = None
        with self.assertRaisesRegex(ValueError, 'identity'): self.prepare(values)

    def test_forged_visual_quote_normalization_rejected(self):
        values = self.fixture(); q = values[5]['quotes']['test']
        q['normalized_quote'] = '~100 nm'; q['normalized_quote_sha256'] = g.digest(q['normalized_quote'].encode())
        with self.assertRaisesRegex(ValueError, 'quote/offset/hash'): self.prepare(values)

    def test_visual_mapping_missing_or_disagrees_rejected(self):
        for key, value in [('visible_punctuation','['), ('visual_status','unchecked'), ('observed_in',[])]:
            values = self.fixture(); values[5]['mappings'][0][key] = value
            with self.assertRaises(ValueError): self.prepare(values)

    def test_changed_render_and_raw_page_rejected(self):
        values = self.fixture(); Path(values[5]['pages'][0]['render_path']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'dependency'): self.prepare(values)
        values = self.fixture(); r = values[5]['pages'][0]
        Path(r['raw_text_path']).write_bytes(b'fabricated'); r['raw_text_sha256'] = g.digest(b'fabricated')
        with self.assertRaisesRegex(ValueError, 'actual PDF'): self.prepare(values)

    def test_visual_crlf_offsets_use_explicit_universal_newlines(self):
        values = self.fixture(); row = values[5]['pages'][0]
        page = Path(row['raw_text_path']); page.write_bytes(b'\r\n' + page.read_bytes())
        row['raw_text_sha256'] = g.digest(page.read_bytes())
        q = values[5]['quotes']['test']; q['raw_character_start'] += 1; q['raw_character_end'] += 1
        self.prepare(values)

    def test_fake_claim_quote_and_changed_value_rejected(self):
        values = self.fixture(); ctx = self.prepare(values); e, ev = values[:2]
        c = next(c for c in ev['claims'] if c['pointer'] == '/outcome/descriptors/0/reported')
        c['quote'] = '~ 10 nm'
        with self.assertRaisesRegex(ValueError, 'unmatched'): p.validate_claims(e, ev, values[3], glyph_context=ctx)
        values = self.fixture(); ctx = self.prepare(values); values[0]['outcome']['descriptors'][0]['reported'] = '~ 100 nm'
        with self.assertRaises(ValueError): p.validate_claims(values[0], values[1], values[3], glyph_context=ctx)

    def test_no_unit_or_numeric_whitespace_normalization(self):
        text = '/H11011150 ° C; 20 kg/cm 2; 4 8 nm'
        self.assertEqual('~150 ° C; 20 kg/cm 2; 4 8 nm', g.decode(text, {'/H11011'}, {'/H11011':'~'}))
        self.assertEqual(p.quantity_spans('150 °C'), p.quantity_spans('150 ° C'))
        self.assertNotEqual(p.quantity_spans('48 nm'), p.quantity_spans('4 8 nm'))


if __name__ == '__main__': unittest.main()
