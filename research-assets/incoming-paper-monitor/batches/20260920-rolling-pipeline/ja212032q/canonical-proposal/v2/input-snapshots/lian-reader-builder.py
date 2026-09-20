"""Private Lian academic reader. Source/canonical inputs are read-only."""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import json,hashlib,re,sys
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;C=P/'canonical-proposal'/'v1';O=P/'public-review-proposal'/'v1';O.mkdir(parents=True,exist_ok=True)
assert not(C/'package-manifest.json').exists(),'Revise a frozen proposal separately.'
S=Path('[local path redacted]');SID='lian2021';PRE='lian-2021-'
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
 x=str(x)
 for a,b in [('crystalZIP','crystal ZIP'),('FigureS','Figure S'),('TableS','Table S'),('NCPLQE','NC PLQE'),('DFTPBE','DFT PBE'),('SI1','SI 1'),('atT','at T'),('at0K','at 0 K'),('I0 emission','I₀ emission'),('All26','All 26'),('All8','All 8'),('all57','all 57'),('all891','all 891')]:x=x.replace(a,b)
 x=re.sub(r'\b(Figure|Table|Scheme|Equation|Figures|Tables|at|exc|excitation|emission|FWHM|Stokes|PLQE|PBE|HSE06|over|after|within|for|of|and|all|All|above|below|near|around|approximately|about|step|Fig\.)(?=\d)',r'\1 ',x)
 x=re.sub(r'(?<=\d)(?=(?:nm|mm|µm|mL|µL|mM|mg|mmol|mol|ns|µs|min|days|months|keV|MeV|meV|eV|kV|rpm|h|K)(?:\b|\d))',' ',x)
 x=re.sub(r'(?<=\d)(?=°C|Å)',' ',x);x=re.sub(r';(?=\S)','; ',x);x=re.sub(r'\s*±\s*',' ± ',x)
 x=x.replace('grade,90%','grade, 90%').replace('2000 uL','2000 µL').replace('Nc feed','Nanocrystal feed').replace('Ps toluene','PS/toluene').replace('Si angle','SI angle').replace('Si length','SI length')
 return x
D=read(P/'source-facts.json');I=read(P/'source-inventory.json');A=read(P/'original-assets-manifest.json');PC=read(P/'page-coverage.json');FR=read(P/'package-freeze.json');CM=read(C/'record-manifest.json');COV=read(C/'source-to-field-coverage.json')
AP=P/'source-independent-audit'/'independent-audit-v2.json';AU=read(AP)
assert AU['status']=='passed'and AU['proposal_freeze_sha256']==sha(P/'package-freeze.json')and not AU['open_findings']
R={x['record_id']:read(x['path'])for x in CM['records']};U={u['id']:u for u in I['inventory_units']};FM={x['id']:x for x in D['facts']};TM={x['id']:x for x in D['tables']};PM={x['id']:x for x in D['protocols']}
for x in CM['records']:assert sha(x['path'])==x['sha256']
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
 if k=='reagents-methods':return'precursors'
 if k=='bulk-characterization':return'structures'
 if k in ['dft-calculation','mechanistic-context']:return'intuition'
 if k=='source-context':return'sources'
 if k.endswith('properties')or k in ['nc-characterization','film-beta-characterization']:return'properties'
 return'protocol'
def add(section,i,title,text,es=None,unit=None,scope='source_context'):
 assert i not in ITEM,i
 item={'id':i,'title':prose(title),'text':prose(text),'claim_type':'source_reported_context','sample_scope':{'formulations':[],'physical_batch_id':None,'scope_kind':scope,'state':prose(title),'link_limit':'Composition and explicit source contexts are retained. They do not identify one physical batch across microscopy, diffraction, luminescence or film measurements.','canonical_sample_links':[]},'evidence':uniq(evidence(es or[])),'source_locators':[e['locator']for e in es or[]],'canonical_links':[],'notes':[],'facts':[],'source_audit_unit_ids':[unit]if unit else[],'source_fact_ids':[],'original_assets':[],'training_eligible':False}
 ITEM[i]=item;next(s for s in SECTIONS if s['id']==section)['items'].append(item)
 if unit:UNIT.setdefault(unit,[]).append(i)
 return item
