"""Six-section private Matuhina reader; exact canonical fields and original crops."""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import json,hashlib,re
P=Path(__file__).resolve().parent;C=P/'canonical-proposal/v1';O=P/'public-review-proposal/v1';O.mkdir(parents=True,exist_ok=True)
assert not(C/'package-manifest.json').exists(),'Frozen proposals require a preserved revision.'
S=Path('[local path redacted]');SID='matuhina2023';PRE='matuhina-2023-'
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def norm(x):return re.sub('[^a-z0-9]+','-',str(x).lower()).strip('-')
def esc(x):return str(x).replace('~','~0').replace('/','~1')
def resolve(x,p):
 for t in p.strip('/').split('/')if p else[]:x=x[int(t)]if isinstance(x,list)else x[t.replace('~1','/').replace('~0','~')]
 return x
def uniq(x):return list({json.dumps(a,ensure_ascii=False,sort_keys=True):a for a in x}.values())
def prose(x):
 x=str(x).replace('degC','°C').replace('angstrom','Å')
 x=re.sub(r'\b(Figure|Table)(S?\d)',r'\1 \2',x)
 x=re.sub(r'\b(at|around|after|about|from|to|over|near|below|above|under|reports|gives|than|retains|of|and|sample|optimized|main|states|for|in|with|the|before|versus|time|interval|gap|cubic|rhombohedral|wavelength|excitation)(?=[<>~\d])',r'\1 ',x,flags=re.I)
 x=re.sub(r'(?<=\d)(nm|µs|ps|ns|meV|eV|weeks|week|days|day|months|month|hours|h)(?=\b)',r' \1',x)
 return x
D=read(P/'source-facts.json');T=read(P/'source-tables.json');I=read(P/'source-inventory.json');A=read(P/'original-assets-manifest.json');PC=read(P/'page-coverage.json');FR=read(P/'package-freeze.json');CM=read(C/'record-manifest.json');COV=read(C/'source-to-field-coverage.json');OWN=read(C/'source-owner-map.json')
PASSED=bool(CM['independent_source_audit_sha256']);AP=Path(CM['independent_source_audit_path'])if PASSED else None
R={x['record_id']:read(x['path'])for x in CM['records']};U={u['id']:u for u in I['inventory_units']};FM={x['id']:x for x in D['facts']};TM={t['id']:t for t in T['tables']};UB={u['source_unit_id']:u['canonical_bindings']for u in COV['source_units']}
for x in CM['records']:assert sha(x['path'])==x['sha256']
SECTIONS=[{'id':i,'title':t,'items':[]}for i,t in [('precursors','Precursors'),('protocol','Synthesis protocol'),('structures','Final structures'),('properties','Properties'),('intuition','Chemical intuition'),('sources','Sources and limitations')]]
ITEM={};UNIT={};FIELD={};OPS={};MAT={};STOCK={};PRODUCT={};MEAS={}
def evidence(es):
 out=[]
 for e in es:
  if 'document_role'in e:out.append({k:e[k]for k in['source_id','document_role','pdf_page','printed_page','locator']});continue
  m=re.search(r'(MAIN|SI) PDF p\. (\d+) \(printed ([^)]+)\)',e['locator']);out.append({'source_id':SID,'document_role':m[1].lower()if m else'main','pdf_page':int(m[2])if m else None,'printed_page':m[3]if m else None,'locator':e['locator']})
 return out
def section_for_record(rid):
 k=rid.removeprefix(PRE)
 if k in['source-materials','cs-oleate-preparation']:return'precursors'
 if k in['xrd-procedure','tem-procedure','icp-procedure','structure-results']:return'structures'
 if k in['optical-procedure','ta-procedure','ltpl-procedure','stability-procedure','lsc-procedure','optical-results','stability-results','device-results']:return'properties'
 if k in['dft-procedure','mechanistic-context']:return'intuition'
 if k=='source-context':return'sources'
 return'protocol'
def add(section,i,title,text,es=(),uid=None,scope='source_context'):
 assert i not in ITEM,i
 item={'id':i,'title':prose(title),'text':prose(text),'source_audit_unit_ids':[uid]if uid else[],'source_fact_ids':[],'evidence':evidence(es),'facts':[],'canonical_links':[],'sample_scope':{'label':scope,'canonical_sample_links':[],'same_batch_verified':False},'original_assets':[],'notes':[],'reviewed':False,'training_eligible':False}
 next(s for s in SECTIONS if s['id']==section)['items'].append(item);ITEM[i]=item
 if uid:UNIT.setdefault(uid,[]).append(i)
 return item
