from pathlib import Path
from datetime import datetime, timezone
import hashlib, json

O = Path(__file__).resolve().parent
J = O.parents[1]
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(name, data): (O/name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
assert not (O/'package-freeze.json').exists(), 'Frozen package must remain immutable'
checks = []
def ck(label, condition):
    checks.append({'check':label, 'passed':bool(condition)})
    assert condition, label

inputs = read(O/'input-bindings.json')['files']
for p,h in inputs.items(): ck('unchanged input '+p, sha(p)==h)
for name in ['author-validation.json','output-validation.json','consumer-execution-checks.json','proposed-links-consumer-checks.json']:
    result=read(O/name)
    ck(name+' passed', result['status'].startswith('passed') and all(x['passed'] for x in result['checks']))
allow=read(O/'public-asset-proposal.json')
ck('33 public symbolic assets',len(allow['assets'])==33)
for a in allow['assets']:
    ck('allowlisted SVG '+a['public_path'],Path(a['path']).suffix=='.svg' and sha(a['path'])==a['sha256'] and a['public_path'].startswith('assets/chemical-registry/sasongko2025-products/'))
(O/'public-assets-proposal.json').write_bytes((O/'public-asset-proposal.json').read_bytes())
ck('allowlist alias exact',(O/'public-assets-proposal.json').read_bytes()==(O/'public-asset-proposal.json').read_bytes())

reader=read(J/'canonical-proposal/v1/reader/sasongko2025.json')
reader_assets={}
def walk(x):
    if isinstance(x,dict):
        if 'public_asset' in x and 'public_asset_sha256' in x: reader_assets[x['public_asset']]=x['public_asset_sha256']
        for v in x.values(): walk(v)
    elif isinstance(x,list):
        for v in x: walk(v)
walk(reader)
link_count=0
for sid,links in read(O/'source-evidence-links.json')['links'].items():
    for a in links:
        ck('existing reader source image '+sid+' '+a['asset_id'],reader_assets.get(a['public_asset'])==a['sha256'])
        link_count+=1

index=read(O/'contact-index.json')
ck('nine reviewed contacts',len(index['contacts'])==9)
panels=[]
for c in index['contacts']:
    ck('reviewed contact bytes '+c['path'],sha(c['path'])==c['sha256'])
    for p in c['panels']:
        ck('reviewed panel bytes '+p['path'],sha(p['path'])==p['sha256'])
        panels.append(p)
ck('33 distinct viewed panels',len(panels)==len({p['path'] for p in panels})==33)
write('author-visual-review.json',{'status':'completed_author_visual_review','independent_approval':False,'actual_scope':'All 33 final cards viewed through nine contact sheets, including re-view of changed phase/unit/citation text. No mounted-browser claim.','contact_index_sha256':sha(O/'contact-index.json'),'contacts':index['contacts'],'panel_count':33,'observations':['Text readable and not clipped.','Reference cells and literature samples explicitly separated from current measurements.','No particle envelope, atomic geometry or coordinate availability implied.'],'browser_review':False})
plan=read(O/'original-evidence-consumer-insertion.json')
plan['status']='frozen_optional_integration_proposal_pending_root_review'
plan['integration_required']=False
plan['decision']='The current consumer works unchanged; root may separately review and test the exact narrow insertion. Existing reader image links remain available.'
write('original-evidence-consumer-insertion.json',plan)
write('freeze-validation.json',{'status':'passed_author_freeze_checks','independent_approval':False,'check_count':len(checks),'original_reader_link_instances':link_count,'checks':checks})

files={str(p):sha(p) for p in sorted(O.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name!='package-freeze.json'}
bound=dict(inputs);bound.update(files)
freeze={'schema_version':'1.0','source_group':'sasongko2025','doi':'10.1021/acs.jpcc.5c05144','status':'frozen_author_proposal_pending_distinct_audit','created_utc':datetime.now(timezone.utc).isoformat(),'counts':read(O/'author-validation.json')['counts'],'author_checks':{'generation':154,'output':1896,'current_consumer':350,'optional_insertion':482,'freeze':len(checks)},'source_freeze_sha256':sha(J/'source-extraction-revision-2/package-freeze.json'),'canonical_freeze_sha256':sha(J/'canonical-proposal/v1/package-freeze.json'),'roles':{'source_author':'peng1998_reader_assets','independent_source_auditor':'backlog_eta','canonical_reader_author':'norberg2004_extract','canonical_transport_auditor':'peng1998_reader_assets','product_author':'peng1998_reader_assets','independent_product_auditor':'pending distinct root review'},'independent_approval':False,'publication_approved':False,'training_eligible':False,'atomic_model':False,'consumer_change_required':False,'files':files,'input_files':inputs,'bound_files':bound,'file_count':len(files),'bound_file_count':len(bound)}
write('package-freeze.json',freeze)
print(json.dumps({'freeze_sha256':sha(O/'package-freeze.json'),'counts':freeze['counts'],'files':len(files),'bound_files':len(bound),'freeze_checks':len(checks),'hashes':{n:sha(O/n) for n in ['registry-additions.json','public-product-contexts-proposal.json','public-assets-proposal.json','bindings.json']}},indent=2))
