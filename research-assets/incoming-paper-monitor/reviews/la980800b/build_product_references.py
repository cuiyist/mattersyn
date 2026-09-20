from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parent;O=R/'molecular-assets'
def load(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
entries={e['id']:e for e in load(O/'registry-additions.json')['entries']}
refs={};products={};notes={};hashes={};excluded=[];checks=[]
def check(v,s):checks.append({'check':s,'passed':bool(v)})
for p in sorted((R/'canonical-drafts').glob('*.json')):
 r=load(p);rid=r['record_id'];key=rid.replace('stiger-1999-','')
 default='identity-stiger-transferred-ag' if key=='tem-saed' else 'identity-stiger-h-si' if key in ['open-circuit-control','silver-free-pulse-control','cyclic-voltammetry'] else 'identity-stiger-ag-si'
 refs[rid]=default;hashes[rid]=sha(p);products[rid]={}
 notes[rid]='Reader identity reference only; not a solved unit cell, measured coordinates or an experimental sample join. '+entries[default]['caption']
 if key=='cyclic-voltammetry':notes[rid]+=' The reference shows the starting silicon-surface identity only; four electrolyte/doping comparison contexts have no universal observed product composition.'
 if key=='characterization':notes[rid]+=' The record-level card illustrates the Ag/Si synthesis context; individual Si, transferred-Ag, and theoretical/contextual entries remain separately scoped. Composition-null contexts receive no sample-level card.'
 for sample in r['products']:
  c=sample.get('composition',{}).get('value');sid=sample['sample_id']
  if not c:
   excluded.append({'record_id':rid,'sample_id':sid,'reason':'No physical product composition is assigned here; no sample-level molecular or solid identity is inferred.'});continue
  if 'mechanically transferred' in c:ref='identity-stiger-transferred-ag'
  elif c.startswith('Ag nanocrystals on Si'):ref='identity-stiger-ag-si'
  elif c.startswith('Si(100)'):
   ref='identity-stiger-si-npp' if sid=='npp-si-substrate' else 'identity-stiger-si-n' if sid=='n-si-substrate' else 'identity-stiger-h-si'
  else:raise ValueError((rid,sid,c))
  products[rid][sid]=ref;check(ref in entries,rid+'/'+sid+' identity exists')
  check(entries[ref]['model2dPath'] is None and entries[ref]['model3dPath'] is None,rid+'/'+sid+' illustrative card without invented coordinates')
  entries[ref]['provenance']['sourceRecords'].append({'recordId':rid,'sampleId':sid,'evidence':sample['composition'].get('evidence',[]),'role':'Optional reader identity only, not canonical input binding'})
 check(default in entries,rid+' record reference exists')
check(all('Ag' not in entries[v]['formula'] for r,m in products.items() if r.endswith('control') for v in m.values()),'Controls do not acquire Ag identity')
check(products['stiger-1999-tem-saed']=={'tem-saed-context':'identity-stiger-transferred-ag'},'TEM product is transferred Ag; no Si wafer geometry')
out={'scope':'Optional reader identity illustrations; not measured structures or canonical synthesis inputs','sourceDoi':'10.1021/la980800b','eligible_training':False,'references':refs,'productBindings':products,'bindingNotes':notes,'sourceRecordSha256':hashes,'excludedNonphysicalContexts':excluded,'validation':{'status':'passed' if all(c['passed'] for c in checks) else 'failed','checks':checks},'crystalReferencePolicy':'No crystal mapping added. No verified local Ag CIF was available; existing ideal Si finite-particle reference is not an appropriate wafer representation. This paper supplies no measured atomic coordinates or solved Ag/Si interface.'}
(O/'product-reference-proposal.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
# Add product evidence to new reference metadata without touching any asset coordinates or depictions.
reg=load(O/'registry-additions.json');reg['entries']=list(entries.values());(O/'registry-additions.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
prov=load(O/'model-provenance.json');prov['entries']=[{'id':e['id'],'provenance':e['provenance'],'assetHashes':e['assetHashes']} for e in entries.values()];(O/'model-provenance.json').write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'references':len(refs),'physical_sample_bindings':sum(map(len,products.values())),'excluded_unassigned_contexts':len(excluded),'status':out['validation']['status']}))