OVERVIEWS={
'precursors':('Stock composition and distinct analytical reagents','Cesium carbonate, oleic acid and ODE form a Cs-oleate stock that is stored under vacuum and reheated before use. A separate manganese chloride mixture contains dry ODE, oleic acid and technical oleylamine. Whole-stock charges remain distinct from the injected aliquots. The reported precursor-loading ratios are retained as source labels because final stock concentration and volume are not specified. Acidic ICP matrices and ionic calibration standards serve analytical roles, rather than synthesis inputs.'),
'protocol':('Five preparations and separately tested workups','The source reports five preparations: 150 and 200 °C at Mn/Cs 0.7, and 180 °C at 0.7, 0.5 and 0.35. These are not a crossed nine-condition grid or independently counted batches. Growth lasts 5 s before ice-water quenching. Primary isolation uses centrifugation without antisolvent, followed by vacuum drying and hexane redispersion. Hexane-only, isopropanol, ethyl acetate and methyl acetate trials retain their own outcomes; they are not combined into one purification recipe.'),
'structures':('Reported phases and unresolved refinement details','The 150 °C product is assigned cubic CsMnCl3, while the 180 and 200 °C products are assigned rhombohedral CsMnCl3. Diffraction, SAED, microscopy and ICP provide distinct sample-specific observations. The original refinement tables retain zero occupancies, inconsistent Wyckoff labels, absent cell angles and missing 200 °C atomic coordinates without repair. Their availability does not by itself qualify a CIF, a measured nanocrystal geometry or an exact recipe–structure label.'),
'properties':('Luminescence, aging and an unencapsulated device','The optimized 180 °C, Mn/Cs 0.5 sample reaches a reported 40% quantum yield, while the cubic sample is nonemissive. Steady spectra, decay fits, transient absorption and low-temperature film measurements retain separate specimen and acquisition contexts. Film phase stability differs from dispersion luminescence stability. The proof-of-concept device uses an unencapsulated NC film on glass, with dark, bare-glass and same-film aging comparisons; no polymer-encapsulation recipe or precise device efficiency is supplied.'),
'intuition':('Structural and photophysical interpretations','The authors connect phase, octahedral distortion and magnetic/electronic models to the different luminescence behavior. They discuss surface stabilization, d–d transitions, self-trapped excitons and possible defects, while leaving the exact microscopic mechanism unresolved. DFT bands, spectroscopic fits and cited bulk results remain distinct from directly measured nanocrystal properties. Source-equation inconsistencies and uncertain sample links are preserved.'),
'sources':('Complete supplied main and SI, with explicit limitations','All 13 main pages and all 13 locally matched SI pages were read and visually inspected. The seven tables, original graphics, equations and 55 references are mapped to the source reader. References identify cited work; their full texts were not newly read. Complete PDFs, full text and whole-page scans remain local. The reader retains all declared conflicts and missing conditions, while independent visual, model, integration and publication gates remain separate.')}
for sec,(title,text)in OVERVIEWS.items():add(sec,'overview-'+sec,title,text,scope='academic overview')
FIG_PROSE={
'graphical-abstract':'The graphical abstract contrasts the source-assigned crystal phases and illustrates the photocurrent concept. It summarizes the study without specifying a new recipe, a measured device geometry or atomic coordinates.',
'figure-1':'The synthesis cartoon shows Cs-oleate injection into the manganese precursor, an idealized reaction equation and an emissive vial. It conveys the hot-injection sequence but does not establish the exact apparatus dimensions, complete dissolved speciation or nanocrystal surface coverage.',
'figure-2':'The five named preparation conditions have separate diffraction profiles and reported refinements. The visible reference labels identify rhombohedral panel a and cubic panel h, while the caption reverses them and contains a code typo and an iodide wording error. These discrepancies remain explicit. The structural illustrations and tabulated fits are source reports, not independently qualified coordinate models.',
'figure-3':'The optimized 180 °C, Mn/Cs 0.5 specimen is shown by TEM and SAED. Panel d reports a 13.4 ± 0.9 nm size, with pentagon-diameter wording. This exact figure value is retained alongside the different prose and other-sample histogram summaries; the image does not prove a same-particle join to every optical measurement.',
'figure-4':'Absorption distinguishes the cubic and rhombohedral samples, and the optimized dispersion is shown under room illumination and 365 nm UV light. PLE, quantum yield and decay comparisons retain their stated source loading labels. The caption’s Cs/Mn wording differs from the Mn/Cs preparation labels; these ratios are not silently inverted. The photographic excitation differs from the maximum-QY condition.',
'figure-5':'The authors compare calculated antiferromagnetic cubic and rhombohedral bands, projected densities of states and selected Γ-state wavefunctions. These HSE06 model results do not supply a measured nanocrystal atomic configuration or an experimentally established microscopic emission mechanism.',
'figure-6':'Transient absorption compares nc150, nc180-07 and nc180-05 with 300 nm excitation at 80 µW. The cubic decay is probed at 445 nm and the rhombohedral decays at 550 nm. Biexponential and triexponential fit components remain associated with the corresponding specimens; their mechanistic assignments are interpretations.',
'figure-7':'The optimized sample is deposited on silica and excited at 380 nm for low-temperature PL. The caption specifies initial cooling to 30 K followed by warming in 20 K increments. The activated-quenching fit and its 100 ± 18 meV binding-energy parameter remain a model of integrated intensity, separate from the solution-spectrum peak and direct atomic structure.',
'figure-8':'Panel a follows stored rhombohedral-film diffraction; panel b follows normalized integrated luminescence of a dispersion. These are separate specimens and observables. The prose’s PLQY or efficiency wording and endpoint percentages do not directly match the plot’s normalized integrated-PL labeling, so both are retained without substitution.',
'figure-9':'The unencapsulated NC-film glass is compared with bare glass and a dark photodiode, then the same film is measured after 11 weeks. The original schematic and current–voltage curves are retained. A future embedded or protected material is not an experimentally demonstrated matrix recipe.',
'figure-s1':'The photographs show precursor preparation, quenched crude material, isolated precipitate and an unisolated dispersion left in ODE for 1 h in air. The black degradation control is distinct from long-term stability measurements on purified specimens.',
'figure-s2':'The source assigns panels a, b, c and d to nc150, nc200, nc180-07 and nc180-035, respectively. TEM, higher-magnification views and SAED remain intact. The c2/c3 labeling and caption continuation contain inconsistencies, which are not repaired by reassigning the images.',
'figure-s2-caption-continuation':'This selected original caption continuation gives the high-magnification and SAED conventions for Figure S2. Its wording remains linked to the original panels and to the recorded panel-label conflict.',
'figure-s3':'The four histograms report nc150 at 3.9 ± 0.9 nm, nc180-07 at 11.0 ± 1.0 nm, nc200 at 10.8 ± 0.8 nm and nc180-035 at 13.4 ± 0.8 nm. The cubic histogram calls its dimension a diameter whereas the prose calls it a length. The optimized 0.5 sample is shown separately in Figure 3.',
'figure-s4':'Absorption, Tauc plots, PL and decay are compared for the printed sample labels. Several panels use 1:3 and 1:4 labels that differ from the 0.5 and 0.35 labels elsewhere. In the Tauc plot, the left squared ordinate has a squared unit and the right squared ordinate has a one-half unit exponent; the printed discrepancy is preserved without correcting a fit.',
'figure-s5':'Excitation-dependent PL and decay refer to the optimized 0.5 specimen, with emission monitored at 670 nm. The plotted 335 nm label differs from the 330 nm entry in Table S6; neither is silently replaced.',
'figure-s6':'The nc180-07 control compares 300, 370 and 420 nm excitation and monitors the decay at 600 nm. These pump and probe conditions differ from Figure 6. The authors’ above-gap wording is retained as an interpretation with its stated optical-gap tension.',
'figure-s7':'The low-temperature emission width is plotted in meV under 380 nm excitation. The lowest plotted temperature is near 70 K, whereas the prose states a 52 meV endpoint at 50 K. No unprinted point is added and no conversion to a wavelength width is assumed.',
'figure-s8':'The fresh cubic specimen is labeled 100% CsMnCl3. After aging, the source refinement assigns 88.1% CsCl, 4.5% Cs3MnCl5 and 7.4% CsMn4Cl9. These are reported phase fractions without supplied uncertainties or an independently validated atomic model.',
'figure-s9':'Aged rhombohedral specimens show partial aggregation. The exact age and preparation-loading label are absent from the caption; they are not inferred from neighboring stability experiments. Ligand stripping remains an author explanation, not a measured coverage result.'}
for uid,u in U.items():
 kind=u['kind'];obj=resolve(D if u['path']=='source-facts.json'else T,u['json_pointer']);oid=u['source_object_id'];bs=UB[uid];sec=section_for_record(bs[0]['record_id']);title=obj.get('title',obj.get('name',oid.replace('-',' ').capitalize()));scope=obj.get('sample_scope',oid);text=title
 if kind=='facts':
  text=obj['claim']
  if obj['claim_class']in['cited_context','author_interpretation','reported_model']and OWN['fact_owner'][oid]=='mechanistic-context':sec='intuition'
  if oid in[SID+'-phase-stability',SID+'-aged-phase-fractions',SID+'-aged-tem']:sec='structures'
 elif kind=='materials':sec='precursors';text=obj['name']+'. '+obj['scope_note']
 elif kind=='stocks':sec='precursors';text=obj['name']+'. '+obj['notes']+' Whole-stock preparation and later aliquot use remain distinct.'
 elif kind=='sample_contexts':
  text=obj['name']+'. '+('This source-defined preparation condition retains its exact temperature, loading label and injected aliquot. It is not an independent batch count.'if obj['kind']=='source_preparation_condition'else'This '+obj['kind'].replace('_',' ')+' context retains its explicit source associations. It does not create an unreported same-aliquot cross-technique link.')
  scope=obj['id']
 elif kind=='figures':
  text=FIG_PROSE[oid];scope='/'.join(obj['sample_ids'])or'conceptual source graphic'
  if oid in['figure-s8','figure-s9']:sec='structures'
 elif kind=='equations':text=obj['expression']+'. '+obj['scope_note'];scope=obj['sample_scope']
 elif kind=='references':sec='sources';title='Reference '+str(obj['number']);text=obj['text']+' This bibliographic pointer does not imply that the cited full text was read.'
 elif kind in['conflicts','missingness']:sec='sources';text=obj['description'];scope='source limitation'
 elif kind=='protocols':text=obj['title']+' retains '+str(len(obj['operations']))+' source-defined actions. '+obj['specimen_application']
 elif kind=='operation':title=obj['action'];text=obj['action']+'. '+obj.get('condition_scope_note','')+' '+obj['quantity_scope_note'];scope='source operation'
 elif kind=='table':text=obj['title']+' contains '+str(len(obj['rows']))+' source rows. The complete column order, units, blank cells, literal entries, notes and footnotes are retained. Refinement tables and fitted parameters do not independently establish an approved model or exact training label.'
 elif kind=='table_row':title=oid.rsplit('-row-',1)[0].replace('table-','Table ').upper().replace('TABLE','Table')+' · '+obj['row_label'];scope=obj['sample_id'];text='The source row '+obj['row_label']+' retains each printed entry under its original column and unit. Its sample assignment is limited to this table context; blanks and inconsistent labels are not repaired.'
 else:raise AssertionError(kind)
 item=add(sec,'source-'+norm(uid),title,text,obj.get('evidence',[]),uid,scope)
 item['canonical_links']=[{'record_id':b['record_id'],'json_pointer':b['pointer'],'relation':'Exact canonical source-unit field; no additional physical sample join.'}for b in bs]
 if kind=='facts':item['claim_type']=obj['claim_class'];item['notes']+=[prose(next(c['description']for c in D['conflicts']if c['id']==cid))for cid in obj['conflict_ids']]
