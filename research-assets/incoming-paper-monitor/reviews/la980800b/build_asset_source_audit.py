"""Independent scientific and hash audit of private Stiger visual packages; no Site writes."""
from pathlib import Path
import json,hashlib,collections,xml.etree.ElementTree as ET
B=Path(__file__).resolve().parent;M=B/'molecular-assets';A=B/'apparatus-review'
REG=Path('[local path redacted]')
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
records={p.stem:read(p) for p in (B/'canonical-drafts').glob('*.json')}
entries={x['id']:x for x in read(M/'registry-additions.json')['entries']}
bindings=read(M/'bindings-additions.json');product=read(M/'product-reference-proposal.json')
checks=[]
def ck(name,b,detail=''):checks.append({'name':name,'passed':bool(b),'detail':detail})
mapping={'si-npp':'identity-stiger-si-npp','si-n':'identity-stiger-si-n','h-si':'identity-stiger-h-si','ga-in':'identity-stiger-ga-in','silver-paint':'identity-stiger-silver-paint','agclo4':'silver-perchlorate-monohydrate','liclo4':'lithium-perchlorate','water':'water','ethanol':'ethanol','nitrogen':'nitrogen','hf':'hydrogen-fluoride','h2so4':'sulfuric-acid','mecn':'acetonitrile','pt-wire':'identity-stiger-pt-wire','ag-wire':'identity-stiger-ag-wire','sce':'identity-stiger-sce','ag-si':'identity-stiger-ag-si','carbon-grid':'identity-stiger-carbon-grid','hopg':'identity-stiger-hopg'}
ck('47 material bindings; 14 new references; 6 reused',sum(len(x)for x in bindings['recordBindings'].values())==47 and len(entries)==14 and len(read(M/'reused-references.json')['entries'])==6)
for rid,r in records.items():
 b=bindings['recordBindings'][rid]
 ck(rid+' exact material coverage',set(b)=={m['id']for m in r['materials']})
 ck(rid+' binding hash current',bindings['sourceRecordSha256'][rid]==sha(B/'canonical-drafts'/(rid+'.json')))
 for m in r['materials']:
  ck(rid+'/'+m['id']+' correct chemical/reference identity',b[m['id']]==mapping[m['id']] and bool(bindings['bindingNotes'][rid][m['id']]))
for eid,e in entries.items():
 ck(eid+' no inferred measured coordinates/3D',e['model3dPath'] is None and not e['provenance']['measuredCoordinates'] and not e['provenance']['eligible_training'])
 for key in ['svgPath','model2dPath']:
  if e.get(key):ck(eid+' '+key+' exact hash',sha(M/e[key])==e['assetHashes'][key])
 if e['depictionKind']!='ionic':ck(eid+' honest identity card',e['model2dPath'] is None and bool(e['limitations']))
for eid,expected,fragments in [('silver-perchlorate-monohydrate',{'Ag':1,'Cl':1,'O':5,'H':2},3),('lithium-perchlorate',{'Li':1,'Cl':1,'O':4},2)]:
 model=read(M/entries[eid]['model2dPath']);counts=collections.Counter(a['element']for a in model['atoms']);counts['H']+=sum(a.get('implicitHydrogenCount',0)for a in model['atoms']);counts=+counts
 adj={a['index']:set()for a in model['atoms']}
 for b in model['bonds']:adj[b['a']].add(b['b']);adj[b['b']].add(b['a'])
 seen=set();groups=[]
 for start in adj:
  if start in seen:continue
  stack=[start];group=set()
  while stack:
   n=stack.pop()
   if n in seen:continue
   seen.add(n);group.add(n);stack.extend(adj[n]-seen)
  groups.append(group)
 ck(eid+' formula, charge and separate ions/hydrate',dict(counts)==expected and sum(a['formalCharge']for a in model['atoms'])==0 and len(groups)==fragments)
 ck(eid+' no invented ion-pair bonds or geometry',not model['has3D'] and not model['allowRotation'] and all(a['z']==0 for a in model['atoms']) and 'not oxidation states' in model['caption'])
for reuse in read(M/'reused-references.json')['entries']:
 for k,p in reuse['assetPaths'].items():ck(reuse['id']+' reused '+k+' unchanged verified asset',sha(REG/p)==reuse['assetHashes'][k])
for update in read(M/'registry-neutralizations.json')['updates']:
 ck(update['id']+' source-neutral reference text','each source record' in update['caption'] and 'not measured solution geometry' in update['caption'])
