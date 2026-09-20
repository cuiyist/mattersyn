"""Freeze the bounded reader correction after author prose inspection; private only."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, re, shutil, sys
sys.dont_write_bytecode = True
C=Path(__file__).resolve().parent; F=C.parent; V2=C/'draft-v2'; O=C/'draft-v3'
S=Path('[local path redacted]')
sys.path.insert(0,str(S/'scripts'))
import build_paper_reviews as consumer
def read(p): return json.loads(Path(p).read_bytes())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x): Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def resolve(x,p):
    for k in p.strip('/').split('/') if p else []:
        k=k.replace('~1','/').replace('~0','~'); x=x[int(k)] if isinstance(x,list) else x[k]
    return x
def diff(a,b,p=''):
    if type(a)!=type(b):return [{'pointer':p,'before':a,'after':b}]
    if isinstance(a,dict):
        out=[]
        for k in sorted(set(a)|set(b)):
            q=p+'/'+k.replace('~','~0').replace('/','~1')
            if k not in a:out.append({'pointer':q,'before_missing':True,'after':b[k]})
            elif k not in b:out.append({'pointer':q,'before':a[k],'after_missing':True})
            else:out+=diff(a[k],b[k],q)
        return out
    if isinstance(a,list):
        if len(a)!=len(b):return [{'pointer':p,'before':a,'after':b}]
        return [d for j,(x,y) in enumerate(zip(a,b)) for d in diff(x,y,p+'/'+str(j))]
    return [] if a==b else [{'pointer':p,'before':a,'after':b}]
assert not (O/'package-freeze.json').exists()
r=read(O/'reader/friedfeld2019.json'); old=read(V2/'reader/friedfeld2019.json')
items={i['id']:i for s in r['reader_sections'] for i in s['items']}
before={i['id']:i for s in old['reader_sections'] for i in s['items']}
# Final author proofreading: one compound token and human equation headings only.
for x in r['recipe_inventory']:x['label']=x['label'].replace('Labeledacid','Labeled acid')
for iid,it in items.items():
    if iid.startswith('source-equations-equation-gaussian-'):
        it['title']='Published Gaussian function '+iid.rsplit('-',1)[1]
    elif iid=='source-equations-scheme1-relation':it['title']='Proposed cluster dissociation relation'
    elif iid.startswith('source-equations-equation-fit-'):
        suffix=iid.removeprefix('source-equations-equation-fit-')
        parts=suffix.split('-'); fig='Figure 5' if parts[0]=='figure5' else 'Figure '+parts[0].upper()
        label={'high':'high concentration','middle':'middle concentration','low':'low concentration','log':'logarithmic regression','inset':'inset','indium':'indium-additive series','acid':'acid-additive series'}
        extra=[]
        for token in parts[1:]:extra.append(token+' °C' if token in ['150','200','250','300'] else label[token])
        it['title']='Published fit: '+fig+(' — '+', '.join(extra) if extra else '')
save(O/'reader/friedfeld2019.json',r)
d=read(O/'reader-revision3-delta.json');d['reader_delta']=diff(old,r);d['reader_delta_count']=len(d['reader_delta']);d['current_reader_sha256']=sha(O/'reader/friedfeld2019.json')
save(O/'reader-revision3-delta.json',d)
b=read(O/'reader/reader-bindings-proposal.json');b['reader_sha256']=sha(O/'reader/friedfeld2019.json');save(O/'reader/reader-bindings-proposal.json',b)
checks=[]
def ck(n,v):checks.append({'check':n,'passed':bool(v)});assert v,n
patterns=[r'/reader_sections/\d+/items/\d+/(title|text)$',r'/reader_sections/\d+/items/\d+/notes/\d+$',r'/reader_sections/\d+/items/\d+/original_assets/\d+/label$',r'/reader_sections/\d+/items/\d+/sample_scope/canonical_sample_links$',r'/(figures|tables|equations|schemes|source_notes)/\d+/(label|caption_paraphrase)$',r'/(figures|tables|equations|schemes|source_notes)/\d+/notes/\d+$',r'/remaining_gaps/\d+$',r'/evidence_conflicts/\d+/(title|description)$',r'/recipe_inventory/\d+/label$']
for x in d['reader_delta']:ck('Final allowed delta '+x['pointer'],any(re.fullmatch(p,x['pointer']) for p in patterns))
for iid,it in items.items():
    for k in ['facts','operation_contexts','material_contexts','stock_contexts','product_contexts','evidence','canonical_links','source_audit_unit_ids','source_fact_ids']:
        ck(iid+' immutable '+k,it.get(k)==before[iid].get(k))
    if iid.startswith(('source-equations-','source-references-')):ck(iid+' literal text immutable',it['text']==before[iid]['text'])
    ck(iid+' readable missingness','Unreported details: .' not in it['text'])
    ck(iid+' no panel JSON','Source panel assignments:' not in it['text'])
cm=read(O/'record-manifest.json'); rec={x['record_id']:read(x['path']) for x in cm['records']}
for x in read(O/'unchanged-record-receipt.json')['records']:ck('Unchanged record '+x['record_id'],sha(x['prior_path'])==sha(x['current_path'])==x['sha256'])
for x in read(O/'reader/source-item-coverage.json')['canonical_field_map']:
    q=next(z for z in items[x['reader_item_id']]['facts'] if z['id']==x['reader_fact_id'])
    ck('Exact typed field '+x['record_id']+x['json_pointer'],resolve(rec[x['record_id']],x['json_pointer'])==q['canonical_quantity'])
omissions=read(F/'canonical-independent-audit/sample-link-omissions.json')
for x in omissions:
    links=items[x['item_id']]['sample_scope']['canonical_sample_links']
    ck('Bounded existing named link '+x['item_id'],links[:-1]==x['existing_links'] and links[-1]['record_id']==x['record_id'] and links[-1]['json_pointer']==x['pointer'] and links[-1]['sample_id']==x['sample_id'] and resolve(rec[x['record_id']],x['pointer'])['sample_id']==x['sample_id'])
for a in b['original_assets']:ck('Original crop immutable '+a['id'],sha(a['private_path'])==sha(O/'isolated-reader-fixture/dist'/a['public_asset'])==a['sha256'])
bf=read(V2/'package-freeze.json')
for p,h in bf['bound_files'].items():ck('Preserved v2 '+p,sha(V2/p)==h)
for p,h in bf['external_bound_inputs'].items():ck('Source boundary '+p,sha(p)==h)
ck('All source coverage retained',sha(V2/'source-to-field-coverage.json')==sha(O/'source-to-field-coverage.json') and sha(V2/'reader/source-item-coverage.json')==sha(O/'reader/source-item-coverage.json'))
ck('All reader counts and gates unchanged',r['counts']==old['counts'] and r['presentation_gates']==old['presentation_gates'])
priorroot=consumer.ROOT
try:consumer.ROOT=O/'isolated-reader-fixture';errors=consumer.validate(r)
finally:consumer.ROOT=priorroot
ck('Current reader consumer accepts final bytes',errors==[])
v=read(O/'author-validation.json');v['initial_correction_check_count']=v['check_count'];v['final_checks']=checks;v['final_check_count']=len(checks);v['reader_delta_count']=len(d['reader_delta']);v['final_reader_sha256']=sha(O/'reader/friedfeld2019.json');v['actual_reader_consumer_errors']=errors
save(O/'author-validation.json',v);save(O/'reader/reader-author-validation.json',v)
proof=[]
for s in r['reader_sections']:
    proof.append('## '+s['title'])
    for it in s['items']:
        proof.append('\n### '+it['id']+' — '+it['title']+'\n\n'+it['text'])
        if it['notes']:proof.append('\n'+'\n'.join('- '+n for n in it['notes']))
(O/'reader/display-proof.md').write_text('\n'.join(proof)+'\n',encoding='utf-8')
save(O/'reader/author-prose-inspection.json',{'status':'author_display_proofread_pending_independent_recheck','author':'/root/norberg2004_extract','reader_sha256':sha(O/'reader/friedfeld2019.json'),'scope':['All 34 operation prose cards; their copied canonical operation payloads are unchanged.','All five main panel descriptions and 39 SI figure captions, with mirrored gallery prose.','All 62 named-context card labels and existing-product links; equal conditions remain distinct from exact physical samples.','All twelve conflict descriptions and repeated notes, stock/material spacing corrections, source summary spacing and both SI contents notes.','All changed display strings inspected from bounded private proof output, including the portion initially truncated; literal reference and equation text left unchanged.','Final equation display headings and the remaining labeled-acid inventory label proofread explicitly.'],'actual_browser':False,'scientific_source_review_repeated':False,'typed_payloads_unchanged':True})
shutil.copyfile(Path(__file__),O/'author-script-snapshots/freeze_reader_v3.py')
bound={str(p.relative_to(O)):sha(p) for p in O.rglob('*') if p.is_file()}
external=dict(bf['external_bound_inputs']);external[str(V2/'package-freeze.json')]=sha(V2/'package-freeze.json');external[str(F/'canonical-independent-audit/sample-link-omissions.json')]=sha(F/'canonical-independent-audit/sample-link-omissions.json')
findings_path=F/'canonical-independent-audit/independent-audit-v2.json'
assert sha(findings_path)=='9d6f9eef8798b58f87ae1e1a103f979bcab2ed896fb59a1ef70ffab439186613'
external[str(findings_path)]=sha(findings_path)
save(O/'package-freeze.json',{'schema':'mattersyn-private-canonical-reader-author-freeze/1','status':'frozen_pending_independent_reader_v3_delta_audit','author':'/root/norberg2004_extract','source_id':'friedfeld2019','created_at':datetime.now(timezone.utc).isoformat(),'source_generation':1,'source_freeze_sha256':cm['source_freeze_sha256'],'source_independent_audit_sha256':cm['source_audit_sha256'],'prior_canonical_reader_freeze_sha256':sha(V2/'package-freeze.json'),'bound_files':bound,'external_bound_inputs':external,'record_manifest_sha256':sha(O/'record-manifest.json'),'reader_sha256':sha(O/'reader/friedfeld2019.json'),'counts':cm['counts'],'reader_counts':r['counts'],'initial_author_checks':v['initial_correction_check_count'],'final_author_checks':len(checks),'reader_delta_count':len(d['reader_delta']),'named_sample_links_added':62,'unchanged_canonical_record_count':30,'canonical_independent_audit_passed':False,'training_eligible':False,'publication_approved':False})
print(json.dumps({'status':'frozen_for_distinct_recheck','freeze_sha256':sha(O/'package-freeze.json'),'reader_sha256':sha(O/'reader/friedfeld2019.json'),'record_manifest_sha256':sha(O/'record-manifest.json'),'delta_sha256':sha(O/'reader-revision3-delta.json'),'unchanged_record_receipt_sha256':sha(O/'unchanged-record-receipt.json'),'initial_checks':v['initial_correction_check_count'],'final_checks':len(checks),'bound_files':len(bound),'reader_deltas':len(d['reader_delta'])}))
