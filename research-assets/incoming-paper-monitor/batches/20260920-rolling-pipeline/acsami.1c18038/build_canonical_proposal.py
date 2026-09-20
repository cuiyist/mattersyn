"""Private Lian canonical author proposal; frozen source and Site are read-only."""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import json,hashlib,re,sys
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;O=P/'canonical-proposal'/'v1';O.mkdir(parents=True,exist_ok=True)
assert not(O/'package-manifest.json').exists(),'Revise a frozen proposal separately.'
S=Path('[local path redacted]');sys.path.insert(0,str(S/'scripts'))
from record_helpers import record,source,fact,qty,material,operation,state,product,measurement
from dataset_lib import validate_record,eligibility,build_groups
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def norm(x):return re.sub('[^a-z0-9]+','-',str(x).lower()).strip('-')
def key(x):return norm(x).replace('-','_')
def compact(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'))
def esc(x):return str(x).replace('~','~0').replace('/','~1')
def resolve(x,p):
 for t in p.strip('/').split('/')if p else[]:x=x[int(t)]if isinstance(x,list)else x[t.replace('~1','/').replace('~0','~')]
 return x
D=read(P/'source-facts.json');I=read(P/'source-inventory.json');FR=read(P/'package-freeze.json');SID='lian2021';PRE='lian-2021-'
assert sha(P/'package-freeze.json')=='2eca0b5181f3b60156227095e51833af870c7a3ea7e0590c4d3e782931555ae7'
for path,h in FR['bound_files'].items():assert sha(path)==h,path
AUDIT_PATH=P/'source-independent-audit'/'independent-audit-v2.json'
AUDIT=read(AUDIT_PATH)if AUDIT_PATH.exists()else None
PASSED=bool(AUDIT and AUDIT.get('status')=='passed'and AUDIT.get('proposal_freeze_sha256')==sha(P/'package-freeze.json')and not AUDIT.get('open_findings'))
AUDIT_NOTE='Distinct supplied-PDF source audit passed revision 2; canonical/reader approval remains pending.'if PASSED else'Distinct supplied-PDF source audit is pending; this is an unapproved canonical/reader draft.'
FM={x['id']:x for x in D['facts']};MM={x['id']:x for x in D['materials']};PP={x['id']:x for x in D['protocols']};UU={x['id']:x for x in I['inventory_units']};UM={(x['type'],x['source_object_id']):x['id']for x in I['inventory_units']}
CON={x['id']:x for x in D['conflicts']};GAP={x['id']:x for x in D['gaps']};R={};FL={i:[]for i in FM};UL={i:[]for i in UU};TL={};OBJECTS=[];TABLEMETA=[]
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
SRC=source(SID,D['doi'],D['title'],'; '.join(D['authors']),2021,si='All 26 supplied SI pages read and viewed; cited crystal ZIP/MP4 unavailable. '+AUDIT_NOTE)
SRC['main_status']='All 8 supplied main pages read and viewed. '+AUDIT_NOTE
SRC['reuse_status']='Private proposal with selected crops only; public transport, visual bindings and browser review remain separate gates.'
COMMON=[AUDIT_NOTE,'Canonical/reader independent approval, publication and training admission are not asserted.','Source-defined record/context IDs are not physical batch labels or replicate counts.','Only supplied main/SI PDFs were read; the cited crystal ZIP and scintillation MP4 are unavailable.','No qualified atomic model, relaxed DFT geometry, exact recipe–structure or particle-size training label is admitted.']
CONFIG={
'bulk-a-route':('Bulk A solvent-evaporation synthesis','(C12H28N)2SbCl5','literature_protocol'),
'bulk-b-route':('Bulk B stoichiometric variant','(C12H28N)SbCl4','protocol_variant'),
'nc-a-route':('A nanocrystal ligand-assisted reprecipitation','(C12H28N)2SbCl5','literature_protocol'),
'composite-film-series':('Five phosphor/nanocrystal/PS film formulations','A nanocrystals / BaMgAl10O17:Eu2+ / PS','procedure'),
'spincoat-film-route':('Precursor spin-coating and annealing','(C12H28N)2SbCl5','procedure'),
'bulk-characterization':('Bulk diffraction, XPS, TGA and optical acquisition','Antimony-halide bulk A and B','procedure'),
'nc-characterization':('Nanocrystal microscopy and optical acquisition','(C12H28N)2SbCl5','procedure'),
'film-beta-characterization':('Film photoluminescence and beta irradiation','Bulk A and A composite/spin-coated films','procedure'),
'dft-calculation':('Relaxed electronic-structure calculations','Antimony-halide A and B calculation contexts','procedure'),
'bulk-a-properties':('Bulk A photophysical and structural results','(C12H28N)2SbCl5','observation'),
'bulk-b-properties':('Bulk B structure and non-emissive outcome','(C12H28N)SbCl4','observation'),
'nc-properties':('Nanocrystal size, optics and settling','(C12H28N)2SbCl5','observation'),
'film-properties':('Composite and spin-coated film results','A-based film contexts','observation'),
'mechanistic-context':('Distortion and photophysical models','Antimony-halide model contexts','observation'),
'reagents-methods':('Source-qualified material inventory','Study materials','observation'),
'source-context':('Bibliographic scope and missing attachments','Study source context','observation')}
for k,(title,formula,kind)in CONFIG.items():
 r=record(PRE+k,'Lian et al. (2021) · '+title,formula,'Zero-dimensional organic antimony halides',PP[k]['title']if k in PP else title,deepcopy(SRC),'Full supplied main/SI PDF scope; fields carry exact source locators',kind)
 r['schema_version']='1.3.0';r['lineage'].update(source_group=SID,recipe_family=SID+'-stoichiometry-nanocrystal-films')
 r['quality'].update(review_status='imported_unreviewed',review_scope='Private author draft. '+AUDIT_NOTE,requested_tasks=[],experimental_outcome='not_established',missing_fields=COMMON.copy(),conflicts=[])
 r['intended_target']['composition']=fact(formula if k in list(CONFIG)[:5]else None,FE('source-identity'),note='Only preparation records state a synthetic target. Calculated, measured and contextual outputs remain separate.')
 if k=='bulk-b-route':r['lineage']['parent_record_id']=PRE+'bulk-a-route'
 if k=='composite-film-series':r['material'].update(architecture='composite',components=['(C12H28N)2SbCl5','BaMgAl10O17:Eu2+','PS'])
 R[k]=r
def own(fid):
 short=fid.removeprefix(SID+'-')
 if short in['source-identity','supplement-scope']:return'source-context'
 if short in['background','si-distortion-definitions','activation','phonon-coupling','photophysical-model']:return'mechanistic-context'
 if short=='chemicals':return'reagents-methods'
 if short.startswith('bulk-a-')and short in['bulk-a-charge','bulk-a-growth']:return'bulk-a-route'
 if short=='bulk-b-variant':return'bulk-b-route'
 if short in['nc-stock','nc-injection','nc-recovery']:return'nc-a-route'
 if short in['composite-mixing','composite-casting']:return'composite-film-series'
 if short in['spincoat-stock','spincoat-deposit']:return'spincoat-film-route'
 if short in['a-structure','a-distortion','pxrd-consistency','xps-shift','thermal-stability','si-coordinates','si-adps']:return'bulk-characterization'
 if short in['b-structure','b-distortion','b-nonemission']:return'bulk-b-properties'
 if short.startswith('a-')or short in['excitation-series','bulk-air-stability','temperature-series']:return'bulk-a-properties'
 if short.startswith('dft-')or short=='parity-interpretation':return'dft-calculation'
 if short.startswith('nc-'):return'nc-properties'
 if short in['film-spectrum-series','spincoat-optics','scintillation']:return'film-properties'
 if short in['acquisition-xray','acquisition-xps-tga','acquisition-pl','acquisition-plqe']:return'bulk-characterization'
 if short=='acquisition-tem':return'nc-characterization'
 if short=='acquisition-beta':return'film-beta-characterization'
 raise KeyError(short)
OWN={fid:own(fid)for fid in FM}
def Q(qv,scope='',extra=''):
 es=E(qv['evidence']);note=extra+' '+cn(qv.get('conflict_ids',[])+qv.get('gap_ids',[]))
 if 'spincoat'in scope:note=note.replace('G3: '+GAP['G3']['description'],'G3 describes the separate nanocrystal/phosphor/PS composite-film series. For this precursor spin-coated film, the DMF charge and annealing conditions are reported; filtration details, atmosphere and film thickness remain unspecified.')
 basis='Source context: '+scope+'. Printed-to-value scale: '+str(qv.get('printed_to_value_scale',1))+'.'
 if qv.get('uncertainty')is not None:note+=' Uncertainty after source scaling: '+str(qv['uncertainty'])+' '+str(qv['unit'])+'; definition: '+str(qv.get('uncertainty_definition'))+'.'
 if qv['unit']is None:note+=' The source does not report a unit; no conventional unit is silently supplied.'
 if qv['status']in['reported_text','reported_identifier','reported_ratio_parts','reported_mesh']:
  return fact(qv['raw_text'],es,note=basis+' '+note+' Components, where applicable: '+compact(qv.get('components'))+'.')
 v=qv['value'];lo=(qv.get('range')or{}).get('min');hi=(qv.get('range')or{}).get('max');cmp=qv.get('comparison')
 if cmp in['<','<=']:hi=v;v=None
 if cmp in['>','>=']:lo=v;v=None
 return qty(v,qv['unit']or'',es,'reported'if v is not None or lo is not None or hi is not None else'not_reported',minimum=lo,maximum=hi,approximate=qv.get('approximate',False),qualifier=note.strip(),basis=basis,raw_text=qv['raw_text'],minimum_exclusive=cmp=='>'if cmp in['>','>=']else None,maximum_exclusive=cmp=='<'if cmp in['<','<=']else None)
def sample(r,scope,es):
 sid=norm(scope)
 if not any(p['sample_id']==sid for p in r['products']):
  formula='(C12H28N)2SbCl5'if scope in['bulk-a','bulk-a-crystal','nc-a','nc-a-dried-powder','nc-a-colloid-vs-dry','film-spincoat']else'(C12H28N)SbCl4'if scope in['bulk-b','bulk-b-crystal']else None
  pr=product(sid,formula,E(es),link='general_context',notes=['Source context: '+scope+'.','This source-defined composition/state/model context is not an author-labelled physical batch or replicate.','No measured product atomic coordinates, exact recipe–structure pair or universal cross-technique specimen identity is inferred.'])
  pr['source_sample_label']=scope
  if scope in['bulk-a','bulk-a-crystal']:pr['phase']=fact('triclinic P-1',FE('a-structure'),note='Source bulk-crystal assignment; not qualified model geometry.')
  if scope in['bulk-b','bulk-b-crystal']:pr['phase']=fact('monoclinic P21/c',FE('b-structure'),note='Two crystallographically independent Sb centres in SI; no single-centre collapse.')
  if scope.startswith('nc-a'):pr['morphology']=fact('nanocrystals',FE('nc-phase-size'),note='Mean diameter belongs to TEM context; no synthesis target diameter or universal physical aliquot join.')
  r['products'].append(pr);link('sample_context',scope,r,f'/products/{len(r["products"])-1}')
 return sid
ROLES={'tpa-cl':'organic_cation_precursor','sbcl3':'metal_precursor','dmf':'solvent','toluene':'solvent','oleic-acid':'ligand','ps':'polymer_matrix','blue-phosphor':'preformed_phosphor','glass':'support','nitrogen':'characterization_atmosphere','liquid-nitrogen':'instrument_coolant'}
def addm(r,mid,stage='characterization'):
 if any(m['id']==mid for m in r['materials']):return mid
 src=MM[mid];r['materials'].append(material(mid,src['name'],src['source_formula_or_abbreviation'],ROLES.get(mid,'source_sample'),stage,E(src['evidence']),notes=[src['scope_note'],'Source role: '+src['role']+'.','Chemical/atomic visual binding is separately pending.']))
 ptr=f'/materials/{len(r["materials"])-1}';link('material',mid,r,ptr);unit('material',mid,r,ptr);return mid
for mid in MM:addm(R['reagents-methods'],mid)
STAGE={'a-dissolve-filter':'precursor_preparation','a-evaporate':'synthesis','b-dissolve-filter':'precursor_preparation','b-evaporate':'synthesis','nc-dissolve-filter':'precursor_preparation','nc-inject':'synthesis','nc-centrifuge':'workup','film-blend':'precursor_preparation','film-cast':'synthesis','spin-feed':'precursor_preparation','spin-deposit':'synthesis'}
for pid,pr in PP.items():
 r=R[pid];produced={}
 for j,so in enumerate(pr['operations']):
  stage=STAGE.get(so['id'],'characterization');ins=[]
  for mid in so['inputs']:
   if mid in MM:ins.append(addm(r,mid,stage))
   else:assert mid in produced,(pid,mid);ins.append(mid)
  for out in so['outputs']:
   kind='analysis_data'if stage=='characterization'else'fraction'if so['retained_fraction']==out else'sample_set'if out=='film-mixtures'else'stock'if out.endswith('feed')else'mixture'
   parents=[i for i in ins if i!='glass']if out=='composite-film'else ins
   r['material_states'].append(state(out,out.replace('-',' '),parents,kind))
  env='room temperature'if so['id']in['a-evaporate','b-evaporate']else'N2 applies only to TGA; XPS atmosphere not specified'if so['id']=='bulk-xps-tga'else None
  desc=so['action']+'. '+' '.join(FM[fid]['claim']for fid in so['source_fact_ids'])
  desc+=' Missing fields: '+(', '.join(so['missing_fields'])or'none specifically enumerated')+'.'
  op=operation(so['id'],norm(so['action']),so['action'],E(so['evidence']),ins,so['outputs'],depends=list(dict.fromkeys(produced[x]for x in so['inputs']if x in produced)),stage=stage,description=desc,environment=fact(env,E(so['evidence'])),retained_fraction=so['retained_fraction'])
  for qv in so['quantities']:
   # PLQE is an observed result, not an acquisition setting; ratio/mesh strings live in lossless measurement fields.
   if so['id']=='nc-plqe'and qv['meaning']=='PLQE':continue
   cq=Q(qv,pid)
   if 'unit'not in cq:continue
   pk=key(qv['meaning']);op['parameters'][pk]=cq
   for fid in so['source_fact_ids']:
    for iq,original in enumerate(FM[fid]['quantities']):
     if qv==original:link('fact',fid,r,f'/operations/{j}/parameters/'+esc(pk),'/quantities/'+str(iq))
  r['operations'].append(op)
  for out in so['outputs']:produced[out]=so['id']
  unit('protocol',pid,r,f'/operations/{j}');link('operation',so['id'],r,f'/operations/{j}');r['quality']['missing_fields']+=so['missing_fields']
# Source preparation stocks are formulated solutions, not additional dosing events.
STOCK_OWNER={'a-feed':'bulk-a-route','b-feed':'bulk-b-route','nc-feed':'nc-a-route','spin-feed':'spincoat-film-route','ps-toluene':'composite-film-series'}
for st in D['stocks']:
 r=R[STOCK_OWNER[st['id']]];es=FM[st['source_fact_id']]['evidence']if st.get('source_fact_id')else st['evidence'];comps=[]
 for c in st['components']:comps.append({'material_id':addm(r,c['material_id'],'precursor_preparation'),'quantities':{}})
 row={'id':'stock-'+st['id'],'name':st['id'].replace('-',' ')+' formulation','components':comps,'concentrations':{},'preparation_operation_ids':[r['operations'][0]['id']],'scope':st['scope']+' This formulation duplicates no physical charge. Source roles: '+', '.join(c['material_id']+'='+c['role']for c in st['components'])+'.','evidence':E(es)}
 r['stocks'].append(row);ptr=f'/stocks/{len(r["stocks"])-1}';link('stock',st['id'],r,ptr);unit('stock',st['id'],r,ptr)
# Every original factual claim and typed quantity receives a source-scoped canonical measurement.
for fid,f in FM.items():
 r=R[OWN[fid]];sid=sample(r,f['sample_scope'],f['evidence']);es=E(f['evidence']);note='Source claim class: '+f['claim_class']+'. '+cn(f['conflict_ids']+f['gap_ids'])
 r['measurements'].append(measurement(fid+'-claim',sid,'source_claim',fact(f['claim'],es,note=note),'Source text; explicit claim classification',es,conditions=f['sample_scope']))
 ptr=f'/measurements/{len(r["measurements"])-1}/value';link('fact',fid,r,ptr,'/claim');unit('fact',fid,r,ptr)
 for iq,qv in enumerate(f['quantities']):
  r['measurements'].append(measurement(fid+'-q'+str(iq+1),sid,key(qv['meaning']),Q(qv,f['sample_scope'],note),'Source-reported result/condition; measured versus model scope explicit',E(qv['evidence']),conditions=f['sample_scope']+'; quantity meaning: '+qv['meaning']))
  ptr=f'/measurements/{len(r["measurements"])-1}/value';link('fact',fid,r,ptr,'/quantities/'+str(iq));unit('fact',fid,r,ptr)
 r['quality']['conflicts']+=[cn([cid])for cid in f['conflict_ids']]
for tab in D['tables']:
 r=R['bulk-characterization'];es=E(tab['evidence']);scope=tab['sample_scope'];sid=sample(r,scope,tab['evidence']);extra='Bulk single-crystal source table; no nanocrystal coordinates, complete hydrogen/occupancy model, supplied CIF, relaxed DFT geometry or exact training pair is approved. '+(cn(['C1'])if scope=='bulk-b-crystal'else'')
 meta={k:deepcopy(tab[k])for k in['id','title','columns','sample_scope','notes','evidence']}
 r['measurements'].append(measurement(tab['id']+'-definition',sid,'table_definition',fact(compact(meta),es,note=extra),'Source table headings, columns and notes',es))
 ptr=f'/measurements/{len(r["measurements"])-1}/value';unit('table',tab['id'],r,ptr);TABLEMETA.append({'table_id':tab['id'],'record_id':r['record_id'],'pointer':ptr})
 for row in tab['rows']:
  for c in row['cells']:
   col=c.get('column','value');cell_scope=('bulk-a-crystal'if col=='A'else'bulk-b-crystal')if tab['id']=='table-s1'else scope
   cell_sid=sample(r,cell_scope,c['evidence']);r['measurements'].append(measurement(c['id'],cell_sid,key(tab['id']+' '+row['row_label']+' '+col),Q(c,cell_scope,extra),'Printed source table cell',E(c['evidence']),conditions='Row '+row['row_label']+'; column '+col+'.'))
   ptr=f'/measurements/{len(r["measurements"])-1}/value';link('table_cell',c['id'],r,ptr);unit('table',tab['id'],r,ptr)
FIGOWNER={'graphical-abstract':'mechanistic-context','figure-1':'bulk-characterization','figure-2':'bulk-a-properties','figure-3':'dft-calculation','figure-4':'nc-properties','figure-5':'film-properties','figure-s1':'bulk-characterization','figure-s2':'bulk-characterization','figure-s3':'bulk-characterization','figure-s4':'bulk-a-properties','figure-s5':'bulk-a-properties','figure-s6':'bulk-a-properties','figure-s7':'bulk-a-properties','figure-s8':'bulk-a-properties','figure-s9':'bulk-a-properties','figure-s10':'mechanistic-context','figure-s11':'nc-properties','figure-s12':'nc-properties','figure-s13':'nc-properties','figure-s14':'film-properties','figure-s15':'film-properties'}
for obj in D['figures']+D['schemes']+D['equations']:
 kind='figure'if obj in D['figures']else'scheme'if obj in D['schemes']else'equation';owner=FIGOWNER[obj['id']]if kind=='figure'else'bulk-a-route'if kind=='scheme'else'mechanistic-context';r=R[owner];scope=obj.get('sample_scope',obj.get('scope','source-context'));sid=sample(r,scope,obj['evidence']);es=E(obj['evidence']);text=(obj.get('title','')+'. '+obj.get('scope_note',''))if kind!='equation'else obj['expression']+'; '+obj['meaning']
 r['measurements'].append(measurement(obj['id']+'-context',sid,kind+'_context',fact(text,es,note='Original artwork/definition retained; no raw plot digitization or atomistic model approval.'),'Source '+kind,es));unit(kind,obj['id'],r,f'/measurements/{len(r["measurements"])-1}/value')
# Explicit source sample objects remain separate from record-local contexts generated above.
SAMPLE_OWNER={'bulk-a':'bulk-a-route','bulk-b':'bulk-b-route','nc-a':'nc-a-route','nc-a-dried-powder':'nc-properties','nc-a-colloid-vs-dry':'nc-properties','film-spincoat':'spincoat-film-route','beta-nc-film':'film-beta-characterization','dft-a':'dft-calculation','dft-b':'dft-calculation'}
for obj in D['samples']:
 r=R[SAMPLE_OWNER.get(obj['id'],'composite-film-series')];es=obj.get('evidence')or FM[SID+'-'+('dft-method'if obj['id'].startswith('dft-')else'source-identity')]['evidence'];sid=sample(r,obj['id'],es);ip=next(i for i,p in enumerate(r['products'])if p['sample_id']==sid);r['products'][ip]['notes']+=['Source sample object: '+compact(obj)];unit('sample_context',obj['id'],r,f'/products/{ip}')
for k,sid,out in [('bulk-a-route','bulk-a','bulk-a'),('bulk-b-route','bulk-b','bulk-b'),('nc-a-route','nc-a','nc-a'),('spincoat-film-route','film-spincoat','spincoat-film')]:
 r=R[k];pr=next(p for p in r['products']if p['sample_id']==sid)
 assert any(s['id']==out for s in r['material_states'])
 pr['recipe_link']='explicit';pr['material_state_id']=out;pr['link_evidence']=E(PP[k]['operations'][-1]['evidence'])
 pr['notes'].append('Explicit preparation-to-nominal-product relation only; separate characterization aliquots and atomic models are not thereby joined.')
 r['intended_target']['composition']['evidence']=E(PP[k]['operations'][0]['evidence'])
for ref in D['references']:
 r=R['source-context'];sid=sample(r,'bibliographic-context',ref['evidence']);es=E(ref['evidence']);r['measurements'].append(measurement(ref['id'],sid,'bibliographic_reference',fact(ref['citation'],es,note='Citation identity from this source only; cited full text not read.'),'Source reference list',es));unit('reference',ref['id'],r,f'/measurements/{len(r["measurements"])-1}/value')
for r in R.values():
 r['quality']['missing_fields']=list(dict.fromkeys(r['quality']['missing_fields']));r['quality']['conflicts']=list(dict.fromkeys(r['quality']['conflicts']));r['context_links']=[{'label':'Complete source reader and limitations','url':'/paper-review.html?id='+SID,'relation':'private_unapproved_reader_proposal'}]
errors=[e for r in R.values()for e in validate_record(r)];assert not errors,errors[:30]
assert all(FL.values())and all(UL.values())and len(TL)==891
assert len(set(build_groups(list(R.values())).values()))==1
assert not any(v['eligible']for r in R.values()for v in eligibility(r).values())
records=[]
for r in R.values():
 name=r['record_id']+'.json';save(name,r);records.append({'record_id':r['record_id'],'path':str(O/name),'sha256':sha(O/name),'record_type':r['record_type']})
coverage={'schema':'mattersyn-private-field-coverage/1','source_freeze_sha256':sha(P/'package-freeze.json'),'facts':[{'source_fact_id':i,'canonical_bindings':b}for i,b in FL.items()],'source_units':[{'source_unit_id':i,'canonical_bindings':b}for i,b in UL.items()],'table_cells':[{'source_cell_id':i,'canonical_bindings':b}for i,b in TL.items()],'table_definitions':TABLEMETA,'source_objects':OBJECTS,'transport_scope':'All57claims/134typed quantities, all891table cells,167uniquely identified inventory objects,15material identities,5stocks and21operations retain exact field links. No missing attachment, atomic geometry or training label is fabricated.'}
save('source-to-field-coverage.json',coverage)
save('lossless-source-map.json',{'private_only':True,'source_freeze_sha256':sha(P/'package-freeze.json'),**{k:deepcopy(D[k])for k in['facts','materials','stocks','protocols','samples','tables','figures','schemes','equations','references','conflicts','gaps']}})
checks=[];BY={r['record_id']:r for r in R.values()}
def ck(n,ok):checks.append({'check':n,'passed':bool(ok)});assert ok,n
def value_ok(src,dst):
 if src['status']in['reported_text','reported_identifier','reported_ratio_parts','reported_mesh']:return dst['value']==src['raw_text']
 if src.get('comparison')in['<','<=']:v=dst['maximum']==src['value']and dst.get('maximum_exclusive')==(src['comparison']=='<')
 elif src.get('comparison')in['>','>=']:v=dst['minimum']==src['value']and dst.get('minimum_exclusive')==(src['comparison']=='>')
 else:v=dst['value']==src['value']
 return v and dst['raw_text']==src['raw_text']and dst['approximate']==src['approximate']and dst['unit']==(src['unit']or'')
for fid,bs in FL.items():
 for b in bs:
  dst=resolve(BY[b['record_id']],b['pointer']);src=resolve(FM[fid],b['source_pointer']);ck(fid+' '+b['pointer'],dst['value']==src if b['source_pointer']=='/claim'else value_ok(src,dst))
for tab in D['tables']:
 for row in tab['rows']:
  for c in row['cells']:
   b=TL[c['id']][0];dst=resolve(BY[b['record_id']],b['pointer']);ck(c['id']+' exact raw/value/bound/scale transport',value_ok(c,dst))
   if c['uncertainty']is not None:ck(c['id']+' uncertainty retained',str(c['uncertainty'])in dst['qualifier'])
for uid,bs in UL.items():
 for b in bs:ck(uid+' resolves '+b['pointer'],resolve(BY[b['record_id']],b['pointer'])is not None)
for path,h in FR['bound_files'].items():ck('Frozen source unchanged '+path,sha(path)==h)
ck('No model or task admission',all(r['structure_assets']==[]and r['quality']['requested_tasks']==[]for r in R.values()))
ck('Distinct source revision-2 audit binds current freeze',PASSED)
ck('Peeled film excludes removed glass support',next(s for s in R['composite-film-series']['material_states']if s['id']=='composite-film')['parent_ids']==['film-mixtures']and 'glass'in R['composite-film-series']['operations'][1]['inputs'])
ck('Spin-coated film retains support',next(s for s in R['spincoat-film-route']['material_states']if s['id']=='spincoat-film')['parent_ids']==['spin-feed','glass'])
ck('Composite missingness is explicitly qualified on spincoat quantities','G3: '+GAP['G3']['description']not in compact(R['spincoat-film-route']['operations']))
for row in D['tables'][0]['rows']:
 for c in row['cells']:
  b=TL[c['id']][0];m=resolve(BY[b['record_id']],b['pointer'].rsplit('/',1)[0]);ck(c['id']+' explicit A/B column context',m['sample_id']==('bulk-a-crystal'if c['column']=='A'else'bulk-b-crystal'))
counts={'records':len(R),'literature_routes':2,'protocol_variants':1,'procedures':6,'observations':7,'operations':sum(len(r['operations'])for r in R.values()),'material_slots':sum(len(r['materials'])for r in R.values()),'stock_slots':sum(len(r['stocks'])for r in R.values()),'sample_context_slots':sum(len(r['products'])for r in R.values()),'measurements':sum(len(r['measurements'])for r in R.values()),'source_facts':len(FL),'source_fact_bindings':sum(map(len,FL.values())),'source_units':len(UL),'source_unit_bindings':sum(map(len,UL.values())),'source_table_cells':len(TL),'source_groups':1,'eligible_training_rows':0,'atomic_structure_assets':0}
save('author-validation.json',{'status':'author_schema_semantic_transport_checks_passed','author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'checks':checks,'check_count':len(checks),'counts':counts,'schema_errors':errors,'independent_source_audit':'passed_revision_2'if PASSED else'pending','independent_canonical_audit':'pending','site_written':False,'training_exported':False})
save('record-manifest.json',{'schema':'mattersyn-private-canonical-proposal/1','source_id':SID,'version':1,'author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'status':'private_unapproved_author_proposal','independent_source_audit_path':str(AUDIT_PATH)if PASSED else None,'independent_source_audit_sha256':sha(AUDIT_PATH)if PASSED else None,'source_freeze_sha256':sha(P/'package-freeze.json'),'records':records,'counts':counts,'coverage_sha256':sha(O/'source-to-field-coverage.json'),'validation_sha256':sha(O/'author-validation.json'),'input_modules':{str(S/'scripts'/n):sha(S/'scripts'/n)for n in['dataset_lib.py','record_helpers.py','schema_definition.py']},'author_script_sha256':sha(__file__)})
print(json.dumps(counts));print('MANIFEST',sha(O/'record-manifest.json'))
