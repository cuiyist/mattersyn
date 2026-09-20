"""Preserve first independent read and resolve its single typing error from pixels."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib
R=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8'))
dump=lambda p,x:Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
initial=R/'si-pages09-10-independent-reading.json'
comparison=R/'si-pages09-10-independent-comparison.json'
archive=R/'si-pages09-10-independent-comparison-initial.json'
if archive.exists():
 assert archive.read_bytes()==comparison.read_bytes(), 'Do not replace a previous initial comparison'
else: archive.write_bytes(comparison.read_bytes())
resolved=read(initial)
assert resolved['blocks']['9R'][21][5]=='11777.73'
resolved['blocks']['9R'][21][5]='11177.73'
resolved['basis']+=' One auditor typing error was resolved only after native magnified reinspection; initial reading is retained unchanged.'
resolved['initial_reading_path']=str(initial)
resolved['initial_reading_sha256']=sha(initial)
rp=R/'si-pages09-10-independent-reading-resolved.json';dump(rp,resolved)
resolution=[
 {'id':'SI9R13-Fobs2','row_id':'si-p09-R-r013','hkl':[8,24,24],'field':'Fobs2','initial_author_value':'60085.61','initial_auditor_value':'50085.61','source_value':'50085.61','required_change':'author transcription','detail':'p9-R13-detail.png'},
 {'id':'SI9R22-sigma','row_id':'si-p09-R-r022','hkl':[3,3,25],'field':'sigma_Fobs2','initial_author_value':'11177.73','initial_auditor_value':'11777.73','source_value':'11177.73','required_change':'independent auditor transcription; author was correct','detail':'p9-R22-detail.png'},
 {'id':'SI10R24-Fcal2','row_id':'si-p10-R-r024','hkl':[6,6,26],'field':'Fcal2','initial_author_value':'216556.06','initial_auditor_value':'216566.06','source_value':'216566.06','required_change':'author transcription','detail':'p10-R24-detail.png'}]
for r in resolution:
 p=R/'reader-assets'/'si-pages09-10-independent'/r['detail'];r.update({'detail_path':str(p),'detail_sha256':sha(p),'source_reinspection':'Original native scan rectangle, magnified 2x with nearest-neighbor; source digits visually read and unambiguous.'})
out={'schema':'mattersyn-independent-reading-resolution/1','auditor':'/root/norberg2004_extract','created_at':datetime.now(timezone.utc).isoformat(),'initial_author_checkpoint_sha256':'bd7a33eb0fda9cc82b4010b0353c5dd2c5fcf236660c90d4147408c207454bb7','initial_author_manifest_sha256':'f9fe21b0b42271a5368facbce0332bad0d2019c696e6bb2a211d682c74e86e84','initial_reading':{'path':str(initial),'sha256':sha(initial)},'initial_comparison':{'path':str(archive),'sha256':sha(archive)},'resolved_reading':{'path':str(rp),'sha256':sha(rp)},'differences':resolution,'author_correction_status':'requested; separate final audit must verify corrected boundary','author_files_changed_by_auditor':False}
dump(R/'si-pages09-10-independent-resolution-history.json',out)
print(json.dumps({'status':'single auditor typo resolved with initial reading preserved','initial_sha256':sha(initial),'resolved_sha256':sha(rp)}))
