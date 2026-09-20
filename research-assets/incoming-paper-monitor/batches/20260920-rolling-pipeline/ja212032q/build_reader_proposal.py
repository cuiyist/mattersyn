"""Private unapproved Ghosh academic reader. Source/canonical inputs are read-only."""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import json,hashlib,re,sys
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;C=P/'canonical-proposal'/'v1';O=P/'public-review-proposal'/'v1';O.mkdir(parents=True,exist_ok=True)
assert not(C/'package-manifest.json').exists(),'Revise a frozen proposal separately.'
S=Path('[local path redacted]');SID='ghosh2012';PRE='ghosh-2012-'
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
assert AU['status']=='passed'and not AU['open_findings']and AU['proposal_freeze_sha256']==sha(P/'package-freeze.json')
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
 if k=='source-materials':return 'precursors'
 if k in ['structural-results','tem-procedure','xrd-procedure','ligand-spectra','ftir-procedure']:return 'structures'
 if k=='surface-mechanisms':return 'intuition'
 if k=='source-context':return 'sources'
 if k in ['photophysical-results','single-dot-procedure','lifetime-procedure','ensemble-optics','core-only-control']:return 'properties'
 return 'protocol'

def add(section,i,title,text,es=None,unit=None,scope='source_context'):
 assert i not in ITEM,i
 item={'id':i,'title':prose(title),'text':prose(text),'claim_type':'source_reported_context','sample_scope':{'formulations':[],'physical_batch_id':None,'scope_kind':scope,'state':prose(title),'link_limit':'Core sizes, shell cycles and explicit source contexts are retained. They do not identify one physical batch across microscopy, diffraction, ligand analysis and luminescence.','canonical_sample_links':[]},'evidence':uniq(evidence(es or[])),'source_locators':[e['locator']for e in es or[]],'canonical_links':[],'notes':[],'facts':[],'source_audit_unit_ids':[unit]if unit else[],'source_fact_ids':[],'original_assets':[],'training_eligible':False}
 ITEM[i]=item;next(s for s in SECTIONS if s['id']==section)['items'].append(item)
 if unit:UNIT.setdefault(unit,[]).append(i)
 return item
