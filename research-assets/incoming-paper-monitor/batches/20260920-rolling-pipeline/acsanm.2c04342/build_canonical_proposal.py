"""Private Matuhina source-to-canonical authoring; sources and Site are read-only."""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import json,hashlib,re,sys
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;O=P/'canonical-proposal/v1';O.mkdir(parents=True,exist_ok=True)
assert not(O/'package-manifest.json').exists(),'Preserve frozen proposals; use a new revision.'
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
D=read(P/'source-facts.json');I=read(P/'source-inventory.json');T=read(P/'source-tables.json');FR=read(P/'package-freeze.json');SID='matuhina2023';PRE='matuhina-2023-'
for p,h in FR['bound_files'].items():assert sha(p)==h,p
AP=P/'source-independent-audit/independent-audit.json';AU=read(AP)if AP.exists()else None
SOURCE_PASSED=bool(AU and AU.get('status')=='passed'and not AU.get('open_findings')and sha(P/'package-freeze.json')in compact(AU))
if SOURCE_PASSED:
 for p,h in AU['bound_files'].items():assert sha(p)==h,p
AUDIT_NOTE=('The supplied 13-page main and 13-page SI extraction passed distinct source audit. 'if SOURCE_PASSED else'The supplied 13-page main and 13-page SI extraction is frozen; distinct source audit is pending. ')+'Canonical and reader independent review remain pending. Historical pending flags in immutable source payloads describe the author-freeze stage.'
AUTHORS=['Anastasia Matuhina','G. Krishnamurthy Grandhi','Fang Pan','Maning Liu','Harri Ali-Löytty','Hussein M. Ayedh','Antti Tukiainen','Jan-Henrik Smått','Ville Vähänissi','Hele Savin','Jingrui Li','Patrick Rinke','Paola Vivo']
FM={f['id']:f for f in D['facts']};MM={m['id']:m for m in D['materials']};PP={p['id']:p for p in D['protocols']};SC={s['id']:s for s in D['sample_contexts']};UM={(u['kind'],u['source_object_id']):u['id']for u in I['inventory_units']};UU={u['id']:u for u in I['inventory_units']};CON={x['id']:x for x in D['conflicts']};GAP={x['id']:x for x in D['missingness']}
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
SRC=source(SID,D['doi'],D['title'],'; '.join(AUTHORS),2023,si='Matched local 13-page SI; complete page reading and original-page visual inspection. '+AUDIT_NOTE)
SRC['main_status']='All 13 main pages read and visually inspected. '+AUDIT_NOTE
SRC['reuse_status']='Private factual extraction and selected original crop proposal; raw PDFs, complete text and whole-page scans remain local.'
COMMON=[AUDIT_NOTE,'Record and sample-context counts do not count independent physical batches.','Five source-defined preparation conditions are not a Cartesian grid; source loading ratios are not recalculated from unknown stock molarity.','No qualified atomic model, exact recipe–structure pair, same-aliquot cross-technique join or training admission is approved.']
CONFIG={p['id']:(p['title'],'literature_protocol'if p['id']=='hot-injection-series'else'procedure')for p in D['protocols']}
CONFIG.update({'structure-results':('Phase, composition and morphology observations','observation'),'optical-results':('Luminescence and transient-absorption observations','observation'),'stability-results':('Separate stored-film and dispersion observations','observation'),'device-results':('Unencapsulated-film photocurrent proof of concept','observation'),'mechanistic-context':('Source interpretations and cited comparisons','observation'),'source-materials':('Source-qualified material identities','observation'),'source-context':('Bibliography and unresolved source limitations','observation')})
for pid,(title,kind)in CONFIG.items():
 formula='Study materials'if pid=='source-materials'else'Study source context'if pid=='source-context'else'Cs-oleate stock'if pid=='cs-oleate-preparation'else'CsMnCl3'
 r=record(PRE+pid,'Matuhina et al. (2023) · '+title,formula,'CsMnCl3 nanocrystal phase and luminescence',title,deepcopy(SRC),'Complete supplied main and SI with exact source locators',kind);r['schema_version']='1.3.0';r['lineage'].update(source_group=SID,recipe_family=SID+'-hot-injection-study')
 r['quality'].update(review_status='imported_unreviewed',review_scope=AUDIT_NOTE,requested_tasks=[],experimental_outcome='not_established',missing_fields=COMMON.copy(),conflicts=[])
 r['intended_target']['composition']=fact('CsMnCl3'if kind=='literature_protocol'else None,FE('identity'),note='Intended synthesis target only. Other records retain preparation, analytical, control, model or source context.')
 R[pid]=r
