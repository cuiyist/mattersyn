"""Unapproved private Ghosh canonical proposal; source freeze and Site remain read-only."""
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
D=read(P/'source-facts.json');I=read(P/'source-inventory.json');FR=read(P/'package-freeze.json');SID='ghosh2012';PRE='ghosh-2012-'
assert sha(P/'package-freeze.json')=='41917b06435344d340990aa7364e651722e6e61f27bb04013b05d32cbb6d0d0b'
for p,h in FR['bound_files'].items():assert sha(p)==h,p
AP=P/'source-independent-audit/independent-audit-v2.json';AU=read(AP)
assert AU['status']=='passed'and not AU['open_findings']and AU['proposal_freeze_sha256']==sha(P/'package-freeze.json')
for p,h in AU['bound_files'].items():assert sha(p)==h,p
AUDIT_NOTE='All supplied main/SI extraction passed distinct source audit of revision 2. Canonical/reader review remains pending; this is an unapproved private draft. Historical pending flags in the frozen source payload describe its author freeze, before the separate audit.'
FM={f['id']:f for f in D['facts']};MM={m['id']:m for m in D['materials']};PP={p['id']:p for p in D['protocols']};SM={x['id']:x for x in D['samples']};UM={(u['type'],u['source_object_id']):u['id']for u in I['inventory_units']};UU={u['id']:u for u in I['inventory_units']};CON={x['id']:x for x in D['conflicts']};GAP={x['id']:x for x in D['gaps']}
R={};FL={i:[]for i in FM};UL={i:[]for i in UU};TL={};OBJECTS=[];TABLEMETA=[]
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
SRC=source(SID,D['doi'],D['title'],'; '.join(D['authors']),2012,si='All nine supplied SI pages read and viewed by extraction author. '+AUDIT_NOTE)
SRC['main_status']='All ten main pages read and viewed by extraction author. '+AUDIT_NOTE
SRC['reuse_status']='Private selected-crop proposal only; raw source PDFs/text/pages remain local. Public import and browser gates are separate.'
COMMON=[AUDIT_NOTE,'Record/context IDs do not count independent batches or replicates.','No atomic model, exact recipe–structure pair, universal cross-technique sample join or training eligibility is approved.','Parameter-comparison branches are not a complete factorial design or interchangeable preferred protocol.']
CONFIG={}
for pid,p in PP.items():
 kind='literature_protocol'if p['kind']=='synthesis'else'protocol_variant'if p['kind']=='synthesis_variant'else'procedure'
 CONFIG[pid]=(p['title'],'CdSe'if pid.startswith('core-')else'CdSe/CdS',kind)
for pid,title,formula in[
('ligand-spectra','Ligand-dependent FTIR and reference bands','CdSe/CdS'),('structural-results','TEM, phase and morphology contexts','CdSe/CdS'),('photophysical-results','Blinking, lifetime and volume results','CdSe/CdS'),('surface-mechanisms','Surface, dipole and electronic interpretations','CdSe/CdS'),('source-materials','Source-qualified reagents and formulations','Study materials'),('source-context','Bibliography, source scope and limitations','Study source context')]:CONFIG[pid]=(title,formula,'observation')
for k,(title,formula,kind)in CONFIG.items():
 r=record(PRE+k,'Ghosh et al. (2012) · '+title,formula,'CdSe cores and CdSe/CdS giant quantum dots',title,deepcopy(SRC),'Full supplied main/SI source scope with exact field locators',kind)
 r['schema_version']='1.3.0';r['lineage'].update(source_group=SID,recipe_family=SID+'-core-shell-parameter-study')
 r['quality'].update(review_status='imported_unreviewed',review_scope=AUDIT_NOTE,requested_tasks=[],experimental_outcome='not_established',missing_fields=COMMON.copy(),conflicts=[])
 r['intended_target']['composition']=fact(formula if kind in['literature_protocol','protocol_variant']else None,FE('core-charge')if formula=='CdSe'else FE('shell-charge'),note='Nominal preparation target only; observations and acquisition records have no synthetic target.')
 if k in['core-small-variant','core-large-variant']:r['lineage']['parent_record_id']=PRE+'core-standard-route'
 if formula=='CdSe/CdS':r['material'].update(architecture='core_shell',components=['CdSe','CdS'])
 R[k]=r
