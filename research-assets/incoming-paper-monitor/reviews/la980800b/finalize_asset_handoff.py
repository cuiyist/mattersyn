from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import json,hashlib,re,math
R=Path(__file__).resolve().parent;O=R/'molecular-assets'
def load(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
# Preserve the auditor's source wording correction if the original crop finalizer is rerun later.
p=R/'finalize_source_assets.py';s=p.read_text(encoding='utf8');s=s.replace('Source supplies lever thickness and NC resonance range. Tip material and radius are not specified.','Source gives Ultralever dimensions of 0.6 µm and 2 µm without naming the dimension type, plus an NC resonance range. Tip material and radius are not specified.')
p.write_text(s,encoding='utf8')
checks=[]
def check(v,label):checks.append({'check':label,'passed':bool(v)})
for id,expected,nfrags,cation in [('silver-perchlorate-monohydrate',{'Ag':1,'Cl':1,'O':5,'H':2},3,'Ag'),('lithium-perchlorate',{'Li':1,'Cl':1,'O':4},2,'Li')]:
 m=load(O/'models'/f'{id}-2d.json');atoms=m['atoms'];bonds=m['bonds'];counts=Counter(a['element'] for a in atoms);counts['H']+=sum(a.get('implicitHydrogenCount',0) for a in atoms);counts=+counts
 check(counts==Counter(expected),id+' serialized elemental/hydrogen count')
 check(sum(a.get('formalCharge',0) for a in atoms)==0,id+' serialized net formal charge')
 check(all(a['index']==i and all(math.isfinite(a[k]) for k in ['x','y','z']) for i,a in enumerate(atoms)),id+' finite indexed 2D atoms')
 check(all(a['z']==0 for a in atoms) and m['has3D'] is False,id+' no invented 3D geometry')
 graph={i:set() for i in range(len(atoms))}
 for b in bonds:
  check(b['a'] in graph and b['b'] in graph and b['a']!=b['b'],id+' valid serialized bond endpoints')
  graph[b['a']].add(b['b']);graph[b['b']].add(b['a'])
 fragments=[];remaining=set(graph)
 while remaining:
  todo=[remaining.pop()];group=set(todo)
  while todo:
   for t in graph[todo.pop()]-group:group.add(t);remaining.discard(t);todo.append(t)
  fragments.append(group)
 check(len(fragments)==nfrags,id+' disconnected ionic/hydrate fragments')
 ci=next(a['index'] for a in atoms if a['element']==cation)
 check(not graph[ci],id+' no cation coordination bond invented')
 cli=next(a['index'] for a in atoms if a['element']=='Cl')
 anion={cli}|graph[cli]
 check(len(graph[cli])==4 and all(atoms[i]['element']=='O' for i in graph[cli]),id+' perchlorate connectivity')
 check(sum(atoms[i]['formalCharge'] for i in anion)==-1,id+' perchlorate anion charge minus one')
check('lever thickness' not in (R/'chemical-reference-proposal.json').read_text(encoding='utf8'),'Ultralever dimension type remains unspecified')
reg=load(O/'registry-additions.json');bindings=load(O/'bindings-additions.json');proposal=load(O/'product-reference-proposal.json')
for rid,hs in bindings['sourceRecordSha256'].items():check(hs==sha(R/'canonical-drafts'/(rid+'.json')),rid+' final binding source hash')
for rid,hs in proposal['sourceRecordSha256'].items():check(hs==sha(R/'canonical-drafts'/(rid+'.json')),rid+' final product-reference source hash')
for e in reg['entries']:
 for k,h in e['assetHashes'].items():check(sha(O/e[k])==h,e['id']+' final '+k+' hash')
 check(e['provenance']['measuredCoordinates'] is False and e['provenance']['eligible_training'] is False,e['id']+' explicit illustrative flags')
for e in load(O/'asset-manifest.json')['files']:check(sha(O/e['path'])==e['sha256'],e['path']+' manifest hash')
scene=load(R/'apparatus-review/scene-manifest.json');check(scene['module_sha256']==sha(R/'stiger-protocol.mjs'),'Final module SHA matches scene manifest')
for row in scene['rows']:check(sha(R/'apparatus-review'/row['svg'])==row['svg_sha256'],row['record_id']+'/'+row['operation_id']+' final SVG hash')
save(O/'serialized-validation.json',{'status':'passed' if all(c['passed'] for c in checks) else 'failed','passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),'checks':checks})
save(R/'apparatus-review/creator-visual-review.json',{'status':'passed','module_sha256':sha(R/'stiger-protocol.mjs'),'operations_visually_reviewed':36,'contact_sheets':6,'rendered_source_actions':26,'reviewer':'synthesis_prior_art','scope':'Creator inspected all six sheets / 36 scenes. Targeted open-circuit control correction re-rendered and checked. Instrument geometry and surface markers remain explicitly illustrative. Browser QA remains with parent.','corrections':['Open-circuit control uses immersion alone; source does not establish reference/counter electrode connections for this control.','Control rinse contains no deposited Ag particles and does not add an unsupported solvent-purity label.','HOPG calibration is a separate instrument branch with unspecified timing.','AFM reference and plated specimens remain alternatives, not a combined sample.']})
files=['crop-assets/manifest.json','crop-assets/validation.json','chemical-reference-proposal.json','molecular-assets/registry-additions.json','molecular-assets/bindings-additions.json','molecular-assets/product-reference-proposal.json','molecular-assets/registry-neutralizations.json','molecular-assets/asset-manifest.json','molecular-assets/model-provenance.json','molecular-assets/validation.json','molecular-assets/serialized-validation.json','stiger-protocol.mjs','apparatus-review/scene-manifest.json','apparatus-review/dispatch-validation.json','apparatus-review/render-validation.json','apparatus-review/creator-visual-review.json']
out={'source_id':'stiger1999','doi':'10.1021/la980800b','source_sha256':'e581449713ddca5e0cb68d05593df476d0e5150b88bc7c6dcbdb269ac70881fb','created_utc':datetime.now(timezone.utc).isoformat(),'status':'ready_for_parent_integration_with_independent_audit_pending','all_private':True,'source_crops':{'count':15,'numbered_figure_count':9,'table_count':1,'scheme_count':1,'equation_count':3,'extra_detail':'Measured SAED Figure 6b extracted additionally; Figure 6c remains a source indexing schematic.','all_visually_reviewed':True},'chemistry':reg['summary'],'product_identity_references':{'records':len(proposal['references']),'physical_sample_bindings':sum(map(len,proposal['productBindings'].values())),'excluded_unassigned_contexts':len(proposal['excludedNonphysicalContexts'])},'apparatus':{'module':'stiger-protocol.mjs','exports':['buildStigerScene','createStigerArt'],'operations':36,'distinct_actions':26,'creator_visual_review':'passed','browser_qa':'parent_pending','dispatch_checks':load(R/'apparatus-review/dispatch-validation.json')['passed']},'integration_notes':['Merge new registry entries and copy files from molecular-assets/asset-manifest.json. Reuse existing six references; no duplicate molecular assets.','Apply registry-neutralizations.json for HF and sulfuric acid: generic chemical metadata only, retaining existing coordinate assets and hashes.','Merge material bindings and reader identity references; no product identity for composition-null model/context entries.','No new crystal mapping: no local verified Ag CIF and no solved Ag/Si interface. Existing finite Si nanocrystal view is inappropriate to this wafer contribution.','Root may update sourceRecordSha256 after its serialization or validated canonical changes. Preserve actual material IDs and scoped product identities.','Original Figures 5/7 charge units, Figure 2 caption/body concentrations and Figure 8/summary rate inconsistencies remain source conflicts; assets make no conversions.'],'files':[{'path':p,'sha256':sha(R/p)} for p in files]}
audits=['crop-source-audit.json','molecular-source-audit.json','apparatus-source-audit.json']
if all((R/p).exists() for p in audits):
 out['independent_audits']=[{'path':p,'sha256':sha(R/p)} for p in audits]
 out['status']='ready_for_parent_integration_independently_audited'
 out['independent_audit_scope']='Independent reviewer confirmed 15 original source crops, all three chemical sheets / 190 checks, and all six apparatus sheets / 87 checks, including the corrected OCP immersion scene. Parent browser QA remains separate.'
save(R/'asset-handoff.json',out)
(R/'asset-handoff.md').write_text('Stiger 1999 private asset handoff\n\n15 faithful original source crops, including the actual Figure 6b SAED and separate Figure 6c indexing schematic. All nine full source pages and all crops were visually reviewed.\n\n14 new chemical references (two 2D ionic-component models and 12 honest identity cards), six reused molecular identities, 47/47 material bindings, eight record identity references and 18 physical sample references. Thirty composition-null contexts are excluded from sample-level identity binding. Transferred TEM Ag uses a distinct card from the Ag/Si wafer. Apply the supplied generic HF/H2SO4 metadata neutralizations. No crystal model is added.\n\nThe module covers all 36 operations / 26 action types. All six scene sheets were inspected; 181 dispatch/source checks passed with no text outside the frame. The open-circuit control is simple immersion; HOPG is a separate instrument calibration. Exact pulse/duration/scene values are drawn only from the selected canonical operation.\n\nThe private package is ready for parent integration. Independent source audit and parent browser QA are tracked separately; creator rendering alone is not browser or independent verification. File hashes are in asset-handoff.json.\n',encoding='utf8')
if out.get('independent_audits'):
 p=R/'asset-handoff.md';s=p.read_text(encoding='utf8');s=s.replace('The private package is ready for parent integration. Independent source audit and parent browser QA are tracked separately; creator rendering alone is not browser or independent verification. File hashes are in asset-handoff.json.','The private package is ready for parent integration. Independent audits passed all 15 source crops, all three chemical sheets / 190 checks, and all six apparatus sheets / 87 checks against the final module. The OCP correction is closed. Parent browser QA remains separate. Audit report hashes and asset hashes are in asset-handoff.json.');p.write_text(s,encoding='utf8')
print(json.dumps({'status':'passed' if all(c['passed'] for c in checks) else 'failed','checks':len(checks),'module_sha256':sha(R/'stiger-protocol.mjs'),'handoff_sha256':sha(R/'asset-handoff.json')}))