UB={x['source_unit_id']:x['canonical_bindings']for x in COV['source_units']}
TABLE_PROSE={
'table-1':'All five post-sulfur/post-cadmium schedules and their quantum yields at 5, 11 and 15 monolayers are retained. Approximate values and the greater-than-45% bound remain explicit. These comparison schedules are distinct from the preferred 1 h/2.5 h protocol; the narrative uncertainty statistics are not substituted into the table.',
'table-2':'The six solvent and ligand contexts retain precipitation onset, morphology, semiquantitative wurtzite:zinc-blende weight ratios, qualitative thick-shell quantum-yield labels and original TEM images. Low, Mod-High and None are not converted to fabricated percentages. The table does not identify every TEM population with one precise core size and shell count.',
'table-3':'The four stoichiometry variants retain both poor and improved outcomes. The 1% and 10% labels denote withdrawal of reaction solution while precursor charges remain fixed; they are not molar excess percentages. The TEM images show moderately thick shells, while the quantum-yield column concerns shells thicker than 15 monolayers. Those observations are not joined as one verified same-thickness specimen.',
'table-s1':'All eighteen rows and 180 numeric values preserve the printed core diameters, TEM-derived shell counts and volumes, amplitudes, component lifetimes and reported average lifetimes. The four core-size families stay separate. Mean and rounded coefficients do not necessarily recompute the reported mean lifetime exactly. The 5.5 nm/16.9 ML trace examples are not forced onto the 15.57 ML row.',
'table-s2-inset':'The eleven characteristic oleic-acid band assignments belong to the unnumbered inset inside Figure S2. The descending O–H range and very weak C=C qualifier are preserved. This is a pure-ligand reference, not a measured particle-surface composition.'}
FIG_PROSE={
'graphical-abstract':'The graphical abstract contrasts representative thick-shell blinking behavior and morphology. It summarizes the study rather than defining an additional experimental batch or a new numerical dataset.',
'figure-1':'Panels a/d show primary amine with Cd:OA 1:4; b/e show primary amine with 1:10; c/f show secondary amine with 1:4. The spectra distinguish mixed amine/oleate from oleate-dominated signatures. They do not establish exact ligand coverage or surface atomic coordinates.',
'figure-2':'The original TEM image retains the red outlines marking connected CdSe/CdS particles and the 5 nm scale bar. The authors interpret these attachments in terms of dipole-driven association; the image does not measure a dipole magnitude or identify every solution-phase contact.',
'figure-3':'The four core families are 2.2 nm (black), 3.0 nm (red), 4.0 nm (green) and 5.5 nm (blue). Panel a plots the nonblinking fraction against shell monolayers; panel b contrasts large- and small-core on-time histograms; panel c relates the fraction to average particle volume. The approximate 750 nm³ threshold and graphical uncertainty bars are retained without digitizing new precision. The caption uses at least 99% on-time, while main prose elsewhere uses greater than 99%.',
'figure-4':'Average photoluminescence lifetimes are plotted against total particle volume for the same four core-size families. Most series approach roughly 65 ns above approximately 750 nm³, but the 3.0 nm series continues to increase. The reported SI table provides its fitted values; the plotted trend is not a universal lifetime rule.',
'figure-s1':'Three original TEM images show short-anneal shell additions at 5, 11 and 19 monolayers, with reported overall diameters of 8.29, 12.01 and 17.3 nm. Each cation or anion addition is followed by 10 min, and each scale bar is 10 nm. The caption does not identify a unique starting-core batch.',
'figure-s2':'The pure oleic-acid reference spectrum accompanies an eleven-row band-assignment table. Its 1705 cm−1 carbonyl value remains distinct from the approximate acid-like feature near 1710 cm−1 discussed for particle studies.',
'figure-s3':'The left Cd:OA 1:4 particles are less strongly faceted than the right 1:10 particles. Both scale bars represent 10 nm. The source does not supply an exact core diameter and shell count for this pair.',
'figure-s4':'Panels a and e are wurtzite and zinc-blende reference lines. Experimental panels b, c and d correspond to primary amine, secondary amine and constant-sulfur growth, with displayed W:ZB ratios of 74:26, 67:33 and 40:60. The continued caption defines a semiquantitative phase-weight analysis, not an atomic-coordinate refinement supplied for these samples.',
'figure-s5':'This conceptual drawing compares primary- and secondary-amine packing on curved and flatter particle surfaces. The proposed steric preference for oleate at thick shells is an interpretation, not measured ligand coverage or a recovered molecular geometry.',
'figure-s6':'The secondary-amine experiment compares 5 and 11 monolayers. Its caption subsequently calls the thin-shell ligand oleylamine and assigns an NH2 band, creating a retained identity inconsistency. The printed peak values and both traces are preserved without silently correcting the ligand.',
'figure-s7':'The representative decay trace belongs to a film with 5.5 nm CdSe cores and 16.9 CdS monolayers under 405 nm, 1.0 MHz excitation. The logarithmic data and triexponential fit remain original artwork. The source does not explicitly identify this trace with the 15.57 ML final large-core table row.',
'figure-s8':'The upper binary plot is the 2.2 nm core/14.5 ML population and the lower plot the 5.5 nm core/16.9 ML population. Yellow denotes on and black off. Red and blue line traces each select dot index 6 from different populations. Their threshold is subtracted, unlike the raw per-pixel intensity used in the main classification equation; 100 ms integration and 91 ms readout are reported.'}