OWNER_GROUPS={
'core-standard-route':['core-charge','core-degas','core-inject','core-standard','core-wash'],
'core-small-variant':['core-small'],'core-large-variant':['core-large'],
'optimized-shell-route':['shell-charge','shell-stocks','shell-passivation','shell-ligand-switch','shell-anneal','shell-withdraw','shell-wash-qy'],
'anneal-series':['thin-shell-baseline','short-anneal-tem','anneal-qy-summary','anneal-asymmetry'],
'solvent-ligand-series':['ode-cycling','od-cycling','od-late-dilution','extreme-dilution','ligand-amounts','secondary-shape','no-added-amine'],
'stoichiometry-series':['withdrawal-series','withdrawal-oa'],
'constant-s-variant':['constant-s-protocol','constant-s-outcome'],
'ligand-spectra':['ftir-primary-low-oa','ftir-high-oa','ftir-secondary','secondary-thin-ftir','ftir-windows'],
'structural-results':['attachment-image','xrd-pattern-values','oa-morphology-pair'],
'surface-mechanisms':['ml-model','steric-model','dipole-model','termination-model','quasi-type-ii','core-only-model','lattice-background'],
'photophysical-results':['optimized-performance','core-series','nonblinking-definition','nonblinking-large','volume-threshold','lifetime-volume','lifetime-table-contract','lifetime-example','blinking-examples','blinking-examples-threshold'],
'ensemble-optics':['ensemble-acquisition'],
'ftir-procedure':['ftir-acquisition'],'tem-procedure':['tem-acquisition'],'xrd-procedure':['xrd-acquisition','xrd-phase-fit'],
'single-dot-procedure':['single-dot-preparation','single-dot-excitation','single-dot-frames','single-dot-analysis'],
'lifetime-procedure':['lifetime-preparation','lifetime-excitation','lifetime-detection'],
'core-only-control':['core-only-control','larger-core-context'],
'source-materials':['materials'],'source-context':['historical-qy','historical-blinking']}
OWN={SID+'-'+fid:owner for owner,fids in OWNER_GROUPS.items()for fid in fids};assert set(OWN)==set(FM),(set(FM)-set(OWN),set(OWN)-set(FM))
def Q(qv,scope='',extra=''):
 es=E(qv['evidence']);note=extra+' '+cn(qv.get('conflict_ids',[])+qv.get('gap_ids',[]));basis='Source context: '+scope+'.'
 if qv.get('uncertainty')is not None:note+=' Reported uncertainty '+str(qv['uncertainty'])+' '+str(qv.get('unit'))+'; definition '+str(qv.get('uncertainty_definition'))+'.'
 if qv.get('unit')is None:note+=' No numeric unit is inferred for this text/image field.'
 if qv['status']in['reported_text','reported_identifier','reported_ratio_parts','original_image']:
  return fact(qv['raw_text'],es,note=basis+' '+note+' Ratio components: '+compact(qv.get('components'))+'.'+(' Original asset ID: '+qv['asset_id']if qv.get('asset_id')else''))
 v=qv['value'];lo=(qv.get('range')or{}).get('min');hi=(qv.get('range')or{}).get('max');cmp=qv.get('comparison')
 if cmp in['<','<=']:hi=v;v=None
 if cmp in['>','>=']:lo=v;v=None
 return qty(v,qv.get('unit')or'',es,'reported'if v is not None or lo is not None or hi is not None else'not_reported',minimum=lo,maximum=hi,approximate=qv.get('approximate',False),qualifier=note.strip(),basis=basis,raw_text=qv['raw_text'],minimum_exclusive=cmp=='>'if cmp in['>','>=']else None,maximum_exclusive=cmp=='<'if cmp in['<','<=']else None)