UB={x['source_unit_id']:x['canonical_bindings']for x in COV['source_units']}
TABLE_PROSE={
'table-s1':'The crystallographic and refinement summary separately describes bulk A and bulk B. Both empirical formulae, cell parameters, temperatures, symmetry assignments and refinement statistics are retained. Neither this table nor the nanocrystal diffraction comparison establishes a complete nanocrystal atomic model.',
'table-s2':'All 29 A bond-distance rows retain their atom labels and standard uncertainties. These are bulk single-crystal measurements.',
'table-s3':'All 32 B bond-distance rows retain the two independent Sb centres. The main-text average distance does not identify which centre or averaging procedure it uses.',
'table-s4':'All 38 A bond-angle rows retain labels and uncertainties. Selected central angles in the distortion calculation remain distinct from the full geometry table.',
'table-s5':'All 40 B bond-angle rows retain labels and uncertainties. The two independent Sb environments are not collapsed into one coordination polyhedron.',
'table-s6':'All 32 non-hydrogen A coordinate rows retain the printed tokens. The coordinate numbers are converted to fractional values with a factor of 10⁻⁴, and Ueq numbers are converted with a factor of 10⁻³ Å². Uncertainties are scaled with their values; negative or greater-than-one coordinates remain unwrapped.',
'table-s7':'All 36 non-hydrogen B coordinate rows retain their atom identities, fractional-coordinate scaling and equivalent displacement parameters. The two Sb centres remain separate.',
'table-s8':'All 32 A anisotropic-displacement rows retain the literal column order U11, U22, U33, U23, U13, U12. Printed values and their uncertainties are converted with a factor of 10⁻³ Å². Negative off-diagonal values remain signed.',
'table-s9':'All 36 B anisotropic-displacement rows retain the same six-column convention and printed scale. These source observations do not certify a positive-definite model or supply missing hydrogen positions and occupancies.'}
FIG_PROSE={
'graphical-abstract':'The graphical abstract summarizes the authors’ structural-modulation argument. It is a conceptual overview rather than an additional specimen or measurement.',
'figure-1':'Panels a and b show bulk A; panels c and d show bulk B. A contains isolated pyramidal [SbCl5]²⁻ units, whereas B contains isolated seesaw [SbCl4]⁻ units. These crystal drawings do not give nanocrystal surface coordinates.',
'figure-2':'The figure compares the bulk compounds and resolves the excitation-dependent emission of A. Its yellow and blue decay measurements describe different emission channels; the absence of detected B emission is not a measured zero quantum efficiency. The 35 mm scale in the photographs describes the dishes, not a crystal or nanocrystal diameter.',
'figure-3':'The relaxed electronic-structure calculations compare A and B band structures, projected states and transition probabilities. The PBE and HSE06 gaps are computed outputs, not measured optical gaps or released relaxed atomic-coordinate files.',
'figure-4':'Panel a shows nanocrystal powder diffraction; panel b shows TEM with a 20 nm scale bar. Panel c shows HRTEM with a 5 nm scale bar and the reported 3.4 Å spacing assigned to (224). Panel d shows the optical spectra, while panels e and f show decays at 614 and 465 nm, respectively. The dried-powder quantum efficiency is kept separate from colloidal settling and from an exact microscopy-to-optics specimen join.',
'figure-5':'Panels a and b show composite-film photographs and emission spectra for the ordered blue-phosphor/yellow-nanocrystal mass parts 1/0, 1/3, 1/2, 2/3 and 0/1. Panels c and d show the β-irradiation demonstration. The source does not identify one of those five ratios as the exact β-tested film formulation.',
'figure-s1':'The supplied powder patterns are compared with patterns simulated from the bulk structures. Agreement supports the reported phase assignment; it does not supply a measured nanocrystal CIF.',
'figure-s2':'The Sb core-level XPS comparison belongs to bulk A and B. Its chemical-shift interpretation is distinct from a quantitative oxidation-state or composition determination.',
'figure-s3':'The bulk thermogravimetric curves were acquired under nitrogen. The stated atmosphere belongs to TGA and is not assigned to the separate XPS acquisition.',
'figure-s4':'The absolute PLQE measurement reports 96.8% for bulk A under 365 nm excitation. The baseline and sample spectra remain original artwork and have not been digitized.',
'figure-s5':'The bulk A chromaticity comparison retains its two excitation conditions. The CIE coordinates are emission results, not synthesis inputs or a standardized stability test.',
'figure-s6':'The normalized bulk A excitation series spans 280–400 nm in 10 nm steps. These spectral curves show the excitation dependence of emission and are not additional quantum-yield measurements.',
'figure-s7':'The PLQE comparison tests the air-storage stability of bulk A over three months. Humidity and a degradation constant are not specified. This observation is distinct from nanocrystal colloidal settling and the qualitative dried-powder stability statement.',
'figure-s8':'The temperature-dependent spectra track bulk A emission over 77–337 K in 20 K steps. The reported temperature intervals remain separate from fitted activation and coupling parameters; no raw curve arrays are supplied.',
'figure-s9':'The supplementary fits at 197, 237 and 277 K provide the reported decomposition of the bulk emission bands. The raw plotted traces have not been digitized.',
'figure-s10':'The intensity-temperature fit supports the reported activation energy of 205.26 meV. Its fit coefficient is retained as a model result rather than a synthesis parameter.',
'figure-s11':'The nanocrystal diameter histogram reports 6.43 ± 0.17 nm. The uncertainty definition and particle count are not stated, and the visibly broad distribution is retained rather than converted into a monodispersity claim.',
'figure-s12':'The absolute PLQE measurement reports 89.3% at 365 nm for dried nanocrystal powder, as specified by the acquisition method. It is not assigned to the settling toluene dispersion.',
'figure-s13':'The photographs distinguish the nanocrystal dispersion and dried powder. Colloidal settling within the reported five-minute context is kept separate from the qualitative several-month dry-powder stability statement; no quantified degradation curve is inferred.',
'figure-s14':'The precursor spin-coated and annealed film has a reported emission maximum of 611 nm and FWHM of 123 nm under 365 nm excitation. It is separate from the nanocrystal/phosphor/PS composite-film series.',
'figure-s15':'The bulk-crystal β-irradiation demonstration is distinct from the composite-film demonstration in Figure 5. No absolute scintillation yield or detector sensitivity is inferred.'}
OBJS={k:{x['id']:x for x in D[k]}for k in ['materials','stocks','samples','figures','schemes','equations','references']}
for uid,u in U.items():
 oid=u['source_object_id'];kind=u['type'];binds=UB[uid];rid=binds[0]['record_id'];section=section_for_record(rid);obj=resolve(D,u['json_pointer']);title=obj.get('title',obj.get('name',oid.replace('-',' ').capitalize()));text=title;scope=kind
 if kind=='fact':
  text=obj['claim'];scope=obj['sample_scope'];title=obj.get('title',obj['id'].removeprefix(SID+'-').replace('-',' ').capitalize())
  if obj['claim_class']in ['author_interpretation','cited_context','author_model']:section='intuition'
  if oid.removeprefix(SID+'-')in ['b-structure','b-distortion','nc-phase-size','acquisition-tem']:section='structures'
  if oid.removeprefix(SID+'-')in ['acquisition-pl','acquisition-plqe','thermal-stability','acquisition-xps-tga']:section='properties'
 elif kind=='table':text=TABLE_PROSE[oid];scope=obj['sample_scope'];section='structures'
 elif kind=='protocol':text='This source-defined procedure preserves each operation, input, output and missing field. Bulk evaporation, nanocrystal reprecipitation and the two film preparations remain distinct.'
 elif kind=='figure':text=FIG_PROSE[oid];scope=obj['sample_scope'];section='intuition'if oid in ['graphical-abstract','figure-3','figure-s10']else'structures'if oid in ['figure-1','figure-s1','figure-s11']else'properties'
 elif kind=='scheme':text='The scheme summarizes the stoichiometric modulation from bulk A to bulk B. It does not establish a nanocrystal surface structure or a separate additional experiment.';scope=obj['sample_scope'];section='intuition'
 elif kind=='equation':text=obj['expression']+'. '+obj['meaning']+' This is an author-defined model or descriptor, not a new measured structure.';scope=obj['scope'];section='intuition'
 elif kind=='reference':text=obj['citation']+' This citation is reproduced as source identity; its full text was not separately read for this contribution.';section='sources';title=('SI reference 'if oid.startswith('si-')else'Reference ')+oid.rsplit('-',1)[-1]
 elif kind=='material':text=obj['name']+'. '+obj['scope_note'];section='precursors'
 elif kind=='stock':text=obj['scope'];section='precursors'
 elif kind=='sample_context':text=obj['name']+'. '+obj['identity_join_limit'];scope=obj['id']
 item=add(section,'source-'+norm(uid),title,text,u['evidence'],uid,scope)
 item['canonical_links']=[{'record_id':b['record_id'],'json_pointer':b['pointer'],'relation':'Exact canonical field for this source object; no new physical sample join.'}for b in binds]
 if kind=='fact':
  item['claim_type']=obj['claim_class']
  item['notes']+=[prose(next(c['description']for c in D['conflicts']if c['id']==cid))for cid in obj['conflict_ids']]
