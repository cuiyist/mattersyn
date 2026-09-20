"""Freeze author output after distinct source approval; canonical review remains open."""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import json,hashlib,shutil,sys
sys.dont_write_bytecode=True
C=Path(__file__).resolve().parent;F=C.parent;O=C/'draft-v2';V1=C/'draft-v1'
assert not(O/'package-freeze.json').exists()
S=Path('[local path redacted]');sys.path.insert(0,str(S/'scripts'))
from dataset_lib import validate_record,eligibility,build_groups,walk
import build_paper_reviews as consumer
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def resolve(x,p):
    for z in p.strip('/').split('/')if p else[]:
        z=z.replace('~1','/').replace('~0','~');x=x[int(z)]if isinstance(x,list)else x[z]
    return x
checks=[]
def ck(n,v):checks.append({'check':n,'passed':bool(v)});assert v,n
def without_evidence(x):
    if isinstance(x,dict):return{k:without_evidence(v)for k,v in x.items()if k not in['evidence','link_evidence']}
    if isinstance(x,list):return[without_evidence(v)for v in x]
    return x
M=read(O/'record-manifest.json');CV=read(O/'source-to-field-coverage.json');R={x['record_id']:read(x['path'])for x in M['records']}
OLD=read(V1/'record-manifest.json');OR={x['record_id']:read(x['path'])for x in OLD['records']}
V1C=read(V1/'author-checkpoint-source-v1.json')
for p,h in V1C['bound_files'].items():ck('original draft checkpoint '+p,sha(V1/p)==h)
INPUT={n:read(x['path'])for n,x in M['effective_source_files'].items()}
ck('passed source audit exact hash',sha(M['source_audit_path'])==M['source_audit_sha256']=='0da964026bc39b05289890fbcda3a51ab307dfd95c7227a7f01d686a25622f6d')
ck('passed source audit status',read(M['source_audit_path'])['status']=='passed')
ck('effective source freeze hash',sha(Path(M['source_overlay_path'])/'package-freeze.json')==M['source_freeze_sha256']=='9f76d5810d3bd2caef97dca7c96fc6ae8ad0a8362bdab8f9ac2d4811867de816')
for rid,r in R.items():
    ck(rid+' current schema and semantics',not validate_record(r))
    ck(rid+' no eligible task',not any(v['eligible']for v in eligibility(r).values()))
    for k in['materials','stocks','material_states','operations','condition_options','products','intended_target','structure_assets','lineage','method']:
        ck(rid+' unchanged '+k+(' apart from corrected evidence'if k=='products'else''),without_evidence(r[k])==without_evidence(OR[rid][k])if k=='products'else r[k]==OR[rid][k])
    ck(rid+' all numeric values unchanged',[(p,v['value'],v.get('minimum'),v.get('maximum'),v.get('unit'))for p,v in walk(r)if'value'in v and'unit'in v]==[(p,v['value'],v.get('minimum'),v.get('maximum'),v.get('unit'))for p,v in walk(OR[rid])if'value'in v and'unit'in v])
    ck(rid+' no promoted collection or tasks','collection'not in r and r['quality']['review_status']=='imported_unreviewed'and r['quality']['requested_tasks']==[])
ck('one source split group',len(set(build_groups(list(R.values())).values()))==1)
for b in CV['source_objects']:
    if not b.get('source_pointer')or b['category']=='operation':continue
    v=resolve(R[b['record_id']],b['pointer'])
    if isinstance(v,dict)and isinstance(v.get('value'),str)and v['value'].startswith('{'):
        file='source-tables.json'if b['category']=='table'else'source-facts.json';ck(b['source_id']+' complete source object',json.loads(v['value'])==resolve(INPUT[file],b['source_pointer']))
for f in CV['facts']:
    orig=next(x for x in INPUT['source-facts.json']['facts']if x['id']==f['source_fact_id'])
    for b in f['canonical_bindings']:
        v=resolve(R[b['record_id']],b['pointer']);q=resolve(orig,b['source_pointer'])
        if b['source_pointer']=='/claim':ck(f['source_fact_id']+' exact claim',v['value']==q)
        else:
            ck(f['source_fact_id']+b['source_pointer']+' exact raw token',v.get('raw_text',v.get('value'))==q['raw_text'])
            if q['value']is not None and not q.get('range')and not q.get('comparison'):ck(f['source_fact_id']+b['source_pointer']+' exact value',v['value']==q['value'])