def sample(r,scope,es):
 sid=norm(scope)
 if not any(p['sample_id']==sid for p in r['products']):
  formula='CdSe'if scope.startswith('core-')and scope not in['core-common']else'CdSe/CdS'if scope.startswith(('lifetime-row','anneal-row','od-','ode-','withdraw-','constant-s','si-blinking','si-large-core','optimized','four-core'))else None
  p=product(sid,formula,E(es),link='general_context',notes=['Source scope: '+scope+'.','Context ID is not an author-assigned physical batch. No all-technique same-particle join is inferred.','No product atomic coordinates or exact training pair are approved.']);p['source_sample_label']=scope;r['products'].append(p);link('sample_context',scope,r,f'/products/{len(r["products"])-1}')
 return sid
ROLES={'cdo':'listed_metal_precursor','cd-oleate':'metal_precursor','top-se':'chalcogen_precursor','sulfur':'chalcogen_precursor','selenium':'listed_chalcogen_precursor','top':'listed_precursor_or_reference','topo':'ligand','oa':'ligand','ola':'ligand','doa':'ligand','ode':'solvent','od':'solvent','ethanol':'precipitant','hexane':'solvent','toluene':'quench_solvent','argon':'inert_atmosphere','r6g':'quantum_yield_reference','acetone':'cleaning_solvent','glass':'support','silicon':'support','diamond':'measurement_cell','liquid-nitrogen':'instrument_coolant','immersion-oil':'optical_coupling','cdse-core':'preformed_core','cdse-cds':'source_sample'}
def addm(r,mid,stage='characterization'):
 if any(m['id']==mid for m in r['materials']):return mid
 m=MM[mid];sf=m['source_formula_or_abbreviation'];formula=sf if sf in['CdO','Ar','N2','CdSe','CdSe/CdS']else None
 r['materials'].append(material(mid,m['name'],formula,ROLES[mid],stage,E(m['evidence']),notes=[m['scope_note'],'Source formula or abbreviation: '+str(sf)+'. Abbreviations such as OA, ODE, OD, TOP and TOPO are not treated as elemental formulae.','Source-qualified identity only; molecular/product visual binding is separately pending.']));ptr=f'/materials/{len(r["materials"])-1}';link('material',mid,r,ptr);unit('material',mid,r,ptr);return mid
for mid in MM:addm(R['source-materials'],mid)
STOCK_OWNER={'top-se-injection':'core-standard-route','s-od-stock':'optimized-shell-route','cd-oleate-stock':'optimized-shell-route'}
for st in D['stocks']:
 r=R[STOCK_OWNER[st['id']]];fid=st.get('source_fact_id')or st['source_fact_ids'][0];es=FM[fid]['evidence'];components=[]
 for co in st['components']:components.append({'material_id':addm(r,co['material_id'],'synthesis'),'quantities':{}})
 concentrations={}
 if st.get('concentration'):concentrations['reported_concentration']=Q(st['concentration'],st['id'])
 if st['id']=='top-se-injection':
  for co,qv in zip(components,st['quantities']):co['quantities'][key(qv['meaning'])]=Q(qv,st['id'])
 stock={'id':st['id'],'name':st['id'].replace('-',' ')+' formulation','components':components,'concentrations':concentrations,'preparation_operation_ids':[],'scope':st['scope']+' Source describes the supplied formulation; no separate upstream preparation operation is fabricated and no additional dosing event is counted.','evidence':E(es)}
 r['stocks'].append(stock);ptr=f'/stocks/{len(r["stocks"])-1}';unit('stock',st['id'],r,ptr);link('stock',st['id'],r,ptr)
