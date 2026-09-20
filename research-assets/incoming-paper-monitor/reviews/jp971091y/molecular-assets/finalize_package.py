"""Hash assets and record completed manual visual checks. Writes privately only."""
import json,hashlib
from pathlib import Path
OUT=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
registry=read(OUT/'registry-additions.json');validation=read(OUT/'validation-report.json')
assert validation['status']=='passed'
visuals=[*sorted((OUT/'review').glob('svg-contact-sheet-*.png')),OUT/'review/computed-models-contact-sheet.png']
assert len(visuals)==4 and all(p.exists() for p in visuals)
validation['visualReview']={'status':'passed','scope':'All 17 actual SVG depictions/cards were rendered and visually inspected. The new octane 3D JSON-coordinate projection were inspected. Numerical topology/charge/geometry checks are in this report; no browser interaction or experimental geometry validation is claimed.',
 'assets':[{'file':p.relative_to(OUT).as_posix(),'sha256':sha(p)} for p in visuals]}
validation['knownGeometryLimit']={'id':'diethylzinc','status':'usable illustrative model with explicit limitation','detail':'No complete installed MMFF/UFF Zn parameterization. ETKDG distance-geometry coordinates are unminimized and labeled as such; no force-field energy is supplied.'}
dump(OUT/'validation-report.json',validation)
files=[]
for folder in ['svg','models','sdf']:
    for p in sorted((OUT/folder).glob('*')):
        if p.is_file():files.append({'file':p.relative_to(OUT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size,'eligible_training':False,'scope':'Illustrative reference only; not experimental sample coordinates'})
metadata=['registry-additions.json','bindings-additions.json','reused-references.json','missing-identities.json','model-provenance.json','molecules-3d-additions.json','validation-report.json']
dump(OUT/'asset-manifest.json',{'sourceDoi':'10.1021/jp971091y','sourceSha256':'dac183303049a3275d4f1874c66ac0ceece9895bc175f7f7e9727ef7c9cd8f9d','summary':registry['summary'],'files':files,
 'metadataHashes':{f:sha(OUT/f) for f in metadata},'scripts':{p.name:sha(p) for p in sorted(OUT.glob('*.py'))},'noSiteChanges':True,'noNetworkRequests':True})
print(json.dumps({'assetFiles':len(files),'summary':registry['summary'],'checks':validation['checkCount'],'registrySha256':sha(OUT/'registry-additions.json'),'bindingSha256':sha(OUT/'bindings-additions.json')}))
