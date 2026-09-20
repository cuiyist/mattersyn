"""Author provenance, numerical transport and rendering checks; then immutable freeze."""
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal
import json,hashlib,math,re,logging
from pypdf import PdfReader
import pypdfium2 as pdfium
from PIL import Image
logging.getLogger('pypdf').setLevel(logging.ERROR)
P=Path(__file__).resolve().parent;SID='sasongko2025';AUTHOR='/root/peng1998_reader_assets'
assert not(P/'package-freeze.json').exists(),'Version frozen corrections rather than overwriting.'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(n):return json.loads((P/n).read_text(encoding='utf-8-sig'))
def save(n,x):(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
checks=[]
def check(label,ok):
    checks.append({'check':label,'passed':bool(ok)})
    if not ok:raise AssertionError(label)
def walk(o,path=''):
    yield path,o
    if isinstance(o,dict):
        for k,v in o.items():yield from walk(v,path+'/'+k.replace('~','~0').replace('/','~1'))
    if isinstance(o,list):
        for i,v in enumerate(o):yield from walk(v,path+'/'+str(i))
def ptr(o,p):
    for part in p.split('/')[1:]:
        part=part.replace('~1','/').replace('~0','~');o=o[int(part)]if isinstance(o,list)else o[part]
    return o
prep=read('source-preparation.json');docs={d['role']:d for d in prep['documents']};sf=read('source-facts.json');iv=read('source-inventory.json');tab=read('source-tables.json');cov=read('page-coverage.json');am=read('original-assets-manifest.json');identity=read('intake-identity.json')
check('intake hash',sha(prep['intake_manifest']['path'])==prep['intake_manifest']['sha256'])
check('generation1 exact intake bundle',prep['source_generation']==sf['source_generation']==1 and sf['bundle_sha256']==identity['bundle_sha256']==prep['bundle_sha256']=='60981509bcd71286c99c1795e7ef6eb803310e24d22bbb9f7a26299f10b427ab')
expected={'semantic_units':157,'facts':48,'materials':13,'stocks':4,'stock_components':9,'protocols':9,'operations':21,'sample_contexts':33,'figures':8,'schemes':1,'tables_or_numeric_listings':6,'table_cells':121,'table_numeric_cells':97,'equations':2,'references':89,'original_crops':17}
check('frozen expected counts',iv['counts']==expected)
for role,d in docs.items():
    check(role+' original bytes unchanged',sha(d['source_path'])==d['sha256'])
    check(role+' real PDF',Path(d['source_path']).read_bytes().startswith(b'%PDF-'))
    check(role+' actual page count',len(PdfReader(d['source_path']).pages)==d['page_count']==(9 if role=='main' else 11))
check('actual paired title/authors',identity['title']==sf['title'] and identity['authors']==sf['authors'] and len(sf['authors'])==7 and identity['year']==2025)
check('recipe supported',identity['recipe_present']is True and identity['recipe_evidence'][0]['document_role']=='si' and identity['recipe_evidence'][0]['pdf_page']==3)
for key in ['facts','materials','stocks','protocols','sample_contexts','figures','schemes','equations','references']:
    check(key+' count',len(sf[key])==expected[key]);check(key+' unique IDs',len({x['id']for x in sf[key]})==len(sf[key]))
check('21 operations',sum(len(x['operations'])for x in sf['protocols'])==21)
check('100 primary typed fact quantities',sum(len(x['quantities'])for x in sf['facts'])==100)
check('source conflicts and gaps',len(sf['conflicts'])==5 and len(sf['missingness'])==6)
check('all figure IDs',{f['id']for f in sf['figures']}=={f'figure-{i}'for i in range(1,6)}|{f'figure-s{i}'for i in range(1,4)})
for role,n in [('main',74),('si',15)]:check(role+' references complete', [r['number']for r in sf['references']if r['document_role']==role]==list(range(1,n+1)))
fids={f['id']for f in sf['facts']};mids={m['id']for m in sf['materials']};sids={s['id']for s in sf['sample_contexts']};rids={r['id']for r in sf['references']}
for name,data in [('source-facts.json',sf),('source-tables.json',tab),('source-inventory.json',iv),('original-assets-manifest.json',am),('intake-identity.json',identity)]:
    for path,x in walk(data):
        if not isinstance(x,dict):continue
        if 'source_fact_ids'in x:
            for fid in x['source_fact_ids']:check(name+path+' fact '+fid,fid in fids)
        if 'material_id'in x:check(name+path+' stock material',x['material_id']in mids)
        for key in ['sample_ids','sample_context_ids']:
            if key in x:
                for sid in x[key]:check(name+path+' sample '+sid,sid in sids)
        if x.get('reference_id'):check(name+path+' reference',x['reference_id']in rids)
        if all(k in x for k in ['document_role','source_sha256','pdf_page','locator']):
            d=docs[x['document_role']];check(name+path+' source evidence',x['source_sha256']==d['sha256']and 1<=x['pdf_page']<=d['page_count']and bool(x['locator']))
        if all(k in x for k in ['raw_text','value','range','unit','comparison','status']):
            check(name+path+' source raw token',isinstance(x['raw_text'],str)and(bool(x['raw_text'])or x['status']=='missing'))
            check(name+path+' unit/qualification',bool(x['unit'])and x['comparison']in[None,'<','>','<=','>=']and bool(x['evidence']))
            if x['value']is not None:
                token=x['raw_text'].replace('−','-').replace(' × 10','e').replace('×10','e').replace('^','').lstrip('~');token=re.sub(r'^(<=|>=|<|>)','',token).split('±')[0].strip()
                check(name+path+' exact finite parsed number',math.isfinite(x['value'])and float(Decimal(token))==x['value'])
            if x['range']is not None:check(name+path+' ordered source interval',sorted(x['ordered_endpoints'])==[x['range']['min'],x['range']['max']])
            if x['uncertainty']is not None:check(name+path+' exact undefined ± statistic',float(Decimal(x['raw_text'].split('±')[1].strip()))==x['uncertainty']['value']and'unreported'in x['uncertainty']['kind'])
            if x['status']=='missing':check(name+path+' blank not zero',x['value']is None and x['range']is None)
check('no training admission',sf['training_eligibility']is False and all(s['atomic_structure_supplied']is False for s in sf['sample_contexts']))
check('audit still pending',sf['independent_audit_status']=='pending')
check('private complete-source policy',iv['public_source_text_allowed']is False and iv['private_payload_path'].startswith('source-render/'))
payload=read(iv['private_payload_path']);pids={p['id']for p in payload['pages']}
check('20 complete private payloads',len(payload['pages'])==20 and payload['public_export_allowed']is False)
check('157 unique semantic units',len(iv['units'])==157 and iv['units']==iv['semantic_units'] and len({u['id']for u in iv['units']})==157)
for u in iv['units']:
    check(u['id']+' mapped evidence',bool(u['evidence'])and all(p in pids for p in u['source_payload_ids']))
    for t in u['extraction_targets']:
        data=read(t['file'])
        if'json_pointer'in t:check(u['id']+' pointer resolves',ptr(data,t['json_pointer'])is not None)
        if'asset_id'in t:check(u['id']+' asset exists',any(a['id']==t['asset_id']for a in data['assets']))
        if'private_payload_id'in t:check(u['id']+' private page target',t['private_payload_id']in pids)
check('all20 actual page reads/views',len(cov['pages'])==cov['actual_text_pages_read']==cov['actual_visual_pages_inspected']==20)
for p in cov['pages']:
    label=p['document_role']+str(p['pdf_page'])
    check(label+' actual coverage',p['text_read']is True and p['visual_review']is True and bool(p['source_unit_ids']))
    check(label+' cached text exact',sha(p['text_path'])==p['text_sha256']);check(label+' cached render exact',sha(p['render_path'])==p['render_sha256'])
check('121 total cells/97 numeric',tab['total_cells']==121 and tab['total_numeric_cells']==97 and sum(t['cell_count']for t in tab['tables'])==121 and sum(t['numeric_cell_count']for t in tab['tables'])==97)
t=next(x for x in tab['tables']if x['id']=='table-s1')
check('TableS1 all55 cells',len(t['rows'])==11 and t['cell_count']==55 and all(len(r['cells'])==5 for r in t['rows']))
check('TableS1 two blank beta-alpha values',[(i+1,j+1)for i,r in enumerate(t['rows'])for j,c in enumerate(r['cells'])if c['status']=='missing']==[(8,4),(9,4)])
check('TableS1 six embedded quantities',sum(len(r['additional_quantities'])for r in t['rows'])==tab['additional_sample_cell_quantities']==6)
check('final asset directory exactly allowlisted',{str(p)for p in(P/'reader-assets').glob('*.png')}=={a['path']for a in am['assets']})
rasters={}
for a in am['assets']:
    check(a['id']+' hash',sha(a['path'])==a['sha256'])
    key=(a['document_role'],a['pdf_page'])
    if key not in rasters:
        d=pdfium.PdfDocument(docs[key[0]]['source_path']);page=d[key[1]-1];rasters[key]=page.render(scale=a['render_dpi']/72).to_pil().convert('RGB');page.close();d.close()
    full=rasters[key];im=Image.open(a['path']).convert('RGB');b=a['crop_box_render_pixels'];box=a['crop_box_normalized']
    check(a['id']+' actual dimensions',list(im.size)==a['pixel_dimensions']and list(full.size)==a['rendered_page_dimensions'])
    check(a['id']+' exact crop bounds',b==[round(box[0]*full.width),round(box[1]*full.height),round(box[2]*full.width),round(box[3]*full.height)])
    check(a['id']+' full fresh pixel replay',im.tobytes()==full.crop(tuple(b)).tobytes())
    check(a['id']+' not public fullpage',a['contains_complete_source_page']is False and a['publication_approved']is False and im.size!=full.size)
native=['graphical-abstract','raman-context','table-s1','characterization-equation']
visual={'schema':'mattersyn-author-visual-review/1','source_id':SID,'author':AUTHOR,'status':'author_checked_pending_independent_audit','source_text_pages_actually_read':{'main':list(range(1,10)),'si':list(range(1,12))},'source_image_pages_actually_inspected':{'main':list(range(1,10)),'si':list(range(1,12))},'selected_crop_count':17,'all_selected_crops_actually_inspected_in_contact_sheets':True,'final_native_crop_rechecks':native,'contact_sheets':[{'path':str(p),'sha256':sha(p)}for p in sorted((P/'source-render/crop-contacts').glob('*.png'))],'scope_note':'All20 original pages read/viewed. All final crop content inspected in contact sheets; four named final crops also opened natively. A broader Raman excerpt was narrowed and its final native pixels inspected. Removed continuation crop stays privately archived and is excluded from final assets. No claim that17 native windows were opened.','fresh_pdfium_pixel_replays':17,'independent_audit_claim':False,'crop_hashes':{a['object_id']:a['sha256']for a in am['assets']}}
save('author-visual-review.json',visual)
for a in am['assets']:
    a.update(author_visual_inspection='passed_author_contact_review',author_review_receipt='author-visual-review.json')
    if a['object_id']in native:a['additional_native_crop_inspection']=True
save('original-assets-manifest.json',am)
own=['prepare_sources.py','source-preparation.json','source_author_data.py','build_extraction.py','finalize_extraction.py','extraction-notes.md','source-facts.json','source-tables.json','source-inventory.json','intake-identity.json','original-assets-manifest.json','page-coverage.json','author-visual-review.json']
check('all explicit author files exist',all((P/n).is_file()for n in own))
validation={'schema':'mattersyn-source-author-validation/1','source_id':SID,'author':AUTHOR,'at':datetime.now(timezone.utc).isoformat(),'status':'passed_author_checks','independent_audit_status':'pending','supporting_check_count':len(checks),'failed_checks':0,'counts':expected,'fact_quantities':100,'checks':checks,'limitations':['Author source reading and mechanical transport/render checks are not a distinct scientific audit.','No curves digitized/refitted; no molecular/crystal/training/publication approval.']}
save('author-validation.json',validation);own.append('author-validation.json')
paths=[P/n for n in own]+sorted(p for p in(P/'source-render').rglob('*')if p.is_file())+sorted(p for p in(P/'reader-assets').rglob('*')if p.is_file())
bound={p.relative_to(P).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size}for p in paths}
freeze={'schema':'mattersyn-source-extraction-freeze/1','source_id':SID,'author':AUTHOR,'revision':1,'created_at':datetime.now(timezone.utc).isoformat(),'status':'immutable_author_proposal_pending_independent_source_audit','source_generation':1,'bundle_sha256':prep['bundle_sha256'],'intake_manifest':prep['intake_manifest'],'source_files':{d['source_path']:d['sha256']for d in docs.values()},'bound_files':bound,'bound_file_count':len(bound),'counts':expected,'fact_quantities':100,'author_validation_sha256':sha(P/'author-validation.json'),'independent_audit_status':'pending','all_scientific_training_and_publication_gates':False,'private_source_policy':'Original PDFs, full-page images/text and retired drafts stay local under source-render. Only17 selected original excerpts are candidates; no publication approval. Other workers audit/canonical folders excluded.'}
save('package-freeze.json',freeze)
print(json.dumps({'freeze_sha256':sha(P/'package-freeze.json'),'facts_sha256':sha(P/'source-facts.json'),'inventory_sha256':sha(P/'source-inventory.json'),'bound_files':len(bound),'checks':len(checks),'counts':expected},indent=2))