for rid,r in R.items():
 item=add(section_for_record(rid),'record-'+rid,r['title'].split(' · ',1)[1],r['method']+'. This record retains a source-defined preparation, measurement, interpretation or source context. It does not add an independent physical batch.');item['canonical_links']=[{'record_id':rid,'json_pointer':'','relation':'Private canonical proposal pending distinct approval.'}];item['notes']+=list(dict.fromkeys(prose(x)for x in r['quality']['conflicts']))
def displayed(q):
 if q['value']is not None:return q['value']
 lo,hi=q.get('minimum'),q.get('maximum')
 if lo is not None and hi is not None:return str(lo)+'–'+str(hi)
 if lo is not None:return('> 'if q.get('minimum_exclusive')else'≥ ')+str(lo)
 if hi is not None:return('< 'if q.get('maximum_exclusive')else'≤ ')+str(hi)
 return'Not reported'
def attach(item,rid,ptr,label,q,sid=None):
 assert(rid,ptr)not in FIELD,(rid,ptr)
 out={'id':rid+'::'+ptr,'label':prose(label),'value':displayed(q),'unit':q.get('unit'),'status':q['status'],'approximate':q.get('approximate',False),'basis':'exact_canonical_field','qualifier':prose(' '.join(q.get(k,'')for k in['basis','qualifier','note'])),'evidence':evidence(q['evidence']),'canonical_record_id':rid,'json_pointer':ptr,'canonical_quantity':deepcopy(q),'presentation_kind':'exact_quantity','training_eligible':False}
 if sid:out['sample_id']=sid
 item['facts'].append(out);FIELD[(rid,ptr)]=(item['id'],out);return out
