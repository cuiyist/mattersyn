"""Deterministic synthetic engineering fixtures; no real visual/source credit."""
import base64
import copy
import json
from pathlib import Path
import tempfile
import unittest
import preliminary as p
import visual_transcription as v
from test_preliminary import entry, evidence, synthetic_pdf


class VisualTranscriptionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write(self, name, value):
        path = self.root / name
        path.write_bytes(value if isinstance(value, bytes) else p.packed(value))
        return {'path': str(path), 'sha256': v.digest(path.read_bytes())}

    def fixture(self, raw_quote='Observed diameter 25mm.', transcribed='Observed diameter 25µm.', reported='25 µm', pointer='/outcome/descriptors/0/reported'):
        e = entry()
        if pointer.startswith('/operations'):
            e['operations'][1]['conditions'][0]['reported'] = reported
        else:
            e['outcome']['descriptors'][0]['reported'] = reported
        ev, _ = evidence(e)
        claim = next(c for c in ev['claims'] if c['pointer'] == pointer)
        claim['quote'] = raw_quote
        raw = synthetic_pdf(' | '.join(c['quote'] for c in ev['claims']))
        e['document_sha256'] = v.digest(raw)
        texts = p.read_pdf_pages(raw, [1])[1]; text = texts[1]
        raw_pin = self.write('raw.txt', text.encode())
        png = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jR3sAAAAASUVORK5CYII=')
        render = self.write('synthetic.png', png)
        render.update(document_sha256=e['document_sha256'], page=1, rendering='SYNTHETIC FIXTURE ONLY: stand-in PNG, no assertion of a real paper render')
        # One declared minimal replacement; all surrounding characters are exact.
        left = 0
        while left < min(len(raw_quote), len(transcribed)) and raw_quote[left] == transcribed[left]: left += 1
        right = 0
        while right < min(len(raw_quote), len(transcribed)) - left and raw_quote[-1-right] == transcribed[-1-right]: right += 1
        end = len(raw_quote)-right; final_end = len(transcribed)-right
        row = {'pointer':pointer,'page':1,'raw_start':text.index(raw_quote),'raw_end':text.index(raw_quote)+len(raw_quote),'raw_quote':raw_quote,'raw_quote_sha256':v.digest(raw_quote.encode()),'transcribed_quote':transcribed,'transcribed_quote_sha256':v.digest(transcribed.encode()),'edits':[{'start':left,'end':end,'raw':raw_quote[left:end],'replacement':transcribed[left:final_end]}],'author_visual_checked':True}
        receipt = {'schema':v.SCHEMA,'source_id':e['source_id'],'document_sha256':e['document_sha256'],'author_visual_checked':True,'independent_scientific_audit':False,'accuracy':'unmeasured','training_ready':False,'pages':[{'page':1,'raw_text':raw_pin,'render':render}],'transcriptions':[row]}
        self.pins = {}
        def load(path, expected=None):
            b = path.read_bytes(); sha = v.digest(b)
            if expected is not None and sha != expected: raise ValueError('dependency hash mismatch')
            self.pins[str(path)] = sha
            return b
        self.load = load
        return e, ev, texts, receipt, raw

    def prepare(self, values):
        e, ev, texts, receipt, _ = values
        return v.prepare(self.write('visual.json', receipt),e,texts,ev['claims'],p.scientific_fields(e),Path,self.load)

    def test_explicit_micrometre_and_ratio_corrections(self):
        cases = [('Observed diameter 25mm.','Observed diameter 25µm.','25 µm','/outcome/descriptors/0/reported'),('The ratio was 14:l','The ratio was 14:1','14:1','/operations/1/conditions/0/reported')]
        for args in cases:
            with self.subTest(args=args):
                values=self.fixture(*args); before=copy.deepcopy(values[:3]); ctx=self.prepare(values)
                p.validate_claims(*values[:3],visual_context=ctx)
                self.assertEqual(before,values[:3]); self.assertEqual(3,len(self.pins))

    def test_absent_receipt_retains_raw_failure(self):
        values=self.fixture()
        with self.assertRaises(ValueError):p.validate_claims(*values[:3])

    def test_source_identity_and_page_mismatches(self):
        for field,value in [('source_id','wrong'),('document_sha256','f'*64)]:
            values=self.fixture();values[3][field]=value
            with self.assertRaisesRegex(ValueError,'identity'):self.prepare(values)
        values=self.fixture();values[3]['pages'][0]['page']=2
        with self.assertRaisesRegex(ValueError,'page'):self.prepare(values)

    def test_render_source_page_and_provenance_required(self):
        for field,value in [('page',2),('document_sha256','f'*64),('rendering','')]:
            values=self.fixture();values[3]['pages'][0]['render'][field]=value
            with self.assertRaises(ValueError):self.prepare(values)
        values=self.fixture();del values[3]['pages'][0]['render']
        with self.assertRaises(ValueError):self.prepare(values)

    def test_pin_tampering_raw_render_and_receipt(self):
        for kind in ['raw_text','render']:
            values=self.fixture();Path(values[3]['pages'][0][kind]['path']).write_bytes(b'tampered')
            with self.assertRaisesRegex(ValueError,'dependency'):self.prepare(values)
        values=self.fixture();pin=self.write('visual.json',values[3]);pin['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'dependency'):v.prepare(pin,values[0],values[2],values[1]['claims'],p.scientific_fields(values[0]),Path,self.load)

    def test_rehashed_fake_page_and_non_png_still_reject(self):
        values=self.fixture();values[3]['pages'][0]['raw_text']=self.write('fake.txt',b'fabricated')
        with self.assertRaisesRegex(ValueError,'actual PDF'):self.prepare(values)
        values=self.fixture();values[3]['pages'][0]['render'].update(self.write('fake.png',b'not a PNG'))
        with self.assertRaisesRegex(ValueError,'PNG'):self.prepare(values)

    def test_raw_offsets_and_span_hashes_required(self):
        for field,value in [('raw_start',0),('raw_end',999999),('raw_quote_sha256','f'*64),('transcribed_quote_sha256','f'*64)]:
            values=self.fixture();values[3]['transcriptions'][0][field]=value
            with self.assertRaises(ValueError):self.prepare(values)

    def test_pointer_rebinding_and_page_rebinding_reject(self):
        for field,value in [('pointer','/precursors/0/amount'),('pointer','/not-a-field'),('page',2)]:
            values=self.fixture();values[3]['transcriptions'][0][field]=value
            with self.assertRaises(ValueError):self.prepare(values)

    def test_doi_and_title_ineligible(self):
        for pointer in ['/doi','/title']:
            values=self.fixture();values[3]['transcriptions'][0]['pointer']=pointer
            with self.assertRaisesRegex(ValueError,'ineligible'):self.prepare(values)

    def test_no_identity_bypass_through_context(self):
        values=self.fixture();ctx=self.prepare(values);e,ev,texts=values[:3]
        c=next(c for c in ev['claims'] if c['pointer']=='/doi');c['quote']='Printed ID 10.9999/other';texts[1]+=' '+c['quote']
        ctx[('/doi',1,p.norm(c['quote']))]=e['doi']
        with self.assertRaisesRegex(ValueError,'DOI identity'):p.validate_claims(e,ev,texts,visual_context=ctx)

    def test_undeclared_substitutions_rejected(self):
        values=self.fixture();row=values[3]['transcriptions'][0];row['transcribed_quote']='Observed diameter 250µm.';row['transcribed_quote_sha256']=v.digest(row['transcribed_quote'].encode())
        with self.assertRaisesRegex(ValueError,'undeclared'):self.prepare(values)

    def test_edit_outside_span_overlapping_or_wrong_raw(self):
        for update in [{'start':-1},{'end':9999},{'raw':'different'}]:
            values=self.fixture();values[3]['transcriptions'][0]['edits'][0].update(update)
            with self.assertRaises(ValueError):self.prepare(values)
        values=self.fixture();row=values[3]['transcriptions'][0];row['edits']*=2
        with self.assertRaisesRegex(ValueError,'overlapping'):self.prepare(values)

    def test_missing_author_check_or_inflated_scope_rejected(self):
        for key,value in [('author_visual_checked',False),('independent_scientific_audit',True),('accuracy','validated'),('training_ready',True)]:
            values=self.fixture();values[3][key]=value
            with self.assertRaisesRegex(ValueError,'declaration'):self.prepare(values)
        values=self.fixture();values[3]['transcriptions'][0]['author_visual_checked']=False
        with self.assertRaises(ValueError):self.prepare(values)

    def test_duplicate_unused_and_partial_claims_rejected(self):
        values=self.fixture();values[3]['transcriptions']*=2
        with self.assertRaisesRegex(ValueError,'duplicate'):self.prepare(values)
        values=self.fixture();c=next(c for c in values[1]['claims'] if c['pointer']=='/outcome/descriptors/0/reported');c['quote']='25mm'
        with self.assertRaisesRegex(ValueError,'exact matching claim'):self.prepare(values)

    def test_transcription_does_not_authorize_other_claim(self):
        values=self.fixture();ctx=self.prepare(values)
        self.assertIsNone(v.quote('Observed diameter 25mm.',1,'/operations/0/action',ctx))
        self.assertIsNone(v.quote('25mm',1,'/outcome/descriptors/0/reported',ctx))

    def test_unknown_units_and_wrong_quantities_remain_rejected(self):
        values=self.fixture('Observed value 25furl0ng.','Observed value 25furlong.','25 furlong');ctx=self.prepare(values)
        with self.assertRaisesRegex(ValueError,'unsupported quantity'):p.validate_claims(*values[:3],visual_context=ctx)
        values=self.fixture();ctx=self.prepare(values);values[0]['outcome']['descriptors'][0]['reported']='250 µm'
        with self.assertRaises(ValueError):p.validate_claims(*values[:3],visual_context=ctx)

    def test_unresolved_glyphs_still_hold(self):
        values=self.fixture('Observed /H99999 25mm.','Observed /H99999 25µm.')
        with self.assertRaisesRegex(ValueError,'unresolved'):self.prepare(values)

    def test_c_style_unresolved_glyphs_remain_held(self):
        values=self.fixture('Observed /C999 25mm.','Observed /C999 25µm.')
        with self.assertRaisesRegex(ValueError,'unresolved'):self.prepare(values)

    def test_raw_claim_cannot_be_replaced_with_transcribed_text(self):
        values=self.fixture();ctx=self.prepare(values);c=next(c for c in values[1]['claims'] if c['pointer']=='/outcome/descriptors/0/reported');c['quote']='Observed diameter 25µm.'
        with self.assertRaisesRegex(ValueError,'unmatched'):p.validate_claims(*values[:3],visual_context=ctx)

    def test_long_transcribed_copy_remains_rejected(self):
        raw='This is a synthetic source sentence for a deliberate copy boundary test. '*3+'25mm'
        values=self.fixture(raw,raw[:-4]+'25µm');ctx=self.prepare(values);values[0]['scope']=values[3]['transcriptions'][0]['transcribed_quote']
        with self.assertRaisesRegex(ValueError,'verbatim'):p.validate_claims(*values[:3],visual_context=ctx)

    def test_universal_newline_offsets_still_pin_original_bytes(self):
        values=self.fixture();row=values[3]['pages'][0];path=Path(row['raw_text']['path']);path.write_bytes(b'\r\n'+path.read_bytes());row['raw_text']['sha256']=v.digest(path.read_bytes());t=values[3]['transcriptions'][0];t['raw_start']+=1;t['raw_end']+=1;self.prepare(values)

    def test_actual_pdf_projection_merge_and_dependency_recheck(self):
        values=self.fixture();e,ev,texts,receipt,raw=values
        ev.update(schema=p.EVIDENCE_SCHEMA,source_id=e['source_id'],document=self.write('source.pdf',raw),identity={'doi':e['doi'],'title':e['title'],'checked':True},page_map=self.write('pages.json',{'schema':p.MAP_SCHEMA,'document_sha256':e['document_sha256'],'source_pages':1,'pages':[{'page':1,'text':texts[1]}]}),visual_transcription=self.write('visual.json',receipt))
        screen=self.write('screen.jsonl',(json.dumps({'decision':'pass','source_sha256':e['document_sha256']})+'\n').encode());ev['screened_pass']=dict(screen,line_number=1)
        self.write(e['source_id']+'.json',ev);pins={};before=copy.deepcopy(e)
        doc=p.project({'schema':p.SCHEMA,'entries':[e]},self.root,pins_out=pins)
        self.assertEqual(before,e);self.assertEqual(7,len(pins));self.assertNotIn('visual_transcription',doc['entries'][0])
        cp=self.write('public.json',doc);rp=self.write('validation.json',{'schema':'mattersyn-preliminary-validation/1','status':'private_anchors_verified','candidate_sha256':cp['sha256'],'dependencies':pins,'entries':[e['source_id']],'independent_scientific_audit':False,'accuracy':'unmeasured','training_ready':False})
        self.assertEqual(doc,p.merge_catalog({'schema':p.SCHEMA,'entries':[]},[(cp['path'],rp['path'])]))
        Path(receipt['pages'][0]['render']['path']).write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError,'dependency changed'):p.merge_catalog({'schema':p.SCHEMA,'entries':[]},[(cp['path'],rp['path'])])


if __name__ == '__main__': unittest.main()
