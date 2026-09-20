"""Academic source reader with exact canonical pointers and existing sample links."""
from pathlib import Path
from copy import deepcopy
import json,hashlib,re,shutil,sys
sys.dont_write_bytecode=True
C=Path(__file__).resolve().parent;J=C.parent;P=C/'v1';O=P/'reader';O.mkdir(exist_ok=True)
assert not(P/'package-freeze.json').exists()
S=Path('[local path redacted]');sys.path.insert(0,str(S/'scripts'))
import build_paper_reviews as consumer
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def norm(x):return re.sub('[^a-z0-9]+','-',str(x).lower()).strip('-')
def esc(x):return str(x).replace('~','~0').replace('/','~1')
def resolve(x,p):
 for k in p.strip('/').split('/')if p else[]:
  k=k.replace('~1','/').replace('~0','~');x=x[int(k)]if isinstance(x,list)else x[k]
 return x
def unique(xs):return list({json.dumps(x,sort_keys=True,ensure_ascii=False):x for x in xs}.values())
def prose(s):
 s=str(s)
 fixes={'Figure1':'Figure 1','Figure2':'Figure 2','Figure3':'Figure 3','Figure4':'Figure 4','Figure5':'Figure 5','Scheme1':'Scheme 1','TableS1':'Table S1','OAm:OA1':'OAm:OA 1','toluene1':'toluene 1','growth25C':'growth at 25 °C','growth50C':'growth at 50 °C','growth100C':'growth at 100 °C','at350K':'at 350 K','350K':'350 K','430K':'430 K','190K':'190 K','row11':'row 11','row10':'row 10','row9':'row 9','row8':'row 8','row7':'row 7','row6':'row 6','row5':'row 5','row4':'row 4','row3':'row 3','row2':'row 2','row1':'row 1','states80':'states 80','above190':'above 190','is80':'is 80','nanocrystals15.6':'nanocrystals 15.6','reference14':'reference 14','labels6.38':'labels 6.38','as(002)':'as (002)','a6.36':'a = 6.36','number(2)':'number (2)','equation(1)':'equation (1)','S1 on S7':'S1 on S7'}
 for a,b in fixes.items():s=s.replace(a,b)
 return re.sub(' +',' ',s).strip()
CM=read(P/'record-manifest.json');OWN=read(P/'source-owner-map.json');CV=read(P/'source-to-field-coverage.json')
def effective(n):
 x=CM['effective_source_files'][n];assert sha(x['path'])==x['sha256'];return read(x['path'])
D=effective('source-facts.json');I=effective('source-inventory.json');T=effective('source-tables.json');A=effective('original-assets-manifest.json');PC=effective('page-coverage.json')
R={x['record_id']:read(x['path'])for x in CM['records']};SID='sasongko2025';PRE='sasongko-2025-'
SECTIONS=[{'id':k,'title':v,'items':[]}for k,v in [('precursors','Precursors'),('protocol','Synthesis protocol'),('structures','Final structures'),('properties','Properties'),('intuition','Chemical intuition'),('sources','Sources and limitations')]]
ITEM={};OBJ={};PTR={};FIELD={};OPS={};MATS={};STOCKS={};PRODS={};UNITS={}
def sec(rid):return OWN['section_by_record'][rid]
def evidence(es):
 result=[]
 for e in es:
  if'document_role'in e:result.append({k:e[k]for k in['source_id','document_role','pdf_page','printed_page','locator']if k in e})
  else:
   m=re.search(r'(MAIN|SI) PDF p\. (\d+) \(printed ([^)]+)\)',e['locator'])
   result.append({'source_id':SID,'document_role':m[1].lower()if m else'main','pdf_page':int(m[2])if m else None,'printed_page':m[3]if m else None,'locator':e['locator']})
 return result
def add(section,id,title,text,es=(),scope='Source context'):
 assert id not in ITEM
 it={'id':id,'title':prose(title),'text':prose(text),'source_audit_unit_ids':[],'source_fact_ids':[],'evidence':evidence(es),'facts':[],'canonical_links':[],'sample_scope':{'label':prose(scope),'canonical_sample_links':[],'same_batch_verified':False},'original_assets':[],'notes':[],'reviewed':False,'training_eligible':False}
 ITEM[id]=it;next(s for s in SECTIONS if s['id']==section)['items'].append(it);return it
