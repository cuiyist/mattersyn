"""Preserve an unapproved Friedfeld draft; not a final canonical approval."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil,sys
C=Path(__file__).resolve().parent;F=C.parent;O=C/'draft-v1'
assert not(O/'author-checkpoint-source-v1.json').exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def resolve(x,p):
    for z in p.strip('/').split('/')if p else[]:
        z=z.replace('~1','/').replace('~0','~');x=x[int(z)]if isinstance(x,list)else x[z]
    return x
cm=read(O/'record-manifest.json');cv=read(O/'source-to-field-coverage.json');R={x['record_id']:read(x['path'])for x in cm['records']}
D=read(F/'source-facts.json');T=read(F/'source-tables.json');I=read(F/'source-inventory.json');P={'source-facts.json':D,'source-tables.json':T}
checks=[]
def ck(n,v):checks.append({'check':n,'passed':bool(v)});assert v,n
for r in cm['records']:ck(r['record_id']+' exact draft hash',sha(r['path'])==r['sha256'])
for b in cv['source_objects']:
    if not b.get('source_pointer')or b['category']=='operation':continue
    value=resolve(R[b['record_id']],b['pointer'])
    if isinstance(value,dict)and isinstance(value.get('value'),str)and value['value'].startswith('{'):
        file='source-tables.json'if b['category']=='table'else'source-facts.json';ck(b['source_id']+' exact structured source payload',json.loads(value['value'])==resolve(P[file],b['source_pointer']))
for b in cv['table_cells']:
    q=resolve(T,b['source_pointer']);v=resolve(R[b['record_id']],b['pointer']);ck(b['source_pointer']+' raw numeric token',v['raw_text']==q['raw_text'])
    if not q.get('range')and not q.get('comparison'):ck(b['source_pointer']+' numeric value',v['value']==q['value'])
    ck(b['source_pointer']+' exact unit',v['unit']==(q.get('unit')or''))
for f in cv['facts']:
    orig=next(x for x in D['facts']if x['id']==f['source_fact_id'])
    for b in f['canonical_bindings']:
        v=resolve(R[b['record_id']],b['pointer']);q=resolve(orig,b['source_pointer'])
        if b['source_pointer']=='/claim':ck(f['source_fact_id']+' literal claim',v['value']==q)
        else:
            ck(f['source_fact_id']+b['source_pointer']+' raw token',(v.get('raw_text',v.get('value')))==q['raw_text'])
            if not q.get('range')and not q.get('comparison')and q['value']is not None:ck(f['source_fact_id']+b['source_pointer']+' numeric value',v['value']==q['value'])
rr=R['friedfeld-2019-conversion-concentration'];so=next(s for s in rr['stocks']if s['id']=='msc-injection-varied')
ck('changed concentration stock has no representative MSC mass or amount',all(not any(k in c['quantities']for k in['msc_mass','msc_amount'])for c in so['components']))
ck('all current structure assets absent',all(r['structure_assets']==[]for r in R.values()))
ck('all batches unknown',all(r['lineage']['batch_id']is None and all(p['batch_id']is None for p in r['products'])for r in R.values()))
ck('all current tasks withheld',all(r['quality']['requested_tasks']==[]for r in R.values()))
ck('no source binary or whole-page public asset',all(not a['contains_complete_source_page']for a in read(F/'original-assets-manifest.json')['assets']))
save('canonical-author-validation.json',{'status':'passed_author_consistency_only','check_count':len(checks),'checks':checks,'source_audit_status':'pending_versioned_corrections','canonical_independent_audit':False,'publication_approval':False})
snap=O/'author-script-snapshots';snap.mkdir(exist_ok=True)
for n in['build_actual_draft.py','build_reader_draft.py','checkpoint_actual_draft.py']:shutil.copyfile(C/n,snap/n)
(O/'AUTHOR_CHECKPOINT.md').write_text('''# Friedfeld private draft checkpoint

Thirty actual records and the six-section reader have been authored, with 58 instances of the source’s 34 operations. The 750 measurements include literal structured source payloads as well as typed quantities; none of these counts represents independent physical batches. All 51 selected original crops are mapped and copied into the isolated reader fixture.

The current schema and actual reader consumer pass. The reader has 417 items and 2,131 exact canonical fields. This checkpoint remains unapproved and is **not the final canonical freeze**. No molecular/apparatus asset, website, training task or publication gate is approved here.

The source auditor has requested four narrow corrections: two main-page evidence locators, the undefined statistical meaning of the reported ±0.5 nm TEM uncertainty, and the labeled comparison sample in Figure S1. These source corrections will be preserved in a new source revision and transported into a separate draft version. The source numbers and original crop pixels are not expected to change. This v1 is retained so that the later delta can be checked.

Record boundaries: one representative conversion, three explicitly linked concentration/additive variants, fifteen separate source preparative/acquisition procedures, and eleven contextual observations. Cited phosphorus and cluster preparations remain incomplete. The isotope-acid synthesis is a supporting ligand preparation. Altered-concentration records exclude the representative 20 mg/0.00121 mmol charge; retained distillation residue, separate fractions and external coolants retain their own graph roles. Source fits, phase evidence and observed distributions do not become operation settings or exact atomic labels.
''',encoding='utf-8')
bound={str(p.relative_to(O)):sha(p)for p in O.rglob('*')if p.is_file()}
save('author-checkpoint-source-v1.json',{'status':'preserved_unapproved_author_checkpoint_source_v1','author':'/root/norberg2004_extract','created_at':datetime.now(timezone.utc).isoformat(),
    'source_freeze_sha256':sha(F/'package-freeze.json'),'source_independent_audit_pending':True,'canonical_freeze':False,'bound_files':bound,
    'counts':cm['counts'],'reader_counts':read(O/'reader/reader-author-validation.json')['counts'],'author_consistency_checks':len(checks),
    'next_action':'Consume the preserved source revision2 and distinct passed source audit, regenerate a separate draft-v2, then request root independent canonical/reader review.'})
print(json.dumps({'checkpoint':str(O/'author-checkpoint-source-v1.json'),'sha256':sha(O/'author-checkpoint-source-v1.json'),'checks':len(checks),'bound_files':len(bound)}))