OWNER_GROUPS={
'cs-oleate-preparation':['cs-charge','cs-degas','cs-oa','cs-store'],
'hot-injection-series':['mn-charge','mn-degas','inject','variant-map','quench','temperature-outcome'],
'primary-isolation':['isolate','dry-redisperse'],'purification-trials':['centrifuge-trial','antisolvent-trial','meoac-trial'],'unisolated-control':['unisolated'],
'xrd-procedure':['xrd-prep','xrd-acquire','xrd-ambient'],'tem-procedure':['tem'],'optical-procedure':['optical-acquisition'],'ta-procedure':['ta-acquisition','ta-power'],'icp-procedure':['icp'],'ltpl-procedure':['ltpl'],'stability-procedure':['stability-storage'],'dft-procedure':['dft-method','dft-exchange','bands'],'lsc-procedure':['lsc-setup'],
'structure-results':['phase','icp-result','morphology','tem-histograms','distortion'],
'optical-results':['optical-summary','ple','crystal-field','qy-series','excitation-qy','trpl','ta-components','ltpl-shift','binding-energy','ltpl-width','optical-illustration'],
'stability-results':['phase-stability','aged-phase-fractions','pl-stability','aged-tem'],'device-results':['lsc-result'],
'mechanistic-context':['phase-hypothesis','emission-mechanism','ta-ste','ta-below-gap','outlook','literature-optical-context','literature-structural-context'],
'source-materials':['chemicals','dry-solvents'],'source-context':['identity','source-availability']}
OWN={SID+'-'+fid:owner for owner,fids in OWNER_GROUPS.items()for fid in fids};assert set(OWN)==set(FM),(set(FM)-set(OWN),set(OWN)-set(FM))
TEXT_STATUSES={'reported_text','reported_identifier','reported_ratio_parts','original_image','group_header'}
def Q(qv,scope='',extra=''):
 es=E(qv['evidence']);note=(extra+' '+cn(qv.get('conflict_ids',[])+qv.get('gap_ids',[]))).strip();basis='Source context: '+scope+'.'
 if qv.get('uncertainty')is not None:note+=' Reported uncertainty '+str(qv['uncertainty'])+' '+str(qv.get('unit'))+'; '+str(qv.get('uncertainty_definition')or'definition not stated')+'.'
 if qv.get('unit_interpretation'):note+=' '+qv['unit_interpretation']
 if qv['status']in TEXT_STATUSES:return fact(qv['raw_text'],es,note=basis+' '+note+' Source components: '+compact(qv.get('components'))+'. Text-only fields retain their literal form.')
 v=qv['value'];lo=(qv.get('range')or{}).get('min');hi=(qv.get('range')or{}).get('max');cmp=qv.get('comparison')
 if cmp in['<','<=']:hi=v;v=None
 if cmp in['>','>=']:lo=v;v=None
 return qty(v,qv.get('unit')or'',es,'reported'if v is not None or lo is not None or hi is not None else'not_reported',minimum=lo,maximum=hi,approximate=qv.get('approximate',False),qualifier=note,basis=basis,raw_text=qv['raw_text'],minimum_exclusive=cmp=='>'if cmp in['>','>=']else None,maximum_exclusive=cmp=='<'if cmp in['<','<=']else None)
