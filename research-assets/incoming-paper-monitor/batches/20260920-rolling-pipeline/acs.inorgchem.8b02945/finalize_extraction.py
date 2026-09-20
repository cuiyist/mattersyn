"""Validate and freeze this private author extraction; never alter an existing freeze."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, math, re
from decimal import Decimal
from PIL import Image
from pypdf import PdfReader
import pypdfium2 as pdfium

P = Path(__file__).resolve().parent
SID = 'friedfeld2019'
AUTHOR = '/root/peng1998_reader_assets'
assert not (P / 'package-freeze.json').exists(), 'Frozen package must be versioned, not overwritten.'
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(name): return json.loads((P / name).read_text(encoding='utf-8-sig'))
def save(name, data): (P / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
checks = []
def check(label, passed):
    checks.append({'check': label, 'passed': bool(passed)})
    if not passed: raise AssertionError(label)
def walk(obj, path=''):
    yield path, obj
    if isinstance(obj, dict):
        for key, value in obj.items(): yield from walk(value, path + '/' + key.replace('~', '~0').replace('/', '~1'))
    elif isinstance(obj, list):
        for i, value in enumerate(obj): yield from walk(value, path + '/' + str(i))
def pointer(obj, path):
    for token in path.split('/')[1:]:
        token = token.replace('~1', '/').replace('~0', '~')
        obj = obj[int(token)] if isinstance(obj, list) else obj[token]
    return obj

prep = read('source-preparation.json')
docs = {d['role']: d for d in prep['documents']}
sf = read('source-facts.json'); inv = read('source-inventory.json')
tables = read('source-tables.json'); coverage = read('page-coverage.json')
assets = read('original-assets-manifest.json')
identity = read('intake-identity.json')
check('intake manifest exact hash', sha(prep['intake_manifest']['path']) == prep['intake_manifest']['sha256'])
check('source generation', prep['source_generation'] == identity['source_generation'] == sf['source_generation'] == 1)
check('intake bundle', prep['bundle_sha256'] == sf['bundle_sha256'] == identity['bundle_sha256'] == 'b13b449fbf4cab06f886ab37ee5e9051844453c5481dd533ab36a1869b78fdde')
for role, d in docs.items():
    check(role + ' unchanged original hash', sha(d['source_path']) == d['sha256'])
    check(role + ' detected PDF', Path(d['source_path']).read_bytes().startswith(b'%PDF-'))
    check(role + ' actual page count', len(PdfReader(d['source_path']).pages) == d['page_count'] == (8 if role == 'main' else 25))
check('title/author/DOI identity', sf['title'] == identity['title'] == 'Conversion of InP Clusters to Quantum Dots' and sf['authors'] == identity['authors'] == ['Max R. Friedfeld', 'Dane A. Johnson', 'Brandi M. Cossairt'] and identity['doi'] == '10.1021/acs.inorgchem.8b02945')
check('recipe present with evidence', identity['recipe_present'] is True and len(identity['recipe_evidence']) == 2)
expected = {'semantic_units':207, 'facts':65, 'materials':39, 'stocks':5, 'stock_components':10, 'protocols':16, 'operations':34, 'sample_contexts':62, 'figures':44, 'schemes':2, 'tables_or_numeric_listings':6, 'table_numeric_cells':185, 'equations':31, 'references':56, 'original_crops':51}
check('expected inventory counts', inv['counts'] == expected)
for key in ['facts','materials','stocks','protocols','sample_contexts','figures','schemes','equations','references']:
    check(key + ' actual count', len(sf[key]) == expected[key])
    check(key + ' unique identifiers', len({x['id'] for x in sf[key]}) == len(sf[key]))
check('34 actual operations', sum(len(p['operations']) for p in sf['protocols']) == 34)
check('153 primary fact quantities', sum(len(f['quantities']) for f in sf['facts']) == 153)
check('all 56 references in source order', [x['number'] for x in sf['references']] == list(range(1,57)))
check('all main and SI figure identifiers', {x['id'] for x in sf['figures']} == {f'figure-{i}' for i in range(1,6)} | {f'figure-s{i}' for i in range(1,40)})
facts = {x['id']:x for x in sf['facts']}; samples = {x['id'] for x in sf['sample_contexts']}; materials = {x['id'] for x in sf['materials']}
for i, obj in walk(sf):
    if not isinstance(obj, dict): continue
    if 'source_fact_ids' in obj:
        for f in obj['source_fact_ids']: check('fact reference ' + i + ' ' + f, f in facts)
    if 'material_id' in obj: check('stock material ' + i, obj['material_id'] in materials)
    if 'sample_context_ids' in obj:
        for s in obj['sample_context_ids']: check('figure sample ' + i + ' ' + s, s in samples)
    if 'sample_ids' in obj:
        for s in obj['sample_ids']: check('protocol sample ' + i + ' ' + s, s in samples)
    if 'atomic_structure_supplied' in obj: check('no supplied atomistic model ' + i, obj['atomic_structure_supplied'] is False)
for name, obj in [('source-facts.json',sf),('source-tables.json',tables),('source-inventory.json',inv),('original-assets-manifest.json',assets),('intake-identity.json',identity)]:
    for path, item in walk(obj):
        if not isinstance(item,dict): continue
        if all(k in item for k in ['document_role','source_sha256','pdf_page','locator']):
            d=docs[item['document_role']]
            check(name + path + ' source evidence', item['source_sha256']==d['sha256'] and 1 <= item['pdf_page'] <= d['page_count'] and bool(item['locator']))
        if all(k in item for k in ['raw_text','value','unit','comparison','range','status']):
            check(name + path + ' raw/unit retained', isinstance(item['raw_text'],str) and bool(item['raw_text']) and bool(item['unit']))
            if item['value'] is not None:
                check(name + path + ' finite number', isinstance(item['value'],(int,float)) and math.isfinite(item['value']))
                token=item['raw_text'].replace('−','-').replace(' × 10','e').replace('×10','e').replace('^','').lstrip('~')
                token=re.sub(r'^(<=|>=|<|>)','',token)
                check(name + path + ' exact parsed raw', float(Decimal(token)) == item['value'])
            if item['range'] is not None:
                check(name + path + ' range preserves ordered source endpoints', sorted(item['ordered_endpoints']) == [item['range']['min'],item['range']['max']])
            check(name + path + ' bound qualification', item['comparison'] in [None,'<','>','<=','>='])
            check(name + path + ' evidence retained', bool(item['evidence']))
check('12 explicit source conflicts and 6 gaps', len(sf['conflicts'])==12 and len(sf['missingness'])==6)
check('no independent/training approval', sf['independent_audit_status']=='pending' and sf['training_eligibility'] is False)
check('raw complete text stays private', inv['public_source_text_allowed'] is False and inv['private_payload_path'].startswith('source-render/'))
payload = read(inv['private_payload_path'])
check('all 33 private source payloads', len(payload['pages'])==33 and payload['public_export_allowed'] is False)
payload_ids={x['id'] for x in payload['pages']}
check('207 unique semantic units', len(inv['units'])==207 and inv['units']==inv['semantic_units'] and len({u['id'] for u in inv['units']})==207)
for unit in inv['units']:
    check(unit['id']+' evidence', bool(unit['evidence']))
    for pid in unit['source_payload_ids']: check(unit['id']+' private payload '+pid, pid in payload_ids)
    for target in unit['extraction_targets']:
        data=read(target['file'])
        if 'json_pointer' in target: check(unit['id']+' target pointer', pointer(data,target['json_pointer']) is not None)
        if 'asset_id' in target: check(unit['id']+' target asset', any(a['id']==target['asset_id'] for a in data['assets']))
        if 'private_payload_id' in target: check(unit['id']+' private target', target['private_payload_id'] in payload_ids)
for table in tables['tables']:
    cells=[c for row in table['rows'] for c in row['cells']]
    check(table['id']+' all numeric cells retained', table['cell_count']==table['numeric_cell_count']==len(cells))
check('185 exact numeric-listing cells', sum(t['cell_count'] for t in tables['tables'])==tables['total_numeric_cells']==185)
check('all 33 pages actually read and inspected', len(coverage['pages'])==coverage['actual_text_pages_read']==coverage['actual_visual_pages_inspected']==33)
for page in coverage['pages']:
    label=page['document_role']+str(page['pdf_page'])
    check(label+' actual reading coverage', page['text_read'] is True and page['visual_review'] is True and bool(page['source_unit_ids']))
    check(label+' original text cache unchanged', sha(page['text_path'])==page['text_sha256'])
    check(label+' original page render unchanged', sha(page['render_path'])==page['render_sha256'])

# Pixel replay is an author rendering check, separate from the recorded actual visual reading.
render_cache={}
for a in assets['assets']:
    check(a['id']+' original crop hash', sha(a['path'])==a['sha256'])
    key=(a['document_role'],a['pdf_page'])
    if key not in render_cache:
        doc=pdfium.PdfDocument(docs[key[0]]['source_path']);page=doc[key[1]-1]
        render_cache[key]=page.render(scale=a['render_dpi']/72).to_pil().convert('RGB')
        page.close();doc.close()
    full=render_cache[key];current=Image.open(a['path']).convert('RGB')
    check(a['id']+' render size', list(full.size)==a['rendered_page_dimensions'])
    bounds=a['crop_box_render_pixels'];box=a['crop_box_normalized']
    check(a['id']+' exact rectangular bounds', bounds==[round(box[0]*full.width),round(box[1]*full.height),round(box[2]*full.width),round(box[3]*full.height)])
    check(a['id']+' fresh PDFium pixel equality', full.crop(tuple(bounds)).tobytes()==current.tobytes())
    check(a['id']+' source snippet only', a['contains_complete_source_page'] is False and (bounds[2]-bounds[0])*(bounds[3]-bounds[1])<full.width*full.height and a['publication_approved'] is False)
    check(a['id']+' exact sample contexts', all(s in samples for s in a['sample_context_ids']))

native_reviewed=['figure-s36','figure-s37','acid-preparation','s38-fit-boxes','s39-fit-boxes']
visual={
    'schema':'mattersyn-author-visual-review/1','source_id':SID,'author':AUTHOR,
    'status':'author_checked_pending_independent_audit','source_pages_actually_read':{'main':list(range(1,9)),'si':list(range(1,26))},
    'source_pages_actually_visually_inspected':{'main':list(range(1,9)),'si':list(range(1,26))},
    'all_51_selected_crops_actually_viewed_on_contact_sheets':True,
    'contact_sheets':[{'path':str(p),'sha256':sha(p)} for p in sorted((P/'source-render/crop-contacts').glob('*.png'))],
    'native_final_crop_rechecks':native_reviewed,
    'scope_note':'All 33 source pages were read in text and actual images. All 51 selected crops were inspected on nine contact sheets. Small Gaussian fit boxes were additionally read at native crop resolution. Final S36/S37 split and acid-preparation crop were reopened after final crop-boundary adjustments. This does not claim 51 individual native-window inspections.',
    'pixel_render_replay_count':51,'independent_audit_claim':False,
    'crop_hashes':{a['object_id']:a['sha256'] for a in assets['assets']}}
save('author-visual-review.json',visual)
for a in assets['assets']:
    a['author_visual_inspection']='passed_author_contact_sheet_review'
    a['author_review_receipt']='author-visual-review.json'
    if a['object_id'] in native_reviewed:a['additional_native_crop_inspection']=True
assets['asset_review_scope']='All 51 selected crops actually viewed in nine contact sheets; five listed final crops additionally reopened natively. All 33 original pages read/viewed. Exact scope in author-visual-review.json; independent audit pending.'
save('original-assets-manifest.json',assets)
validation={'schema':'mattersyn-source-author-validation/1','source_id':SID,'author':AUTHOR,'at':datetime.now(timezone.utc).isoformat(),'status':'passed_author_checks','independent_audit_status':'pending','supporting_check_count':len(checks),'passed_checks':sum(c['passed'] for c in checks),'failed_checks':0,'counts':expected,'fact_quantities':153,'checks':checks,'limitations':['Mechanical checks support author transport and source provenance; they are not independent scientific verification.','No curve digitization, refitting, molecular model, current product atomic coordinates, canonical record or training approval.']}
save('author-validation.json',validation)
own_names=['prepare_sources.py','source-preparation.json','source_author_data.py','source_numeric_data.py','inspect_crop_layout.py','build_extraction.py','finalize_extraction.py','reading-checkpoint.md','extraction-notes.md','intake-identity.json','source-facts.json','source-tables.json','source-inventory.json','page-coverage.json','original-assets-manifest.json','author-visual-review.json','author-validation.json']
files=[P/n for n in own_names]
files += sorted(p for p in (P/'source-render').rglob('*') if p.is_file())
files += sorted(p for p in (P/'reader-assets').rglob('*') if p.is_file())
check('explicit own-file freeze set exists', all(p.is_file() for p in files))
bound={p.relative_to(P).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in files}
freeze={'schema':'mattersyn-source-extraction-freeze/1','source_id':SID,'author':AUTHOR,'revision':1,'created_at':datetime.now(timezone.utc).isoformat(),'status':'immutable_author_proposal_pending_independent_source_audit','source_generation':1,'bundle_sha256':prep['bundle_sha256'],'intake_manifest':prep['intake_manifest'],'source_files':{d['source_path']:d['sha256'] for d in docs.values()},'bound_files':bound,'bound_file_count':len(bound),'counts':expected,'fact_quantities':153,'author_validation_sha256':sha(P/'author-validation.json'),'independent_audit_status':'pending','all_scientific_training_and_publication_gates':False,'private_source_policy':'Original PDFs and source-render full-page text/images remain local. Reader-assets are selected excerpt candidates only and not approved for publication. Other workers\u2019 canonical/audit files are outside this author freeze.'}
save('package-freeze.json',freeze)
print(json.dumps({'freeze_sha256':sha(P/'package-freeze.json'),'source_facts_sha256':sha(P/'source-facts.json'),'source_inventory_sha256':sha(P/'source-inventory.json'),'bound_file_count':len(bound),'checks':len(validation['checks']),'counts':expected},indent=2))