for rid,r in R.items():
 item=add(section_for_record(rid),'record-'+rid,r['title'].split(' · ',1)[1],r['method']+'. This record identifies a source-defined preparation, measurement or model context; it does not count physical batches.')
 item['canonical_links']=[{'record_id':rid,'json_pointer':'','relation':'Private canonical author proposal; distinct canonical/reader approval remains pending.'}];item['notes']+=list(map(prose,r['quality']['missing_fields']+r['quality']['conflicts']))
def displayed(q):
 if q['value']is not None:return q['value']
 lo,hi=q.get('minimum'),q.get('maximum')
 if lo is not None and hi is not None:return str(lo)+'–'+str(hi)
 if lo is not None:return('> 'if q.get('minimum_exclusive')else'≥ ')+str(lo)
 if hi is not None:return('< 'if q.get('maximum_exclusive')else'≤ ')+str(hi)
 return'Not reported'
def attach(item,rid,ptr,label,q,sid=None):
 assert(rid,ptr)not in FIELD,(rid,ptr)
 f={'id':rid+'::'+ptr,'label':prose(label),'value':displayed(q),'unit':q.get('unit'),'status':q['status'],'approximate':q.get('approximate',False),'basis':'exact_canonical_field','qualifier':prose(' '.join(q.get(k,'')for k in ['basis','qualifier','note'])),'evidence':evidence(q['evidence']),'canonical_record_id':rid,'json_pointer':ptr,'canonical_quantity':deepcopy(q),'presentation_kind':'exact_quantity','training_eligible':False}
 if sid:f['sample_id']=sid
 item['facts'].append(f);FIELD[(rid,ptr)]=(item['id'],f);return f
