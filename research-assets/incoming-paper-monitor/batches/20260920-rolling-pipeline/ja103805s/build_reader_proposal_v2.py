"""Private source-linked Evans reader; no Site writes or whole-document public assets."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
from collections import Counter
import json,hashlib,re,sys
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parent;C=B/'canonical-proposal/v2';O=B/'public-review-proposal/v2';O.mkdir(parents=True,exist_ok=True)
SITE=Path(r'[local path redacted]');SID='evans2010'
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def esc(x):return str(x).replace('~','~0').replace('/','~1')
def norm(x):return re.sub('[^a-z0-9]+','-',str(x).lower()).strip('-')
def resolve(x,p):
 for t in p.strip('/').split('/') if p else []:x=x[int(t)] if isinstance(x,list) else x[t.replace('~1','/').replace('~0','~')]
 return x
def uniq(x):return list({json.dumps(a,sort_keys=True,ensure_ascii=False):a for a in x}.values())
I=read(B/'source-inventory.json');F=read(B/'source-extraction-revision-2/source-facts.json');A=read(B/'selected-original-assets.json');PC=read(B/'page-coverage.json');MAN=read(C/'record-manifest.json');COV=read(C/'source-to-field-coverage.json');FR=read(B/'source-extraction-revision-2/source-extraction-freeze.json')
R={x['record_id']:read(x['path']) for x in MAN['records']};U={u['id']:u for u in I['units']};FM={f['id']:f for f in F['facts']}
for r in MAN['records']:assert sha(r['path'])==r['sha256']
SEC=[{'id':s,'title':t,'items':[]} for s,t in [('precursors','Precursors'),('protocol','Synthesis protocol'),('structures','Final structures'),('properties','Properties'),('intuition','Chemical intuition'),('sources','Sources and limitations')]]
ITEMS={};FIELD={};UNIT={};OPS={};MATS={};STOCKS={};PROD={};MEAS={}
def readevidence(es):
 out=[]
 for e in es:
  m=re.search(r'(MAIN|SI) PDF p\. (\d+) \(printed ([^)]+)\)',e['locator'])
  out.append({'source_id':SID,'document_role':m[1].lower() if m else 'cif' if e['locator'].startswith('CIF') else 'main','pdf_page':int(m[2]) if m else None,'printed_page':m[3] if m else None,'locator':e['locator']})
 return out
def ue(uid):
 u=U[uid];return [{'source_id':SID,'document_role':u['source_role'],'pdf_page':u['pdf_page'],'printed_page':u['printed_page'],'locator':u['locator']}]
def add(sec,key,title,text,scope='source_context',units=None,evidence=None):
 assert key not in ITEMS,key
 i={'id':key,'title':title,'text':text,'claim_type':'source_reported_context','sample_scope':{'formulations':[],'physical_batch_id':None,'scope_kind':scope,'state':title,'link_limit':'Source associations preserve their original formulation and technique scopes. Identical nominal composition does not establish one physical specimen.','canonical_sample_links':[]},'evidence':uniq((evidence or [])+[e for u in units or [] for e in ue(u)]),'source_locators':[],'canonical_links':[],'notes':[],'facts':[],'source_audit_unit_ids':units or [],'source_fact_ids':[],'original_assets':[],'training_eligible':False}
 i['source_locators']=[e['locator'] for e in i['evidence']];ITEMS[key]=i;next(s for s in SEC if s['id']==sec)['items'].append(i)
 for u in units or []:UNIT.setdefault(u,[]).append(key)
 return i
def polish(x):
 # Source-author spacing corrections for human prose only; canonical fields stay exact.
 for a,b in [('species9','species 9'),('FigureS','Figure S'),('Table1','Table 1'),('compound3','compound 3'),('compound4','compound 4'),('compound13','compound 13'),('excessDPPSe','excess DPPSe'),('two-level','two-level')]:x=x.replace(a,b)
 x=re.sub(r'(?<=[a-z])(?=\d)', ' ',x)
 x=re.sub(r'(?<=\d)(?=(?:mol|mmol|umol|mL|uL|mg|nm|ppm|min|h\b|°C))',' ',x)
 return x
TITLE={
'identity':'Paper identity and publication metadata','main-si-cif-pairing':'Main article, supporting information and molecular-CIF pairing','acknowledgments':'Acknowledgments and research support','background':'Cited quantum-dot synthesis background','abstract-mechanistic-scope':'Scope of the authors’ mechanistic conclusions','commercial-versus-pure':'Commercial and purified phosphine-selenide controls','nmr-general':'NMR acquisition and solvent preparation','impurity-reactivity':'Secondary-phosphine impurities and precursor reactivity','dppse-room-temp-reactivity':'Room-temperature DPPSe–metal-carboxylate observations','dpp-topse-main-shifts':'TOPSe/DPP reaction: main-text chemical shifts','se-exchange-evidence':'Evidence for rapid selenium exchange','mechanism-limit-and-outlook':'Mechanistic limits and future hypotheses','ligand-aggregation':'Ligand-dependent stabilization and aggregation','species9-acquisition':'Single-crystal diffraction of molecular species 9','yield-general':'Study-wide precursor-conversion claim','cif-format-limitation':'Original CIF syntax and delivery limitation',
'object-figure-1':'Figure 1: PbSe cluster formation from A, B and C','object-table-1':'Table 1: observed compounds and NMR assignments','object-scheme-1':'Scheme 1: proposed DPPSe/Pb-oleate pathways','object-scheme-2':'Scheme 2: proposed reduction by DPP','object-figure-2':'Figure 2: TOPSe with 15 mol% DPP','object-figure-S1':'Figure S1: commercial TOP impurities','object-figure-S2':'Figure S2: tributylphosphine impurities','object-figure-S3':'Figure S3: TOPSe impurities and couplings','object-figure-S4':'Figure S4: TOPSe fractions A/C and independent stock B','object-figure-S5':'Figure S5: A/B/C absorption time series','object-figure-S6':'Figure S6: phosphorus NMR during the Pb thermal control','object-figure-S7':'Figure S7: proton NMR of the same Pb-control time series','object-figure-S8':'Figure S8: separate Cd precursor-ratio experiments','object-figure-S9':'Figure S9: the separate Pb 1:1 experiment','object-figure-S10':'Figure S10: Cd reaction at 10 minutes and 24 hours','object-figure-S11':'Figure S11: carbon NMR of the 24-hour Cd sample','object-figure-S12':'Figure S12: molecular species 9','object-figure-S13':'Figure S13: intermolecular packing of species 9','object-figure-S14':'Figure S14: alternative monomer-generation hypotheses','object-figure-S15':'Figure S15: separate CdSe and PbSe optical examples','object-figure-S16':'Figure S16: spherical and cubic PbSe TEM examples','object-scheme-S1':'Scheme S1: alternative pathways to species 9','object-scheme-S13-unnumbered':'SI S13: proposed disproportionation pathway','object-table-S7-composition':'SI S7: composition determined by phosphorus NMR','object-calculation-S21-yield':'SI S21: optical conversion calculation and printed conflict'}
P={p['id']:p for p in I['procedures']}
PN={norm(p['id']):p for p in I['procedures']}
def unit_section(u):
 uid=u['id'];short=uid.removeprefix('evans2010-')
 if u['kind'] in ['identity','metadata','reference','source_scope','source_format']:return 'sources'
 if short.startswith('cif-') or short=='species9-acquisition' or short in ['object-figure-S12','object-figure-S13','object-figure-S16']:return 'structures'
 if short in P:return 'precursors' if P[short]['category'] in ['precursor_preparation','purification','stock_preparation'] else 'protocol'
 if short.startswith('reagent-'):return 'precursors'
 if u['kind'] in ['author_model','author_interpretation','cited_background'] or short in ['impurity-reactivity','dppse-room-temp-reactivity','se-exchange-evidence','ligand-aggregation']:return 'intuition'
 if short in ['object-figure-S1','object-figure-S2','object-figure-S3','object-figure-S4','object-table-S7-composition']:return 'precursors'
 return 'properties'
for uid,u in U.items():
 short=uid.removeprefix('evans2010-');title=TITLE.get(short,P.get(short,{}).get('label') or (u['claim'] if u['kind']=='material' else short.replace('-',' ').capitalize()))
 if u['kind']=='cif_scalar':title='Molecular crystal: '+u['locator'].split(';')[0]
 if u['kind']=='cif_loop':title={'cif-loop-1':'CIF scattering factors','cif-loop-2':'CIF symmetry operations','cif-loop-3':'CIF atomic sites and occupancies','cif-loop-4':'CIF anisotropic displacement parameters','cif-loop-5':'CIF bond and contact distances','cif-loop-6':'CIF angles','cif-loop-7':'CIF torsions'}[short]
 text=polish(u['claim'])
 if u['kind'].startswith('cif_'):text+=' The supplied refinement belongs to molecular Pb(Se₂PPh₂)₂ (species 9), not to a PbSe or CdSe quantum dot. Raw uncertainty notation and refinement flags remain explicit.'
 if u['kind']=='author_model':text+=' This is an author-proposed pathway; unisolated intermediates are not presented as measured atomic structures.'
 ii=add(unit_section(u),'unit-'+norm(short),title,text,u['kind'],[uid]);ii['notes']+=['Source status: '+u['status']+'.']
 for c in I['source_conflicts']:
  if c['id'] in u.get('conflict_ids',[]):ii['notes'].append(c['id']+': '+c['issue'])
for x in COV['source_units']:
 ii=ITEMS[UNIT[x['source_unit_id']][0]]
 for b in x['canonical_bindings']:ii['canonical_links'].append({'record_id':b['record_id'],'json_pointer':b['pointer'],'relation':'Exact source-unit field; source scope and missingness retained.'})
def recsec(rid):
 k=rid.removeprefix('evans-2010-')
 if k in ['molecular9-structure','pbse-tem']:return 'structures'
 if k in ['reagents','top-impurities','tbp-impurities','topse-impurities'] or k in PN and PN[k]['category'] in ['precursor_preparation','purification','stock_preparation']:return 'precursors'
 if k=='mechanism':return 'intuition'
 if k=='source-context':return 'sources'
 return 'protocol' if k in PN else 'properties'
for rid,r in R.items():
 ii=add(recsec(rid),'record-'+rid,r['title'].split(' · ',1)[1],r['method'].capitalize()+'. This record preserves one preparation, control family or observation context; it does not count physical replicates.')
 ii['canonical_links'].append({'record_id':rid,'json_pointer':'','relation':'Private canonical author draft; independent audit pending.'});ii['notes']+=r['quality']['missing_fields']+r['quality']['conflicts']
def value(q):
 if q['value'] is not None:return q['value']
 a,b=q.get('minimum'),q.get('maximum')
 if a is not None and b is not None:return ('(' if q.get('minimum_exclusive') else '[')+str(a)+', '+str(b)+(')' if q.get('maximum_exclusive') else ']')
 if a is not None:return ('> ' if q.get('minimum_exclusive') else '≥ ')+str(a)
 if b is not None:return ('< ' if q.get('maximum_exclusive') else '≤ ')+str(b)
 return 'Not reported'
def attach(ii,rid,ptr,label,q,sample=None):
 assert (rid,ptr) not in FIELD,(rid,ptr)
 ff={'id':rid+'::'+ptr,'label':label,'value':value(q),'unit':q.get('unit'),'status':q['status'],'approximate':q.get('approximate',False),'basis':'exact_canonical_field','qualifier':' '.join(q.get(k,'') for k in ['basis','qualifier','note']),'evidence':readevidence(q.get('evidence',[])),'canonical_record_id':rid,'json_pointer':ptr,'canonical_quantity':deepcopy(q),'presentation_kind':'exact_quantity','training_eligible':False}
 if sample:ff['sample_id']=sample
 ii['facts'].append(ff);FIELD[(rid,ptr)]=(ii['id'],ff);return ff
SOURCEPTR={}
PAYLOADS={(x['record_id'],x['pointer']):x for x in COV['source_objects'] if x.get('mode')=='lossless_curated_source_payload'}
for x in COV['source_units']:
 for b in x['canonical_bindings']:SOURCEPTR.setdefault((b['record_id'],b['pointer']),x['source_unit_id'])
for rid,r in R.items():
 for n,op in enumerate(r['operations']):
  ptr=f'/operations/{n}';uid=SOURCEPTR[(rid,ptr)];ii=add('properties' if op['stage']=='characterization' else recsec(rid),'operation-'+op['id'],op['label'],polish(op['description']),'source_operation',[uid],readevidence(op['evidence']))
  labels={m['id']:m['name'] for m in r['materials']}|{s['id']:s['name'] for s in r['stocks']}|{s['id']:s['name'] for s in r['material_states']}
  ii['operation_context']={'record_id':rid,'operation_id':op['id'],'json_pointer':ptr,**{k:deepcopy(op[k]) for k in ['stage','branch','depends_on','environment','inputs','outputs','retained_fraction','endpoint']},'optional_inputs':op.get('optional_inputs',[]),'material_flow_labels':{k:labels[k] for k in op['inputs']+op.get('optional_inputs',[])+op['outputs']},'diagram_binding_status':'pending_independent_visual_binding'}
  ii['canonical_links'].append({'record_id':rid,'json_pointer':ptr,'relation':'Exact operation, inputs, output, conditions and retained fraction.'});ii['notes']+=['Inputs: '+', '.join(labels[x] for x in op['inputs'])+'.','Output: '+', '.join(labels[x] for x in op['outputs'])+'.']
  if op.get('optional_inputs'):ii['notes'].append('Separate source alternatives: '+', '.join(labels[x] for x in op['optional_inputs'])+'. These are not combined charges.')
  if op['retained_fraction']:ii['notes'].append('Retained fraction: '+labels[op['retained_fraction']]+'.')
  for key,q in op['parameters'].items():attach(ii,rid,ptr+'/parameters/'+esc(key),key.replace('_',' ').capitalize(),q)
  for key in ['environment','endpoint']:attach(ii,rid,ptr+'/'+key,key.capitalize(),op[key])
  OPS[rid+'::'+op['id']]=ii['id']
 for n,m in enumerate(r['materials']):
  key='material-'+m['id'];ii=ITEMS.get(key) or add('intuition' if m['role']=='proposed_intermediate' else 'precursors',key,m['name'],('Proposed, unisolated intermediate. ' if m['role']=='proposed_intermediate' else '')+'Formula or source condensed identity: '+str(m['formula'] or 'not assigned')+'. Molecular coordinates and geometry are not inferred from the name.','material_identity',evidence=readevidence(m['evidence']))
  ptr=f'/materials/{n}';ii.setdefault('material_identities',[]).append({'source_material_id':m['id'],'name':m['name'],'formula':m['formula'],'role':m['role'],'canonical_record_id':rid,'json_pointer':ptr,'exact_molecular_asset_binding_approved':False});ii['notes']+=m['notes'];ii['canonical_links'].append({'record_id':rid,'json_pointer':ptr,'relation':'Exact material slot; source role and stage remain record-specific.'});MATS[rid+'::'+m['id']]=ii['id']
  for key,q in m['quantities'].items():attach(ii,rid,ptr+'/quantities/'+esc(key),m['name']+' · '+key,q)
 for n,s in enumerate(r['stocks']):
  ptr=f'/stocks/{n}';ii=ITEMS.get('stock-'+s['id']) or add('precursors','stock-'+s['id'],s['name'].capitalize(),'The stock composition and concentration are distinct from the final reaction mixture. Absolute charges, dilution and missing solvent information retain their source scope.','stock_context',evidence=readevidence(s['evidence']))
  ii.setdefault('stock_contexts',[]).append({'record_id':rid,'json_pointer':ptr,**deepcopy(s),'molecular_bindings_approved':False});ii['canonical_links'].append({'record_id':rid,'json_pointer':ptr,'relation':'Exact stock components and concentration basis.'});STOCKS[rid+'::'+s['id']]=ii['id']
  ii['notes'].append('Components: '+', '.join(next(m['name'] for m in r['materials'] if m['id']==c['material_id']) for c in s['components'])+'.')
  if s['id']=='pbse-pb-stock':ii['notes'].append('The Pb-oleate stock solvent is not explicitly reported in the PbSe recipe.')
  if s['id']=='topse-B':ii['notes'].append('B is independently prepared, not the second distillation cut. The starting-solute wording conflicts between prose and caption (C4).')
  for key,q in s['concentrations'].items():attach(ii,rid,ptr+'/concentrations/'+esc(key),key.replace('_',' ').capitalize(),q)
 for n,m in enumerate(r['measurements']):
  ptr=f'/measurements/{n}/value';uid=SOURCEPTR[(rid,ptr)];ii=ITEMS[UNIT[uid][0]];label=m['property'].replace('_',' ').capitalize()
  ff=attach(ii,rid,ptr,label,m['value'],m['sample_id']);MEAS[rid+'::'+m['id']]=ii['id']
  if (rid,ptr) in PAYLOADS:
   obj=json.loads(m['value']['value']);ff['value']=obj;ff['label']=('Worked expression' if 'raw_expression_transcribed' in obj else 'Complete source table')+' · '+obj['id'];ff['presentation_kind']='curated_source_inventory';ff['basis']='exact_canonical_payload_with_academic_display'
 for n,p in enumerate(r['products']):
  ptr=f'/products/{n}';ii=ITEMS['record-'+rid];ii.setdefault('product_contexts',[]).append({'record_id':rid,'json_pointer':ptr,**deepcopy(p),'atomic_asset_binding_approved':False});PROD[rid+'::'+p['sample_id']]=ii['id'];ii['canonical_links'].append({'record_id':rid,'json_pointer':ptr,'relation':'Source context or named sample; physical aliquot identity not inferred.'})
  for key in ['composition','phase','morphology','surface']:attach(ii,rid,ptr+'/'+key,(p['source_sample_label'] or p['sample_id'])+' · '+key,p[key],p['sample_id'])
FACTMAP={}
for x in COV['facts']:
 fid=x['source_fact_id'];entries=[]
 for b in x['canonical_bindings']:
  iid,ff=FIELD[(b['record_id'],b['pointer'])];ff.setdefault('source_fact_ids',[]).append(fid);ITEMS[iid]['source_fact_ids'].append(fid);entries.append({**b,'reader_item_id':iid,'reader_fact_id':ff['id']})
 FACTMAP[fid]=entries
GROUP={k:[] for k in ['figures','tables','schemes','equations','source_notes']};PUBLIC=[]
for a in A['assets']:
 assert sha(a['path'])==a['sha256'];uid='evans2010-object-'+a['id'];assert uid in U
 group='figures' if a['id'].startswith('figure-') else 'tables' if a['id'].startswith('table-') else 'schemes' if a['id'].startswith('scheme-') else 'source_notes'
 public='assets/figures/evans2010/'+Path(a['path']).name;ii=ITEMS[UNIT[uid][0]];rids=sorted({b['record_id'] for b in next(x for x in COV['source_units'] if x['source_unit_id']==uid)['canonical_bindings']})
 entry={'id':SID+'-'+a['id'],'label':ii['title'],'caption_paraphrase':ii['text'],'document_role':a['source_role'],'page':a['pdf_page'],'printed_page':a['printed_page'],'sample_scope':U[uid]['sample_scope'],'sample_links':rids,'sample_linkage':'Figure-level context only. Panel labels and source-specific relationships are retained; no universal physical sample is inferred.','public_asset':public,'public_asset_sha256':a['sha256'],'asset_provenance':{'source_sha256':a['source_sha256'],'source_pdf_page':a['pdf_page'],'crop_pdf_points':a['crop_pdf_points'],'renderer':a['renderer'],'dpi':a['dpi'],'pixel_dimensions':a['pixel_dimensions'],'transformation':'Selected original figure/table/scheme crop; no generated reconstruction or full-page rendering.'},'source_locators':[U[uid]['locator']],'notes':ii['notes'].copy(),'reader_render_verified':False,'reviewed':False,'training_eligible':False}
 if a['id']=='figure-S16':entry['notes']+=['Left scale bar: 5 nm; right scale bar: 50 nm. Scale bars are not measured particle diameters. Exact recipe/time linkage for the two morphology examples is unreported.','Hexagonal and cubic particle packing are not assignments of the internal atomic crystal phase.']
 if a['id'] in ['figure-S12','figure-S13']:entry['notes'].append('Molecular species 9 only; the CIF is not a PbSe or CdSe quantum-dot structure.')
 if a['id']=='calculation-S21-yield':entry['notes'].append('The printed final denominator has a positive exponent inconsistent with the initial limiting charge. The original and qualified calculation remain separate.')
 GROUP[group].append(entry);PUBLIC.append({'id':entry['id'],'private_path':a['path'],'public_asset':public,'sha256':a['sha256'],'selected_original_only':True})
 ii['original_assets'].append({'id':entry['id'],'label':'Open original '+entry['label'],'public_asset':public,'public_asset_sha256':a['sha256']})
for table in I['tables']:
 entry=next((x for x in GROUP['tables'] if x['id']==SID+'-'+table['id']),None)
 if entry is None:
  entry={'id':SID+'-'+table['id'],'label':table['id'].replace('-',' ').capitalize(),'source_locators':[U[u]['locator'] for u in table.get('source_unit_ids',[table.get('source_unit_id')])],'scope':'Curated arrangement of source-reported labels; no new experimental replicate or trace digitization.'};GROUP['tables'].append(entry)
 entry['source_rows']=deepcopy(table['rows']);entry['source_notes']={k:deepcopy(v) for k,v in table.items() if k not in ['rows','id','source_unit_id','source_unit_ids']}
calc=next(x for x in GROUP['source_notes'] if x['id']==SID+'-calculation-S21-yield')
for eq in I['equations']:
 GROUP['equations'].append({'id':SID+'-'+eq['id'],'label':eq['id'].replace('-',' ').capitalize(),**deepcopy(eq),'public_asset':calc['public_asset'],'public_asset_sha256':calc['public_asset_sha256'],'scope':'Author calculation with printed notation preserved; model values are not measured current-QD coordinates.'})
for ii in ITEMS.values():
 ii['canonical_links']=uniq(ii['canonical_links']);ii['notes']=uniq(ii['notes']);ii['source_fact_ids']=uniq(ii['source_fact_ids'])
 for f in ii['facts']:
  if f.get('sample_id'):
   rid=f['canonical_record_id'];n=next(n for n,p in enumerate(R[rid]['products']) if p['sample_id']==f['sample_id']);ii['sample_scope']['canonical_sample_links'].append({'record_id':rid,'sample_id':f['sample_id'],'json_pointer':f'/products/{n}','relation':'Record-scoped source context; not an independent replicate.'})
 ii['sample_scope']['canonical_sample_links']=uniq(ii['sample_scope']['canonical_sample_links'])
docs=[]
for role in ['main','si']:
 d=FR['source_documents'][role];pages=[p for p in PC['pages'] if p['source_role']==role];docs.append({'role':role,'filename':d['original_filename'],'sha256':d['sha256'],'page_count':d['page_count'],'pages':[{'page':p['pdf_page'],'printed_page':p['printed_page'],'text_read':p['text_read'],'visual_review':p['visually_inspected'],'sections':[p['coverage_notes']]} for p in pages]})
gaps=[x['scope']+': '+', '.join(x['fields']) for x in I['missingness']]
routes={rid:[other for other in R if other!=rid and (rid.endswith('cdse-qd') and any(s in other for s in ['cd-oleate','dppse','cd-ratio','cd-timecourse','optical','mechanism','source-context']) or rid.endswith('pbse-qd') and any(s in other for s in ['pb-oleate','dppse','pb-ratio','pbse-tem','pbse-conversion','optical','mechanism','source-context']) or rid.endswith('pbse-msc-family') and any(s in other for s in ['topse','top-impurities','pb-oleate','mechanism','source-context']))] for rid in R if R[rid]['record_type']=='literature_protocol'}
counts={'reader_items':len(ITEMS),'source_units':len(UNIT),'source_facts':len(FACTMAP),'source_fact_bindings':sum(map(len,FACTMAP.values())),'typed_reader_fields':len(FIELD),'operations':len(OPS),'material_slots':len(MATS),'stock_slots':len(STOCKS),'sample_context_slots':len(PROD),'measurements':len(MEAS),'canonical_records':len(R),'selected_original_assets':len(PUBLIC),'full_page_public_assets':0,'main_pages':3,'si_pages':21,'exact_qd_structure_pairs':0}
review={'schema_version':'1.0','paper_id':SID,'doi':I['doi'],'title':I['title'],'paper':{'authors':['Christopher M. Evans','Meagan E. Evans','Todd D. Krauss'],'year':2010,'journal':'Journal of the American Chemical Society','volume':132,'pages':'10973–10975'},'source_group':SID,'review_scope':'supplied_main_and_matched_si','documents':docs,'supporting_information':{'status':'matched_and_independently_source_reviewed','matched_local_si_count':1,'pdf_pages':21,'additional_molecular_cif':True,'scope':'Complete independent source review passed revision 2. Molecular species 9 supplies the CIF; QD coordinates are absent.'},'document_identity_verification':{'method':'Content identity, source fingerprints and species-9 formula/cell/diffraction agreement. The CIF lacks the article DOI/title and is paired by content.'},'coverage_status':'private_author_reader_proposal','independent_audit':'Independent source audit passed revision 2. Canonical, reader, molecular/apparatus and browser reviews remain separate pending gates.','publication_status':'Private proposal only.','source_review_promoted':False,'training_eligible':False,'recipe_inventory':[{'id':rid,'label':r['title'],'record_ids':[rid],'record_type':r['record_type'],'status':'author_draft_pending_independent_review','scope':'Supporting procedures and observation contexts are not additional independent synthesis experiments.','gaps':r['quality']['missing_fields']} for rid,r in R.items()],'characterization_inventory':{'reader_item_ids':[i['id'] for s in SEC if s['id'] in ['structures','properties'] for i in s['items']]},'chemical_intuition':{'reader_item_ids':[i['id'] for s in SEC if s['id']=='intuition' for i in s['items']]},'reader_contract':{'version':'1.0','section_ids':[s['id'] for s in SEC]},'reader_sections':SEC,**GROUP,'remaining_gaps':gaps+['Molecular, apparatus, crystal/product and browser visual gates remain pending.'],'evidence_conflicts':deepcopy(I['source_conflicts']),'route_evidence_contexts':routes,'route_evidence_scope_notes':{'all':'These record-ID links are context associations. A TEM image or representative conversion example is not assigned to an exact recipe specimen unless the source states that link.','molecular_crystal':'Species 9 is a separate molecular preparation and diffraction result; it is not a QD structural target.'},'material_evidence_records':{'CdSe':[rid for rid in R if any(s in rid for s in ['cdse','cd-oleate','cd-ratio','cd-timecourse','optical','mechanism'])],'PbSe':[rid for rid in R if any(s in rid for s in ['pbse','pb-oleate','pb-ratio','topse','top-impurities','optical','mechanism'])]},'counts':counts}
save('evans2010.json',review)
save('reader-bindings-proposal.json',{'source_id':SID,'status':'private_unapproved','reader_sha256':sha(O/'evans2010.json'),'original_assets':PUBLIC,'operation_to_reader_item':OPS,'material_to_reader_item':MATS,'stock_to_reader_item':STOCKS,'product_to_reader_item':PROD,'molecular_apparatus_bindings_approved':False,'publication_approved':False})
save('source-item-coverage.json',{'source_units':UNIT,'source_facts':FACTMAP,'canonical_field_map':[{'record_id':r,'json_pointer':p,'reader_item_id':v[0],'reader_fact_id':v[1]['id']} for (r,p),v in FIELD.items()],'measurement_to_reader_item':MEAS,'private_canonical_manifest_sha256':sha(C/'record-manifest.json')})
checks=0;errors=[]
for (rid,ptr),(iid,f) in FIELD.items():assert resolve(R[rid],ptr)==f['canonical_quantity'];checks+=1
for s in SEC:
 for ii in s['items']:
  for l in ii['canonical_links']:resolve(R[l['record_id']],l['json_pointer']);checks+=1
for route,links in routes.items():assert route in R and isinstance(links,list) and all(x in R for x in links);checks+=1
assert set(UNIT)==set(U) and set(FACTMAP)==set(FM)
assert all(i in ITEMS for i in review['characterization_inventory']['reader_item_ids'])
assert len(PUBLIC)==25 and not any('/pages/' in p['public_asset'] for p in PUBLIC)
for x in PUBLIC:assert sha(x['private_path'])==x['sha256'];checks+=1
assert not re.search(r'[A-Z]:[\\/]',json.dumps(review)),'Private local path leaked into reader'
for r in MAN['records']:assert sha(r['path'])==r['sha256'];checks+=1
save('author-validation.json',{'status':'passed_author_pointer_and_contract_checks','checks':checks,'counts':counts,'independent_reader_audit':'pending','mounted_renderer_browser_check':'not_performed','schema_validation':'Canonical records separately validated; current reader contract/pointers verified without writing Site.','routes_contain_only_real_record_ids':True,'characterization_inventory_links_resolve':True,'private_paths_in_reader':False,'whole_page_or_raw_text_public_assets':False})
inputs={str(p):sha(p) for p in [B/'source-extraction-revision-2/source-extraction-freeze.json',B/'source-inventory.json',B/'source-extraction-revision-2/source-facts.json',B/'page-coverage.json',B/'selected-original-assets.json',B/'source-scientific-audit.json',C/'record-manifest.json',C/'source-to-field-coverage.json',SITE/'scripts/build_paper_reviews.py',SITE/'dist/source-evidence.mjs']}
save('reader-manifest.json',{'schema':'mattersyn-private-reader-proposal/1','source_id':SID,'version':2,'author':'/root/norberg2004_extract','created_at':datetime.now(timezone.utc).isoformat(),'status':'private_author_draft_pending_independent_audit','input_hashes':inputs,'outputs':{n:sha(O/n) for n in ['evans2010.json','reader-bindings-proposal.json','source-item-coverage.json','author-validation.json']},'author_script_sha256':sha(__file__),'counts':counts,'published':False})
print(json.dumps(counts));print('READER',sha(O/'evans2010.json'));print('MANIFEST',sha(O/'reader-manifest.json'))
