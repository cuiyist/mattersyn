from pathlib import Path
import json,hashlib
J=Path(__file__).resolve().parent;p=J/'release-config.json';c=json.loads(p.read_text('utf-8-sig'));a=J/c['browser_delta_audit']['path'];report=json.loads(a.read_text('utf8'));assert report['status']=='passed' and not report['open_findings'];c['browser_delta_audit']['sha256']=hashlib.sha256(a.read_bytes()).hexdigest();c.update(status='all_local_gates_passed_ready_for_verified_delivery',ready_for_root_execution=True,version_is_proposed_until_root_verifies=False);p.write_text(json.dumps(c,indent=2)+'\n','utf8')