PTRUNIT={}
for uid,bs in UB.items():
 for b in bs:PTRUNIT.setdefault((b['record_id'],b['pointer']),uid)
TD={(x['record_id'],x['pointer']):x['table_id']for x in COV['table_definitions']}
OP_EXTRA={
'nc-inject':'Use only the five paired preparation conditions in the condition options. The listed temperatures and aliquots must not be independently crossed or added together.',
'ipa-or-etoac':'Split the crude suspension into separate trials. Isopropanol and ethyl acetate are alternatives, not a combined antisolvent mixture.',
'ta-acquire':'Figure 6 uses 300 nm excitation at 80 µW, with 445 nm probing for the cubic specimen and 550 nm for the rhombohedral specimens. The separate Figure S6 control uses 300, 370 and 420 nm pumps and a 600 nm decay probe for nc180-07. These settings do not describe one combined acquisition.',
'dft-calculate':'The authors use separately reported cubic and rhombohedral primitive-cell models. The canonical input node denotes structural comparison context, not proof that the SI coordinates were the exact DFT input; no geometry model is approved.',
'age-specimens':'Films and diluted dispersions are stored and measured as separate specimens. Their diffraction and luminescence changes are not interchangeable observables.'}
for rid,r in R.items():
 for j,op in enumerate(r['operations']):
  ptr=f'/operations/{j}';uid='operation:'+op['id'];item=ITEM[UNIT[uid][0]];sourceop=next(o for pr in D['protocols']for o in pr['operations']if o['id']==op['id']);names={m['id']:m['name']for m in r['materials']}|{s['id']:s['name']for s in r['stocks']}|{s['id']:s['name']for s in r['material_states']}
  item['text']=prose(op['label']+'. '+OP_EXTRA.get(op['id'],'')+' '+sourceop.get('condition_scope_note','')+' The quantitative fields below retain the source-scoped settings for this action. Missing settings are left unspecified.')
  item['operation_context']={'record_id':rid,'operation_id':op['id'],'json_pointer':ptr,**{k:deepcopy(op[k])for k in['stage','branch','depends_on','environment','inputs','outputs','retained_fraction','endpoint']},'material_flow_labels':{k:names[k]for k in op['inputs']+op['outputs']},'diagram_binding_status':'pending_independent_visual_binding'}
  item['notes']+=['Inputs: '+', '.join(names[k]for k in op['inputs'])+'.','Outputs: '+', '.join(names[k]for k in op['outputs'])+'.'];OPS[rid+'::'+op['id']]=item['id']
  if op['retained_fraction']:item['notes'].append('Retained fraction: '+names[op['retained_fraction']]+'.')
  for k,q in op['parameters'].items():attach(item,rid,ptr+'/parameters/'+esc(k),k.replace('_',' ').capitalize(),q)
  for k in['environment','endpoint']:attach(item,rid,ptr+'/'+k,k.capitalize(),op[k])
 for j,m in enumerate(r['materials']):
  item=ITEM[UNIT['materials:'+m['id']][0]];ptr=f'/materials/{j}';item.setdefault('material_identities',[]).append({'source_material_id':m['id'],'name':m['name'],'formula':m['formula'],'role':m['role'],'stage':m['stage'],'canonical_record_id':rid,'json_pointer':ptr,'exact_molecular_asset_binding_approved':False});MAT[rid+'::'+m['id']]=item['id']
  for k,q in m['quantities'].items():attach(item,rid,ptr+'/quantities/'+esc(k),m['name']+' · '+k,q)
 for j,st in enumerate(r['stocks']):
  item=ITEM[UNIT['stocks:'+st['id']][0]];ptr=f'/stocks/{j}';item.setdefault('stock_contexts',[]).append({'record_id':rid,'json_pointer':ptr,**deepcopy(st),'molecular_bindings_approved':False});STOCK[rid+'::'+st['id']]=item['id']
  for k,q in st['concentrations'].items():attach(item,rid,ptr+'/concentrations/'+esc(k),k.replace('_',' ').capitalize(),q)
  for n,c in enumerate(st['components']):
   for k,q in c['quantities'].items():attach(item,rid,ptr+f'/components/{n}/quantities/'+esc(k),c['material_id']+' · '+k,q)
 for j,opt in enumerate(r['condition_options']):
  ptr=f'/condition_options/{j}';item=ITEM[UNIT[PTRUNIT[(rid,ptr)]][0]]
  for k,q in opt['parameters'].items():attach(item,rid,ptr+'/parameters/'+esc(k),opt['label']+' · '+k.replace('_',' '),q)
 for j,m in enumerate(r['measurements']):
  ptr=f'/measurements/{j}/value';item=ITEM[UNIT[PTRUNIT[(rid,ptr)]][0]];out=attach(item,rid,ptr,m['property'].replace('_',' ').capitalize(),m['value'],m['sample_id']);MEAS[rid+'::'+m['id']]=item['id']
  if(rid,ptr)in TD:out['value']=json.loads(m['value']['value']);out['label']='Table headings, column order, footnotes and source scope';out['presentation_kind']='curated_source_inventory';out['basis']='exact_canonical_payload_with_academic_display'
 for j,p in enumerate(r['products']):
  ptr=f'/products/{j}';item=ITEM['record-'+rid];item.setdefault('product_contexts',[]).append({'record_id':rid,'json_pointer':ptr,**deepcopy(p),'atomic_asset_binding_approved':False});item['canonical_links'].append({'record_id':rid,'json_pointer':ptr,'relation':'Source-defined specimen or interpretation context; no new exact pair.'});PRODUCT[rid+'::'+p['sample_id']]=item['id']
  for k in['composition','phase','morphology','surface']:attach(item,rid,ptr+'/'+k,p['source_sample_label']+' · '+k,p[k],p['sample_id'])
 for k,q in r['intended_target'].items():attach(ITEM['record-'+rid],rid,'/intended_target/'+k,'Intended target · '+k,q)
