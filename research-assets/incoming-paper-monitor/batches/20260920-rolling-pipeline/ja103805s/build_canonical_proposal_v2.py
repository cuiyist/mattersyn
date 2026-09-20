"""Private Evans draft authoring; original extraction and Site are read-only."""
from pathlib import Path
from copy import deepcopy
from collections import Counter
from datetime import datetime,timezone
import hashlib,json,re,sys
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parent
O=B/'canonical-proposal/v2';O.mkdir(parents=True,exist_ok=True)
S=Path(r'[local path redacted]')
sys.path.insert(0,str(S/'scripts'))
from record_helpers import record,source,fact,qty,material,operation,state,product,measurement
from dataset_lib import validate_record,eligibility,build_groups
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def norm(x):return re.sub('[^a-z0-9]+','-',str(x).lower()).strip('-')
def esc(x):return str(x).replace('~','~0').replace('/','~1')
def compact(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'))
def resolve(x,p):
 for t in p.strip('/').split('/') if p else []:x=x[int(t)] if isinstance(x,list) else x[t.replace('~1','/').replace('~0','~')]
 return x
I=read(B/'source-inventory.json');D=read(B/'source-extraction-revision-2/source-facts.json');FREEZE=read(B/'source-extraction-revision-2/source-extraction-freeze.json')
assert sha(B/'source-extraction-revision-2/source-extraction-freeze.json')=='e152d9356ba06facf5330a0220f3ad232b23076741a7c30876aa5a953d046ce1'
for x in FREEZE['files']:assert sha(x['path'])==x['sha256'],x['path']
U={x['id']:x for x in I['units']};F={x['id']:x for x in D['facts']};M={x['id']:x for x in I['materials']};P={x['id']:x for x in I['procedures']}
SID='evans2010';PRE='evans-2010-';R={};UL={u:[] for u in U};FL={f:[] for f in F};OBJ=[]
def E(uid):
 u=U[uid];return [{'source_id':SID,'locator':('CIF ' if u['source_role']=='cif' else u['source_role'].upper()+' PDF p. '+str(u['pdf_page'])+' (printed '+str(u['printed_page'])+'), ')+u['locator']}]
def bindu(r,uid,p):UL[uid].append({'record_id':r['record_id'],'pointer':p})
def bindf(r,fid,p,sub=''):FL[fid].append({'record_id':r['record_id'],'pointer':p,'source_value_pointer':sub})
SRC=source(SID,I['doi'],I['title'],'Christopher M. Evans; Meagan E. Evans; Todd D. Krauss',2010,si='Matched 21-page SI and species-9 molecular CIF; source author reading complete, independent scientific audit pending.')
SRC['main_status']='All three main pages and 21 SI pages read and visually inspected by source author; independent audit is a separate gate.'
SRC['reuse_status']='Private canonical proposal. No article or figure reuse permission inferred.'
COMMON=['Source and canonical independent scientific audits are pending.','No QD atomic-coordinate CIF is supplied.','Source-defined recipe families and observation contexts are not independently enumerated physical batches.']
def base(k,title,formula='CdSe / PbSe',kind='observation',method='Source-scoped characterization or interpretation'):
 r=record(PRE+norm(k),'Evans et al. (2010) · '+title,formula,'Phosphine-selenide precursor chemistry and CdSe/PbSe nanocrystals',method,deepcopy(SRC),'Main pp. 10973–10975; SI pp. S1–S21 and molecular CIF',kind)
 r['schema_version']='1.3.0';r['lineage'].update(source_group=SID,recipe_family=SID+'-phosphine-selenide-study')
 r['quality'].update(review_status='imported_unreviewed',requested_tasks=[],missing_fields=COMMON.copy(),conflicts=[],review_scope='Private author draft from the unchanged source extraction freeze. Record IDs are curation contexts, not replicate or physical batch claims. No training, reader, visual, structure-pair or publication approval.',experimental_outcome='not_established')
 r['intended_target']['composition']=fact(formula if kind=='literature_protocol' else None,E('evans2010-identity'),note='Only the named synthesis route supplies an intended product; supporting procedures and observations do not imply a new QD synthesis.')
 R[k]=r;return r
FORM={'cd-oleate':'Cd(C18H33O2)2','pb-oleate':'Pb(C18H33O2)2','topse':'SeP(C8H17)3','dppse':'SePPh2H','tippse':'SeP(C3H7)3','tepse':'SeP(C2H5)3','tppse':'SeP(C6H5)3','species9-crystallization':'C24H20P2PbSe4','pbse-qd':'PbSe','cdse-qd':'CdSe','pbse-msc-family':'PbSe','tertiary-negative-rescue':'PbSe','dpp-pb-control':'Pb','dpp-cd-negative':'Cd precursor control','topse-distillation':'TOPSe mixture','topse-B-stock':'TOPSe mixture'}
for k,p in P.items():
 r=base(k,p['label'],FORM[k],'literature_protocol' if k in ['pbse-qd','cdse-qd','pbse-msc-family'] else 'procedure',p['category'].replace('_',' '))
 r['quality']['missing_fields']+=p['missing'];r['quality']['conflicts']=[c['id']+': '+c['issue'] for c in I['source_conflicts'] if c['id'] in p['conflict_ids']]
for k,t,form in [('reagents','Reagents and commercial grades','Reagent inventory'),('nmr-methods','General NMR acquisition and solvent handling','NMR contexts'),('top-impurities','Commercial TOP impurity spectra','TOP mixture'),('tbp-impurities','Tributylphosphine impurity spectrum','TBP mixture'),('topse-impurities','TOPSe impurity spectra','TOPSe mixture'),('compound-identities','Observed compound identities and NMR assignments','Observed compounds'),('cd-ratios','Cd precursor ratio comparison','Cd precursor mixtures'),('pb-ratio','Pb precursor 1:1 comparison','Pb precursor mixture'),('cd-timecourse','Cd precursor reaction at 10 minutes and 24 hours','Cd precursor mixture'),('topse-dpp15','TOPSe with 15 mol% DPP','PbSe reaction context'),('molecular9-structure','Molecular species 9 diffraction and refinement','C24H20P2PbSe4'),('pbse-tem','PbSe TEM morphology examples','PbSe'),('optical-comparison','CdSe and PbSe optical examples','CdSe / PbSe'),('pbse-conversion','Representative PbSe optical conversion calculation','PbSe'),('mechanism','Mechanistic evidence, hypotheses and limitations','CdSe / PbSe'),('source-context','Source identity, references and limitations','Study context')]:base(k,t,form)
def uk(uid):
 short=uid.removeprefix(SID+'-')
 if short in P:return short
 if short.startswith('reagent-'):return 'reagents'
 if short=='nmr-general':return 'nmr-methods'
 if short.startswith('cif-') or short=='species9-acquisition':return 'molecular9-structure'
 if U[uid]['kind'] in ['reference','identity','metadata','source_scope']:return 'source-context'
 return {'object-figure-1':'pbse-msc-family','object-table-1':'compound-identities','object-figure-2':'topse-dpp15','object-figure-S1':'top-impurities','object-figure-S2':'tbp-impurities','object-figure-S3':'topse-impurities','object-figure-S4':'topse-distillation','object-table-S7-composition':'topse-distillation','object-figure-S5':'pbse-msc-family','object-figure-S6':'dpp-pb-control','object-figure-S7':'dpp-pb-control','object-figure-S8':'cd-ratios','object-figure-S9':'pb-ratio','object-figure-S10':'cd-timecourse','object-figure-S11':'cd-timecourse','object-figure-S12':'molecular9-structure','object-figure-S13':'molecular9-structure','object-figure-S15':'optical-comparison','object-figure-S16':'pbse-tem','object-calculation-S21-yield':'pbse-conversion','dpp-topse-main-shifts':'topse-dpp15'}.get(short,'mechanism')
def sample(r,key,label=None,formula=None,link='general_context',out=None,uid='evans2010-identity'):
 key=norm(key)
 if not any(p['sample_id']==key for p in r['products']):
  x=product(key,formula,E(uid),link=link,state=out,notes=['Curated source context; no physical batch or replicate identity inferred.']);x['source_sample_label']=label or key;r['products'].append(x)
 return key
def q(f,sub='',v0=None):
 v=resolve(f['value'],sub) if sub else f['value'];status=f['status'];basis='Source status: '+status+'. Source unit: '+f['source_unit_id']+'. Source scope: '+f['sample_scope']+'.'
 if sub:basis+=' Source value pointer: '+sub+'.'
 qualifier=' '.join([f.get('qualifier','')]+[c['id']+': '+c['issue'] for c in I['source_conflicts'] if c['id'] in f.get('conflict_ids',[])])
 if f.get('standard_uncertainty') is not None:qualifier+=' Standard uncertainty as reported: '+str(f['standard_uncertainty'])+'.'
 st='author_derived' if status in ['author_derived','author_interpretation'] else 'calculated' if status=='computed_from_reported' else 'not_reported' if v is None and f.get('minimum') is None and f.get('maximum') is None else 'reported'
 if status in ['author_model_input','reported_refinement_model','cited_background']:basis+=' This is a model/reference context, not a direct QD measurement.'
 if isinstance(v,(int,float)) and not isinstance(v,bool) or (v is None and f.get('unit') is not None):
  unit=f.get('unit') or ''
  for tag,un in [('ppm','ppm'),('Hz','Hz'),('integral','relative integral'),('mol_percent','mol%')]:
   if tag in sub:unit=un;break
  return qty(v,unit,E(f['source_unit_id']),st,minimum=None if sub else f.get('minimum'),maximum=None if sub else f.get('maximum'),approximate=f.get('approximate',False),qualifier=qualifier,basis=basis,raw_text=(f.get('raw_text') or '') if not sub else str(v),derivation='Curator calculation from the explicitly reported starting charge; the conflicting printed expression remains separately preserved.' if st=='calculated' else None,minimum_exclusive=None if sub else f.get('minimum_exclusive'),maximum_exclusive=None if sub else f.get('maximum_exclusive'))
 if v==[] or v=={}:return fact(compact(v),E(f['source_unit_id']),'reported',note=basis+' Empty source annotation container; this is not a quantitative zero or absence-of-signal claim. '+qualifier)
 return fact(v,E(f['source_unit_id']),st,note=basis+' '+qualifier)
def addmat(r,k,stage='precursor_preparation',role=None):
 if any(m['id']==k for m in r['materials']):return k
 if k in M:
  m=M[k];uid=m['source_unit_id'];payload=U[uid].get('payload');notes=[]
  if U[uid]['kind']=='material':notes=['Supplier: '+str((payload or {}).get('supplier') or 'not reported')+'.','Grade: '+str((payload or {}).get('grade') or 'not reported')+'.',(payload or {}).get('note','Identity follows the named source reagent; no molecular coordinates supplied.')]
  role=role or ('proposed_intermediate' if k.startswith('intermediate-') else 'solvent' if k in ['toluene','toluene-d8','ode','acetone'] else 'ligand' if k=='oa' else 'atmosphere' if k=='n2' else 'metal_precursor' if k in ['cdo','pbo','cd-oleate','pb-oleate'] else 'chalcogen_precursor' if k in ['se','topse','dppse','tippse','tepse','tppse'] else 'source_material')
  mm=material(k,m['name'],m['formula_or_condensed_identity'],role,stage,E(uid),notes=notes)
  for f in F.values():
   if f['source_unit_id']==uid and f['property']=='commercial purity':mm['quantities']['purity']=q(f);bindf(r,f['id'],f'/materials/{len(r["materials"])}/quantities/purity')
 else:
  rkey=r['record_id'].removeprefix(PRE);uid=next((p['source_unit_id'] for pk,p in P.items() if norm(pk)==rkey),'evans2010-object-figure-S4' if k=='unknown-p-impurities' else 'evans2010-nmr-general');name,form={'top-unspecified':('Trioctylphosphine; source does not identify the lot for this use','P(C8H17)3'),'unknown-p-impurities':('Unidentified phosphorus impurities',None),'toluene-grade-unspecified':('Toluene; grade not restated for this operation','C7H8')}[k]
  mm=material(k,name,form,role or 'source_material',stage,E(uid),notes=['Identity/grade is not silently selected from a different source context.'])
 r['materials'].append(mm);bindu(r,uid,f'/materials/{len(r["materials"])-1}');return k
for m in I['materials']:
 r=R['reagents'] if m['id'] not in ['compound-2','compound-3','compound-4','compound-5','compound-7','compound-8','compound-12','compound-13'] and not m['id'].startswith('intermediate-') else R['mechanism'] if m['id'].startswith('intermediate-') else R['compound-identities'];addmat(r,m['id'])
# Operation entries are source steps. Each stage explicitly charges only its named inputs.
# Tuple: action, academic label, material inputs, environment, parameter-fact suffixes, stage, retained.
OPS={
'cd-oleate': [('heat','Combine reagents and dissolve cadmium oxide',['cdo','oa','ode','n2'],'Flowing nitrogen',['cdo-mass','cdo-amount','oleic-acid-volume','oleic-acid-amount','octadecene-volume','flask-capacity','temperature'],'precursor_preparation',False),('hold_cool','Hold after dissolution and cool',[],'Flowing nitrogen; cool to room temperature',['hold-after-dissolution'],'precursor_preparation',False),('precipitate_centrifuge','Precipitate and isolate cadmium oleate',['acetone'],None,[],'workup',True)],
'pb-oleate':[('heat','Combine lead precursor and inherit the stated preparation',['pbo','oa','ode','n2'],'Flowing nitrogen; explicitly inherited Cd-oleate procedure',['pbo-mass','pbo-amount','oleic-acid-volume','oleic-acid-amount','octadecene-volume','inherited-temperature','inherited-additional-hold','inherited-flask-capacity'],'precursor_preparation',False),('precipitate_centrifuge','Cool, precipitate and isolate lead oleate',['acetone'],'Room-temperature cooling; inherited acetone precipitation and centrifugation',[],'workup',True),('characterize','Record the stated FTIR identity confirmation',[],None,[],'characterization',False)],
'topse':[('stir','Combine TOP and selenium under nitrogen',['top-unspecified','se','n2'],'Nitrogen-filled glovebox; overnight duration not numeric',['top-volume','top-amount','se-mass','se-amount'],'precursor_preparation',False),('retain_solution','Retain unpurified TOPSe solution',[],None,[],'precursor_preparation',True)],
'dppse':[('combine','Charge DPP, selenium and anhydrous toluene',['dpp','se','toluene','n2'],'Nitrogen glovebox; seal with septum',['selenium-mass','selenium-amount','dpp-volume','dpp-amount','anhydrous-toluene-volume'],'precursor_preparation',False),('reflux','Attach condenser and reflux under nitrogen',[],'Slight nitrogen flow; water-cooled condenser',['reflux-duration'],'precursor_preparation',False),('recrystallize','Concentrate and recrystallize DPPSe',['toluene-grade-unspecified'],'Hot toluene; numeric temperature unreported',[],'workup',True)],
'tippse':[('stir','Prepare TIPPSe at room temperature',['tipp','se','toluene','n2'],'Nitrogen glovebox; room temperature overnight',['tipp-volume','tipp-amount','se-mass','se-amount','toluene-volume'],'precursor_preparation',False),('recrystallize','Remove volatiles and recrystallize TIPPSe',['toluene-grade-unspecified'],'In vacuo; hot toluene recrystallization',[],'workup',True)],
'tepse':[('stir','Prepare TEPSe under nitrogen',['tep','se','toluene','n2'],'Nitrogen glovebox; overnight',['tep-volume','tep-amount','se-mass','se-amount','toluene-volume'],'precursor_preparation',False),('filter_concentrate','Remove excess selenium and concentrate filtrate',[],None,[],'workup',True),('recrystallize','Recrystallize and wash TEPSe',['acetone'],'Hot acetone recrystallization; cold acetone washing',[],'workup',True)],
'tppse':[('stir','Prepare TPPSe under nitrogen',['tpp','se','toluene','n2'],'Nitrogen glovebox; overnight',['tpp-mass','tpp-amount','se-mass','se-amount','toluene-volume'],'precursor_preparation',False),('filter_concentrate','Remove excess selenium and concentrate filtrate',[],None,[],'workup',True),('recrystallize','Recrystallize and wash TPPSe',['toluene-grade-unspecified','acetone'],'Hot toluene recrystallization; cold acetone washing',[],'workup',True)],
'tertiary-negative-rescue':[('combine','Prepare the pure-TIPPSe control',['pb-oleate','tippse','toluene-d8'],'J-Young NMR tube',['pb-oleate-mass','pb-oleate-amount','tippse-mass','tippse-amount','toluene-d8-total-volume'],'synthesis',False),('heat_monitor','Heat and monitor the negative control',[],None,['control-temperature','control-duration'],'synthesis',False),('add','Add DIPP to the control mixture',['dipp'],'Rescue temperature and duration not stated',['dipp-volume','dipp-amount'],'synthesis',False),('context','Retain the analogous TEPSe and TPPSe control statement',[],None,[],'characterization',False)],
'topse-distillation':[('evacuate_heat','Charge and evacuate the short-path apparatus',['topse'],'One-neck flask; short-path head; receiving flask',['initial-topse-volume','pressure'],'fractionation',False),('distill','Collect A and two unlabelled distillation cuts',[],'Slow heating; rate and temperature location unreported',['a-collection-start-temperature','a-collected-volume','unlabelled-cut2-temperature','unlabelled-cut2-volume','unlabelled-cut3-temperature','unlabelled-cut3-volume'],'fractionation',True),('retain_residue','Retain residue C and analyze the fractions',[],None,[],'fractionation',True)],
'topse-B-stock':[('prepare_stock','Prepare the independently made B stock',['top-unspecified'],'Starting-solute wording conflicts between prose and caption',['nominal-topse-concentration'],'precursor_preparation',False)],
'pbse-msc-family':[('heat','Generate lead oleate in situ',['pbo','oa','ode','n2'],'Nitrogen atmosphere; three-neck flask',['pbo-mass','pbo-amount','oleic-acid-volume','oleic-acid-amount','octadecene-volume','precursor-dissolution-temperature'],'precursor_preparation',False),('cool_inject','Cool and inject the assigned TOPSe source',[],'A, B and C are separate alternatives, not co-injected',['injection-growth-temperature','topse-amount'],'synthesis',False),('monitor','Follow the separate A, B and C absorption series',[],None,['comparison-time'],'characterization',False),('context','Retain the A/C qualitative MSC comparison',[],None,[],'characterization',False)],
'dpp-pb-control':[('combine_seal','Prepare and flame-seal the DPP/Pb control',['dpp','pb-oleate','toluene-d8'],'Flame-sealed under vacuum',['dpp-volume','dpp-amount','pb-oleate-mass','pb-oleate-amount','toluene-d8-volume'],'synthesis',False),('heat_monitor','Heat in an oil bath and follow NMR',[],'Oil bath',['oil-bath-temperature'],'synthesis',False),('context','Record the incompletely specified Pb-metal challenge',[],None,[],'characterization',False)],
'dpp-cd-negative':[('heat_monitor','Prepare and monitor the Cd thermal control',['dpp','cd-oleate','toluene-d8'],'Analogous sealed-tube heating; several days',['dpp-volume','dpp-amount','cd-oleate-mass','cd-oleate-amount','toluene-d8-volume','inherited-bath-temperature'],'synthesis',False),('context','Record the reported absence of reaction',[],None,[],'characterization',False)],
'species9-crystallization':[('combine_stocks','Combine the two molecular-crystal stocks',[],'Room temperature',['dppse-stock-volume','dppse-stock-concentration','pb-oleate-stock-volume','pb-oleate-stock-concentration'],'synthesis',False),('evaporate','Allow slow evaporation and isolate species 9',[],'Several days; atmosphere not reported',[],'workup',True),('context','Retain the ratio-threshold discrepancy',[],None,[],'characterization',False)],
'pbse-qd':[('dissolve_add','Prepare the DPPSe solution and add oleic acid',['dppse','toluene','oa','n2'],'Nitrogen glovebox',['dppse-mass','dppse-amount','anhydrous-toluene-volume','oleic-acid-volume','oleic-acid-amount'],'precursor_preparation',False),('combine_stock','Combine with the Pb-oleate stock',[],'Stock solvent is not explicitly stated',['pb-oleate-stock-volume','pb-oleate-stock-concentration','pb-oleate-amount'],'synthesis',False),('seal_heat','Seal the cuvette and heat in an oil bath',[],'Teflon-sealable cuvette; sealed under nitrogen',['cuvette-optical-length','oil-bath-temperature'],'synthesis',False),('monitor','Monitor growth and the red optical example',[],None,['optical-example-heating-duration'],'characterization',False)],
'cdse-qd':[('heat_stock','Heat the Cd-oleate and oleic-acid stock',['n2'],'Flowing nitrogen; three-neck flask',['cd-stock-volume','cd-oleate-stock-concentration','cd-oleate-amount','oleic-acid-in-cd-stock','growth-temperature'],'precursor_preparation',False),('inject','Rapidly inject the DPPSe stock',[],'At the growth temperature; numeric injection duration not reported',['dppse-injection-stock-volume','dppse-stock-concentration','dppse-amount','oleic-acid-in-se-stock'],'synthesis',False),('monitor','Record formation and the blue optical example',[],None,['optical-example-heating-duration'],'characterization',False)]}
STOCKCOMP={'topse-neat':['topse','top-unspecified','unknown-p-impurities'],'topse-A':['topse','top-unspecified','dop','unknown-p-impurities'],'topse-B':['topse','top-unspecified','dop','unknown-p-impurities'],'topse-C':['topse','top-unspecified','dop','unknown-p-impurities'],'species9-dppse-stock':['dppse','toluene-grade-unspecified'],'species9-pb-stock':['pb-oleate','toluene-grade-unspecified'],'pbse-pb-stock':['pb-oleate'],'pbse-dppse-solution':['dppse','toluene','oa'],'cdse-cd-stock':['cd-oleate','ode','oa'],'cdse-dppse-stock':['dppse','ode','oa']}
SM={s['id']:s for s in I['stocks']}
def addstock(r,k):
 if any(s['id']==k for s in r['stocks']):return k
 s=SM[k];uid=s['source_unit_id'];components=[{'material_id':addmat(r,x),'quantities':{}} for x in STOCKCOMP[k]]
 conc={};amount=s.get('concentration_mol_L')
 if amount is not None:conc['solute_concentration']=qty(amount,'mol/L',E(uid),basis='Source stock concentration; not final mixture concentration.')
 x={'id':k,'name':k.replace('-',' '),'components':components,'concentrations':conc,'preparation_operation_ids':[],'scope':compact(s)+' Stock IDs distinguish formulations, not independently identified physical batches.','evidence':E(uid)}
 r['stocks'].append(x);bindu(r,uid,f'/stocks/{len(r["stocks"])-1}');OBJ.append({'category':'stocks','source_id':k,'record_id':r['record_id'],'pointer':f'/stocks/{len(r["stocks"])-1}'})
 return k
for k,p in P.items():
 r=R[k];previous=None;uid=p['source_unit_id']
 for j,(act,label,inputs,env,params,stage,retain) in enumerate(OPS[k]):
  ins=[addmat(r,x,stage) for x in inputs]
  if previous and act not in ['context','characterize']:ins.insert(0,previous)
  if k=='species9-crystallization' and j==0:ins += [addstock(r,x) for x in ['species9-dppse-stock','species9-pb-stock']]
  if k=='pbse-qd' and j==1:ins.append(addstock(r,'pbse-pb-stock'))
  if k=='cdse-qd':
   if j==0:ins.append(addstock(r,'cdse-cd-stock'))
   if j==1:ins.append(addstock(r,'cdse-dppse-stock'))
  oid=r['record_id']+'-op-'+str(j+1);out=oid+'-state';r['material_states'].append(state(out,label+' — resulting state',ins,kind='analysis_data' if stage=='characterization' else 'fraction' if retain else 'mixture'))
  op=operation(oid,act,label,E(uid),ins,[out],depends=[r['operations'][-1]['id']] if r['operations'] else [],stage=stage,description=p['steps'][j],environment=fact(env,E(uid)),retained_fraction=out if retain else None)
  for suffix in params:
   fid=uid+'-'+suffix;assert fid in F,fid;op['parameters'][norm(suffix).replace('-','_')]=q(F[fid]);bindf(r,fid,f'/operations/{j}/parameters/{norm(suffix).replace("-","_")}')
  if k=='pbse-msc-family' and j==1:
   op['optional_inputs']=[addstock(r,x) for x in ['topse-A','topse-B','topse-C']];op['description']+=' Choose one stock per variant. optional_inputs here denotes mutually exclusive alternatives; never combine all three.'
  if k=='topse-B-stock':
   op['optional_inputs']=[addmat(r,'topse'),addmat(r,'se')];op['description']+=' These optional inputs preserve conflicting source alternatives, not simultaneous TOPSe and selenium charges.'
  if k=='topse-distillation' and j==1:r['material_states'][-1]['kind']='sample_set';op['description']+=' The output state denotes three physically separate collected fractions, not a pooled solution.'
  if k=='tertiary-negative-rescue' and j==3:op['description']+=' No joint addition of TEPSe and TPPSe is implied.'
  r['operations'].append(op);bindu(r,uid,f'/operations/{j}');previous=out
 r['quality']['missing_fields']+=['No complete executable SOP is asserted.']
 sample(r,k,p['sample_scope'],FORM[k] if k not in ['dpp-cd-negative','topse-B-stock','topse-distillation'] else None,'explicit' if k in ['pbse-qd','cdse-qd','species9-crystallization'] else 'general_context',None,uid)
 if k=='topse':addstock(r,'topse-neat')
 if k=='pbse-qd':addstock(r,'pbse-dppse-solution')
 if k=='topse-distillation':
  for sk in ['topse-A','topse-C']:addstock(r,sk)
 if k=='topse-B-stock':addstock(r,'topse-B')
# Inheritance is a procedure relation only, not physical precursor consumption.
for k,p in P.items():
 for parent in p['explicit_inheritance']:R[k]['context_links'].append({'label':'Explicitly inherited procedure conditions','url':'/records/'+R[parent.removeprefix(SID+'-')]['record_id']+'.html','relation':'procedure_inheritance_not_physical_sample_lineage'})
# Every source context has a scientific claim; curated payloads remain losslessly in a private sidecar.
for uid,u in U.items():
 r=R[uk(uid)];sid=sample(r,uk(uid)+'-source-context',u['sample_scope'],FORM.get(uk(uid)),uid=uid)
 m=measurement(norm(uid)+'-context',sid,'source_context',fact(u['claim'],E(uid),note='Original classification: '+u['kind']+'; original status: '+u['status']+'. Source scope: '+u['sample_scope']+'.'),'Source text / original object',E(uid))
 r['measurements'].append(m);bindu(r,uid,f'/measurements/{len(r["measurements"])-1}/value')
 for c in I['source_conflicts']:
  if c['id'] in u.get('conflict_ids',[]) and c['id']+': '+c['issue'] not in r['quality']['conflicts']:r['quality']['conflicts'].append(c['id']+': '+c['issue'])
def leaves(v,p=''):
 if v==[] or v=={}:yield p,v
 elif isinstance(v,dict):
  for k,x in v.items():yield from leaves(x,p+'/'+esc(k))
 elif isinstance(v,list):
  for j,x in enumerate(v):yield from leaves(x,p+'/'+str(j))
 else:yield p,v
# Complete typed source facts, including every CIF cell. Raw token/line metadata lives in the lossless map.
for fid,f in F.items():
 r=R[uk(f['source_unit_id'])];sid=sample(r,norm(f['sample_scope']),f['sample_scope'],None,uid=f['source_unit_id'])
 if f['source_unit_id'].startswith('evans2010-cif-loop-'):
  vals=[(f'/rows/{i}/{esc(tag)}/value',cell['value']) for i,row in enumerate(f['value']['rows']) for tag,cell in row.items()]
 else:vals=list(leaves(f['value']))
 for n,(sub,v) in enumerate(vals):
  val=q(f,sub);mid=norm(fid)+('-field-'+str(n+1) if sub else '')
  m=measurement(mid,sid,norm(f['property']+sub).replace('-','_'),val,'Original CIF refinement field' if f['source_unit_id'].startswith('evans2010-cif-') else 'Source-reported or explicitly classified context',E(f['source_unit_id']),conditions='Exact source scope: '+f['sample_scope']+'. '+f.get('qualifier',''))
  r['measurements'].append(m);ptr=f'/measurements/{len(r["measurements"])-1}/value';bindf(r,fid,ptr,sub);bindu(r,f['source_unit_id'],ptr)
# Preserve selected microscopy specimen boundaries explicitly; image bars remain scale bars.
for sx in I['sample_lineage']:
 if sx['id'] in P:r=R[sx['id']]
 elif sx['id'].startswith('msc-'):r=R['pbse-msc-family']
 elif sx['id'].startswith('cd-ratio-'):r=R['cd-ratios']
 elif sx['id']=='cd-timecourse':r=R['cd-timecourse']
 elif sx['id']=='pb-ratio-1to1':r=R['pb-ratio']
 elif sx['id']=='topse-dpp15':r=R['topse-dpp15']
 elif sx['id']=='species9-cif':r=R['molecular9-structure']
 elif sx['id'].startswith('pbse-tem-'):r=R['pbse-tem']
 else:r=R['pbse-conversion']
 sid=sample(r,sx['id'],sx['label'],None,uid=sx['source_unit_ids'][0]);p=next(x for x in r['products'] if x['sample_id']==sid);p['notes']+=sx['limits'];OBJ.append({'category':'sample_lineage','source_id':sx['id'],'record_id':r['record_id'],'pointer':f'/products/{r["products"].index(p)}'})
R['molecular9-structure']['quality']['missing_fields']+=['Molecular species 9 only. Original CIF has a nonstandard prefix and is not provided as a repaired public asset. Calculated riding hydrogens are not independently located atoms.']
R['pbse-conversion']['quality']['missing_fields']+=['The 2.25 µmol / 3.025 mL example is not established as the 10 µmol / approximately 4 mL S19 recipe specimen.']
R['pbse-tem']['quality']['missing_fields']+=['Exact synthesis time and physical batch links for the spherical and cubic examples are unreported. No mean diameter is extracted from the 5 nm / 50 nm image bars.']
for k in ['cd-ratios','cd-timecourse']:R[k]['quality']['missing_fields']+=['Same nominal composition does not prove the same physical specimen between S8 and S10. S11 explicitly refers to the S10 late sample.']
for k,r in R.items():
 if k!='source-context':r['context_links'].append({'label':'Complete supplied source and limitations','url':'/paper-review.html?id=evans2010','relation':'source_reader_pending_independent_audit'})
errors=[e for r in R.values() for e in validate_record(r)]
assert not errors,errors[:30]
assert all(UL.values()) and all(FL.values()),{'units':[u for u,v in UL.items() if not v],'facts':[f for f,v in FL.items() if not v]}
groups=build_groups(list(R.values()));assert len(set(groups.values()))==1
assert not any(v['eligible'] for r in R.values() for v in eligibility(r).values())
recs=[]
for r in R.values():
 fn=r['record_id']+'.json';save(fn,r);recs.append({'record_id':r['record_id'],'path':str(O/fn),'sha256':sha(O/fn),'record_type':r['record_type']})
COV={'source_freeze_sha256':sha(B/'source-extraction-revision-2/source-extraction-freeze.json'),'facts':[{'source_fact_id':f,'canonical_bindings':v} for f,v in FL.items()],'source_units':[{'source_unit_id':u,'canonical_bindings':v} for u,v in UL.items()],'source_objects':OBJ,'source_value_transport':'All scalar facts and every CIF loop cell value are typed fields. Full raw source-fact objects with tokens/line locators and all curated inventory payloads are retained in private lossless-source-map.json; these private payloads are not public article/SI text caches.'}
save('source-to-field-coverage.json',COV)
save('lossless-source-map.json',{'source_freeze_sha256':sha(B/'source-extraction-revision-2/source-extraction-freeze.json'),'facts':D['facts'],'units':I['units'],'materials':I['materials'],'stocks':I['stocks'],'sample_lineage':I['sample_lineage'],'procedures':I['procedures'],'tables':I['tables'],'equations':I['equations'],'references':I['references'],'source_conflicts':I['source_conflicts'],'missingness':I['missingness'],'private_only':True})
checks=0
for fid,links in FL.items():
 for a in links:
  r=next(r for r in R.values() if r['record_id']==a['record_id']);assert resolve(r,a['pointer'])==q(F[fid],a['source_value_pointer']);checks+=1
for uid,links in UL.items():
 for a in links:assert resolve(next(r for r in R.values() if r['record_id']==a['record_id']),a['pointer']) is not None;checks+=1
for x in FREEZE['files']:assert sha(x['path'])==x['sha256'];checks+=1
counts={'records':len(R),'synthesis_route_families':3,'supporting_preparation_control_families':13,'observation_context_records':len(R)-16,'operations':sum(len(r['operations']) for r in R.values()),'materials':sum(len(r['materials']) for r in R.values()),'stocks':sum(len(r['stocks']) for r in R.values()),'products_or_contexts':sum(len(r['products']) for r in R.values()),'measurements':sum(len(r['measurements']) for r in R.values()),'source_facts':len(F),'source_fact_bindings':sum(map(len,FL.values())),'source_units':len(U),'source_unit_bindings':sum(map(len,UL.values())),'source_groups':1,'training_rows':0,'exact_qd_structure_pairs':0}
save('author-validation.json',{'status':'passed_author_schema_and_transport_checks','checks':checks,'counts':counts,'schema_errors':errors,'source_freeze_unchanged':True,'independent_scientific_audit':'pending','reader_visual_browser_publication':'pending','record_hashes':{x['record_id']:x['sha256'] for x in recs}})
save('record-manifest.json',{'schema':'mattersyn-private-canonical-proposal/1','source_id':SID,'version':2,'created_at':datetime.now(timezone.utc).isoformat(),'author':'/root/norberg2004_extract','status':'author_draft_pending_source_and_canonical_audits','source_freeze_sha256':sha(B/'source-extraction-revision-2/source-extraction-freeze.json'),'records':recs,'counts':counts,'coverage_sha256':sha(O/'source-to-field-coverage.json'),'validation_sha256':sha(O/'author-validation.json'),'author_script_sha256':sha(__file__)})
print(json.dumps(counts));print('MANIFEST',sha(O/'record-manifest.json'))