for b in CV['table_cells']:
    q=resolve(INPUT['source-tables.json'],b['source_pointer']);v=resolve(R[b['record_id']],b['pointer'])
    ck(b['source_pointer']+' table raw/value/unit',(v['raw_text'],v['value'],v['unit'])==(q['raw_text'],q['value'],q['unit']or''))
rv=read(O/'reader/friedfeld2019.json');RMAP=read(O/'reader/source-item-coverage.json');items={i['id']:i for s in rv['reader_sections']for i in s['items']}
for b in RMAP['canonical_field_map']:
    item=items[b['reader_item_id']];q=next(q for q in item['facts']if q['id']==b['reader_fact_id']);ck(b['record_id']+b['json_pointer']+' reader value',resolve(R[b['record_id']],b['json_pointer'])==q['canonical_quantity'])
assets=read(O/'reader/reader-bindings-proposal.json')['original_assets'];oldassets=read(V1/'reader/reader-bindings-proposal.json')['original_assets']
ck('all 51 original asset bytes unchanged',{x['id']:x['sha256']for x in assets}=={x['id']:x['sha256']for x in oldassets})
for a in assets:ck(a['id']+' original crop hash',sha(a['private_path'])==a['sha256'])
s1=next(x for x in rv['figures']if x['id']=='asset-friedfeld2019-figure-s1')
ck('Figure S1 includes labeled and unlabeled contexts',{x['sample_id']for x in s1['sample_scope']['canonical_sample_links']}=={'phenylacetate-reference','nmr-labeled'})
ck('all quantity and observation field references covered',len(RMAP['canonical_field_map'])==sum(1 for r in R.values()for p,v in walk(r)if{'value','status','evidence'}<=v.keys()))
oldroot=consumer.ROOT
try:consumer.ROOT=O/'isolated-reader-fixture';errors=consumer.validate(rv)
finally:consumer.ROOT=oldroot
ck('actual current reader consumer accepts final source-v2 reader',errors==[])
ck('all original source units resolve',set(RMAP['source_units'])=={u['id']for u in INPUT['source-inventory.json']['units']})
ck('no browser or publication claim',rv['presentation_gates']['browser_render']is False and rv['presentation_gates']['publication']is False)
def diff(a,b,path=''):
    if type(a)!=type(b):return [{'pointer':path,'before':a,'after':b}]
    if isinstance(a,dict):
        out=[]
        for k in sorted(set(a)|set(b)):
            p=path+'/'+k.replace('~','~0').replace('/','~1')
            if k not in a:out.append({'pointer':p,'before_missing':True,'after':b[k]})
            elif k not in b:out.append({'pointer':p,'before':a[k],'after_missing':True})
            else:out+=diff(a[k],b[k],p)
        return out
    if isinstance(a,list):
        if len(a)!=len(b):return [{'pointer':path,'before':a,'after':b}]
        return[y for j,(x,z)in enumerate(zip(a,b))for y in diff(x,z,path+'/'+str(j))]
    return []if a==b else[{'pointer':path,'before':a,'after':b}]
delta={rid:diff(OR[rid],R[rid])for rid in R};reader_delta=diff(read(V1/'reader/friedfeld2019.json'),rv)
save('source-revision2-transport-delta.json',{'status':'author_delta_for_independent_review','source_author_correction_history':str(Path(M['source_overlay_path'])/'source-correction-history.json'),
    'source_author_correction_history_sha256':sha(Path(M['source_overlay_path'])/'source-correction-history.json'),'canonical_deltas':delta,'reader_deltas':reader_delta,
    'notes':['Only passed source corrections and source-audit status statements were regenerated.','No operation/material/stock/target/lineage/numeric quantity changed. Product context values and lineage are unchanged; corrected source locators propagate into their evidence.','The original source-v1 draft checkpoint and all 124 bound files are unchanged.']})
save('author-validation.json',{'status':'passed_author_checks_pending_distinct_canonical_reader_audit','created_at':datetime.now(timezone.utc).isoformat(),'checks':checks,'check_count':len(checks),
    'source_independent_audit_status':'passed','canonical_independent_audit':False,'actual_reader_consumer_errors':errors,'actual_browser':False,'publication_approved':False})