def sample(r,scope,es,formula=None):
 sid=norm(scope)
 if not any(p['sample_id']==sid for p in r['products']):
  p=product(sid,formula,E(es),link='general_context',notes=['Source scope: '+scope+'.','Named specimen, preparation condition or analysis context only; not proof of one unique physical batch or an exact same-aliquot cross-technique link.','No approved atomic structure or exact recipe–structure pair.']);p['source_sample_label']=scope;r['products'].append(p);link('sample_context',scope,r,f'/products/{len(r["products"])-1}')
 return sid
GRADE={'cs-carbonate':'Cs2CO3 purity','ode':'ODE purity','oa':'OA purity','olam':'OlAm technical grade','mncl2':'MnCl2 purity','hexane':'hexane purity','meoac':'MeOAc purity'}
def addm(r,mid,stage='characterization'):
 if any(m['id']==mid for m in r['materials']):return mid
 m=MM[mid];r['materials'].append(material(mid,m['name'],m['source_formula_or_abbreviation'],m['role'],stage,E(m['evidence']),notes=[m['scope_note'],'Identity and role are source scoped; qualified molecular/component bindings remain separate.']));j=len(r['materials'])-1;ptr=f'/materials/{j}';unit('materials',mid,r,ptr);link('material',mid,r,ptr)
 for iq,qv in enumerate(FM[SID+'-chemicals']['quantities']):
  if qv['meaning']==GRADE.get(mid):r['materials'][j]['quantities']['reported_grade']=Q(qv,mid);link('fact',SID+'-chemicals',r,ptr+'/quantities/reported_grade','/quantities/'+str(iq))
 return mid
for mid in MM:addm(R['source-materials'],mid)
STOCK_OWNER={'cs-oleate-stock':'cs-oleate-preparation','mn-precursor':'hot-injection-series','icp-matrix':'icp-procedure','cs-calibration':'icp-procedure','mn-calibration':'icp-procedure'}
STOCK_PREP={'cs-oleate-stock':['cs-load','cs-degas','cs-add-oa'],'mn-precursor':['mn-load'],'icp-matrix':[],'cs-calibration':[],'mn-calibration':[]}
CQ={'Cs2CO3 mass':'cs-carbonate','ODE charge':'ode','dry OA charge':'oa','MnCl2 mass':'mncl2','dry ODE charge':'ode','dry OlAm charge':'olam','HNO3 matrix concentration':'hno3','Milli-Q water resistivity':'milliq'}
for st in D['stocks']:
 r=R[STOCK_OWNER[st['id']]];components=[]
 for mid in st['components']:
  co={'material_id':addm(r,mid,'precursor_preparation'if st['id']in['cs-oleate-stock','mn-precursor']else'characterization'),'quantities':{}}
  for qv in st['quantities']:
   target=CQ.get(qv['meaning']);target=(st['id'].replace('-calibration','-standard')if qv['meaning']=='ionic standard concentration interval'else target)
   if target==mid:co['quantities'][key(qv['meaning'])]=Q(qv,st['id'],'Whole stock formulation or analytical reference, not an injected reaction aliquot.')
  components.append(co)
 stock={'id':st['id'],'name':st['name'],'components':components,'concentrations':{},'preparation_operation_ids':STOCK_PREP[st['id']],'scope':st['sample_scope']+'. '+st['notes'],'evidence':E(st['evidence'])};r['stocks'].append(stock);unit('stocks',st['id'],r,f'/stocks/{len(r["stocks"])-1}')
