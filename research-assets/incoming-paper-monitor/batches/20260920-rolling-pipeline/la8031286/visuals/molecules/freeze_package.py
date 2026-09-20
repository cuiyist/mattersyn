"""Freeze author-reviewed Pati chemical proposal; no shared project mutations."""
from pathlib import Path
import json,hashlib,datetime
O=Path(__file__).resolve().parent;P=O.parents[1]
assert not (O/'package-freeze.json').exists(),'Preserve original freeze.'
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,v):(O/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
inputs=read(O/'input-bindings.json')
external={**inputs['source_files'],**inputs['canonical_records']}
for key in ['canonical_record_manifest','canonical_package_manifest']:
 x=inputs[key];external[x['path']]=x['sha256']
external[str(P/'source-preparation.json')]=sha(P/'source-preparation.json')
for d in read(P/'source-preparation.json')['documents']:external[d['source_path']]=d['sha256']
for n in ['main-01.png','main-02.png']:external[str(P/'source-render'/n)]=sha(P/'source-render'/n)
for p,h in external.items():assert sha(p)==h,('Changed input',p)
for n in ['generation-checks.json','binding-author-checks.json','author-validation.json','consumer-checks.json']:
 d=read(O/n);assert all(c['passed'] for c in d['checks']),n
for p,h in read(O/'consumer-checks.json')['bound_files'].items():assert sha(p)==h,('Consumer input changed',p)
panels=sorted([*O.glob('previews/*.png'),*O.glob('stock-previews/*.png'),*O.glob('conformer-previews/*.png')]);contacts=sorted(O.glob('contacts/contact-*.png'))
assert len(panels)==32 and len(contacts)==6
save('author-visual-review.json',{'author':'/root/peng1998_reader_assets','created_at':now,'status':'passed_author_visual_review',
 'actual_scope':'All 32 panels were actually viewed on six contact sheets. The final corrected cerium-nitrate card was additionally viewed at native size. Final regeneration changed no other preview content; source main pages 1 and 2 were reopened for material/stock scope.',
 'counts':{'identity_panels':20,'stock_panels':6,'retained_geometry_panels':6,'contacts':6},
 'observations':['TEA named-reference graph and literal conflicting formula are visible together.','Ce nitrate shows clear 1/3/6 multiplicities, with no coordination bonds.','The three alcohols have correct terminal hydroxyl connectivity and separate stock labels.','Unknown solutions, supplies and proposed species remain symbolic.','No clipping was found in the reviewed cards or their qualifiers.','Six stock cards distinguish concentration from 100 mL transfer and unknown preparation volume.'],
 'contact_files':{str(p):sha(p) for p in contacts},'panel_files':{str(p):sha(p) for p in panels},'independent_approval':False,'browser_approval':False})
entries=read(O/'registry-additions.json')['entries'];assets={}
for e in entries:
 for k in ['svgPath','model2dPath','model3dPath']:
  if e[k]:assert sha(O/e[k])==e['assetHashes'][k];assets[e[k]]=sha(O/e[k])
assert len(assets)==34
save('public-asset-proposal.json',{'schema':'mattersyn-molecule-public-allowlist/1','source_id':'pati2009','status':'private_unapproved_candidates','assets':[{'path':p,'sha256':h} for p,h in sorted(assets.items())],'excluded':'Original papers/SI, full pages, raw references, registry snapshots, contact/stock previews and all product coordinates.'})
logical=['registry-additions.json','bindings-proposal.json','material-slot-map.json','stock-component-map.json','solution-components-proposal.json','source-stock-reference-proposal.json','reference-qualification.json','public-asset-proposal.json','input-bindings.json']
save('effective-file-map.json',{n:{'path':str(O/n),'sha256':sha(O/n)} for n in logical})
save('effective-public-assets.json',{p:{'path':str(O/p),'sha256':h} for p,h in sorted(assets.items())})
bound={str(p):sha(p) for p in sorted(O.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
bound.update(external)
validation_counts={n:read(O/n)['check_count'] for n in ['generation-checks.json','binding-author-checks.json','author-validation.json','consumer-checks.json']}
save('package-freeze.json',{'schema':'mattersyn-private-molecular-package/1','author':'/root/peng1998_reader_assets','created_at':now,'source_id':'pati2009','doi':'10.1021/la8031286','status':'frozen_author_proposal_pending_distinct_molecular_audit',
 'source_revision':1,'source_generation':1,'source_freeze_sha256':sha(P/'package-freeze.json'),'source_audit_sha256':sha(P/'source-independent-audit/independent-audit.json'),
 'canonical_revision':1,'canonical_package_sha256':inputs['canonical_package_manifest']['sha256'],'canonical_review_status':'Separate review pending at author freeze; no canonical promotion is implied.',
 'counts':read(O/'author-validation.json')['counts']|{'symbolic_identities':12,'preview_panels':32,'contact_sheets':6,'bound_files':len(bound)},'validation_counts':validation_counts,
 'scope':['20 source identities and exact 45 material/12 component slot references.','Eight 2D graphs, six unchanged cached atom/bond arrays; zero newly generated 3D or product atom models.','TEA named graph explicitly differs from the literal printed formula; no source/canonical correction made.','No nitrate hydrate coordination or new water charge, and no stock-preparation-volume inference.','Author static/consumer checks only; distinct scientific, integration and browser gates remain.'],
 'cached_input_policy':'Immutable reference-snapshots bind the cached inputs; original shared-registry paths are historical provenance only.',
 'public_projection':'Only the 34 files in effective-public-assets.json are proposed Site chemical assets.','independent_approval':False,'browser_approval':False,'training_approval':False,'bound_files':bound})
print(json.dumps({'freeze':str(O/'package-freeze.json'),'sha256':sha(O/'package-freeze.json'),'bound_files':len(bound),'validation_counts':validation_counts},indent=2))
