"""Private Sommer canonical authoring. Frozen extraction and Site are read-only."""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import json,hashlib,re,sys
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;O=P/'canonical-proposal/v1';O.mkdir(parents=True,exist_ok=True)
assert not(O/'package-manifest.json').exists(),'Use a preserved new revision after freeze.'
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
D=read(P/'source-facts.json');I=read(P/'source-inventory.json');T=read(P/'source-tables.json');FR=read(P/'package-freeze.json');SID='sommer2020';PRE='sommer-2020-'
for p,h in FR['bound_files'].items():assert sha(p)==h,p
AP=P/'source-independent-audit/independent-audit.json';AU=read(AP)if AP.exists()else None
SOURCE_PASSED=bool(AU and AU.get('status')=='passed'and not AU.get('open_findings')and any(v==sha(P/'package-freeze.json')for v in AU.values()if isinstance(v,str)))
if SOURCE_PASSED:
 for p,h in AU['bound_files'].items():assert sha(p)==h,p
AUDIT_NOTE=('The complete supplied 11-page main extraction passed distinct source audit. Declared SI remains locally unlocated/unverified. 'if SOURCE_PASSED else'The supplied-main extraction is frozen but distinct source audit is pending. Declared SI remains locally unlocated/unverified. ')+ 'Canonical/reader independent review remains pending; this is an unapproved private author draft. Historical pending flags in immutable source payloads refer to their author-freeze time.'
FM={f['id']:f for f in D['facts']};MM={m['id']:m for m in D['materials']};PP={p['id']:p for p in D['protocols']};UM={(u['kind'],u['source_object_id']):u['id']for u in I['inventory_units']};UU={u['id']:u for u in I['inventory_units']};CON={x['id']:x for x in D['conflicts']};GAP={x['id']:x for x in D['missingness']}
R={};FL={i:[]for i in FM};UL={i:[]for i in UU};TL={};OBJECTS=[];TABLEMETA=[];OP_SCOPE=[]
def E(es):return[{'source_id':SID,'locator':e['document_role'].upper()+' PDF p. '+str(e['pdf_page'])+' (printed '+str(e['printed_page'])+'), '+e['locator']+'; source SHA256 '+e['source_sha256']}for e in es]
def FE(i):return E(FM[SID+'-'+i]['evidence'])
def cn(ids):return' '.join(i+': '+(CON[i]['description']if i in CON else GAP[i]['description'])for i in ids if i in CON or i in GAP)
def link(cat,sid,r,ptr,sp=None):
 b={'record_id':r['record_id'],'pointer':ptr}
 if sp is not None:b['source_pointer']=sp
 if cat=='fact':FL[sid].append(b)
 elif cat=='unit':UL[sid].append(b)
 elif cat=='table_cell':TL.setdefault(sid,[]).append(b)
 else:OBJECTS.append({'category':cat,'source_id':sid,**b})
def unit(kind,sid,r,p):link('unit',UM[(kind,sid)],r,p)
SRC=source(SID,D['doi'],D['title'],'; '.join(D['authors']),2020,si='Declared on main p.9, locally unlocated and unverified. No SI content is claimed read.')
SRC['main_status']='All 11 supplied main pages read and visually inspected by extraction author. '+AUDIT_NOTE
SRC['reuse_status']='Selected original crops are private proposals. Complete PDFs/text/page images remain local. No public import or browser approval is implied.'
COMMON=[AUDIT_NOTE,'Record IDs and context counts do not count independent physical batches or replicates.','No atomic model, exact recipe–structure pair, universal cross-technique sample join or training admission is approved.','Pure process specifications and author refinement/model results are distinguished from experimental product observations.']
CONFIG={p['id']:(p['title'],'literature_protocol'if p['kind']=='synthesis'else'procedure')for p in D['protocols']}
CONFIG.update({
'precursor-structures':('Precursor-solution PDF interpretations','observation'),
'formation-model':('Nucleation, impurity and defect interpretations','observation'),
'phase-size-results':('Sample-specific phase and size results','observation'),
'optical-results':('Sample-specific optical comparison and cited ranges','observation'),
'condition-matrix':('Complete Table 1 condition matrix','observation'),
'source-materials':('Source-qualified material identities','observation'),
'source-context':('Bibliography, conflicts and source limitations','observation')})
for pid,(title,kind)in CONFIG.items():
 formula='ZnAl2O4'if pid not in['source-materials','source-context','precursor-structures']else'Zn-Al precursor context'if pid=='precursor-structures'else'Study materials'if pid=='source-materials'else'Study source context'
 r=record(PRE+pid,'Sommer et al. (2020) · '+title,formula,'ZnAl2O4 spinel hydrothermal synthesis',title,deepcopy(SRC),'Complete supplied-main source scope with exact locators',kind);r['schema_version']='1.3.0'
 r['lineage'].update(source_group=SID,recipe_family=SID+'-hydrothermal-reactor-study')
 r['quality'].update(review_status='imported_unreviewed',review_scope=AUDIT_NOTE,requested_tasks=[],experimental_outcome='not_established',missing_fields=COMMON.copy(),conflicts=[])
 r['intended_target']['composition']=fact('ZnAl2O4'if kind=='literature_protocol'else None,FE('scope'),note='Nominal target only for the three laboratory route records. Procedure/model/context records do not create a new synthesis outcome.')
 R[pid]=r