STAGES={'core-charge':'precursor_preparation','core-evacuate':'precursor_preparation','core-inject':'synthesis','core-grow-cool':'synthesis','core-isolate':'workup','small-quench':'synthesis','small-isolate':'workup','large-feed':'synthesis','large-isolate':'workup','shell-charge':'precursor_preparation','shell-passivate':'synthesis','shell-cycles':'synthesis','shell-withdraw':'fractionation','shell-purify':'workup','compare-anneals':'synthesis','compare-ode-od':'synthesis','extreme-dilution':'synthesis','compare-ligands':'synthesis','compare-withdrawals':'fractionation','withdraw-oa':'synthesis','constant-s-grow':'synthesis'}
EXTERNAL_SCOPE={'core-growth':'Common core-growth mixture after initial injection; see the parent core route. This external branch input is not a newly prepared batch.','growing-shells':'Shell-growth mixture from the comparison family; complete row-specific parent composition is not established.','core-only-7nm':'Separate 7 nm core-only control; upstream synthesis unreported.'}
PARAMETER_SCOPE={'ftir-purify-cast':{'washing cycles'},'ftir-acquire':{'spectral resolution','accumulated scans'},'xrd-deposit':set(),'ensemble-acquire':set(),'core-control-wash':set(),'compare-anneals':set()}
STEP_DESCRIPTIONS={
'ftir-purify-cast':'Particles are washed six times, then particle or pure-ligand solutions in hexane are cast onto the diamond measurement cell and the solvent evaporated. The six wash cycles describe particle preparation; acquisition resolution and scan count belong to the following action.',
'ftir-acquire':'Acquire ATR-FTIR at 4 cm−1 resolution with 32 accumulated scans. The preceding particle purification is not repeated during acquisition; the spectra retain the distinct particle and pure-ligand reference contexts.',
'xrd-deposit':'Deposit the particle sample on background-less silicon. Wavelength, angular range, sampling width and scan speed belong to the following diffraction acquisition, not the deposition action.',
'ensemble-acquire':'Measure absorption and emission, and determine relative quantum yield using Rhodamine 6G. The 99% value is the reported reference-reagent purity, not the product quantum yield or an acquisition control.',
'core-control-wash':'Compare the separate 7 nm core-only control before and after washing, and assess diluted samples on glass. The reported unwashed QY and emission wavelength are outcomes, not washing settings. Its upstream core synthesis is unreported.',
'compare-anneals':'Compare the five distinct post-S/post-Cd schedules in condition_options and Table 1. The 20 min and stated 3 h narrative summaries and their QY statistics remain separately scoped measurements; they are not one fixed condition assigned to every comparison.'}
OP_SCOPE=[]
for pid,pr in PP.items():
 r=R[pid];produced={}
 for j,so in enumerate(pr['operations']):
  stage=STAGES.get(so['id'],'characterization');ins=[]
  outs=[so['id']+'-withdrawn-aliquots'if out=='withdrawn-aliquots'else out for out in so['outputs']]
  for mid in so['inputs']:
   if mid in MM:ins.append(addm(r,mid,stage))
   elif mid in{st['id']for st in r['stocks']}:ins.append(mid)
   elif mid in produced:ins.append(mid)
   else:
    assert mid in EXTERNAL_SCOPE,(pid,mid)
    if not any(st['id']==mid for st in r['material_states']):r['material_states'].append(state(mid,EXTERNAL_SCOPE[mid],[],'product'if mid=='core-only-7nm'else'reaction_batch'))
    ins.append(mid)
  for out in outs:
   kind='analysis_data'if stage=='characterization'and out not in['ftir-film','xrd-specimen','single-dot-slide','lifetime-film']else'aliquot'if out.endswith('-withdrawn-aliquots')else'product'if so['retained_fraction']==out else'reaction_batch'if stage in['synthesis','precursor_preparation']else'mixture'
   parents=[i for i in ins if i not in['argon','liquid-nitrogen','acetone','immersion-oil']]
   if so['id']in['core-isolate','small-isolate','large-isolate','shell-purify']:parents=[i for i in ins if i!='ethanol']
   r['material_states'].append(state(out,out.replace('-',' '),parents,kind))
  env='argon during heat-up after the evacuation stages'if so['id']=='core-evacuate'else None
  desc=STEP_DESCRIPTIONS.get(so['id'],so['action']+'. '+' '.join(FM[f]['claim']for f in so['source_fact_ids']))+' Missing fields: '+', '.join(so['missing_fields'])+'.'
  if pr.get('inherited_operation_refs'):desc+=' Common parent-route stages are inherited references, not duplicated physical charges: '+', '.join(x['operation_id']for x in pr['inherited_operation_refs'])+'.'
  oo=operation(so['id'],norm(so['action']),so['action'],E(so['evidence']),ins,outs,depends=list(dict.fromkeys(produced[i]for i in so['inputs']if i in produced)),stage=stage,description=desc,environment=fact(env,E(so['evidence'])),retained_fraction=so['retained_fraction'])
  for qv in so['quantities']:
   # Measured sizes, QYs, phase ratios and observed turbidity are results, not control settings.
   meaning=qv['meaning'];skip=any(x in meaning.lower()for x in['qy','core diameter','face count','onset','wz:zb','faceting','signature','incomplete clearing'])or meaning in['dilution starting shell count']and so['id']!='compare-ode-od'
   if so['id']in PARAMETER_SCOPE:skip=meaning not in PARAMETER_SCOPE[so['id']]
   if so['id']=='compare-ligands'and meaning in['OA after fourteen layers','associated shell count']:skip=True
   OP_SCOPE.append({'record_id':r['record_id'],'operation_id':so['id'],'quantity_meaning':meaning,'raw_text':qv['raw_text'],'placement':'context_measurement_only'if skip or qv['status']in['reported_text','reported_identifier','reported_ratio_parts','original_image']else'operation_parameter_and_context_measurement','reason':'Operation-specific source control only; results, shared acquisition/preparation fields and text-only formulation ratios remain losslessly typed in source measurements.'})
   if skip:continue
   cq=Q(qv,pid)
   if 'unit'not in cq:continue
   pk=key(meaning);oo['parameters'][pk]=cq
   for fid in so['source_fact_ids']:
    for iq,original in enumerate(FM[fid]['quantities']):
     if qv==original:link('fact',fid,r,f'/operations/{j}/parameters/'+esc(pk),'/quantities/'+str(iq))
  r['operations'].append(oo);unit('protocol',pid,r,f'/operations/{j}');link('operation',so['id'],r,f'/operations/{j}');r['quality']['missing_fields']+=so['missing_fields']
  for out in so['outputs']:produced[out]=so['id']
  if pr['kind']=='parameter_comparison':oo['branch']='reported_parameter_comparison';oo['description']+=' This operation groups source-described alternatives for navigation, not a single physical charge containing all alternatives simultaneously.'
