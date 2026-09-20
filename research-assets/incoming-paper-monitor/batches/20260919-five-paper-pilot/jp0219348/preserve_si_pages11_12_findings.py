"""Preserve the initial independent/author comparison and source findings."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
R=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8'));dump=lambda p,x:Path(p).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
p=R/'si-pages11-12-independent-comparison.json';dest=R/'si-pages11-12-independent-comparison-initial.json'
assert read(p)['author_checkpoint_sha256']=='6579e0a2e3da5f12809bdfad7116b83373b8206ae3ee135d39ff49104983389e'
if dest.exists():assert dest.read_bytes()==p.read_bytes()
else:dest.write_bytes(p.read_bytes())
findings=[
 {'cell_id':'si-p11-R-r033-sigma_Fobs2','hkl':[5,11,27],'type':'author_digit_error','initial_author_token':'7604.83','independent_token':'7694.83','source_digits':'7694.83','required_final_token':'7694.83','resolution':'A new native 3x detail unambiguously confirms the 9; bounded author correction requested.','detail':'p11-R33-detail.png'},
 {'cell_id':'si-p11-R-r035-Fobs2','hkl':[9,11,27],'type':'source_sign_uncertainty','initial_independent_provisional_token':'-1965.46','source_digits':'1965.46','signed_value_candidates':[-1965.46,1965.46],'required_numeric_value':None,'resolution':'Both reviewers cannot establish the sign from the degraded native mark. Keep an explicitly editorial sign-unresolved token, clear digits and candidate signs; do not assert either sign.','detail':'p11-R35-detail.png'},
 {'cell_id':'si-p12-L-r012-Fcal2','hkl':[11,17,27],'type':'source_sign_uncertainty','initial_independent_provisional_token':'3757.09','source_digits':'3757.09','signed_value_candidates':[-3757.09,3757.09],'required_numeric_value':None,'resolution':'The initial positive reading and scan-speck interpretation are not sufficiently certain. Both reviewers preserve the degraded prefix as unresolved, without physical inference from Fcal². This supersedes the positive-value interpretation in the initial source-sign note.','detail':'p12-L12-detail.png'}]
for f in findings:
 p=R/'reader-assets/si-pages11-12-independent'/f['detail'];f['detail_path']=str(p);f['detail_sha256']=sha(p)
out={'schema':'mattersyn-independent-si-source-findings/1','auditor':'/root/norberg2004_extract','created_at':datetime.now(timezone.utc).isoformat(),'initial_author_manifest_sha256':'0e70e5d2c4afccde345e96fbcbb2fd4d33336a206f11b7e54b49855242e7a3a8','initial_author_checkpoint_sha256':'6579e0a2e3da5f12809bdfad7116b83373b8206ae3ee135d39ff49104983389e','initial_independent_reading_sha256':sha(R/'si-pages11-12-independent-reading.json'),'initial_comparison':{'path':str(dest),'sha256':sha(dest)},'findings':findings,'status':'awaiting exact final author recheck; no final audit asserted','author_files_changed_by_auditor':False}
dump(R/'si-pages11-12-independent-resolution-history.json',out)
print(json.dumps({'status':'initial reading/comparison retained; one digit correction and two unresolved signs recorded'}))
