"""Exact private Matuhina material and stock-component binding proposal."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
import json,hashlib
O=Path(__file__).resolve().parent;P=O.parents[1];C=P/'canonical-proposal/v1';assert not(O/'package-freeze.json').exists()
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jsha(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def ptr(x,p):
 for t in p.strip('/').split('/'):x=x[int(t)]if isinstance(x,list)else x[t.replace('~1','/').replace('~0','~')]
 return x
def qfmt(q):
 if q.get('raw_text'):return q['raw_text']+(' '+q['unit']if q.get('unit')else'')
 if q.get('value')is not None:return str(q['value'])+(' '+q['unit']if q.get('unit')else'')
 return'Not reported'
checks=[]
def ck(n,v):checks.append({'check':n,'passed':bool(v)});assert v,n
cm=read(C/'record-manifest.json');records={r['record_id']:read(r['path'])for r in cm['records']};paths={r['record_id']:Path(r['path'])for r in cm['records']}
for row in cm['records']:ck('Canonical hash '+row['record_id'],sha(row['path'])==row['sha256'])
source=read(P/'source-facts.json');sm={m['id']:m for m in source['materials']};ss={s['id']:s for s in source['stocks']};entries={e['provenance']['sourceMaterialId']:e for e in read(O/'registry-additions.json')['entries']}
QMAP={
('cs-oleate-preparation','cs-carbonate'):[('cs-load','cs2co3_mass','whole_stock_component_charge')],
('cs-oleate-preparation','ode'):[('cs-load','ode_charge','whole_stock_solvent_charge_not_final_volume')],
('cs-oleate-preparation','oa'):[('cs-add-oa','dry_oa_charge','whole_stock_component_charge')],
('hot-injection-series','mncl2'):[('mn-load','mncl2_mass','manganese_formulation_charge')],
('hot-injection-series','ode'):[('mn-load','dry_ode_charge','manganese_formulation_solvent_charge')],
('hot-injection-series','oa'):[('mn-load','dry_oa_charge','manganese_formulation_ligand_charge')],
('hot-injection-series','olam'):[('mn-load','dry_olam_charge','manganese_formulation_ligand_charge')],
('purification-trials','hexane'):[('hexane-spin','hexane_volume','separate_hexane_trial_not_primary_redispersion_volume')],
('xrd-procedure','cover-glass'):[('xrd-deposit','cover_glass_side_1','support_dimension'),('xrd-deposit','cover_glass_side_2','support_dimension')],
('ta-procedure','quartz-cuvette'):[('ta-load','cuvette_thickness','optical_cell_dimension')],
('icp-procedure','milliq'):[('icp-dilute','milli_q_water_resistivity','analytical_water_resistivity')],
('icp-procedure','hno3'):[('icp-dilute','hno3_matrix_concentration','diluted_matrix_not_concentrated_digest_strength')],
('lsc-procedure','lsc-glass'):[('lsc-assemble','window_edge_length','source_glass_edge_dimension'),('lsc-assemble','window_edge_thickness','source_glass_edge_dimension')],
('lsc-procedure','si-photodiode'):[('lsc-assemble','photodiode_side_1','device_dimension'),('lsc-assemble','photodiode_side_2','device_dimension')]}
def qlink(rid,p,kind):
 q=ptr(records[rid],p);return{'record_id':rid,'json_pointer':p,'quantity':deepcopy(q),'meaning':kind,'display_label':p.split('/')[-1].replace('_',' '),'display_value':qfmt(q)}
def opref(rid,op,k,kind):
 n=next(i for i,o in enumerate(records[rid]['operations'])if o['id']==op);return qlink(rid,f'/operations/{n}/parameters/{k}',kind)
bindings={'schemaVersion':'1.0','source_id':'matuhina2023','status':'private_author_proposal_pending_independent_molecular_audit','recordBindings':{},'bindingNotes':{},'binding_approved':False,'published':False,'eligible_training':False};slots=[]
for rid,r in records.items():
 if not r['materials']:continue
 bindings['recordBindings'][rid]={};bindings['bindingNotes'][rid]={}
 for j,m in enumerate(r['materials']):
  mid=m['id'];e=entries[mid];ck(rid+'/'+mid+' identity',m['formula']==sm[mid]['source_formula_or_abbreviation']and m['name']==sm[mid]['name'])
  refs=[opref(rid,*q)for q in QMAP.get((rid.removeprefix('matuhina-2023-'),mid),[])];gr=[qlink(rid,f'/materials/{j}/quantities/{k}','source_reported_reagent_grade_not_yield')for k in m['quantities']]
  caption=m['name']+'; '+m['role'].replace('_',' ')+' in this source context. '+e['caption']
  if refs:caption+=' Context-specific quantities: '+'; '.join(q['display_label']+': '+q['display_value']+' ('+q['meaning'].replace('_',' ')+')'for q in refs)+'.'
  if gr:caption+=' Source reagent grade: '+'; '.join(q['display_value']for q in gr)+'.'
  if mid=='hno3':caption+=' The 2% value belongs to the diluted analytical matrix. It is not the concentration of the unspecified concentrated acid used for digestion.'
  note={'record_id':rid,'material_id':mid,'json_pointer':f'/materials/{j}','canonical_record_sha256':sha(paths[rid]),'registry_id':e['id'],'entry_sha256':jsha(e),'canonical_identity':deepcopy(m),'source_material':deepcopy(sm[mid]),'quantity_links':refs,'grade_context_links':gr,'viewOverrides':{'name':m['name'],'caption':caption,'limitations':deepcopy(e['limitations'])},'binding_approved':False,'source_specific_join':'Exact canonical material identity slot only; quantities retain source operation or stock context. No measured atomic/product structure or ligand-coverage binding.'};slots.append(note);bindings['recordBindings'][rid][mid]=e['id'];bindings['bindingNotes'][rid][mid]=note
stockrows=[];contexts=[]
for rid,r in records.items():
 for si,s in enumerate(r['stocks']):
  comps=[]
  for ci,c in enumerate(s['components']):
   mid=c['material_id'];mi=next(j for j,m in enumerate(r['materials'])if m['id']==mid);refs=[qlink(rid,f'/stocks/{si}/components/{ci}/quantities/{k}','source_stock_component_quantity_not_additional_reaction_charge')for k in c['quantities']]
   comps.append({'material_id':mid,'registry_id':entries[mid]['id'],'role':r['materials'][mi]['role'],'json_pointer':f'/stocks/{si}/components/{ci}','material_json_pointer':f'/materials/{mi}','source_quantities':deepcopy(c['quantities']),'quantity_links':refs,'binding_approved':False})
  cqs=[qlink(rid,f'/stocks/{si}/concentrations/{k}','source_stock_concentration')for k in s['concentrations']];summary='; '.join(sm[c['material_id']]['name']+': '+('; '.join(q['display_value']for q in c['quantity_links'])or'amount not separately reported')for c in comps)
  limit=s['scope']+' Separate component models do not establish dissolved coordination, hydration or aggregation. Whole-stock charges are not additional reaction charges.'
  if s['id']=='cs-oleate-stock':limit+=' The final stock volume and concentration are unreported. Storage is under vacuum; pre-injection degassing is at least 30 min at 120 °C, then heating to 150 °C under Ar. The 2, 3 and 4 mL injections remain separate route conditions.'
  if s['id']in['icp-matrix','cs-calibration','mn-calibration']:limit+=' The 2% HNO3 basis is unspecified. Counterions and exact ionic speciation of the calibration standards are not supplied.'
  row={'record_id':rid,'stock_id':s['id'],'json_pointer':f'/stocks/{si}','canonical_record_sha256':sha(paths[rid]),'canonical_stock':deepcopy(s),'source_stock':deepcopy(ss[s['id']]),'components':comps,'concentrations':deepcopy(s['concentrations']),'concentration_links':cqs,'solution_quantity_links':[],'scope':s['scope'],'evidence':deepcopy(s['evidence']),'display_summary':summary,'display_limit':limit,'binding_approved':False};stockrows.append(row)
  contexts.append({'record_id':rid,'id':'matuhina2023-'+s['id'],'label':s['name'],'scope':summary+'. '+limit,'components':[{'material_id':c['material_id'],'registry_id':c['registry_id'],'role':c['role'],'label':sm[c['material_id']]['name'],'viewOverrides':{'caption':sm[c['material_id']]['name']+' in '+s['name']+'. '+summary+'. '+limit,'limitations':[limit,entries[c['material_id']]['limitations'][-1]]}}for c in comps],'binding_approved':False})
ck('Complete exact scope',len(entries)==28 and len(slots)==55 and len(stockrows)==5 and sum(len(s['components'])for s in stockrows)==15)
save('bindings-proposal.json',bindings);save('material-slot-map.json',{'schema':'mattersyn-molecular-slot-proposal/1','material_slot_count':55,'identity_count':28,'slots':slots,'independent_audit':'pending'});save('stock-component-map.json',{'schema':'mattersyn-stock-component-proposal/1','stock_count':5,'component_count':15,'stocks':stockrows,'independent_audit':'pending'});save('solution-components-proposal.json',{'schemaVersion':'1.0','contexts':contexts,'binding_approved':False})
inp=read(O/'input-bindings.json');inp.update(canonical_record_manifest={'path':str(C/'record-manifest.json'),'sha256':sha(C/'record-manifest.json')},canonical_package_manifest={'path':str(C/'package-manifest.json'),'sha256':sha(C/'package-manifest.json')},source_audit={'path':str(P/'source-independent-audit/independent-audit.json'),'sha256':sha(P/'source-independent-audit/independent-audit.json')},canonical_records={str(paths[rid]):sha(paths[rid])for rid in records});save('input-bindings.json',inp);save('binding-author-checks.json',{'author':'/root/backlog_eta','status':'author_checks_passed_independent_pending','created_at':datetime.now(timezone.utc).isoformat(),'checks':checks,'check_count':len(checks),'independent_approval':False});print(json.dumps({'slots':55,'stocks':5,'components':15,'checks':len(checks)}))
