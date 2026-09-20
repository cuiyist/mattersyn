"""Private record promotion proposal; does not import records or publish a Site."""
from pathlib import Path
from copy import deepcopy
import json,sys,hashlib,datetime
B=Path(__file__).resolve().parent;S=B.parents[4]/'recipe-atlas'
sys.path.insert(0,str(S/'scripts'))
from dataset_lib import validate_record,eligibility,training_view,build_groups
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
audit=read(B/'canonical-records-audit.json');assert audit['status']=='passed' and not audit['open_findings']
O=B/'promotion-proposal';D=O/'records';D.mkdir(parents=True,exist_ok=True)
scope='All 2 supplied main pages and 3 content-matched SI pages completely read and visually inspected; independent source extraction and canonical scientific audits passed. Source conflicts and unreported parameters are preserved. This scope does not establish identical physical aliquots across analytical techniques or measured atomic coordinates.'
tasks={'gu-2004-heterodimer':['precursor_selection','partial_protocol'],'gu-2004-cdacac-preparation':['partial_protocol']}
rows=[];promoted=[];exports=[]
for p in sorted((B/'canonical-drafts').glob('*.json')):
    assert audit['bound_record_files'][p.name]==sha(p)
    original=read(p);r=deepcopy(original)
    r['collection']='reviewed_literature'
    r['quality'].update(review_status='source_reviewed',review_scope=scope,requested_tasks=tasks.get(r['record_id'],[]))
    r['sources'][0]['main_status']='Both supplied main pages text-read and visually inspected; independent source and canonical audits passed.'
    restored=deepcopy(r)
    restored['collection']=original['collection']
    restored['quality']=original['quality']
    restored['sources'][0]['main_status']=original['sources'][0]['main_status']
    assert restored==original,'Unexpected scientific-field mutation'
    errors=validate_record(r);assert not errors,(r['record_id'],errors)
    e=eligibility(r)
    for task,v in e.items():
        if v['eligible']:exports.append(training_view(r,task))
    assert not any(e[t]['eligible'] for t in ['exact_structure_recipe','size_conditioned_recipe','success_prediction','optical_outcome'])
    dest=D/p.name;save(dest,r);promoted.append(r)
    rows.append({'record_id':r['record_id'],'source_sha256':sha(p),'proposal_sha256':sha(dest),'eligible_tasks':[t for t,v in e.items() if v['eligible']]})
prec=next(x for x in exports if x['task']=='precursor_selection')
assert {m['name'] for m in prec['output']['precursors']}=={'Pt(acac)2','Fe(CO)5','Elemental sulfur powder','Cd(acac)2'}
assert set(prec['input'])=={'composition','method'}
assert len(exports)==3
assert len(set(build_groups(promoted).values()))==1
assert len(next(x for x in exports if x['task']=='partial_protocol' and x['record_id']=='gu-2004-heterodimer')['output']['operations'])==15
assert len(next(x for x in exports if x['task']=='partial_protocol' and x['record_id']=='gu-2004-cdacac-preparation')['output']['operations'])==6
save(O/'training-export-preview.json',{'status':'private_proposal_only','published':False,'exports':exports})
save(O/'promotion-manifest.json',{'status':'private_proposal_valid_pending_reader_visual_release_checks','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'source_canonical_audit_sha256':sha(B/'canonical-records-audit.json'),'records':rows,
    'allowed_promotion_fields':['collection','quality.review_status','quality.review_scope','quality.requested_tasks','sources[0].main_status'],
    'scientific_fields_unchanged':True,'one_source_split_group':True,'record_count':len(rows),'proposed_precursor_selection_rows':1,'proposed_partial_protocol_rows':2,
    'proposed_exact_structure_pairs':0,'proposed_size_conditioned_rows':0,'proposed_optical_rows':0,'proposed_success_labels':0,
    'training_export_preview_sha256':sha(O/'training-export-preview.json'),'site_modified':False,'publication_approved':False})
print(json.dumps({'private_proposed_records':len(rows),'precursor_selection_rows':1,'partial_protocol_rows':2,'other_training_tasks':0,'scientific_fields_unchanged':True}))