OWNER_GROUPS={
'mw-route':['mw-stock','mw-base','mw-vessel','mw-profile-1','mw-profile-2','mw-pressure'],
'scf-route':['scf-settings'],'acs-route':['acs-settings','acs-ramp-assumption'],'lab-workup':['workup'],
'insitu-nitrate':['insitu-nitrate-stock','insitu-mix','insitu-load','insitu-acquisition'],
'insitu-oxide':['insitu-oxide-stock'],'insitu-refinement':['insitu-defects','insitu-minor-phase'],
'lab-xrd-procedure':['lab-xrd','lab-fit'],'synchrotron-procedure':['synchrotron-xrd','synchrotron-fit'],
'pdf-procedure':['pdf-acquisition','pdf-fit'],'microscopy-procedure':['tem-prep','tem-acquire'],
'optical-procedure':['uvvis-acquire','uvvis-transform'],
'precursor-structures':['d3-peaks','d3-fit','d3-solution','d4-solution','d2-pdf','d2-size'],
'formation-model':['structures-background','inversion-background','formation-model','conclusion-coordination','ratio-not-ph','heating-background','cited-zno-heating'],
'phase-size-results':['insitu-middle','insitu-lowbase','insitu-highbase','insitu-nobase','insitu-oxide-outcome','insitu-sizes','mw-lowbase-outcome','mw-highbase-outcome','mw-middle-outcome','mw-time-outcome','mw-heating-outcome','scf-outcome','acs-outcome','phasepure-size','acs-bimodal-size','tem-morphology','conclusion-range','figure11-display','insitu-i7-i8-scope'],
'optical-results':['optical-outcome','optical-literature'],
'source-materials':['reagents'],'source-context':['identity','scope','si-availability']}
OWN={SID+'-'+fid:owner for owner,fids in OWNER_GROUPS.items()for fid in fids};assert set(OWN)==set(FM),(set(FM)-set(OWN),set(OWN)-set(FM))
def Q(qv,scope='',extra=''):
 es=E(qv['evidence']);note=(extra+' '+cn(qv.get('conflict_ids',[])+qv.get('gap_ids',[]))).strip();basis='Source context: '+scope+'.'
 if qv.get('uncertainty')is not None:note+=' Reported parenthetic uncertainty '+str(qv['uncertainty'])+' '+str(qv.get('unit'))+'; '+qv.get('uncertainty_definition','definition not stated')+'.'
 if qv['status']in['reported_text','reported_identifier','reported_ratio_parts','original_image']:
  return fact(qv['raw_text'],es,note=basis+' '+note+' Source ratio components: '+compact(qv.get('components'))+'. No numerical unit or endpoint is inferred for text-only fields.')
 v=qv['value'];lo=(qv.get('range')or{}).get('min');hi=(qv.get('range')or{}).get('max');cmp=qv.get('comparison')
 if cmp in['<','<=']:hi=v;v=None
 if cmp in['>','>=']:lo=v;v=None
 return qty(v,qv.get('unit')or'',es,'reported'if v is not None or lo is not None or hi is not None else'not_reported',minimum=lo,maximum=hi,approximate=qv.get('approximate',False),qualifier=note,basis=basis,raw_text=qv['raw_text'],minimum_exclusive=cmp=='>'if cmp in['>','>=']else None,maximum_exclusive=cmp=='<'if cmp in['<','<=']else None)
