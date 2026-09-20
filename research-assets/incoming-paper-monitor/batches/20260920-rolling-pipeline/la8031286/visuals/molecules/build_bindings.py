"""Exact Pati private material/stock bindings to the frozen canonical proposal."""
from pathlib import Path
from copy import deepcopy
import json,hashlib,datetime
O=Path(__file__).resolve().parent;P=O.parents[1];C=P/'canonical-proposal/v1'
assert not (O/'package-freeze.json').exists()
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jsha(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def save(n,v):(O/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
def ptr(v,p):
 for k in p.strip('/').split('/'):v=v[int(k)] if isinstance(v,list) else v[k.replace('~1','/').replace('~0','~')]
 return v
def fmt(q):
 v=q.get('raw_text') or (str(q['value']) if q.get('value') is not None else 'Not reported')
 return v+(' '+q['unit'] if q.get('unit') else '')
checks=[]
def ck(n,v):checks.append({'check':n,'passed':bool(v)});assert v,n
manifest=read(C/'record-manifest.json');records={};paths={}
for x in manifest['records']:
 ck('Canonical exact '+x['record_id'],sha(x['path'])==x['sha256']);r=read(x['path']);records[r['record_id']]=r;paths[r['record_id']]=Path(x['path'])
ck('Final canonical manifest',sha(C/'package-manifest.json')=='5986df83c2313f8e5418d0c46c049d86e2ef62dbd049359c7a53a5010e312281')
source=read(P/'source-facts.json');sm={m['id']:m for m in source['materials']};ss={s['id']:s for s in source['stocks']};entries={e['provenance']['sourceMaterialId']:e for e in read(O/'registry-additions.json')['entries']}
def link(rid,p,meaning,label):
 q=ptr(records[rid],p);ck('Quantity object '+p,'status' in q and 'unit' in q)
 return {'record_id':rid,'json_pointer':p,'quantity':deepcopy(q),'meaning':meaning,'display_label':label,'display_value':fmt(q)}
def op(rid,oid,key,meaning,label):
 i=next(i for i,x in enumerate(records[rid]['operations']) if x['id']==oid)
 return link(rid,f'/operations/{i}/parameters/{key}',meaning,label)
routeq={
 'cerium-nitrate':[('prepare-nitrate','cerium_nitrate_stock_concentration','nitrate_stock_concentration_not_crystal_content','Nitrate stock concentration'),('drip','nitrate_stock_transferred_volume','stock_solution_transfer_not_solute_mass_or_total_preparation_volume','Nitrate stock portion transferred')],
 'tea':[('prepare-tea','tea_stock_concentration','tea_stock_concentration_not_pure_reagent_density','TEA stock concentration'),('drip','tea_receiving_volume','stock_solution_portion_not_flask_capacity_or_stock_preparation_volume','TEA stock portion in receiver')],
 'burette':[('drip','addition_rate','nitrate_solution_feed_rate_not_apparatus_capacity','Nitrate stock feed rate')],
 'erlenmeyer':[('drip','tea_receiving_volume','contained_solution_portion_not_flask_capacity','Contained TEA stock portion')],
 'filter-paper':[('filter','filter_pore_diameter','filter_pore_size_not_nanocrystal_size','Filter pore diameter')]}
bindings={'schemaVersion':'1.0','source_id':'pati2009','recordBindings':{},'bindingNotes':{},'status':'private_author_proposal','binding_approved':False,'published':False,'eligible_training':False};slots=[]
for rid,r in records.items():
 if not r['materials']:continue
 bindings['recordBindings'][rid]={};bindings['bindingNotes'][rid]={}
 for mi,m in enumerate(r['materials']):
  mid=m['id'];entry=entries[mid];ck(rid+'/'+mid+' exact source material',m['formula']==sm[mid]['source_formula_or_abbreviation'] and m['name']==sm[mid]['name'])
  refs=[op(rid,*q) for q in routeq.get(mid,[])] if rid.endswith('-route') else []
  if rid=='pati-2009-packing' and mid=='pipet':refs=[op(rid,'packing-acquire','pipet_nominal_volume','nominal_pipet_volume_not_powder_sample_volume','Nominal pipet volume')]
  # The 10 mL quantity belongs to filtrate, never to added ammonium hydroxide.
  if rid=='pati-2009-filtrate-diagnostic':refs=[op(rid,'diagnostic','filtrate_aliquot','tested_filtrate_aliquot_not_ammonium_hydroxide_charge','Separate filtrate test aliquot')]
  grades=[link(rid,f'/materials/{mi}/quantities/{key}','reported_reagent_grade_not_solution_concentration','Reported reagent grade') for key in m['quantities']]
  caption=entry['caption']+' Role in this record: '+m['role'].replace('_',' ')+'.'
  if refs:caption+=' Scoped quantities: '+'; '.join(q['display_label']+' '+q['display_value']+' ('+q['meaning'].replace('_',' ')+')' for q in refs)+'.'
  if grades:caption+=' Source reagent grade: '+', '.join(q['display_value'] for q in grades)+'.'
  if mid in ['cerium-nitrate','tea'] and rid.endswith('-route'):
   solvent=next(s for s in ['ethanol','propanol','butanol'] if s in rid);caption+=' These references belong only to the '+sm[solvent]['name']+' route; the other alcohols are alternatives.'
  note={'record_id':rid,'material_id':mid,'json_pointer':f'/materials/{mi}','canonical_record_sha256':sha(paths[rid]),'registry_id':entry['id'],'entry_sha256':jsha(entry),'canonical_identity':deepcopy(m),'source_material':deepcopy(sm[mid]),'quantity_links':refs,'grade_context_links':grades,'viewOverrides':{'name':m['name'],'caption':caption,'limitations':deepcopy(entry['limitations'])},'reference_formula':entry['formula'],'literal_source_formula':m['formula'],'reference_identity_basis':'Name-qualified graph separate from conflicting printed TEA formula.' if mid=='tea' else 'Source name or formula reference; no measured specimen geometry.','binding_approved':False,'source_specific_join':'Exact canonical material slot; this is not product-coordinate or task eligibility.'}
  bindings['recordBindings'][rid][mid]=entry['id'];bindings['bindingNotes'][rid][mid]=note;slots.append(note)
stockrows=[];contexts=[]
for rid,r in records.items():
 for si,s in enumerate(r['stocks']):
  src=ss[s['id']];comps=[]
  for ci,c in enumerate(s['components']):
   mid=c['material_id'];mi=next(i for i,m in enumerate(r['materials']) if m['id']==mid);sc=next(c for c in src['components'] if c['material_id']==mid)
   refs=[link(rid,f'/stocks/{si}/components/{ci}/quantities/{key}','reported_component_quantity_not_an_additional_charge',key.replace('_',' ')) for key in c['quantities']]
   comps.append({'material_id':mid,'registry_id':entries[mid]['id'],'role':sc['role'],'canonical_material_role':r['materials'][mi]['role'],'json_pointer':f'/stocks/{si}/components/{ci}','material_json_pointer':f'/materials/{mi}','source_quantities':deepcopy(c['quantities']),'quantity_links':refs,'binding_approved':False})
  conc=[link(rid,f'/stocks/{si}/concentrations/{key}','reported_stock_concentration_not_final_mixed_reaction_concentration','Stock concentration') for key in s['concentrations']]
  solute=comps[0]['material_id'];transfer=op(rid,'drip','nitrate_stock_transferred_volume' if solute=='cerium-nitrate' else 'tea_receiving_volume','subsequent_stock_solution_portion_not_total_stock_preparation_volume','Subsequent stock portion')
  summary=sm[solute]['name']+' in '+sm[comps[1]['material_id']]['name']+'; '+', '.join(q['display_value'] for q in conc)+' reported stock concentration.'
  limit='The '+transfer['display_value']+' portion is the amount subsequently used in precipitation. Preparation mass, final stock preparation volume and storage are not reported. Solute and solvent depictions are separate references, not a measured dissolved complex.'
  if solute=='cerium-nitrate':limit+=' Six water molecules are part of the nitrate hydrate formula; no separate water charge is introduced.'
  else:limit+=' Triethanolamine is shown by its name-qualified graph; the source-printed formula conflict is retained.'
  row={'record_id':rid,'stock_id':s['id'],'json_pointer':f'/stocks/{si}','canonical_record_sha256':sha(paths[rid]),'canonical_stock':deepcopy(s),'source_stock':deepcopy(src),'components':comps,'concentrations':deepcopy(s['concentrations']),'concentration_links':conc,'solution_quantity_links':[transfer],'scope':s['scope'],'evidence':deepcopy(s['evidence']),'display_summary':summary,'display_limit':limit,'binding_approved':False};stockrows.append(row)
  contexts.append({'record_id':rid,'id':'pati2009-'+s['id'],'label':s['name'],'scope':summary+' '+limit,'components':[{'material_id':c['material_id'],'registry_id':c['registry_id'],'role':c['role'],'label':sm[c['material_id']]['name'],'viewOverrides':{'caption':entries[c['material_id']]['caption']+' In this stock: '+summary+' '+limit,'limitations':[limit]+entries[c['material_id']]['limitations']}} for c in comps],'binding_approved':False})
ck('Exact 45 slots / 6 stocks / 12 components',len(slots)==45 and len(stockrows)==6 and sum(len(x['components']) for x in stockrows)==12)
save('bindings-proposal.json',bindings);save('material-slot-map.json',{'schema':'mattersyn-molecular-slot-proposal/1','material_slot_count':45,'identity_count':20,'slots':slots,'independent_audit':'pending'})
save('stock-component-map.json',{'schema':'mattersyn-stock-component-proposal/1','stock_count':6,'component_count':12,'stocks':stockrows,'independent_audit':'pending'})
save('solution-components-proposal.json',{'schemaVersion':'1.0','contexts':contexts,'binding_approved':False})
inp=read(O/'input-bindings.json');inp['canonical_records']={str(paths[rid]):sha(paths[rid]) for rid in records};save('input-bindings.json',inp)
save('binding-author-checks.json',{'author':'/root/peng1998_reader_assets','status':'passed_author_checks','check_count':len(checks),'checks':checks,'independent_approval':False})
print(json.dumps({'slots':len(slots),'stocks':len(stockrows),'components':12,'checks':len(checks)}))
