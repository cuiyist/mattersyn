"""Finish the independent molecular audit against effective canonical-v2/metadata-v3."""
from pathlib import Path
from datetime import datetime, timezone
import json,hashlib,copy
A=Path(__file__).resolve().parent;G=A.parent.parent;M=G/'visuals/molecules';V=M/'metadata-correction-v3';R=M/'canonical-v2-rebind'
checks=[];bound={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):
 p=Path(p);bound[str(p)]=sha(p);return json.loads(p.read_text(encoding='utf-8'))
def ck(label,ok):
 checks.append({'check':label,'passed':bool(ok)})
 if not ok:raise AssertionError(label)
def objsha(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def diff(a,b,p=''):
 if type(a)!=type(b):return [(p,a,b)]
 if isinstance(a,dict):
  if set(a)!=set(b):return [(p,a,b)]
  return [x for k in a for x in diff(a[k],b[k],p+'/'+k.replace('~','~0').replace('/','~1'))]
 if isinstance(a,list):
  if len(a)!=len(b):return [(p,a,b)]
  return [x for i,(v,w) in enumerate(zip(a,b)) for x in diff(v,w,p+'/'+str(i))]
 return [] if a==b else [(p,a,b)]
reports={name:read(A/name) for name in ['mechanical-checks-v1.json','rebind-v2-checks.json','actual-viewer-checks-v3.json']}
for n,d in reports.items():ck('independent report passed '+n,d['status']=='passed')
fr=read(V/'package-freeze.json');fm=read(V/'effective-file-map.json');assets=read(V/'effective-public-assets.json')
ck('v3 exact freeze',sha(V/'package-freeze.json')=='a7f7df265a7f34d92d5b16bafed8fcbc234ecea64cf93798ca23b4c2c853c393')
for fn,digest in fr['bound_files'].items():
 p=Path(fn);ck('v3 bound '+fn,p.is_file() and sha(p)==digest);bound[str(p)]=sha(p)
effective={}
for name,row in fm.items():
 ck('effective file '+name,sha(row['path'])==row['sha256']);effective[name]=read(row['path'])
oldmap=read(R/'effective-file-map.json')
modelrel='models/ghosh2012-liquid-nitrogen-reference-3d.json'
oldmodel=read(M/modelrel);newmodel=read(assets[modelrel]['path'])
modeldiff=diff(oldmodel,newmodel)
ck('one source-neutral metadata field only',modeldiff==[('/sourceType','Geometry derived from an external reference, not observed Norberg atomic coordinates','Geometry derived from an external reference; not observed sample coordinates')])
ck('nitrogen arrays exactly unchanged',all(oldmodel[k]==newmodel[k] for k in ['atoms','bonds','functionalGroups','referenceDistanceAngstrom','referenceIsotopologue','coordinateSource','construction']))
reg=effective['registry-additions.json'];origreg=read(M/'registry-additions.json')
entries={e['id']:e for e in reg['entries']};eid='ghosh2012-liquid-nitrogen-reference';index=[e['id'] for e in reg['entries']].index(eid)
ck('registry only one model asset digest',diff(origreg,reg)==[(f'/entries/{index}/assetHashes/model3dPath',sha(M/modelrel),sha(assets[modelrel]['path']))])
ck('updated model digest',sha(assets[modelrel]['path'])=='55894a8e613a3c3b2c6631befe4a458bc4fd879fc2aca533c6e247bc2d13710d')
for name in ['bindings-proposal.json','material-slot-map.json']:
 old=read(oldmap[name]['path']);new=effective[name];changes=diff(old,new)
 ck('only two entry hash leaves '+name,len(changes)==2 and all(p.endswith('/entry_sha256') for p,a,b in changes))
 ck('entry hash exact '+name,all(a==objsha(origreg['entries'][index]) and b==objsha(entries[eid]) for p,a,b in changes))
for name in ['stock-component-map.json','solution-components-proposal.json','reference-qualification.json','input-bindings.json']:
 ck('unchanged effective '+name,fm[name]==oldmap[name])
oldallow=read(M/'public-asset-proposal.json');allow=effective['public-asset-proposal.json']
ck('allowlist only nitrogen digest',diff(oldallow,allow)==[('/relative_asset_files/'+modelrel.replace('/','~1'),sha(M/modelrel),sha(assets[modelrel]['path']))])
ck('48 exact mapped assets',len(assets)==48 and set(assets)==set(allow['relative_asset_files']))
for rel,row in assets.items():
 ck('effective public hash '+rel,sha(row['path'])==row['sha256']==allow['relative_asset_files'][rel]);bound[row['path']]=sha(row['path'])
 if rel!=modelrel:ck('unchanged other public asset '+rel,Path(row['path'])==M/rel and sha(row['path'])==sha(M/rel))
for s in effective['material-slot-map.json']['slots']:
 ck('all88 entry pointers remain exact '+s['record_id']+'/'+s['material_id'],s['entry_sha256']==objsha(entries[s['registry_id']]))
 ck('all88 binding mirrors final '+s['record_id']+'/'+s['material_id'],effective['bindings-proposal.json']['bindingNotes'][s['record_id']][s['material_id']]==s)
canonical=read(G/'canonical-reader-independent-audit/independent-audit-v2.json')
ck('distinct canonical v2 audit exact',sha(G/'canonical-reader-independent-audit/independent-audit-v2.json')=='98b389f3a2f3527815d91f72bd6c0c7431122ec06a78a4b96bf47e85e1887ba3' and canonical['status']=='passed' and not canonical.get('open_findings'))
source=read(G/'source-independent-audit/independent-audit-v2.json')
ck('source v2 exact passed',sha(G/'source-independent-audit/independent-audit-v2.json')=='366bb63e0011c3c1b44d5940e0d1e0f396c04e57ab786cf72ac527cc3d1fd6e0' and source['status']=='passed')
for fn,digest in source['bound_files'].items():
 if Path(fn).suffix.lower()=='.pdf':
  ck('original source bytes '+fn,sha(fn)==digest);bound[fn]=sha(fn)
for report in reports.values():
 for fn,digest in report.get('bound_files',{}).items():
  ck('prior checked bytes remain '+fn,sha(fn)==digest);bound[fn]=digest
manual=read(A/'manual-review-checkpoint.json')
for role,pages in manual['source_pages_actually_reopened'].items():
 for page in pages:
  for folder,suffix in [('source-render','png'),('private/text','txt')]:
   p=G/folder/f'{role}-{page:02d}.{suffix}';bound[str(p)]=sha(p)
for name in manual['all_viewed_contacts']:p=M/'contacts'/name;bound[str(p)]=sha(p)
for p in A.glob('*.py'):bound[str(p)]=sha(p)
for p in A.glob('*.mjs'):bound[str(p)]=sha(p)
for p in [V/'metadata-delta.json',R/'rebind-delta.json',M/'package-freeze.json',R/'package-freeze.json']:bound[str(p)]=sha(p)
finalchecks={'schema':'mattersyn.independent_final_molecular_delta_checks/1','status':'passed','check_count':len(checks),'checks':checks,'model_metadata_delta':modeldiff,'created_at':datetime.now(timezone.utc).isoformat()}
checkpath=A/'final-v3-delta-checks.json';checkpath.write_text(json.dumps(finalchecks,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');bound[str(checkpath)]=sha(checkpath)
history=copy.deepcopy(manual['finding_history']);history[0].update(status='resolved',effective_source_type=newmodel['sourceType'],correction_freeze_sha256=sha(V/'package-freeze.json'))
report={
 'schema':'mattersyn.independent_molecular_source_audit/1','source_id':'ghosh2012','doi':'10.1021/ja212032q','author':'/root/backlog_eta','auditor':'/root/peng1998_reader_assets','created_at':datetime.now(timezone.utc).isoformat(),'status':'passed',
 'scope':'Independent reference identity/graph/geometry qualification, source-specific slot and stock mappings, public asset boundaries, static visual inspection and actual viewer pure-function checks. Effective canonical-v2 plus molecular metadata-v3 overlay only.',
 'base_molecule_freeze_sha256':sha(M/'package-freeze.json'),'canonical_v2_rebind_freeze_sha256':sha(R/'package-freeze.json'),'effective_molecule_freeze_sha256':sha(V/'package-freeze.json'),
 'canonical_package_sha256':'7b71cd4d861328b057adefab344b0bb1029152cf981e569ccfacf06f1672316d','canonical_audit_sha256':sha(G/'canonical-reader-independent-audit/independent-audit-v2.json'),'source_audit_sha256':sha(G/'source-independent-audit/independent-audit-v2.json'),
 'effective_files':fm,'effective_public_assets':assets,
 'counts':{'identities':25,'material_slots':88,'quantity_references':59,'stocks':3,'stock_components':8,'connectivity_models':13,'unchanged_retained_3d_arrays':10,'symbolic_identities':12,'public_files':48,'static_previews_actually_viewed':38,'contacts_actually_viewed':8,'new_product_bindings':0},
 'checks_by_scope':{n:d['check_count'] for n,d in reports.items()}|{'final-v3-delta-checks.json':len(checks)},'check_count':sum(d['check_count'] for d in reports.values())+len(checks),
 'manual_scopes':manual['manual_scopes'],'actual_source_reading':{'scope':manual['source_reading_scope'],'pages':manual['source_pages_actually_reopened']},
 'finding_history':history,'open_findings':[],'checker_assumption_history':manual['checker_assumption_history'],
 'integration_requirements':['Use metadata-correction-v3/effective-file-map.json and effective-public-assets.json, not the original registry/model hashes.','Preserve source-specific viewOverrides alongside the reference-model caption.','No product/sample coordinate binding is approved. Later integration, mounted-browser and deployment remain separate.'],
 'bound_files':bound,'bound_file_count':len(bound),'site_modified':False,'source_or_canonical_modified':False,'author_files_modified':False,'mounted_browser_approved':False,'publication_approved':False,'training_approved':False,
}
out=A/'independent-audit.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(A/'independent-audit.md').write_text('# Ghosh molecular and stock audit\n\nPassed against canonical v2 and the preserved molecular metadata-v3 overlay. All25 identities,88 material slots,59 quantity references and three stocks/eight components were checked. All38 previews were actually viewed; source main2/3/5/6 and SI4/5 were reopened.\n\nThirteen connectivity models,10 unchanged retained3D references and12 symbolic identities preserve grade/isomer/speciation/support limits. TOP-Se has no3D promotion; nitrogen is detector coolant. No particle coordinates, upstream stock reaction or training pair is invented.\n\nOne downloadable nitrogen source-type label retained the prior-paper name; its source-neutral correction and dependent hashes passed. Atomic arrays, captions, quantities and slot assignments are unchanged. Use the final effective file and public-asset maps; original freezes remain intact.\n\n'+str(report['check_count'])+' supporting checks and15 manual scopes passed, with no open findings. No Site, source, canonical or author files were modified. Mounted browser, product binding and publication remain separate.\n\nJSON SHA256: `'+sha(out)+'`\n',encoding='utf-8')
print(json.dumps({'status':'passed','audit_sha256':sha(out),'checks':report['check_count'],'final_delta_checks':len(checks),'bound_files':len(bound)}))
