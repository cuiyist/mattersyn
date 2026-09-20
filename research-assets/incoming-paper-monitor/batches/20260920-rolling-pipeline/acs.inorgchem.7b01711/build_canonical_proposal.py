"""Private Morrison canonical author proposal. Site and frozen source are read-only."""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import json,hashlib,re,sys
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent
O=P/'canonical-proposal'/'v1';O.mkdir(parents=True,exist_ok=True)
S=Path('[local path redacted]')
sys.path.insert(0,str(S/'scripts'))
from record_helpers import record,source,fact,qty,material,operation,state,product,measurement
from dataset_lib import validate_record,eligibility,build_groups
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,x):(O/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def norm(x):return re.sub('[^a-z0-9]+','-',str(x).lower()).strip('-')
def key(x):return norm(x).replace('-','_')
def esc(x):return str(x).replace('~','~0').replace('/','~1')
def resolve(x,p):
 for t in p.strip('/').split('/')if p else []:x=x[int(t)]if isinstance(x,list)else x[t.replace('~1','/').replace('~0','~')]
 return x
def compact(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'))
D=read(P/'source-facts.json');I=read(P/'source-inventory.json');FR=read(P/'package-freeze.json')
AUDIT_PATH=P/'source-independent-audit'/'independent-audit-v2.json';AUDIT=read(AUDIT_PATH)
assert AUDIT['status']=='passed'and AUDIT['package_freeze_sha256']==sha(P/'package-freeze.json')and AUDIT['source_facts_sha256']==sha(P/'source-facts.json')
assert sha(P/'package-freeze.json')=='3b261b2f0aec35ab5fd9452fa8a9fee87ece32d87ef9ef2b29e617d70a74ccc8'
for path,digest in FR['bound_files'].items():assert sha(path)==digest,path
SID='morrison2017';PRE='morrison-2017-';R={};FM={f['id']:f for f in D['facts']};MM={m['id']:m for m in D['materials']};PP={p['id']:p for p in D['protocols']};UU={u['id']:u for u in I['source_units']}
CON={c['id']:c for c in D['contradictions']};GAP={g['id']:g for g in D['gaps']}
FL={f:[]for f in FM};UL={u:[]for u in UU};TL={};OBJECTS=[];TABLEMETA=[]
def E(es):
 return [{'source_id':SID,'locator':e['document_role'].upper()+' PDF p. '+str(e['pdf_page'])+' (printed '+str(e['printed_page'])+'), '+e['locator']+'; source SHA256 '+e['source_sha256']}for e in es]
def FE(short):return E(FM[SID+'-'+short]['evidence'])
def link(category,source_id,r,pointer,source_pointer=None):
 row={'record_id':r['record_id'],'pointer':pointer}
 if source_pointer is not None:row['source_pointer']=source_pointer
 if category=='fact':FL[source_id].append(row)
 elif category=='unit':UL[source_id].append(row)
 elif category=='table_cell':TL.setdefault(source_id,[]).append(row)
 else:OBJECTS.append({'category':category,'source_id':source_id,**row})
def conflict_note(ids):return ' '.join(i+': '+(CON[i]['description']if i in CON else GAP[i]['description']if i in GAP else i)for i in ids)
SRC=source(SID,D['doi'],D['title'],'; '.join(D['authors']),2017,si='Matched 17-page SI read and visually inspected; distinct source audit passed corrected revision 2. Canonical/reader review remains pending.')
SRC['main_status']='All 10 main pages read and visually inspected; independent source audit passed revision 2. Canonical and reader audits remain separate pending gates.'
SRC['reuse_status']='Private proposal. Selected-original public reuse and complete-source exclusion remain separately gated.'
COMMON=['Private canonical author proposal; independent source audit passed separately, while canonical/reader review remains pending.','No complete executable laboratory SOP is asserted.','Upstream NH4PTC and starting CdSe-belt preparations are cited rather than supplied in full.','No supplied CdSe/CdS product atomic coordinates; precursor crystal tables do not establish a product structure.','Physical batch identity is not inferred across TEM, XRD, elemental and optical contexts.']
CONFIG={
 'precursor-preparation':('Aqueous preparation of Cd(PTC)₂','C14H12CdN2S4','procedure'),
 'precursor-crystallization':('THF/hexane precursor crystallization','C18H20CdN2OS4','procedure'),
 'decomposition-nmr':('DMSO-d₆ conversion and isolated powder control','CdS','procedure'),
 'decomposition-thf':('THF standalone CdS powder control','CdS','procedure'),
 'decomposition-dmso-hot':('Partially specified hot-DMSO powder control','CdS','procedure'),
 'excess-precursor-rt':('Room-temperature precursor exposure and back exchange','CdSe/CdS','procedure'),
 'excess-precursor-hot':('Excess-precursor thick-shell growth','CdSe/CdS','literature_protocol'),
 'monolayer-shell':('Controlled monolayer CdS shell growth','CdSe/CdS','literature_protocol'),
 'added-base-comparison':('Added-base NMR comparison','Cd(PTC)2 conversion','procedure'),
 'single-crystal-acquisition':('Precursor single-crystal acquisition and tabulated structure','C18H20CdN2OS4','procedure'),
 'reagents-methods':('Complete reagent inventory and analytical methods','Study materials','observation'),
 'starting-belt-reference':('Cited starting-belt structure and ligation','CdSe','observation'),
 'precursor-properties':('Precursor identity, spectra and solution behavior','C14H12CdN2S4','observation'),
 'thick-shell-characterization':('Excess-precursor product characterization','CdSe/CdS','observation'),
 'monolayer-characterization':('Monolayer optical, diffraction and microscopy contexts','CdSe/CdS','observation'),
 'powder-comparison':('Separate standalone-powder XRD and EDS contexts','CdS','observation'),
 'mechanistic-context':('Proposed pathways, ligation model and qualitative failures','CdSe/CdS and precursor conversion','observation'),
 'source-context':('Source identity, references and limitations','Study context','observation')}
for k,(title,formula,kind)in CONFIG.items():
 method=PP[k]['title']if k in PP else title
 r=record(PRE+k,'Morrison et al. (2017) · '+title,formula,'Cadmium dithiocarbamate precursor and CdSe/CdS quantum belts',method,deepcopy(SRC),'Complete main and matched SI; exact fields carry individual locators',kind)
 r['schema_version']='1.3.0';r['lineage'].update(source_group=SID,recipe_family=SID+'-precursor-shell-study')
 r['quality'].update(review_status='imported_unreviewed',requested_tasks=[],review_scope='Private canonical author draft based on source revision 2, independently source-audited by /root/peng1998_reader_assets. No independent canonical/reader approval, training admission, exact structure pairing or publication is asserted.',missing_fields=COMMON.copy(),conflicts=[],experimental_outcome='not_established')
 r['intended_target']['composition']=fact(formula if k in PP and k not in ['single-crystal-acquisition','added-base-comparison','excess-precursor-rt']else None,E(PP[k]['operations'][0]['evidence'])if k in PP else FE('ambient'),note='Only a reported preparation identifies a target; observation and model contexts do not create synthetic runs.')
 if formula=='CdSe/CdS':r['material'].update(elements=['Cd','Se','S'],components=['CdSe','CdS'],architecture='core_shell'if k!='excess-precursor-rt'else'unresolved')
 R[k]=r
def owner(f):
 short=f['id'].removeprefix(SID+'-')
 if short.startswith('instrument-')or short in ['ambient','as-received']:return'reagents-methods'
 if short in ['starting-facet-model','starting-amine-model','prior-oleate-stoichiometry','prior-oleate','core-dimensions']:return'starting-belt-reference'
 if short=='upstream':return'source-context'
 if short in ['precursor-charge','precursor-workup','precursor-yield','precursor-yield-results']:return'precursor-preparation'
 if short in ['crystal-growth']:return'precursor-crystallization'
 if short in ['crystal-mount','crystal-refine','crystal-electronic-gap','polymer-structure','geometry-prose','ccdc']:return'single-crystal-acquisition'
 if short.startswith('precursor-')or short in ['solubility','si-ir']:return'precursor-properties'
 if short in ['nmr-charge','nmr-powder-isolate','nmr-evolution','nmr-normalized','si-hnmr','si-cnmr']:return'decomposition-nmr'
 if short=='thf-powder':return'decomposition-thf'
 if short=='dmso-powder':return'decomposition-dmso-hot'
 if short in ['rt-excess','rt-shift','si-dispersibility']:return'excess-precursor-rt'
 if short in ['hot-excess']:return'excess-precursor-hot'
 if short in ['hot-pl','thick-morphology','si-sulfur-model']:return'thick-shell-characterization'
 if short in ['qb-purify','qb-grow','qb-aliquot','qb-optical-wash','monolayer-dose']:return'monolayer-shell'
 if short in ['catalyst-identity','base-rate','si-base']:return'added-base-comparison'
 if short in ['monolayer-optics','xrd-orientation','c-compression','tem-prep','tem-thickness','monolayer-interp']:return'monolayer-characterization'
 if short in ['powder-eds-prose','si-powder-lattice','si-eds']:return'powder-comparison'
 if short in ['mechanism','surface-model','literature-context','failed-options','outlook']:return'mechanistic-context'
 if short=='version-note':return'source-context'
 raise KeyError(short)
OWN={fid:owner(f)for fid,f in FM.items()}
SCOPE_FORM={'precursor-powder':'C14H12CdN2S4','precursor-crystal':'C18H20CdN2OS4','precursor-solution':'Cd(PTC)2; solution nuclearity unknown','cited-starting-qb-model':'CdSe','cited-ligation-model':'CdSe with cited ligation','powder-thf':'CdS','powder-dmso-hot':'CdS','powder-dmso-nmr':'CdS','powder-solvent-controls':'CdS','monolayer-shell-family':'CdSe/CdS','monolayer-optical-aliquots':'CdSe/CdS','monolayer-tem-context':'CdSe/CdS','excess-shell-family':'CdSe/CdS','excess-shell-hot':'CdSe/CdS','excess-shell-rt':'CdSe with precursor exposure; extent unresolved'}
def sample(r,scope,es):
 sid=norm(scope)
 if not any(p['sample_id']==sid for p in r['products']):
  pp=product(sid,SCOPE_FORM.get(scope),E(es),link='general_context',notes=['Source context: '+scope+'.','No author-assigned batch identifier or universal cross-technique specimen link is supplied.','This context does not count a replicate, aliquot series point or independent experiment.'])
  phases={'precursor-crystal':('monoclinic; P21/n',D['tables'][4]['evidence']),'cited-starting-qb-model':('wurtzite',FM[SID+'-starting-facet-model']['evidence']),'excess-shell-family':('wurtzite diffraction assignment',next(f['evidence']for f in D['figures']if f['id']=='figure-5')),'monolayer-shell-family':('wurtzite diffraction assignment',next(f['evidence']for f in D['figures']if f['id']=='figure-8')),'powder-thf':('wurtzite',next(f['evidence']for f in D['figures']if f['id']=='figure-s6')),'powder-dmso-hot':('wurtzite',FM[SID+'-dmso-powder']['evidence'])}
  if scope in phases:
   phase,pev=phases[scope];pp['phase']=fact(phase,E(pev),note='Source-family or cited-reference assignment. No measured atomic coordinates or universal physical-batch identity is implied.')
  if scope.startswith('monolayer-')or scope in ['excess-shell-family','excess-shell-hot','cited-starting-qb-model']:
   pp['morphology']=fact('quantum belts',E(es),note='Source context retains the belt morphology; microscopy size and reference-core dimensions remain separate quantitative observations.')
  pp['source_sample_label']=scope;r['products'].append(pp)
  link('sample_context',scope,r,f'/products/{len(r["products"])-1}')
 return sid
def Q(qv,scope='',extra=''):
 es=E(qv['evidence']);note=' '.join([extra,conflict_note(qv.get('conflict_ids',[]))]).strip()
 basis='Source scope: '+scope+'. Printed-to-value scale: '+str(qv.get('printed_to_value_scale',1))+'.'
 if qv.get('uncertainty')is not None:note+=' Reported standard uncertainty after printed scaling: '+str(qv['uncertainty'])+' '+str(qv['unit'])+'.'
 val=qv['value'];lo=(qv.get('range')or{}).get('min');hi=(qv.get('range')or{}).get('max');cmp=qv.get('comparison')
 if cmp in ['<','<=']:hi=val;val=None
 if cmp in ['>','>=']:lo=val;val=None
 if qv['status']in ['reported_text','reported_identifier']:
  return fact(qv['raw_text'],es,note=basis+' '+note)
 status='not_reported'if val is None and lo is None and hi is None else'reported'
 return qty(val,qv['unit']or'',es,status,minimum=lo,maximum=hi,approximate=qv.get('approximate',False),qualifier=note.strip(),basis=basis,raw_text=qv['raw_text'],minimum_exclusive=cmp=='>'if cmp in ['>','>=']else None,maximum_exclusive=cmp=='<'if cmp in ['<','<=']else None)
def addm(r,mid,stage='characterization'):
 if any(m['id']==mid for m in r['materials']):return mid
 src=MM[mid]
 role='metal_precursor'if mid in ['cdcl2','cdptc']else'chalcogen_precursor'if mid=='nh4ptc'else'seed'if mid=='cdse-qb'else'solvent'if mid in ['water','ethanol','thf','hexane','dmso-d6','thf-d8','dmso','toluene','dmf','methanol','chloroform','dichloromethane']else'ligand'if mid=='n-octylamine'else'catalytic_base'if mid=='aniline'else'characterization_support'if mid in ['tem-grid','xrd-substrate']else'reference_material'if mid.endswith('-reference')else'observed_product_or_intermediate'
 mat=material(mid,src['name'],src['source_formula_or_abbreviation'],role,stage,E(src['evidence']),notes=[src['scope_note'],'Original role: '+src['role']+'.','A condensed formula/name does not qualify a molecular or atomistic depiction.'])
 r['materials'].append(mat);link('material',mid,r,f'/materials/{len(r["materials"])-1}');return mid
for mid in MM:addm(R['reagents-methods'],mid)
STAGES={
 'precursor-add':'precursor_preparation','precursor-stir-filter':'workup','precursor-wash-dry':'workup','crystal-solution':'precursor_preparation','crystal-vapor':'workup',
 'nmr-heat':'synthesis','nmr-isolate':'workup','thf-heat':'synthesis','thf-wash':'workup','dmso-hot':'synthesis','rt-combine':'surface_exchange','rt-backexchange':'surface_exchange',
 'hot-growth':'synthesis','hot-backexchange':'surface_exchange','qb-wash':'workup','qb-shell':'synthesis','qb-sample':'characterization','aliquot-thf':'workup','aliquot-repassivate':'surface_exchange','aliquot-toluene-wash':'workup','aliquot-optics':'characterization','qb-tem':'characterization','base-nmr':'characterization','crystal-mount-measure':'characterization'}
LABELS={'precursor-add':'Dissolve the salts and add the cadmium solution dropwise','precursor-stir-filter':'Stir for 30 min and recover the precipitate','precursor-wash-dry':'Wash with cold water and ethanol, then vacuum dry','crystal-solution':'Prepare the ambiguously quantified THF crystallization solution','crystal-vapor':'Leave the sealed THF/hexane vapor-diffusion assembly overnight','nmr-heat':'Heat the DMSO-d₆ sample and acquire the NMR time series','nmr-isolate':'Recover the yellow solid and prepare the XRD specimen','thf-heat':'Heat the septum-capped THF precursor solution','thf-wash':'Wash the THF-derived solid and prepare the XRD specimen','dmso-hot':'Heat the incompletely specified DMSO powder control','rt-combine':'Expose starting belts to saturated precursor in DMSO','rt-backexchange':'Remove excess precursor and redisperse in neat n-octylamine','hot-growth':'Grow thick shells with excess precursor at 70 °C','hot-backexchange':'Redisperse the resulting thick-shell belts in n-octylamine','qb-wash':'Remove excess amine using three precipitate-retaining washes','qb-shell':'Heat the washed belts in the THF precursor solution','qb-sample':'Take aliquots at the specified reaction times','aliquot-thf':'Dilute an aliquot with THF and recover its precipitate','aliquot-repassivate':'Repassivate the recovered aliquot with n-octylamine','aliquot-toluene-wash':'Wash the repassivated aliquot with toluene','aliquot-optics':'Disperse the washed aliquot for UV–visible and PL measurements','qb-tem':'Prepare a separate microscopy context from the shell-growth family','base-nmr':'Compare conversion with and without added aniline','crystal-mount-measure':'Mount the precursor crystal and acquire single-crystal diffraction'}
for pid,pr in PP.items():
 r=R[pid];produced={}
 for j,srcop in enumerate(pr['operations']):
  ins=[];stage=STAGES[srcop['id']]
  for mid in srcop['inputs']:
   if mid in MM:ins.append(addm(r,mid,stage))
   else:
    assert mid in produced,(pid,mid);ins.append(mid)
  for out in srcop['outputs']:
   kind='analysis_data'if 'time-series'in out else'aliquot'if 'aliquot'in out else'sample_set'if 'family'in out else'fraction'if srcop['retained_fraction']==out else'mixture'
   r['material_states'].append(state(out,out.replace('-',' '),ins,kind))
  phase_prose={
   'precursor-add':'Prepare separate aqueous CdCl2 and NH4PTC solutions. Add the cadmium solution dropwise to the continuously stirred ligand solution; a white precipitate begins to form immediately.',
   'precursor-stir-filter':'Stir the combined suspension for 30 min, then vacuum filter and retain the precipitate.',
   'precursor-wash-dry':'Wash the retained precipitate with ice-chilled deionized water and three ice-chilled ethanol portions, then dry under vacuum for 1 h. The printed isolated mass, amount and yield are retained as product observations in separate fields.',
   'crystal-solution':'Place the printed “20 mmol solution” of Cd(PTC)2 in THF in a small vial. Neither a solvent volume nor a concentration denominator is reported.',
   'crystal-vapor':'Place the vial within a larger hexane-containing jar, seal, and leave undisturbed overnight. The source reports pale-yellow spindling crystals; no numerical duration is supplied.',
   'nmr-heat':'Dissolve the reported precursor charge in DMSO-d6 and heat at 50 °C. Acquire NMR spectra every 60 min over 12 h. Species appearance and disappearance are observations, not recipe inputs.',
   'nmr-isolate':'Separate the bright-yellow solid by benchtop centrifugation, wash it three times with toluene, and deposit it on an unspecified XRD substrate. The speed, time and drying details are not reported.',
   'thf-heat':'Dissolve the reported precursor charge in THF in a septum-capped vial and heat at 66 °C. The heating duration is not supplied.',
   'thf-wash':'Wash the THF-derived yellow product with three toluene portions and deposit it for XRD. Its initial separation and drying procedures are not stated.',
   'dmso-hot':'Heat the precursor in DMSO without CdSe belts at 70 °C. Yellow solid appears within 1 h and conversion appears complete after about 4 h. These are narrative reaction observations; precursor and solvent charges are unreported.',
   'rt-combine':'Combine the starting amine-ligated belts with excess saturated Cd(PTC)2 in DMSO at room temperature. The absolute belt charge, solution volume and numerical room temperature are unknown.',
   'rt-backexchange':'Remove excess precursor using an unspecified procedure, then redisperse the exposed belts in neat n-octylamine. The amount and duration are not supplied.',
   'hot-growth':'Heat the excess-precursor belt mixture at 70 °C. The reported orange and red color changes mark observed progress; they are not independently specified stopping criteria.',
   'hot-backexchange':'Redisperse the thick-shell belts in n-octylamine. The recovery method, amine amount and treatment duration are unreported.',
   'qb-wash':'Add toluene to the 0.512 g starting dispersion aliquot, centrifuge, discard the supernatant, and retain the belt precipitate. Repeat twice for three total washes; the dispersion mass is not a dry CdSe mass.',
   'qb-shell':'Suspend the washed belts in the Cd(PTC)2/THF solution and heat at 66 °C. The source reports 3 h as ideal and 1.0–1.5 times an estimated monolayer requirement, but does not supply the core-concentration or surface-area calculation.',
   'qb-sample':'Remove 2–3-drop aliquots at 1, 2, 3, 4 and 16 h. These are time-course samples from the reaction family, not five independent synthesis protocols.',
   'aliquot-thf':'Dilute a collected aliquot with THF, centrifuge, discard the supernatant and retain the precipitate.',
   'aliquot-repassivate':'Resuspend the retained aliquot in n-octylamine for L-type repassivation. The amine volume and treatment duration are not reported.',
   'aliquot-toluene-wash':'Add toluene, centrifuge and retain the precipitate. Repeat washing to remove amine; the number of repeats for this stage is not specified.',
   'aliquot-optics':'Finally suspend the washed precipitate in toluene for UV–visible and PL measurements. The final dispersion volume and concentration are unreported.',
   'qb-tem':'Redisperse core–shell belts in n-octylamine and deposit on a copper grid with carbon film. This separate microscopy context does not establish an exact physical-aliquot link to the optical measurement sample.',
   'base-nmr':'Compare precursor conversion with and without added aniline at 50 °C in DMSO. The main p. 5 n-octylamine wording conflicts with the later aniline description. The added base amount is unreported.',
   'crystal-mount-measure':'Mount a precursor crystal on a MiTeGen cryoloop and collect single-crystal diffraction using the stated Bruker/Oxford apparatus and Mo Kα radiation. Refine the precursor structure using the reported protocol; no external CIF has been supplied or reconstructed.'}
  op=operation(srcop['id'],key(srcop['id']),LABELS[srcop['id']],E(srcop['evidence']),ins,srcop['outputs'],depends=list(dict.fromkeys(produced[i]for i in srcop['inputs']if i in produced)),stage=stage,branch=pid,description=phase_prose[srcop['id']],environment=fact('Ambient conditions unless otherwise specified; heating conditions are separately typed.',FE('ambient'),note='Ambient is not a numerical room-temperature setting or a specified gas atmosphere.'),retained_fraction=srcop['retained_fraction'])
  for qv in srcop['quantities']:
   phase_allowed={'precursor-wash-dry':{'water wash','ethanol wash cycles','ethanol each wash','vacuum drying'},'nmr-heat':{'precursor mass','printed precursor amount','DMSO-d6 mass','temperature','spectrum interval','monitoring period'},'dmso-hot':{'temperature'},'rt-combine':{'saturated concentration'},'rt-backexchange':set(),'hot-growth':{'temperature'},'aliquot-optics':set(),'qb-tem':set()}
   if srcop['id']in phase_allowed and qv['meaning']not in phase_allowed[srcop['id']]:continue
   val=Q(qv,pr['title'],'This field retains its stated meaning: charge, process setting, time-course point or observed endpoint. It is not automatically a requested target.')
   if 'unit'not in val:continue
   op['parameters'][key(qv['meaning'])]=val
   for fid in srcop['source_fact_ids']:
    for nq,orig in enumerate(FM[fid]['quantities']):
     if qv==orig:link('fact',fid,r,f'/operations/{j}/parameters/'+esc(key(qv['meaning'])),'/quantities/'+str(nq))
  op['description']+=' Missing fields for this phase: '+(', '.join(srcop['missing_fields'])or'none specifically listed')+'. '+conflict_note(srcop['conflict_ids'])
  if srcop['id']=='qb-tem':op['description']+=' This microscopy branch consumes the shell-growth family directly; it does not consume the final optical dispersion or establish its physical aliquot identity.'
  r['operations'].append(op)
  for out in srcop['outputs']:produced[out]=srcop['id']
  link('unit',pid,r,f'/operations/{j}');link('operation',srcop['id'],r,f'/operations/{j}')
  r['quality']['missing_fields']+=srcop['missing_fields']
  r['quality']['conflicts']+=[conflict_note([cid])for cid in srcop['conflict_ids']]
# Stocks preserve reported formulations. Their presence does not add a second physical charge.
STOCK_OWNER={'cdcl2-aqueous':'precursor-preparation','nh4ptc-aqueous':'precursor-preparation','cdptc-thf-shell':'monolayer-shell','cdptc-dmso-excess':'excess-precursor-rt','cdptc-thf-crystal-feed':'precursor-crystallization'}
for st in D['stocks']:
 r=R[STOCK_OWNER[st['id']]];f=FM[st['source_fact_id']]
 comps=[{'material_id':addm(r,m,'precursor_preparation'),'quantities':{}}for m in [st['solute'],st['solvent']]]
 concentrations={'solute_concentration':Q(st['concentration'],st['scope'])}if st.get('concentration')else{}
 row={'id':st['id'],'name':st['id'].replace('-',' '),'components':comps,'concentrations':concentrations,'preparation_operation_ids':[],'scope':st['scope']+' This is the solution formulation already described by the linked operation, not an additional charge or independently prepared batch.','evidence':E(f['evidence'])}
 r['stocks'].append(row);link('stock',st['id'],r,f'/stocks/{len(r["stocks"])-1}')
# Every claim and every scalar/range quantity receives a typed canonical field.
for fid,f in FM.items():
 r=R[OWN[fid]];sid=sample(r,f['sample_scope'],f['evidence']);ev=E(f['evidence'])
 note='Source classification: '+f['claim_class']+'. '+conflict_note(f['conflict_ids']+f['gap_ids'])
 claim=measurement(fid+'-claim',sid,'source_claim',fact(f['claim'],ev,note=note),'Source text with claim classification',ev,conditions=f['sample_scope'])
 r['measurements'].append(claim);ptr=f'/measurements/{len(r["measurements"])-1}/value';link('fact',fid,r,ptr,'/claim');link('unit',fid,r,ptr)
 for nq,qv in enumerate(f['quantities']):
  m=measurement(fid+'-q'+str(nq+1),sid,key(qv['meaning']),Q(qv,f['sample_scope'],note),'Source-reported quantity; source scope retained',ev,conditions='Uncertainty, bounds, source conflicts and reference/model status remain explicit.')
  r['measurements'].append(m);ptr=f'/measurements/{len(r["measurements"])-1}/value';link('fact',fid,r,ptr,'/quantities/'+str(nq));link('unit',fid,r,ptr)
 r['quality']['conflicts']+=[conflict_note([cid])for cid in f['conflict_ids']]
TABLE_OWNER={t['id']:'single-crystal-acquisition'if t['sample_scope']=='precursor-crystal'else'thick-shell-characterization'if t['id']=='table-s5'else'powder-comparison'for t in D['tables']}
TABLE_CONFLICTS={'table-1':[],'table-2':['C10'],'table-s5':[],'figure-s7-eds-table':['C7','C9']}
for t in D['tables']:
 r=R[TABLE_OWNER[t['id']]];sid=sample(r,t['sample_scope'],t['evidence']);extra=conflict_note(TABLE_CONFLICTS.get(t['id'],[]))
 if t['sample_scope']=='precursor-crystal':extra+=' Coordinates and displacement parameters belong to the THF-solvated precursor, not to CdSe/CdS belts. No qualified CIF or atomic viewer is created.'
 meta={k:deepcopy(t[k])for k in ['id','title','sample_scope','columns','notes','evidence']}
 m=measurement(t['id']+'-definition',sid,'table_definition',fact(compact(meta),E(t['evidence']),note=extra),'Source table definitions and notes',E(t['evidence']))
 r['measurements'].append(m);ptr=f'/measurements/{len(r["measurements"])-1}/value';link('unit',t['id'],r,ptr);TABLEMETA.append({'table_id':t['id'],'record_id':r['record_id'],'pointer':ptr})
 for row in t['rows']:
  for c in row['cells']:
   column=c.get('column','value')
   m=measurement(c['id'],sid,key(t['id']+' '+row['row_label']+' '+column),Q(c,t['sample_scope'],extra),'Printed table cell',E(c['evidence']),conditions='Row '+row['row_label']+'; column '+column+'.')
   r['measurements'].append(m);ptr=f'/measurements/{len(r["measurements"])-1}/value';link('table_cell',c['id'],r,ptr);link('unit',t['id'],r,ptr)
 r['quality']['conflicts']+=[conflict_note([cid])for cid in TABLE_CONFLICTS.get(t['id'],[])]
FIG_OWNER={'graphical-abstract':'mechanistic-context','figure-1':'starting-belt-reference','figure-2':'single-crystal-acquisition','figure-3':'thick-shell-characterization','figure-4':'thick-shell-characterization','figure-5':'thick-shell-characterization','figure-6':'decomposition-nmr','figure-7':'monolayer-characterization','figure-8':'monolayer-characterization','figure-9':'monolayer-characterization','figure-s1':'precursor-properties','figure-s2':'decomposition-nmr','figure-s3':'decomposition-nmr','figure-s4':'single-crystal-acquisition','figure-s5':'excess-precursor-rt','figure-s6':'powder-comparison','figure-s7':'powder-comparison','figure-s8':'added-base-comparison','figure-s9-ab':'monolayer-characterization','figure-s9-c':'monolayer-characterization'}
for f in D['figures']:
 r=R[FIG_OWNER[f['id']]];sid=sample(r,f['sample_scope'],f['evidence']);ev=E(f['evidence'])
 mm=measurement(f['id']+'-context',sid,'figure_context',fact(f['title']+'. '+f['scientific_scope'],ev,note='Original excerpt and labels are retained. No raw-curve digitization or exact cross-technique batch identity inferred.'),'Original figure/caption',ev)
 r['measurements'].append(mm);link('unit',f['id'],r,f'/measurements/{len(r["measurements"])-1}/value')
for s in D['schemes']:
 r=R['starting-belt-reference'if s['id']=='scheme-1'else'mechanistic-context'];sid=sample(r,s['sample_scope'],s['evidence']);ev=E(s['evidence'])
 r['measurements'].append(measurement(s['id']+'-context',sid,'proposed_or_cited_scheme',fact(s['title']+'. '+s['scope_note'],ev,note='Author or cited model; not a measured atomic structure.'),'Source scheme',ev));link('unit',s['id'],r,f'/measurements/{len(r["measurements"])-1}/value')
for eq in D['equations']:
 own='single-crystal-acquisition'if eq['kind']=='crystallographic_definition'or eq['id']=='refinement-objective'else'thick-shell-characterization'if eq['id']=='hypothetical-sulfur-mass-balance'else'mechanistic-context'
 r=R[own];sid=sample(r,eq['kind'],eq['evidence']);ev=E(eq['evidence']);r['measurements'].append(measurement(eq['id'],sid,'equation_or_definition',fact(eq['description'],ev,note='Classification: '+eq['kind']+'.'),'Source equation/definition',ev));link('unit',eq['id'],r,f'/measurements/{len(r["measurements"])-1}/value')
for u in I['source_units']:
 if UL[u['id']]:continue
 r=R['source-context'];sid=sample(r,'bibliographic-and-source-context',u['evidence']);ev=E(u['evidence']);r['measurements'].append(measurement(u['id'],sid,'reference'if u['kind']=='reference'else'source_context',fact(u['title'],ev,note='External cited documents were not read; this field records the present-source citation or administrative statement.'),'Source text',ev));link('unit',u['id'],r,f'/measurements/{len(r["measurements"])-1}/value')
# All supplied sample-context objects receive explicit record-local links.
for s in D['samples']:
 rows=[x for x in OBJECTS if x['category']=='sample_context'and x['source_id']==s['id']]
 assert rows,('Unmapped source sample context',s['id'])
for r in R.values():
 r['quality']['missing_fields']=list(dict.fromkeys(r['quality']['missing_fields']))
 r['quality']['conflicts']=list(dict.fromkeys(r['quality']['conflicts']))
 r['context_links'].append({'label':'Complete source reader and limitations','url':'/paper-review.html?id='+SID,'relation':'private_reader_pending_independent_review'})
errors=[e for r in R.values()for e in validate_record(r)]
assert not errors,errors[:50]
assert all(FL.values())and all(UL.values())and len(TL)==471
groups=build_groups(list(R.values()));assert len(set(groups.values()))==1
assert not any(v['eligible']for r in R.values()for v in eligibility(r).values())
records=[]
for r in R.values():
 name=r['record_id']+'.json';save(name,r);records.append({'record_id':r['record_id'],'path':str(O/name),'sha256':sha(O/name),'record_type':r['record_type']})
coverage={'schema':'mattersyn-private-field-coverage/1','source_freeze_sha256':sha(P/'package-freeze.json'),'facts':[{'source_fact_id':f,'canonical_bindings':links}for f,links in FL.items()],'source_units':[{'source_unit_id':u,'canonical_bindings':links}for u,links in UL.items()],'table_cells':[{'source_cell_id':c,'canonical_bindings':links}for c,links in TL.items()],'table_definitions':TABLEMETA,'source_objects':OBJECTS,'transport_scope':'Every claim and source scalar/range, all 471 table cells, all source items, materials, stocks and protocol operations are field-linked. Raw printed tokens/ESDs/scaling remain in quantities and the lossless curated sidecar. No full-page/text cache is copied into proposed public data.'}
save('source-to-field-coverage.json',coverage)
save('lossless-source-map.json',{'private_only':True,'source_freeze_sha256':sha(P/'package-freeze.json'),'facts':D['facts'],'materials':D['materials'],'stocks':D['stocks'],'protocols':D['protocols'],'samples':D['samples'],'tables':D['tables'],'figures':D['figures'],'schemes':D['schemes'],'equations':D['equations'],'references':D['references'],'contradictions':D['contradictions'],'gaps':D['gaps']})
checks=[]
def ck(label,passed):checks.append({'check':label,'passed':bool(passed)})
BYID={r['record_id']:r for r in R.values()}
for fid,links in FL.items():
 for b in links:
  value=resolve(BYID[b['record_id']],b['pointer']);orig=resolve(FM[fid],b['source_pointer'])
  if b['source_pointer']=='/claim':passed=value['value']==orig
  elif orig['status']in ['reported_text','reported_identifier']:passed=value['value']==orig['raw_text']
  else:passed=value['raw_text']==orig['raw_text']and(value.get('maximum')==orig['value']if orig.get('comparison')in ['<','<=']else value.get('minimum')==orig['value']if orig.get('comparison')in ['>','>=']else value['value']==orig['value'])
  ck(fid+' '+b['pointer']+' value transport',passed)
for uid,links in UL.items():
 for b in links:ck(uid+' pointer resolves',resolve(BYID[b['record_id']],b['pointer'])is not None)
for t in D['tables']:
 for row in t['rows']:
  for c in row['cells']:
   b=TL[c['id']][0];v=resolve(BYID[b['record_id']],b['pointer']);ck(c['id']+' raw/scaled value transport',v.get('raw_text',v['value'])==c['raw_text']and(v['value']==c['raw_text']if c['status']in ['reported_text','reported_identifier']else v.get('maximum')==c['value']if c.get('comparison')in ['<','<=']else v['value']==c['value']))
for path,h in FR['bound_files'].items():ck('Frozen source unchanged '+path,sha(path)==h)
ck('All current training tasks remain empty/ineligible',all(r['quality']['requested_tasks']==[]and not any(x['eligible']for x in eligibility(r).values())for r in R.values()))
ck('No precursor/product atomic asset admission',all(r['structure_assets']==[]for r in R.values()))
assert all(c['passed']for c in checks),[c for c in checks if not c['passed']][:15]
counts={'records':len(R),'literature_route_records':2,'supporting_procedures':8,'observation_records':8,'operations':sum(len(r['operations'])for r in R.values()),'material_slots':sum(len(r['materials'])for r in R.values()),'stock_slots':sum(len(r['stocks'])for r in R.values()),'sample_context_slots':sum(len(r['products'])for r in R.values()),'measurements':sum(len(r['measurements'])for r in R.values()),'source_facts':len(FL),'source_fact_bindings':sum(map(len,FL.values())),'source_units':len(UL),'source_unit_bindings':sum(map(len,UL.values())),'source_table_cells':len(TL),'source_groups':1,'eligible_training_rows':0,'atomic_structure_assets':0}
save('author-validation.json',{'status':'author_schema_semantic_and_transport_checks_passed','author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'checks':checks,'check_count':len(checks),'counts':counts,'schema_errors':errors,'independent_source_audit':'passed_revision_2_separate_from_canonical_review','independent_canonical_audit':'pending','site_written':False,'training_exported':False})
save('record-manifest.json',{'schema':'mattersyn-private-canonical-proposal/1','source_id':SID,'version':1,'author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'status':'author_draft_source_audit_passed_canonical_audit_pending','independent_source_audit_path':str(AUDIT_PATH),'independent_source_audit_sha256':sha(AUDIT_PATH),'source_freeze_sha256':sha(P/'package-freeze.json'),'records':records,'counts':counts,'coverage_sha256':sha(O/'source-to-field-coverage.json'),'validation_sha256':sha(O/'author-validation.json'),'input_modules':{str(S/'scripts'/name):sha(S/'scripts'/name)for name in ['dataset_lib.py','record_helpers.py','schema_definition.py']},'author_script_sha256':sha(__file__)})
print(json.dumps(counts));print('MANIFEST',sha(O/'record-manifest.json'))
