"""Private Evans apparatus proposal, derived from independently passed v3 operations."""
from pathlib import Path
import json,hashlib,shutil
E=Path(__file__).resolve().parents[1];M=E.parents[4];S=M/'recipe-atlas'
OUT=E/'visuals/apparatus/v1';OUT.mkdir(parents=True,exist_ok=True)
source=E/'canonical-proposal/v3';manifest=json.loads((source/'record-manifest.json').read_text(encoding='utf8'))
records=[json.loads(Path(x['path']).read_text(encoding='utf8')) for x in manifest['records']]
assert len(records)==32 and sum(len(r['operations']) for r in records)==46
choices={
 'cd-oleate':['heat','cool','centrifuge'],
 'pb-oleate':['heat','centrifuge','ftir'],
 'topse':['glovebox','solution'],
 'dppse':['glovebox','reflux','rotavap-crystal'],
 'tippse':['glovebox','vacuum-crystal'],
 'tepse':['glovebox','filter-concentrate','crystal-wash'],
 'tppse':['glovebox','filter-concentrate','crystal-wash'],
 'tertiary-negative-rescue':['nmr-load','nmr-heat','rescue','alternatives'],
 'topse-distillation':['distill-setup','distill-cuts','residue'],
 'topse-b-stock':['b-stock'],
 'pbse-msc-family':['heat','abc-inject','absorption','abc-context'],
 'dpp-pb-control':['flame-seal','nmr-oil','no-challenge'],
 'dpp-cd-negative':['nmr-oil','no-reaction'],
 'species9-crystallization':['two-stocks','slow-evaporation','ratio-conflict'],
 'pbse-qd':['glovebox','combine-stock','cuvette-bath','optical'],
 'cdse-qd':['heat','hot-inject','optical']}
data={'source_group':'evans2010','status':'private_author_proposal_pending_independent_apparatus_audit','author':'/root','records':{},'configs':{}}
for r in records:
 if not r['operations']:continue
 key=r['record_id'].removeprefix('evans-2010-');kinds=choices[key];assert len(kinds)==len(r['operations'])
 data['records'][r['record_id']]=[o['id'] for o in r['operations']]
 for o,kind in zip(r['operations'],kinds):
  data['configs'][o['id']]={'art':kind,'record_key':key,'extra_rows':[]}
  rows=data['configs'][o['id']]['extra_rows']
  if kind=='distill-cuts':rows.append({'label':'Fraction identity','value':'A, second cut and third cut are separate collected fractions. The residual pot is a separate output leading to C. B is prepared independently.'})
  if kind=='residue':rows.append({'label':'Retained fraction','value':'Approximately 4 mL residual pot C; it is not a collected distillate.'})
  if kind=='abc-inject':rows.append({'label':'Stock choice','value':'Choose one A, B or C source. These are mutually exclusive variants, not three jointly injected stocks.'})
  if kind=='optical':rows.append({'label':'Spectral scope','value':'Reported Figure S15 example; no generated spectrum or one-to-one TEM specimen assignment is supplied by this schematic.'})
  if kind=='no-reaction':rows.append({'label':'Negative evidence','value':'No reaction reported within the stated observation scope. No detection limit or numerical duration is inferred.'})
  if kind=='heat' and key=='pb-oleate':rows.append({'label':'Inherited procedure','value':'The source explicitly adopts the Cd-oleate method for the remaining preparation; this is not an independently measured second set of conditions.'})
  if kind in {'glovebox','solution','combine-stock','two-stocks','slow-evaporation'}:rows.append({'label':'Vessel geometry','value':'Explanatory container silhouette; vessel type and dimensions are not inferred unless explicitly reported beside this scene.'})
base=M/'research-assets/incoming-paper-monitor/batches/20260919-five-paper-pilot/jp0219348/visuals/apparatus/v1/heo2003-protocol.mjs'
txt=base.read_text(encoding='utf8');before=txt[:txt.index('const DATA=')];after=txt[txt.index('const C='):]
after=after[:after.index('function crystal(')]+(E/'visuals/evans_apparatus_geometry.mjs').read_text(encoding='utf8')+'\n'+after[after.index('function quantity('):]
after=after.replace('Heo2003','Evans2010').replace('heo2003','evans2010').replace('Heo et al. 2003','Evans et al. 2010').replace('Missing Heo scene','Missing Evans scene')
after=after.replace('heo-scene','evans-scene')
after=after.replace("if(o.id==='exchange'){const feed=r.stocks?.find(s=>s.id==='tl-acetate-feed');if(feed?.concentrations?.thallous_acetate)rows.unshift({label:'Thallous acetate feed',value:quantity(feed.concentrations.thallous_acetate)});}",'')
after=after.replace('viewBox="0 75 400 385"','viewBox="0 75 400 385"')
after=after.replace('Crystal shape, apparatus geometry and colors are illustrative; reported conditions and unresolved source discrepancies are retained.','Apparatus geometry, liquid colors and crystal symbols are explanatory. Conditions, retained fractions and source discrepancies remain attached to each operation.')
after=after.replace('No measured diffraction pattern or exact apparatus dimensions are implied.','No measured spectrum, exact apparatus dimensions, particle size or vessel pressure is inferred.')
(OUT/'evans2010-protocol.mjs').write_text(before+'const DATA='+json.dumps(data,ensure_ascii=False)+';\n'+after,encoding='utf8')
shutil.copy2(S/'dist/quantity-value.mjs',OUT/'quantity-value.mjs')
payload=[{k:r[k] for k in ['record_id','lineage','operations']} for r in records if r['operations']]
(OUT/'records.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(OUT/'scene-config.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'operations':46,'records_with_operations':len(payload),'unique_visual_types':len(set(c['art'] for c in data['configs'].values())),'output':str(OUT)}))