for fid,f in FM.items():
 r=R[OWN[fid]];sid=sample(r,f['sample_scope'],f['evidence']);es=E(f['evidence']);note='Source claim class: '+f['claim_class']+'. '+cn(f['conflict_ids']+f['gap_ids'])
 r['measurements'].append(measurement(fid+'-claim',sid,'source_claim',fact(f['claim'],es,note=note),'Source text with explicit reported/model/context scope',es,conditions=f['sample_scope']));ptr=f'/measurements/{len(r["measurements"])-1}/value';link('fact',fid,r,ptr,'/claim');unit('fact',fid,r,ptr)
 for iq,qv in enumerate(f['quantities']):
  r['measurements'].append(measurement(fid+'-q'+str(iq+1),sid,key(qv['meaning']),Q(qv,f['sample_scope'],note),'Source result, condition or stated model parameter',E(qv['evidence']),conditions=f['sample_scope']+'; '+qv['meaning']));ptr=f'/measurements/{len(r["measurements"])-1}/value';link('fact',fid,r,ptr,'/quantities/'+str(iq));unit('fact',fid,r,ptr)
 r['quality']['conflicts']+=[cn([x])for x in f['conflict_ids']]
TABLEOWNER={'table-1':'anneal-series','table-2':'solvent-ligand-series','table-3':'stoichiometry-series','table-s1':'photophysical-results','table-s2-inset':'ligand-spectra'}
for t in D['tables']:
 r=R[TABLEOWNER[t['id']]];es=E(t['evidence']);sid=sample(r,t['sample_scope'],t['evidence']);meta={k:deepcopy(t[k])for k in['id','title','columns','sample_scope','notes','evidence']};r['measurements'].append(measurement(t['id']+'-definition',sid,'table_definition',fact(compact(meta),es,note='Lossless source table headings and qualifiers, not an exact multi-technique sample join.'),'Source table definition',es));ptr=f'/measurements/{len(r["measurements"])-1}/value';unit('table',t['id'],r,ptr);TABLEMETA.append({'table_id':t['id'],'record_id':r['record_id'],'pointer':ptr})
 for row in t['rows']:
  scope=row.get('sample_id',t['sample_scope']);ss=sample(r,scope,t['evidence'])
  for c in row['cells']:
   col=c['column'];extra='Table 3 TEM represents moderately thick shells; QY column >15 ML. Same-thickness identity is unverified.'if t['id']=='table-3'else''
   r['measurements'].append(measurement(c['id'],ss,key(t['id']+' '+row['row_label']+' '+col),Q(c,scope,extra),'Source table numeric/text/image cell',E(c['evidence']),conditions='Row '+row['row_label']+'; column '+col+'. '+row.get('qualifier','')));ptr=f'/measurements/{len(r["measurements"])-1}/value';link('table_cell',c['id'],r,ptr);unit('table',t['id'],r,ptr)
  if t['id']=='table-1':r['condition_options'].append({'id':'anneal-row-'+row['row_label'],'label':'Table 1 post-S/post-Cd anneal schedule '+row['row_label'],'parameters':{c['column']:Q(c,scope)for c in row['cells'][:2]},'evidence':es})