PTRUNIT={}
for uid,bs in UB.items():
 for b in bs:PTRUNIT.setdefault((b['record_id'],b['pointer']),uid)
TD={(x['record_id'],x['pointer']):x['table_id']for x in COV['table_definitions']}
for rid,r in R.items():
 for n,op in enumerate(r['operations']):
  ptr=f'/operations/{n}';uid=PTRUNIT[(rid,ptr)];section=section_for_record(rid)if op['stage']=='characterization'else'protocol'
  if op['id']=='nc-tem':section='structures'
  if op['id']in ['bulk-xps-tga','bulk-optics','bulk-plqe']:section='properties'
  item=add(section,'operation-'+op['id'],op['label'],op['description'],op['evidence'],scope='source_operation')
  names={m['id']:m['name']for m in r['materials']}|{s['id']:s['name']for s in r['stocks']}|{s['id']:s['name']for s in r['material_states']}
  item['source_audit_unit_ids']=[uid];UNIT[uid].append(item['id']);item['operation_context']={'record_id':rid,'operation_id':op['id'],'json_pointer':ptr,**{k:deepcopy(op[k])for k in ['stage','branch','depends_on','environment','inputs','outputs','retained_fraction','endpoint']},'material_flow_labels':{k:names[k]for k in op['inputs']+op['outputs']},'diagram_binding_status':'pending_independent_visual_binding'}
  item['canonical_links'].append({'record_id':rid,'json_pointer':ptr,'relation':'Exact operation and source-scoped material flow.'});item['notes']+=['Inputs: '+', '.join(names[k]for k in op['inputs'])+'.','Outputs: '+', '.join(names[k]for k in op['outputs'])+'.']
  if op['retained_fraction']:item['notes'].append('Retained fraction: '+names[op['retained_fraction']]+'.')
  for k,q in op['parameters'].items():attach(item,rid,ptr+'/parameters/'+esc(k),k.replace('_',' ').capitalize(),q)
  for k in ['environment','endpoint']:attach(item,rid,ptr+'/'+k,k.capitalize(),op[k])
  OPS[rid+'::'+op['id']]=item['id']
 for n,m in enumerate(r['materials']):
  iid='material-'+m['id'];item=ITEM.get(iid)or add('precursors',iid,m['name'],'The source-qualified identity and role are listed below. Condensed formulae and nominal material names do not specify solution speciation, hydration or an atomistic product model.',m['evidence'],scope='material_identity');ptr=f'/materials/{n}'
  item.setdefault('material_identities',[]).append({'source_material_id':m['id'],'name':m['name'],'formula':m['formula'],'role':m['role'],'canonical_record_id':rid,'json_pointer':ptr,'exact_molecular_asset_binding_approved':False});item['notes']+=list(map(prose,m['notes']));item['canonical_links'].append({'record_id':rid,'json_pointer':ptr,'relation':'Exact record-specific material identity, role and stage.'});MAT[rid+'::'+m['id']]=iid
  for k,q in m['quantities'].items():attach(item,rid,ptr+'/quantities/'+esc(k),m['name']+' · '+k,q)
 for n,st in enumerate(r['stocks']):
  ptr=f'/stocks/{n}';item=add('precursors','stock-'+st['id'],st['name'].capitalize(),st['scope'],st['evidence'],scope='stock_context');item['stock_contexts']=[{'record_id':rid,'json_pointer':ptr,**deepcopy(st),'molecular_bindings_approved':False}];item['canonical_links'].append({'record_id':rid,'json_pointer':ptr,'relation':'Reported formulation; no additional physical charge.'});STOCK[rid+'::'+st['id']]=item['id']
  item['notes'].append('Components: '+', '.join(next(m['name']for m in r['materials']if m['id']==c['material_id'])for c in st['components'])+'. Solvent charge is not a calibrated final solution volume.')
  for k,q in st['concentrations'].items():attach(item,rid,ptr+'/concentrations/'+esc(k),k.replace('_',' ').capitalize(),q)
  for j,c in enumerate(st['components']):
   for k,q in c['quantities'].items():attach(item,rid,ptr+f'/components/{j}/quantities/'+esc(k),c['material_id']+' · '+k,q)
 for n,m in enumerate(r['measurements']):
  ptr=f'/measurements/{n}/value';uid=PTRUNIT[(rid,ptr)];item=ITEM[UNIT[uid][0]];f=attach(item,rid,ptr,m['property'].replace('_',' ').capitalize(),m['value'],m['sample_id']);MEAS[rid+'::'+m['id']]=item['id']
  if(rid,ptr)in TD:f['value']=json.loads(m['value']['value']);f['label']='Table headings, column order and source notes';f['presentation_kind']='curated_source_inventory';f['basis']='exact_canonical_payload_with_academic_display'
 for n,p in enumerate(r['products']):
  ptr=f'/products/{n}';item=ITEM['record-'+rid];item.setdefault('product_contexts',[]).append({'record_id':rid,'json_pointer':ptr,**deepcopy(p),'atomic_asset_binding_approved':False});item['canonical_links'].append({'record_id':rid,'json_pointer':ptr,'relation':'Source-scoped specimen, model or reference context.'});PRODUCT[rid+'::'+p['sample_id']]=item['id']
  for k in ['composition','phase','morphology','surface']:attach(item,rid,ptr+'/'+k,p['source_sample_label']+' · '+k,p[k],p['sample_id'])
 for k,q in r['intended_target'].items():attach(ITEM['record-'+rid],rid,'/intended_target/'+k,'Intended target · '+k,q)
