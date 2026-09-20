"""Preserve a later reading addendum while restoring immutable author inputs."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess
P=Path(__file__).resolve().parent;M=P.parents[4];D=M.parent/'mattersyn-github-project'
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda b:hashlib.sha256(b).hexdigest()
note=P/'root-preview-reading.md';add=P/'root-source-reading-addendum-20260920.md'
expected={read(P/r)['bound_files'][str(note)] for r in ['visuals/apparatus/package-freeze.json','visuals/product-context/package-freeze.json']};assert len(expected)==1
expected=expected.pop();current=note.read_bytes();assert sha(current)!=expected
rel=note.relative_to(M).as_posix();cmd=[r'C:/Program Files/Git/cmd/git.exe','-c','safe.directory='+D.as_posix(),'-c','core.longpaths=true','-C',str(D)]
commits=subprocess.check_output(cmd+['log','-8','--format=%H','--',rel],text=True).splitlines();original=None
for commit in commits:
 raw=subprocess.check_output(cmd+['show',commit+':'+rel])
 if sha(raw)==expected:original=raw;origin=commit;break
assert original is not None,'Original expected bytes must be found before restoration.'
assert not add.exists();add.write_bytes(current);note.write_bytes(original)
assert sha(note.read_bytes())==expected and sha(add.read_bytes())==sha(current)
receipt={'status':'restored_exact_original_bound_bytes','at':datetime.now(timezone.utc).isoformat(),'original_path':str(note),'original_sha256':expected,'recovered_from_project_commit':origin,'later_note_preserved_at':str(add),'later_note_sha256':sha(current),'scientific_package_files_changed':False,'frozen_manifests_changed':False,'reason':'Root later extended an ancillary reading note that author freezes already bound; preserve the extension separately and recover the exact original note.'}
(P/'site-integration-proposal/ancillary-note-restoration.json').write_text(json.dumps(receipt,indent=2)+'\n','utf8')
print(json.dumps(receipt))