FACTMAP={};TABLEMAP={}
for row in COV['facts']:
 bs=[]
 for b in row['canonical_bindings']:
  iid,q=FIELD[(b['record_id'],b['pointer'])];q.setdefault('source_fact_ids',[]).append(row['source_fact_id']);ITEM[iid]['source_fact_ids'].append(row['source_fact_id']);bs.append({**b,'reader_item_id':iid,'reader_fact_id':q['id']})
 FACTMAP[row['source_fact_id']]=bs
for row in COV['table_cells']:
 b=row['canonical_bindings'][0];iid,q=FIELD[(b['record_id'],b['pointer'])];q['source_table_cell_id']=row['source_cell_id'];TABLEMAP[row['source_cell_id']]={**b,'reader_item_id':iid,'reader_fact_id':q['id']}
ASSET_UNITS={a['id']:['figures:'+a['id']]for a in A['assets']if a['id']in {f['id']for f in D['figures']}}
for a in A['assets']:
 if a['id'].startswith('table-'):ASSET_UNITS[a['id']]=['table:'+('table-s2'if a['id'].startswith('table-s2-')else a['id'])]
for eq in D['equations']:
 for aid in eq['asset_ids']:ASSET_UNITS.setdefault(aid,[]).append('equations:'+eq['id'])