FIGOWNER={'graphical-abstract':'photophysical-results','figure-1':'ligand-spectra','figure-2':'structural-results','figure-3':'photophysical-results','figure-4':'photophysical-results','figure-s1':'anneal-series','figure-s2':'ligand-spectra','figure-s3':'structural-results','figure-s4':'structural-results','figure-s5':'surface-mechanisms','figure-s6':'ligand-spectra','figure-s7':'photophysical-results','figure-s8':'photophysical-results'}
for obj in D['figures']+D['schemes']+D['equations']:
 kind='figure'if obj in D['figures']else'scheme'if obj in D['schemes']else'equation';owner=FIGOWNER[obj['id']]if kind=='figure'else'optimized-shell-route'if kind=='scheme'else'single-dot-procedure'if obj['id'].startswith('equation-on')else'lifetime-procedure';r=R[owner];scope=obj.get('sample_scope',obj.get('scope','source-context'));sid=sample(r,scope,obj['evidence']);es=E(obj['evidence']);text=obj.get('title','')+'. '+obj.get('scope_note','')if kind!='equation'else obj['expression']+'. '+obj['meaning']
 r['measurements'].append(measurement(obj['id']+'-context',sid,kind+'_context',fact(text,es,note='Original source definition/artwork; no plot digitization or new atomic geometry.'),'Source '+kind,es));unit(kind,obj['id'],r,f'/measurements/{len(r["measurements"])-1}/value')
for obj in D['samples']:
 linked=[f for f in D['facts']if f['sample_scope']==obj['id']];owner=OWN[linked[0]['id']]if linked else next((TABLEOWNER[t['id']]for t in D['tables']if any(row.get('sample_id')==obj['id']for row in t['rows'])),'source-context');r=R[owner];es=obj.get('evidence')or D['facts'][0]['evidence'];sid=sample(r,obj['id'],es);ip=next(i for i,p in enumerate(r['products'])if p['sample_id']==sid);r['products'][ip]['notes'].append('Source context object: '+compact(obj));unit('sample_context',obj['id'],r,f'/products/{ip}')
