"""Private, exact Sasongko reagent and solution-component author bindings."""
from pathlib import Path
from copy import deepcopy
import json,hashlib,sys,textwrap,html
O=Path(__file__).resolve().parent;J=O.parents[1];C=J/'canonical-proposal/v1';S=J/'source-extraction-revision-2';M=J.parents[4]
sys.path.insert(0,str(M/'research-assets/corpus-20260917/runtime'))
import fitz
assert not (O/'package-freeze.json').exists()
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jsha(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def save(n,v):(O/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
def ptr(v,p):
 for k in p.strip('/').split('/'):v=v[int(k)] if isinstance(v,list) else v[k.replace('~1','/').replace('~0','~')]
 return v
def fmt(q):
 unit=q.get('unit') or ''
 if unit=='volume_parts':unit='volume part' if q.get('value')==1 else 'volume parts'
 return (q.get('raw_text') or (str(q['value']) if q.get('value') is not None else 'Not reported'))+' '+unit
checks=[]
def ck(n,v):checks.append({'check':n,'passed':bool(v)});assert v,n
manifest=read(C/'record-manifest.json');records={};paths={}
for x in manifest['records']:
 ck('Canonical hash '+x['record_id'],sha(x['path'])==x['sha256']);r=read(x['path']);records[r['record_id']]=r;paths[r['record_id']]=Path(x['path'])
ck('Canonical freeze',sha(C/'package-freeze.json')=='3cab2fe6181dbf2149b2a0ac59f4a80d99c05cab4870342e141815c904549fb5')
source=read(S/'source-facts.json');sm={x['id']:x for x in source['materials']};ss={x['id']:x for x in source['stocks']};entries={e['provenance']['sourceMaterialId']:e for e in read(O/'registry-additions.json')['entries']}
def link(rid,p,meaning,label):
 q=ptr(records[rid],p);ck('Typed exact quantity '+rid+p,'status' in q and 'unit' in q)
 return {'record_id':rid,'json_pointer':p,'quantity':deepcopy(q),'meaning':meaning,'display_label':label,'display_value':fmt(q)}
def op(rid,oid,key,meaning,label):
 i=next(i for i,x in enumerate(records[rid]['operations']) if x['id']==oid)
 return link(rid,f'/operations/{i}/parameters/{key}',meaning,label)
H='sasongko-2025-hot-injection';F='sasongko-2025-fa-oleate-preparation'
mapq={
 (H,'pbi2'):[('lead-charge-degas','pbi2_charge','reaction_charge','Lead iodide charge')],
 (H,'ode'):[('lead-charge-degas','ode_charge','reaction_charge_not_upstream_stock_charge','Reaction ODE charge')],
 (H,'oam'):[('add-oam','oam_volume','reaction_charge','Reaction OAm charge')],
 (H,'oa'):[('add-oa','selected_oa_volume','select_one_source_paired_option_not_all_values','Selected OA charge')],
 (F,'formamidine-acetate'):[('fa-charge','formamidine_acetate_charge','whole_upstream_stock_charge','Stock salt charge')],
 (F,'oa'):[('fa-charge','stock_oa_charge','whole_upstream_stock_charge','Stock OA charge')],
 (F,'ode'):[('fa-charge','stock_ode_charge','whole_upstream_stock_charge','Stock ODE charge')]}
bindings={'schemaVersion':'1.0','source_id':'sasongko2025','recordBindings':{},'bindingNotes':{},'status':'private_author_proposal','binding_approved':False,'published':False,'eligible_training':False};slots=[]
for rid,r in records.items():
 if not r['materials']:continue
 bindings['recordBindings'][rid]={};bindings['bindingNotes'][rid]={}
 for mi,m in enumerate(r['materials']):
  mid=m['id'];e=entries[mid];ck(rid+'/'+mid+' source identity',m['formula']==sm[mid]['source_formula_or_abbreviation'] and m['name']==sm[mid]['name'])
  refs=[op(rid,*q) for q in mapq.get((rid,mid),[])];options=[]
  key={'oa':'oa_volume','oam':'oam_volume','acetonitrile':'wash_acetonitrile_parts','toluene':'wash_toluene_parts'}.get(mid)
  if rid==H and key:
   for oi,opt in enumerate(r['condition_options']):
    options.append({'condition_option_id':opt['id'],'condition_option':deepcopy(opt),'quantity_link':link(rid,f'/condition_options/{oi}/parameters/{key}','paired_source_option_not_cartesian_expansion',opt['id']+' '+key.replace('_',' '))})
  grades=[link(rid,f'/materials/{mi}/quantities/{k}','source_reagent_grade_not_stock_concentration','Source reagent grade') for k in m['quantities']]
  caption=e['caption']+' Role here: '+m['role']+'.'
  if refs:caption+=' '+ '; '.join(q['display_label']+': '+q['display_value'] for q in refs)+'.'
  if options:caption+=' Source conditions remain paired alternatives; the complete option and exact quantities are retained in the binding map.'
  if rid==H and mid=='formamidine-acetate':caption+=' Upstream stock ingredient, not an additional salt charge at injection; 0.51 mL of the prepared stock is injected.'
  if rid.endswith('source-materials'):caption+=' This inventory slot does not imply an experimental charge or product-coordinate assignment.'
  note={'record_id':rid,'material_id':mid,'json_pointer':f'/materials/{mi}','canonical_record_sha256':sha(paths[rid]),'registry_id':e['id'],'entry_sha256':jsha(e),'canonical_identity':deepcopy(m),'source_material':deepcopy(sm[mid]),'quantity_links':refs,'grade_context_links':grades,'condition_option_links':options,'viewOverrides':{'name':m['name'],'caption':caption,'limitations':deepcopy(e['limitations'])},'reference_formula':e['formula'],'literal_source_formula':m['formula'],'binding_approved':False,'source_specific_join':'Exact material slot. No product/sample coordinates or task admission.'}
  bindings['recordBindings'][rid][mid]=e['id'];bindings['bindingNotes'][rid][mid]=note;slots.append(note)
stockrows=[];contexts=[]
for rid,r in records.items():
 for si,s in enumerate(r['stocks']):
  src=ss[s['id']];comps=[]
  for ci,c in enumerate(s['components']):
   mid=c['material_id'];mi=next(i for i,m in enumerate(r['materials']) if m['id']==mid);sc=next(c for c in src['components'] if c['material_id']==mid)
   refs=[link(rid,f'/stocks/{si}/components/{ci}/quantities/{k}','relative_volume_parts_not_absolute_charge' if k=='volume_parts' else 'whole_stock_formulation_not_injection_aliquot',k.replace('_',' ')) for k in c['quantities']]
   comps.append({'material_id':mid,'registry_id':entries[mid]['id'],'role':sc['role'],'canonical_material_role':r['materials'][mi]['role'],'json_pointer':f'/stocks/{si}/components/{ci}','material_json_pointer':f'/materials/{mi}','source_quantities':deepcopy(c['quantities']),'quantity_links':refs,'binding_approved':False})
  fa=s['id']=='fa-oleate-stock';solrefs=[op(H,'inject-fa','fa_precursor_aliquot','subsequent_prepared_stock_aliquot_not_stock_preparation_volume','Subsequent injection aliquot')] if fa else []
  summary='; '.join(sm[c['material_id']]['name']+': '+', '.join(q['display_value'] for q in c['quantity_links']) for c in comps)+'.'
  limit=('Whole precursor formulation; the separate injection uses 0.51 mL. Final volume, concentration, storage and dissolved species are unknown. The three references describe ingredients, not an identified FA-oleate complex.' if fa else 'One alternative washing formulation, with relative volume parts only. Absolute volume, concentration, premixing, storage and repetition count are unreported. Select the ratio paired with the source condition; do not combine the alternatives.')
  row={'record_id':rid,'stock_id':s['id'],'json_pointer':f'/stocks/{si}','canonical_record_sha256':sha(paths[rid]),'canonical_stock':deepcopy(s),'source_stock':deepcopy(src),'components':comps,'concentrations':deepcopy(s['concentrations']),'concentration_links':[],'solution_quantity_links':solrefs,'scope':s['scope'],'evidence':deepcopy(s['evidence']),'display_summary':summary,'display_limit':limit,'stock_svg_path':'stock-svg/sasongko2025-'+s['id']+'.svg','binding_approved':False};stockrows.append(row)
  contexts.append({'record_id':rid,'id':rid+'-'+s['id'],'label':s['name'],'scope':summary+' '+limit,'components':[{'material_id':c['material_id'],'registry_id':c['registry_id'],'role':c['role'],'label':sm[c['material_id']]['name'],'viewOverrides':{'caption':entries[c['material_id']]['caption']+' In this formulation: '+summary+' '+limit,'limitations':[limit]+entries[c['material_id']]['limitations']}} for c in comps],'binding_approved':False})
ck('26 slots / 5 stocks / 12 components',len(slots)==26 and len(stockrows)==5 and sum(len(x['components']) for x in stockrows)==12)
save('bindings-proposal.json',bindings);save('material-slot-map.json',{'schema':'mattersyn-molecular-slot-proposal/1','material_slot_count':len(slots),'identity_count':len(entries),'slots':slots,'independent_audit':'pending'})
save('stock-component-map.json',{'schema':'mattersyn-stock-component-proposal/1','stock_count':len(stockrows),'component_count':12,'stocks':stockrows,'independent_audit':'pending'})
save('solution-components-proposal.json',{'schemaVersion':'1.0','contexts':contexts,'binding_approved':False})
def tx(x,y,t,size=20):return f'<text x="{x}" y="{y}" font-family="Arial, sans-serif" font-size="{size}" fill="#173445">{html.escape(t)}</text>'
stockart=[]
for sid in ss:
 row=next(x for x in stockrows if x['stock_id']==sid);fa=sid=='fa-oleate-stock';lines=textwrap.wrap(row['display_limit'],104);h=700
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="{h}" viewBox="0 0 1100 {h}"><rect x="1" y="1" width="1098" height="698" rx="18" fill="white" stroke="#bfd1dc"/>'+tx(35,50,ss[sid]['name'],26)+tx(35,95,'Ingredient references and source amounts; no dissolved complex is drawn',19)
 for i,c in enumerate(row['components']):
  y=130+i*112;svg+=f'<rect x="35" y="{y}" width="1030" height="94" rx="12" fill="#edf5f8"/>'+tx(58,y+32,sm[c['material_id']]['name'],23)+tx(58,y+68,', '.join(q['display_value'] for q in c['quantity_links'])+' — '+c['role'],20)
 y=512 if fa else 412
 for i,l in enumerate(lines):svg+=tx(35,y+i*26,l,18)
 svg+=tx(35,670,'Source: Sasongko et al. 2025, Supporting Information p. S3',17)+'</svg>';p=O/row['stock_svg_path'];p.write_text(svg,'utf8');doc=fitz.open(stream=svg.encode(),filetype='svg');png=O/'stock-previews'/('sasongko2025-'+sid+'.png');doc[0].get_pixmap(matrix=fitz.Matrix(1,1),alpha=False).save(png)
 stockart.append({'stock_id':sid,'path':row['stock_svg_path'],'sha256':sha(p),'preview':str(png.relative_to(O)),'mapped_record_ids':[x['record_id'] for x in stockrows if x['stock_id']==sid],'components':[x['material_id'] for x in row['components']],'source_scope':row['display_limit'],'atomic_model':False})
save('stock-illustration-proposal.json',{'source_id':'sasongko2025','formulations':stockart,'binding_approved':False})
inp=read(O/'input-bindings.json');inp['canonical_records']={str(paths[rid]):sha(paths[rid]) for rid in records};inp['consumer_snapshot']={'path':str(O/'reference-snapshots/chemical-viewer.mjs'),'sha256':sha(O/'reference-snapshots/chemical-viewer.mjs')};save('input-bindings.json',inp)
save('binding-author-checks.json',{'status':'passed_author_checks','check_count':len(checks),'checks':checks,'independent_approval':False})
print(json.dumps({'slots':len(slots),'stocks':len(stockrows),'components':12,'checks':len(checks)}))
