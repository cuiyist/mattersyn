from pathlib import Path
import tarfile,json,hashlib
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas';p=S/'.sites-runtime/site-schwartz2003.tar.gz'
with tarfile.open(p,'r:gz') as t:
 names={m.name.removeprefix('./') for m in t.getmembers()}
 assert 'dist/.openai/hosting.json' in names and 'dist/index.html' in names
 manifest=json.load(t.extractfile('dist/.openai/hosting.json'))
 assert manifest['project_id']=='appgprj_6aaad65d939881918d6b5d5254e0f0d9'
 assert 'dist/data/paper-reviews/schwartz2003.json'in names and 'dist/schwartz2003-protocol.mjs'in names
 assert not any('/.git/'in x or x.startswith('.git/')for x in names)
v={'status':'passed','archive':str(p),'size_bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'entry_count':len(names),'source_commit':json.loads((B/'publication-source.json').read_text(encoding='utf-8'))['commit_sha']}
(B/'archive-validation.json').write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8');print(json.dumps(v))