STAGE={op['id']:('precursor_preparation'if pid=='cs-oleate-preparation'or op['id']in['mn-load','mn-degas']else'synthesis'if pid=='hot-injection-series'else'workup'if pid in['primary-isolation','purification-trials']else'characterization')for pid,pr in PP.items()for op in pr['operations']}
EXTERNAL={i for pr in PP.values()for op in pr['operations']for i in op['inputs']if i not in MM}
ANALYSIS={'xrd-data','reported-refinement-data','tem-saed-data','optical-data','trpl-fits','ta-data','ta-fits','icp-results','ltpl-data','binding-energy-fit','stability-data','dft-results','lsc-curves','aged-lsc-curves'}
SUPPORTS={'argon','quench-water','heavy-water','quartz-cuvette'}
SINGLE={'cs-charge','cs-degassed','cs-oleate-stock','stored-cs-stock','hot-cs-stock','mn-precursor','conditioned-mn'}
ENV={'cs-degas':'Vacuum; pressure unreported','cs-add-oa':'Ar during addition; additional degassing reported with incompletely specified switching order','cs-store':'Vacuum storage','cs-reactivate':'Vacuum degassing followed by heating under Ar','mn-load':'Inert atmosphere','mn-degas':'Vacuum; pressure unreported','nc-inject':'Ar, vigorous stirring; rate unreported','nc-dry':'Vacuum desiccator; pressure unreported','leave-crude':'Air exposure','xrd-acquire':'Ambient conditions, about 40% relative humidity and 25 °C','age-specimens':'Dark storage of separate film/dispersion specimens at about 40% relative humidity and 25 °C'}
for pid,pr in PP.items():
 r=R[pid];produced={};outmap={};knownstocks={s['id']for s in r['stocks']}
 for j,so in enumerate(pr['operations']):
  stage=STAGE[so['id']];ins=[]
  for mid in so['inputs']:
   if mid in MM:ins.append(addm(r,mid,stage))
   elif mid in outmap:ins.append(outmap[mid])
   elif mid in knownstocks:ins.append(mid)
   else:
    if not any(s['id']==mid for s in r['material_states']):r['material_states'].append(state(mid,'Source context supplied separately: '+mid.replace('-',' '),[],'analysis_data'if mid in ANALYSIS else'mixture'if mid in SINGLE else'sample_set'))
    ins.append(mid)
  outs=[]
  for out in so['outputs']:
   mapped=out+'-prepared-state'if out in knownstocks else out;outs.append(mapped);kind='analysis_data'if out in ANALYSIS else'waste'if out=='discarded-supernatants'else'mixture'if out in SINGLE else'sample_set';parents=[m for m in ins if m not in SUPPORTS]
   if so['id']=='ipa-or-etoac':parents=[m for m in parents if m!=('etoac'if out.startswith('ipa')else'ipa')]
   if out in['nc-precipitate-series','dried-nc-series']:parents=[m for m in parents if m!='discarded-supernatants']
   r['material_states'].append(state(mapped,('Analysis result: 'if kind=='analysis_data'else'Separate source specimens: 'if kind=='sample_set'else'')+out.replace('-',' '),parents,kind))
  desc=so['action']+'. '+so.get('condition_scope_note','')+' '+so['quantity_scope_note']+' Missing fields: '+', '.join(so['missing_fields'])+'.'
  if so.get('alternative_inputs'):desc+=' Isopropanol and ethyl acetate are alternative antisolvents applied to separate aliquots; they are not combined.'
  if pid=='dft-procedure':desc+=' Reported refinement data provide comparison context; this graph does not assert that the SI coordinates were the exact computed input. The authors cite prior cubic and rhombohedral structures. No qualified coordinate model is attached.'
  if pid=='stability-procedure':desc+=' Stored films and dispersions are separate specimens, never pooled.'
  oo=operation(so['id'],norm(so['action']),so['action'],E(so['evidence']),ins,outs,depends=list(dict.fromkeys(produced[m]for m in so['inputs']if m in produced)),stage=stage,branch='source_contexts_applied_separately',description=desc,environment=fact(ENV.get(so['id']),E(so['evidence'])),retained_fraction=(outs[so['outputs'].index(so['retained_fraction'])]if so['retained_fraction']in so['outputs']else outmap.get(so['retained_fraction'],so['retained_fraction'])))
  for qv in so['quantities']:
   cq=Q(qv,pid);keep=so['id']not in['nc-inject','ta-acquire']and'unit'in cq
   if so['id']=='ta-acquire':keep=qv['meaning']=='time resolution'
   OP_SCOPE.append({'record_id':r['record_id'],'operation_id':so['id'],'quantity_meaning':qv['meaning'],'raw_text':qv['raw_text'],'placement':'operation_parameter_and_context_measurement'if keep else'separate_condition_option_or_context_measurement','reason':'Injection combinations and TA pump/probe contexts stay separate; no Cartesian condition grid or merged specimen is inferred.'})
   if keep:
    pk=key(qv['meaning']);assert pk not in oo['parameters'];oo['parameters'][pk]=cq
    for fid in so['source_fact_ids']:
     for iq,original in enumerate(FM[fid]['quantities']):
      if qv==original:link('fact',fid,r,f'/operations/{j}/parameters/'+esc(pk),'/quantities/'+str(iq))
  r['operations'].append(oo);unit('protocols',pid,r,f'/operations/{j}');unit('operation',so['id'],r,f'/operations/{j}');r['quality']['missing_fields']+=so['missing_fields']
  for old,new in zip(so['outputs'],outs):produced[old]=so['id'];outmap[old]=new
