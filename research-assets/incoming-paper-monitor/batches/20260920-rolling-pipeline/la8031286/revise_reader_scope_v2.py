"""Preserve v1; correct exactly one reader review_scope metadata token."""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import sys,json,hashlib,shutil,importlib.util
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;C1=P/'canonical-proposal/v1';C2=P/'canonical-proposal/v2';R1=P/'public-review-proposal/v1';R2=P/'public-review-proposal/v2'
S=Path('[local path redacted]')
assert not (C2/'package-manifest.json').exists(), 'Preserve v2 once frozen.'
for p in [C2,R2,C2/'validator-snapshots']:p.mkdir(parents=True,exist_ok=True)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
checks=[]
def ck(k,v):checks.append({'check':k,'passed':bool(v)});assert v,k
base=read(C1/'package-manifest.json');audit=P/'canonical-reader-independent-audit/independent-audit-v1.json'
for p,h in base['bound_files'].items():ck('v1 unchanged '+p,sha(p)==h)
ck('v1 freeze exact',sha(C1/'package-manifest.json')=='5986df83c2313f8e5418d0c46c049d86e2ef62dbd049359c7a53a5010e312281')
old=read(R1/'pati2009.json');new=deepcopy(old)
ck('expected old scope',old['review_scope']=='complete_supplied_main_and_matched_si');new['review_scope']='supplied_main_and_matched_si'
save(R2/'pati2009.json',new)
restored=deepcopy(new);restored['review_scope']=old['review_scope'];ck('all reader scientific and presentation fields preserved',restored==old)
record_manifest=read(C1/'record-manifest.json');record_manifest['version']=2;record_manifest['created_at']=datetime.now(timezone.utc).isoformat();record_manifest['status']='private_unapproved_author_proposal_reader_scope_only_revision'
record_rows=[]
for meta in record_manifest['records']:
 oldpath=Path(meta['path']);dest=C2/oldpath.name;shutil.copyfile(oldpath,dest)
 ck('record byte-identical '+meta['record_id'],sha(dest)==meta['sha256']);meta['path']=str(dest)
 record_rows.append({'record_id':meta['record_id'],'prior_path':str(oldpath),'effective_path':str(dest),'sha256':sha(dest),'byte_identical':True})
record_manifest['prior_manifest']={'path':str(C1/'record-manifest.json'),'sha256':sha(C1/'record-manifest.json')}
save(C2/'record-manifest.json',record_manifest)
for n in ['source-to-field-coverage.json','source-owner-map.json','operation-quantity-scope.json','lossless-source-map.json']:
 shutil.copyfile(C1/n,C2/n);ck('unchanged transport '+n,sha(C1/n)==sha(C2/n))
shutil.copyfile(R1/'source-item-coverage.json',R2/'source-item-coverage.json')
bindings=read(R1/'reader-bindings-proposal.json');bindings['reader_sha256']=sha(R2/'pati2009.json');save(R2/'reader-bindings-proposal.json',bindings)
diff={'schema':'mattersyn-preserved-reader-metadata-delta/1','author':'/root/backlog_eta','source_id':'pati2009','prior_package':{'path':str(C1/'package-manifest.json'),'sha256':sha(C1/'package-manifest.json')},'prior_independent_audit':{'path':str(audit),'sha256':sha(audit)},'reader_change':[{'json_pointer':'/review_scope','before':old['review_scope'],'after':new['review_scope'],'reason':'Use the actual Site validator’s supported token for the same supplied-main-plus-matched-SI scope.'}],'canonical_scientific_changes':[],'reader_scientific_changes':[],'reader_prior_sha256':sha(R1/'pati2009.json'),'reader_effective_sha256':sha(R2/'pati2009.json'),'unchanged_records':record_rows,'all_other_reader_fields_equal':True,'visual_package_rebind_policy':'All exact v1 record SHA bindings remain scientifically valid. A distinct reviewer must approve this metadata-only revision receipt; no visual asset or record mutation is required.'}
save(C2/'reader-scope-delta.json',diff)
# Exercise the unchanged actual current validator against an isolated fixture;
# it needs publication asset/record paths but must never write the Site.
fixture=C2/'reader-contract-fixture';(fixture/'data/records').mkdir(parents=True,exist_ok=True)
for meta in record_manifest['records']:shutil.copyfile(meta['path'],fixture/'data/records'/(meta['record_id']+'.json'))
for asset in bindings['original_assets']:
 dest=fixture/'dist'/asset['public_asset'];ck('safe fixture asset destination',dest.resolve().is_relative_to(fixture.resolve()));dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(asset['private_path'],dest);ck('exact fixture asset',sha(dest)==asset['sha256'])
