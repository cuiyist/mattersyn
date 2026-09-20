"""Freeze the exact private reader proposal for a different reviewer's audit."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
O=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
v=read(O/'proposal-validation.json');r=read(O/'nagasaki2004.json');inp=read(O/'reader-authoring-inputs.json')
assert v['status']=='passed' and v['reader_sha256']==sha(O/'nagasaki2004.json')
assert all(sha(Path(p))==h for p,h in inp['input_hashes'].items()),'Frozen input changed.'
names=['build_reader.py','validate_reader.py','freeze_reader.py','nagasaki2004.json','source-item-coverage.json','canonical-measurement-coverage.json','reader-bindings-proposal.json','reader-items-summary.json','reader-authoring-inputs.json','proposal-validation.json','reader-notes.md','operation-prose-correction.json']
manifest={'schema':'mattersyn-private-reader-proposal-manifest/1','source_id':'nagasaki2004','frozen_at':datetime.now(timezone.utc).isoformat(),'status':'author_validated_pending_independent_reader_audit','reader_path':str(O/'nagasaki2004.json'),'reader_sha256':sha(O/'nagasaki2004.json'),'counts':r['counts'],'author_validation_checks':v['check_count'],'files':{str(O/n):sha(O/n) for n in names},'bound_inputs':inp['input_hashes'],'actual_author_reinspection':{'main_text_pages':[1,2,3,4,5],'si_text_pages':[1],'main_visual_pages':[1,2,3,4,5],'si_visual_pages':[1,2,3],'original_crops_visually_inspected':['main-figure1','main-figure2','main-figure3','main-figure4','main-figure5','main-figure6','si-figure1','si-figure2']},'pending_gates':['Independent scientific reader audit','Molecular/polymer/protein and apparatus binding review','Source-specific structural-reference and specimen binding review','Actual Site build and mounted browser review','Publication approval through the existing project workflow'],'independent_reader_audit_passed':False,'viewer_bindings_approved':False,'training_eligible':False,'site_modified':False,'ledger_modified':False,'source_or_canonical_modified':False,'published':False}
p=O/'reader-proposal-manifest.json';p.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':manifest['status'],'reader_sha256':manifest['reader_sha256'],'manifest_sha256':sha(p),'validation_sha256':sha(O/'proposal-validation.json'),'source_coverage_sha256':sha(O/'source-item-coverage.json'),'canonical_coverage_sha256':sha(O/'canonical-measurement-coverage.json')},ensure_ascii=False))