OBJS={k:{x['id']:x for x in D[k]}for k in ['materials','stocks','samples','figures','schemes','equations','references']}
for uid,u in U.items():
 oid=u['source_object_id'];kind=u['type'];binds=UB[uid];rid=binds[0]['record_id'];section=section_for_record(rid);obj=resolve(D,u['json_pointer']);title=obj.get('title',obj.get('name',oid.replace('-',' ').capitalize()));text=title;scope=kind
 if kind=='fact':
  text=obj['claim'];scope=obj['sample_scope'];title=obj.get('title',obj['id'].removeprefix(SID+'-').replace('-',' ').capitalize())
  if obj['claim_class']in ['author_interpretation','cited_context','author_model']:section='intuition'
  if oid.removeprefix(SID+'-')in ['short-anneal-tem','secondary-shape','attachment-image','xrd-pattern-values','oa-morphology-pair']:section='structures'
  if oid.removeprefix(SID+'-')in ['optimized-performance','nonblinking-definition','anneal-qy-summary','anneal-asymmetry','thin-shell-baseline']:section='properties'
 elif kind=='table':text=TABLE_PROSE[oid];scope=obj['sample_scope'];section='precursors'if oid=='table-s2-inset'else'properties'if oid in['table-1','table-s1']else'structures'
 elif kind=='protocol':text='This source-defined scope preserves its operations, alternatives and missing fields. Core-growth branches, preferred shell growth, comparative shell treatments and analytical preparation remain distinct. Grouped comparison inputs name alternatives and are not a combined physical charge.'
 elif kind=='figure':text=FIG_PROSE[oid];scope=obj['sample_scope'];section='intuition'if oid=='figure-s5'else'precursors'if oid=='figure-s2'else'structures'if oid in['figure-1','figure-2','figure-s1','figure-s3','figure-s4','figure-s6']else'properties'
 elif kind=='scheme':text='The generic SILAR scheme separates anion and cation additions, their annealing intervals and adjustable ligand/core variables. It starts with anion, while the preferred experimental protocol separately prepassivates the core with cadmium. A completed pair grows a full shell monolayer; one reagent addition is not silently counted as a complete layer.';scope=obj['sample_scope'];section='protocol'
 elif kind=='equation':text=obj['expression']+'. '+obj['meaning']+' This is an author-defined model or descriptor, not a new measured structure.';scope=obj['scope'];section='intuition'
 elif kind=='reference':text=obj['citation']+' This citation is reproduced as source identity; its full text was not separately read for this contribution.';section='sources';title=('SI reference 'if oid.startswith('si-')else'Reference ')+oid.rsplit('-',1)[-1]
 elif kind=='material':text=obj['name']+'. '+obj['scope_note'];section='precursors'
 elif kind=='stock':text=obj['scope'];section='precursors'
 elif kind=='sample_context':text=obj['name'].capitalize()+'. '+obj['scope_note']+' '+obj.get('lineage_relation','');scope=obj['id']
 if kind=='sample_context':
  title={'core-2p2':'2.2 nm CdSe core-growth branch','core-5p5':'5.5 nm CdSe core-growth branch','core-3-or-4':'3 or 4 nm CdSe core-growth branch','core-common':'Common core preparation','ftir-primary-1to4':'Primary amine, Cd:OA 1:4','ftir-primary-1to10':'Primary amine, Cd:OA 1:10','od-secondary':'Octadecane with secondary amine','od-primary':'Octadecane with primary amine','ode-primary':'Octadecene with primary amine','core-only-7nm':'Separate 7 nm core-only control'}.get(oid,title)
  if oid.startswith('lifetime-row-'):title='Lifetime row '+oid.rsplit('-',1)[-1]+': '+str(obj['reported_core_diameter_nm'])+' nm core, '+str(obj['reported_shell_monolayers_TEM'])+' TEM-derived monolayers'
  text=title+'. '+obj['scope_note']+' '+obj.get('lineage_relation','')
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
  if op['id']in['tem-acquire','xrd-deposit','xrd-acquire-fit','ftir-purify-cast','ftir-acquire']:section='structures'
  if op['id'].startswith(('single-','lifetime-'))or op['id']in['ensemble-acquire','core-control-wash']:section='properties'
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
 for n,option in enumerate(r['condition_options']):
  item=ITEM['source-table-table-1'];ptr=f'/condition_options/{n}'
  item['canonical_links'].append({'record_id':rid,'json_pointer':ptr,'relation':'Exact source comparison schedule; a full shell cycle contains separate S and Cd additions.'})
  for k,q in option['parameters'].items():attach(item,rid,ptr+'/parameters/'+esc(k),option['label']+' · '+k,q)
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
 docs.append({'role':role,'filename':'10.1021_ja212032q'+('_si_1'if role=='si'else'')+'.pdf','sha256':pages[0]['source_sha256'],'page_count':len(pages),'pages':[{'page':p['pdf_page'],'printed_page':p['printed_page'],'text_read':p['text_read_in_full'],'visual_review':p['native_page_image_visually_inspected'],'sections':[prose(p['scope_notes'])]}for p in pages]})