def sample(r,scope,es,formula=None):
 sid=norm(scope)
 if not any(p['sample_id']==sid for p in r['products']):
  p=product(sid,formula,E(es),link='general_context',notes=['Source scope: '+scope+'.','This is a named source specimen or context, not proof of a unique batch, all-technique same-aliquot identity or independent outcome.','No measured atomic structure or exact recipe–structure pair is approved.']);p['source_sample_label']=scope;r['products'].append(p);link('sample_context',scope,r,f'/products/{len(r["products"])-1}')
 return sid
def addm(r,mid,stage='characterization'):
 if any(m['id']==mid for m in r['materials']):return mid
 m=MM[mid];r['materials'].append(material(mid,m['name'],m['source_formula_or_abbreviation'],m['role'],stage,E(m['evidence']),notes=[m['scope_note'],'Chemical identity and source role only; independently qualified molecular/component bindings remain pending.']));ptr=f'/materials/{len(r["materials"])-1}';unit('material',mid,r,ptr);link('material',mid,r,ptr);return mid
for mid in MM:addm(R['source-materials'],mid)
STOCK_OWNER={s['id']:'mw-route'if s['id'].startswith('mw-')else'insitu-oxide'if s['id']=='insitu-oxide-slurry'else'insitu-nitrate'for s in D['stocks']}
STOCK_PREP={'mw-nitrate-stock':'mw-dissolve','mw-low-base':'mw-base','mw-middle-base':'mw-base','mw-high-base':'mw-base','insitu-nitrate-stock':'insitu-stock','insitu-base-solutions':None,'insitu-oxide-slurry':'oxide-slurry'}
COMPONENT_Q={'mw-nitrate-stock':{'zn-nitrate':['Zn(NO3)2·6H2O mass'],'al-nitrate':['Al(NO3)3·9H2O mass'],'demin-feed-water':['demineralized water charge']},'insitu-nitrate-stock':{'zn-nitrate':['Zn(NO3)2·6H2O mass'],'al-nitrate':['Al(NO3)3·9H2O mass']},'insitu-oxide-slurry':{'zno-feed':['ZnO mass'],'aloh3':['Al(OH)3 mass']}}
for st in D['stocks']:
 r=R[STOCK_OWNER[st['id']]];nested=st['id']in['mw-low-base','mw-middle-base','mw-high-base'];ids=['zn-nitrate','al-nitrate','demin-feed-water','naoh']if nested else st['components'];components=[]
 for mid in ids:
  co={'material_id':addm(r,mid,'precursor_preparation'),'quantities':{}}
  for qv in st['quantities']:
   if qv['meaning']in COMPONENT_Q.get(st['id'],{}).get(mid,[]):co['quantities'][key(qv['meaning'])]=Q(qv,st['id'])
  components.append(co)
 cq={}
 for qv in st['quantities']:
  if qv['unit']=='M' and(st['id']!='insitu-base-solutions'):cq[key(qv['meaning'])]=Q(qv,st['id'])
 scope=st['sample_scope']+'. '+st['notes']
 scope=scope.replace('retained in sommer2020-insitu-mix and the insitu-mix operation.','recorded with the separate mixing step.')
 if nested:scope+=' These constituents belong to the already prepared mixed-nitrate stock. They do not represent fresh nitrate/water charges; only the source-specific final NaOH concentration is assigned here.'
 if st['id']=='insitu-base-solutions':scope+=' The source fact also describes postmix metal concentrations and aliquot volumes; these do not become NaOH-stock concentrations.'
 stock={'id':st['id'],'name':st['name'],'components':components,'concentrations':cq,'preparation_operation_ids':[STOCK_PREP[st['id']]]if STOCK_PREP[st['id']]else[],'scope':scope,'evidence':E(st['evidence'])};r['stocks'].append(stock);ptr=f'/stocks/{len(r["stocks"])-1}';unit('stock',st['id'],r,ptr);link('stock',st['id'],r,ptr)