OVERVIEW={
 'precursors':('FA and lead precursors, ligands and solvents','The paper supplies a separate FA-oleate preparation and a PbI2/ODE reaction mixture. Whole-stock charges remain distinct from the 0.51 mL FA-stock injection. Technical oleylamine and ODE purities, anhydrous solvent claims and unspecified supplier or grade information retain their reported scope. Prepared FA-oleate is an operational stock identity; no dissolved coordination geometry is supplied.'),
 'protocol':('Hot injection and sequential purification','The source compares three ligand ratios, three washing ratios and three growth temperatures in separate experimental families. Each of the nine condition options preserves the other two source-fixed parameters. They are not a full Cartesian design or nine identified physical batches. The first centrifugation retains the precipitate; the second retains the supernatant. Growth dwell, wash amounts and storage conditions remain unreported.'),
 'structures':('Diffraction, microscopy and reference structures','Source XRD and TEM observations remain linked to their specific comparison specimens. The 25 °C material has reported α-FAPbI3, δ-FAPbI3 and PbI2 features; higher-temperature specimens retain their reported α assignments without inferred phase fractions. The 6.38 Å fringe labeled (002) and the cited 6.36 Å cubic cell remain an unresolved source tension. Cited bulk cells and schematic atomic drawings do not supply measured QD coordinates.'),
 'properties':('Photoluminescence, Raman and thermal aging','Reported lifetimes, size distributions, temperature-dependent PL fits and Raman trends are retained with exact source context. Synthesis temperatures in °C are distinct from optical measurement temperatures in K. PL intensity and its normalized aging trend are not an absolute quantum yield. Raman assignments from cited studies do not establish PbO2 or δ-phase contamination in the current specimen.'),
 'intuition':('Ligand, purification and phase interpretations','The authors relate ligand balance and washing conditions to precursor availability, passivation, dissolution and nonradiative recombination. Their temperature-dependent phase and emission model uses cited bulk reference cells. These explanations remain author interpretations, separate from measured occupancies, atomic coordinates, device performance or independently reproduced mechanisms.'),
 'sources':('Original evidence and unresolved limitations','Nine supplied main pages and eleven matched SI pages passed a distinct source audit. The source inventory retains 48 facts, 157 semantic units, 121 table cells, six additional quantities embedded in table specimen labels, eight figures, one scheme, two equations and 89 references. This private reader still requires independent canonical and presentation review. Selected original crops remain separate from local full-page images and raw source text.'),
}
for k,(title,text)in OVERVIEW.items():add(k,'overview-'+k,title,text)
for rid,r in R.items():
 it=add(sec(rid),'record-'+rid,r['method'],r['method']+'. The record retains its source-defined procedure or observation scope; it does not identify an independent replicate.',scope=rid)
 it['canonical_links']=[{'record_id':rid,'json_pointer':'','relation':'Private canonical record pending independent review.'}]
 it['notes']=[prose(x)for x in r['quality']['conflicts']]
def owner(cat,obj):
 if cat=='facts':k=OWN['fact_owner'][obj['id']]
 elif cat=='materials':k='source-materials'
 elif cat=='stocks':k='fa-oleate-preparation'if obj['id']=='fa-oleate-stock'else'hot-injection'
 elif cat=='protocols':k=OWN['protocol_owner'][obj['id']]
 elif cat=='sample_contexts':k=OWN['sample_owner'][obj['id']]
 elif cat=='figures':k=OWN['figure_owner'][obj['id']][0]
 elif cat=='equations':k=OWN['equation_owner'][obj['id']]
 elif cat=='schemes':k='mechanistic-context'
 else:k='source-context'
 return PRE+k
