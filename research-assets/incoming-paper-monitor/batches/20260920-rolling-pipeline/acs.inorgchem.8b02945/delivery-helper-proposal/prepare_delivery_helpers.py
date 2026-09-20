"""Root adoption only; default check is read-only, --apply is explicit."""
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
