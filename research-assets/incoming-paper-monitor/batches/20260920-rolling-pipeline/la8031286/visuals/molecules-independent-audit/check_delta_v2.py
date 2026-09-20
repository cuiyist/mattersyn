from pathlib import Path
import json,hashlib,copy,datetime
A=Path(__file__).resolve().parent;V=A.parent/'molecules';D=V/'annotation-correction-v2';N=A.parents[1]
bound={};checks=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):p=Path(p);bound[str(p)]=sha(p);return json.loads(p.read_text('utf8'))
def ck(name,v):checks.append({'check':name,'passed':bool(v)})
def jsha(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
f=read(D/'package-freeze.json');base=read(V/'package-freeze.json')
ck('Exact author v2 freeze',sha(D/'package-freeze.json')=='35311cb254b6b9970a39f929a1e59380cd78cc1379927f245849aedeb5859c70')
ck('Exact retained original freeze',sha(V/'package-freeze.json')=='8b5724b9a7008dfb74cdc8f5cea7fdfcd47939a26b89d85916aebc77fed7c202')
for label,freeze in [('original',base),('overlay',f)]:
 for p,h in freeze['bound_files'].items():bound[p]=sha(p);ck(label+' bound bytes '+p,sha(p)==h)
filemap=read(D/'effective-file-map.json');assets=read(D/'effective-public-assets.json');oldassets=read(V/'effective-public-assets.json')
for n,x in filemap.items():ck('Effective metadata hash '+n,sha(x['path'])==x['sha256'])
for n,x in assets.items():ck('Effective asset hash '+n,sha(x['path'])==x['sha256'])
modelname='models/pati2009-cerium-nitrate-2d.json';oldmodel=read(V/modelname);newmodel=read(assets[modelname]['path']);expectedmodel=copy.deepcopy(oldmodel)
bad=[g for g in oldmodel['functionalGroups']if g['label']=='Tertiary amine nitrogen'];ck('Exactly three false groups',len(bad)==3 and [g['atomIndices']for g in bad]==[[2],[6],[10]])
expectedmodel['functionalGroups']=[g for g in oldmodel['functionalGroups']if g not in bad]
ck('Exact annotation-only model change',newmodel==expectedmodel)
ck('Exact unchanged graph arrays',newmodel['atoms']==oldmodel['atoms'] and newmodel['bonds']==oldmodel['bonds'])
ck('Retains three nitrates, Ce and six waters',len(newmodel['functionalGroups'])==10 and sum(g['label']=='Nitrate resonance group'for g in newmodel['functionalGroups'])==3 and sum(g['label']=='Water formula component'for g in newmodel['functionalGroups'])==6)
oldreg=read(V/'registry-additions.json');newreg=read(filemap['registry-additions.json']['path']);expectedreg=copy.deepcopy(oldreg);expectedreg['entries'][0]['functionalGroups']=expectedmodel['functionalGroups'];expectedreg['entries'][0]['assetHashes']['model2dPath']=sha(assets[modelname]['path'])
ck('Exact registry annotation and dependent hash only',newreg==expectedreg)
entryhash=jsha(newreg['entries'][0]);entryid=newreg['entries'][0]['id'];ck('TEA tertiary amine preserved',newreg['entries'][1]==oldreg['entries'][1] and any(g['label']=='Tertiary amine nitrogen'for g in newreg['entries'][1]['functionalGroups']))
for name in ['bindings-proposal.json','material-slot-map.json']:
 old=read(V/name);new=read(filemap[name]['path']);exp=copy.deepcopy(old);n=0
 if name.startswith('bindings'):
  for rid,notes in exp['bindingNotes'].items():
   for mid,note in notes.items():
    if exp['recordBindings'][rid][mid]==entryid:note['entry_sha256']=entryhash;n+=1
 else:
  for slot in exp['slots']:
   if slot['registry_id']==entryid:slot['entry_sha256']=entryhash;n+=1
 ck('Exactly four digest dependencies '+name,n==4);ck('All other binding data identical '+name,new==exp)
oldproposal=read(V/'public-asset-proposal.json');newproposal=read(filemap['public-asset-proposal.json']['path']);expected=copy.deepcopy(oldproposal)
for x in expected['assets']:
 if x.get('relative_path')==modelname or x.get('path')==modelname:x['sha256']=sha(assets[modelname]['path'])
ck('Public allowlist changes only affected model digest',newproposal==expected)
ck('All 34 public asset names preserved',set(assets)==set(oldassets)and len(assets)==34)
for name,x in assets.items():
 ck('Only affected model path/hash changes '+name,name==modelname or x==oldassets[name])
 ck('Exact effective asset byte '+name,sha(x['path'])==x['sha256'])
for name,x in filemap.items():
 if name not in ['registry-additions.json','material-slot-map.json','bindings-proposal.json','public-asset-proposal.json']:ck('Unchanged supporting metadata '+name,Path(x['path'])==V/name and sha(x['path'])==sha(V/name))
for p in (N/'canonical-proposal/v2').glob('pati-2009-*.json'):ck('Canonical v2 exact byte bridge '+p.name,sha(p)==sha(N/'canonical-proposal/v1'/p.name))
history=read(D/'correction-history.json');audit=read(N/'canonical-reader-independent-audit/independent-audit-v2.json');ck('Current canonical passed audit bridge',audit['status']=='passed'and f['canonical_v2_receipt']['independent_audit_sha256']==sha(N/'canonical-reader-independent-audit/independent-audit-v2.json'))
result={'schema':'mattersyn-independent-molecule-overlay-checks/1','auditor':'/root/norberg2004_extract','check_count':len(checks),'checks':checks,'failures':[c for c in checks if not c['passed']],'bound_files':bound}
(A/'delta-checks-v2.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
script=(A/'check_consumer_independent.mjs').read_text('utf8')
script=script.replace("const read=p=>JSON.parse(fs.readFileSync(p,'utf8').replace(/^\\ufeff/,''));", """const overlay=path.join(A,'annotation-correction-v2');
const metaMap=JSON.parse(fs.readFileSync(path.join(overlay,'effective-file-map.json'),'utf8'));
const assetMap=JSON.parse(fs.readFileSync(path.join(overlay,'effective-public-assets.json'),'utf8'));
const resolvedPath=p=>{const relative=path.relative(A,p).replaceAll('\\\\','/');return metaMap[relative]?.path||assetMap[relative]?.path||p;};
const read=p=>JSON.parse(fs.readFileSync(resolvedPath(p),'utf8').replace(/^\\ufeff/,''));""")
script=script.replace("const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');", "const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(resolvedPath(p))).digest('hex');")
script=script.replace("consumer-checks-v1.json","consumer-checks-v2.json").replace("[path.resolve(p),sha(p)]","[path.resolve(resolvedPath(p)),sha(p)]")
(A/'check_consumer_effective_v2.mjs').write_text(script,'utf8')
print(json.dumps({'checks':len(checks),'failures':result['failures']}))
