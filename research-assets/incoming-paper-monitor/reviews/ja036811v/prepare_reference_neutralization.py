from pathlib import Path
from copy import deepcopy
import json,hashlib,re,html
B=Path(__file__).resolve().parent;V=B/'visuals';S=B.parents[3]/'recipe-atlas';R=S/'dist/assets/chemical-registry';O=V/'neutralized'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
before=next(e for e in read(R/'registry.json')['entries']if e['id']=='dimethyl-sulfoxide');e=deepcopy(before)
caption='Dimethyl sulfoxide reference connectivity and computed free-molecule conformer. Grade, concentration, reaction role and sample preparation belong to each source record. This reference is not a measured solution complex, hydration structure or surface-bound ligand geometry.'
e['caption']=caption;e['limitations']=['Reference geometry is illustrative and excluded from measured crystal-structure labels. Source-specific solvent grade and use are not inferred.'];e.setdefault('provenance',{})['previousSourceSpecificDisplayText']={'caption':before.get('caption'),'limitations':before.get('limitations')}
files=[]
for k in ['svgPath','model2dPath','model3dPath']:
 name=e.get(k)
 if not name:continue
 src=R/name;dst=O/name;dst.parent.mkdir(parents=True,exist_ok=True)
 if k=='svgPath':
  t=src.read_text(encoding='utf8');u=re.sub(r'<desc>.*?</desc>','<desc>'+html.escape(caption)+'</desc>',t,flags=re.S)
  if u==t and '<desc>'not in t:u=t.replace('</svg>','<desc>'+html.escape(caption)+'</desc></svg>')
  dst.write_text(u,encoding='utf8')
 else:
  m=read(src);new=deepcopy(m);new['caption']=caption;assert new['atoms']==m['atoms']and new['bonds']==m['bonds'];write(dst,new)
 files.append({'path':name,'before_sha256':sha(src),'sha256':sha(dst),'private_path':str(dst)});e['assetHashes'][k]=sha(dst)
hb=next(x for x in read(R/'registry.json')['entries']if x['id']=='helium');ha=deepcopy(hb);ha['limitations']=['Element identity only; a single-atom symbol is sufficient.'];ha.setdefault('provenance',{})['previousSourceSpecificLimitations']=hb.get('limitations')
write(V/'registry-neutralizations.json',{'scope':'Shared DMSO and helium display metadata only; original identity provenance and exact molecular graph/coordinates retained. Previously paper-specific grade/QDOH/NMR/carrier-gas wording remains recorded in provenance, not displayed as universal conditions.','source_registry_sha256':sha(R/'registry.json'),'updates':[{'id':e['id'],'before':before,'after':e},{'id':'helium','before':hb,'after':ha}],'files':files})
print('Prepared DMSO/helium metadata neutralization with exact before/after hashes; Site unchanged.')