M['status']='frozen_private_author_proposal_pending_independent_canonical_reader_audit';M.pop('final_freeze_allowed',None);M['canonical_independent_audit_passed']=False;save('record-manifest.json',M)
snap=O/'author-script-snapshots';snap.mkdir(exist_ok=True)
for n in['build_actual_draft.py','build_reader_draft.py','finalize_revision2.py']:shutil.copyfile(C/n,snap/n)
(O/'PROPOSAL_NOTES.md').write_text('''# Friedfeld canonical and reader proposal

The author proposal contains 30 records: one representative cluster-conversion protocol, three explicitly inherited additive/concentration variants, 15 supporting procedures and 11 observations. Its 58 operation instances arise from 34 source operations and do not count physical batches. All 65 facts/153 fact quantities, 207 semantic units, 39 source materials, five source stock definitions, 62 source contexts, 185 printed numeric cells, 44 figures, two schemes, 31 equation entries and 56 references are retained.

The effective source revision2 has passed a distinct independent scientific audit. This proposal still requires root’s independent canonical/reader review. No training task, measured atomic structure, molecular/apparatus approval, browser gate or publication gate is granted by this author freeze.

The reader uses five academic sections plus sources and limitations, with 417 items, 2,131 exact canonical fields and all 51 selected original crops. The actual current reader validator passed against an isolated fixture with real record and crop bytes. All full-page images, source PDFs and raw source text remain outside the proposed public assets. Reference studies and author mechanisms do not become current recipes.

Scientific boundaries for review: representative 20 mg/0.00121 mmol injection is excluded from changed-concentration amounts; paired source alternatives are not a Cartesian matrix. The isotope-acid synthesis and cited-only cluster/phosphine preparations remain separate. Ether extracts, residue, solvent distillate and purified fraction sets retain their proper lineage. Coolants and ice-water bath components are external to the reaction charge. Acquisition specimens are separate contexts, not pooled mixtures. Source rate/Scherrer/Gaussian values remain fits or calculations, with source discrepancies retained. The ±0.5 nm TEM uncertainty has no asserted statistical definition. Figure S1 links both labeled and unlabeled cluster contexts.

Source-v1 drafts and all their bound bytes remain preserved. The detailed transport delta enumerates source locator/uncertainty/sample corrections and source-audit metadata changes. Operations, materials, stocks, states, condition options, targets, lineage and numeric values remain unchanged. Product context values and lineage are unchanged; corrected source locators propagate into their evidence. Molecular assets are being prepared separately by root; this package uses the stable source material IDs.
''',encoding='utf-8')
bound={str(p.relative_to(O)):sha(p)for p in O.rglob('*')if p.is_file()}
inputs={str(F/'package-freeze.json'):sha(F/'package-freeze.json'),str(Path(M['source_overlay_path'])/'package-freeze.json'):M['source_freeze_sha256'],str(Path(M['source_overlay_path'])/'effective-file-map.json'):sha(Path(M['source_overlay_path'])/'effective-file-map.json'),M['source_audit_path']:M['source_audit_sha256'],str(V1/'author-checkpoint-source-v1.json'):sha(V1/'author-checkpoint-source-v1.json')}
inputs.update({x['path']:x['sha256']for x in M['effective_source_files'].values()})
save('package-freeze.json',{'schema':'mattersyn-private-canonical-reader-author-freeze/1','status':'frozen_pending_independent_canonical_reader_audit','author':'/root/norberg2004_extract','source_id':'friedfeld2019',
    'created_at':datetime.now(timezone.utc).isoformat(),'source_freeze_sha256':M['source_freeze_sha256'],'source_independent_audit_sha256':M['source_audit_sha256'],'source_generation':1,
    'bound_files':bound,'external_bound_inputs':inputs,'record_manifest_sha256':sha(O/'record-manifest.json'),'reader_sha256':sha(O/'reader/friedfeld2019.json'),
    'counts':M['counts'],'reader_counts':rv['counts'],'author_checks':len(checks),'training_eligible':False,'canonical_independent_audit_passed':False,'publication_approved':False})
print(json.dumps({'status':'frozen_for_independent_review','freeze':str(O/'package-freeze.json'),'freeze_sha256':sha(O/'package-freeze.json'),'record_manifest_sha256':sha(O/'record-manifest.json'),'reader_sha256':sha(O/'reader/friedfeld2019.json'),'checks':len(checks),'bound_files':len(bound)}))
