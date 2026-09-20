"""Root applies reviewed helper drafts; --check is read-only and the default."""
from pathlib import Path
import argparse,json,hashlib,shutil
D=Path(__file__).resolve().parent;N=D.parent;M=N.parents[4]
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');args=ap.parse_args()
manifest=read(D/'package-manifest.json')
for row in manifest['files']:assert sha(D/row['path'])==row['sha256'],row['path']
target=M/'research-assets/verify_public_delivery.py';original=D/'input-snapshots/verify_public_delivery.py';proposed=D/'verify_public_delivery-proposed.py'
assert sha(target) in {sha(original),sha(proposed)},'Shared verifier changed; prepare a new reviewed delta.'
assert read(D/'release-endpoints.json')['count']==324
if args.apply:
 for name in ['finalize_reader_publication.py','prepare_publication_rule.py','sync_release_delta.py','release_pati.py']:
  p=N/name
  if p.exists():assert p.read_bytes()==(D/name).read_bytes(),str(p)
  else:shutil.copyfile(D/name,p)
 destination=N/'site-integration-proposal/release-endpoints.json'
 if destination.exists():assert destination.read_bytes()==(D/'release-endpoints.json').read_bytes()
 else:shutil.copyfile(D/'release-endpoints.json',destination)
 target.write_bytes(proposed.read_bytes())
 print('Applied reviewed verifier extension and local helpers; no publication or network verification run.')
else:print('Draft checks passed; no mutation. Root may apply after independent review.')