PANELS={
 'figure-1':'Panel a compares XRD patterns and the six printed diffraction widths; panel b shows normalized steady-state PL; panel c shows time-resolved PL. The OAm:OA ratios are 1:2, 1:3 and 1:4 at 100 °C with 1:20 acetonitrile:toluene washing. Numerical peak positions have not been inferred from the curves.',
 'figure-2':'Panel a compares XRD patterns and all six printed widths; panel b compares time-resolved PL. Washing ratios are 1:1, 1:10 and 1:20 acetonitrile:toluene at fixed 100 °C growth and OAm:OA 1:3. Unreported lifetime components are not reconstructed.',
 'figure-3':'Panels a–c show diffraction, time-resolved PL and normalized PL for growth at 25, 50 and 100 °C. OAm:OA is 1:3 and washing is 1:20 acetonitrile:toluene. Panels d–f are TEM images with 20 nm bars; the 100 °C inset labels d(002) = 6.38 Å. Panels g–i report mean dimensions of 7.6 ± 2.4, 9.5 ± 1.6 and 10.4 ± 1.1 nm, with histogram FWHM values 5.7, 3.7 and 2.7 nm. The ± statistic is undefined. The 25 °C diffraction marks PbI2 and δ-FAPbI3 alongside α-phase assignments.',
 'figure-4':'Panel a shows the absolute PL intensity map with a ×10⁴ scale; panel b shows normalized intensity from 80 to 430 K. The source assigns optical phase boundaries at 140 and 250 K; these are not QD coordinate refinements.',
 'figure-5':'Panels a, b and c show PL peak energy, FWHM and integrated intensity versus temperature. The source discusses boundaries at 140 and 250 K, enhancement through 350 K and decreasing intensity above 350 K. Reported slopes are retained without an independent refit.',
 'figure-s1':'The three photographed washing-waste vials are labeled OAm:OA 1:2, 1:3 and 1:4. The caption attributes the 1:4 appearance to partial QD dissolution. These discarded fractions are distinct from the retained final product supernatant.',
 'figure-s2':'Panel a shows low-frequency Raman curves across 50–300 cm−1 with displayed temperatures from 80 to 190 K. Panel b shows the extracted peak position and FWHM. The prose also states an attempted 80–200 K range; useful acquisition above 190 K is limited by overlap. The source misreference to Figure S1 remains documented.',
 'figure-s3':'Panel a compares a 300 K reference spectrum with spectra at 350 K after 0, 30, 60, 90, 120, 150, 180 and 210 min. Panel b gives normalized intensity versus hours and the printed fit −0.026t + 1. It is not an absolute PL quantum yield.',
}
for cat in['facts','materials','stocks','protocols','sample_contexts','figures','schemes','equations','conflicts','missingness','references']:
 for j,obj in enumerate(D[cat]):
  oid=obj.get('id',str(j));rid=owner(cat,obj);section=sec(rid);title=obj.get('title',obj.get('name',obj.get('label',obj.get('source_context',oid))));es=obj.get('evidence',[])
  if cat=='facts':text=obj['claim']
  elif cat=='materials':text=obj['name']+'. '+obj['scope_note'];section='precursors'
  elif cat=='stocks':
   text=('Prepare the whole FA stock at 60 °C for 30 min under vacuum, then at 135 °C for 2 h under nitrogen. The 0.51 mL transfer is an aliquot; it does not establish the final stock volume or concentration.'if oid=='fa-oleate-stock'else'This is one alternative acetonitrile:toluene washing formulation. Its ratio expresses volume parts; absolute solvent quantities and premixing details are unreported. Select only the formulation paired with the source comparison.');section='precursors'
  elif cat=='protocols':text=title+'. Each stage, retained fraction and condition remains linked to its original source. Missing conditions are not inferred.'
  elif cat=='sample_contexts':text=title+'. '+obj['physical_batch_join']+' Context type: '+obj['kind'].replace('_',' ')+'.'
  elif cat=='figures':text=PANELS[oid]
  elif cat=='schemes':text='The source proposes γ-tetragonal to β-tetragonal evolution at 140 K and an α-cubic regime from 250 K, with PL enhancement through 350 K followed by excessive-expansion effects. Atomic-looking illustrations are conceptual; no particle atomic coordinates are supplied.'
  elif cat=='equations':text=obj['raw_expression']+'. '+prose(obj.get('source_context',''))+'. The expression is retained as printed; no missing equation, amplitudes or fit components are reconstructed.'
  elif cat=='references':text=obj.get('raw_citation',obj.get('citation',str(oid)))+' The cited full paper is not claimed to have been newly supplied or reviewed.';section='sources'
  else:text=obj['description'];section='sources'
  it=add(section,'source-'+cat+'-'+norm(oid),title,text,es,obj.get('sample_scope',obj.get('label',oid)));OBJ[(cat,oid)]=it
  if cat=='facts':it['source_fact_ids']=[oid];it['claim_type']=obj['claim_class'];it['notes']=[prose(c['description'])for c in D['conflicts']if c['id']in obj['conflict_ids']]
  if cat=='figures':it['source_sample_context_ids']=obj['sample_context_ids']
