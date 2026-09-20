from pathlib import Path
import sys,json,hashlib,xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
sys.path.insert(0,'[local path redacted]')
sys.path.insert(0,'[local path redacted]')
import pymupdf
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent; OLD=Path('[local path redacted]')
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
reg=read(R/'registry-additions.json');old={e['id']:e for e in read(OLD/'registry.json')['entries']};new={e['id']:e for e in reg['entries']};b=read(R/'bindings-additions.json');checks=[]
def check(ok,s):checks.append({'passed':bool(ok),'check':s})
check(len(new)==47 and not(set(new)&set(old)),'Unique new identity IDs with no collision')
ims=[]
for e in reg['entries']:
 for k,h in e['assetHashes'].items():check(sha(R/e[k])==h,e['id']+' '+k+' hash')
 if not e['model3dPath']:
  check(e['model2dPath'] is None,e['id']+' no invented atomic or molecular coordinates')
  svg=(R/e['svgPath']).read_bytes();ET.fromstring(svg)
  doc=pymupdf.open(stream=svg,filetype='svg');pdf=pymupdf.open('pdf',doc.convert_to_pdf());pix=pdf[0].get_pixmap(matrix=pymupdf.Matrix(.7,.7),alpha=False)
  im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples);can=Image.new('RGB',(620,300),'white');can.paste(im,(10,22));ImageDraw.Draw(can).text((12,3),e['id'],fill='black');ims.append(can)
for rid,ms in b['recordBindings'].items():
 p=R.parent/'canonical-drafts'/(rid+'.json');r=read(p);check(sha(p)==b['sourceRecordSha256'][rid],rid+' current record hash')
 check(set(ms)=={m['id'] for m in r['materials']},rid+' every material exactly once')
 for m in r['materials']:
  e={**old,**new}[ms[m['id']]];check(e['formula']==m.get('formula'),rid+'/'+m['id']+' exact formula binding')
for e in read(R/'reused-references.json')['entries']:
 for k,p in e['assetPaths'].items():check(sha(OLD/p)==e['assetHashes'][k],e['id']+' reused '+k+' hash')
for i in range(0,len(ims),6):
 sheet=Image.new('RGB',(1240,900),'#d9e1e6')
 for n,im in enumerate(ims[i:i+6]):sheet.paste(im,(n%2*620,n//2*300))
 sheet.save(R/'review'/('cards-contact-'+str(i//6+1)+'.png'))
save(R/'package-validation.json',{'status':'passed' if all(x['passed'] for x in checks) else 'failed','checks':checks,'passed':sum(x['passed'] for x in checks),'failed':sum(not x['passed'] for x in checks),'summary':reg['summary']})
save(R/'asset-manifest.json',{'sourceDoi':'10.1021/cm970189m','sourceSha256':'eac4fe78e4bc3ab9c15e0409b69232e4294a0c07787d3ca650c378f6341d4adc','illustrative_only':True,'eligible_training':False,'files':[{'path':str(p.relative_to(R)).replace('\\','/'),'sha256':sha(p),'bytes':p.stat().st_size} for folder in ['svg','models','sdf'] for p in sorted((R/folder).glob('*'))]})
# Sync the molecule-only proposal after formula-order normalization without recomputing conformers.
save(R/'molecule-registry-proposal.json',{'schemaVersion':'1.0.0','entries':[e for e in reg['entries'] if e['model3dPath']],'summary':{'newMoleculeEntries':22}})
print(json.dumps({'passed':sum(x['passed'] for x in checks),'failed':sum(not x['passed'] for x in checks),'cardContactSheets':5}))