for sc in D['sample_contexts'][:5]:
 r=R['hot-injection-series'];r['condition_options'].append({'id':sc['id'],'label':sc['name']+' · reported preparation condition, not independently counted batch','parameters':{k:Q(sc[k],sc['id'])for k in['injection_temperature','reported_loading_Mn_Cs','cs_oleate_aliquot']},'evidence':E(sc['evidence'])});unit('sample_contexts',sc['id'],r,f'/condition_options/{len(r["condition_options"])-1}')
 ss=sample(r,sc['id'],sc['evidence'],'CsMnCl3');p=next(p for p in r['products']if p['sample_id']==ss);p.update(recipe_link='explicit',link_evidence=E(sc['evidence']),material_state_id='nc-crude-series');p['phase']=fact(sc['reported_phase'],E(sc['evidence']),note='Source-reported phase assignment; not independent phase-purity or atomic-model approval.');p['notes'].append('Isolation and redispersion are recorded separately in primary-isolation. '+sc['phase_scope_note'])
for fid,f in FM.items():
 r=R[OWN[fid]];sid=sample(r,f['sample_scope'],f['evidence']);note='Source claim class: '+f['claim_class']+'. '+cn(f['conflict_ids']+f['gap_ids'])
 r['measurements'].append(measurement(fid+'-claim',sid,'source_claim',fact(f['claim'],E(f['evidence']),note=note),'Source text with process/observation/model/cited scope',E(f['evidence']),conditions=f['sample_scope']));ptr=f'/measurements/{len(r["measurements"])-1}/value';link('fact',fid,r,ptr,'/claim');unit('facts',fid,r,ptr)
 for iq,qv in enumerate(f['quantities']):
  r['measurements'].append(measurement(fid+'-q'+str(iq+1),sid,key(qv['meaning']),Q(qv,f['sample_scope'],note),'Reported source specification or result; scope retained',E(qv['evidence']),conditions=f['sample_scope']+'; '+qv['meaning']));ptr=f'/measurements/{len(r["measurements"])-1}/value';link('fact',fid,r,ptr,'/quantities/'+str(iq));unit('facts',fid,r,ptr)
 r['quality']['conflicts']+=[cn([x])for x in f['conflict_ids']]