FACTMAP={};TABLEMAP={}
for row in COV['facts']:
 fid=row['source_fact_id'];out=[]
 for b in row['canonical_bindings']:
  iid,f=FIELD[(b['record_id'],b['pointer'])];f.setdefault('source_fact_ids',[]).append(fid);ITEM[iid]['source_fact_ids'].append(fid);out.append({**b,'reader_item_id':iid,'reader_fact_id':f['id']})
 FACTMAP[fid]=out
for row in COV['table_cells']:
 b=row['canonical_bindings'][0];iid,f=FIELD[(b['record_id'],b['pointer'])];f['source_table_cell_id']=row['source_cell_id'];TABLEMAP[row['source_cell_id']]={**b,'reader_item_id':iid,'reader_fact_id':f['id']}
GROUP={k:[]for k in ['figures','tables','schemes','equations','source_notes']};PUBLIC=[];ASSET_UNITS={a['id']:[]for a in A['assets']}
for kind,plural in [('figure','figures'),('table','tables'),('scheme','schemes'),('equation','equations')]:
 for obj in D[plural]:
  for aid in obj.get('asset_ids',[obj.get('asset_id')]):
   if aid:ASSET_UNITS[aid].append(kind+':'+obj['id'])
for a in A['assets']:
 assert sha(a['path'])==a['sha256']and not a['whole_source_page'];ids=ASSET_UNITS[a['id']];assert ids,a['id'];uid=ids[0];item=ITEM[UNIT[uid][0]];e=a['evidence'][0];kind=uid.split(':',1)[0];group={'figure':'figures','table':'tables','scheme':'schemes','equation':'equations'}[kind]
 public='assets/figures/'+SID+'/'+Path(a['path']).name;rids=sorted({b['record_id']for u in ids for b in UB[u]})
 entry={'id':SID+'-'+a['id'],'label':item['title']+(' · continued excerpt'if a['id'].endswith(('-b','-c','-caption','-heading'))else''),'caption_paraphrase':item['text'],'document_role':e['document_role'],'page':e['pdf_page'],'printed_page':e['printed_page'],'sample_scope':item['sample_scope'],'sample_links':rids,'sample_linkage':'Source-defined composition, measurement or model context; no new same-aliquot, atomic-coordinate or exact recipe–structure join.','public_asset':public,'public_asset_sha256':a['sha256'],'asset_provenance':{'source_sha256':a['source_sha256'],'source_pdf_page':e['pdf_page'],'crop_normalized':a['bbox_normalized'],'source_render_scale':a['render_scale'],'pixel_dimensions':a['pixel_dimensions'],'transformation':'Original selected crop; no reconstructed plot, changed labels or whole-page attachment.'},'source_locators':[x['locator']for x in a['evidence']],'notes':item['notes'].copy(),'reader_render_verified':False,'reviewed':False,'training_eligible':False}
 if kind=='table':entry.update(source_rows=deepcopy(TM[uid.split(':',1)[1]]['rows']),source_notes=deepcopy(TM[uid.split(':',1)[1]]['notes']))
 GROUP[group].append(entry);PUBLIC.append({'id':entry['id'],'private_path':a['path'],'public_asset':public,'sha256':a['sha256'],'selected_original_only':True,'publication_approved':False})
 for u in ids:ITEM[UNIT[u][0]]['original_assets'].append({'id':entry['id'],'label':'Open original '+entry['label'],'public_asset':public,'public_asset_sha256':a['sha256']})
