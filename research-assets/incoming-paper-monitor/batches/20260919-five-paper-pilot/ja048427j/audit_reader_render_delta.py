"""Independent bounded renderer delta; no source/canonical/reader author changes."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
B=Path(__file__).resolve().parent;O=B/'public-review-proposal'
def rd(p):return json.loads(Path(p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
prior=O/'audit-history/prose-corrected-freeze/norberg2004.json';current=O/'norberg2004.json'
assert sha(prior)=='1c6d2074023fee56b491ad9eb8d17c7a185aca7e19e1eef092ef181340649519'
old,new=rd(prior),rd(current);diffs=[]
def walk(a,b,p=''):
 if type(a)!=type(b):diffs.append({'pointer':p,'before':a,'after':b});return
 if isinstance(a,dict):
  for k in sorted(set(a)|set(b)):
   q=p+'/'+k.replace('~','~0').replace('/','~1')
   if k not in a or k not in b:diffs.append({'pointer':q,'before':a.get(k),'after':b.get(k)})
   else:walk(a[k],b[k],q)
 elif isinstance(a,list):
  if len(a)!=len(b):diffs.append({'pointer':p,'before':a,'after':b})
  else:
   for n,(v,w)in enumerate(zip(a,b)):walk(v,w,p+'/'+str(n))
 elif a!=b:diffs.append({'pointer':p,'before':a,'after':b})
walk(old,new)
allowed=['/public_asset_sha256','/asset_provenance/renderer','/asset_provenance/replaces_archived_render','/source_review_basis']
bad=[d for d in diffs if not any(d['pointer'].endswith(s)for s in allowed)]
manifest=rd(B/'reader-assets/asset-manifest.json');originals=[]
for a in manifest['assets']:
 p=B/a['path'];h=sha(p);originals.append({'path':str(p),'sha256':h,'matches_frozen_source_asset':h==a['sha256']})
assert not bad and all(a['matches_frozen_source_asset']for a in originals)
reported=rd(O/'reader-render-correction.json')['changed_reader_fields']
assert {json.dumps(d,sort_keys=True)for d in diffs}=={json.dumps(d,sort_keys=True)for d in reported}
out={'schema':'mattersyn-independent-renderer-delta/1','source_id':'norberg2004','auditor':'/root/peng1998_reader_assets','at':datetime.now(timezone.utc).isoformat(),'status':'passed','prior_reader_sha256':sha(prior),'current_reader_sha256':sha(current),'changed_field_count':len(diffs),'allowed_field_suffixes':allowed,'changes':diffs,'unapproved_changes':bad,'unchanged_original_assets':originals,'source_prose_quantities_sample_links_and_public_paths_unchanged':True,'canonical_modified':False,'reader_render_correction_sha256':sha(O/'reader-render-correction.json')}
(B/'reader-render-delta-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'status':'passed','changes':len(diffs),'unchanged_originals':len(originals)}))
