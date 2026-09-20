"""Bounded candidate-site insertion after distinct math/binding audits; publication separate."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil
L=Path(__file__).resolve().parent;V=L/'visuals/bulk-structure-proposal';O=L/'site-integration-proposal';S=Path(r'[local path redacted]')
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['coordinate-math-audit.json','binding-audit.json']:assert read(L/'visuals/bulk-structure-independent-audit'/name)['status']=='passed'
assert sha(V/'package-freeze.json')=='1be18eb56e16404e36c2db78ff90c8e89f15c6d5ad29ceae5e9c0b8b946f7d5e'
assert not (O/'bulk-view-integration-delta.json').exists(),'one-time insertion'
assets=read(V/'public-asset-proposal.json')['files']
for a in assets:
 src=Path(a['source']);dest=S/'dist'/a['target'];assert sha(src)==a['sha256'];assert not dest.exists();dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
changes=[]
def modify(path,transform):
 before=sha(path);shutil.copy2(path,O/('pre-bulk-'+path.name));text=path.read_text(encoding='utf8');changed=transform(text);assert changed!=text;path.write_text(changed,encoding='utf8');changes.append({'path':str(path),'before_sha256':before,'after_sha256':sha(path)})
def crystal(t):
 t="import {mountLianBulk,eligibleBulkContexts} from './lian2021-bulk-viewer.mjs';\n"+t
 old='await productIdentity(host,r);registryPromise'
 new="await productIdentity(host,r);if(eligibleBulkContexts(r).length){if(!document.querySelector('link[data-lian-bulk-css]')){const css=document.createElement('link');css.rel='stylesheet';css.href=new URL('./lian2021-bulk-viewer.css',import.meta.url);css.dataset.lianBulkCss='true';document.head.append(css);}await mountLianBulk(host,r);}registryPromise"
 assert t.count(old)==1;return t.replace(old,new)
modify(S/'dist/crystal-viewer.mjs',crystal)
def builder(t):
 old="    else:body+='<p class=\"record-note\">No sample-resolved atomic coordinates are supplied for this record. A reported phase or size does not establish an exact product CIF.</p>'"
 new="    elif r.get('lineage',{}).get('source_group')=='lian2021' and r['record_id'] in {'lian-2021-bulk-a-route','lian-2021-bulk-b-route','lian-2021-bulk-characterization'}:body+='<p class=\"record-note\">Partial non-hydrogen bulk-crystal coordinates from the supporting tables are shown separately below. Hydrogen positions, occupancies and a verified link to the same physical synthesis aliquot are unavailable; no complete sample CIF or exact training pair is assigned.</p>'\n"+old
 assert old in t;return t.replace(old,new)
modify(S/'scripts/build_dataset.py',builder)
out={'at':datetime.now(timezone.utc).isoformat(),'status':'candidate_integrated_pending_browser_and_transport_audit','package_freeze_sha256':sha(V/'package-freeze.json'),'public_assets':assets,'code_changes':changes,'canonical_mutation':False,'training_mutation':False,'scope':'Four explicit bulk contexts only; pre-existing identity cards retained. Other sample and material contexts do not mount this model.'}
(O/'bulk-view-integration-delta.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out,indent=2))