for item in ITEM.values():
 item['canonical_links']=uniq(item['canonical_links']);item['notes']=uniq(item['notes']);item['source_fact_ids']=uniq(item['source_fact_ids'])
 for f in item['facts']:
  if f.get('sample_id'):
   rid=f['canonical_record_id'];n=next(n for n,p in enumerate(R[rid]['products'])if p['sample_id']==f['sample_id']);item['sample_scope']['canonical_sample_links'].append({'record_id':rid,'sample_id':f['sample_id'],'json_pointer':f'/products/{n}','relation':'Exact canonical source context; no new physical specimen join.'})
 for b in item['canonical_links']:
  if b['json_pointer'].startswith('/measurements/'):
   m=resolve(R[b['record_id']],'/'.join(b['json_pointer'].split('/')[:3]));n=next(i for i,p in enumerate(R[b['record_id']]['products'])if p['sample_id']==m['sample_id']);item['sample_scope']['canonical_sample_links'].append({'record_id':b['record_id'],'sample_id':m['sample_id'],'json_pointer':f'/products/{n}','relation':'Existing measurement context; no additional specimen association.'})
  elif b['json_pointer'].startswith('/products/'):
   p=resolve(R[b['record_id']],b['json_pointer']);item['sample_scope']['canonical_sample_links'].append({'record_id':b['record_id'],'sample_id':p['sample_id'],'json_pointer':b['json_pointer'],'recipe_link':p['recipe_link'],'relation':'Exact source-defined product/context pointer.'})
 item['sample_scope']['canonical_sample_links']=list({(x['record_id'],x['json_pointer']):x for x in item['sample_scope']['canonical_sample_links']}.values())
docs=[]
for role in ['main','si']:
 pages=[p for p in PC['pages']if p['document_role']==role]
 docs.append({'role':role,'filename':'10.1021_acsami.1c18038'+('_si_1'if role=='si'else'')+'.pdf','sha256':pages[0]['source_sha256'],'page_count':len(pages),'pages':[{'page':p['pdf_page'],'printed_page':p['printed_page'],'text_read':p['text_read_in_full'],'visual_review':p['native_page_image_visually_inspected'],'sections':[prose(p['scope_notes'])]}for p in pages]})
