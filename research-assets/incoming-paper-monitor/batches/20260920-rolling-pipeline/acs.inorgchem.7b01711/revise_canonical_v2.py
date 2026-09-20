"""Preserve v1 and apply independent finding MCR1, one classification field."""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import json,hashlib,shutil,sys
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;C1=P/'canonical-proposal/v1';C2=P/'canonical-proposal/v2';V1=P/'public-review-proposal/v1';V2=P/'public-review-proposal/v2'
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if C2.exists():
 assert sha(C2/'package-manifest.json')==sha(C1/'package-manifest.json'),'A completed v2 freeze cannot be overwritten.'
oldfreeze=read(C1/'package-manifest.json')
protected={str(p):sha(p) for root in [C1,V1] for p in root.rglob('*') if p.is_file()}
for p,h in oldfreeze['bound_files'].items():assert sha(p)==h,p
shutil.copytree(C1,C2,dirs_exist_ok=True);shutil.copytree(V1,V2,dirs_exist_ok=True)
rid='morrison-2017-single-crystal-acquisition';record=read(C2/(rid+'.json'));before=deepcopy(record)
assert record['material_states'][0]=={'id':'precursor-crystal-structure','name':'precursor crystal structure','kind':'mixture','parent_ids':['cdptc-thf-crystal']}
record['material_states'][0]['kind']='analysis_data';save(C2/(rid+'.json'),record)
restored=deepcopy(record);restored['material_states'][0]['kind']='mixture';assert restored==before
S=Path('[local path redacted]');sys.path.insert(0,str(S/'scripts'))
from dataset_lib import validate_record,eligibility
schema_checks=[]
cm=read(C2/'record-manifest.json')
for row in cm['records']:
 p=C2/(row['record_id']+'.json');r=read(p)
 errors=validate_record(r);assert not errors,(row['record_id'],errors)
 assert not any(x['eligible'] for x in eligibility(r).values()),row['record_id']
 if row['record_id']!=rid:assert sha(p)==sha(C1/p.name)
 schema_checks.append({'record_id':row['record_id'],'schema_and_semantic_errors':errors,'eligibility':eligibility(r)})
 row['path']=str(p);row['sha256']=sha(p)
assert (V2/'morrison2017.json').read_bytes()==(V1/'morrison2017.json').read_bytes()
delta={'schema':'mattersyn-canonical-correction/1','author':'/root/backlog_eta','finding':'MCR1','requested_by':'/root/peng1998_reader_assets','source_independent_audit_sha256':sha(P/'source-independent-audit/independent-audit-v2.json'),'canonical_v1_audit_sha256':sha(P/'canonical-reader-independent-audit/independent-audit-v1.json'),'canonical_changes':[{'record_id':rid,'pointer':'/material_states/0/kind','before':'mixture','after':'analysis_data','reason':'The crystal-mount-measure output is a diffraction/refinement result, not a newly synthesized mixture.'}],'reader_scientific_changes':[],'reader_byte_identical':True,'source_quantities_operations_materials_products_measurements_and_sample_links_unchanged':True,'old_record_sha256':sha(C1/(rid+'.json')),'new_record_sha256':sha(C2/(rid+'.json')),'old_package_manifest_sha256':sha(C1/'package-manifest.json'),'schema_recheck':schema_checks,'v1_preserved_files':protected,'all_original_v1_files_unchanged':True}
save(C2/'correction-delta.json',delta)
validation=read(C2/'author-validation.json');validation['revision']=2;validation['revision_check']='One kind field corrected; all 18 schema/semantic checks repeated, no eligible tasks; all other canonical science and reader bytes exactly unchanged.';validation['checks'].append({'check':'MCR1 output classification and full record invariance','passed':True});validation['check_count']=len(validation['checks']);save(C2/'author-validation.json',validation)
cm.update(version=2,created_at=datetime.now(timezone.utc).isoformat(),status='source_audit_passed_one_classification_correction_pending_independent_recheck',validation_sha256=sha(C2/'author-validation.json'),revision_script_sha256=sha(__file__),correction_delta_sha256=sha(C2/'correction-delta.json'));save(C2/'record-manifest.json',cm)
rm=read(V2/'reader-manifest.json');rm.update(version=2,created_at=datetime.now(timezone.utc).isoformat(),reader_byte_identical_to_v1=True)
newinputs={}
for path,h in rm['input_hashes'].items():
 p=Path(path);q=C2/p.name if p.parent==C1 else p
 newinputs[str(q)]=sha(q)
rm['input_hashes']=newinputs;rm['outputs']={name:sha(V2/name) for name in rm['outputs']};save(V2/'reader-manifest.json',rm)
(C2/'revision-notes.md').write_text('MCR1: only `/material_states/0/kind` in `morrison-2017-single-crystal-acquisition` changes from `mixture` to `analysis_data`. All quantitative science, source data, 17 other records, 252 reader items and all reader bytes are unchanged. v1 remains immutable. Original author notes/validation record the historical v1 scope; this delta documents v2. Independent recheck and visual/promotion gates remain separate.\n',encoding='utf-8')
bound={}
for path,h in oldfreeze['bound_files'].items():
 p=Path(path);q=C2/p.name if p.parent==C1 else V2/p.name if p.parent==V1 else p
 bound[str(q)]=sha(q)
for p in [Path(__file__),C2/'correction-delta.json',C2/'revision-notes.md',P/'canonical-reader-independent-audit/independent-audit-v1.json']:bound[str(p)]=sha(p)
freeze=deepcopy(oldfreeze);freeze.update(version=2,frozen_at=datetime.now(timezone.utc).isoformat(),status='author_classification_correction_pending_independent_recheck',canonical_record_manifest_sha256=sha(C2/'record-manifest.json'),reader_manifest_sha256=sha(V2/'reader-manifest.json'),reader_sha256=sha(V2/'morrison2017.json'),bound_files=bound,bound_file_count=len(bound),scope_notes_path=str(C2/'revision-notes.md'),previous_package_manifest_sha256=sha(C1/'package-manifest.json'),correction_delta_sha256=sha(C2/'correction-delta.json'))
freeze['author_checks']['canonical']=validation['check_count'];save(C2/'package-manifest.json',freeze)
for p,h in protected.items():assert sha(p)==h,p
print(json.dumps({'manifest_sha256':sha(C2/'package-manifest.json'),'record_manifest_sha256':sha(C2/'record-manifest.json'),'reader_sha256':sha(V2/'morrison2017.json'),'record_sha256':sha(C2/(rid+'.json')),'delta_sha256':sha(C2/'correction-delta.json')}))