ck('No Ag or Ag/Si atomistic structure invented','No crystal mapping added' in product['crystalReferencePolicy'] and 'No verified local Ag CIF' in product['crystalReferencePolicy'])
ck('Eight record cards are explicitly reader context',len(product['references'])==8 and not product['eligible_training'] and all('not a solved unit cell' in n for n in product['bindingNotes'].values()))
for rid,r in records.items():
 ck(rid+' product reference hash current',product['sourceRecordSha256'][rid]==sha(B/'canonical-drafts'/(rid+'.json')))
 ps={p['sample_id']:p for p in r['products']}
 for sid,eid in product['productBindings'][rid].items():
  ck(rid+'/'+sid+' card assigned only to composition-scoped context',sid in ps and ps[sid]['composition']['value'] is not None and eid in entries and entries[eid]['model2dPath'] is None)
 for p in r['products']:
  if p['composition']['value'] is None:ck(rid+'/'+p['sample_id']+' null composition not assigned physical card',p['sample_id'] not in product['productBindings'][rid])
ck('Both controls remain Si, not silver products',all(product['references']['stiger-1999-'+k]=='identity-stiger-h-si' for k in ['open-circuit-control','silver-free-pulse-control']))
ck('Transferred TEM identity distinct from Si wafer',product['references']['stiger-1999-tem-saed']=='identity-stiger-transferred-ag' and product['productBindings']['stiger-1999-characterization']['tem-saed-context']=='identity-stiger-transferred-ag')
molecular={'status':'passed' if all(c['passed']for c in checks)else'must_fix','source_id':'stiger1999','scope':'Independent source-science review of all 47 material bindings, 14 new identity/connectivity references, 6 reused references, and product-state cards. All three chemical contact sheets visually inspected; reused assets verified by exact prior-reviewed hashes and chemical identity.','check_count':len(checks),'checks':checks,'files':[{'basename':str(p.relative_to(B)),'sha256':sha(p)}for p in [M/'registry-additions.json',M/'bindings-additions.json',M/'product-reference-proposal.json',M/'asset-manifest.json',M/'reused-references.json',M/'registry-neutralizations.json']],'notes':['Perchlorate formal charges are RDKit bonding bookkeeping, not oxidation states; ions and hydrate water remain disconnected.','Alloy, paint, electrode assembly, wafer, carbon/gold support and HOPG are identity cards. No molecular structure is fabricated for these materials.','Source-supplied purities and solution concentrations remain distinct; molecular reuse imports no previous-source recipe conditions.','Eight default record cards illustrate context, not a universal experimental specimen. Null-composition/model contexts have no sample card.','Apparatus items absent from canonical materials (Teflon holder, diamond scribe, AFM hardware) remain in source prose and apparatus scenes; no arbitrary chemical formula required.','SI remains unverified; actual Site rendering and publication not audited here.'],'visual_sheets':[{'basename':str(p.relative_to(B)),'sha256':sha(p),'status':'independently_visually_inspected'}for p in sorted((M/'review').glob('contact-*.png'))]}
(B/'molecular-source-audit.json').write_text(json.dumps(molecular,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
(B/'molecular-source-audit.md').write_text('# Independent molecular/source audit\n\n'+molecular['status'].upper()+': '+str(len(checks))+' checks; 47 material bindings, 14 new references and 6 reused references. All new chemical sheets visually inspected.\n\n'+'\n'.join('- '+n for n in molecular['notes'])+'\n',encoding='utf8')

checks=[];manifest=read(A/'scene-manifest.json');module=B/'stiger-protocol.mjs'
ck('Exact current module hash',manifest['module_sha256']==sha(module))
allops={(rid,o['id']):o for rid,r in records.items()for o in r['operations']}
ck('Every one of 36 current operations covered once',len(manifest['rows'])==36 and {(r['record_id'],r['operation_id'])for r in manifest['rows']}==set(allops))
scenes={}
for row in manifest['rows']:
 key=(row['record_id'],row['operation_id']);p=A/row['svg'];s=p.read_text(encoding='utf8');scenes[key]=s
 ck('/'.join(key)+' current source and SVG hash',row['source_record_sha256']==sha(B/'canonical-drafts'/(key[0]+'.json')) and sha(p)==row['svg_sha256'])
 ck('/'.join(key)+' correct action and evidence',row['action']==allops[key]['action'] and row['source_evidence']==allops[key]['evidence'])
def sc(r,o):return ' '.join(' '.join(ET.fromstring(scenes[('stiger-1999-'+r,o)]).itertext()).split())
ck('Oxidation reports acid temperature, not heater setpoint','Solution: 80 °C' in sc('electrodeposition','oxidize') and 'Time: ≈10 min' in sc('electrodeposition','oxidize') and 'not a measured wafer-heater' in sc('electrodeposition','oxidize'))
ck('Etch treatment 5min and no exact H coverage','Treatment: 5 min' in sc('electrodeposition','etch') and 'Exact surface H coverage' in sc('electrodeposition','etch'))
ck('Purge is pre-use, not continuous synthesis gas','does not establish continuous gas flow' in sc('electrodeposition','purge'))
ck('CV preserves alternatives and Ag/SCE distinction','Ag-containing OR Ag-free' in sc('cyclic-voltammetry','prepare') and 'Ag wire for Ag-containing solution' in sc('cyclic-voltammetry','scan') and 'SCE for Ag-free solution' in sc('cyclic-voltammetry','scan'))
ck('Pulse proper Ag reference and OCP distinction','-800 mV versus Ag' in sc('electrodeposition','pulse') and 'not a zero-volt hold' in sc('electrodeposition','open-circuit'))
ck('Silver paint belongs to back contact','separate' in sc('electrodeposition','paint') or 'distinct' in sc('electrodeposition','paint'))
ck('OCP control simple immersion without implied instrument wiring','instrument connections for this control are unspecified' in sc('open-circuit-control','immerse') and 'Pt counter' not in sc('open-circuit-control','immerse') and 'Ag ref.' not in sc('open-circuit-control','immerse'))
ck('Silver-free control no invented numeric bias','Control pulse value not specified' in sc('silver-free-pulse-control','pulse') and '-800' not in sc('silver-free-pulse-control','pulse'))
ck('Control rinse no deposited-silver claim','Retain deposited silver' not in sc('open-circuit-control','rinse'))
ck('AFM alternative specimens and height distinction','OR' in sc('afm','scan') and 'not automatically spherical diameters' in sc('afm','analyze'))
ck('TEM transferred Au/carbon grid and source unit','Carbon-coated gold grid' in sc('tem-saed','transfer') and '200 keV' in sc('tem-saed','image'))
ck('SAED no simulated data and indexing separated','No rings or spots are generated' in sc('tem-saed','diffract') and 'indexing schematic' in sc('tem-saed','diffract'))
ck('HOPG independent calibration','Independent instrument calibration' in sc('tem-saed','calibrate') and 'timing relative' in sc('tem-saed','calibrate'))
apparatus={'status':'passed'if all(c['passed']for c in checks)else'must_fix','source_id':'stiger1999','scope':'Independent read of complete module and all 36 rendered source-operation scenes. All six contact sheets visually inspected, including the corrected OCP immersion scene.','module_sha256':sha(module),'scene_manifest_sha256':sha(A/'scene-manifest.json'),'operation_count':36,'check_count':len(checks),'checks':checks,'findings':[{'id':'A01','status':'resolved','title':'Open-circuit control must not imply specified three-electrode instrument connections','detail':'Replaced connected Ag/Pt setup with simple Ag-bath/silicon exposure and explicit unknown connections, timing and geometry.'}],'visual_sheets':[{'basename':str(p.relative_to(B)),'sha256':sha(p),'status':'independently_visually_inspected'}for p in sorted(A.glob('contact-*.png'))],'scope_limits':['Quantities not printed inside every illustration remain in the selected canonical operation in the shared reader UI; actual integration must preserve that adjacency.','Glassware and functional cell geometry, cut layout, heat source and surface markers are explicitly illustrative, not measured apparatus dimensions or exact H coverage.','No synthetic AFM map, current trace, diffraction pattern or atomistic Ag/Si interface is produced.','Source records remain private audit drafts; no Site rendering or publication claim in this report.']}
(B/'apparatus-source-audit.json').write_text(json.dumps(apparatus,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
(B/'apparatus-source-audit.md').write_text('# Independent apparatus/source audit\n\n'+apparatus['status'].upper()+': '+str(len(checks))+' checks; all 36 operations and six rendered sheets inspected. Module SHA256: '+sha(module)+'.\n\nA01 resolved: OCP exposure now uses simple immersion without unreported instrument connections.\n\n'+'\n'.join('- '+n for n in apparatus['scope_limits'])+'\n',encoding='utf8')
print(json.dumps({'molecular':{'status':molecular['status'],'checks':molecular['check_count'],'failed':[c for c in molecular['checks']if not c['passed']]},'apparatus':{'status':apparatus['status'],'checks':apparatus['check_count'],'failed':[c for c in apparatus['checks']if not c['passed']]}},indent=2))