GROUP={k:[]for k in['figures','tables','schemes','equations','source_notes']};PUBLIC=[]
for a in A['assets']:
 assert sha(a['path'])==a['sha256']and not a['contains_complete_source_page'];ids=ASSET_UNITS[a['id']];uid=ids[0];item=ITEM[UNIT[uid][0]];kind=uid.split(':')[0];group={'figures':'figures','table':'tables','equations':'equations'}[kind];public='assets/figures/'+SID+'/'+Path(a['path']).name;rids=sorted({b['record_id']for u in ids for b in UB[u]})
 entry={'id':SID+'-'+a['id'],'label':item['title']+(' · continuation crop'if a['id']=='table-s2-b'else''),'caption_paraphrase':item['text'],'document_role':a['source_role'],'page':a['pdf_page'],'printed_page':a['printed_page'],'sample_scope':deepcopy(item['sample_scope']),'sample_links':rids,'sample_linkage':'Source-defined context only; no exact same-aliquot or atomic-coordinate join.','public_asset':public,'public_asset_sha256':a['sha256'],'asset_provenance':{'source_sha256':a['source_sha256'],'source_pdf_page':a['pdf_page'],'crop_normalized':a['normalized_bbox'],'source_render_scale':a['render_scale'],'pixel_dimensions':a['size_px'],'transformation':'Selected original crop; no reconstruction, relabeling or complete-page attachment.'},'source_locators':[e['locator']for e in item['evidence']],'notes':item['notes'].copy(),'reader_render_verified':False,'reviewed':False,'training_eligible':False}
 if kind=='table':tid=uid.split(':',1)[1];entry.update(source_rows=deepcopy(TM[tid]['rows']),source_notes=deepcopy(TM[tid]['notes']))
 GROUP[group].append(entry);PUBLIC.append({'id':entry['id'],'private_path':a['path'],'public_asset':public,'sha256':a['sha256'],'selected_original_only':True,'publication_approved':False})
 for u in ids:ITEM[UNIT[u][0]]['original_assets'].append({'id':entry['id'],'label':'Open original '+entry['label'],'public_asset':public,'public_asset_sha256':a['sha256']})
for item in ITEM.values():
 item['canonical_links']=uniq(item['canonical_links']);item['notes']=uniq(item['notes']);item['source_fact_ids']=uniq(item['source_fact_ids'])
 for q in item['facts']:
  if q.get('sample_id'):
   rid=q['canonical_record_id'];n=next(i for i,p in enumerate(R[rid]['products'])if p['sample_id']==q['sample_id']);item['sample_scope']['canonical_sample_links'].append({'record_id':rid,'sample_id':q['sample_id'],'json_pointer':f'/products/{n}','relation':'Exact existing canonical context; no additional physical sample join.'})
 for b in item['canonical_links']:
  if b['json_pointer'].startswith('/measurements/'):
   m=resolve(R[b['record_id']],'/'.join(b['json_pointer'].split('/')[:3]));n=next(i for i,p in enumerate(R[b['record_id']]['products'])if p['sample_id']==m['sample_id']);item['sample_scope']['canonical_sample_links'].append({'record_id':b['record_id'],'sample_id':m['sample_id'],'json_pointer':f'/products/{n}','relation':'Source-scoped measurement context.'})
  elif re.fullmatch(r'/products/\d+',b['json_pointer']):
   p=resolve(R[b['record_id']],b['json_pointer']);item['sample_scope']['canonical_sample_links'].append({'record_id':b['record_id'],'sample_id':p['sample_id'],'json_pointer':b['json_pointer'],'recipe_link':p['recipe_link'],'relation':'Exact canonical product/context pointer.'})
 item['sample_scope']['canonical_sample_links']=list({(b['record_id'],b['json_pointer']):b for b in item['sample_scope']['canonical_sample_links']}.values())
