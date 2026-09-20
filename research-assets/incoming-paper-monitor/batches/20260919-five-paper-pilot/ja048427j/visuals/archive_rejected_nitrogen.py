from pathlib import Path
import hashlib,json
V=Path(__file__).resolve().parent;M=V/'molecules';target=M/'rejected-nitrogen-candidate';target.mkdir(exist_ok=True);files=[]
for relative in ['reused/svg/nitrogen.svg','reused/models/nitrogen-2d.json','reused/models/nitrogen-3d.json','review/nitrogen-2d.png','review/nitrogen-3d.png','review/nitrogen-projection.svg']:
    p=M/relative
    if p.exists():
        assert p.resolve().is_relative_to(M.resolve())
        dest=target/p.name;digest=hashlib.sha256(p.read_bytes()).hexdigest();p.rename(dest);files.append({'original_path':relative,'archived_path':str(dest),'sha256':digest,'eligible_for_reuse':False})
(target/'rejection.json').write_text(json.dumps({'status':'rejected before author freeze','reported_by':'independent reviewer backlog_eta','reason':'Old N2 model has 1.460 Å N–N distance. Generic bond plausibility window failed to catch this specific reference error.','replacement':'norberg2004-nitrogen-reference, derived from audited gu2004-nitrogen-reference/NIST 1.09768 Å geometry','lesson':'Verify reference-specific bond constants where available; graph and broad range checks alone do not establish geometry validity.','files':files},indent=2)+'\n')