for pr in D['protocols']:
 rid=PRE+OWN['protocol_owner'][pr['id']]
 for op in pr['operations']:
  scope=next(x for x in CV['operations']if x['source_operation_id']==op['id']);text=op['description']+' '+(' '.join(scope['notes']))
  if op['missing_fields']:text+=' Unreported details: '+', '.join(op['missing_fields'])+'.'
  it=add(sec(rid),'operation-'+op['id'],op['action'],text,op['evidence'],pr['id']);OBJ[('operation',op['id'])]=it
for t in T['tables']:
 rid=PRE+OWN['table_owner'][t['id']];es=t.get('evidence')or t['rows'][0]['cells'][0]['evidence']
 it=add(sec(rid),'table-'+t['id'],t['title'],'All original row and column labels, numerical cells and blank cells are retained. Source calculations, reference specimens and current results remain separately scoped.',es,t['id']);OBJ[('table',t['id'])]=it
for b in CV['source_objects']:
 cat={'material':'materials','stock':'stocks','sample_context':'sample_contexts'}.get(b['category'],b['category']);it=OBJ.get((cat,b['source_id']),ITEM['record-'+b['record_id']]);PTR[(b['record_id'],b['pointer'])]=it
 it['canonical_links'].append({'record_id':b['record_id'],'json_pointer':b['pointer'],'relation':'Exact canonical source object or operation.'})
for x in CV['facts']:
 for b in x['canonical_bindings']:PTR[(b['record_id'],b['pointer'])]=OBJ[('facts',x['source_fact_id'])]
for b in CV['table_cells']:PTR[(b['record_id'],b['pointer'])]=OBJ[('table',b['table_id'])]
for x in CV['source_units']:
 u=next(u for u in I['units']if u['id']==x['source_unit_id']);mapped=[]
 for b in x['canonical_bindings']:
  it=PTR.get((b['record_id'],b['pointer']))
  if it is None:it=add('intuition'if u['kind']=='conceptual_figure'else'sources','unit-'+u['id'],u['title'],u['summary'],u['evidence']);PTR[(b['record_id'],b['pointer'])]=it
  it['source_audit_unit_ids'].append(u['id']);mapped.append(it['id'])
 UNITS[u['id']]=list(dict.fromkeys(mapped))
def nearest(rid,p):
 while p:
  if(rid,p)in PTR:return PTR[(rid,p)]
  p=p.rsplit('/',1)[0]
 return ITEM['record-'+rid]
def shown(q):
 if q['value']is not None:return q['value']
 lo,hi=q.get('minimum'),q.get('maximum')
 if lo is not None and hi is not None:return str(lo)+'–'+str(hi)
 if lo is not None:return('> 'if q.get('minimum_exclusive')else'≥ ')+str(lo)
 if hi is not None:return('< 'if q.get('maximum_exclusive')else'≤ ')+str(hi)
 return'Not reported'
def walk(v,p,rid):
 if isinstance(v,dict):
  if{'value','status','evidence'}<=v.keys():
   it=nearest(rid,p);label=p.rsplit('/',1)[-1].replace('_',' ');sample=None
   if p.startswith('/measurements/'):
    m=resolve(R[rid],'/'.join(p.split('/')[:3]));label=m['property'].replace('_',' ');sample=m['sample_id']
   q={'id':rid+'::'+p,'label':label.capitalize(),'value':shown(v),'unit':v.get('unit'),'status':v['status'],'approximate':v.get('approximate',False),'qualifier':' '.join(v.get(k,'')for k in['qualifier','basis','note']),'basis':'exact_canonical_field','evidence':evidence(v['evidence']),'canonical_record_id':rid,'json_pointer':p,'canonical_quantity':deepcopy(v),'presentation_kind':'exact_quantity','training_eligible':False}
   if sample:q['sample_id']=sample
   if isinstance(v['value'],str)and v['value'].startswith('{'):q['value']=json.loads(v['value']);q['presentation_kind']='curated_source_inventory';q['basis']='exact_canonical_structured_source_payload'
   it['facts'].append(q);FIELD[(rid,p)]=(it['id'],q);return
  for k,x in v.items():walk(x,p+'/'+esc(k),rid)
 elif isinstance(v,list):
  for j,x in enumerate(v):walk(x,p+'/'+str(j),rid)