routes={PRE+'bulk-a-route':[PRE+k for k in ['bulk-characterization','bulk-a-properties','mechanistic-context','dft-calculation','reagents-methods','source-context']],PRE+'bulk-b-route':[PRE+k for k in ['bulk-characterization','bulk-b-properties','mechanistic-context','dft-calculation','reagents-methods','source-context']],PRE+'nc-a-route':[PRE+k for k in ['nc-characterization','nc-properties','composite-film-series','film-beta-characterization','film-properties','reagents-methods','source-context']]}
counts={'reader_items':len(ITEM),'source_units':len(UNIT),'source_facts':len(FACTMAP),'source_fact_bindings':sum(map(len,FACTMAP.values())),'source_table_cells':len(TABLEMAP),'typed_reader_fields':len(FIELD),'canonical_records':len(R),'operations':len(OPS),'material_slots':len(MAT),'stock_slots':len(STOCK),'sample_context_slots':len(PRODUCT),'measurements':len(MEAS),'selected_original_assets':len(PUBLIC),'full_page_public_assets':0,'main_pages':8,'si_pages':26,'eligible_training_rows':0,'atomic_structure_assets':0}
review={'schema_version':'1.0','paper_id':SID,'doi':D['doi'],'title':D['title'],'paper':{'authors':D['authors'],'year':2021,'journal':'ACS Applied Materials & Interfaces','volume':13,'pages':'58908–58915'},'source_group':SID,'review_scope':'supplied_main_and_matched_si','documents':docs,'supporting_information':{'status':'matched_and_independently_source_reviewed','matched_local_si_count':1,'pdf_pages':26,'scope':'All supplied PDF pages were read and visually inspected; the independent source audit passed revision 2. The main article also identifies crystal ZIP and MP4 attachments, which were not found among the supplied local files and were not downloaded.'},'document_identity_verification':{'method':'Exact source hashes; matching title/byline and continuity with the main article’s supporting-information declaration.'},'coverage_status':'private_author_reader_proposal','independent_audit':'Independent source audit passed revision 2. Canonical, reader, molecular/apparatus, model and browser approvals remain separate pending gates.','publication_status':'Private proposal only.','source_review_promoted':False,'training_eligible':False,'recipe_inventory':[{'id':rid,'label':r['title'],'record_ids':[rid],'record_type':r['record_type'],'status':'author_draft_pending_independent_review','scope':'Records count preparation, measurement or model contexts rather than independently prepared physical batches.','gaps':r['quality']['missing_fields']}for rid,r in R.items()],'characterization_inventory':{'reader_item_ids':[i['id']for s in SECTIONS if s['id']in ['structures','properties']for i in s['items']]},'chemical_intuition':{'reader_item_ids':[i['id']for s in SECTIONS if s['id']=='intuition'for i in s['items']]},'reader_contract':{'version':'1.0','section_ids':[s['id']for s in SECTIONS]},'reader_sections':SECTIONS,**GROUP,'remaining_gaps':[prose(g['description'])for g in D['gaps']]+['Independent source passage does not approve this canonical/reader proposal. Molecular, product/crystal, apparatus, browser and publication stages remain separate.'],'evidence_conflicts':[{**deepcopy(c),'description':prose(c['description'])}for c in D['conflicts']],'route_evidence_contexts':routes,'route_evidence_scope_notes':{'all':'Record-ID arrays expose composition and source context without assigning every measurement to one physical specimen.','bulk_structure':'Printed non-hydrogen coordinates and displacement parameters apply to bulk A and B. The supplied PDFs omit complete hydrogen/occupancy data, and the cited crystal ZIP is absent; no atomic model is approved.','nanocrystal':'Bulk phase comparisons and one HRTEM spacing do not provide nanocrystal surface coordinates or exact recipe–structure labels. Dried-powder PLQE and colloidal settling remain separate states.','films':'The five relative blue/yellow mass formulations differ from the precursor spin-coated film. The precise composite ratio used in the β demonstration is not specified.','models':'Calculated gaps, parity/transition-probability arguments and fitted coupling descriptors remain author models rather than measured synthesis outcomes.'},'material_evidence_records':{'(C12H28N)2SbCl5':[PRE+k for k in ['bulk-a-route','bulk-characterization','bulk-a-properties','nc-a-route','nc-characterization','nc-properties','spincoat-film-route','film-properties']],'(C12H28N)SbCl4':[PRE+k for k in ['bulk-b-route','bulk-characterization','bulk-b-properties']],'A nanocrystals / BaMgAl10O17:Eu2+ / PS':[PRE+k for k in ['composite-film-series','film-beta-characterization','film-properties']]},'counts':counts}
save(SID+'.json',review)
save('reader-bindings-proposal.json',{'source_id':SID,'status':'private_unapproved','reader_sha256':sha(O/(SID+'.json')),'original_assets':PUBLIC,'operation_to_reader_item':OPS,'material_to_reader_item':MAT,'stock_to_reader_item':STOCK,'product_to_reader_item':PRODUCT,'molecular_apparatus_bindings_approved':False,'publication_approved':False})
save('source-item-coverage.json',{'source_units':UNIT,'source_facts':FACTMAP,'table_cells':TABLEMAP,'canonical_field_map':[{'record_id':rid,'json_pointer':ptr,'reader_item_id':v[0],'reader_fact_id':v[1]['id']}for(rid,ptr),v in FIELD.items()],'measurement_to_reader_item':MEAS,'private_canonical_manifest_sha256':sha(C/'record-manifest.json')})
checks=[]
def ck(n,ok):checks.append({'check':n,'passed':bool(ok)})
for(rid,ptr),(iid,f)in FIELD.items():ck(iid+' '+ptr+' exact canonical equality',resolve(R[rid],ptr)==f['canonical_quantity'])
for item in ITEM.values():
 for b in item['canonical_links']:ck(item['id']+' canonical pointer',resolve(R[b['record_id']],b['json_pointer'])is not None)
 for b in item['sample_scope']['canonical_sample_links']:ck(item['id']+' sample pointer',resolve(R[b['record_id']],b['json_pointer'])['sample_id']==b['sample_id'])