TABOWNER={'table-1':'ta-procedure','table-s1':'structure-results','table-s2':'structure-results','table-s3':'icp-procedure','table-s4':'optical-results','table-s5':'optical-results','table-s6':'optical-procedure'}
for tab in T['tables']:
 r=R[TABOWNER[tab['id']]];ss=sample(r,tab['id']+' definition',tab['evidence']);es=E(tab['evidence']);meta={k:deepcopy(v)for k,v in tab.items()if k!='rows'}
 r['measurements'].append(measurement(tab['id']+'-definition',ss,'source_table_definition',fact(compact(meta),es,note='Literal source headings, units, notes and footnotes. Structural/refinement values remain unqualified; blank and zero cells are not repaired.'),'Original table definition',es));ptr=f'/measurements/{len(r["measurements"])-1}/value';unit('table',tab['id'],r,ptr);TABLEMETA.append({'table_id':tab['id'],'record_id':r['record_id'],'pointer':ptr})
 for row in tab['rows']:
  suffix='-xrd'if tab['id']in['table-s1','table-s2']else'-icp'if tab['id']=='table-s3'else'-ta'if tab['id']=='table-1'else'-trpl'if tab['id']=='table-s6'else'-optical';sid=sample(r,row['sample_id']+suffix,row['evidence'])
  for c in row['cells']:
   note='Literal '+tab['id']+' row '+row['row_label']+'. '+('Repeated source group heading metadata; not an additional printed body cell.'if not c['is_printed_body_cell']else'Printed body cell.')
   if tab['id']in['table-s1','table-s2']:note+=' Reported refinement only; zero occupancies, Wyckoff labels, missing angles/uncertainties and absent NCs@200 coordinate block remain unvalidated. No model or exact structure label is created.'
   if tab['id']=='table-s6':note+=' Printed average lifetimes are retained despite the unresolved printed-equation consistency issue.'
   r['measurements'].append(measurement(c['id'],sid,key(c['column']),Q(c,row['sample_id']+suffix,note),'Original table cell; measurement/refinement context',E(c['evidence']),conditions=row['row_label']+'; '+c['column']));ptr=f'/measurements/{len(r["measurements"])-1}/value';link('table_cell',c['id'],r,ptr);unit('table',tab['id'],r,ptr);unit('table_row',row['id'],r,ptr)
FIGOWNER={'graphical-abstract':'mechanistic-context','figure-1':'hot-injection-series','figure-2':'structure-results','figure-3':'structure-results','figure-4':'optical-results','figure-5':'dft-procedure','figure-6':'ta-procedure','figure-7':'ltpl-procedure','figure-8':'stability-results','figure-9':'device-results','figure-s1':'unisolated-control','figure-s2':'structure-results','figure-s2-caption-continuation':'structure-results','figure-s3':'structure-results','figure-s4':'optical-results','figure-s5':'optical-procedure','figure-s6':'ta-procedure','figure-s7':'ltpl-procedure','figure-s8':'stability-results','figure-s9':'stability-results'}
EQOWNER={'synthesis-schematic':'hot-injection-series','distortion':'structure-results','ta-triexponential':'ta-procedure','ta-biexponential':'ta-procedure','thermal-quenching':'ltpl-procedure','trpl-biexponential':'optical-procedure','trpl-average':'optical-procedure','tauc-axes':'optical-results'}
for kind,objs,owners in [('figures',D['figures'],FIGOWNER),('equations',D['equations'],EQOWNER)]:
 for obj in objs:
  r=R[owners[obj['id']]];scope='/'.join(obj.get('sample_ids',[]))or obj.get('sample_scope','author context');ss=sample(r,scope,obj['evidence']);txt=obj['title']+'. '+obj.get('expression','')+' '+obj['scope_note']+' '+cn(obj.get('conflict_ids',[])+obj.get('gap_ids',[]))
  r['measurements'].append(measurement(obj['id']+'-context',ss,kind.rstrip('s')+'_context',fact(txt,E(obj['evidence']),note='Source graphic/expression context; no additional experiment or qualified measured atomic structure.'),'Original '+kind.rstrip('s'),E(obj['evidence'])));unit(kind,obj['id'],r,f'/measurements/{len(r["measurements"])-1}/value')
def scowner(sc):
 sid=sc['id']
 if sc['kind']=='source_preparation_condition':return'hot-injection-series'
 if sid=='cs-oleate-stock':return'cs-oleate-preparation'
 if sid=='below150':return'hot-injection-series'
 if sid=='unisolated-control':return'unisolated-control'
 if sid.endswith('trial'):return'purification-trials'
 if sid.startswith('lsc-'):return'device-results'
 if sid.startswith('dft-'):return'dft-procedure'
 if sid.startswith('ltpl-'):return'ltpl-procedure'
 if sid.endswith('-trpl'):return'optical-procedure'
 if sid.endswith('-ta'):return'ta-procedure'
 if sid.endswith('-icp'):return'icp-procedure'
 if sid.endswith('-xrd'):return'structure-results'
 if sid.endswith('-tem'):return'tem-procedure'
 return'stability-results'
