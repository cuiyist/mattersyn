from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
A=Path(__file__).resolve().parent;N=A.parent.parent;C=N/'canonical-proposal/v2'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not (A/'package-freeze.json').exists(),'Preserve any prior freeze before revision'
checks=read(A/'author-validation.json');assert checks['checks']==750
assert sha(C/'package-manifest.json')=='433555d5ccaaa0a3d98c01f3f9657921872611fee766557e9c4756f49e806508'
assert sha(N/'canonical-reader-independent-audit/independent-audit-v2.json')=='c8be4ee1522e9c1c4fb9555f8242870e5b75dd0be3c0198eaa0915f1320d4139'
inputs=[]
def bind(p,role,expected=None):
 actual=sha(p)
 if expected: assert actual==expected,(p,actual,expected)
 inputs.append({'path':str(p),'sha256':actual,'bytes':p.stat().st_size,'role':role})
for f in ['package-freeze.json','source-facts.json','source-inventory.json','source-tables.json','page-coverage.json','pairing-review.json','source-correction-history.json','source-independent-audit/independent-audit-v2.json','canonical-reader-independent-audit/independent-audit-v2.json']:
 bind(N/f,'source_or_prior_independent_audit')
bind(C/'package-manifest.json','canonical_v2_manifest')
for p in sorted(C.glob('morrison-*.json')):bind(p,'canonical_v2_record_unchanged')
for s in read(N/'pairing-review.json')['original_file_copies']:bind(Path(s['source_path']),'original_document_read_only',s['sha256'])
viewed=['main-02','main-03','main-04','main-05','main-06','main-07','si-07','si-08','si-14']
for stem in viewed:bind(N/'source-render'/(stem+'.png'),'actually_viewed_relevant_original_page')
for stem in ['main-02','main-03','main-04','main-05','main-06','main-07','si-08','si-14']:
 p=N/'private/text'/(stem+'.txt')
 if p.exists():bind(p,'read_relevant_source_text_private_only')
preview=read(A/'preview-manifest.json');assert len(preview['scenes'])==24
for s in preview['scenes']:
 assert sha(A/s['svg_path'])==s['svg_sha256'];assert sha(A/s['png_path'])==s['png_sha256']
preview['visual_review_status']='all_24_scenes_actually_inspected_by_author_in_six_contacts; changed_scenes_reinspected_after_corrections'
write(A/'preview-manifest.json',preview)
review={'author':'/root/norberg2004_extract','status':'passed_author_visual_review_pending_independent_audit','actual_source_pages_viewed':viewed,'fresh_all_source_pages_review_claim':False,'all_24_scenes_viewed':True,'all_155_display_rows_read':True,'contact_sheets':preview['contacts'],'pre_freeze_corrections':['Moved shell-stock label to avoid collision with the scene title.','Repositioned supernatant/precipitate labels in the three centrifugation-flow scenes.','Used an uncoated belt symbol for room-temperature back-exchange to avoid assigning an established shell geometry.','Displayed canonical multiple and degree units as × and ° without changing typed units.'],'scientific_checks':['All quantities and eight additional observations use exact canonical pointers.','Printed mass/amount conflicts, ambiguous 20 mmol solution and monolayer charge basis preserved.','≤15 min remains upper bound; 2 h is observation, not onset; SI 1 h conflict remains visible.','100(2) K is the precursor-crystal acquisition condition; mounting dimensions remain approximate.','Optical aliquots and separate microscopy branch are not merged.','Initial three washes versus final unknown repetition count remain distinct.','No measured pattern, spectrum, nanocrystal atomic coordinates or exact apparatus dimensions invented.'],'not_approved':['Independent scientific apparatus audit','Mounted browser QA','Site integration','Publication','Training eligibility']}
write(A/'author-visual-review.json',review)
files=[]
for p in sorted(A.rglob('*')):
 if p.is_file() and '__pycache__' not in p.parts:
  files.append({'path':p.relative_to(A).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size})
freeze={'schema':'mattersyn-apparatus-author-package/1','source_id':'morrison2017','doi':'10.1021/acs.inorgchem.7b01711','author':'/root/norberg2004_extract','created_at':datetime.now(timezone.utc).isoformat(),'status':'frozen_author_proposal_pending_distinct_independent_audit','canonical_manifest_sha256':sha(C/'package-manifest.json'),'source_revision2_freeze_sha256':sha(N/'package-freeze.json'),'canonical_independent_audit_sha256':sha(N/'canonical-reader-independent-audit/independent-audit-v2.json'),'counts':{'canonical_collection_records':18,'records_with_operations':10,'operations':24,'art_types':24,'parameter_rows':62,'additional_typed_observation_acquisition_rows':8,'all_display_rows':155,'svg_previews':24,'png_previews':24,'contact_sheets':6,'author_mechanical_checks':750},'public_asset_proposal':['morrison2017-protocol.mjs'],'runtime_dependency':'quantity-value.mjs already present in Site; private identical helper only','source_files_unchanged':True,'canonical_files_unchanged':True,'shared_site_or_ledger_edits':False,'independent_approval':False,'publication_approval':False,'training_approval':False,'inputs':inputs,'files':files}
write(A/'package-freeze.json',freeze)
print(json.dumps({'package_freeze_sha256':sha(A/'package-freeze.json'),'module_sha256':sha(A/'morrison2017-protocol.mjs'),'files':len(files),'inputs':len(inputs),'counts':freeze['counts']}))