for owner,scope,stateid in[('core-standard-route','core-3-or-4','core-3-or-4'),('core-small-variant','core-2p2','core-2p2'),('core-large-variant','core-5p5','core-5p5'),('optimized-shell-route','optimized-shell','optimized-cdse-cds'),('constant-s-variant','constant-s','constant-s-particles')]:
 r=R[owner];p=next(p for p in r['products']if p['sample_id']==scope);p.update(recipe_link='explicit',material_state_id=stateid,link_evidence=E(PP[owner]['operations'][-1]['evidence']));p['notes'].append('Explicit preparation-to-nominal-product family only; no exact cross-technique batch/structure label.');r['intended_target']['composition']['evidence']=E(PP[owner]['operations'][0]['evidence'])
for ref in D['references']:
 r=R['source-context'];sid=sample(r,'bibliographic-context',ref['evidence']);es=E(ref['evidence']);r['measurements'].append(measurement(ref['id'],sid,'bibliographic_reference',fact(ref['citation'],es,note='Source reference only; full cited work not read.'),'Reference list',es));unit('reference',ref['id'],r,f'/measurements/{len(r["measurements"])-1}/value')
for r in R.values():
 r['quality']['missing_fields']=list(dict.fromkeys(r['quality']['missing_fields']));r['quality']['conflicts']=list(dict.fromkeys(r['quality']['conflicts']));r['context_links']=[{'label':'Source reader and limitations','url':'/paper-review.html?id='+SID,'relation':'private_unapproved_reader_proposal'}]
errors=[e for r in R.values()for e in validate_record(r)];assert not errors,errors[:40]
assert all(FL.values())and all(UL.values())and len(TL)==272
assert len(set(build_groups(list(R.values())).values()))==1
assert not any(v['eligible']for r in R.values()for v in eligibility(r).values())
records=[]
for r in R.values():
 n=r['record_id']+'.json';save(n,r);records.append({'record_id':r['record_id'],'path':str(O/n),'sha256':sha(O/n),'record_type':r['record_type']})
coverage={'schema':'mattersyn-private-field-coverage/1','source_freeze_sha256':sha(P/'package-freeze.json'),'facts':[{'source_fact_id':i,'canonical_bindings':b}for i,b in FL.items()],'source_units':[{'source_unit_id':i,'canonical_bindings':b}for i,b in UL.items()],'table_cells':[{'source_cell_id':i,'canonical_bindings':b}for i,b in TL.items()],'table_definitions':TABLEMETA,'source_objects':OBJECTS,'transport_scope':'All 71 claims, 194 quantities, 272 table cells and source inventory objects receive exact field links. Comparison contexts do not create independent batches; no model/training admission.'}
save('source-to-field-coverage.json',coverage);save('lossless-source-map.json',{'private_only':True,'source_freeze_sha256':sha(P/'package-freeze.json'),**{k:deepcopy(D[k])for k in['facts','materials','stocks','protocols','samples','tables','figures','schemes','equations','references','conflicts','gaps']}})
save('operation-quantity-scope.json',{'schema':'mattersyn-operation-quantity-scope/1','source_facts_sha256':sha(P/'source-facts.json'),'entries':OP_SCOPE,'notes':['This downstream assignment does not change the frozen extraction. Each source quantity remains in its source-scoped canonical measurement.','Five alternative anneal schedules are typed condition_options; their QYs and rounded narrative totals are context-only.','Repeated withdrawal outputs receive operation-specific local state IDs to prevent graph collisions; no extra physical aliquot is inferred.']})
checks=[];BY={r['record_id']:r for r in R.values()}
def ck(n,ok):checks.append({'check':n,'passed':bool(ok)});assert ok,n
def vok(src,dst):
 if src['status']in['reported_text','reported_identifier','reported_ratio_parts','original_image']:return dst['value']==src['raw_text']
 cmp=src.get('comparison')
 if cmp in['<','<=']:ok=dst['maximum']==src['value']and dst.get('maximum_exclusive')==(cmp=='<')
 elif cmp in['>','>=']:ok=dst['minimum']==src['value']and dst.get('minimum_exclusive')==(cmp=='>')
 elif src.get('range'):ok=dst['minimum']==src['range']['min']and dst['maximum']==src['range']['max']
 else:ok=dst['value']==src['value']
 return ok and dst['raw_text']==src['raw_text']and dst['approximate']==src['approximate']and dst['unit']==(src['unit']or'')
