"""Copy final delivery receipts after the full filtered project synchronization."""
from pathlib import Path
import hashlib,json,sys,socket
R=Path(__file__).resolve().parents[2];M=R.parents[1];D=M.parent/'mattersyn-github-project'
sys.path.insert(0,str(M/'research-assets'));import public_projection_policy as policy
rels=['MEMORY.md','research-assets/github-public-delivery-verification.json','research-assets/github-publication-checkpoint.json','research-assets/github-public-project-sync.json','research-assets/github-public-site-sync.json','research-assets/incoming-paper-monitor/latest-publication.json']
base='research-assets/incoming-paper-monitor/batches/20260920-rolling-pipeline/'
rels += [base+n for n in ['save_ready_for_integration.py','save_verified_progress.py','sync_final_checkpoint.py','progress-publication-verification.json','ready-for-integration-checkpoint.json']]
proof=[]
for rel in rels:
 p=M/rel;raw=policy.transform_bytes(rel,p.read_bytes());target=D/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
 proof.append({'path':rel,'sha256':hashlib.sha256(raw).hexdigest()})
for rel in ['ja103805s/visuals/apparatus-independent-audit/independent-audit-v1.json','acs.inorgchem.7b01711/package-freeze.json']:
 p=M/base/rel;t=D/base/rel;expected=policy.transform_bytes(base+rel,p.read_bytes())
 assert t.exists() and t.read_bytes()==expected,rel
for port in [5193,5194]:
 s=socket.socket();s.settimeout(1);result=s.connect_ex(('127.0.0.1',port));s.close();assert result!=0, f'Preview {port} still listening'
print(json.dumps({'final_receipts_projected':len(proof),'new_audit_and_source_freeze_present':True,'owned_previews_stopped':True}))
