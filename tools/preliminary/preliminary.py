"""Local preliminary contribution checks. Mechanical anchoring is not a science audit."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import re
import shutil
import subprocess
import unicodedata
from pathlib import Path

import sys
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT/'recipe-atlas/scripts'))
from preliminary_contract import (SCHEMA, EVIDENCE_SCHEMA, MAP_SCHEMA, NUMBER, UNITS, _keys, _int, norm, source_id, validate_catalog)
validate_public = validate_catalog
import glyph_normalization as glyphs
from shared_unit_lists import coordinated_quantity_spans

def scientific_fields(e):
    """Required private anchors. Scope/deferred/missing/review fields are editorial metadata."""
    fields={'/doi':(e['doi'],e['inspected_pages']),'/title':(e['title'],e['inspected_pages']),'/material/label':(e['material']['label'],e['inspected_pages']),'/method_label':(e['method_label'],e['inspected_pages'])}
    for i,v in enumerate(e['material']['elements']):fields[f'/material/elements/{i}']=(v,e['inspected_pages'])
    for i,p in enumerate(e['precursors']):
        for key in ['name','amount','role']:
            if p[key] is not None:fields[f'/precursors/{i}/{key}']=(p[key],[l['page'] for l in p['locators']])
    for i,op in enumerate(e['operations']):
        pages=[l['page'] for l in op['locators']];fields[f'/operations/{i}/action']=(op['action'],pages)
        for j,c in enumerate(op['conditions']):
            for key in ['parameter','reported']:fields[f'/operations/{i}/conditions/{j}/{key}']=(c[key],pages)
    for key in ['sample_label','link_basis']:fields['/outcome/'+key]=(e['outcome'][key],[l['page'] for l in e['outcome']['locators']])
    for i,d in enumerate(e['outcome']['descriptors']):
        for key in ['kind','reported','technique']:fields[f'/outcome/descriptors/{i}/{key}']=(d[key],[l['page'] for l in d['locators']])
    return fields

def matching_text(text):
    # Comparison view only; source bytes, page maps and raw quotes are untouched.
    return re.sub(r'°\s+C(?![A-Za-z])', '°C', norm(text))


def _token_in_quote(token, quote):
    t=matching_text(token);q=matching_text(quote)
    if NUMBER.fullmatch(t): return t in {norm(v) for v in NUMBER.findall(q)}
    if UNITS.fullmatch(t): return t in {norm(v) for v in UNITS.findall(q)}
    return t in q

_NUM = r'[-+−]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?'
_UNIT = UNITS.pattern.removeprefix('(?<![A-Za-z])').removesuffix('(?![A-Za-z])')
_UNIT_ATOM = _UNIT+r'(?:\^?[-−]\d+|\^\d+|\d+)?'
_LITERAL_UNIT = _UNIT_ATOM+r'(?:(?:\s*/\s*|\s+)'+_UNIT_ATOM+r')*'
_QUANTITY = re.compile(r'(?<![A-Za-z0-9.])(?P<qualifier><=|>=|<|>|≤|≥|~|≈)?\s*(?P<number>'+_NUM+r'(?:\s*(?:±|\+/-|–|−|-|to)\s*'+_NUM+r')?)\s*(?P<unit>'+_LITERAL_UNIT+r')(?![A-Za-z])')

def quantity_spans(text):
    # Literal association only: no unit conversion, numerical rounding or interpretation.
    view = matching_text(text)
    standalone = {(m['qualifier'] or '',re.sub(r'\s+','',m['number']),re.sub(r'\s+','',m['unit'])) for m in _QUANTITY.finditer(view)}
    return standalone | coordinated_quantity_spans(view, _LITERAL_UNIT)

def reject_long_public_copy(entry, texts):
    def walk(value,pointer=''):
        if isinstance(value,dict):
            for k,v in value.items():walk(v,pointer+'/'+k)
        elif isinstance(value,list):
            for i,v in enumerate(value):walk(v,pointer+'/'+str(i))
        elif isinstance(value,str) and pointer not in {'/title','/doi','/citation'} and len(value)>=160 and any(norm(value) in text for text in texts.values()):
            raise ValueError('long verbatim public source passage at '+pointer)
    walk(entry)

def validate_claims(entry, ev, texts, *, glyph_context=None):
    required=scientific_fields(entry);covered={p:[] for p in required};checked_quotes={p:[] for p in required}
    if not isinstance(ev['claims'],list):raise ValueError('claims must be a list')
    for claim in ev['claims']:
        if not _keys(claim,'pointer page quote value_tokens semantic_link_checked'):raise ValueError('claim keys invalid')
        ptr=claim['pointer'];page=claim['page']
        if ptr not in required or not _int(page) or page not in required[ptr][1] or page not in texts:raise ValueError('claim pointer/page not in scientific field locators')
        quote=claim['quote']
        if not isinstance(quote,str) or not 1<=len(quote)<=4000 or not norm(quote) or norm(quote) not in texts[page]:raise ValueError('unmatched exact normalized quote at '+ptr)
        quote=glyphs.quote(quote,page,glyph_context)
        checked_quotes[ptr].append(quote)
        if claim['semantic_link_checked'] is not True:raise ValueError('author semantic link check missing at '+ptr)
        tokens=claim['value_tokens']
        if ptr=='/doi':
            if not isinstance(tokens,list) or len(tokens)>128 or not all(isinstance(t,str) and 0<len(t)<=80 for t in tokens):raise ValueError('DOI token list malformed')
            # DOI identifiers are case-insensitive metadata, never physical quantities.
            identifiers=re.findall(r'(?<![A-Za-z0-9./])10\.\d{4,9}/[^\s<>"\\?#]+',norm(quote),re.IGNORECASE)
            if entry['doi'].casefold() not in {v.casefold() for v in identifiers}:raise ValueError('literal DOI identity missing from source quote')
            covered[ptr].append(entry['doi'])
            continue
        if not isinstance(tokens,list) or len(tokens)>128 or not all(isinstance(t,str) and 0<len(t)<=80 and _token_in_quote(t, quote) for t in tokens):raise ValueError('source-value token not in quote at '+ptr)
        covered[ptr].extend(matching_text(t) for t in tokens)
    for ptr,(value,_) in required.items():
        claims=[c for c in ev['claims'] if c['pointer']==ptr]
        if not claims:raise ValueError('missing scientific anchor: '+ptr)
        if ptr=='/doi':continue
        wanted={norm(t) for t in NUMBER.findall(matching_text(value))+UNITS.findall(matching_text(value))}
        if not wanted.issubset(set(covered[ptr])):raise ValueError('numeric/unit token coverage incomplete at '+ptr)
        reported=quantity_spans(value)
        quoted=set().union(*(quantity_spans(q) for q in checked_quotes[ptr]))
        if not reported.issubset(quoted):raise ValueError('literal numeric-unit association missing at '+ptr)
        # Numeric followed by an unknown unit-like word in a quantity field is a hold,
        # not implicit support from an unrelated number elsewhere in the quote.
        if ptr.endswith(('/amount','/reported')):
            for m in re.finditer(r'(?<![A-Za-z0-9.])'+_NUM+r'\s*((?:[^\W\d_]|°)+)',matching_text(value)):
                word=m.group(1)
                if not UNITS.fullmatch(word) and word.lower() not in {'and','to','or','at','by','with','of','in','as','after','before','for','is','was','reported','approximately'}:
                    raise ValueError('unsupported quantity unit association at '+ptr)
    reject_long_public_copy(entry,glyphs.copy_check_texts(texts,glyph_context))

def read_pdf_pages(raw, pages):
    try:
        from pypdf import PdfReader
        from io import BytesIO
    except ImportError as exc:
        raise ValueError('Private projection requires local pypdf; public validation does not') from exc
    try:
        document=PdfReader(BytesIO(raw), strict=True)
        return len(document.pages), {page:norm(document.pages[page-1].extract_text() or '') for page in pages if 1<=page<=len(document.pages)}
    except Exception as exc:
        raise ValueError('Local PDF parsing failed: '+type(exc).__name__) from exc

def validate_private(entry, evidence_path, *, pins_out=None):
    """Read and hash actual dependencies, verify source pages and each private claim.

    Returns errors. A positive semantic flag is the author's check, never independent audit.
    Text-less/scanned pages are held in v1 rather than accepted through invented OCR receipts.
    """
    errors=[];evidence_path=Path(evidence_path);pins={}
    def load(path, expected=None):
        raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest();pins[path]=digest
        if expected is not None and digest!=expected:raise ValueError('dependency hash mismatch: '+path.name)
        return raw
    def resolve(value):
        p=Path(value);return p if p.is_absolute() else evidence_path.parent/p
    try:
        raw=load(evidence_path,entry['evidence_fingerprint']);ev=json.loads(raw)
        if not isinstance(ev,dict) or set(ev) not in [set('schema source_id document screened_pass identity page_map claims'.split()),set('schema source_id document screened_pass identity page_map claims glyph_normalization'.split())] or ev['schema']!=EVIDENCE_SCHEMA or ev['source_id']!=entry['source_id']:raise ValueError('invalid private evidence identity/keys')
        if not _keys(ev['identity'],'doi title checked') or ev['identity'].get('checked') is not True or ev['identity']!={'doi':entry['doi'],'title':entry['title'],'checked':True}:raise ValueError('source identity check missing/mismatched')
        for key in ['document','page_map']:
            if not _keys(ev[key],'path sha256'):raise ValueError(key+' private pin malformed')
        if ev['document']['sha256']!=entry['document_sha256']:raise ValueError('document hash differs from public entry')
        pdf=resolve(ev['document']['path']);pdfraw=load(pdf,ev['document']['sha256'])
        if not pdfraw.startswith(b'%PDF-'):raise ValueError('source is not a PDF')
        page_count,actual_pages=read_pdf_pages(pdfraw,entry['inspected_pages'])
        if page_count!=entry['source_pages']:raise ValueError('actual PDF page count mismatch')
        screen=ev['screened_pass']
        if not _keys(screen,'path sha256 line_number') or not _int(screen['line_number']) or screen['line_number']<1:raise ValueError('screened-pass pin malformed')
        lines=load(resolve(screen['path']),screen['sha256']).decode('utf-8-sig').splitlines();row=json.loads(lines[screen['line_number']-1])
        if row.get('decision')!='pass' or row.get('source_sha256')!=entry['document_sha256']:raise ValueError('actual screening row is not a pass for this PDF')
        pm=json.loads(load(resolve(ev['page_map']['path']),ev['page_map']['sha256']))
        if not _keys(pm,'schema document_sha256 source_pages pages') or pm['schema']!=MAP_SCHEMA or pm['document_sha256']!=entry['document_sha256'] or pm['source_pages']!=entry['source_pages']:raise ValueError('page-map source identity mismatch')
        if not isinstance(pm['pages'],list):raise ValueError('page-map pages must be a list')
        texts={}
        for page in pm['pages']:
            if not _keys(page,'page text') or not _int(page['page']) or page['page'] in texts or page['page'] not in entry['inspected_pages'] or not isinstance(page['text'],str):raise ValueError('invalid/duplicate page map row')
            texts[page['page']]=norm(page['text'])
        if set(texts)!=set(entry['inspected_pages']):raise ValueError('inspected pages must equal pinned page-map pages')
        for page,text in texts.items():
            if not text or actual_pages.get(page)!=text:raise ValueError('page '+str(page)+' text differs from actual PDF extraction; scanned/OCR-only pages require a later supported workflow')
        glyph_context=glyphs.prepare(ev['glyph_normalization'],entry,pdfraw,texts,resolve,load) if 'glyph_normalization' in ev else None
        validate_claims(entry, ev, texts, glyph_context=glyph_context)
        for path,digest in pins.items():
            if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('dependency changed during validation: '+path.name)
    except (OSError,ValueError,TypeError,KeyError,IndexError,subprocess.SubprocessError) as exc:
        errors.append(str(exc))
    if not errors and pins_out is not None: pins_out.update({str(p.resolve()):h for p,h in pins.items()})
    return errors

def project(document, evidence_dir, *, pins_out=None):
    """Project only after all public and private checks pass. No partial output."""
    result=copy.deepcopy(document)
    if not isinstance(result,dict) or not isinstance(result.get('entries'),list):raise ValueError('invalid candidate envelope')
    for e in result['entries']:
        if not isinstance(e,dict) or 'evidence_fingerprint' not in e or not isinstance(e.get('doi'),str) or e.get('source_id')!=source_id(e['doi']):raise ValueError('candidate DOI/source ID and fingerprint key must already be explicit and canonical')
        path=Path(evidence_dir)/(e['source_id']+'.json');e['evidence_fingerprint']=hashlib.sha256(path.read_bytes()).hexdigest()
    errors=validate_public(result)
    if not errors:
        for e in result['entries']:errors.extend(e['source_id']+': '+x for x in validate_private(e,Path(evidence_dir)/(e['source_id']+'.json'),pins_out=pins_out))
    if errors:raise ValueError('\n'.join(errors))
    return result

def packed(document):
    return (json.dumps(document,ensure_ascii=False,indent=2)+'\n').encode('utf-8')

def merge_catalog(base, candidates):
    """Append validated candidates without changing any prior entry or scientific field.

    candidates is a sequence of (public candidate path, private validation receipt path).
    Receipts are mechanical local validation results, not independently audited approvals.
    """
    errors=validate_catalog(base)
    if errors:raise ValueError('\n'.join(errors))
    result=copy.deepcopy(base)
    for candidate_path,receipt_path in candidates:
        raw=Path(candidate_path).read_bytes();doc=json.loads(raw);r=json.loads(Path(receipt_path).read_bytes())
        if not _keys(r,'schema status candidate_sha256 dependencies entries independent_scientific_audit accuracy training_ready') or r['schema']!='mattersyn-preliminary-validation/1' or r['status']!='private_anchors_verified' or r['independent_scientific_audit'] is not False or r['accuracy']!='unmeasured' or r['training_ready'] is not False:raise ValueError('invalid mechanical validation receipt')
        if r['candidate_sha256']!=hashlib.sha256(raw).hexdigest():raise ValueError('candidate changed after validation')
        errors=validate_catalog(doc)
        if errors:raise ValueError('\n'.join(errors))
        if r['entries']!=[e['source_id'] for e in doc['entries']]:raise ValueError('receipt source membership mismatch')
        if not isinstance(r['dependencies'],dict) or (doc['entries'] and len(r['dependencies'])<4):raise ValueError('missing private evidence dependency pins')
        if any(e['evidence_fingerprint'] not in r['dependencies'].values() or e['document_sha256'] not in r['dependencies'].values() for e in doc['entries']):raise ValueError('candidate identity not bound to evidence dependencies')
        for path,digest in r['dependencies'].items():
            if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest:raise ValueError('evidence dependency changed after validation')
        result['entries'].extend(doc['entries'])
    errors=validate_catalog(result)
    if errors:raise ValueError('\n'.join(errors))
    assert result['entries'][:len(base['entries'])]==base['entries']
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='command',required=True)
    p=sub.add_parser('validate-public');p.add_argument('input',type=Path)
    p=sub.add_parser('project');p.add_argument('input',type=Path);p.add_argument('--evidence-dir',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--receipt',required=True,type=Path)
    p=sub.add_parser('merge');p.add_argument('input',type=Path,help='Existing public catalog');p.add_argument('--candidate',action='append',required=True,type=Path);p.add_argument('--validation',action='append',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=ap.parse_args()
    try:
        doc=json.loads(a.input.read_bytes())
        if a.command=='validate-public':
            errors=validate_public(doc)
            if errors:raise ValueError('\n'.join(errors))
            print(json.dumps({'status':'public_schema_valid','entries':len(doc['entries']),'independent_scientific_audit':False}))
        elif a.command=='project':
            if a.output.exists():raise ValueError('output already exists; choose a new candidate path')
            if a.receipt.exists():raise ValueError('receipt already exists; choose a new private receipt path')
            pins={};result=project(doc,a.evidence_dir,pins_out=pins);raw=packed(result)
            receipt={'schema':'mattersyn-preliminary-validation/1','status':'private_anchors_verified','candidate_sha256':hashlib.sha256(raw).hexdigest(),'dependencies':pins,'entries':[e['source_id'] for e in result['entries']],'independent_scientific_audit':False,'accuracy':'unmeasured','training_ready':False}
            with a.output.open('xb') as f:f.write(raw)
            with a.receipt.open('xb') as f:f.write(packed(receipt))
            print(json.dumps({'status':'private_anchors_verified_public_candidate_written','entries':len(result['entries']),'independent_scientific_audit':False,'accuracy':'unmeasured','training_ready':False}))
        else:
            if len(a.candidate)!=len(a.validation):raise ValueError('candidate/validation arguments must pair in order')
            if a.output.exists():raise ValueError('output exists; choose a new catalog path')
            result=merge_catalog(doc,zip(a.candidate,a.validation))
            with a.output.open('xb') as f:f.write(packed(result))
            print(json.dumps({'status':'merged','preliminary_sources':len(result['entries']),'gold_counts_changed':False}))
    except (OSError,ValueError) as exc:ap.exit(1,str(exc)+'\n')

if __name__=='__main__':main()