for fid,bs in FL.items():
 for b in bs:
  dst=resolve(BY[b['record_id']],b['pointer']);ss=resolve(FM[fid],b['source_pointer']);ck(fid+' '+b['pointer'],dst['value']==ss if b['source_pointer']=='/claim'else vok(ss,dst))
for t in D['tables']:
 for row in t['rows']:
  for c in row['cells']:
   b=TL[c['id']][0];ck('Source cell '+c['id'],vok(c,resolve(BY[b['record_id']],b['pointer'])))
for u,bs in UL.items():
 for b in bs:ck('Inventory pointer '+u+' '+b['pointer'],resolve(BY[b['record_id']],b['pointer'])is not None)
for p,h in FR['bound_files'].items():ck('Frozen input unchanged '+p,sha(p)==h)
ck('Exactly 33 source operations',sum(len(r['operations'])for r in R.values())==33)
ck('No task/model/collection promotion',all(not r['structure_assets']and not r['quality']['requested_tasks']and r['quality']['review_status']=='imported_unreviewed'and'collection'not in r for r in R.values()))
ck('Five comparison schedules',len(R['anneal-series']['condition_options'])==5)
for opid,allowed in PARAMETER_SCOPE.items():
 op=next(o for r in R.values()for o in r['operations']if o['id']==opid)
 ck('Action-specific quantity placement '+opid,set(op['parameters'])=={key(k)for k in allowed})
counts={'records':len(R),'record_types':{k:sum(r['record_type']==k for r in R.values())for k in['literature_protocol','protocol_variant','procedure','observation']},'operations':sum(len(r['operations'])for r in R.values()),'material_slots':sum(len(r['materials'])for r in R.values()),'stock_slots':sum(len(r['stocks'])for r in R.values()),'sample_context_slots':sum(len(r['products'])for r in R.values()),'measurements':sum(len(r['measurements'])for r in R.values()),'source_facts':len(FL),'source_fact_bindings':sum(map(len,FL.values())),'source_units':len(UL),'source_unit_bindings':sum(map(len,UL.values())),'source_table_cells':len(TL),'source_groups':1,'eligible_training_rows':0,'atomic_structure_assets':0}
save('author-validation.json',{'status':'author_schema_semantic_transport_checks_passed','author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'checks':checks,'check_count':len(checks),'counts':counts,'schema_errors':errors,'independent_source_audit':'passed_revision_2','independent_canonical_audit':'pending','site_written':False,'training_exported':False})
save('record-manifest.json',{'schema':'mattersyn-private-canonical-proposal/1','source_id':SID,'version':1,'author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'status':'private_unapproved_author_proposal','independent_source_audit_path':str(AP),'independent_source_audit_sha256':sha(AP),'source_freeze_sha256':sha(P/'package-freeze.json'),'records':records,'counts':counts,'coverage_sha256':sha(O/'source-to-field-coverage.json'),'validation_sha256':sha(O/'author-validation.json'),'input_modules':{str(S/'scripts'/n):sha(S/'scripts'/n)for n in['dataset_lib.py','record_helpers.py','schema_definition.py']},'author_script_sha256':sha(__file__)})
print(json.dumps(counts));print('MANIFEST',sha(O/'record-manifest.json'))
