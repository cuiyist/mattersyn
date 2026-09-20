"""Preserve the independently found bound-purity caption issue before correction."""
from pathlib import Path
import json, hashlib, shutil, datetime

O=Path(__file__).parent
E=O.parents[1]
B=E/'visuals/molecules'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
archive=O/'initial-review'
archive.mkdir(exist_ok=True)
for name in ['mechanical-audit.json','viewer-function-audit.json','check_molecules.py','check_viewer.mjs']:
    if not (archive/name).exists(): shutil.copyfile(O/name,archive/name)
slots=read(B/'material-slot-map.json')
findings=[]
for i,s in enumerate(slots):
    if s['material_id']=='pbo':
        findings.append({'record_id':s['record_id'],'material_id':'pbo',
            'slot_map_pointer':f'/{i}/viewOverrides/caption',
            'bindings_pointer':f"/bindingNotes/{s['record_id']}/pbo/viewOverrides/caption",
            'actual_caption':s['viewOverrides']['caption'],
            'quantity':s['canonical_identity']['quantities']['purity']})
report={'schema':'mattersyn-independent-molecular-finding/1','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'reviewer':'/root/peng1998_reader_assets','status':'correction_requested','finding_id':'EVANS-MOLECULE-01',
    'finding':'Three PbO binding captions display None% although the canonical source purity is a lower bound of 99.9%.',
    'source_locator':'SI PDF page 1, Experimental Procedures, Materials: PbO (99.9+%).',
    'required_delta':'Replace the three captions and their three mirrored binding-note captions with source-faithful ≥99.9% or 99.9+% as printed. Preserve all quantities, entry identities, SVGs, models and specimen assignments.',
    'affected_slots':findings,
    'bound_files':{str(p):sha(p) for p in [B/'package-freeze.json',B/'material-slot-map.json',B/'bindings-proposal.json',E/'reader-assets/si-01.txt']},
    'other_review_status':'Full graph/source-coordinate/slot checks and all 50 preview inspections completed without another substantive finding. This report does not approve integration.'}
p=archive/'finding.json'
if p.exists(): raise SystemExit('Refusing to overwrite original finding')
p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(p,sha(p))