STAGE={'mw-dissolve':'precursor_preparation','mw-base':'precursor_preparation','mw-load':'precursor_preparation','mw-heat':'synthesis','scf-feed':'precursor_preparation','scf-react':'synthesis','acs-load':'precursor_preparation','acs-heat':'synthesis','lab-separate':'workup','lab-wash':'workup','lab-dry':'workup','insitu-stock':'precursor_preparation','insitu-mix':'precursor_preparation','insitu-stir-load':'precursor_preparation','insitu-heat':'synthesis','oxide-slurry':'precursor_preparation','oxide-load':'precursor_preparation','oxide-heat':'synthesis'}
OUTCOME_ONLY={'oxide-heat':{'I15 temperature','I16 temperature'},'mw-base':set(),'mw-heat':{'reported approximate pressure interval'},'insitu-heat':set(),'acs-heat':{'set point','assumed time to set point'},'scf-react':{'pressure'},'pdf-solutions':set()}
SUPPORTS={m['id']for m in D['materials']if m['role']in['apparatus','support','measurement_reference']}
EXTERNAL_NAMES={'mw-formulations':'Separate laboratory NaOH-adjusted formulations from the microwave preparation','mw-crude':'Microwave crude products, separate specimens','scf-crude':'SCF crude products, separate specimens','acs-crude':'Autoclave crude products, separate specimens','insitu-nitrate-series':'Separate nitrate-based in situ experiment observations','insitu-oxide-series':'Separate oxide-feed in situ experiment observations','dried-lab-powders':'Separately isolated laboratory powders; not pooled samples'}
ANALYSIS={'insitu-analysis-data','total-scattering-data','precursor-analysis-data','lab-diffraction','lab-refinement-data','synchrotron-data','synchrotron-refinement-data','microscopy-data','reflectance-data','optical-analysis-data'}
SINGLE_MIX={'mw-nitrate-stock','insitu-nitrate-stock','insitu-oxide-slurry'}
for pid,pr in PP.items():
 r=R[pid];produced={};outmap={};knownstocks={s['id']for s in r['stocks']}
 for j,so in enumerate(pr['operations']):
  stage=STAGE.get(so['id'],'characterization');ins=[]
  for mid in so['inputs']:
   if mid in MM:ins.append(addm(r,mid,stage))
   elif mid in outmap:ins.append(outmap[mid])
   elif mid in knownstocks:ins.append(mid)
   else:
    assert mid in EXTERNAL_NAMES,(pid,mid)
    if not any(s['id']==mid for s in r['material_states']):r['material_states'].append(state(mid,EXTERNAL_NAMES[mid],[],'sample_set'))
    ins.append(mid)
  outs=[]
  for out in so['outputs']:
   mapped=out+'-prepared-state'if out in knownstocks else out;outs.append(mapped)
   kind='analysis_data'if out in ANALYSIS else'waste'if out in['supernatant','wash-supernatants']else'mixture'if out in SINGLE_MIX else'sample_set'
   parents=[m for m in ins if m not in SUPPORTS]
   if out in['retained-lab-powder','washed-powder','dried-lab-powders']:parents=[m for m in parents if m not in['demin-wash-water','ethanol-96']]
   title=out.replace('-',' ')
   if kind=='sample_set':title='Separate source specimens: '+title
   r['material_states'].append(state(mapped,title,parents,kind))
  desc=so['action']+'. '+so.get('condition_scope_note','')+' '+so['quantity_scope_note']+' Missing fields: '+(', '.join(so['missing_fields'])or'none additionally identified')+'.'
  if len(pr['sample_ids'])>1:desc+=' The operation applies separately to the listed source contexts and does not combine different experiments into one physical batch.'
  if pid=='lab-workup':desc+=' Microwave, SCF and autoclave powders are alternative inputs from their respective routes, not a pooled charge.'
  if so['id']=='scf-feed':desc+=' The main gives flow rates and ratios; it does not supply a fully quantified upstream feed recipe.'
  env='ambient atmosphere during grid drying'if so['id']=='microscopy-deposit'else'vacuum; pressure unreported'if so['id']=='lab-dry'else None
  oo=operation(so['id'],norm(so['action']),so['action'],E(so['evidence']),ins,outs,depends=list(dict.fromkeys(produced[m]for m in so['inputs']if m in produced)),stage=stage,branch='source_contexts_applied_separately',description=desc,environment=fact(env,E(so['evidence'])),retained_fraction=outmap.get(so['retained_fraction'],so['retained_fraction']))
  for qv in so['quantities']:
   keep=qv['meaning']in OUTCOME_ONLY[so['id']]if so['id']in OUTCOME_ONLY else True
   if so['id']=='oxide-slurry'and qv['meaning']=='ZnO nominal size':keep=False
   cq=Q(qv,pid);keep=keep and 'unit'in cq
   OP_SCOPE.append({'record_id':r['record_id'],'operation_id':so['id'],'quantity_meaning':qv['meaning'],'raw_text':qv['raw_text'],'placement':'operation_parameter_and_context_measurement'if keep else'context_measurement_or_condition_option_only','reason':'Only applicable action controls are stage parameters. Alternative profiles, sample-specific schedules, product outcomes, ratios and source text remain separately mapped.'})
   if keep:
    pk=key(qv['meaning']);oo['parameters'][pk]=cq
    for fid in so['source_fact_ids']:
     for iq,original in enumerate(FM[fid]['quantities']):
      if qv==original:link('fact',fid,r,f'/operations/{j}/parameters/'+esc(pk),'/quantities/'+str(iq))
  r['operations'].append(oo);unit('protocol',pid,r,f'/operations/{j}');unit('operation',so['id'],r,f'/operations/{j}');link('operation',so['id'],r,f'/operations/{j}');r['quality']['missing_fields']+=so['missing_fields']
  for old,new in zip(so['outputs'],outs):produced[old]=so['id'];outmap[old]=new
