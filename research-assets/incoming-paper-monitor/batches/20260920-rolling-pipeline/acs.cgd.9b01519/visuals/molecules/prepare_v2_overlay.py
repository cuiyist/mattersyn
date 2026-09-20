"""Preserve the original molecule freeze; rebind only approved canonical metadata."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
import json,hashlib,sys,xml.etree.ElementTree as ET
O=Path(__file__).resolve().parent;P=O.parents[1];D=O/'canonical-v2-rebind';M=P.parents[4]
sys.dont_write_bytecode=True;sys.path.insert(0,str(M/'research-assets/corpus-20260917/runtime'))
import pymupdf
assert not(D/'package-freeze.json').exists()
D.mkdir(exist_ok=True)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jsha(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def save(n,x):
 p=D/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def ptr(x,p):
 for t in p.strip('/').split('/'):x=x[int(t)]if isinstance(x,list)else x[t]
 return x
def diff(a,b,p=''):
 if type(a)!=type(b):return[{'pointer':p,'before':a,'after':b}]
 if isinstance(a,dict):return sum([diff(a.get(k),b.get(k),p+'/'+k.replace('~','~0').replace('/','~1'))for k in sorted(a.keys()|b.keys())],[])
 if isinstance(a,list):
  if len(a)!=len(b):return[{'pointer':p,'before':a,'after':b}]
  return sum([diff(x,y,p+'/'+str(i))for i,(x,y)in enumerate(zip(a,b))],[])
 return []if a==b else[{'pointer':p,'before':a,'after':b}]
basefreeze=read(O/'package-freeze.json');assert sha(O/'package-freeze.json')=='27436ab4627bd5efe80cc7aa6a226579ba0337735768e45740ca5e6ee23e4b13'
for p,h in basefreeze['bound_files'].items():assert sha(p)==h,'Original freeze changed: '+p
cm=P/'canonical-proposal/v2/record-manifest.json';manifest=read(cm);records={r['record_id']:read(r['path'])for r in manifest['records']};paths={r['record_id']:Path(r['path'])for r in manifest['records']}
checks=[]
def ck(label,v):checks.append({'check':label,'passed':bool(v)});assert v,label
for r in manifest['records']:ck('Canonical v2 hash '+r['record_id'],sha(r['path'])==r['sha256'])
# SVG geometry and connectivity paths remain byte-identical; only text changes.
rel='svg/sommer2020-insitu-water-reference.svg';oldsvg=(O/rel).read_text();newsvg=oldsvg.replace('Water-based nitrate-stock solvent','Water reference · grade unspecified').replace('Grade not specified in the in situ nitrate preparation.','Water grade is unspecified for this context; other water grades are not inherited.')
ck('Four exact SVG text replacements',oldsvg.count('Water-based nitrate-stock solvent')==2 and oldsvg.count('Grade not specified in the in situ nitrate preparation.')==2)
(D/'svg').mkdir(exist_ok=True);(D/rel).write_text(newsvg,encoding='utf8');(D/'previews').mkdir(exist_ok=True)
doc=pymupdf.open(stream=newsvg.encode(),filetype='svg');doc[0].get_pixmap(alpha=False).save(str(D/'previews/sommer2020-insitu-water-reference.png'));doc.close()
a=ET.fromstring(oldsvg);b=ET.fromstring(newsvg)
for x,y in zip(a.iter(),b.iter()):ck('SVG unchanged element geometry '+x.tag,x.tag==y.tag and x.attrib==y.attrib)
reg=read(O/'registry-additions.json');target=next(e for e in reg['entries']if e['id']=='sommer2020-insitu-water-reference');target['assetHashes']['svgPath']=sha(D/rel);entries={e['id']:e for e in reg['entries']};save('registry-additions.json',reg)
bindings=read(O/'bindings-proposal.json');slots=read(O/'material-slot-map.json');stocks=read(O/'stock-component-map.json')
for row in slots['slots']:
 rid=row['record_id'];mid=row['material_id'];newmat=ptr(records[rid],row['json_pointer']);changes=diff(row['canonical_identity'],newmat)
 ck(rid+'/'+mid+' allowed material identity changes',not changes or(rid=='sommer-2020-scf-route'and mid=='insitu-water'and set(x['pointer']for x in changes)<={'/name','/notes/0'}))
 row['canonical_record_sha256']=sha(paths[rid]);row['canonical_identity']=deepcopy(newmat);row['entry_sha256']=jsha(entries[row['registry_id']])
 if rid=='sommer-2020-scf-route'and mid=='insitu-water':
  e=entries[row['registry_id']];caption='Aqueous SCF solvent; source-specific water reference. '+newmat['notes'][0]+' Context-specific quantity: solvent flow rate: '+row['quantity_links'][0]['display_value']+'. '+e['limitations'][-1]+' Storage conditions are not supplied for this material context.'
  row['viewOverrides']={'name':'Aqueous SCF solvent','caption':caption,'limitations':[newmat['notes'][0],e['limitations'][-1]]}
 bindings['bindingNotes'][rid][mid]=deepcopy(row)
for row in stocks['stocks']:
 rid=row['record_id'];ck(rid+'/'+row['stock_id']+' exact stock unchanged',ptr(records[rid],row['json_pointer'])==row['canonical_stock']);row['canonical_record_sha256']=sha(paths[rid])
save('bindings-proposal.json',bindings);save('material-slot-map.json',slots);save('stock-component-map.json',stocks)
inputs=read(O/'input-bindings.json');inputs['canonical_record_manifest']={'path':str(cm),'sha256':sha(cm)};inputs['canonical_records']={str(paths[rid]):sha(paths[rid])for rid in records}
ca=P/'canonical-reader-independent-audit/independent-audit-v2.json';ck('Canonical v2 independently passed',sha(ca)=='8bf47e1fb1d72c074d050e1638d68add32a29faf7f5013fbe9cc3e159088c12c' and read(ca)['status'].startswith('passed'));inputs['canonical_independent_audit']={'path':str(ca),'sha256':sha(ca)};save('input-bindings.json',inputs)
allow=read(O/'public-asset-proposal.json')
for x in allow['assets']:
 if x['path']==rel:x['sha256']=sha(D/rel)
save('public-asset-proposal.json',allow)
replacement_names=['registry-additions.json','bindings-proposal.json','material-slot-map.json','stock-component-map.json','input-bindings.json','public-asset-proposal.json']
effective={name:{'path':str(D/name),'sha256':sha(D/name)}for name in replacement_names}
for name in ['solution-components-proposal.json','reference-qualification.json']:effective[name]={'path':str(O/name),'sha256':sha(O/name)}
save('effective-file-map.json',effective)
save('effective-public-assets.json',{x['path']:{'path':str(D/x['path']if x['path']==rel else O/x['path']),'sha256':x['sha256']}for x in allow['assets']})
delta={n:diff(read(O/n),read(D/n))for n in replacement_names};save('rebind-delta.json',{'base_freeze_sha256':sha(O/'package-freeze.json'),'canonical_v2_manifest_sha256':sha(cm),'canonical_independent_audit':inputs['canonical_independent_audit'],'changes':delta,'svg_text_replacements':[{'before':'Water-based nitrate-stock solvent','after':'Water reference · grade unspecified','occurrences':2},{'before':'Grade not specified in the in situ nitrate preparation.','after':'Water grade is unspecified for this context; other water grades are not inherited.','occurrences':2}],'unchanged_model_hashes':{str(p.relative_to(O)):sha(p)for p in sorted((O/'models').glob('*.json'))},'all_model_bytes_unchanged':True,'stock_quantities_and_components_unchanged':True,'recordBindings_unchanged':bindings['recordBindings']==read(O/'bindings-proposal.json')['recordBindings'],'checks':checks,'check_count':len(checks),'pending':'Corrected SVG preview receipt and distinct molecular overlay audit.'})
print(json.dumps({'status':'overlay_built_unapproved','canonical_manifest_sha256':sha(cm),'checks':len(checks),'changed_public_assets':1,'unchanged_models':8}))