# R keys are already complete record IDs; these arrays expose study context only.
routes={PRE+k:[rid for rid in R if rid!=PRE+k]for k in['core-standard-route','core-small-variant','core-large-variant','optimized-shell-route','constant-s-variant']}
counts={'reader_items':len(ITEM),'source_units':len(UNIT),'source_facts':len(FACTMAP),'source_fact_bindings':sum(map(len,FACTMAP.values())),'source_table_cells':len(TABLEMAP),'typed_reader_fields':len(FIELD),'canonical_records':len(R),'operations':len(OPS),'material_slots':len(MAT),'stock_slots':len(STOCK),'sample_context_slots':len(PRODUCT),'measurements':len(MEAS),'selected_original_assets':len(PUBLIC),'full_page_public_assets':0,'main_pages':10,'si_pages':9,'eligible_training_rows':0,'atomic_structure_assets':0}
review={'schema_version':'1.0','paper_id':SID,'doi':D['doi'],'title':D['title'],'paper':{'authors':D['authors'],'year':2012,'journal':'Journal of the American Chemical Society','volume':134,'pages':'9634–9643'},'source_group':SID,'review_scope':'supplied_main_and_matched_si','documents':docs,'supporting_information':{'status':'matched_full_supplied_pdf_source_audit_passed','matched_local_si_count':1,'pdf_pages':9,'scope':'All ten main and nine matched SI pages were read and visually inspected by the extraction author. A distinct source audit of extraction revision 2 passed. Raw fit trajectories and atomic-coordinate files are not supplied or invented.'},'document_identity_verification':{'method':'Exact source hashes and matching six-author byline/title; main SI declaration and figure/table continuity.'},'coverage_status':'private_author_reader_proposal','independent_audit':'The separate full supplied-source extraction audit passed revision 2; canonical and reader independent reviews remain pending. Historical pending flags in the frozen source payload precede that audit. No model approval is claimed.','publication_status':'Private unapproved proposal only.','source_review_promoted':False,'training_eligible':False,'recipe_inventory':[{'id':rid,'label':r['title'],'record_ids':[rid],'record_type':r['record_type'],'status':'author_draft_pending_independent_review','scope':'Core routes, shell variants and comparison/acquisition contexts do not count independently verified batches.','gaps':r['quality']['missing_fields']}for rid,r in R.items()],'characterization_inventory':{'reader_item_ids':[i['id']for s in SECTIONS if s['id']in['structures','properties']for i in s['items']]},'chemical_intuition':{'reader_item_ids':[i['id']for s in SECTIONS if s['id']=='intuition'for i in s['items']]},'reader_contract':{'version':'1.0','section_ids':[s['id']for s in SECTIONS]},'reader_sections':SECTIONS,**GROUP,'remaining_gaps':[prose(g['description'])for g in D['gaps']]+['The source extraction audit passed; independent canonical and reader approval is pending. Molecular, product, apparatus, browser and publication gates remain separate.'],'evidence_conflicts':deepcopy(D['conflicts']),'route_evidence_contexts':routes,'route_evidence_scope_notes':{'all':'The linked records are study context, not a statement that every figure measured the exact product of this route.','core':'3/4 nm common growth, 2.2 nm quench and 5.5 nm feed variants are separate branches. The unreported preparation of 7 nm core-only control is not inherited from them.','shell':'The preferred S 1 h/Cd 2.5 h schedule differs from Table 1. Source half-layer precursor additions, full shell cycles and Cd prepassivation remain distinct.','comparisons':'Table 2 and 3 alternatives are not simultaneous ligand/solvent charges; Table 3 moderately thick TEM and >15 ML QY scopes differ.','structure':'TEM and semiquantitative phase weights do not supply atomic coordinates, CIF or exact recipe–structure labels.','optics':'The two nonblinking inequalities, source-specific mean lifetimes, 3 nm exception and unverified 16.9/15.57 ML join are retained.'},'material_evidence_records':{'CdSe':[rid for rid,r in R.items()if r['material']['formula']=='CdSe'],'CdSe/CdS':[rid for rid,r in R.items()if r['material']['formula']=='CdSe/CdS']},'counts':counts}
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
ck('All source units/facts/table cells',set(UNIT)==set(U)and set(FACTMAP)==set(FM)and len(TABLEMAP)==272)
ck('All canonical operation/material/stock/product/measurement slots',len(OPS)==CM['counts']['operations'] and len(MAT)==CM['counts']['material_slots'] and len(STOCK)==CM['counts']['stock_slots'] and len(PRODUCT)==CM['counts']['sample_context_slots'] and len(MEAS)==CM['counts']['measurements'])
ck('Six academic/source sections',[s['id']for s in SECTIONS]==['precursors','protocol','structures','properties','intuition','sources'])
ck('36 selected original excerpts only',len(PUBLIC)==36 and all(not a['whole_source_page']for a in A['assets']))
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