# Context-only supplied apparatus/material records never manufacture new products.
def qscope(qv,default):
 m=re.match(r'^(M\d+|S\d+|A\d+|I\d+(?:/I\d+)?|D\d+)\b',qv['meaning'])
 return m[1]if m else default
for fid,f in FM.items():
 r=R[OWN[fid]];sid=sample(r,f['sample_scope'],f['evidence']);note='Source claim class: '+f['claim_class']+'. '+cn(f['conflict_ids']+f['gap_ids'])
 r['measurements'].append(measurement(fid+'-claim',sid,'source_claim',fact(f['claim'],E(f['evidence']),note=note),'Source text: process, observation, model or cited context as labeled',E(f['evidence']),conditions=f['sample_scope']));ptr=f'/measurements/{len(r["measurements"])-1}/value';link('fact',fid,r,ptr,'/claim');unit('fact',fid,r,ptr)
 for iq,qv in enumerate(f['quantities']):
  scope=qscope(qv,f['sample_scope']);qs=sample(r,scope,qv['evidence'])
  r['measurements'].append(measurement(fid+'-q'+str(iq+1),qs,key(qv['meaning']),Q(qv,scope,note),'Reported source specification or result; scope retained',E(qv['evidence']),conditions=scope+'; '+qv['meaning']));ptr=f'/measurements/{len(r["measurements"])-1}/value';link('fact',fid,r,ptr,'/quantities/'+str(iq));unit('fact',fid,r,ptr)
 r['quality']['conflicts']+=[cn([x])for x in f['conflict_ids']]