for sc in D['sample_contexts']:
 r=R[scowner(sc)];ss=sample(r,sc['id'],sc['evidence']);ip=next(i for i,p in enumerate(r['products'])if p['sample_id']==ss);r['products'][ip]['notes'].append('Source context definition: '+compact(sc));unit('sample_contexts',sc['id'],r,f'/products/{ip}')
for kind,arr in [('references',D['references']),('conflicts',D['conflicts']),('missingness',D['missingness'])]:
 for obj in arr:
  r=R['source-context'];es=obj.get('evidence')or D['facts'][0]['evidence'];ss=sample(r,'bibliography'if kind=='references'else'source limitations',es);txt=obj['text']if kind=='references'else obj['description'];r['measurements'].append(measurement(obj['id'],ss,kind,fact(txt,E(es),note='Bibliographic pointer; cited full text was not independently read.'if kind=='references'else'Unresolved limitation retained without silent repair.'),'Source '+kind,E(es)));unit(kind,obj['id'],r,f'/measurements/{len(r["measurements"])-1}/value')
for r in R.values():
 r['quality']['missing_fields']=list(dict.fromkeys(r['quality']['missing_fields']));r['quality']['conflicts']=list(dict.fromkeys(r['quality']['conflicts']));r['context_links']=[{'label':'Complete source reader and limitations','url':'/paper-review.html?id='+SID,'relation':'private_unapproved_reader_proposal'}]
 if r['record_id']==PRE+'hot-injection-series':r['context_links']+=[{'label':'Cs-oleate stock preparation','url':'/records/'+PRE+'cs-oleate-preparation.html','relation':'source_reported_upstream_stock'},{'label':'Primary isolation and redispersion','url':'/records/'+PRE+'primary-isolation.html','relation':'source_reported_separate_workup'}]
errors=[e for r in R.values()for e in validate_record(r)];assert not errors,errors[:50]
assert all(FL.values())and all(UL.values())and len(TL)==321
assert len(set(build_groups(list(R.values())).values()))==1
assert not any(v['eligible']for r in R.values()for v in eligibility(r).values())
records=[]
for r in R.values():
 n=r['record_id']+'.json';save(n,r);records.append({'record_id':r['record_id'],'path':str(O/n),'sha256':sha(O/n),'record_type':r['record_type']})
coverage={'schema':'mattersyn-private-field-coverage/1','source_freeze_sha256':sha(P/'package-freeze.json'),'facts':[{'source_fact_id':i,'canonical_bindings':b}for i,b in FL.items()],'source_units':[{'source_unit_id':i,'canonical_bindings':b}for i,b in UL.items()],'table_cells':[{'source_cell_id':i,'canonical_bindings':b}for i,b in TL.items()],'table_definitions':TABLEMETA,'source_objects':OBJECTS,'transport_scope':'All source claims and quantities, 301 printed body cells plus 20 repeated heading metadata fields, and every inventory unit have typed/pointer coverage. Source definitions remain losslessly retained privately.'}
save('source-to-field-coverage.json',coverage);save('lossless-source-map.json',{'private_only':True,'source_freeze_sha256':sha(P/'package-freeze.json'),**deepcopy(D),'tables':deepcopy(T['tables'])});save('operation-quantity-scope.json',{'entries':OP_SCOPE,'notes':COMMON});save('source-owner-map.json',{'fact_owner':OWN,'figure_owner':FIGOWNER,'equation_owner':EQOWNER,'table_owner':TABOWNER,'sample_owner':{s['id']:scowner(s)for s in D['sample_contexts']},'authors':AUTHORS})
checks=[];BY={r['record_id']:r for r in R.values()}
def ck(n,ok):checks.append({'check':n,'passed':bool(ok)});assert ok,n
def vok(src,dst):
 if src['status']in TEXT_STATUSES:return dst['value']==src['raw_text']
 cmp=src.get('comparison')
 if cmp in['<','<=']:ok=dst['maximum']==src['value']and dst.get('maximum_exclusive')==(cmp=='<')
 elif cmp in['>','>=']:ok=dst['minimum']==src['value']and dst.get('minimum_exclusive')==(cmp=='>')
 elif src.get('range'):ok=dst['minimum']==src['range']['min']and dst['maximum']==src['range']['max']
 else:ok=dst['value']==src['value']
 return ok and dst['raw_text']==src['raw_text']and dst['approximate']==src['approximate']and dst['unit']==(src['unit']or'')and(src.get('uncertainty')is None or str(src['uncertainty'])in dst['qualifier'])
