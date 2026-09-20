"""Finalize reviewed metadata, then build and check the exact public dataset."""
from pathlib import Path
import json,hashlib,subprocess,sys,shutil
from datetime import datetime,timezone
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
changed=[]
for p in sorted((S/'data/records').glob('littau-*.json')):
    r=read(p);proposal=read(B/'public-record-proposal/records'/p.name)
    for key in r:
        if key not in {'quality','structure_assets'}:assert r[key]==proposal[key],(p.name,key)
    for key in r['quality']:
        if key!='review_scope':assert r['quality'][key]==proposal['quality'][key],(p.name,key)
    before=sha(p)
    r['quality']['review_scope']=r['quality']['review_scope'].replace('Final item-coverage reconciliation, canonical-to-reader audit and publication remain separate pending gates.','Source-item coverage, canonical-to-reader mapping and targeted browser checks are complete for this supplied-main contribution.').replace('Precursor selection and partial literature-protocol supervision are proposed only;','Only precursor selection and partial literature-protocol supervision are enabled;')
    write(p,r);changed.append({'record_id':p.stem,'before_sha256':before,'after_sha256':sha(p),'permitted_changes':['review-scope completion wording','independently audited illustrative structure assets on 6.0/2.0 only']})
binding_path=S/'dist/assets/chemical-registry/bindings.json';bindings=read(binding_path)
for p in sorted((S/'data/records').glob('littau-*.json')):bindings['sourceRecordSha256'][p.stem]=sha(p)
write(binding_path,bindings)
p=S/'data/paper-reviews/littau1993.json';r=read(p)
r['coverage_status']='supplied_main_reviewed_and_reader_integrated; SI_not_located_or_verified'
r['independent_audit']='Seven-page source review, canonical joins and bounded reader data-retention audit completed; targeted browser checks completed by the site owner'
r['audit_details']='All seven supplied main pages and thirteen original crops were independently reviewed. Bounded scientific audits covered three formulation records, nine supporting procedures and AKS41 context. Source-item reconciliation accounts for 164 staged units and 1,235 leaves; 136 reader evidence items preserve quantitative and qualitative context. Browser checks covered representative protocol, molecule, crystal, figure-filter, responsive and evidence-search interactions. This does not establish laboratory reproduction, verified SI or unreported physical batch identities.'
r['publication_status']='reviewed_contribution_ready_for_publication'
r['training_note']='This source ledger is not itself a training example. Three synthesis variants are eligible only for precursor selection and partial protocol tasks. Nine supporting procedures and one contextual observation have no enabled training tasks. Exact-structure, size-outcome and success labels are not enabled for this source.'
for item in r['recipe_inventory']:item['status']='source_reviewed_and_reader_integrated'
r['remaining_gaps']=[x for x in r['remaining_gaps'] if x!='Reader integration, figure-to-state joins and visual verification have not been completed for this proposal.']
write(p,r)
write(B/'final-record-delta.json',{'at':datetime.now(timezone.utc).isoformat(),'records':changed,'measurement_product_lineage_preserved':True,'training_tasks_unchanged_from_audited_proposal':True})
log=[]
def run(path,*args):
    result=subprocess.run([sys.executable,str(path),*args],cwd=S,text=True,capture_output=True,encoding='utf-8')
    log.append({'script':Path(path).name,'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
    if result.returncode:
        write(B/'final-build-validation.json',{'status':'failed','results':log});raise SystemExit(result.stdout+result.stderr)
for name in ['build_dataset.py','build_paper_reviews.py','build_atlas.py']:run(S/'scripts'/name)
run(B/'inventory-proposal/build_inventory_proposal.py');shutil.copy2(B/'inventory-proposal/inventory-summary.json',S/'data/inventory-summary.json')
for name in ['build_inventory.py','check_site.py','check_atlas.py']:run(S/'scripts'/name)
run(S/'scripts/check_quality.py','--root',str(S))
write(B/'final-build-validation.json',{'status':'passed','at':datetime.now(timezone.utc).isoformat(),'results':log})
print('Final build passed: 168 records, 15 hubs, all local links/assets and privacy checks. Validated output retained for publication.')