def rowowner(sid):return'mw-route'if sid[0]=='M'else'scf-route'if sid[0]=='S'else'acs-route'if sid[0]=='A'else'insitu-oxide'if sid in['I15','I16']else'insitu-nitrate'if sid[0]=='I'else'pdf-procedure'
for tab in T['tables']:
 r=R['condition-matrix'];ss=sample(r,'Table 1 reported condition contexts',tab['evidence']);es=E(tab['evidence']);meta={k:deepcopy(v)for k,v in tab.items()if k!='rows'}
 r['measurements'].append(measurement(tab['id']+'-definition',ss,'source_table_definition',fact(compact(meta),es,note='Complete source table header/footnote/scope; this is a process/observation matrix, not 37 new outcome labels.'),'Original table definition',es));ptr=f'/measurements/{len(r["measurements"])-1}/value';unit('table',tab['id'],r,ptr);TABLEMETA.append({'table_id':tab['id'],'record_id':r['record_id'],'pointer':ptr})
 for ir,row in enumerate(tab['rows']):
  sid=sample(r,row['sample_id'],row['row_label_evidence']);rp=[]
  labelid=f'table-1-r{ir+1:02}-sample';r['measurements'].append(measurement(labelid,sid,'reported_sample_label',fact(row['row_label'],E(row['row_label_evidence'])),'Original table row label',E(row['row_label_evidence'])));ptr=f'/measurements/{len(r["measurements"])-1}/value';link('table_cell',labelid,r,ptr);unit('table_row',row['sample_id'],r,ptr);rp.append(ptr)
  for c in row['cells']:
   r['measurements'].append(measurement(c['id'],sid,key(c['column']),Q(c,row['sample_id'],'Table 1 process specification or acquisition context, not a new product-outcome measurement.'),'Original Table 1 condition cell',E(c['evidence']),conditions='Row '+row['row_label']+'; column '+c['column']));ptr=f'/measurements/{len(r["measurements"])-1}/value';link('table_cell',c['id'],r,ptr);unit('table',tab['id'],r,ptr);unit('table_row',row['sample_id'],r,ptr);rp.append(ptr)
  rr=R[rowowner(row['sample_id'])];es=E(row['row_label_evidence']);params={c['column']:Q(c,row['sample_id'])for c in row['cells']if c['column']!='Zn_Al_OH'and c['status']!='reported_text'}
  rr['condition_options'].append({'id':'table-1-'+row['sample_id'].lower(),'label':row['sample_id']+' · separately reported '+('total-scattering observation conditions; no heating recipe inferred'if row['sample_id'].startswith('D')else'conditions'),'parameters':params,'evidence':es});unit('table_row',row['sample_id'],rr,f'/condition_options/{len(rr["condition_options"])-1}')
  # Sample labels remain author labels, not newly assigned batch IDs.
  ps=sample(rr,row['sample_id'],row['row_label_evidence'],'ZnAl2O4'if row['sample_id'][0]in['M','S','A']else None);ip=next(i for i,p in enumerate(rr['products'])if p['sample_id']==ps)
  if row['sample_id'][0]in['M','S','A']:
   rr['products'][ip].update(recipe_link='explicit',link_evidence=es,material_state_id={'M':'mw-crude','S':'scf-crude','A':'acs-crude'}[row['sample_id'][0]])
   rr['products'][ip]['notes'].append('This row denotes its source-defined preparation specimen and nominal target, not phase purity, isolated yield or an exact atomic structure.')
 for ft in tab['footnotes']:
  r['measurements'].append(measurement(ft['id'],ss,'source_table_footnote',fact(ft['text'],E(ft['evidence'])),'Original table footnote',E(ft['evidence'])));unit('footnote',ft['id'],r,f'/measurements/{len(r["measurements"])-1}/value')
# Heating profiles are sequential controls within alternative named profiles, never one combined program.
for fid,label in [('mw-profile-1','Profile 1: M1-M3 and M7-M9'),('mw-profile-2','Profile 2: M4-M6')]:
 ff=FM[SID+'-'+fid];R['mw-route']['condition_options'].append({'id':fid,'label':label+'; Table 1 totals conflict and remain separate','parameters':{key(q['meaning']):Q(q,ff['sample_scope'],cn(['C1']))for q in ff['quantities']},'evidence':E(ff['evidence'])})
FIGOWNER={'graphical-abstract':'formation-model','figure-1':'formation-model','figure-2':'precursor-structures','figure-3':'precursor-structures','figure-4':'precursor-structures','figure-5':'formation-model','figure-6':'phase-size-results','figure-7':'phase-size-results','figure-8':'phase-size-results','figure-9':'phase-size-results','figure-10':'phase-size-results','figure-11':'phase-size-results','figure-12':'phase-size-results','figure-13':'optical-results'}
EQOWNER={'heating-profile-1':'mw-route','heating-profile-2':'mw-route','zn-hydrolysis':'precursor-structures','zn-dissolution':'precursor-structures','al-dimer':'precursor-structures','spinel-defects':'insitu-refinement','kubelka-munk':'optical-procedure'}
for kind,objs,owners in [('figure',D['figures'],FIGOWNER),('equation',D['equations'],EQOWNER)]:
 for obj in objs:
  r=R[owners[obj['id']]];scope='/'.join(obj.get('sample_ids',[]))or'author context';ss=sample(r,scope,obj['evidence']);txt=obj.get('title',obj.get('expression',''))+'. '+obj.get('notes',obj.get('interpretation_scope',''))+' '+cn(obj.get('conflict_ids',[])+obj.get('gap_ids',[]))
  r['measurements'].append(measurement(obj['id']+'-context',ss,kind+'_context',fact(txt,E(obj['evidence']),note='Source context/graphic only; no additional measured atomic structure.'),'Original '+kind,E(obj['evidence'])));unit(kind,obj['id'],r,f'/measurements/{len(r["measurements"])-1}/value')