for rid,r in R.items():
 for j,m in enumerate(r['materials']):
  it=OBJ[('materials',m['id'])];it.setdefault('material_contexts',[]).append({'record_id':rid,'json_pointer':f'/materials/{j}',**deepcopy(m),'exact_molecular_asset_binding_approved':False});PTR[(rid,f'/materials/{j}')]=it;MATS[rid+'::'+m['id']]=it['id']
 for j,st in enumerate(r['stocks']):
  it=OBJ[('stocks',st['id'])];it.setdefault('stock_contexts',[]).append({'record_id':rid,'json_pointer':f'/stocks/{j}',**deepcopy(st),'molecular_bindings_approved':False});PTR[(rid,f'/stocks/{j}')]=it;STOCKS[rid+'::'+st['id']]=it['id']
 for j,op in enumerate(r['operations']):
  it=OBJ[('operation',op['id'])];it.setdefault('operation_contexts',[]).append({'record_id':rid,'json_pointer':f'/operations/{j}',**deepcopy(op),'apparatus_binding_approved':False});PTR[(rid,f'/operations/{j}')]=it;OPS[rid+'::'+op['id']]=it['id']
 for j,p in enumerate(r['products']):
  it=OBJ.get(('sample_contexts',p['sample_id']),ITEM['record-'+rid]);it.setdefault('product_contexts',[]).append({'record_id':rid,'json_pointer':f'/products/{j}',**deepcopy(p),'atomic_asset_binding_approved':False});PTR[(rid,f'/products/{j}')]=it;PRODS[rid+'::'+p['sample_id']]=it['id']
 walk(r,'',rid)
for it in ITEM.values():
 it['canonical_links']=unique(it['canonical_links']);it['source_audit_unit_ids']=list(dict.fromkeys(it['source_audit_unit_ids']))
 for q in it['facts']:
  if q.get('sample_id'):
   j=next(j for j,p in enumerate(R[q['canonical_record_id']]['products'])if p['sample_id']==q['sample_id'])
   it['sample_scope']['canonical_sample_links'].append({'record_id':q['canonical_record_id'],'json_pointer':f'/products/{j}','sample_id':q['sample_id'],'relation':'Source context; no new physical-aliquot association.'})
 it['sample_scope']['canonical_sample_links']=unique(it['sample_scope']['canonical_sample_links'])
def samplelink(sid):
 rid=PRE+OWN['sample_owner'][sid];j=next(j for j,p in enumerate(R[rid]['products'])if p['sample_id']==sid)
 return{'record_id':rid,'json_pointer':f'/products/{j}','sample_id':sid,'relation':'Existing named source context, not an exact cross-technique aliquot match.'}
for s in D['sample_contexts']:OBJ[('sample_contexts',s['id'])]['sample_scope']['canonical_sample_links'].append(samplelink(s['id']))
for fig in D['figures']:
 OBJ[('figures',fig['id'])]['sample_scope']['canonical_sample_links']+=list(map(samplelink,fig['sample_context_ids']))
