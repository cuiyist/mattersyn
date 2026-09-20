"""Sasongko canonical author proposal; private paths only, no source/Site writes."""
from pathlib import Path
from copy import deepcopy
import json,hashlib,re,sys
sys.dont_write_bytecode=True
C=Path(__file__).resolve().parent;J=C.parent;O=C/'v1';O.mkdir(exist_ok=True)
assert not(O/'package-freeze.json').exists()
S=Path('[local path redacted]');sys.path.insert(0,str(S/'scripts'))
from record_helpers import record,source,fact,qty,material,operation,state,product,measurement
from dataset_lib import validate_record,eligibility,build_groups
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def norm(x):return re.sub('[^a-z0-9]+','-',str(x).lower()).strip('-')
def key(x):return norm(x).replace('-','_')
def compact(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'))
def esc(x):return str(x).replace('~','~0').replace('/','~1')
def resolve(x,p):
 for k in p.strip('/').split('/')if p else[]:
  k=k.replace('~1','/').replace('~0','~');x=x[int(k)]if isinstance(x,list)else x[k]
 return x
overlay=J/'source-extraction-revision-2';audit=J/'source-independent-audit/independent-audit-v2.json'
assert sha(overlay/'package-freeze.json')=='d34778349e9942a73a1d275536af354e93d52739692e689fe2f12d394db7fddc'
assert sha(audit)=='c709225b9555ba89d3d952a6153561b011351c00fb2c62733c920447479edb58'and read(audit)['status']=='passed'
replacements=read(overlay/'effective-file-map.json')['replacements']
def effective(n):return Path(replacements[n]['path'])if n in replacements else J/n
for f in [J/'package-freeze.json',overlay/'package-freeze.json']:
 for p,h in read(f)['bound_files'].items():
  pp=Path(p)if Path(p).is_absolute()else J/p
  assert sha(pp)==(h['sha256']if isinstance(h,dict)else h),p
D=read(effective('source-facts.json'));I=read(effective('source-inventory.json'));T=read(effective('source-tables.json'));A=read(effective('original-assets-manifest.json'))
SID='sasongko2025';PRE='sasongko-2025-'
FM={x['id']:x for x in D['facts']};MM={x['id']:x for x in D['materials']};SC={x['id']:x for x in D['sample_contexts']};ST={x['id']:x for x in D['stocks']};PP={x['id']:x for x in D['protocols']}
CON={x['id']:x for x in D['conflicts']};GAP={x['id']:x for x in D['missingness']}
def E(es):return[{'source_id':SID,'locator':e['document_role'].upper()+' PDF p. '+str(e['pdf_page'])+' (printed '+str(e.get('printed_page'))+'), '+e['locator']+'; original SHA256 '+e['source_sha256']}for e in es]
def fe(k):return E(FM[SID+'-'+k]['evidence'])
def quals(q):return' '.join(i+': '+(CON.get(i)or GAP.get(i))['description']for i in q.get('conflict_ids',[])+q.get('gap_ids',[])if i in CON or i in GAP)
def Q(q,scope='',force=None):
 ev=E(q['evidence']);note='Source scope: '+scope+'. '+quals(q)+' Original status: '+q['status']+'.'
 if q.get('uncertainty')is not None:note+=' Source uncertainty: '+compact(q['uncertainty'])+'.'
 if q.get('ordered_endpoints')is not None:note+=' Ordered source endpoints: '+compact(q['ordered_endpoints'])+'.'
 if q['status']=='reported_text':return fact(q['raw_text'],ev,note=note)
 v=q['value'];lo=(q.get('range')or{}).get('min');hi=(q.get('range')or{}).get('max');cmp=q.get('comparison')
 if cmp in['<','<=']:hi=v;v=None
 if cmp in['>','>=']:lo=v;v=None
 status=force or('author_derived'if q['status']in['source_calculation','author_calculated','author_derived']else'reported')
 if v is None and lo is None and hi is None:status='not_reported'
 return qty(v,q.get('unit')or'',ev,status,minimum=lo,maximum=hi,approximate=q.get('approximate',False),raw_text=q['raw_text'],qualifier=note,basis=scope,minimum_exclusive=cmp=='>'if cmp in['>','>=']else None,maximum_exclusive=cmp=='<'if cmp in['<','<=']else None)
PLAN=[
 ('hot-injection','Hot injection with source-paired ligand, washing and temperature conditions','literature_protocol','protocol',['qd-synthesis-family','purification-family']),
 ('fa-oleate-preparation','FA-oleate precursor preparation','procedure','precursors',['fa-oleate-preparation']),
 ('xrd','Powder X-ray diffraction acquisition','procedure','structures',['xrd']),
 ('trpl','Time-resolved photoluminescence acquisition','procedure','properties',['trpl']),
 ('tem','Transmission electron microscopy acquisition','procedure','structures',['tem']),
 ('temperature-pl','Variable-temperature photoluminescence','procedure','properties',['temperature-pl']),
 ('temperature-raman','Variable-temperature Raman spectroscopy','procedure','properties',['temperature-raman']),
 ('thermal-aging','Optical aging at 350 K','procedure','properties',['thermal-aging']),
 ('source-materials','Precursors, solvents and reference identities','observation','precursors',[]),
 ('ligand-results','Ligand-ratio comparison','observation','structures',[]),
 ('wash-results','Purification-ratio comparison and washing waste','observation','structures',[]),
 ('growth-results','Growth-temperature structure and optical comparison','observation','structures',[]),
 ('temperature-results','Temperature-dependent optical observations','observation','properties',[]),
 ('raman-results','Current Raman observations and cited assignments','observation','properties',[]),
 ('aging-results','Thermal photoluminescence stability','observation','properties',[]),
 ('reference-cells','Cited bulk phase cell parameters','observation','structures',[]),
 ('literature-comparison','Published phase-transition comparison','observation','properties',[]),
 ('mechanistic-context','Chemical intuition and conceptual phase model','observation','intuition',[]),
 ('source-context','Sources and limitations','observation','sources',[]),
]
OWN={}
def own(k,ids):
 for x in ids.split():OWN[SID+'-'+x]=k
own('source-context','identity source-notes')
own('source-materials','materials')
own('fa-oleate-preparation','fa-charge fa-vacuum fa-hot')
own('hot-injection','qd-charge qd-preheat qd-ligands qd-equilibrate qd-inject wash-formulation wash-spin redisperse clarify-spin')
own('ligand-results','ligand-design ligand-xrd ligand-optical')
own('wash-results','wash-design wash-results washing-photo')
own('growth-results','temperature-design temperature-phase temperature-lifetimes temperature-size fringe')
own('xrd','xrd-method');own('trpl','trpl-method');own('tem','tem-method');own('temperature-pl','temperature-method')
own('temperature-results','pl-temperature-scan pl-gamma pl-beta pl-alpha pl-overheat')
own('raman-results','raman-range raman-observation raman-reference')
own('aging-results','thermal-stability');own('reference-cells','cited-cell-gamma cited-cell-beta cited-cell-alpha')
own('literature-comparison','literature-transition')
own('mechanistic-context','ligand-mechanism wash-limit scheme-model background conclusion')
assert set(OWN)==set(FM)
SOWN={}
for sid,s in SC.items():
 SOWN[sid]=('ligand-results'if sid.startswith('ligand-')else'wash-results'if sid.startswith('wash-')or sid=='washing-waste'else'growth-results'if sid.startswith('growth-')else'reference-cells'if sid.endswith('-reference')else'literature-comparison'if sid.startswith('table-s1-')else{'fa-stock':'fa-oleate-preparation','temperature-pl':'temperature-results','temperature-raman':'raman-results','aging-350':'aging-results','phase-model':'mechanistic-context'}.get(sid,'hot-injection'))
TO={'ligand-numeric':'ligand-results','wash-numeric':'wash-results','growth-numeric':'growth-results','pl-slopes':'temperature-results','reference-cells':'reference-cells','table-s1':'literature-comparison'}
FO={'figure-1':['ligand-results'],'figure-2':['wash-results'],'figure-3':['growth-results'],'figure-4':['temperature-results'],'figure-5':['temperature-results'],'figure-s1':['wash-results'],'figure-s2':['raman-results'],'figure-s3':['aging-results']}
EO={'lifetime-eq2':'trpl','aging-fit':'aging-results'}
PO={pid:k for k,title,kind,section,pids in PLAN for pid in pids}
R={};OB=[];FL={k:[]for k in FM};UL={u['id']:[]for u in I['units']};TC=[];OP=[];TYPED=[]
status='Private canonical and reader author proposal from independently audited source revision 2; separate canonical review is pending.'
src=source(SID,D['doi'],D['title'],'; '.join(D['authors']),D['year'],si='All 11 supplied matched SI pages passed distinct source review.')
src['main_status']='All nine supplied main pages passed distinct source review.'
for k,title,kind,section,pids in PLAN:
 formula='FA-oleate'if k=='fa-oleate-preparation'else'FAPbI3'if k not in['source-context','source-materials']else'Study source context'
 rr=record(PRE+k,'Sasongko et al. (2025) · '+title,formula,'Lead halide perovskite quantum dots',title,deepcopy(src),'Exact original main/SI page and figure locators',kind);rr['schema_version']='1.3.0'
 rr['lineage'].update(source_group=SID,recipe_family=SID+'-hot-injection-study')
 rr['intended_target']['composition']=fact(formula if kind=='literature_protocol'or k=='fa-oleate-preparation'else None,fe('identity'),note='Nominal target only; observation/acquisition records do not establish a new synthesis target.')
 rr['quality'].update(review_status='imported_unreviewed',review_scope=status,requested_tasks=[],experimental_outcome='not_established',missing_fields=['No current atomic coordinates or exact structure–recipe pair.','Named contexts are not physical batch identifiers or independent replicates.'],conflicts=[])
 rr['context_links']=[{'label':'Source document reader','url':'/paper-review.html?id='+SID,'relation':'private_unapproved_reader'}];R[k]=rr
def bind(cat,oid,r,ptr,sp=None):
 b={'category':cat,'source_id':oid,'record_id':r['record_id'],'pointer':ptr}
 if sp:b['source_pointer']=sp
 OB.append(b);return b
def sample(r,sid,es):
 if not any(p['sample_id']==sid for p in r['products']):
  s=SC.get(sid);p=product(sid,s['reported_whole_composition']if s else None,E(es),link='general_context',phase=s['reported_phase_scope']if s else None,notes=['Source context only; no exact physical-aliquot or replicate association.'])
  p['source_sample_label']=s['label']if s else sid
  if s:p['notes']+=[s['physical_batch_join'],'Source context kind: '+s['kind']+'.']
  if s and s['kind']=='literature_structure_context':p['notes'].append('Quoted reference cell parameters, not a current measured QD structure; no supplied coordinates.')
  r['products'].append(p)
 return sid
purity={'formamidine-acetate':'formamidine acetate purity','oa':'OA purity','oam':'OAm purity','ode':'ODE purity','toluene':'toluene purity','acetonitrile':'acetonitrile purity','hexane':'hexane purity'}
def addm(r,mid):
 if not any(m['id']==mid for m in r['materials']):
  m=MM[mid];qs={}
  if mid in purity:qs['reported_purity']=Q(next(q for q in FM[SID+'-materials']['quantities']if q['meaning']==purity[mid]),mid)
  r['materials'].append(material(mid,m['name'],m['source_formula_or_abbreviation'],m['role'],'precursor_preparation',E(m['evidence']),quantities=qs,notes=[m['scope_note'],'Source identity is not an approved molecular geometry or solution-speciation model.']))
  bind('material',mid,r,f'/materials/{len(r["materials"])-1}')
 return mid
for mid in MM:addm(R['source-materials'],mid)
def adds(r,sid):
 if any(x['id']==sid for x in r['stocks']):return sid
 s=ST[sid];components=[]
 for c in s['components']:
  qq={key(q['meaning']):Q(q,sid+' whole formulation')for q in c.get('amount_quantities',[])}
  if c.get('parts'):qq['volume_parts']=Q(c['parts'],sid+' relative-volume formulation, not an absolute charge')
  components.append({'material_id':addm(r,c['material_id']),'quantities':qq})
 prep=['fa-charge','fa-vacuum-hold','fa-nitrogen-hold']if sid=='fa-oleate-stock'and r is R['fa-oleate-preparation']else[]
 scope=('Whole prepared stock charges are distinct from the 0.51 mL injection aliquot. Final stock volume, concentration and storage are unreported. See the separate FA-oleate preparation.'if sid=='fa-oleate-stock'else'Alternative washing formulation: select only the ratio paired with the chosen source condition. Absolute solvent volumes, premixing details and repeat count are unreported.')
 r['stocks'].append({'id':sid,'name':s['name'],'components':components,'concentrations':{},'preparation_operation_ids':prep,'scope':scope,'evidence':E(s['evidence'])});bind('stock',sid,r,f'/stocks/{len(r["stocks"])-1}');return sid
adds(R['fa-oleate-preparation'],'fa-oleate-stock')
for sid in ST:adds(R['hot-injection'],sid)
def stateadd(r,sid,parents=(),kind='mixture',label=None):
 if not any(x['id']==sid for x in r['material_states']):r['material_states'].append(state(sid,label or sid.replace('-',' '),list(dict.fromkeys(parents)),kind))
 return sid
alternative_meanings={'add-oa':{'OA low volume','OA middle volume','OA high volume'},'cool-equilibrate':{'temperature low','temperature middle','temperature high'},'add-wash':{'acetonitrile parts','toluene low parts','toluene middle parts','toluene high parts'}}
context_only={'temperature-pl-acquire':{'gamma-beta transition','beta-alpha transition'},'temperature-raman-acquire':{'overlap threshold'},'thermal-aging-acquire':{'reference temperature label','normalized slope','normalized intercept'}}
for k,title,kind,section,pids in PLAN:
 r=R[k];produced={};outmap={}
 for pid in pids:
  pr=PP[pid]
  for so in pr['operations']:
   oi=len(r['operations']);oid=so['id'];pi=D['protocols'].index(pr);si=pr['operations'].index(so);sp=f'/protocols/{pi}/operations/{si}';ins=[];notes=[]
   for raw in so['inputs']:
    if pr['kind']=='measurement_or_analysis':ins.append(stateadd(r,raw,kind='sample_set',label='Separate source specimen: '+SC[raw]['label']))
    elif raw in MM:ins.append(addm(r,raw))
    elif raw in ST:ins.append(adds(r,raw))
    elif raw in outmap:ins.append(outmap[raw])
    else:
     stkind='sample_set'if pid not in['fa-oleate-preparation','qd-synthesis-family','purification-family']else'mixture'
     ins.append(stateadd(r,raw,kind=stkind,label='Separate source specimen: '+SC[raw]['label']if raw in SC else'One selected washing formulation'if raw=='selected-wash'else None))
   outs=[]
   for raw in so['outputs']:
    z=raw+'-prepared-state'if raw in ST else raw
    sk='analysis_data'if pr['kind']=='measurement_or_analysis'else'fraction'if raw in['first-precipitate','washing-waste','final-supernatant','second-precipitate','stored-supernatant']else'reaction_batch'if raw=='growing-qd'else'mixture'
    stateadd(r,z,[a for a in ins if a!='nitrogen'],sk);outmap[raw]=z;outs.append(z)
   ps={}
   for qi,q in enumerate(so['quantities']):
    if q['meaning']in alternative_meanings.get(oid,set()):notes.append('Alternative '+q['meaning']+': '+q['raw_text']+' '+str(q['unit'])+'; select only the paired condition.');continue
    if q['meaning']in context_only.get(oid,set()):notes.append('Observation or comparison context, not an acquisition setpoint: '+q['meaning']+' = '+q['raw_text']+' '+str(q['unit'])+'.');continue
    pk=key(q['meaning']);ps[pk]=Q(q,pid);TYPED.append({'source_file':'source-facts.json','source_pointer':sp+'/quantities/'+str(qi),'record_id':r['record_id'],'pointer':f'/operations/{oi}/parameters/{pk}'})
   if oid=='add-oa':ps['selected_oa_volume']=qty(None,'mL',E(so['evidence']),qualifier='Select 0.4, 0.6 or 0.8 mL from the paired condition option; not sequential charges.')
   if oid=='cool-equilibrate':ps['selected_growth_temperature']=qty(None,'degC',E(so['evidence']),qualifier='Select the paired 25, 50 or 100 °C condition; do not infer a Cartesian experiment matrix.')
   if oid=='add-wash':notes.append('Select exactly one of the three stock formulations; their components are not pooled. Absolute wash volumes are not reported.')
   if pr['kind']=='measurement_or_analysis':notes.append('Inputs denote separate source specimens or datasets, not a physically pooled mixture. Synthesis nitrogen is not inherited by acquisition.')
   env=None
   if oid=='fa-vacuum-hold':env='Vacuum; numerical pressure not reported.'
   elif oid=='fa-nitrogen-hold':env='Nitrogen; numerical pressure not reported.'
   elif pid=='qd-synthesis-family':env='Nitrogen synthesis conditions. Degassing vacuum is not explicitly specified; numerical pressure is unreported.'
   desc=so['description']+' '+(' '.join(notes))
   if so['missing_fields']:desc+=' Unreported: '+', '.join(so['missing_fields'])+'.'
   stage='characterization'if pr['kind']=='measurement_or_analysis'else'precursor_preparation'if pid=='fa-oleate-preparation'else'workup'if pid=='purification-family'else'synthesis'
   dep=list(dict.fromkeys(produced[x]for x in so['inputs']if x in produced))
   if oi and r['operations'][-1]['id']not in dep:dep.append(r['operations'][-1]['id'])
   retain='first-precipitate'if oid=='first-spin'else'final-supernatant'if oid=='second-spin'else None
   r['operations'].append(operation(oid,norm(so['action']),so['action'],E(so['evidence']),ins,outs,depends=dep,parameters=ps,stage=stage,description=desc,environment=fact(env,E(so['evidence'])),retained_fraction=retain))
   r['quality']['missing_fields']+=so['missing_fields'];OP.append({'source_protocol_id':pid,'source_operation_id':oid,'source_pointer':sp,'record_id':r['record_id'],'pointer':f'/operations/{oi}','notes':notes});bind('operation',oid,r,f'/operations/{oi}',sp)
   for z in so['outputs']:produced[z]=oid
# Paired alternatives use only values already printed in the source, with separate family IDs.
for sid,s in SC.items():
 if s['kind']not in['reaction_condition_context','purification_condition_context']:continue
 c=s['condition_scope'];den=c['OAm_OA_volume_parts'][1];temp=c['growth_temperature_C'];wash=c['acetonitrile_toluene_volume_parts'][1]
 def qf(fid,meaning,value):return next(q for q in FM[SID+'-'+fid]['quantities']if q['meaning']==meaning and q['value']==value)
 oq=next(q for q in FM[SID+'-qd-ligands']['quantities']if q['unit']=='mL'and q['value']=={2:.4,3:.6,4:.8}[den])
 tq=next(q for q in FM[SID+'-qd-equilibrate']['quantities']if q['unit']=='degC'and q['value']==temp)
 wq=next(q for q in ST['wash-1-'+str(wash)]['quantities']if q['meaning']=='toluene parts')
 aq=next(q for q in ST['wash-1-'+str(wash)]['quantities']if q['meaning']=='acetonitrile parts')
 R['hot-injection']['condition_options'].append({'id':sid,'label':s['label'],'parameters':{'growth_temperature':Q(tq,sid),'oa_volume':Q(oq,sid),'oam_volume':Q(qf('qd-ligands','OAm volume',.2),sid),'wash_acetonitrile_parts':Q(aq,sid),'wash_toluene_parts':Q(wq,sid)},'evidence':E(s['evidence'])})
 sample(R['hot-injection'],sid,s['evidence'])
R['hot-injection']['context_links'].append({'label':'FA-oleate stock preparation','url':'/records/'+PRE+'fa-oleate-preparation.html','relation':'upstream_preparation_not_whole_stock_transfer'})
def addmeasure(r,mid,sid,prop,value,es,tech='Source evidence',conditions=''):
 sample(r,sid,es);r['measurements'].append(measurement(mid,sid,prop,value,tech,E(es),conditions=conditions));return f'/measurements/{len(r["measurements"])-1}/value'
for sid,s in SC.items():
 r=R[SOWN[sid]];sample(r,sid,s['evidence']);j=next(j for j,p in enumerate(r['products'])if p['sample_id']==sid);bind('sample_context',sid,r,f'/products/{j}')
for fid,f in FM.items():
 r=R[OWN[fid]];sid='fact-context-'+fid.removeprefix(SID+'-');note='Claim class: '+f['claim_class']+'. '+quals(f)
 p=addmeasure(r,fid+'-claim',sid,'source_claim',fact(f['claim'],E(f['evidence']),note=note),f['evidence'],conditions=f['sample_scope']);FL[fid].append({'record_id':r['record_id'],'pointer':p,'source_pointer':'/claim'})
 for qi,q in enumerate(f['quantities']):
  p=addmeasure(r,fid+'-q'+str(qi+1),sid,key(q['meaning']),Q(q,f['sample_scope']),q['evidence'],conditions=f['sample_scope']);FL[fid].append({'record_id':r['record_id'],'pointer':p,'source_pointer':'/quantities/'+str(qi)})
 r['quality']['conflicts']+=[i+': '+CON[i]['description']for i in f.get('conflict_ids',[])]
for ti,t in enumerate(T['tables']):
 r=R[TO[t['id']]]
 for ri,row in enumerate(t['rows']):
  sid=row['sample_context'];note='Source row '+row['id']+'. '+row.get('source_scope','Current reported result or source calculation; no independent refit.')
  for field in['cells','additional_quantities']:
   for ci,q in enumerate(row.get(field,[])):
    ptr=addmeasure(r,t['id']+'-'+row['id']+'-'+field+str(ci),sid,key(q['meaning']),Q(q,note,force='author_derived'if t['id']=='pl-slopes'and q['meaning']!='temperature regime'else None),q['evidence'],'Cited literature'if t['id']=='reference-cells'or(t['id']=='table-s1'and row.get('source_scope')=='cited literature only')else'Printed source result',note)
    TC.append({'source_file':'source-tables.json','source_pointer':f'/tables/{ti}/rows/{ri}/{field}/{ci}','table_id':t['id'],'row_id':row['id'],'cell_kind':field,'column_index':ci,'record_id':r['record_id'],'pointer':ptr})
def owner(cat,obj):
 if cat=='facts':return OWN[obj['id']]
 if cat=='materials':return'source-materials'
 if cat=='stocks':return'fa-oleate-preparation'if obj['id']=='fa-oleate-stock'else'hot-injection'
 if cat=='protocols':return PO[obj['id']]
 if cat=='sample_contexts':return SOWN[obj['id']]
 if cat=='figures':return FO[obj['id']][0]
 if cat=='equations':return EO[obj['id']]
 if cat=='schemes':return'mechanistic-context'
 return'source-context'
PB={}
for cat in['facts','materials','stocks','protocols','sample_contexts','figures','schemes','equations','conflicts','missingness','references']:
 for i,x in enumerate(D[cat]):
  r=R[owner(cat,x)];sid=x.get('id',str(i));es=x.get('evidence')or FM[SID+'-identity']['evidence'];sp=f'/{cat}/{i}'
  ptr=addmeasure(r,'payload-'+cat+'-'+norm(sid),'source-payload-context','source_'+cat+'_payload',fact(compact(x),E(es),note='Exact structured source object; historical author-stage flags remain literal. Full source pages and raw text are excluded.'),es,'Structured source inventory')
  PB[('source-facts.json',sp)]={'record_id':r['record_id'],'pointer':ptr};bind(cat,sid,r,ptr,sp)
for i,t in enumerate(T['tables']):
 r=R[TO[t['id']]];sp=f'/tables/{i}';es=t.get('evidence')or t['rows'][0]['cells'][0]['evidence'];ptr=addmeasure(r,'payload-table-'+t['id'],'source-table-context','source_table_payload',fact(compact(t),E(es),note='Complete printed cell matrix and headers; blank values remain missing and source references remain distinct.'),es,'Structured source table')
 PB[('source-tables.json',sp)]={'record_id':r['record_id'],'pointer':ptr};bind('table',t['id'],r,ptr,sp)
for u in I['units']:
 for x in u['extraction_targets']:
  if(x['file'],x.get('json_pointer'))in PB:UL[u['id']].append(PB[(x['file'],x['json_pointer'])])
  else:
   rr=R['mechanistic-context'if u['kind']=='conceptual_figure'else'source-context'];safe={k:u[k]for k in['id','kind','title','summary','source_payload_ids']};safe['public_source_text_included']=False
   ptr=addmeasure(rr,'unit-'+u['id'],'source-unit-context','source_unit_definition',fact(compact(safe),E(u['evidence']),note='Source provenance only; no raw text or complete source-page image in public assets.'),u['evidence'],'Source inventory');UL[u['id']].append({'record_id':rr['record_id'],'pointer':ptr})
for r in R.values():
 r['quality']['missing_fields']=list(dict.fromkeys(r['quality']['missing_fields']));r['quality']['conflicts']=list(dict.fromkeys(r['quality']['conflicts']))
for k in['ligand-results','wash-results','growth-results','temperature-results','raman-results','aging-results']:
 R['hot-injection']['context_links'].append({'label':R[k]['method'],'url':'/records/'+R[k]['record_id']+'.html','relation':'source_comparison_not_exact_aliquot_pair'})
errors=[e for r in R.values()for e in validate_record(r)];save('schema-errors.json',errors);assert not errors,errors[:20]
assert len(OP)==21 and len(TC)==127 and all(FL.values())and all(UL.values())
assert not any(v['eligible']for r in R.values()for v in eligibility(r).values());assert len(set(build_groups(list(R.values())).values()))==1
manifest=[]
for r in R.values():
 p=O/'records'/(r['record_id']+'.json');save('records/'+p.name,r);manifest.append({'record_id':r['record_id'],'path':str(p),'sha256':sha(p),'record_type':r['record_type'],'operations':len(r['operations']),'measurements':len(r['measurements'])})
save('record-boundary-plan.json',{'source_id':SID,'records':[{'record_id':PRE+k,'title':t,'record_type':kind,'reader_section':sec,'source_protocol_ids':pids}for k,t,kind,sec,pids in PLAN],'paired_condition_scope':'Nine source-defined comparison contexts, not a Cartesian design; the repeated optimum does not establish shared aliquots.','one_route':True,'source_operations':21})
save('source-to-field-coverage.json',{'facts':[{'source_fact_id':k,'canonical_bindings':v}for k,v in FL.items()],'source_units':[{'source_unit_id':k,'canonical_bindings':v}for k,v in UL.items()],'source_objects':OB,'table_cells':TC,'operations':OP,'operation_quantities':TYPED,'source_freeze_sha256':sha(overlay/'package-freeze.json')})
save('source-owner-map.json',{'fact_owner':OWN,'sample_owner':SOWN,'table_owner':TO,'figure_owner':FO,'equation_owner':EO,'protocol_owner':PO,'section_by_record':{PRE+k:sec for k,t,kind,sec,pids in PLAN}})
counts={'records':len(R),'source_operations':21,'operation_instances':len(OP),'materials':sum(len(r['materials'])for r in R.values()),'stocks':sum(len(r['stocks'])for r in R.values()),'measurements':sum(len(r['measurements'])for r in R.values()),'condition_options':9}
save('record-manifest.json',{'status':'private_author_draft_pending_distinct_canonical_review','author':'/root/norberg2004_extract','source_id':SID,'source_generation':1,'source_freeze_sha256':sha(overlay/'package-freeze.json'),'source_audit_path':str(audit),'source_audit_sha256':sha(audit),'source_overlay_path':str(overlay),'records':manifest,'counts':counts,'eligible_training_tasks':0,'current_source_audit_status':'passed','effective_source_files':{n:{'path':str(effective(n)),'sha256':sha(effective(n))}for n in['source-facts.json','source-inventory.json','source-tables.json','original-assets-manifest.json','page-coverage.json']}})
print(json.dumps({'status':'private_canonical_draft_valid',**counts}))