for sc in D['sample_contexts']:
 owner=rowowner(sc['id'])if re.fullmatch(r'[MSAID]\d+',sc['id'])else'formation-model'if sc['id']in['formation-model','literature-structures']else'lab-xrd-procedure'if sc['id']=='laboratory-XRD'else'microscopy-procedure'if sc['id']=='microscopy'else'optical-results'if sc['id']=='literature-band-gap'else'source-context';r=R[owner];es=sc.get('evidence')or D['facts'][0]['evidence'];ss=sample(r,sc['id'],es);ip=next(i for i,p in enumerate(r['products'])if p['sample_id']==ss);r['products'][ip]['notes'].append('Source context object: '+compact(sc));unit('sample_context',sc['id'],r,f'/products/{ip}')
for kind,arr in [('reference',D['references']),('conflict',D['conflicts']),('gap',D['missingness'])]:
 for obj in arr:
  r=R['source-context'];es=obj.get('evidence')or D['facts'][0]['evidence'];ss=sample(r,'bibliographic context'if kind=='reference'else'source limitations',es);txt=obj['citation_as_extracted']if kind=='reference'else obj['description'];r['measurements'].append(measurement(obj['id'],ss,kind,fact(txt,E(es),note='Cited full text not independently read.'if kind=='reference'else'Unresolved source limitation retained without silent repair.'),'Source '+kind,E(es)));unit(kind,obj['id'],r,f'/measurements/{len(r["measurements"])-1}/value')
for r in R.values():
 r['quality']['missing_fields']=list(dict.fromkeys(r['quality']['missing_fields']));r['quality']['conflicts']=list(dict.fromkeys(r['quality']['conflicts']));r['context_links']=[{'label':'Full source reader and limitations','url':'/paper-review.html?id='+SID,'relation':'private_unapproved_reader_proposal'}]
 if r['record_type']=='literature_protocol':
  r['context_links'].append({'label':'Common powder isolation applied separately after this route','url':'/records/'+PRE+'lab-workup.html','relation':'source_reported_shared_workup'})
  r['quality']['review_scope']+=' The separately recorded common powder isolation applies after this route; operation IDs are not duplicated and different specimens are never pooled.'
 if r['record_id']==PRE+'acs-route':r['context_links'].append({'label':'Laboratory nitrate/base feed formulation shared with microwave preparation','url':'/records/'+PRE+'mw-route.html','relation':'source_reported_shared_feed_preparation'})
errors=[e for r in R.values()for e in validate_record(r)];assert not errors,errors[:50]
assert all(FL.values())and all(UL.values())and len(TL)==222
assert len(set(build_groups(list(R.values())).values()))==1
assert not any(v['eligible']for r in R.values()for v in eligibility(r).values())
records=[]
for r in R.values():
 n=r['record_id']+'.json';save(n,r);records.append({'record_id':r['record_id'],'path':str(O/n),'sha256':sha(O/n),'record_type':r['record_type']})
coverage={'schema':'mattersyn-private-field-coverage/1','source_freeze_sha256':sha(P/'package-freeze.json'),'facts':[{'source_fact_id':i,'canonical_bindings':b}for i,b in FL.items()],'source_units':[{'source_unit_id':i,'canonical_bindings':b}for i,b in UL.items()],'table_cells':[{'source_cell_id':i,'canonical_bindings':b}for i,b in TL.items()],'table_definitions':TABLEMETA,'source_objects':OBJECTS,'transport_scope':'All source claims, quantities, 222 Table 1 body cells (including 37 labels), and every inventory object have exact typed/pointer transport. Conditions/model calculations are not new independent outcome labels.'}
save('source-to-field-coverage.json',coverage);save('lossless-source-map.json',{'private_only':True,'source_freeze_sha256':sha(P/'package-freeze.json'),**deepcopy(D),'tables':deepcopy(T['tables'])});save('operation-quantity-scope.json',{'entries':OP_SCOPE,'notes':['Condition options retain Table 1 rows and both distinct microwave profiles.','SCF 450/380 conflict, ACS 17-day/2.5-week conflict and in situ time ranges remain explicit.','Shared laboratory workup is applied to separate powders, not pooling different reactor products.']})
checks=[];BY={r['record_id']:r for r in R.values()}
def ck(n,ok):checks.append({'check':n,'passed':bool(ok)});assert ok,n
def vok(src,dst):
 if src['status']in['reported_text','reported_identifier','reported_ratio_parts','original_image']:return dst['value']==src['raw_text']
 cmp=src.get('comparison')
 if cmp in['<','<=']:ok=dst['maximum']==src['value']and dst.get('maximum_exclusive')==(cmp=='<')
 elif cmp in['>','>=']:ok=dst['minimum']==src['value']and dst.get('minimum_exclusive')==(cmp=='>')
 elif src.get('range'):ok=dst['minimum']==src['range']['min']and dst['maximum']==src['range']['max']
 else:ok=dst['value']==src['value']
 return ok and dst['raw_text']==src['raw_text']and dst['approximate']==src['approximate']and dst['unit']==(src['unit']or'')and(src.get('uncertainty')is None or str(src['uncertainty'])in dst['qualifier'])
