from pathlib import Path
import hashlib,json,datetime,urllib.request
P=Path(__file__).resolve().parent
E=P.parent.parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,data): p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
assert not (P/'package-freeze.json').exists(), 'Preserve any existing freeze.'
tests=load(P/'author-tests.json')
assert tests['status']=='passed' and tests['module_sha256']==sha(P/'evans2010-products.mjs')
assert sha(P/'evans2010-products.mjs')==sha(P/'preview/evans2010-products.mjs')
bindings=load(P/'product-bindings-proposal.json')
expected=bindings['bindings'][0]['model_sha256']
url='http://127.0.0.1:5191/assets/chemical-registry/models/evans2010-species9-reference-3d.json?sha='+expected
with urllib.request.urlopen(url) as response:
    payload=response.read(); status=response.status
assert status==200 and hashlib.sha256(payload).hexdigest()==expected
browser={
 'schema':'mattersyn.private-adapter-browser-check.v1','status':'passed',
 'scope':'Author browser verification of the isolated private adapter preview; not integrated Site verification or independent scientific approval.',
 'url':'http://127.0.0.1:5191/',
 'actual_checks':[
  'Viewed the species9 crystallization card and its source-qualified preview/caption.',
  'Opened the existing 3Dmol molecular viewer through the adapter rotate button.',
  'Dragged the visible molecular canvas and visually confirmed changed orientation.',
  'Used the + zoom button and visually confirmed the larger rotated molecular rendering.',
  'Closed the dialog and changed Source context to the single-crystal structure record; the heading and source caption changed correctly.',
  'Read the visible asymmetric-unit, riding-H and no-QD/no-training limitations.',
  'Read browser warning/error logs after these actions: no entries returned.'
 ],
 'browser_log_warning_error_count':0,
 'download_endpoint_check':{'method':'Independent localhost HTTP GET of the exact link target; no claim of browser download-dialog testing.','http_status':status,'sha256':expected},
 'screenshots':{
  'preview-3d-initial.png':'Initial molecular rendering.',
  'preview-3d-rotated-zoomed.png':'Rotation proof. Historical filename includes zoomed; zoom is separately demonstrated in the next screenshot.',
  'preview-3d-zoomed.png':'After the + zoom control, same rotated view.',
  'preview-structure-card.png':'Second allowed record context.'},
 'module_sha256':sha(P/'evans2010-products.mjs'),
 'independent_review':'pending','integrated_browser_review':'pending'
}
write(P/'author-browser-check.json',browser)
readme='''# Evans molecular species 9 product adapter

This private proposal adds a preview, rotate/zoom control and existing model JSON download to Final structures. It creates no coordinates and changes no source or canonical file.

The only allowed bindings are `evans-2010-species9-crystallization/species9-crystallization` and `evans-2010-molecular9-structure/species9-cif`. All QD, magic-size-cluster and other contexts fail closed. The 51-site molecular model retains 20 calculated riding H sites and only the asymmetric-unit molecule; this is neither a periodic lattice display nor a DFT/exact-training admission.

## Integration

Copy only `evans2010-products.mjs` to the existing Site dist directory beside `chemical-viewer.mjs`. The existing qualified registry entry, SVG and model JSON must already be imported at their established chemical-registry paths. Their identities and digests are checked before mounting. In the record Final structures host:

```js
import { mountEvansSpecies9 } from './evans2010-products.mjs';
await mountEvansSpecies9(finalStructuresHost, record);
```

The optional `sampleId` must equal the exact binding above. Root separately proposes adding the existing model JSON as a source-qualified structure asset to those two products, role `measured_sample`, `eligible_as_measured_label: false`, with all requested tasks empty. That canonical promotion is outside this adapter and is not performed here.

## Author verification

`test_adapter.mjs` checks all 32 canonical records and their product scopes, dependency hashes, refusal of altered entries, mounting and viewer delegation. All 201 checks passed. The private browser preview verified both contexts, a visible molecular model, rotation, zoom and source captions. The exact model download endpoint returned bytes with the expected digest. See `author-browser-check.json` for actual scope. Independent review and actual integrated Site/browser verification remain separate gates.

The `preview` directory contains private snapshots used only for this author check. Do not copy it wholesale into Site. Do not publish the original main/SI/CIF documents, original source snapshots or private proposal records from this package.
'''
(P/'README.md').write_text(readme,encoding='utf-8')
bound={str(p):sha(p) for p in sorted(P.rglob('*')) if p.is_file() and p.name!='package-freeze.json'}
for b in bindings['bindings']:
 p=Path(b['canonical_record_path']);assert sha(p)==b['canonical_sha256'];bound[str(p)]=sha(p)
for asset in bindings['unchanged_assets']:
 p=Path(asset['existing_source_path']);assert sha(p)==asset['sha256'];bound[str(p)]=sha(p)
for name in ['registry-additions.json','package-freeze.json']:
 p=E/'visuals/molecules'/name;bound[str(p)]=sha(p)
manifest={
 'schema':'mattersyn.evans-species9-adapter-freeze.v1','status':'author_proposal_frozen',
 'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'source_id':'evans2010','binding_count':2,'new_atomic_models':0,
 'mechanical_checks':tests['count'],'author_browser_check':'passed_private_preview',
 'public_allowlist':[{'source':'evans2010-products.mjs','destination':'dist/evans2010-products.mjs','sha256':sha(P/'evans2010-products.mjs')}],
 'existing_asset_paths':[x['public_path'] for x in bindings['unchanged_assets']],
 'bound_files':bound,'independent_adapter_review':'pending','integrated_browser_review':'pending',
 'unchanged_scope':'No Site, canonical, ledger, source, registry or existing model file was modified by this adapter authoring.'
}
write(P/'package-freeze.json',manifest)
print(json.dumps({'manifest_sha256':sha(P/'package-freeze.json'),'module_sha256':sha(P/'evans2010-products.mjs'),'binding_sha256':sha(P/'product-bindings-proposal.json'),'bound_files':len(bound),'checks':tests['count']},indent=2))