GROUP={k:[]for k in['figures','tables','equations','schemes','source_notes']};PUBLIC=[]
extras={'materials':('source-materials','Purchased reagent statement'),'fa-preparation':('fa-oleate-preparation','FA-oleate preparation'),'qd-preparation':('hot-injection','Hot-injection preparation'),'qd-workup':('hot-injection','Sequential purification'),'characterization-equation':('trpl','Characterization and average-lifetime equation'),'raman-context':('raman-results','Raman measurement scope')}
for a in A['assets']:
 oid=a['object_id'];assert not a['contains_complete_source_page']and sha(a['path'])==a['sha256']
 if oid.startswith('figure-'):it=OBJ[('figures',oid)];group='figures';title=it['title']
 elif oid.startswith('scheme-'):it=OBJ[('schemes',oid)];group='schemes';title=it['title']
 elif oid=='table-s1':it=OBJ[('table',oid)];group='tables';title='Table S1: phase-transition literature comparison'
 elif oid=='graphical-abstract':it=ITEM['unit-'+SID+'-unit-graphical-abstract'];group='source_notes';title='Graphical abstract'
 else:k,title=extras[oid];it=ITEM['record-'+PRE+k];group='source_notes'
 public='assets/figures/'+SID+'/'+Path(a['path']).name;links=list(map(samplelink,a['sample_context_ids']))
 out={'id':a['id'],'label':prose(title),'caption_paraphrase':it['text'],'document_role':a['document_role'],'page':a['pdf_page'],'printed_page':a['printed_page'],'sample_scope':{'label':' / '.join(a['sample_context_ids']),'canonical_sample_links':links,'same_batch_verified':False},'sample_links':sorted({x['record_id']for x in links}),'sample_linkage':'Original source context only; no exact structure–recipe pair.','public_asset':public,'public_asset_sha256':a['sha256'],'asset_provenance':{'source_sha256':a['source_sha256'],'source_pdf_page':a['pdf_page'],'crop_normalized':a['crop_box_normalized'],'source_render_dpi':a['render_dpi'],'renderer':a['renderer'],'pixel_dimensions':a['pixel_dimensions'],'transformation':'Selected original crop; no full page or reconstructed scientific image.'},'source_locators':[e['locator']for e in a['evidence']],'notes':it['notes'],'reader_render_verified':False,'reviewed':False,'training_eligible':False}
 if oid=='table-s1':out['source_rows']=deepcopy(next(t['rows']for t in T['tables']if t['id']=='table-s1'))
 GROUP[group].append(out);it['original_assets'].append({'id':a['id'],'label':'Open original '+prose(title),'public_asset':public,'public_asset_sha256':a['sha256']});PUBLIC.append({'id':a['id'],'private_path':a['path'],'public_asset':public,'sha256':a['sha256'],'selected_original_only':True,'publication_approved':False})
docs=[]
for role in['main','si']:
 pages=[p for p in PC['pages']if p['document_role']==role]
 docs.append({'role':role,'filename':'10.1021_acs.jpcc.5c05144'+('_si_1'if role=='si'else'')+'.pdf','sha256':next(a['source_sha256']for a in A['assets']if a['document_role']==role),'page_count':len(pages),'pages':[{'page':p['pdf_page'],'printed_page':15341+p['pdf_page']if role=='main'else'S'+str(p['pdf_page']),'text_read':p['text_read'],'visual_review':p['visual_review'],'review_basis':'Source author coverage and distinct passed source audit; this converter did not repeat the full source audit.','sections':[p.get('actual_reading_scope',p.get('reading_scope','Audited source page'))]}for p in pages]})