for fid,bs in FL.items():
 for b in bs:
  dst=resolve(BY[b['record_id']],b['pointer']);src=resolve(FM[fid],b['source_pointer']);ck(fid+' '+b['pointer'],dst['value']==src if b['source_pointer']=='/claim'else vok(src,dst))
for ir,row in enumerate(T['tables'][0]['rows']):
 labelid=f'table-1-r{ir+1:02}-sample';b=TL[labelid][0];ck(labelid,resolve(BY[b['record_id']],b['pointer'])['value']==row['row_label'])
 for c in row['cells']:
  b=TL[c['id']][0];ck(c['id'],vok(c,resolve(BY[b['record_id']],b['pointer'])))
for uid,bs in UL.items():
 for b in bs:ck(uid+' '+b['pointer'],resolve(BY[b['record_id']],b['pointer'])is not None)
for p,h in FR['bound_files'].items():ck('Source frozen file unchanged '+p,sha(p)==h)
ck('Exactly 31 source operations',sum(len(r['operations'])for r in R.values())==31)
ck('No tasks or models or promotion',all(not r['quality']['requested_tasks']and not r['structure_assets']and'collection'not in r for r in R.values()))
counts={'records':len(R),'record_types':{k:sum(r['record_type']==k for r in R.values())for k in['literature_protocol','procedure','observation']},'operations':sum(len(r['operations'])for r in R.values()),'material_slots':sum(len(r['materials'])for r in R.values()),'stock_slots':sum(len(r['stocks'])for r in R.values()),'stock_component_slots':sum(len(s['components'])for r in R.values()for s in r['stocks']),'condition_options':sum(len(r['condition_options'])for r in R.values()),'sample_context_slots':sum(len(r['products'])for r in R.values()),'measurements':sum(len(r['measurements'])for r in R.values()),'source_facts':len(FL),'source_fact_bindings':sum(map(len,FL.values())),'source_units':len(UL),'source_unit_bindings':sum(map(len,UL.values())),'source_table_cells':len(TL),'source_groups':1,'eligible_training_rows':0,'atomic_structure_assets':0}
save('author-validation.json',{'status':'author_schema_semantic_transport_checks_passed','author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'checks':checks,'check_count':len(checks),'counts':counts,'schema_errors':errors,'independent_source_audit':'passed'if SOURCE_PASSED else'pending','independent_canonical_audit':'pending','site_written':False,'training_exported':False})
save('record-manifest.json',{'schema':'mattersyn-private-canonical-proposal/1','source_id':SID,'version':1,'author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'status':'private_unapproved_author_proposal','independent_source_audit_path':str(AP)if SOURCE_PASSED else None,'independent_source_audit_sha256':sha(AP)if SOURCE_PASSED else None,'source_freeze_sha256':sha(P/'package-freeze.json'),'records':records,'counts':counts,'coverage_sha256':sha(O/'source-to-field-coverage.json'),'validation_sha256':sha(O/'author-validation.json'),'input_modules':{str(S/'scripts'/n):sha(S/'scripts'/n)for n in['dataset_lib.py','record_helpers.py','schema_definition.py']},'author_script_sha256':sha(__file__)})
print(json.dumps(counts));print('MANIFEST',sha(O/'record-manifest.json'))