for name in ['build_paper_reviews.py','review_scope.py']:shutil.copyfile(S/'scripts'/name,C2/'validator-snapshots'/name)
sys.path.insert(0,str(C2/'validator-snapshots'))
spec=importlib.util.spec_from_file_location('pati_actual_reader_validator',C2/'validator-snapshots/build_paper_reviews.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.ROOT=fixture
prior_errors=module.validate(old);new_errors=module.validate(new)
ck('v1 validator demonstrates exact token failure',prior_errors==['Explicit recognized review_scope is required']);ck('actual current reader validator passes v2',new_errors==[])
validator={'status':'passed_author_actual_reader_contract_check','function':'build_paper_reviews.validate','fixture_root':str(fixture),'scope':'Unchanged actual validator functions; ROOT redirected only to a private exact asset/record fixture. This is not Site integration or browser approval.','prior_v1_errors':prior_errors,'effective_v2_errors':new_errors,'validator_inputs':{str(S/'scripts'/n):sha(S/'scripts'/n) for n in ['build_paper_reviews.py','review_scope.py']},'snapshots':{str(C2/'validator-snapshots'/n):sha(C2/'validator-snapshots'/n) for n in ['build_paper_reviews.py','review_scope.py']}}
save(C2/'actual-reader-validator-check.json',validator)
for p,h in base['bound_files'].items():ck('v1 still unchanged '+p,sha(p)==h)
save(C2/'author-validation.json',{'author':'/root/backlog_eta','status':'passed_author_narrow_delta_checks_pending_distinct_recheck','checks':checks,'check_count':len(checks),'counts':base['counts'],'actual_reader_validator':validator,'independent_approval':False})
save(R2/'author-validation.json',{'status':'passed_author_one_leaf_revision','reader_sha256':sha(R2/'pati2009.json'),'delta_path':str(C2/'reader-scope-delta.json'),'delta_sha256':sha(C2/'reader-scope-delta.json'),'current_validator_errors':new_errors,'source_science_unchanged':True,'all_prior_items_fields_and_assets_preserved':True,'independent_approval':False})
rm=read(R1/'reader-manifest.json');rm['version']=2;rm['created_at']=datetime.now(timezone.utc).isoformat();rm['status']='private_frozen_token_correction_pending_distinct_recheck';rm['prior_reader_manifest']={'path':str(R1/'reader-manifest.json'),'sha256':sha(R1/'reader-manifest.json')};rm['outputs']={n:sha(R2/n) for n in ['pati2009.json','reader-bindings-proposal.json','source-item-coverage.json','author-validation.json']};rm['input_hashes'][str(C2/'record-manifest.json')]=sha(C2/'record-manifest.json');rm['input_hashes'][str(C2/'reader-scope-delta.json')]=sha(C2/'reader-scope-delta.json');rm['revision_script_sha256']=sha(__file__);save(R2/'reader-manifest.json',rm)
(C2/'README.md').write_text('''# Pati canonical/reader revision 2

Exactly one reader metadata leaf changed: review_scope now uses supplied_main_and_matched_si. The actual current Site build_paper_reviews.validate function passes with exact assets/records staged in an isolated private fixture. All 19 canonical records are byte-identical, and all reader values/items/locators/sample links/assets remain unchanged. The original v1 and its distinct audit remain preserved.

This is an unapproved author revision awaiting the distinct auditor’s bounded recheck, not a promotion or new scientific extraction. Existing visual packages retain their exact v1 record hashes. Use reader-scope-delta.json as the narrow record-preservation receipt; independent visual gates remain separate.
''',encoding='utf8')
bound=dict(base['bound_files']);bound[str(C1/'package-manifest.json')]=sha(C1/'package-manifest.json');bound[str(audit)]=sha(audit);bound[str(Path(__file__))]=sha(__file__)
for folder in [C2,R2]:
 for p in folder.rglob('*'):
  if p.is_file():bound[str(p.resolve())]=sha(p)
final={**{k:v for k,v in base.items() if k!='bound_files'},'revision':2,'created_at':datetime.now(timezone.utc).isoformat(),'status':'frozen_for_distinct_canonical_reader_delta_audit','canonical_manifest_sha256':sha(C2/'record-manifest.json'),'reader_sha256':sha(R2/'pati2009.json'),'reader_manifest_sha256':sha(R2/'reader-manifest.json'),'prior_package_sha256':sha(C1/'package-manifest.json'),'reader_delta_sha256':sha(C2/'reader-scope-delta.json'),'author_checks':len(checks),'actual_reader_validator_passed':True,'bound_files':bound}
save(C2/'package-manifest.json',final)
print(json.dumps({'package':str(C2/'package-manifest.json'),'package_sha256':sha(C2/'package-manifest.json'),'reader_sha256':sha(R2/'pati2009.json'),'record_manifest_sha256':sha(C2/'record-manifest.json'),'checks':len(checks),'bound_files':len(bound)},indent=2))
