"""Private Sommer material-slot bindings. Read source/canonical; write this folder only."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
import argparse,hashlib,json
O=Path(__file__).resolve().parent;P=O.parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--canonical-manifest',type=Path,default=P/'canonical-proposal/v1/record-manifest.json');ap.add_argument('--source-audit',type=Path);args=ap.parse_args()
assert not(O/'package-freeze.json').exists(),'Never overwrite a frozen package.'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jsha(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def ptr(x,p):
 for t in p.strip('/').split('/'):x=x[int(t)]if isinstance(x,list)else x[t]
 return x
def qfmt(q):
 raw=q.get('raw_text')
 if raw:return raw+(' '+q['unit']if q.get('unit')and q['unit']!='ratio_parts'else'')
 return str(q.get('value'))+(' '+q['unit']if q.get('unit')else'')if q.get('value')is not None else'Not reported'
manifest=read(args.canonical_manifest);records={};paths={};checks=[]
def ck(s,v):checks.append({'check':s,'passed':bool(v)});assert v,s
for row in manifest['records']:
 path=Path(row['path']);ck('Canonical hash '+row['record_id'],sha(path)==row['sha256']);records[row['record_id']]=read(path);paths[row['record_id']]=path
sf=read(P/'source-facts.json');sm={m['id']:m for m in sf['materials']};ss={s['id']:s for s in sf['stocks']}
registry=read(O/'registry-additions.json');entries={e['provenance']['sourceMaterialId']:e for e in registry['entries']}
if args.source_audit:
 audit=read(args.source_audit);ck('Supplied source audit passed',str(audit.get('status','')).startswith('passed'))
def qlink(rid,p,kind,label=None):return {'record_id':rid,'json_pointer':p,'quantity':deepcopy(ptr(records[rid],p)),'meaning':kind,'display_label':label or p.split('/')[-1].replace('_',' '),'display_value':qfmt(ptr(records[rid],p))}
def opref(rid,opid,k,kind,label=None):
 oi=next(i for i,o in enumerate(records[rid]['operations'])if o['id']==opid)
 return qlink(rid,f'/operations/{oi}/parameters/{k}',kind,label)
QMAP={
 ('mw-route','zn-nitrate'):[('mw-dissolve','zn_no3_2_6h2o_mass','whole_stock_component_charge')],
 ('mw-route','al-nitrate'):[('mw-dissolve','al_no3_3_9h2o_mass','whole_stock_component_charge')],
 ('mw-route','demin-feed-water'):[('mw-dissolve','demineralized_water_charge','charged_water_not_final_volume')],
 ('mw-route','quartz-vessel'):[('mw-load','quartz_vessel_capacity','nominal_vessel_capacity_not_solution_volume')],
 ('acs-route','ptfe-autoclave'):[('acs-load','vessel_capacity','nominal_vessel_capacity_not_solution_volume')],
 ('insitu-nitrate','zn-nitrate'):[('insitu-stock','zn_no3_2_6h2o_mass','whole_stock_component_charge')],
 ('insitu-nitrate','al-nitrate'):[('insitu-stock','al_no3_3_9h2o_mass','whole_stock_component_charge')],
 ('insitu-nitrate','sapphire-capillary'):[('insitu-stir-load','capillary_inner_diameter','support_dimension'),('insitu-stir-load','capillary_outer_diameter','support_dimension')],
 ('insitu-oxide','zno-feed'):[('oxide-slurry','zno_mass','whole_suspension_component_charge')],
 ('insitu-oxide','aloh3'):[('oxide-slurry','al_oh_3_mass','whole_suspension_component_charge')],
 ('lab-workup','demin-wash-water'):[('lab-wash','water_washes','wash_count_not_volume')],
 ('lab-workup','ethanol-96'):[('lab-wash','ethanol_washes','wash_count_not_volume'),('lab-wash','wash_ethanol_grade','wash_grade_not_yield')],
 ('microscopy-procedure','ethanol-99'):[('microscopy-disperse','dispersion_ethanol_grade','dispersion_grade_not_wash_grade')],
 ('microscopy-procedure','tem-grid'):[('microscopy-deposit','grid_mesh','support_mesh_not_particle_size')],
 ('synchrotron-procedure','glass-capillary'):[('synchrotron-load-acquire','glass_capillary_diameter','support_dimension')],
 ('scf-route','naoh'):[('scf-feed','oh_concentration','source_feed_context_not_reconstructed_NaOH_mass')],
 ('scf-route','insitu-water'):[('scf-feed','solvent_flow_rate','source_solvent_flow_not_grade_or_stock_charge')],
}
grade_ids={'zn-nitrate':'sommer2020-reagents-q1','al-nitrate':'sommer2020-reagents-q2','naoh':'sommer2020-reagents-q3','zno-feed':'sommer2020-reagents-q4'}
grade_refs={};rid='sommer-2020-source-materials'
for mid,tid in grade_ids.items():
 mi=next(i for i,m in enumerate(records[rid]['measurements'])if m['id']==tid);grade_refs[mid]=qlink(rid,f'/measurements/{mi}/value','source_wide_grade_or_purchased_size_not_source_product_measurement')
bindings={'schemaVersion':'1.0','source_id':'sommer2020','status':'private_author_proposal_pending_independent_molecular_audit','recordBindings':{},'bindingNotes':{},'binding_approved':False,'published':False,'eligible_training':False};slots=[]
for rid,r in records.items():
 if not r['materials']:continue
 bindings['recordBindings'][rid]={};bindings['bindingNotes'][rid]={}
 for i,m in enumerate(r['materials']):
  mid=m['id'];e=entries[mid];ck(rid+'/'+mid+' exact source identity',m['formula']==sm[mid]['source_formula_or_abbreviation']and m['name']==sm[mid]['name'])
  refs=[opref(rid,op,k,kind)for op,k,kind in QMAP.get((rid.removeprefix('sommer-2020-'),mid),[])];gr=[deepcopy(grade_refs[mid])]if mid in grade_refs else[]
  caption=m['name']+'; '+m['role'].replace('_',' ')+' in this source context. '+sm[mid]['scope_note']
  if refs:caption+=' Context-specific quantities: '+'; '.join(q['display_label']+': '+q['display_value']for q in refs)+'.'
  if gr:caption+=' Source-wide '+('purchased nominal size'if mid=='zno-feed'else'purity lower bound')+': '+gr[0]['display_value']+'.'
  caption+=' '+e['limitations'][-1]+' Storage conditions are not supplied for this material context.'
  note={'record_id':rid,'material_id':mid,'json_pointer':f'/materials/{i}','canonical_record_sha256':sha(paths[rid]),'registry_id':e['id'],'entry_sha256':jsha(e),'canonical_identity':deepcopy(m),'source_material':deepcopy(sm[mid]),'quantity_links':refs,'grade_context_links':gr,'viewOverrides':{'name':m['name'],'caption':caption,'limitations':deepcopy(e['limitations'])},'binding_approved':False,'source_specific_join':'Exact material identity slot only. Quantities retain their operation or stock context. No physical product/specimen or atomic-coordinate binding.'}
  bindings['recordBindings'][rid][mid]=e['id'];bindings['bindingNotes'][rid][mid]=note;slots.append(note)
stock_rows=[];contexts=[]
for rid,r in records.items():
 for si,s in enumerate(r['stocks']):
  comps=[]
  for ci,c in enumerate(s['components']):
   mid=c['material_id'];mi=next(i for i,m in enumerate(r['materials'])if m['id']==mid)
   refs=[qlink(rid,f'/stocks/{si}/components/{ci}/quantities/{k}','whole_formulation_component_charge_not_additional_event')for k in c['quantities']]
   comps.append({'material_id':mid,'registry_id':entries[mid]['id'],'role':r['materials'][mi]['role'],'json_pointer':f'/stocks/{si}/components/{ci}','material_json_pointer':f'/materials/{mi}','source_quantities':deepcopy(c['quantities']),'quantity_links':refs,'binding_approved':False})
  cqs=[qlink(rid,f'/stocks/{si}/concentrations/{k}','reported_final_formulation_concentration_not_isolated_component_dose')for k in s['concentrations']]
  extra=[]
  if s['id']=='insitu-nitrate-stock':extra=[opref(rid,'insitu-stock','solution_volume','stock_solution_volume_not_water_charge')]
  if s['id']=='insitu-base-solutions':extra=[opref(rid,'insitu-mix','naoh_solution_aliquot','delivered_NaOH_solution_aliquot_not_whole_stock_volume')]
  summary='; '.join(sm[c['material_id']]['name']+': '+('; '.join(q['display_value']for q in c['quantity_links'])or'amount not separately specified here')for c in comps)
  allq=cqs+extra
  if allq:summary+='; '+'; '.join(q['display_label']+': '+q['display_value']for q in allq)
  limit=s['scope']+' Separate references do not determine dissolved coordination, protonation, hydration or aggregation. No additional stock charge is created by this display.'
  if s['id'].startswith('mw-')and s['id']!='mw-nitrate-stock':limit+=' Nitrate-salt and water constituents are inherited from mw-nitrate-stock; its charges are not repeated. These formulations are alternatives.'
  if s['id']=='insitu-base-solutions':limit+=' Only the delivered 1.00 mL NaOH-solution aliquot is attached here; final mixed Zn/Al concentrations are excluded. Stock preparation mass and water volume remain unknown.'
  row={'record_id':rid,'stock_id':s['id'],'json_pointer':f'/stocks/{si}','canonical_record_sha256':sha(paths[rid]),'canonical_stock':deepcopy(s),'source_stock':deepcopy(ss[s['id']]),'components':comps,'concentrations':deepcopy(s['concentrations']),'concentration_links':cqs,'solution_quantity_links':extra,'scope':s['scope'],'evidence':deepcopy(s['evidence']),'display_summary':summary,'display_limit':limit,'binding_approved':False};stock_rows.append(row)
  ctx={'record_id':rid,'id':'sommer2020-'+s['id'],'label':s['name'],'scope':summary+'. '+limit,'components':[{'material_id':c['material_id'],'registry_id':c['registry_id'],'role':c['role'],'label':sm[c['material_id']]['name'],'viewOverrides':{'caption':sm[c['material_id']]['name']+' in '+s['name']+'. '+summary+'. '+limit,'limitations':[limit,entries[c['material_id']]['limitations'][-1]]}}for c in comps],'binding_approved':False};contexts.append(ctx)
ck('28 identities,62 slots,7 stocks,23 components',len(entries)==28 and len(slots)==62 and len(stock_rows)==7 and sum(len(s['components'])for s in stock_rows)==23)
for s in stock_rows:
 if s['stock_id']=='insitu-base-solutions':ck('No mixed-metal quantities on NaOH stock',not s['concentrations']and all(q['json_pointer'].endswith('/naoh_solution_aliquot')for q in s['solution_quantity_links']))
save('bindings-proposal.json',bindings);save('material-slot-map.json',{'schema':'mattersyn-molecular-slot-proposal/1','material_slot_count':len(slots),'identity_count':len(entries),'slots':slots,'independent_audit':'pending'})
save('stock-component-map.json',{'schema':'mattersyn-stock-component-proposal/1','stock_count':7,'component_count':23,'stocks':stock_rows,'independent_audit':'pending'});save('solution-components-proposal.json',{'schemaVersion':'1.0','contexts':contexts,'binding_approved':False})
inputmap=read(O/'input-bindings.json');inputmap['canonical_record_manifest']={'path':str(args.canonical_manifest),'sha256':sha(args.canonical_manifest)};inputmap['source_audit']={'path':str(args.source_audit),'sha256':sha(args.source_audit)}if args.source_audit else None
inputmap['canonical_records']={str(paths[rid]):sha(paths[rid])for rid in records};save('input-bindings.json',inputmap)
save('binding-author-checks.json',{'status':'passed_working_author_checks','created_at':datetime.now(timezone.utc).isoformat(),'source_audit_provided':bool(args.source_audit),'canonical_freeze_confirmed':False,'check_count':len(checks),'checks':checks,'independent_approval':False})
print(json.dumps({'status':'working_bindings_created_unapproved','slots':len(slots),'stocks':len(stock_rows),'components':sum(len(s['components'])for s in stock_rows),'checks':len(checks)}))
