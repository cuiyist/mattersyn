"""Copy the final, explicit delivery/pilot files through the public policy."""
from pathlib import Path
import hashlib,json
import public_projection_policy as policy
R=Path(__file__).resolve().parent.parent;D=R.parent/'mattersyn-github-project'
files=[R/'MEMORY.md',R/'research-assets/github-publication-checkpoint.json',R/'research-assets/github-public-delivery-verification.json',R/'research-assets/github-public-project-sync.json',R/'research-assets/verify_public_delivery.py',R/'research-assets/save_public_delivery_completion.py',R/'research-assets/sync_final_pilot_checkpoint.py',R/'research-assets/mattersyn-review-automation.toml',R/'skills/mattersyn-paper-to-site/references/delivery-and-memory.md',R/'research-assets/incoming-paper-monitor/build_public_progress.py',R/'research-assets/incoming-paper-monitor/latest-publication.json']
files.extend(p for p in (R/'research-assets/incoming-paper-monitor/deadline-20260920').glob('*') if p.is_file())
files.extend(p for p in (R/'research-assets/incoming-paper-monitor/batches/20260919-five-paper-pilot/public-projection-review').glob('*') if p.is_file())
changed=[]
for p in files:
 rel=p.relative_to(R).as_posix()
 if policy.exclude_path(rel):continue
 raw=policy.transform_bytes(rel,p.read_bytes());q=D/rel
 if q.exists() and q.read_bytes()==raw:continue
 q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(raw)
 changed.append({'path':rel,'sha256':hashlib.sha256(raw).hexdigest()})
print(json.dumps({'updated_explicit_files':changed,'raw_documents_copied':False},indent=2))