for fid,bs in FL.items():
 for b in bs:
  dst=resolve(BY[b['record_id']],b['pointer']);src=resolve(FM[fid],b['source_pointer']);ck(fid+' '+b['pointer'],dst['value']==src if b['source_pointer']=='/claim'else vok(src,dst))
for tab in T['tables']:
 for row in tab['rows']:
  for c in row['cells']:
   b=TL[c['id']][0];ck(c['id'],vok(c,resolve(BY[b['record_id']],b['pointer'])))
for uid,bs in UL.items():
 for b in bs:ck(uid+' '+b['pointer'],resolve(BY[b['record_id']],b['pointer'])is not None)
for p,h in FR['bound_files'].items():ck('Frozen source unchanged '+p,sha(p)==h)
ck('39 distinct operations',sum(len(r['operations'])for r in R.values())==39)
ck('Exactly five synthesis condition options',len(R['hot-injection-series']['condition_options'])==5)
ck('No tasks, model or promotion',all(not r['quality']['requested_tasks']and not r['structure_assets']and'collection'not in r for r in R.values()))
ck('No input alternate antisolvent contamination',all(not('ipa'in s['parent_ids']and'etoac'in s['parent_ids'])for s in R['purification-trials']['material_states']))
counts={'records':len(R),'record_types':{k:sum(r['record_type']==k for r in R.values())for k in['literature_protocol','procedure','observation']},'operations':sum(len(r['operations'])for r in R.values()),'material_slots':sum(len(r['materials'])for r in R.values()),'stock_slots':sum(len(r['stocks'])for r in R.values()),'stock_component_slots':sum(len(s['components'])for r in R.values()for s in r['stocks']),'condition_options':sum(len(r['condition_options'])for r in R.values()),'sample_context_slots':sum(len(r['products'])for r in R.values()),'measurements':sum(len(r['measurements'])for r in R.values()),'source_facts':len(FL),'source_fact_bindings':sum(map(len,FL.values())),'source_units':len(UL),'source_unit_bindings':sum(map(len,UL.values())),'source_table_cells':len(TL),'source_groups':1,'eligible_training_rows':0,'atomic_structure_assets':0}
save('author-validation.json',{'status':'author_schema_semantic_transport_checks_passed','author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'checks':checks,'check_count':len(checks),'counts':counts,'schema_errors':errors,'independent_source_audit':'passed'if SOURCE_PASSED else'pending','independent_canonical_audit':'pending','site_written':False})
save('record-manifest.json',{'schema':'mattersyn-private-canonical-proposal/1','source_id':SID,'version':1,'author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'status':'private_unapproved_author_proposal','independent_source_audit_path':str(AP)if SOURCE_PASSED else None,'independent_source_audit_sha256':sha(AP)if SOURCE_PASSED else None,'source_freeze_sha256':sha(P/'package-freeze.json'),'records':records,'counts':counts,'coverage_sha256':sha(O/'source-to-field-coverage.json'),'validation_sha256':sha(O/'author-validation.json'),'input_modules':{str(S/'scripts'/n):sha(S/'scripts'/n)for n in['dataset_lib.py','record_helpers.py','schema_definition.py']},'author_script_sha256':sha(__file__)})
print(json.dumps(counts));print('MANIFEST',sha(O/'record-manifest.json'))
