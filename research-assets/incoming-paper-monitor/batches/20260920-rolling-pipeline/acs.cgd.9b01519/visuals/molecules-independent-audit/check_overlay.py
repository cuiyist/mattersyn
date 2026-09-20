"""Independent bounded molecular v2 overlay checks; no author/Site writes."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;P=O.parent/'molecules';X=P/'canonical-v2-rebind';R=O.parents[1]
sys.path.insert(0,str(R.parents[4]/'research-assets/corpus-20260917/runtime'))
import pymupdf
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jsha(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def ptr(x,p):
 for k in p.strip('/').split('/'):
  k=k.replace('~1','/').replace('~0','~');x=x[int(k)]if isinstance(x,list)else x[k]
 return x
def delta(a,b,p=''):
 if type(a)!=type(b):return [{'pointer':p,'before':a,'after':b}]
 if isinstance(a,dict):
  out=[]
  for k in sorted(set(a)|set(b)):
   q=p+'/'+k.replace('~','~0').replace('/','~1')
   out+=delta(a[k],b[k],q) if k in a and k in b else [{'pointer':q,'before':a.get(k),'after':b.get(k)}]
  return out
 if isinstance(a,list):
  if len(a)!=len(b):return [{'pointer':p,'before':a,'after':b}]
  return [d for i,(x,y)in enumerate(zip(a,b))for d in delta(x,y,p+'/'+str(i))]
 return []if a==b else[{'pointer':p,'before':a,'after':b}]
checks=[];bound={}
def ck(s,v):checks.append({'check':s,'passed':bool(v)});assert v,s
def bind(p):p=Path(p).resolve();bound[str(p)]=sha(p);return p
freeze=read(bind(X/'package-freeze.json'))
ck('Exact frozen overlay',sha(X/'package-freeze.json')=='f2b0607fc8b503e8512ffd07720bf75c61a6be46d4ec4e2b646fe1e9a0cd815f')
for p,h in freeze['bound_files'].items():ck('Frozen '+p,sha(bind(p))==h)
for p,h in read(O/'independent-audit-v1.json')['bound_files'].items():ck('Original audit boundary '+p,sha(bind(p))==h)
files=read(bind(X/'effective-file-map.json'));assets=read(bind(X/'effective-public-assets.json'))
for k,v in files.items():ck('Effective logical file '+k,sha(bind(v['path']))==v['sha256'])
ck('Eight logical files',len(files)==8)
def effective(n):return read(files[n]['path'])
reported=read(X/'rebind-delta.json');exact_deltas={}
for n,expected in reported['changes'].items():
 actual=delta(read(P/n),effective(n));exact_deltas[n]=actual
 ck('Exact complete reported delta '+n,actual==expected)
oldassets={x['path']:x['sha256']for x in read(P/'public-asset-proposal.json')['assets']}
ck('36 unchanged asset identities',set(assets)==set(oldassets) and len(assets)==36)
changed=[]
for name,row in assets.items():
 ck('Effective asset '+name,sha(bind(row['path']))==row['sha256'])
 if row['sha256']!=oldassets[name]:changed.append(name)
 if name.startswith('models/'):ck('Model bytes invariant '+name,row['sha256']==oldassets[name])
ck('Exactly one water SVG changed',changed==['svg/sommer2020-insitu-water-reference.svg'])
svgname=changed[0];oldsvg=(P/svgname).read_text(encoding='utf8');newsvg=Path(assets[svgname]['path']).read_text(encoding='utf8');expected=oldsvg
for row in reported['svg_text_replacements']:
 ck('Text occurrences '+row['before'],expected.count(row['before'])==row['occurrences']);expected=expected.replace(row['before'],row['after'])
ck('SVG text-only complete delta',newsvg==expected)
ck('SVG neutral scope', 'nitrate-stock' not in newsvg and 'in situ nitrate preparation' not in newsvg and 'grade unspecified' in newsvg)
preview=bind(X/'previews/sommer2020-insitu-water-reference.png')
with pymupdf.open(stream=newsvg.encode(),filetype='svg')as doc:
 pix=doc[0].get_pixmap(alpha=False);png=pymupdf.Pixmap(str(preview));ck('Corrected preview exact fresh pixels',(pix.width,pix.height,pix.n)==(png.width,png.height,png.n) and pix.samples==png.samples)
manifest=read(bind(freeze['canonical_record_manifest']['path']));ck('Correct canonical v2 manifest',sha(freeze['canonical_record_manifest']['path'])==freeze['canonical_record_manifest']['sha256'])
audit=read(bind(freeze['canonical_audit']['path']));ck('Distinct canonical v2 passed',audit['status']=='passed'and sha(freeze['canonical_audit']['path'])==freeze['canonical_audit']['sha256'])
records={};paths={}
for row in manifest['records']:
 paths[row['record_id']]=bind(row['path']);records[row['record_id']]=read(row['path']);ck('Final record '+row['record_id'],sha(row['path'])==row['sha256'])
registry=effective('registry-additions.json');entries={e['id']:e for e in registry['entries']};bindings=effective('bindings-proposal.json');slots=effective('material-slot-map.json')['slots'];stocks=effective('stock-component-map.json')['stocks']
ck('All record assignments invariant',bindings['recordBindings']==read(P/'bindings-proposal.json')['recordBindings'])
ck('62 exact slots retained',len(slots)==62 and {(s['record_id'],s['material_id'])for s in slots}=={(rid,m['id'])for rid,r in records.items()for m in r['materials']})
qrefs=0
def qs(refs,label):
 global qrefs
 for i,q in enumerate(refs):ck(label+' quantity'+str(i),ptr(records[q['record_id']],q['json_pointer'])==q['quantity']);qrefs+=1
for s in slots:
 rid=s['record_id'];mid=s['material_id'];key=rid+'/'+mid
 ck(key+' exact v2 material',ptr(records[rid],s['json_pointer'])==s['canonical_identity'])
 ck(key+' current record hash',sha(paths[rid])==s['canonical_record_sha256'])
 ck(key+' effective entry',jsha(entries[s['registry_id']])==s['entry_sha256'])
 ck(key+' exact binding note',bindings['bindingNotes'][rid][mid]==s)
 ck(key+' still not self-approved',s['binding_approved']is False)
 qs(s['quantity_links']+s['grade_context_links'],key)
for s in stocks:
 rid=s['record_id'];key=rid+'/'+s['stock_id']
 ck(key+' current hash',sha(paths[rid])==s['canonical_record_sha256'])
 ck(key+' exact final stock',ptr(records[rid],s['json_pointer'])==s['canonical_stock'])
 qs(s['concentration_links']+s['solution_quantity_links'],key)
 for c in s['components']:
  ck(key+'/'+c['material_id']+' exact quantities',ptr(records[rid],c['json_pointer'])['quantities']==c['source_quantities']);qs(c['quantity_links'],key+'/'+c['material_id'])
ck('Seven unchanged selectors',files['solution-components-proposal.json']['sha256']==sha(P/'solution-components-proposal.json'))
s=bindings['bindingNotes']['sommer-2020-scf-route']['insitu-water'];ck('SCF method-qualified title',s['viewOverrides']['name']=='Aqueous SCF solvent')
ck('SCF exact missingness note',records['sommer-2020-scf-route']['materials'][3]['notes'][0]in s['viewOverrides']['caption'])
ck('SCF no inherited charges and flow preserved','No in situ nitrate-stock preparation, salt charge or solution volume is inherited' in s['viewOverrides']['caption']and '14.5 mL/min' in s['viewOverrides']['caption'])
for e in entries.values():
 for kind in ['svgPath','model2dPath','model3dPath']:
  if e.get(kind):ck(e['id']+' final '+kind,e['assetHashes'][kind]==assets[e[kind]]['sha256'])
out={'schema':'mattersyn-independent-molecular-overlay-checks/1','reviewer':'/root/backlog_eta','author':'/root/peng1998_reader_assets','created_at':datetime.now(timezone.utc).isoformat(),'status':'passed','check_count':len(checks),'checks':checks,'exact_deltas':exact_deltas,'quantity_references_rechecked':qrefs,'bound_files':bound,'finding_SM1':'resolved by text-only water SVG and exact SCF display override; no molecular model changes'}
(O/'checks-v2-overlay.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':'passed','checks':len(checks),'quantity_references':qrefs,'bound_files':len(bound)}))