for fig in D['figures']:
 item=ITEM[UNIT['figures:'+fig['id']][0]]
 for label in fig['sample_ids']:
  rid=PRE+OWN['sample_owner'][label];n=next(j for j,p in enumerate(R[rid]['products'])if p['source_sample_label']==label)
  item['sample_scope']['canonical_sample_links'].append({'record_id':rid,'sample_id':R[rid]['products'][n]['sample_id'],'json_pointer':f'/products/{n}','relation':'Explicit source figure context; does not establish a universal same-aliquot or measured-coordinate link.'})
 item['sample_scope']['canonical_sample_links']=list({(b['record_id'],b['json_pointer']):b for b in item['sample_scope']['canonical_sample_links']}.values())
for entries in GROUP.values():
 for e in entries:e['sample_scope']=deepcopy(ITEM[UNIT[ASSET_UNITS[e['id'].removeprefix(SID+'-')][0]][0]]['sample_scope'])
docs=[]
for role in['main','si']:
 pages=[p for p in PC['pages']if p['document_role']==role];docs.append({'role':role,'filename':'10.1021_acsanm.2c04342'+('_si_1'if role=='si'else'')+'.pdf','sha256':pages[0]['source_sha256'],'page_count':13,'pages':[{'page':p['pdf_page'],'printed_page':952+p['pdf_page']if role=='main'else'S'+str(p['pdf_page']),'text_read':p['text_read'],'visual_review':p['native_page_visually_inspected'],'sections':[p['scope_note']]}for p in pages]})
routes={PRE+'hot-injection-series':[rid for rid in R if rid!=PRE+'hot-injection-series']}
counts={'reader_items':len(ITEM),'source_units':len(UNIT),'source_facts':len(FACTMAP),'source_fact_bindings':sum(map(len,FACTMAP.values())),'source_table_cells':len(TABLEMAP),'typed_reader_fields':len(FIELD),'canonical_records':len(R),'operations':len(OPS),'material_slots':len(MAT),'stock_slots':len(STOCK),'sample_context_slots':len(PRODUCT),'measurements':len(MEAS),'selected_original_assets':len(PUBLIC),'full_page_public_assets':0,'main_pages':13,'si_pages_read':13,'eligible_training_rows':0,'atomic_structure_assets':0}
source_status='The distinct supplied main/SI source audit passed; canonical and reader independent approval remain pending.'if PASSED else'The source audit is pending; canonical and reader independent approval also remain pending.'
review={'schema_version':'1.0','paper_id':SID,'doi':D['doi'],'title':D['title'],'paper':{'authors':OWN['authors'],'year':2023,'journal':'ACS Applied Nano Materials','volume':6,'pages':'953–965'},'source_group':SID,'review_scope':'complete_supplied_main_and_matched_si','documents':docs,'supporting_information':{'status':'locally_matched_complete_supplied_pages_read','matched_local_si_count':1,'pdf_pages':13,'scope':'Content-verified main/SI title, byline, declaration and experimental continuity; SI title adds initial “The”. No separate CIF or raw-data files were supplied.'},'document_identity_verification':{'method':'Four incoming/legacy copies rehashed; two unique PDFs with matched title/byline and content continuity.'},'coverage_status':'private_author_reader_proposal','independent_audit':source_status+' Historical source-payload pending flags record the author-freeze stage.','publication_status':'Private unapproved proposal only.','source_review_promoted':False,'training_eligible':False,'recipe_inventory':[{'id':rid,'label':r['title'],'record_ids':[rid],'record_type':r['record_type'],'status':'author_draft_pending_independent_review','scope':'One route with five reported preparation conditions, distinct stock/workup/analytical procedures and observations; no independent batch count.','gaps':r['quality']['missing_fields']}for rid,r in R.items()],'characterization_inventory':{'reader_item_ids':[i['id']for s in SECTIONS if s['id']in['structures','properties']for i in s['items']]},'chemical_intuition':{'reader_item_ids':[i['id']for s in SECTIONS if s['id']=='intuition'for i in s['items']]},'reader_contract':{'version':'1.0','section_ids':[s['id']for s in SECTIONS]},'reader_sections':SECTIONS,**GROUP,'remaining_gaps':[prose(g['description'])for g in D['missingness']]+[source_status,'Molecular, apparatus, product-context, model, browser and publication gates remain separate.'],'evidence_conflicts':deepcopy(D['conflicts']),'route_evidence_contexts':routes,'route_evidence_scope_notes':{'all':'Linked records provide study context, not automatic exact-product measurements for every preparation.','preparation':'Five explicitly paired conditions; source loading labels, whole-stock charges and reaction aliquots remain distinct.','specimens':'Films, dispersions, destructive ICP digests, aging controls, model inputs and device controls retain separate scopes.','structure':'Literal refined values and source crystal illustrations are not qualified atomic models. No zero occupancy, Wyckoff mismatch or absent angle/coordinate is repaired.','photophysics':'Printed fit equations, source lifetimes, wavelength differences and observables remain explicit; no uncertainty or missing point is invented.'},'material_evidence_records':{'CsMnCl3':[rid for rid,r in R.items()if r['material']['formula']=='CsMnCl3']},'counts':counts}
save(SID+'.json',review);save('reader-bindings-proposal.json',{'source_id':SID,'status':'private_unapproved','reader_sha256':sha(O/(SID+'.json')),'original_assets':PUBLIC,'operation_to_reader_item':OPS,'material_to_reader_item':MAT,'stock_to_reader_item':STOCK,'product_to_reader_item':PRODUCT,'molecular_apparatus_bindings_approved':False,'publication_approved':False});save('source-item-coverage.json',{'source_units':UNIT,'source_facts':FACTMAP,'table_cells':TABLEMAP,'canonical_field_map':[{'record_id':rid,'json_pointer':ptr,'reader_item_id':v[0],'reader_fact_id':v[1]['id']}for(rid,ptr),v in FIELD.items()],'measurement_to_reader_item':MEAS,'private_canonical_manifest_sha256':sha(C/'record-manifest.json')})
checks=[]
def ck(n,ok):checks.append({'check':n,'passed':bool(ok)})
for(rid,ptr),(iid,q)in FIELD.items():ck(iid+' '+ptr+' exact canonical equality',resolve(R[rid],ptr)==q['canonical_quantity'])
for item in ITEM.values():
 for b in item['canonical_links']:ck(item['id']+' canonical pointer',resolve(R[b['record_id']],b['json_pointer'])is not None)
 for b in item['sample_scope']['canonical_sample_links']:ck(item['id']+' sample pointer',resolve(R[b['record_id']],b['json_pointer'])['sample_id']==b['sample_id'])
