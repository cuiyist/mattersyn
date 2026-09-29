"""Synthetic engineering fixtures only. No paper or publication credit."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import preliminary as p

def entry():
    loc=[{'page':1,'section':'Synthetic methods and result'}]
    return {'source_id':p.source_id('10.9999/synthetic-demo'),'doi':'10.9999/synthetic-demo','title':'SYNTHETIC TEST ONLY: zinc oxide preparation','citation':'Synthetic engineering fixture; not a research paper','document_sha256':'0'*64,'document_role':'main','source_pages':1,'inspected_pages':[1],'material':{'label':'Zinc oxide','elements':['Zn','O'],'existing_hub_id':None},'method_label':'Synthetic precipitation example','scope':'SYNTHETIC TEST ONLY; validates code, not a scientific contribution.','deferred':['Independent audit and real source data'],'precursors':[{'name':'Zinc salt','amount':'1 g','role':'Precursor','locators':loc}],'operations':[{'order':1,'action':'Dissolve the zinc salt','conditions':[],'locators':loc},{'order':2,'action':'Heat the resulting mixture','conditions':[{'parameter':'Duration','reported':'2 h'}],'locators':loc}],'outcome':{'sample_label':'Synthetic sample','link_basis':'The synthetic paragraph identifies the heated mixture as this product.','descriptors':[{'kind':'size','reported':'10 nm','technique':'TEM','locators':loc}],'locators':loc},'missing_fields':['No real experimental evidence'],'review':copy.deepcopy(p.REVIEW) if hasattr(p,'REVIEW') else {'tier':'preliminary','author_source_checked':True,'independent_audit':'pending','accuracy':'unmeasured','training_ready':False},'extraction':{'origin':'assistant_source_checked','recipe_scope_complete':True,'omitted_variants':'Synthetic fixture has no real variants.','source_identity_checked':True},'evidence_fingerprint':'0'*64}

def evidence(e):
    text=' '.join(v for v,_ in p.scientific_fields(e).values())
    return {'claims':[{'pointer':k,'page':1,'quote':v,'value_tokens':list(set(p.NUMBER.findall(v)+p.UNITS.findall(v))),'semantic_link_checked':True} for k,(v,_) in p.scientific_fields(e).items()]},{1:p.norm(text)}

class PublicTests(unittest.TestCase):
    def test_empty_and_synthetic(self):
        self.assertEqual([],p.validate_catalog({'schema':p.SCHEMA,'entries':[]}));self.assertEqual([],p.validate_catalog({'schema':p.SCHEMA,'entries':[entry()]}))
    def bad(self,e):self.assertTrue(p.validate_catalog({'schema':p.SCHEMA,'entries':[e]}))
    def test_unknown_nested_keys(self):
        e=entry();e['outcome']['raw_text']='private';self.bad(e)
    def test_private_path_and_quote_keys(self):
        e=entry();e['title']='C:' + '/' + 'Users/test/source.pdf';self.bad(e)
        e=entry();e['precursors'][0]['evidence_quote']='secret';self.bad(e)
    def test_order_and_minimum_scope(self):
        e=entry();e['operations'][1]['order']=3;self.bad(e)
        e=entry();e['operations']=e['operations'][:1];self.bad(e)
        e=entry();e['precursors'][0]['amount']=None;e['operations'][1]['conditions']=[];self.bad(e)
    def test_wrong_page_review_and_identity(self):
        for field,val in [('source_pages',False),('inspected_pages',[2]),('doi','http://doi.org/10.9999/synthetic-demo'),('source_id','arbitrary')]:
            e=entry();e[field]=val;self.bad(e)
        e=entry();e['review']['author_source_checked']=1;self.bad(e)
        e=entry();e['review']['training_ready']=True;self.bad(e)
    def test_duplicate_and_outcome(self):
        e=entry();self.assertTrue(p.validate_catalog({'schema':p.SCHEMA,'entries':[e,e]}));e['outcome']['descriptors']=[];self.bad(e)
    def test_malformed_action_no_crash(self):
        e=entry();e['operations'][0]['action']={};self.bad(e)
    def test_controls_and_full_length(self):
        for char in ['\t','\n','\r',chr(127)]:
            e=entry();e['method_label']='Heat'+char+'sample';self.bad(e)
        e=entry();e['method_label']=' '*240+'x';self.bad(e)
        e=entry();e['method_label']=' '*239+'x';self.assertEqual([],p.validate_catalog({'schema':p.SCHEMA,'entries':[e]}))
    def test_bad_element_and_hub(self):
        e=entry();e['material']['elements']=['Xx'];self.bad(e)
        e=entry();e['material']['existing_hub_id']='../secret';self.bad(e)

class AnchorTests(unittest.TestCase):
    def test_ampere_literal_and_pulse_context(self):
        e=entry();e['operations'][1]['conditions'][0]={'parameter':'Activation current','reported':'750 A'};ev,t=evidence(e)
        c=next(c for c in ev['claims'] if c['pointer']=='/operations/1/conditions/0/reported')
        c['quote']='The activation pulse was 30 V/750 A for 30 s.';t[1]+=' '+c['quote']
        p.validate_claims(e,ev,t)
        self.assertFalse(p._token_in_quote('A','750 mA'))
    def test_ampere_requires_same_literal_unit_association(self):
        for source in ['Current 750 mA.','Voltage 750 V.','Voltage 750 V and current 30 A.','Current 750 mA and another current 30 A.']:
            with self.subTest(source=source):
                e=entry();e['operations'][1]['conditions'][0]={'parameter':'Activation current','reported':'750 A'};ev,t=evidence(e)
                c=next(c for c in ev['claims'] if c['pointer']=='/operations/1/conditions/0/reported');c['quote']=source;t[1]+=' '+source
                with self.assertRaises(ValueError):p.validate_claims(e,ev,t)

    def test_doi_case_is_metadata_not_seconds(self):
        e=entry();e['doi']='10.9999/s003';ev,t=evidence(e)
        claim=next(c for c in ev['claims'] if c['pointer']=='/doi');claim['quote']='DOI: 10.9999/S003';t[1]+=' '+claim['quote']
        p.validate_claims(e,ev,t)
    def test_doi_requires_complete_literal_identity(self):
        for wrong in ['DOI: 10.9999/S004','DOI: 10.9999/S0031','DOI: 110.9999/S003','10.9999/S003-appendix','10.9999/S003_extra','10.9999/S003:part2']:
            e=entry();e['doi']='10.9999/s003';ev,t=evidence(e)
            claim=next(c for c in ev['claims'] if c['pointer']=='/doi');claim['quote']=wrong;t[1]+=' '+wrong
            with self.assertRaisesRegex(ValueError,'DOI identity'):p.validate_claims(e,ev,t)
    def test_exact_all_fields(self):
        e=entry();ev,texts=evidence(e);p.validate_claims(e,ev,texts)
    def test_missing_field_and_semantic_flag(self):
        e=entry();ev,t=evidence(e);ev['claims'].pop()
        with self.assertRaisesRegex(ValueError,'missing scientific anchor'):p.validate_claims(e,ev,t)
        ev,t=evidence(e);ev['claims'][0]['semantic_link_checked']=False
        with self.assertRaisesRegex(ValueError,'semantic'):p.validate_claims(e,ev,t)
    def test_wrong_quote_or_page(self):
        e=entry();ev,t=evidence(e);ev['claims'][0]['quote']='not in text'
        with self.assertRaisesRegex(ValueError,'unmatched'):p.validate_claims(e,ev,t)
        ev,t=evidence(e);ev['claims'][0]['page']=2
        with self.assertRaisesRegex(ValueError,'pointer/page'):p.validate_claims(e,ev,t)
    def test_numeric_and_unit_tokens(self):
        e=entry();ev,t=evidence(e);c=next(c for c in ev['claims'] if c['pointer']=='/precursors/0/amount');c['value_tokens']=['1']
        with self.assertRaisesRegex(ValueError,'coverage'):p.validate_claims(e,ev,t)
        self.assertFalse(p._token_in_quote('1','10 g'));self.assertFalse(p._token_in_quote('mg','5 mmg'));self.assertTrue(p._token_in_quote('10','10 nm'))
    def test_full_long_title_is_citation_metadata(self):
        e=entry();e['title']='SYNTHETIC TITLE: '+'A long source title '*12;ev,t=evidence(e);p.validate_claims(e,ev,t)
    def test_numeric_unit_association_not_token_bag(self):
        e=entry();ev,t=evidence(e);c=next(c for c in ev['claims'] if c['pointer']=='/precursors/0/amount');c['quote']='The charge was 1 mL and the isolated mass was 10 g.';t[1]+=' '+c['quote']
        with self.assertRaisesRegex(ValueError,'association'):p.validate_claims(e,ev,t)
    def test_quantity_inequality_and_compound_unit_retained(self):
        for public,source in [('< 10 nm','The particle size is 10 nm.'),('1 mol/L','Charge 1 mol and then add 10 L.')]:
            e=entry();e['precursors'][0]['amount']=public;ev,t=evidence(e);c=next(c for c in ev['claims'] if c['pointer']=='/precursors/0/amount');c['quote']=source;t[1]+=' '+source
            with self.assertRaisesRegex(ValueError,'association'):p.validate_claims(e,ev,t)
        for value in ['1 mol/L','1 g mL-1','<= 10 nm','~ 10 nm']:
            e=entry();e['precursors'][0]['amount']=value;ev,t=evidence(e);p.validate_claims(e,ev,t)
    def test_leading_decimal_does_not_match_digit_suffix(self):
        e=entry();ev,t=evidence(e);c=next(c for c in ev['claims'] if c['pointer']=='/precursors/0/amount');c['quote']='Charge .1 g.';t[1]+=' '+c['quote']
        with self.assertRaises(ValueError):p.validate_claims(e,ev,t)
        e=entry();e['precursors'][0]['amount']='.1 g';ev,t=evidence(e);p.validate_claims(e,ev,t)
    def test_attached_unsupported_unit_fails(self):
        e=entry();e['precursors'][0]['amount']='1sccm';ev,t=evidence(e);c=next(c for c in ev['claims'] if c['pointer']=='/precursors/0/amount');c['quote']='Charge 1 g.';t[1]+=' '+c['quote']
        with self.assertRaisesRegex(ValueError,'unsupported quantity'):p.validate_claims(e,ev,t)
    def test_molar_unit_and_unknown_units(self):
        e=entry();e['precursors'][0]['amount']='1 M';ev,t=evidence(e);c=next(c for c in ev['claims'] if c['pointer']=='/precursors/0/amount');c['quote']='The charge was 1 g.';c['value_tokens']=['1'];t[1]+=' '+c['quote']
        with self.assertRaisesRegex(ValueError,'coverage'):p.validate_claims(e,ev,t)
        e=entry();e['precursors'][0]['amount']='1 furlong';ev,t=evidence(e)
        with self.assertRaisesRegex(ValueError,'unsupported quantity'):p.validate_claims(e,ev,t)
        for value in ['1 M','1 mM','< 10 nm','5–10 nm','5 to 10 nm','7 ± 1 nm']:
            e=entry();e['precursors'][0]['amount']=value;ev,t=evidence(e);p.validate_claims(e,ev,t)
    def test_editorial_long_copy_rejected_citation_retained(self):
        paragraph='This source body paragraph is copied without an authored paraphrase. '*3
        for key in ['scope','deferred','missing_fields']:
            e=entry();e[key]=[paragraph] if key!='scope' else paragraph;ev,t=evidence(e);t[1]+=' '+p.norm(paragraph)
            with self.assertRaisesRegex(ValueError,'verbatim'):p.validate_claims(e,ev,t)
        e=entry();e['citation']=paragraph;ev,t=evidence(e);t[1]+=' '+p.norm(paragraph);p.validate_claims(e,ev,t)
    def test_no_long_verbatim_public_paragraph(self):
        e=entry();e['outcome']['link_basis']='A '*100;ev,t=evidence(e)
        with self.assertRaisesRegex(ValueError,'verbatim'):p.validate_claims(e,ev,t)

def synthetic_pdf(text):
    # A minimal real one-page PDF with a text object; no external generator dependency.
    text=text.replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
    stream=('BT /F1 8 Tf 10 780 Td ('+text+') Tj ET').encode('ascii')
    objs=[b'<< /Type /Catalog /Pages 2 0 R >>',b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 10000 800] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',b'<< /Length '+str(len(stream)).encode()+b' >>\nstream\n'+stream+b'\nendstream']
    raw=b'%PDF-1.4\n';offset=[0]
    for i,obj in enumerate(objs,1):offset.append(len(raw));raw+=f'{i} 0 obj\n'.encode()+obj+b'\nendobj\n'
    start=len(raw);raw+=b'xref\n0 6\n0000000000 65535 f \n'+b''.join(f'{x:010d} 00000 n \n'.encode() for x in offset[1:]);raw+=f'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n'.encode();return raw

class LocalPdfIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.addCleanup(self.tmp.cleanup)
        try:
            import pypdf
            self.pdf_available=True
        except ImportError:self.pdf_available=False
    def fixture(self):
        e=entry();ev,texts=evidence(e);pdf=self.root/'synthetic.pdf';pdf.write_bytes(synthetic_pdf(texts[1]));e['document_sha256']=hashlib.sha256(pdf.read_bytes()).hexdigest()
        actual=p.read_pdf_pages(pdf.read_bytes(),[1])[1][1]
        page=self.root/'pages.private.json';page.write_bytes(p.packed({'schema':p.MAP_SCHEMA,'document_sha256':e['document_sha256'],'source_pages':1,'pages':[{'page':1,'text':actual}]}))
        screen=self.root/'screen.private.jsonl';screen.write_bytes(p.packed({'decision':'pass','source_sha256':e['document_sha256']}))
        # JSONL fixture is one actual line.
        screen.write_text(json.dumps({'decision':'pass','source_sha256':e['document_sha256']})+'\n')
        ev.update(schema=p.EVIDENCE_SCHEMA,source_id=e['source_id'],document={'path':str(pdf),'sha256':e['document_sha256']},screened_pass={'path':str(screen),'sha256':hashlib.sha256(screen.read_bytes()).hexdigest(),'line_number':1},identity={'doi':e['doi'],'title':e['title'],'checked':True},page_map={'path':str(page),'sha256':hashlib.sha256(page.read_bytes()).hexdigest()})
        path=self.root/(e['source_id']+'.json');path.write_bytes(p.packed(ev));e['evidence_fingerprint']=hashlib.sha256(path.read_bytes()).hexdigest();return e,path,ev
    def test_actual_pdf_and_dependency_hashes(self):
        if not self.pdf_available:self.skipTest('Local pypdf integration unavailable')
        e,path,ev=self.fixture();pins={};self.assertEqual([],p.validate_private(e,path,pins_out=pins));self.assertEqual(4,len(pins))
        Path(ev['page_map']['path']).write_text('{}');self.assertIn('dependency hash mismatch',p.validate_private(e,path)[0])
    def test_forged_map_and_actual_pdf_page_count(self):
        if not self.pdf_available:self.skipTest('Local pypdf integration unavailable')
        e,path,ev=self.fixture();page=Path(ev['page_map']['path']);m=json.loads(page.read_bytes());m['pages'][0]['text']='fabricated text';page.write_bytes(p.packed(m));ev['page_map']['sha256']=hashlib.sha256(page.read_bytes()).hexdigest();path.write_bytes(p.packed(ev));e['evidence_fingerprint']=hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertIn('differs from actual PDF',p.validate_private(e,path)[0]);e['source_pages']=2;self.assertIn('page count mismatch',p.validate_private(e,path)[0])
    def test_merge_preservation_duplicate_and_modified_candidate(self):
        if not self.pdf_available:self.skipTest('Local pypdf integration unavailable')
        e,path,ev=self.fixture();pins={};doc=p.project({'schema':p.SCHEMA,'entries':[e]},self.root,pins_out=pins);candidate=self.root/'candidate.json';candidate.write_bytes(p.packed(doc));receipt=self.root/'receipt.private.json';receipt.write_bytes(p.packed({'schema':'mattersyn-preliminary-validation/1','status':'private_anchors_verified','candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'dependencies':pins,'entries':[e['source_id']],'independent_scientific_audit':False,'accuracy':'unmeasured','training_ready':False}));base={'schema':p.SCHEMA,'entries':[]};self.assertEqual(doc,p.merge_catalog(base,[(candidate,receipt)]));self.assertEqual([],base['entries'])
        with self.assertRaisesRegex(ValueError,'duplicate'):p.merge_catalog(doc,[(candidate,receipt)])
        candidate.write_bytes(candidate.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'changed after validation'):p.merge_catalog(base,[(candidate,receipt)])

if __name__=='__main__':unittest.main()