counts={'reader_items':len(ITEM),'typed_reader_fields':len(FIELD),'canonical_records':len(R),'source_units':len(UNITS),'source_facts':len(D['facts']),'table_cells':121,'additional_table_label_quantities':6,'operation_instances':len(OPS),'source_operations':21,'material_slots':len(MATS),'stock_slots':len(STOCKS),'sample_context_slots':len(PRODS),'measurements':sum(len(r['measurements'])for r in R.values()),'selected_original_assets':len(PUBLIC),'main_pages':9,'si_pages':11,'full_page_public_assets':0,'training_tasks':0}
rv={'schema_version':'1.0','paper_id':SID,'doi':D['doi'],'title':D['title'],'paper':{'authors':D['authors'],'year':2025,'journal':'The Journal of Physical Chemistry C','volume':129,'pages':'15342–15350'},'source_group':SID,'review_scope':'supplied_main_and_matched_si','documents':docs,'supporting_information':{'status':'matched_local_source_audit_passed_canonical_review_pending','matched_local_si_count':1,'pdf_pages':11,'scope':'Complete supplied experimental methods, original figures, Table S1 and references; no current QD coordinate file.'},'coverage_status':'private_author_reader_draft','independent_audit':'Source revision 2 passed distinct source audit; canonical/reader review is pending.','publication_status':'Private unapproved draft','source_review_promoted':False,'training_eligible':False,'recipe_inventory':[{'id':rid,'label':r['title'],'record_ids':[rid],'record_type':r['record_type'],'status':'private_author_draft_pending_independent_review','scope':'Procedure or source comparison, not an independent physical replicate.','gaps':r['quality']['missing_fields']}for rid,r in R.items()],'characterization_inventory':{'reader_item_ids':[i['id']for s in SECTIONS if s['id']in['structures','properties']for i in s['items']]},'chemical_intuition':{'reader_item_ids':[i['id']for s in SECTIONS if s['id']=='intuition'for i in s['items']]},'reader_contract':{'version':'1.0','section_ids':[s['id']for s in SECTIONS]},'reader_sections':SECTIONS,**GROUP,'remaining_gaps':[prose(x['description'])for x in D['missingness']],'evidence_conflicts':[{**deepcopy(x),'description':prose(x['description'])}for x in D['conflicts']],'route_evidence_contexts':{PRE+'hot-injection':[PRE+k for k in['ligand-results','wash-results','growth-results','temperature-results','raman-results','aging-results']]},'route_evidence_scope_notes':{'all':'Paired experimental families and source comparisons, not exact matching aliquots or a full Cartesian matrix.','reference_cells':'Cited bulk lattice parameters and conceptual drawings do not establish measured QD coordinates.'},'presentation_gates':{'molecules':False,'apparatus':False,'products':False,'browser_render':False,'publication':False},'counts':counts}
save(SID+'.json',rv)
save('reader-bindings-proposal.json',{'status':'private_unapproved_draft','source_id':SID,'reader_sha256':sha(O/(SID+'.json')),'original_assets':PUBLIC,'operation_to_reader_item':OPS,'material_to_reader_item':MATS,'stock_to_reader_item':STOCKS,'product_to_reader_item':PRODS,'binding_approved':False})
save('source-item-coverage.json',{'source_units':UNITS,'canonical_field_map':[{'record_id':rid,'json_pointer':p,'reader_item_id':iid,'reader_fact_id':q['id']}for(rid,p),(iid,q)in FIELD.items()],'source_facts':[{'source_fact_id':f['source_fact_id'],'bindings':[{**b,'reader_item_id':FIELD[(b['record_id'],b['pointer'])][0],'reader_fact_id':FIELD[(b['record_id'],b['pointer'])][1]['id']}for b in f['canonical_bindings']]}for f in CV['facts']],'table_cells':[{**b,'reader_item_id':FIELD[(b['record_id'],b['pointer'])][0],'reader_fact_id':FIELD[(b['record_id'],b['pointer'])][1]['id']}for b in CV['table_cells']]})
checks=[]
def ck(n,v):checks.append({'check':n,'passed':bool(v)});assert v,n
for(rid,p),(iid,q)in FIELD.items():ck('Exact canonical quantity '+rid+p,resolve(R[rid],p)==q['canonical_quantity'])
for it in ITEM.values():
 for b in it['canonical_links']:ck(it['id']+' canonical link',resolve(R[b['record_id']],b['json_pointer'])is not None)
 for b in it['sample_scope']['canonical_sample_links']:ck(it['id']+' sample '+b['sample_id'],resolve(R[b['record_id']],b['json_pointer'])['sample_id']==b['sample_id'])
for s in D['sample_contexts']:ck('Named sample link '+s['id'],any(b['sample_id']==s['id']for b in OBJ[('sample_contexts',s['id'])]['sample_scope']['canonical_sample_links']))
ck('157 original source units mapped',set(UNITS)=={u['id']for u in I['units']}and len(UNITS)==157)
ck('17 selected assets',len(PUBLIC)==17)
fixture=P/'isolated-reader-fixture';(fixture/'data/records').mkdir(parents=True,exist_ok=True);(fixture/'dist').mkdir(exist_ok=True)
for x in CM['records']:shutil.copyfile(x['path'],fixture/'data/records'/Path(x['path']).name)
for a in PUBLIC:
 target=fixture/'dist'/a['public_asset'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a['private_path'],target);ck('Exact original crop '+a['id'],sha(target)==a['sha256'])
old=consumer.ROOT
try:consumer.ROOT=fixture;errors=consumer.validate(rv)
finally:consumer.ROOT=old
ck('Actual current reader consumer',not errors)
save('reader-author-validation.json',{'status':'passed_author_checks_pending_distinct_review','checks':checks,'check_count':len(checks),'actual_reader_consumer_errors':errors,'consumer_sha256':sha(S/'scripts/build_paper_reviews.py'),'fixture':str(fixture),'counts':counts,'actual_browser':False,'independent_scientific_approval':False,'publication_approved':False})
(O/'display-proof.md').write_text('\n\n'.join('### '+i['id']+' — '+i['title']+'\n\n'+i['text']for sec in SECTIONS for i in sec['items'])+'\n',encoding='utf-8')
print(json.dumps({'status':'private_reader_valid','checks':len(checks),**counts}))
