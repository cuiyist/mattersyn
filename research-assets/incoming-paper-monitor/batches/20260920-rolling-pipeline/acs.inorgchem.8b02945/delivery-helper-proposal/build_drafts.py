"""Write private Friedfeld delivery proposals only; never execute a release."""
from pathlib import Path
import ast,hashlib,json
D=Path(__file__).resolve().parent;F=D.parent;MON=F.parents[2];M=F.parents[4];P=F.parent/'la8031286'
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def put(name,s):(D/name).write_text(s,'utf8')
def save(name,v):put(name,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
assert not(D/'package-manifest.json').exists()
base=read(P/'site-integration-proposal/release-endpoints.json');assert len(base['paths'])==base['count']==324
pm=read(F/'site-integration-proposal/v1/promotion-manifest.json');assert len(pm['public_assets'])==162 and len(pm['records'])==30
extra=['data/paper-reviews/friedfeld2019.json']+[x['public_path']for x in pm['public_assets']]+[pre+x['record_id']+post for x in pm['records']for pre,post in [('records/','.html'),('data/records/','.json')]]
paths=base['paths']+extra;assert len(paths)==len(set(paths))==547
withheld=base['additional_withheld_paths']+['assets/figures/friedfeld2019/pages/main-01.png','assets/figures/friedfeld2019/pages/si-01.png']
save('release-endpoints.json',{'dataset_version':'0.32.0','source_id':'friedfeld2019','paths':paths,'count':len(paths),'expected_citation_count':40,'additional_withheld_paths':withheld,'additional_withheld_count':18,'extra_endpoints':len(extra),'extra_scope':'One Friedfeld reader, 162 frozen projection assets and 30 record HTML/JSON pairs. All 324 prior endpoints retained in order.','source_projection_manifest_sha256':sha(F/'site-integration-proposal/v1/promotion-manifest.json'),'source_projection_freeze_sha256':sha(F/'site-integration-proposal/v1/package-freeze.json')})
snap=D/'input-snapshots';snap.mkdir(exist_ok=True)
verifier=M/'research-assets/verify_public_delivery.py';raw=verifier.read_text('utf8');assert 'data/paper-reviews/friedfeld2019.json'not in raw
(snap/'verify_public_delivery.py').write_bytes(verifier.read_bytes())
insert="if (D/'data/paper-reviews/friedfeld2019.json').exists():\n paths += "+repr(extra)+"\n"
hold="if (D/'data/paper-reviews/friedfeld2019.json').exists():withheld += ['assets/figures/friedfeld2019/pages/main-01.png','assets/figures/friedfeld2019/pages/si-01.png']\n"
put('verify_public_delivery-proposed.py',raw.replace('assert len(paths)==len(set(paths))',insert+'assert len(paths)==len(set(paths))').replace('withheld_checks=[',hold+'withheld_checks=['))
# Receipt, projection and exact two-leaf finalizer helpers are authored separately.
put('prepare_delivery_helpers.py','''"""Root adoption only; default check is read-only, --apply is explicit."""
from pathlib import Path
import argparse,hashlib,json,shutil
D=Path(__file__).resolve().parent;F=D.parent;M=F.parents[4]
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');args=ap.parse_args()
manifest=read(D/'package-manifest.json')
for x in manifest['files']:assert sha(D/x['path'])==x['sha256'],x['path']
target=M/'research-assets/verify_public_delivery.py';original=D/'input-snapshots/verify_public_delivery.py';proposed=D/'verify_public_delivery-proposed.py'
assert sha(target)in{sha(original),sha(proposed)},'Shared verifier changed; review a new delta.'
assert read(D/'release-endpoints.json')['count']==547
if args.apply:
 for name in ['release_support.py','release_friedfeld.py','sync_release_delta.py','finalize_reader_publication.py']:
  p=F/name
  if p.exists():assert p.read_bytes()==(D/name).read_bytes(),str(p)
  else:shutil.copyfile(D/name,p)
 p=F/'site-integration-proposal/release-endpoints.json'
 if p.exists():assert p.read_bytes()==(D/'release-endpoints.json').read_bytes()
 else:shutil.copyfile(D/'release-endpoints.json',p)
 target.write_bytes(proposed.read_bytes())
 print('Reviewed helpers adopted; no publication, verification network call or ledger checkpoint run.')
else:print('Private draft checks passed; no changes applied.')
''')
save('inputs.json',{'base_endpoint_plan':{'path':str(P/'site-integration-proposal/release-endpoints.json'),'sha256':sha(P/'site-integration-proposal/release-endpoints.json')},'promotion_manifest':{'path':str(F/'site-integration-proposal/v1/promotion-manifest.json'),'sha256':sha(F/'site-integration-proposal/v1/promotion-manifest.json')},'promotion_freeze':{'path':str(F/'site-integration-proposal/v1/package-freeze.json'),'sha256':sha(F/'site-integration-proposal/v1/package-freeze.json')},'prior_finalizer':{'path':str(P/'finalize_reader_publication.py'),'sha256':sha(P/'finalize_reader_publication.py')},'prior_release':{'path':str(P/'release_pati.py'),'sha256':sha(P/'release_pati.py')},'projection_policy':{'path':str(M/'research-assets/public_projection_policy.py'),'sha256':sha(M/'research-assets/public_projection_policy.py')},'sync_helpers':{'path':str(M/'research-assets/sync_github_public.py'),'sha256':sha(M/'research-assets/sync_github_public.py')}})
print(json.dumps({'private_drafts':True,'endpoints':len(paths),'new_endpoints':len(extra),'public_assets':162,'withheld':len(withheld)}))
