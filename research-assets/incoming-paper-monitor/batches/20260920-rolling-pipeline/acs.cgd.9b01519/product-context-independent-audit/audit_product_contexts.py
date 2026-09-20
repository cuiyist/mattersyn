"""Root's independent sample/phase projection audit; no source or proposal mutation."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
A=Path(__file__).resolve().parent;N=A.parent;P=N/'product-context-proposal';C=N/'canonical-proposal/v2'
def read(p):return json.loads(p.read_text('utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ptr(o,s):
 for token in s.strip('/').split('/'):o=o[int(token)] if isinstance(o,list) else o[token.replace('~1','/').replace('~0','~')]
 return o
checks=[]
def ck(name,ok):
 checks.append({'check':name,'passed':bool(ok)});assert ok,name
freeze=read(P/'package-freeze.json');ck('Distinct source author',freeze['author']=='/root/peng1998_reader_assets')
for name,h in freeze['bound_files'].items():ck('Immutable file '+name,sha(Path(name))==h)
ck('Canonical independent pass',read(N/'canonical-reader-independent-audit/independent-audit-v2.json')['status']=='passed')
# Root manually compared original main pp2–6 with these sample/phase sets.
expected={'m1':{'ZnAl2O4','AlOOH'},'m2':{'ZnAl2O4','AlOOH'},'m3':{'ZnAl2O4','AlOOH','ZnO'},**{f'm{i}':{'ZnAl2O4','AlOOH'} for i in range(4,8)},'s1':{'ZnAl2O4'},'s2':{'ZnAl2O4','ZnO'},'a1':{'ZnAl2O4','AlOOH'},'a2':{'ZnAl2O4'},'a3':{'ZnAl2O4','ZnO'},'a4':{'AlOOH'},'a5':{'ZnAl2O4','AlOOH'},'a6':{'ZnAl2O4','ZnO'},'i1':{'ZnAl2O4','AlOOH'},'i2':{'ZnAl2O4','AlOOH'},**{f'i{i}':{'ZnAl2O4'} for i in [3,4,5,6,12,13,15]},**{f'i{i}':{'ZnAl2O4','ZnO'} for i in [9,10,11,16]},'d2':{'ZnO'}}
ctx=read(P/'product-contexts-additions.json');binding=read(P/'bindings.json');reg=read(P/'registry-additions.json');entries={x['id']:x for x in reg['entries']}
records={f.stem:read(f) for f in C.glob('sommer-*.json')}; sf=read(N/'source-facts.json');seen=set();pairs={}
for rid,rows in ctx['recordContexts'].items():
 ck(rid+' actual source',records[rid]['lineage']['source_group']=='sommer2020')
 for row in rows:
  sid=row['sample_id'];key=(rid,sid,row['registry_id']);ck(str(key)+' unique',key not in seen);seen.add(key)
  ck(str(key)+' known source outcome',sid in expected and row['phase_component_formula'] in expected[sid])
  pairs.setdefault((rid,sid),set()).add(row['phase_component_formula'])
  product=ptr(records[rid],row['canonical_product_pointer']);ck(str(key)+' original unknown composition retained',product==row['canonical_product_snapshot'] and product['composition']['value'] is None)
  ck(str(key)+' exact sample ID',product['sample_id']==sid)
  fact=ptr(sf,row['source_fact_pointer']);cl=row['canonical_claim_link'];claim=ptr(records[cl['record_id']],cl['json_pointer'])
  ck(str(key)+' exact evidence claim',fact['id']==row['source_fact_id'] and claim==cl['canonical_measurement'] and claim['value']['value']==fact['claim'])
  ck(str(key)+' current main source',all(e['source_id']=='sommer2020' and 'ca731728' in e['locator'] for e in row['composition_evidence']))
  ck(str(key)+' symbolic role visible','phase component' in row['label'] and 'whole-specimen' in row['caption'] and 'atomic structure' in row['caption'])
  ck(str(key)+' source state limits',row['projection_kind']=='reported_phase_component_not_whole_specimen_composition' and row['training_eligible'] is False and row['atomic_model'] is False)
  e=entries[row['registry_id']];ck(str(key)+' formula and model type',e['formula']==row['phase_component_formula'] and e['depictionKind']=='symbolic_context' and e['model2dPath'] is None and e['model3dPath'] is None)
for (rid,sid),phases in pairs.items():ck(rid+'/'+sid+' complete allowed phase set',phases==expected[sid])
ck('45 record/sample contexts and77phase cards',len(pairs)==45 and len(seen)==77)
excluded={(r['record_id'],r['sample_id']) for r in binding['excluded_contexts']}
for r in records.values():
 for p in r['products']:
  ck(r['record_id']+'/'+p['sample_id']+' included or explicitly excluded',((r['record_id'],p['sample_id']) in pairs)^((r['record_id'],p['sample_id']) in excluded))
for x in binding['excluded_contexts']:
 ck(x['record_id']+'/'+x['sample_id']+' exact exclusion',ptr(records[x['record_id']],x['canonical_product_pointer'])==x['canonical_product'])
ck('No questionable specimen inheritance',not any(s in {'m8','m9','i7','i8','i14'} for _,s in pairs))
for rid,rows in ctx['recordContexts'].items():
 for row in rows:
  s=row['sample_id'];t=row['caption']
  if s=='m2':ck('M2 trace below quantification preserved','below reliable quantification' in t and 'zero impurity' in t)
  if s in ['i1','i2']:ck('In situ transient mixture stays time-dependent','time-dependent' in t and 'not one fixed endpoint' in t)
  if s=='a4':ck('A4 failed-target outcome retained','only AlOOH' in t and 'no ZnAl2O4' in t)
  if s in ['i12','i13']:ck('Low yield not low crystallinity','Low yield is not relabeled low crystallinity' in t)
  if s=='d2':ck('Precursor distinct from product','precursor' in t and 'not synthesized spinel' in t)
  if s in ['a1','a2','a4','a5']:ck('Figure11 conflicts remain','conflict' in t)
for e in entries.values():
 ck(e['id']+' SVG exact',sha(P/e['svgPath'])==e['assetHashes']['svgPath'])
 ck(e['id']+' no geometric claims','Symbolic phase-component' in e['caption'] and not e['eligible_training'])
out={'schema':'mattersyn-independent-product-context-audit/1','status':'passed','author':'/root','proposal_author':freeze['author'],'at':datetime.now(timezone.utc).isoformat(),'proposal_freeze_sha256':sha(P/'package-freeze.json'),'checks':len(checks),'manual_scope':'Root read the complete relevant original main pages 2–6, compared all source phase-specification captions with reported contexts, inspected the three symbolic cards, and independently traced every record/sample/claim projection. Earlier main-only source and canonical audits remain separate; this is not a fresh full-paper or SI audit.','counts':{'component_cards':77,'record_sample_pairs':45,'records':8,'exclusions':len(excluded),'symbols':3},'reviewed_source_pages':[2,3,4,5,6],'scientific_values_changed':False,'open_findings':[],'limitations':['SI locally unlocated/unverified','No atomistic structure, exact pair or training eligibility','Integrated browser/publication gates are separate'],'bound_files':{str(P/'package-freeze.json'):sha(P/'package-freeze.json'),str(C/'package-manifest.json'):sha(C/'package-manifest.json')},'check_results':checks}
(A/'independent-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf-8');print(json.dumps({'status':out['status'],'checks':len(checks),'sha256':sha(A/'independent-audit.json')}))