for a in PUBLIC:ck(a['id']+' crop hash',sha(a['private_path'])==a['sha256'])
ck('All source units/facts/table cells',set(UNIT)==set(U)and set(FACTMAP)==set(FM)and len(TABLEMAP)==891)
ck('All canonical operation/material/stock/product/measurement slots',len(OPS)==21 and len(MAT)==45 and len(STOCK)==5 and len(PRODUCT)==44 and len(MEAS)==1149)
ck('Six academic/source sections',[s['id']for s in SECTIONS]==['precursors','protocol','structures','properties','intuition','sources'])
ck('53 selected original excerpts only',len(PUBLIC)==53 and all(not a['whole_source_page']for a in A['assets']))
ck('No raw local source paths',not re.search(r'[A-Z]:[\\/]',json.dumps(review)))
ck('Record-ID arrays for routes',all(isinstance(a,list)and all(r in R for r in a)for a in routes.values()))
all_typed=set()
def walk_typed(v,ptr,rid):
 if isinstance(v,dict):
  if {'value','status','evidence'}<=v.keys():all_typed.add((rid,ptr));return
  for k,x in v.items():walk_typed(x,ptr+'/'+esc(k),rid)
 elif isinstance(v,list):
  for i,x in enumerate(v):walk_typed(x,ptr+'/'+str(i),rid)
for rid,r in R.items():walk_typed(r,'',rid)
ck('Every canonical typed field exactly represented',all_typed==set(FIELD))
ck('Frozen source and canonical bytes unchanged',all(sha(p)==h for p,h in FR['bound_files'].items())and all(sha(r['path'])==r['sha256']for r in CM['records']))
assert all(c['passed']for c in checks),[c for c in checks if not c['passed']]
save('author-validation.json',{'status':'author_pointer_transport_contract_checks_passed','author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'check_count':len(checks),'checks':checks,'counts':counts,'independent_source_audit':'passed_revision_2','independent_canonical_reader_audit':'pending','browser_visual_gate':'not_performed','site_written':False,'published':False})
inputs={str(p):sha(p)for p in [AP,P/'package-freeze.json',P/'source-facts.json',P/'source-inventory.json',P/'source-tables.json',P/'page-coverage.json',P/'original-assets-manifest.json',C/'record-manifest.json',C/'source-to-field-coverage.json',S/'scripts/build_paper_reviews.py',S/'dist/source-evidence.mjs']}
save('reader-manifest.json',{'schema':'mattersyn-private-reader-proposal/1','source_id':SID,'version':1,'author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'status':'private_author_draft_source_audit_passed_canonical_reader_audit_pending','input_hashes':inputs,'outputs':{n:sha(O/n)for n in [SID+'.json','reader-bindings-proposal.json','source-item-coverage.json','author-validation.json']},'author_script_sha256':sha(__file__),'counts':counts,'published':False})
print(json.dumps(counts));print('READER',sha(O/(SID+'.json')));print('MANIFEST',sha(O/'reader-manifest.json'))