for a in PUBLIC:ck(a['id']+' crop hash',sha(a['private_path'])==a['sha256'])
ck('All source units, facts and321 table cells',set(UNIT)==set(U)and set(FACTMAP)==set(FM)and len(TABLEMAP)==321)
ck('All canonical slots represented',len(OPS)==CM['counts']['operations']and len(MAT)==CM['counts']['material_slots']and len(STOCK)==CM['counts']['stock_slots']and len(PRODUCT)==CM['counts']['sample_context_slots']and len(MEAS)==CM['counts']['measurements'])
ck('Six academic/source sections',[s['id']for s in SECTIONS]==['precursors','protocol','structures','properties','intuition','sources'])
ck('30 selected crops; zero whole pages',len(PUBLIC)==30 and all(not a['contains_complete_source_page']for a in A['assets']))
ck('No raw local source paths',not re.search(r'[A-Z]:[\\/]',json.dumps(review)))
ck('Route context is an ID array',len(routes)==1 and all(isinstance(a,list)and all(r in R for r in a)for a in routes.values()))
all_typed=set()
def walk(v,p,rid):
 if isinstance(v,dict):
  if {'value','status','evidence'}<=v.keys():all_typed.add((rid,p));return
  for k,x in v.items():walk(x,p+'/'+esc(k),rid)
 elif isinstance(v,list):
  for j,x in enumerate(v):walk(x,p+'/'+str(j),rid)
for rid,r in R.items():walk(r,'',rid)
ck('Every typed canonical field represented',all_typed==set(FIELD));ck('All source and canonical inputs unchanged',all(sha(p)==h for p,h in FR['bound_files'].items())and all(sha(x['path'])==x['sha256']for x in CM['records']))
assert all(c['passed']for c in checks),[c for c in checks if not c['passed']]
save('author-validation.json',{'status':'author_pointer_transport_contract_checks_passed','author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'check_count':len(checks),'checks':checks,'counts':counts,'independent_source_audit':'passed'if PASSED else'pending','independent_canonical_reader_audit':'pending','browser_visual_gate':'not_performed','site_written':False,'published':False})
paths=[P/'package-freeze.json',P/'source-facts.json',P/'source-inventory.json',P/'source-tables.json',P/'page-coverage.json',P/'original-assets-manifest.json',C/'record-manifest.json',C/'source-to-field-coverage.json',S/'scripts/build_paper_reviews.py',S/'dist/source-evidence.mjs']+([AP]if PASSED else[])
save('reader-manifest.json',{'schema':'mattersyn-private-reader-proposal/1','source_id':SID,'version':1,'author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'status':'private_author_draft_pending_distinct_review','input_hashes':{str(p):sha(p)for p in paths},'outputs':{n:sha(O/n)for n in[SID+'.json','reader-bindings-proposal.json','source-item-coverage.json','author-validation.json']},'author_script_sha256':sha(__file__),'counts':counts,'published':False})
print(json.dumps(counts));print('READER',sha(O/(SID+'.json')))
