from pathlib import Path
import json,hashlib,copy
B=Path(__file__).resolve().parent;S=B.parents[3]/'recipe-atlas';O=B/'neutralized-references';O.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
reg=S/'dist/assets/chemical-registry'
e=next(e for e in read(reg/'registry.json')['entries']if e['id']=='dimethylformamide');old=copy.deepcopy(e)
stale='QDOH clear colloidal suspension; not specified as an input to the principal synthesis. '
newcaption='Conventional free-molecule connectivity and a locally computed illustrative conformer only; not a measured solution geometry, surface state or specimen crystal.'
e['caption']=newcaption;e['limitations']=[x.replace(stale,'') for x in e['limitations']]
files=[]
for key in ['svgPath','model2dPath','model3dPath']:
 src=reg/e[key];dst=O/e[key];dst.parent.mkdir(parents=True,exist_ok=True)
 text=src.read_text(encoding='utf-8').replace(stale,'');dst.write_text(text,encoding='utf-8')
 if key!='svgPath':
  before=read(src);after=read(dst)
  for k in ['atoms','bonds','functionalGroups']:assert before.get(k)==after.get(k)
 e['assetHashes'][key]=sha(dst);files.append({'path':e[key],'before_sha256':sha(src),'sha256':sha(dst)})
write(O/'registry-updates.json',{'entries':[e],'before_entries':[old],'files':files,'scope':'Remove Veinot-specific QDOH use statement from shared DMF display metadata only. Original reference provenance and all chemical coordinates/connectivity unchanged.'})
print('Staged source-neutral DMF captions; model atoms/bonds/groups unchanged.')
