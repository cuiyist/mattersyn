from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
O=Path(__file__).resolve().parent;A=O.parent;P=A.parents[1]
assert not (O/'package-freeze.json').exists(),'Do not overwrite frozen correction'
def read(p):return json.loads(p.read_text('utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
base=read(A/'package-freeze.json');bound=base['bound_files'].copy()
assert sha(A/'package-freeze.json')=='8b5724b9a7008dfb74cdc8f5cea7fdfcd47939a26b89d85916aebc77fed7c202'
bound[str(A/'package-freeze.json')]=sha(A/'package-freeze.json')
for p,h in bound.items():assert sha(Path(p))==h,p
v2=P/'canonical-proposal/v2'
for p in v2.glob('*.json'):bound[str(p.resolve())]=sha(p)
audit=P/'canonical-reader-independent-audit/independent-audit-v2.json';bound[str(audit.resolve())]=sha(audit)
for p in O.rglob('*'):
 if p.is_file():bound[str(p.resolve())]=sha(p)
validation=read(O/'author-validation.json');consumer=read(O/'consumer-checks.json')
assert validation['status']=='passed_author_checks_not_independent_approval' and consumer['status']=='passed'
for p,h in consumer['bound_files'].items():assert sha(Path(p))==h,p
f={'schema':'mattersyn-molecule-overlay-freeze/1','author':'/root/peng1998_reader_assets','created_at':datetime.now(timezone.utc).isoformat(),'source_id':'pati2009','doi':'10.1021/la8031286','revision':'annotation-correction-v2','status':'frozen_author_correction_pending_distinct_audit','base_freeze_path':str(A/'package-freeze.json'),'base_freeze_sha256':sha(A/'package-freeze.json'),'finding_resolved_by_proposal':'Three nitrate nitrogen annotations removed from the tertiary-amine category. All correct nitrate, cerium, water and TEA groups remain.','effective_file_map':{'path':str(O/'effective-file-map.json'),'sha256':sha(O/'effective-file-map.json')},'effective_public_assets':{'path':str(O/'effective-public-assets.json'),'sha256':sha(O/'effective-public-assets.json')},'counts':{'identities':20,'material_slots':45,'stocks':6,'stock_components':12,'public_assets':34,'public_asset_bytes_changed':1,'incorrect_group_annotations_removed':3,'metadata_replacement_files':4,'author_delta_checks':validation['checks'],'actual_consumer_checks':consumer['check_count']},'canonical_v2_receipt':{'package_manifest_sha256':sha(v2/'package-manifest.json'),'independent_audit_sha256':sha(audit),'all_19_records_byte_identical':True},'unchanged_source_canonical_and_base_package':True,'svg_and_preview_bytes_unchanged':True,'independent_approval':False,'browser_approval':False,'published':False,'training_eligible':False,'bound_files':bound}
(O/'package-freeze.json').write_text(json.dumps(f,ensure_ascii=False,indent=2)+'\n','utf-8')
print(json.dumps({'freeze_sha256':sha(O/'package-freeze.json'),'bound_files':len(bound),'registry_sha256':sha(O/'registry-additions.json'),'corrected_model_sha256':sha(O/'models/pati2009-cerium-nitrate-2d.json'),'effective_file_map_sha256':sha(O/'effective-file-map.json'),'effective_public_assets_sha256':sha(O/'effective-public-assets.json')}))
