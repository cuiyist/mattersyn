"""Private academic Morrison reader with exact canonical pointers and selected excerpts."""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import json,hashlib,re,sys
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;C=P/'canonical-proposal'/'v1';O=P/'public-review-proposal'/'v1';O.mkdir(parents=True,exist_ok=True)
S=Path('[local path redacted]');SID='morrison2017';PRE='morrison-2017-'
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,x):(O/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def norm(x):return re.sub('[^a-z0-9]+','-',str(x).lower()).strip('-')
def esc(x):return str(x).replace('~','~0').replace('/','~1')
def resolve(x,p):
 for t in p.strip('/').split('/')if p else []:x=x[int(t)]if isinstance(x,list)else x[t.replace('~1','/').replace('~0','~')]
 return x
def uniq(x):return list({json.dumps(a,ensure_ascii=False,sort_keys=True):a for a in x}.values())
def prose(x):
 x=str(x)
 for a,b in [('approximately300','approximately 300'),('publicationOctober6,2017','publication on October 6, 2017'),('repostOctober9,2017','reposting on October 9, 2017'),('FigureS','Figure S'),('TableS','Table S'),('Figure7','Figure 7'),('Figures9','Figures 9'),('QY1.53','QY 1.53'),('QY7','QY 7'),('CdS a=','CdS a = '),('mono­layer','monolayer'),('near1:1Cd:S','near 1:1 Cd:S'),('DMSO50','DMSO at 50'),('thioureaN–H','thiourea N–H'),('precursorN–H','precursor N–H'),('at50','at 50'),('At50','At 50'),('over12','over 12'),('precursor11.2','precursor 11.2'),('aniline5.0','aniline 5.0'),('thiourea9.8','thiourea 9.8'),('appears1','appears at 1'),('gone7','gone by 7'),('Precursor209','Precursor 209'),('at193','at 193'),('thiourea180','thiourea 180'),('appearing1','appearing at 1'),('precursor208.0','precursor 208.0'),('and0.19','and 0.19'),('Expected8.8','Expected 8.8'),('found20.67','found 20.67'),('of3.65','of 3.65'),('thickness2.5','thickness 2.5'),('cited1.8','cited 1.8'),('obtain0.7','obtain 0.7'),('one-third','one third'),('all27','all 27'),('a4.10','a = 4.10'),('c6.83','c = 6.83'),('bulk4.13','bulk 4.13'),('deviations−0.83','deviations −0.83'),('labels3303','labels 3303'),('interprets1493','interprets 1493'),('pseudo-sp2N','pseudo-sp² N'),('CCDC1560097','CCDC 1560097')]:x=x.replace(a,b)
 x=re.sub(r'\b(prints|says|mass|gives|from|Keep|as|Printed|defined|after|say|and|fraction|reference|Approximately|approximately|weak|show|October)(?=\d)',r'\1 ',x)
 x=x.replace('labelsTHF','labels THF').replace('DMSO70','DMSO at 70').replace('Fluorolog3','Fluorolog 3')
 x=re.sub(r'(?<=\d)(?=(?:nm|mm|mL|mM|mg|mol|mmol|MHz|keV|ppm|min|h|g)(?:\b|\d))',' ',x)
 x=re.sub(r'(?<=mL)(?=\d)',' ',x)
 x=re.sub(r'(?<=\d)(?=°C|Å)',' ',x)
 x=re.sub(r',(?=[A-Za-z0-9])',', ',x)
 x=re.sub(r';(?=\S)','; ',x)
 x=re.sub(r'\s*±\s*',' ± ',x)
 x=x.replace('1, 3-diphenyl','1,3-diphenyl').replace('breakdown.191.37','breakdown. The 191.37').replace('52.53atom%','52.53 atom%')
 return x
D=read(P/'source-facts.json');I=read(P/'source-inventory.json');A=read(P/'original-assets-manifest.json');PC=read(P/'page-coverage.json');FR=read(P/'package-freeze.json');MAN=read(C/'record-manifest.json');COV=read(C/'source-to-field-coverage.json')
AUDIT_PATH=P/'source-independent-audit'/'independent-audit-v2.json';AUDIT=read(AUDIT_PATH)
assert AUDIT['status']=='passed'and AUDIT['package_freeze_sha256']==sha(P/'package-freeze.json')and AUDIT['source_facts_sha256']==sha(P/'source-facts.json')
R={r['record_id']:read(r['path'])for r in MAN['records']};U={u['id']:u for u in I['source_units']};FM={f['id']:f for f in D['facts']};TM={t['id']:t for t in D['tables']};PM={p['id']:p for p in D['protocols']}
for r in MAN['records']:assert sha(r['path'])==r['sha256']
SECTIONS=[{'id':i,'title':t,'items':[]}for i,t in [('precursors','Precursors'),('protocol','Synthesis protocol'),('structures','Final structures'),('properties','Properties'),('intuition','Chemical intuition'),('sources','Sources and limitations')]]
ITEM={};UNIT={};FIELD={};OPS={};MAT={};STOCK={};PRODUCT={};MEAS={}
def evidence(es):
 out=[]
 for e in es:
  if 'document_role'in e:out.append({k:e[k]for k in ['source_id','document_role','pdf_page','printed_page','locator']});continue
  m=re.search(r'(MAIN|SI) PDF p\. (\d+) \(printed ([^)]+)\)',e['locator'])
  out.append({'source_id':SID,'document_role':m[1].lower()if m else'main','pdf_page':int(m[2])if m else None,'printed_page':m[3]if m else None,'locator':e['locator']})
 return out
def section_for_record(rid):
 k=rid.removeprefix(PRE)
 if k in ['reagents-methods','precursor-preparation','precursor-crystallization','precursor-properties']:return'precursors'
 if k=='single-crystal-acquisition':return'structures'
 if k in ['starting-belt-reference','mechanistic-context']:return'intuition'
 if k=='source-context':return'sources'
 if k in ['thick-shell-characterization','monolayer-characterization','powder-comparison']:return'properties'
 return'protocol'
def add(section,i,title,text,es=None,unit=None,scope='source_context'):
 assert i not in ITEM,i
 item={'id':i,'title':title,'text':prose(text),'claim_type':'source_reported_context','sample_scope':{'formulations':[],'physical_batch_id':None,'scope_kind':scope,'state':title,'link_limit':'These are source-defined preparation, measurement, model or reference contexts. Nominal composition does not identify one physical batch across techniques.','canonical_sample_links':[]},'evidence':uniq(evidence(es or[])),'source_locators':[e['locator']for e in es or[]],'canonical_links':[],'notes':[],'facts':[],'source_audit_unit_ids':[unit]if unit else[],'source_fact_ids':[],'original_assets':[],'training_eligible':False}
 ITEM[i]=item;next(s for s in SECTIONS if s['id']==section)['items'].append(item)
 if unit:UNIT.setdefault(unit,[]).append(i)
 return item
UNITB={x['source_unit_id']:x['canonical_bindings']for x in COV['source_units']}
TABLE_EXTRA={'table-s1':'All 26 non-hydrogen rows retain the printed fractional-coordinate scale, equivalent displacement parameters and standard uncertainties. Negative or greater-than-one coordinates are preserved without wrapping.','table-s2':'All 26 rows retain the literal U11, U22, U33, U23, U13, U12 column order and the printed displacement scaling. These values have not been used to construct or approve an atomic model.','table-s3':'All 20 hydrogen rows retain their printed coordinate and displacement values. Only the N–H positions have reported uncertainties; the riding-hydrogen distinction remains explicit.','table-s4':'All five hydrogen-bond rows and four symmetry transformations are retained, including the THF oxygen label O(1S).','table-1':'The measured diffraction-crystal dimensions are distinct from the approximate mounting dimensions. The cell, space group, refinement statistics and formula apply to the THF-solvated precursor crystal.','table-2':'The six selected distances and six angles retain their labels and standard uncertainties. The prose/table S4 versus S4′ discrepancy remains unresolved.','table-s5':'Three elemental-analysis columns retain four upper bounds and the missing sulfur entry. The hypothetical intact-ligand sulfur calculation is a model, not an experimental synthesis charge.','figure-s7-eds-table':'All printed channel counts, errors, factors and percentages are retained. Blank fields stay missing; zero net counts are not substituted into unreported percentage cells. The THF caption and main-text DMSO association remain distinct.'}
for uid,u in U.items():
 binds=UNITB[uid];rid=binds[0]['record_id'];section=section_for_record(rid);title=u['title'];text=u['title'];scope=u['kind']
 if uid in FM:
  f=FM[uid];title=f['title'];text=f['claim'];scope=f['sample_scope']
  if f['claim_class']in ['author_interpretation','cited_context']:section='intuition'
 elif uid in TM:
  title=TM[uid]['title'];text=TABLE_EXTRA[uid];scope=TM[uid]['sample_scope']
  section='structures'if scope=='precursor-crystal'else'properties'
  if scope=='precursor-crystal':text+=' The measured atomic data describe Cd(PTC)₂·THF. They do not supply CdSe/CdS product coordinates or qualify a recipe–structure training pair.'
 elif uid in PM:title=PM[uid]['title'];text='This procedure preserves the source-defined sequence and its unreported fields. Separate control branches and measurement aliquots are not treated as independent synthesis repetitions.'
 elif uid in [f['id']for f in D['figures']]:
  f=next(f for f in D['figures']if f['id']==uid);title=f['label']+': '+f['title'];text=f['scientific_scope'];scope=f['sample_scope'];section='structures'if uid in ['figure-2','figure-s4','figure-9','figure-s9-ab','figure-s9-c']else'intuition'if uid in ['graphical-abstract','figure-1']else'properties'
 elif uid in [s['id']for s in D['schemes']]:
  s=next(s for s in D['schemes']if s['id']==uid);text=s['scope_note'];title=s['title'];section='intuition';scope=s['sample_scope']
 elif uid in [e['id']for e in D['equations']]:
  e=next(e for e in D['equations']if e['id']==uid);text=e['description'];title=uid.replace('-',' ').capitalize();section='structures'if e['kind']=='crystallographic_definition'or uid=='refinement-objective'else'intuition'
  text={'equation-1':'Base deprotonation of Cd(PTC)₂ is proposed to produce CdS, PhNCS, displaced PTC⁻ and BH⁺.','equation-2':'Protonation of PTC⁻ by BH⁺ is proposed to produce aniline and CS₂ while regenerating the base.','equation-3':'Aniline reacts with PhNCS to form 1,3-diphenylthiourea in the proposed pathway.'}.get(uid,text)
 elif u['kind']=='reference':section='sources';title=('SI reference 'if uid.startswith('si-')else'Reference ')+uid.rsplit('-',1)[1];text=u['title']+' This cited source was not separately downloaded or read for this contribution.'
 else:section='sources'
 item=add(section,'source-'+norm(uid),title,text,u['evidence'],uid,scope)
 for b in binds:item['canonical_links'].append({'record_id':b['record_id'],'json_pointer':b['pointer'],'relation':'Exact canonical field for this source item; source context and missingness retained.'})
 if uid in FM:
  for cid in FM[uid]['conflict_ids']:item['notes'].append(prose(next(c['description']for c in D['contradictions']if c['id']==cid)))
for rid,r in R.items():
 item=add(section_for_record(rid),'record-'+rid,r['title'].split(' · ',1)[1],r['method']+'. This record represents a preparation, control or observation context; it does not enumerate physical batches.')
 item['canonical_links']=[{'record_id':rid,'json_pointer':'','relation':'Private canonical author proposal; independent canonical/reader approval remains pending.'}]
 item['notes']+=list(map(prose,r['quality']['missing_fields']+r['quality']['conflicts']))
def displayed(q):
 if q['value']is not None:return q['value']
 lo,hi=q.get('minimum'),q.get('maximum')
 if lo is not None and hi is not None:return str(lo)+'–'+str(hi)
 if lo is not None:return('> 'if q.get('minimum_exclusive')else'≥ ')+str(lo)
 if hi is not None:return('< 'if q.get('maximum_exclusive')else'≤ ')+str(hi)
 return'Not reported'
def attach(item,rid,ptr,label,q,sid=None):
 assert(rid,ptr)not in FIELD,(rid,ptr)
 ff={'id':rid+'::'+ptr,'label':label,'value':displayed(q),'unit':q.get('unit'),'status':q['status'],'approximate':q.get('approximate',False),'basis':'exact_canonical_field','qualifier':prose(' '.join(q.get(k,'')for k in ['basis','qualifier','note'])),'evidence':evidence(q['evidence']),'canonical_record_id':rid,'json_pointer':ptr,'canonical_quantity':deepcopy(q),'presentation_kind':'exact_quantity','training_eligible':False}
 if sid:ff['sample_id']=sid
 item['facts'].append(ff);FIELD[(rid,ptr)]=(item['id'],ff);return ff
PTRUNIT={}
for x in COV['source_units']:
 for b in x['canonical_bindings']:PTRUNIT.setdefault((b['record_id'],b['pointer']),x['source_unit_id'])
TABLEDEF={(x['record_id'],x['pointer']):x['table_id']for x in COV['table_definitions']}
for rid,r in R.items():
 for n,op in enumerate(r['operations']):
  ptr=f'/operations/{n}';uid=PTRUNIT[(rid,ptr)];item=add('properties'if op['stage']=='characterization'else section_for_record(rid),'operation-'+op['id'],op['label'],op['description'],op['evidence'],scope='source_operation')
  names={m['id']:m['name']for m in r['materials']}|{s['id']:s['name']for s in r['stocks']}|{s['id']:s['name']for s in r['material_states']}
  item['source_audit_unit_ids']=[uid];UNIT[uid].append(item['id'])
  item['operation_context']={'record_id':rid,'operation_id':op['id'],'json_pointer':ptr,**{k:deepcopy(op[k])for k in ['stage','branch','depends_on','environment','inputs','outputs','retained_fraction','endpoint']},'material_flow_labels':{k:names[k]for k in op['inputs']+op['outputs']},'diagram_binding_status':'pending_independent_visual_binding'}
  item['canonical_links'].append({'record_id':rid,'json_pointer':ptr,'relation':'Exact operation and source-scoped material flow.'})
  item['notes']+=['Inputs: '+', '.join(names[k]for k in op['inputs'])+'.','Outputs: '+', '.join(names[k]for k in op['outputs'])+'.']
  if op['retained_fraction']:item['notes'].append('Retained fraction: '+names[op['retained_fraction']]+'.')
  for k,q in op['parameters'].items():attach(item,rid,ptr+'/parameters/'+esc(k),k.replace('_',' ').capitalize(),q)
  for k in ['environment','endpoint']:attach(item,rid,ptr+'/'+k,k.capitalize(),op[k])
  OPS[rid+'::'+op['id']]=item['id']
 for n,m in enumerate(r['materials']):
  iid='material-'+m['id'];item=ITEM.get(iid)or add('precursors',iid,m['name'],'The source names this material in the role given below. Its formula or condensed identity does not establish an isolated molecular geometry, hydration state or solution speciation.',m['evidence'],scope='material_identity')
  ptr=f'/materials/{n}';item.setdefault('material_identities',[]).append({'source_material_id':m['id'],'name':m['name'],'formula':m['formula'],'role':m['role'],'canonical_record_id':rid,'json_pointer':ptr,'exact_molecular_asset_binding_approved':False})
  item['notes']+=list(map(prose,m['notes']));item['canonical_links'].append({'record_id':rid,'json_pointer':ptr,'relation':'Exact record-specific material identity, role and stage.'});MAT[rid+'::'+m['id']]=iid
  for k,q in m['quantities'].items():attach(item,rid,ptr+'/quantities/'+esc(k),m['name']+' · '+k,q)
 for n,st in enumerate(r['stocks']):
  ptr=f'/stocks/{n}';item=add('precursors','stock-'+st['id'],st['name'].capitalize(),st['scope'],st['evidence'],scope='stock_context');item['stock_contexts']=[{'record_id':rid,'json_pointer':ptr,**deepcopy(st),'molecular_bindings_approved':False}];item['canonical_links'].append({'record_id':rid,'json_pointer':ptr,'relation':'Reported solution formulation; no extra physical charge.'});STOCK[rid+'::'+st['id']]=item['id']
  item['notes'].append('Components: '+', '.join(next(m['name']for m in r['materials']if m['id']==c['material_id'])for c in st['components'])+'.')
  for k,q in st['concentrations'].items():attach(item,rid,ptr+'/concentrations/'+esc(k),k.replace('_',' ').capitalize(),q)
 for n,m in enumerate(r['measurements']):
  ptr=f'/measurements/{n}/value';uid=PTRUNIT[(rid,ptr)];item=ITEM[UNIT[uid][0]];label=m['property'].replace('_',' ').capitalize();f=attach(item,rid,ptr,label,m['value'],m['sample_id']);MEAS[rid+'::'+m['id']]=item['id']
  if(rid,ptr)in TABLEDEF:f['value']=json.loads(m['value']['value']);f['label']='Table definitions, column order and source notes';f['presentation_kind']='curated_source_inventory';f['basis']='exact_canonical_payload_with_academic_display'
 for n,p in enumerate(r['products']):
  ptr=f'/products/{n}';item=ITEM['record-'+rid];item.setdefault('product_contexts',[]).append({'record_id':rid,'json_pointer':ptr,**deepcopy(p),'atomic_asset_binding_approved':False});item['canonical_links'].append({'record_id':rid,'json_pointer':ptr,'relation':'Source-scoped specimen, model or reference context.'});PRODUCT[rid+'::'+p['sample_id']]=item['id']
  for k in ['composition','phase','morphology','surface']:attach(item,rid,ptr+'/'+k,p['source_sample_label']+' · '+k,p[k],p['sample_id'])
 for k,q in r['intended_target'].items():attach(ITEM['record-'+rid],rid,'/intended_target/'+k,'Intended target · '+k,q)
FACTMAP={}
for row in COV['facts']:
 fid=row['source_fact_id'];out=[]
 for b in row['canonical_bindings']:
  iid,f=FIELD[(b['record_id'],b['pointer'])];f.setdefault('source_fact_ids',[]).append(fid);ITEM[iid]['source_fact_ids'].append(fid);out.append({**b,'reader_item_id':iid,'reader_fact_id':f['id']})
 FACTMAP[fid]=out
TABLEMAP={}
for row in COV['table_cells']:
 b=row['canonical_bindings'][0];iid,f=FIELD[(b['record_id'],b['pointer'])];f['source_table_cell_id']=row['source_cell_id'];TABLEMAP[row['source_cell_id']]={**b,'reader_item_id':iid,'reader_fact_id':f['id']}
GROUP={k:[]for k in ['figures','tables','schemes','equations','source_notes']};PUBLIC=[]
ASSET_UNITS={a['id']:[a['id']]for a in A['assets']}
ASSET_UNITS['equations-1-3']=['equation-1','equation-2','equation-3']
ASSET_UNITS['table-s5-and-calculation']=['table-s5','hypothetical-sulfur-mass-balance']
ROUTE_ASSOC={'figure-3':['excess-precursor-rt','excess-precursor-hot'],'figure-4':['excess-precursor-hot'],'figure-5':['excess-precursor-hot'],'figure-7':['monolayer-shell'],'figure-8':['monolayer-shell'],'figure-9':['monolayer-shell'],'figure-s9-ab':['monolayer-shell'],'figure-s9-c':['monolayer-shell'],'figure-s6':['decomposition-thf','decomposition-dmso-hot'],'figure-s7':['decomposition-thf']}
for a in A['assets']:
 assert sha(a['path'])==a['sha256']
 ids=ASSET_UNITS[a['id']];uid=ids[0];item=ITEM[UNIT[uid][0]];e=a['evidence'][0]
 group='figures'if a['id'].startswith('figure-')else'tables'if a['id'].startswith('table-')else'schemes'if a['id'].startswith('scheme-')else'equations'if a['id']=='equations-1-3'else'source_notes'
 public='assets/figures/'+SID+'/'+Path(a['path']).name;rids=sorted({b['record_id']for x in ids for b in UNITB[x]}|{PRE+k for k in ROUTE_ASSOC.get(a['id'],[])})
 entry={'id':SID+'-'+a['id'],'label':item['title'],'caption_paraphrase':item['text'],'document_role':e['document_role'],'page':e['pdf_page'],'printed_page':e['printed_page'],'sample_scope':item['sample_scope'],'sample_links':rids,'sample_linkage':'These are source-family context links, not an exact physical-aliquot or atomic-structure pairing. Figure 7 alone explicitly joins its red absorption and blue PL specimen.','public_asset':public,'public_asset_sha256':a['sha256'],'asset_provenance':{'source_sha256':a['source_sha256'],'source_pdf_page':e['pdf_page'],'crop_normalized':a['crop_normalized'],'source_render_scale':a['source_render_scale'],'pixel_dimensions':a['pixel_dimensions'],'transformation':'Original selected crop; no painted labels, reconstructed plot or full-page attachment.'},'source_locators':[e['locator']],'notes':item['notes'].copy(),'reader_render_verified':False,'reviewed':False,'training_eligible':False}
 if uid in TM:entry['source_rows']=deepcopy(TM[uid]['rows']);entry['source_notes']=deepcopy(TM[uid]['notes'])
 if a['id']in ['figure-2','figure-s4','table-1','table-2','table-s1','table-s2','table-s3','table-s4']:entry['notes'].append('THF-solvated Cd(PTC)₂ precursor crystal only. These data do not give CdSe/CdS product coordinates.')
 if a['id']in ['figure-4','figure-9','figure-s9-ab','figure-s9-c']:entry['notes'].append('Image scale bars are not measured particle diameters. Combined shell thickness is distinct from thickness per broad face.')
 GROUP[group].append(entry);PUBLIC.append({'id':entry['id'],'private_path':a['path'],'public_asset':public,'sha256':a['sha256'],'selected_original_only':True,'publication_approved':False})
 for unit in ids:
  ii=ITEM[UNIT[unit][0]];ii['original_assets'].append({'id':entry['id'],'label':'Open original '+entry['label'],'public_asset':public,'public_asset_sha256':a['sha256']})
for t in D['tables']:
 if any(x.get('id')==SID+'-'+t['id']or t['id']=='table-s5'and x['id']==SID+'-table-s5-and-calculation'for x in GROUP['tables']):continue
 GROUP['tables'].append({'id':SID+'-'+t['id'],'label':t['title'],'source_rows':deepcopy(t['rows']),'source_notes':deepcopy(t['notes']),'source_locators':[e['locator']for e in t['evidence']],'scope':'Complete typed table; original is within Figure S7.'})
for item in ITEM.values():
 item['canonical_links']=uniq(item['canonical_links']);item['notes']=uniq(item['notes']);item['source_fact_ids']=uniq(item['source_fact_ids'])
 for f in item['facts']:
  if f.get('sample_id'):
   rid=f['canonical_record_id'];n=next(n for n,p in enumerate(R[rid]['products'])if p['sample_id']==f['sample_id']);item['sample_scope']['canonical_sample_links'].append({'record_id':rid,'sample_id':f['sample_id'],'json_pointer':f'/products/{n}','relation':'Exact canonical source context; no new physical sample join.'})
 item['sample_scope']['canonical_sample_links']=list({(x['record_id'],x['json_pointer']):x for x in item['sample_scope']['canonical_sample_links']}.values())
 # Every figure/protocol card inherits supported context pointers already present in its canonical links.
 for b in item['canonical_links']:
  if b['json_pointer'].startswith('/measurements/'):
   mm=resolve(R[b['record_id']],'/'.join(b['json_pointer'].split('/')[:3]));sid=mm['sample_id'];n=next(i for i,p in enumerate(R[b['record_id']]['products'])if p['sample_id']==sid)
   item['sample_scope']['canonical_sample_links'].append({'record_id':b['record_id'],'sample_id':sid,'json_pointer':f'/products/{n}','relation':'Supported canonical measurement context; no new specimen join.'})
 item['sample_scope']['canonical_sample_links']=list({(x['record_id'],x['json_pointer']):x for x in item['sample_scope']['canonical_sample_links']}.values())
docs=[{'role':d['role'],'filename':Path(d['original_path']).name,'sha256':d['source_sha256'],'page_count':d['page_count'],'pages':[{'page':p['pdf_page'],'printed_page':p['printed_page'],'text_read':p['text_read'],'visual_review':p['visual_inspection'],'sections':[p['covered_content']]}for p in d['pages']]}for d in PC['documents']]
routes={PRE+k:[PRE+x for x in ['precursor-preparation','precursor-crystallization','precursor-properties','single-crystal-acquisition','reagents-methods','starting-belt-reference','mechanistic-context','source-context',('thick-shell-characterization'if k=='excess-precursor-hot'else'monolayer-characterization')]]for k in ['excess-precursor-hot','monolayer-shell']}
counts={'reader_items':len(ITEM),'source_units':len(UNIT),'source_facts':len(FACTMAP),'source_fact_bindings':sum(map(len,FACTMAP.values())),'source_table_cells':len(TABLEMAP),'typed_reader_fields':len(FIELD),'canonical_records':len(R),'operations':len(OPS),'material_slots':len(MAT),'stock_slots':len(STOCK),'sample_context_slots':len(PRODUCT),'measurements':len(MEAS),'selected_original_assets':len(PUBLIC),'full_page_public_assets':0,'main_pages':10,'si_pages':17,'eligible_training_rows':0,'atomic_structure_assets':0}
review={'schema_version':'1.0','paper_id':SID,'doi':D['doi'],'title':D['title'],'paper':{'authors':D['authors'],'year':2017,'journal':'Inorganic Chemistry','volume':56,'pages':'12920–12929'},'source_group':SID,'review_scope':'supplied_main_and_matched_si','documents':docs,'supporting_information':{'status':'matched_and_independently_source_reviewed','matched_local_si_count':1,'pdf_pages':17,'scope':'All supplied pages were read and visually inspected; distinct source audit passed corrected revision 2. Canonical/reader audits remain separate pending gates. Precursor coordinates do not supply product coordinates.'},'document_identity_verification':{'method':'Exact source hashes; matching title and all six authors; main Associated Content and complete SI figure/table continuity. The SI cover does not print the DOI.'},'coverage_status':'private_author_reader_proposal','independent_audit':'Independent source audit passed revision 2. Canonical, reader, molecular/apparatus and browser approvals remain pending.','publication_status':'Private proposal only.','source_review_promoted':False,'training_eligible':False,'recipe_inventory':[{'id':rid,'label':r['title'],'record_ids':[rid],'record_type':r['record_type'],'status':'author_draft_pending_independent_review','scope':'A record identifies a preparation, control or observation context; record counts are not experiment counts.','gaps':r['quality']['missing_fields']}for rid,r in R.items()],'characterization_inventory':{'reader_item_ids':[i['id']for s in SECTIONS if s['id']in ['structures','properties']for i in s['items']]},'chemical_intuition':{'reader_item_ids':[i['id']for s in SECTIONS if s['id']=='intuition'for i in s['items']]},'reader_contract':{'version':'1.0','section_ids':[s['id']for s in SECTIONS]},'reader_sections':SECTIONS,**GROUP,'remaining_gaps':[prose(g['description'])for g in D['gaps']if g['id']!='G10']+['The extraction’s historical G10 pending-audit note is resolved by the independent source revision-2 audit. Canonical/reader, visual/model, browser, training and publication gates remain separate.']+['Molecular, product/crystal, apparatus and browser bindings are pending separate qualification.'],'evidence_conflicts':[{**deepcopy(c),'description':prose(c['description'])}for c in D['contradictions']],'route_evidence_contexts':routes,'route_evidence_scope_notes':{'all':'Record-ID arrays expose source context without assigning one physical specimen to every technique. Only explicitly stated same-specimen relationships are retained.','precursor_structure':'The measured precursor crystal is a THF solvate; no supplied CIF is reconstructed or model-approved here. Product belts have no atomic-coordinate file.','upstream':'Cited preparations of NH4PTC and starting CdSe belts remain unavailable in this local source pair.'},'material_evidence_records':{'CdSe/CdS':[rid for rid in R if R[rid]['material']['formula']=='CdSe/CdS'],'CdS':[rid for rid in R if R[rid]['material']['formula']=='CdS'],'Cd(PTC)2':[rid for rid in R if rid.endswith(('precursor-preparation','precursor-crystallization','precursor-properties','single-crystal-acquisition'))]},'counts':counts}
save('morrison2017.json',review)
save('reader-bindings-proposal.json',{'source_id':SID,'status':'private_unapproved','reader_sha256':sha(O/'morrison2017.json'),'original_assets':PUBLIC,'operation_to_reader_item':OPS,'material_to_reader_item':MAT,'stock_to_reader_item':STOCK,'product_to_reader_item':PRODUCT,'molecular_apparatus_bindings_approved':False,'publication_approved':False})
save('source-item-coverage.json',{'source_units':UNIT,'source_facts':FACTMAP,'table_cells':TABLEMAP,'canonical_field_map':[{'record_id':rid,'json_pointer':ptr,'reader_item_id':row[0],'reader_fact_id':row[1]['id']}for(rid,ptr),row in FIELD.items()],'measurement_to_reader_item':MEAS,'private_canonical_manifest_sha256':sha(C/'record-manifest.json')})
checks=[]
def ck(name,ok):checks.append({'check':name,'passed':bool(ok)})
for(rid,ptr),(iid,f)in FIELD.items():ck(iid+' '+ptr+' typed canonical equality',resolve(R[rid],ptr)==f['canonical_quantity'])
for item in ITEM.values():
 for b in item['canonical_links']:ck(item['id']+' canonical link resolves',resolve(R[b['record_id']],b['json_pointer'])is not None)
 for b in item['sample_scope']['canonical_sample_links']:ck(item['id']+' sample link resolves',resolve(R[b['record_id']],b['json_pointer'])['sample_id']==b['sample_id'])
for a in PUBLIC:ck(a['id']+' candidate excerpt hash',sha(a['private_path'])==a['sha256'])
ck('Complete source units/facts/tables',set(UNIT)==set(U)and set(FACTMAP)==set(FM)and len(TABLEMAP)==471)
ck('All operation/material/stock/product/measurement slots represented',len(OPS)==24 and len(MAT)==64 and len(STOCK)==5 and len(PRODUCT)==41 and len(MEAS)==822)
ck('Six academic/source sections exact',[s['id']for s in SECTIONS]==['precursors','protocol','structures','properties','intuition','sources'])
ck('Only selected excerpts proposed',len(PUBLIC)==30 and not any('source-render'in a['public_asset']or'private/'in a['public_asset']for a in PUBLIC))
ck('No raw local source paths in proposed reader',not re.search(r'[A-Z]:[\\/]',json.dumps(review)))
ck('Route contexts are record-ID arrays',all(isinstance(a,list)and all(r in R for r in a)for a in routes.values()))
ck('Source and canonical files remain hash-exact',all(sha(p)==h for p,h in FR['bound_files'].items())and all(sha(r['path'])==r['sha256']for r in MAN['records']))
assert all(c['passed']for c in checks),[c for c in checks if not c['passed']]
save('author-validation.json',{'status':'author_pointer_transport_and_contract_checks_passed','author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'check_count':len(checks),'checks':checks,'counts':counts,'independent_source_audit':'passed_revision_2_separate_from_canonical_reader_review','independent_canonical_reader_audit':'pending','browser_visual_gate':'not_performed','site_written':False,'published':False})
inputs={str(p):sha(p)for p in [AUDIT_PATH,P/'package-freeze.json',P/'source-facts.json',P/'source-inventory.json',P/'source-tables.json',P/'page-coverage.json',P/'original-assets-manifest.json',C/'record-manifest.json',C/'source-to-field-coverage.json',S/'scripts/build_paper_reviews.py',S/'dist/source-evidence.mjs']}
save('reader-manifest.json',{'schema':'mattersyn-private-reader-proposal/1','source_id':SID,'version':1,'author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'status':'private_author_draft_source_audit_passed_canonical_reader_audit_pending','input_hashes':inputs,'outputs':{n:sha(O/n)for n in ['morrison2017.json','reader-bindings-proposal.json','source-item-coverage.json','author-validation.json']},'author_script_sha256':sha(__file__),'counts':counts,'published':False})
print(json.dumps(counts));print('READER',sha(O/'morrison2017.json'));print('MANIFEST',sha(O/'reader-manifest.json'))
