"""Freeze the narrow independently requested average-model labeling revision."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
root=Path(__file__).resolve().parent; out=root/'structure-candidate'; old=root/'structure-candidate-revision-1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
bind=lambda p:{'path':str(p),'sha256':sha(p)}
old_freeze=json.loads((old/'package-freeze.json').read_text())
assert sha(old/'package-freeze.json')=='fef2f3fd8416b0b57f05f7223b04c53634964aed3fd628e50f0aca27af676df0'
for p in old_freeze['files']:
    archived=old/Path(p['path']).name
    actual=archived if archived.exists() else Path(p['path'])
    assert sha(actual)==p['sha256']
# Numeric model output is unchanged; wording is applied directly to avoid another
# run against an already reopened freeze. The builder contains the final wording.
replacements={
 'origin choice2':'origin choice 2','all23 Table3':'all 23 Table 3',
 'is107.1602':'is 107.1602','Table3 reports111.7':'Table 3 reports 111.7',
 'of4.5398':'of 4.5398','or2.27':'or 2.27','other22 Table3':'other 22 Table 3',
 'ofthree':'of three','of0.5':'of 0.5','Table2 footnote':'Table 2 footnote'}
for name in ('average-model.json','heo2003-average-position-occupancy.cif'):
    p=out/name; text=p.read_text(encoding='utf8')
    for before,after in replacements.items():text=text.replace(before,after)
    p.write_text(text,encoding='utf8')
model=json.loads((out/'average-model.json').read_text());model['cif']=bind(out/'heo2003-average-position-occupancy.cif')
(out/'average-model.json').write_text(json.dumps(model,indent=2)+'\n')
report=json.loads((out/'author-validation.json').read_text());report['cif']=bind(out/'heo2003-average-position-occupancy.cif')
(out/'author-validation.json').write_text(json.dumps(report,indent=2)+'\n')
current=json.loads((out/'average-model.json').read_text());previous=json.loads((old/'average-model.json').read_text())
assert all(current[k]==previous[k] for k in ['fractionalSites','asymmetric_sites','refinement_weighted_counts','a','spaceGroup'])
files=[root/'build_average_model.py',Path(__file__),root/'main-tables.json',root/'source-scientific-audit.json',
       old/'package-freeze.json',old/'independent-audit.json',out/'heo2003-average-position-occupancy.cif',
       out/'average-model.json',out/'author-validation.json']
freeze={'status':'private_revised_author_candidate_targeted_reaudit_pending','author':'/root',
        'at':datetime.now(timezone.utc).isoformat(),'revision':'Label one unresolved 2.27-ESD angle tension and make the three-ESD threshold explicit; coordinates and occupancies unchanged.',
        'numeric_model_unchanged':True,'files':[bind(p) for p in files]}
(out/'package-freeze.json').write_text(json.dumps(freeze,indent=2)+'\n')
print(json.dumps({'freeze_sha256':sha(out/'package-freeze.json'),'positions_and_occupancies_unchanged':True}))
