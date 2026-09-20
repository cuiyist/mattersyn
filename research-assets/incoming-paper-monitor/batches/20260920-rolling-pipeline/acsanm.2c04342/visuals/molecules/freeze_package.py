"""Freeze the private Matuhina molecular proposal after actual author review."""
from pathlib import Path
import hashlib, json, shutil
from datetime import datetime, timezone

O=Path(__file__).resolve().parent
P=O.parent.parent
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(n,v): (O/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not (O/'package-freeze.json').exists(), 'Frozen package must not be overwritten'
now=datetime.now(timezone.utc).isoformat()
inputs=read(O/'input-bindings.json')
qual=read(O/'reference-qualification.json')
snapshots={s['original_path']:s for s in qual['snapshots']}
for p,h in inputs['inputs'].items():
    target=O/snapshots[p]['snapshot'] if p in snapshots else Path(p)
    assert sha(target)==h, f'Input changed: {target}'
for p,h in inputs['canonical_records'].items():
    assert sha(p)==h, f'Canonical input changed: {p}'
for n in ['author-validation.json','generation-checks.json','binding-author-checks.json','viewer-function-checks.json']:
    d=read(O/n)
    assert all(c['passed'] for c in d['checks']),n
v=read(O/'viewer-function-checks.json')
assert sha(v['module_path'])==v['module_sha256']
shutil.copyfile(v['module_path'],O/'reference-snapshots/chemical-viewer.mjs')
panels=sorted([*O.glob('previews/*.png'),*O.glob('stock-previews/*.png'),*O.glob('conformer-previews/*.png')])
assert len(panels)==39
contacts=sorted(O.glob('contacts/contact-*.png'))
assert len(contacts)==7
write('author-visual-review.json',{
 'author':'/root/backlog_eta','recorded_at':now,'status':'passed_author_visual_review',
 'actual_scope':'All 39 final panels were visually inspected on seven contact sheets; each sheet was opened using view_image. This records author review, not independent approval or mounted browser QA.',
 'counts':{'identity_panels':28,'stock_panels':5,'retained_conformer_projections':6,'contact_sheets':7},
 'checks':['Readable formulas, charge and isotope labels; unambiguous disconnected salt components.',
 'No clipped chemical structures or stock captions in the final panels.',
 'Cs carbonate and anhydrous MnCl2 explicitly avoid coordination or lattice assertions.',
 'Cis OA/oleylamine references do not assign source batch isomer composition or surface coordination.',
 'Octadecene and hexane remain unspecified source identities without assigned positional isomers.',
 'Water for quenching, ultrapure analytical water and heavy-water optical continuum generation remain distinct.',
 'Five stock cards distinguish whole charges, unknown final molarity and injection aliquots.',
 'Support, calibration, product and degradation-phase symbols carry no recovered atomic coordinates.'],
 'contact_files':{str(p):sha(p) for p in contacts},'panel_files':{str(p):sha(p) for p in panels},
 'independent_approval':False,'browser_approval':False})
logical=['registry-additions.json','bindings-proposal.json','material-slot-map.json','stock-component-map.json',
 'solution-components-proposal.json','source-stock-reference-proposal.json','reference-qualification.json','public-asset-proposal.json']
write('effective-file-map.json',{n:{'path':str(O/n),'sha256':sha(O/n)} for n in logical})
assets=read(O/'public-asset-proposal.json')['assets']
assert len(assets)==44
for a in assets: assert sha(O/a['path'])==a['sha256']
write('effective-public-assets.json',{a['path']:{'path':str(O/a['path']),'sha256':a['sha256']} for a in assets})
bound={str(p):sha(p) for p in sorted(O.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
# Live Site registry/asset inputs are represented by their immutable copied bytes.
for p,h in inputs['inputs'].items():
    if p not in snapshots: bound[p]=h
bound.update(inputs['canonical_records'])
for n in ['package-manifest.json','record-manifest.json']:
    p=P/'canonical-proposal/v1'/n
    bound[str(p)]=sha(p)
write('package-freeze.json',{
 'schema':'mattersyn-private-molecular-package/1','author':'/root/backlog_eta','created_at':now,
 'source_id':'matuhina2023','doi':'10.1021/acsanm.2c04342',
 'status':'frozen_author_proposal_pending_distinct_molecular_audit',
 'source_revision':2,'source_freeze_sha256':sha(P/'package-freeze.json'),
 'canonical_revision':1,'canonical_package_sha256':sha(P/'canonical-proposal/v1/package-manifest.json'),
 'counts':read(O/'author-validation.json')['counts']|{'preview_panels':39,'contact_sheets':7,'bound_files':len(bound)},
 'validation_counts':{n:read(O/n)['check_count'] for n in ['generation-checks.json','binding-author-checks.json','author-validation.json','viewer-function-checks.json']},
 'scope':['Source-qualified molecular references and symbolic identities only.',
 'Six cached illustrative conformers retain all atom/bond/coordinate arrays; no new 3D conformation or product lattice was generated.',
 'New name-derived graphs are explicitly labeled reference connectivity, not a downloaded or measured structure.',
 '55 canonical material slots and 15 stock-component pointers are exact and individually qualified.',
 'Source/canonical/reader files were not altered; final integration and browser checks remain separate.'],
 'cached_input_policy':'Original cached reference paths/hashes are historical provenance in input-bindings.json. Immutable reference-snapshots are authoritative audit inputs if the shared Site registry later changes.',
 'public_projection':'Only the 44 files in effective-public-assets.json are candidate chemical assets. Raw reference caches, private source data, stock/contact previews and audit files are not part of this Site asset allowlist.',
 'independent_approval':False,'browser_approval':False,'training_approval':False,
 'bound_files':bound})
print(json.dumps({'freeze':str(O/'package-freeze.json'),'sha256':sha(O/'package-freeze.json'),'bound_files':len(bound)},indent=2))
