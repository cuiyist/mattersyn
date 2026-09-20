"""Private Pati canonical proposal; exact audited source remains read-only."""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import json,hashlib,re,sys
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;O=P/'canonical-proposal/v1';O.mkdir(parents=True,exist_ok=True)
assert not(O/'package-manifest.json').exists(),'Preserve frozen proposal'
S=Path('[local path redacted]');sys.path.insert(0,str(S/'scripts'))
from record_helpers import record,source,fact,qty,material,operation,state,product,measurement
from dataset_lib import validate_record,eligibility,build_groups
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def norm(x):return re.sub('[^a-z0-9]+','-',str(x).lower()).strip('-')
def key(x):return norm(x).replace('-','_')
def esc(x):return str(x).replace('~','~0').replace('/','~1')
def compact(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'))
def resolve(x,p):
 for t in p.strip('/').split('/')if p else[]:x=x[int(t)]if isinstance(x,list)else x[t.replace('~1','/').replace('~0','~')]
 return x
D=read(P/'source-facts.json');I=read(P/'source-inventory.json');T=read(P/'source-tables.json');FR=read(P/'package-freeze.json');AP=P/'source-independent-audit/independent-audit.json';AU=read(AP)
assert sha(P/'package-freeze.json')=='b2d275bdd94514bba3b2b4e9f4c91920791801f268bc86a5616b8af87e89c0ce'
assert sha(AP)=='792fe4a10d755d7db21d3c8dee035591a682563bfa9e5ffce3b1a9882daa37eb'
for p,h in FR['bound_files'].items():assert sha(p)==h,p
SID='pati2009';PRE='pati-2009-';FM={f['id']:f for f in D['facts']};MM={m['id']:m for m in D['materials']};SC={s['id']:s for s in D['sample_contexts']};PP={p['id']:p for p in D['protocols']};CON={x['id']:x for x in D['conflicts']};GAP={x['id']:x for x in D['missingness']}
PAY={'source-facts.json':D,'source-tables.json':T};UU={u['id']:u for u in I['inventory_units']};UM={}
for u in UU.values():
 ob=resolve(PAY[u['payload_path']],u['json_pointer']);oid=ob.get('id',ob.get('label'))
 if u['kind']=='figure_panel':oid=u['json_pointer']
 UM[(u['kind'],oid)]=u['id']
R={};FL={i:[]for i in FM};UL={i:[]for i in UU};TL={};OBJECTS=[];TABLEMETA=[];OP_SCOPE=[]
def E(es):return[{'source_id':SID,'locator':e['document_role'].upper()+' PDF p. '+str(e['pdf_page'])+' (printed '+str(e['printed_page'])+'), '+e['locator']+'; source SHA256 '+e['source_sha256']}for e in es]
def FE(fid):return E(FM[SID+'-'+fid]['evidence'])
def cn(ids):return' '.join(i+': '+(CON[i]['description']if i in CON else GAP[i]['description'])for i in ids if i in CON or i in GAP)
def link(cat,sid,r,ptr,sp=None):
 b={'record_id':r['record_id'],'pointer':ptr}
 if sp is not None:b['source_pointer']=sp
 if cat=='fact':FL[sid].append(b)
 elif cat=='unit':UL[sid].append(b)
 elif cat=='table_cell':TL.setdefault(sid,[]).append(b)
 else:OBJECTS.append({'category':cat,'source_id':sid,**b})
def unit(kind,sid,r,ptr):link('unit',UM[(kind,sid)],r,ptr)
AUDIT_NOTE='The complete supplied four-page main and four-page matched SI extraction passed distinct source audit. Canonical and reader proposals remain unapproved pending their separate review. Historical pending flags in retained source payloads describe their author-freeze stage.'
COMMON=[AUDIT_NOTE,'Records and context counts do not count independent physical batches.','Three alcohol substitutions, as-prepared/calcined powders, solution DLS and XPS exposure states remain distinct.','As-prepared local CeO2 crystallites do not establish pure whole-powder composition.','No qualified atomic model, exact recipe–structure pair, automatic same-aliquot join or training admission.']
SRC=source(SID,D['doi'],D['title'],'; '.join(D['authors']),D['year'],si='Matched four-page local XPS SI; all supplied pages read and visually inspected. '+AUDIT_NOTE);SRC['main_status']='Complete four-page main read and visually inspected. '+AUDIT_NOTE
CONFIG={sol+'-route':(name+' precipitation','literature_protocol')for sol,name in [('ethanol','Ethanol'),('propanol','1-Propanol'),('butanol','1-Butanol')]}
CONFIG.update({'filtrate-diagnostic':('Separate filtrate-completeness test','procedure'),'calcination':('Separate powder calcination','procedure')})
CONFIG.update({p['id']:(p['title'],'procedure')for p in D['protocols']if p['id']not in['precipitation-family','calcination']})
CONFIG.update({'source-materials':('Source-qualified material inventory','observation'),'structure-results':('Microscopy, diffraction and dispersity observations','observation'),'property-results':('Thermal, surface and packing observations','observation'),'mechanistic-context':('Author interpretations and cited comparisons','observation'),'source-context':('Sources and unresolved limitations','observation')})
for pid,(title,kind)in CONFIG.items():
 r=record(PRE+pid,'Pati et al. (2009) · '+title,'Study source context'if pid=='source-context'else'Study materials'if pid=='source-materials'else'CeO2','Ceria precipitation with triethanolamine',title,deepcopy(SRC),'Complete supplied main and SI; exact local source locators',kind);r['schema_version']='1.3.0';r['lineage'].update(source_group=SID,recipe_family=SID+'-alcohol-tea-study')
 r['quality'].update(review_status='imported_unreviewed',review_scope=AUDIT_NOTE,requested_tasks=[],experimental_outcome='not_established',missing_fields=COMMON.copy(),conflicts=[])
 r['intended_target']['composition']=fact('CeO2'if kind=='literature_protocol'else None,FE('identity'),note='Intended target only; no pure whole as-prepared product composition is asserted.')
 R[pid]=r
OWNER_GROUPS={
'source-context':['identity','acknowledgments','si-declaration'],
'source-materials':['cerium-material','tea-material','alcohol-materials','stocks'],
'ethanol-route':['precipitation','poststir','filtration','alcohol-wash-dry','acetone-wash','colors'],
'filtrate-diagnostic':['filtrate-control'],'calcination':['calcination'],
'xrd':['xrd-acquisition'],'bet':['bet-acquisition'],'tem':['tem-acquisition'],'tga':['tga-acquisition'],'dsc':['dsc-acquisition'],'xps':['xps-acquisition'],'dls':['dls-acquisition'],'packing':['packing-acquisition'],
'xps-fit':['si-peak-labels','si-exposure','si-fitting','si-fit-four','si-fit-ten','si-short-results','si-long-results'],
'structure-results':['abstract','tem-size','saed','figure1-bars','dls-values','calcined-tem','asprep-xrd','calcined-xrd','conclusion-dls'],
'property-results':['bet-results','bet-diameters','tga-steps','tga-calculation','dsc-results','xps-elements','xps-short-main','packing-result'],
'mechanistic-context':['applications','prior-routes','prior-diethylamine','tea-motivation','dls-literature','solvent-effect','prior-deprotonation','hydroxo-conflict','water-model','fast-deprotonation','outlook']}
OWN={SID+'-'+fid:owner for owner,fs in OWNER_GROUPS.items()for fid in fs};assert set(OWN)==set(FM)
TEXT_STATUSES={'reported_text','reported_identifier','reported_ratio_parts','original_image','group_header'}
def Q(qv,scope='',extra=''):
 es=E(qv['evidence']);note=(extra+' '+cn(qv.get('conflict_ids',[])+qv.get('gap_ids',[]))).strip()
 if qv.get('uncertainty')is not None:note+=' Reported uncertainty '+str(qv['uncertainty'])+' '+str(qv.get('unit'))+'.'
 if qv['status']in TEXT_STATUSES:return fact(qv['raw_text'],es,note='Source context: '+scope+'. '+note)
 v=qv['value'];lo=(qv.get('range')or{}).get('min');hi=(qv.get('range')or{}).get('max');cmp=qv.get('comparison')
 if cmp in['<','<=']:hi=v;v=None
 if cmp in['>','>=']:lo=v;v=None
 return qty(v,qv.get('unit')or'',es,'reported'if v is not None or lo is not None or hi is not None else'not_reported',minimum=lo,maximum=hi,approximate=qv.get('approximate',False),qualifier=note,basis='Source context: '+scope+'.',raw_text=qv['raw_text'],minimum_exclusive=cmp=='>'if cmp in['>','>=']else None,maximum_exclusive=cmp=='<'if cmp in['<','<=']else None)
def sample(r,scope,es,formula=None):
 sid=norm(scope)
 if not any(p['sample_id']==sid for p in r['products']):
  p=product(sid,formula,E(es),link='general_context',notes=['Source scope: '+scope+'.','A context is not a new replicate or a verified same-aliquot cross-technique link.']);p['source_sample_label']=scope;r['products'].append(p);link('sample_context',scope,r,f'/products/{len(r["products"])-1}')
 return sid
def addm(r,mid,stage='characterization'):
 if any(m['id']==mid for m in r['materials']):return mid
 m=MM[mid];r['materials'].append(material(mid,m['name'],m['source_formula_or_abbreviation'],m['role'],stage,E(m['evidence']),notes=[m['scope_note'],'Named identity and printed formula retained separately; no molecular model approval.']));ptr=f'/materials/{len(r["materials"])-1}';unit('materials',mid,r,ptr)
 for fid in m['source_fact_ids']:
  for iq,qv in enumerate(FM[fid]['quantities']):
   if 'purity'in qv['meaning']and(mid in ['cerium-nitrate','tea']or(mid=='ethanol'and'ethanol'in qv['meaning'])or(mid=='propanol'and'propanol'in qv['meaning'])or(mid=='butanol'and'butanol'in qv['meaning'])):
    r['materials'][-1]['quantities']['reported_grade']=Q(qv,mid);link('fact',fid,r,ptr+'/quantities/reported_grade','/quantities/'+str(iq))
 return mid
for mid in MM:addm(R['source-materials'],mid)
for st in D['stocks']:
 sol=st['id'].split('-')[0];r=R[sol+'-route'];co=[{'material_id':addm(r,c['material_id'],'precursor_preparation'),'quantities':{}}for c in st['components']]
 stock={'id':st['id'],'name':st['name'],'components':co,'concentrations':{'reported_stock_concentration':Q(st['quantities'][0],st['id'],'Final stock concentration; preparation volume and solute mass not reported. 100 mL is subsequent transfer only.')},'preparation_operation_ids':['prepare-nitrate'if'nitrate'in st['id']else'prepare-tea'],'scope':st['scope_note']+' Preparation: '+st['preparation']+' Storage not reported.','evidence':E(st['evidence'])};r['stocks'].append(stock);unit('stocks',st['id'],r,f'/stocks/{len(r["stocks"])-1}')
OPMAP={};SUPPORT={'filter-paper','burette','erlenmeyer','pipet','air','nitrogen-bet'}
def buildops(r,pr,sol=None,only=None,skip=()):
 produced={};outmap={};knownstocks={s['id']for s in r['stocks']}
 for so in pr['operations']:
  if so['id']in skip or(only and so['id']not in only):continue
  j=len(r['operations']);isroute=sol is not None;stage='precursor_preparation'if so['id'].startswith('prepare-')else'synthesis'if so['id']in['drip','poststir','calcine']else'workup'if isroute else'characterization'
  convert=lambda mid:sol if mid=='selected-alcohol'else sol+'-nitrate-stock'if mid=='selected-nitrate-stock'else sol+'-tea-stock'if mid=='selected-tea-stock'else mid
  sourceins=[convert(i)for i in so['inputs']];ins=[]
  for mid in sourceins:
   if mid in MM:ins.append(addm(r,mid,stage))
   elif mid in outmap:ins.append(outmap[mid])
   elif mid in knownstocks:ins.append(mid)
   else:
    if not any(s['id']==mid for s in r['material_states']):r['material_states'].append(state(mid,'Separate source specimen/context: '+mid.replace('-',' '),[], 'sample_set'))
    ins.append(mid)
  for extra in(['air']if so['id']=='tga-acquire'else['nitrogen-bet']if so['id']=='bet-acquire'else['pipet']if so['id']=='packing-acquire'else[]):ins.append(addm(r,extra,stage))
  outs=[]
  for out0 in so['outputs']:
   out=convert(out0);out=out+'-prepared-state'if out in knownstocks else out;outs.append(out)
   kind='analysis_data'if out.endswith('-data')else'mixture'if isroute else'sample_set'
   r['material_states'].append(state(out,('Separate specimens: 'if kind=='sample_set'else'Analysis result: 'if kind=='analysis_data'else'')+out.replace('-',' '),[x for x in ins if x not in SUPPORT],kind))
  desc=so['action']+'. '+so['quantity_scope_note']+' Missing fields: '+', '.join(so['missing_fields'])+'.'
  if isroute:desc+=' This record uses only '+MM[sol]['name']+' for both stock solutions and the alcohol wash. No other alcohol is mixed into this route.'
  else:desc+=' Inputs identify separate specimens or contexts; they are not pooled.'
  if so['id']=='diagnostic':desc+=' Only a 10 mL filtrate aliquot enters the NH4OH diagnostic; the retained precipitate stays on the separate main branch. No explicit diagnostic result is supplied.'
  if so['id']=='calcine':desc+=' Apply independently to each solvent-derived preparation; atmosphere is unreported and must not inherit TGA air.'
  env='Room temperature; numerical temperature not reported'if so['id']in['drip','poststir','ambient-dry']else'Air (TGA only)'if so['id']=='tga-acquire'else None
  if so['retained_fraction']:desc+=' Source retained-fraction wording: '+so['retained_fraction']+'.'
  retained={'filter':'precipitate','alcohol-wash':'washed-precipitate','acetone-wash':'as-prepared-powder','diagnostic':'diagnostic-mixture'}.get(so['id'],so['retained_fraction'])
  oo=operation(so['id'],norm(so['action']),so['action'],E(so['evidence']),ins,outs,depends=list(dict.fromkeys(produced[i]for i in sourceins if i in produced)),stage=stage,branch=sol or'separate_source_contexts',description=desc,environment=fact(env,E(so['evidence'])),retained_fraction=retained)
  for qv in so['quantities']:
   pk=key(qv['meaning']);oo['parameters'][pk]=Q(qv,sol or pr['id']);OP_SCOPE.append({'record_id':r['record_id'],'operation_id':so['id'],'meaning':qv['meaning'],'raw_text':qv['raw_text'],'placement':'source_operation_parameter'})
   for fid in so['source_fact_ids']:
    for iq,oq in enumerate(FM[fid]['quantities']):
     if oq==qv:link('fact',fid,r,f'/operations/{j}/parameters/'+esc(pk),'/quantities/'+str(iq))
  r['operations'].append(oo);unit('protocols',pr['id'],r,f'/operations/{j}');unit('operation',so['id'],r,f'/operations/{j}');OPMAP.setdefault(so['id'],[]).append({'record_id':r['record_id'],'pointer':f'/operations/{j}'})
  for old,new in zip([convert(x)for x in so['outputs']],outs):produced[old]=so['id'];outmap[old]=new
  r['quality']['missing_fields']+=so['missing_fields']
for sol in['ethanol','propanol','butanol']:buildops(R[sol+'-route'],PP['precipitation-family'],sol,skip=['diagnostic'])
buildops(R['filtrate-diagnostic'],PP['precipitation-family'],only=['diagnostic'])
for pid,pr in PP.items():
 if pid!='precipitation-family':buildops(R[pid],pr)
def scowner(sc):
 sid=sc['id']
 if sid.endswith('-as-prepared')and sid.split('-')[0]in['ethanol','propanol','butanol']:return sid.split('-')[0]+'-route'
 if sid in['ethanol-calcined','propanol-calcined','butanol-calcined']:return'calcination'
 if sid.endswith('-solution-dls'):return'dls'
 if sid.startswith('xrd-'):return'xrd'
 if sid=='butanol-tga':return'tga'
 if'dsc'in sid:return'dsc'
 if sid=='packing-powder':return'packing'
 if sid.startswith('xps-'):return'xps-fit'if sid=='xps-fit-context'else'xps'
 return'mechanistic-context'
for sc in D['sample_contexts']:
 r=R[scowner(sc)];sid=sample(r,sc['id'],sc['evidence']);j=next(i for i,p in enumerate(r['products'])if p['sample_id']==sid);p=r['products'][j]
 p['notes']+=[sc.get('lineage_note',''),sc['cross_technique_physical_batch_join']]
 if sc['id'].endswith('-as-prepared')and r['record_type']=='literature_protocol':p.update(recipe_link='explicit',link_evidence=E(sc['evidence']),material_state_id='as-prepared-powder');p['composition']=fact(None,E(sc['evidence']),note='Whole as-prepared composition unresolved; local CeO2 microscopy is not a bulk purity label.')
 if sc['reported_whole_composition']:p['composition']=fact('CeO2',E(sc['evidence']),note='Source calcined-phase purity claim; not a new elemental analysis.');p['phase']=fact('cubic',E(sc['evidence']),note='Source-reported calcined phase.');p['parent_sample_id']=None;p['notes'].append('Corresponding solvent preparation is source-linked, but exact physical-batch identity across techniques is unknown.')
 unit('sample_contexts',sc['id'],r,f'/products/{j}')
for fid,f in FM.items():
 owners=[OWN[fid]]
 if OWN[fid]=='ethanol-route':owners=['ethanol-route','propanol-route','butanol-route']
 for owner in owners:
  r=R[owner];sid=sample(r,f['sample_scope'],f['evidence']);note='Source claim class: '+f['claim_class']+'. '+cn(f['conflict_ids']+f['gap_ids'])
  r['measurements'].append(measurement(fid+'-claim',sid,'source_claim',fact(f['claim'],E(f['evidence']),note=note),'Source process/observation/model/cited context',E(f['evidence']),conditions=f['sample_scope']));ptr=f'/measurements/{len(r["measurements"])-1}/value';link('fact',fid,r,ptr,'/claim');unit('facts',fid,r,ptr)
  for iq,qv in enumerate(f['quantities']):
   r['measurements'].append(measurement(fid+'-q'+str(iq+1),sid,key(qv['meaning']),Q(qv,f['sample_scope'],note),'Reported source quantity with stated scope',E(qv['evidence']),conditions=f['sample_scope']));ptr=f'/measurements/{len(r["measurements"])-1}/value';link('fact',fid,r,ptr,'/quantities/'+str(iq));unit('facts',fid,r,ptr)
  r['quality']['conflicts']+=[cn([i])for i in f['conflict_ids']]
for tab in T['tables']:
 r=R['xps-fit'];sid=sample(r,'xps-fit-context',tab['evidence']);meta={k:deepcopy(v)for k,v in tab.items()if k!='rows'};es=E(tab['evidence'])
 r['measurements'].append(measurement(tab['id']+'-definition',sid,'source_table_definition',fact(compact(meta),es,note='Literal printed headings, 36 raw grid cells and inconsistent spin/specimen labels retained; no repaired fit or fractions.'),'Original table definition',es));ptr=f'/measurements/{len(r["measurements"])-1}/value';unit('table',tab['id'],r,ptr);TABLEMETA.append({'table_id':tab['id'],'record_id':r['record_id'],'pointer':ptr})
 for ri,row in enumerate(tab['rows']):
  for ci,c in enumerate(row['cells']):
   cid=row['id']+'-'+c['column'];r['measurements'].append(measurement(cid,sid,c['column'],Q(c,'xps-fit-context',row['source_group_header']+' '+row['peak_label']+' '+row['oxidation_assignment_as_printed']+' as printed. No unambiguous unique physical specimen assigned from conflicting labels.'),'Source XPS fitted peak',E(c['evidence'])));ptr=f'/measurements/{len(r["measurements"])-1}/value';link('table_cell',cid,r,ptr);unit('table',tab['id'],r,ptr);unit('table_row',row['id'],r,ptr)
FIGOWNER={'figure-1':'structure-results','figure-2':'xrd','figure-3':'property-results','figure-s1':'xps-fit'};EQOWNER={x['id']:('mechanistic-context'if x['id']=='reaction'else'xps-fit')for x in D['equations']}
# Preserve every remaining source unit as an explicit context payload, without inventing observations.
for uid,u in UU.items():
 if UL[uid]:continue
 obj=resolve(PAY[u['payload_path']],u['json_pointer']);kind=u['kind'];owner=FIGOWNER[obj['id']]if kind=='figures'else EQOWNER[obj['id']]if kind=='equations'else FIGOWNER[D['figures'][int(u['json_pointer'].split('/')[2])]['id']]if kind=='figure_panel'else'source-context'
 r=R[owner];es=u['evidence']or D['facts'][0]['evidence'];sid=sample(r,'source unit '+uid,es);r['measurements'].append(measurement(uid,sid,'source_'+kind,fact(compact(obj),E(es),note='Exact source-unit payload retained for scope and completeness; historical author-status fields are not the current independent-audit decision.'),'Source inventory context',E(es)));unit(kind,obj.get('id',obj.get('label')),r,f'/measurements/{len(r["measurements"])-1}/value')if kind not in['figure_panel','reference_gap']else link('unit',uid,r,f'/measurements/{len(r["measurements"])-1}/value')
for r in R.values():
 r['quality']['missing_fields']=list(dict.fromkeys(r['quality']['missing_fields']));r['quality']['conflicts']=list(dict.fromkeys(r['quality']['conflicts']));r['context_links']=[{'label':'Complete source reader and limitations','url':'/paper-review.html?id='+SID,'relation':'private_unapproved_reader'}]
 if r['record_type']=='literature_protocol':r['context_links']+=[{'label':'Separate filtrate diagnostic','url':'/records/'+PRE+'filtrate-diagnostic.html','relation':'separate_branch'},{'label':'Post-synthesis calcination','url':'/records/'+PRE+'calcination.html','relation':'separate_post_treatment'}]
errors=[e for r in R.values()for e in validate_record(r)];assert not errors,errors[:30]
assert all(FL.values())and all(UL.values())and len(TL)==20
assert len(set(build_groups(list(R.values())).values()))==1
assert not any(v['eligible']for r in R.values()for v in eligibility(r).values())
records=[]
for r in R.values():
 n=r['record_id']+'.json';save(n,r);records.append({'record_id':r['record_id'],'path':str(O/n),'sha256':sha(O/n),'record_type':r['record_type']})
save('source-to-field-coverage.json',{'source_freeze_sha256':sha(P/'package-freeze.json'),'facts':[{'source_fact_id':i,'canonical_bindings':b}for i,b in FL.items()],'source_units':[{'source_unit_id':i,'canonical_bindings':b}for i,b in UL.items()],'table_cells':[{'source_cell_id':i,'canonical_bindings':b}for i,b in TL.items()],'table_definitions':TABLEMETA,'source_objects':OBJECTS,'operation_instances':OPMAP})
save('lossless-source-map.json',{'private_only':True,'source_freeze_sha256':sha(P/'package-freeze.json'),'source_facts':D,'source_tables':T,'source_inventory':I})
save('source-owner-map.json',{'fact_owner':OWN,'figure_owner':FIGOWNER,'equation_owner':EQOWNER,'table_owner':{'table-s1':'xps-fit'},'sample_owner':{s['id']:scowner(s)for s in D['sample_contexts']},'authors':D['authors']})
save('operation-quantity-scope.json',{'entries':OP_SCOPE,'distinct_source_operations':19,'canonical_operation_instances':35,'note':'Three explicitly reported alcohol alternatives expand eight main-branch stages each. Diagnostic, calcination and analytical contexts are kept separate.'})
BY={r['record_id']:r for r in R.values()};checks=[]
def ck(n,ok):checks.append({'check':n,'passed':bool(ok)});assert ok,n
def vok(src,dst):
 if src['status']in TEXT_STATUSES:return dst['value']==src['raw_text']
 cmp=src.get('comparison')
 if cmp in['<','<=']:ok=dst['maximum']==src['value']and dst.get('maximum_exclusive')==(cmp=='<')
 elif cmp in['>','>=']:ok=dst['minimum']==src['value']and dst.get('minimum_exclusive')==(cmp=='>')
 elif src.get('range'):ok=dst['minimum']==src['range']['min']and dst['maximum']==src['range']['max']
 else:ok=dst['value']==src['value']
 return ok and dst['raw_text']==src['raw_text']and dst['unit']==(src['unit']or'')and dst['approximate']==src['approximate']
for fid,bs in FL.items():
 for b in bs:
  dst=resolve(BY[b['record_id']],b['pointer']);src=resolve(FM[fid],b['source_pointer']);ck(fid+' '+b['pointer'],dst['value']==src if b['source_pointer']=='/claim'else vok(src,dst))
for row in T['tables'][0]['rows']:
 for cell in row['cells']:
  b=TL[row['id']+'-'+cell['column']][0];ck(row['id']+cell['column'],vok(cell,resolve(BY[b['record_id']],b['pointer'])))
for uid,bs in UL.items():
 for b in bs:ck(uid+' '+b['pointer'],resolve(BY[b['record_id']],b['pointer'])is not None)
for p,h in FR['bound_files'].items():ck('Frozen source unchanged '+p,sha(p)==h)
ck('35 operation instances /19 source operations',sum(len(r['operations'])for r in R.values())==35 and len(OPMAP)==19)
ck('No tasks or structures or promotion',all(not r['quality']['requested_tasks']and not r['structure_assets']and'collection'not in r for r in R.values()))
for sol in['ethanol','propanol','butanol']:
 r=R[sol+'-route'];ck(sol+' route has only its selected alcohol',set(m['id']for m in r['materials'])&{'ethanol','propanol','butanol'}=={sol});ck(sol+' no NH4OH on route',not any(m['id']=='ammonium-hydroxide'for m in r['materials']));ck(sol+' no pure as-prepared composition',all(p['composition']['value']is None for p in r['products']))
counts={'records':len(R),'record_types':{k:sum(r['record_type']==k for r in R.values())for k in['literature_protocol','procedure','observation']},'operations':sum(len(r['operations'])for r in R.values()),'distinct_source_operations':len(OPMAP),'material_slots':sum(len(r['materials'])for r in R.values()),'stock_slots':sum(len(r['stocks'])for r in R.values()),'stock_component_slots':sum(len(s['components'])for r in R.values()for s in r['stocks']),'sample_context_slots':sum(len(r['products'])for r in R.values()),'measurements':sum(len(r['measurements'])for r in R.values()),'source_facts':len(FL),'source_fact_bindings':sum(map(len,FL.values())),'source_units':len(UL),'source_unit_bindings':sum(map(len,UL.values())),'source_table_cells':len(TL),'source_groups':1,'eligible_training_rows':0,'atomic_structure_assets':0}
save('author-validation.json',{'status':'author_schema_semantic_transport_checks_passed','author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'checks':checks,'check_count':len(checks),'counts':counts,'schema_errors':errors,'independent_source_audit':'passed','independent_canonical_audit':'pending','site_written':False})
save('record-manifest.json',{'schema':'mattersyn-private-canonical-proposal/1','source_id':SID,'version':1,'author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'status':'private_unapproved_author_proposal','independent_source_audit_path':str(AP),'independent_source_audit_sha256':sha(AP),'source_freeze_sha256':sha(P/'package-freeze.json'),'records':records,'counts':counts,'coverage_sha256':sha(O/'source-to-field-coverage.json'),'validation_sha256':sha(O/'author-validation.json'),'input_modules':{str(S/'scripts'/n):sha(S/'scripts'/n)for n in['dataset_lib.py','record_helpers.py','schema_definition.py']},'author_script_sha256':sha(__file__)})
print(json.dumps(counts));print('MANIFEST',sha(O/'record-manifest.json'))
