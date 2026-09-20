"""Five academic sections plus sources; private Sommer reader with lossless typed pointers."""
from pathlib import Path
from datetime import datetime,timezone
from copy import deepcopy
import json,hashlib,re
P=Path(__file__).resolve().parent;C=P/'canonical-proposal/v1';O=P/'public-review-proposal/v1';O.mkdir(parents=True,exist_ok=True)
assert not(C/'package-manifest.json').exists(),'Frozen proposal requires a new preserved revision.'
S=Path('[local path redacted]');SID='sommer2020';PRE='sommer-2020-'
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,x):(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def norm(x):return re.sub('[^a-z0-9]+','-',str(x).lower()).strip('-')
def esc(x):return str(x).replace('~','~0').replace('/','~1')
def resolve(x,p):
 for t in p.strip('/').split('/')if p else[]:x=x[int(t)]if isinstance(x,list)else x[t.replace('~1','/').replace('~0','~')]
 return x
def uniq(x):return list({json.dumps(a,ensure_ascii=False,sort_keys=True):a for a in x}.values())
def prose(x):return str(x).replace('degC','°C').replace('angstrom','Å').replace('wt%','wt%')
D=read(P/'source-facts.json');T=read(P/'source-tables.json');I=read(P/'source-inventory.json');A=read(P/'original-assets-manifest.json');PC=read(P/'page-coverage.json');FR=read(P/'package-freeze.json');CM=read(C/'record-manifest.json');COV=read(C/'source-to-field-coverage.json')
PASSED=bool(CM['independent_source_audit_sha256']);AP=Path(CM['independent_source_audit_path'])if PASSED else None
R={x['record_id']:read(x['path'])for x in CM['records']};U={u['id']:u for u in I['inventory_units']};FM={x['id']:x for x in D['facts']};TM={t['id']:t for t in T['tables']};UB={u['source_unit_id']:u['canonical_bindings']for u in COV['source_units']}
for x in CM['records']:assert sha(x['path'])==x['sha256']
SECTIONS=[{'id':i,'title':t,'items':[]}for i,t in [('precursors','Precursors'),('protocol','Synthesis protocol'),('structures','Final structures'),('properties','Properties'),('intuition','Chemical intuition'),('sources','Sources and limitations')]]
ITEM={};UNIT={};FIELD={};OPS={};MAT={};STOCK={};PRODUCT={};MEAS={}
def evidence(es):
 out=[]
 for e in es:
  if 'document_role'in e:out.append({k:e[k]for k in ['source_id','document_role','pdf_page','printed_page','locator']});continue
  m=re.search(r'(MAIN|SI) PDF p\. (\d+) \(printed ([^)]+)\)',e['locator']);out.append({'source_id':SID,'document_role':m[1].lower()if m else'main','pdf_page':int(m[2])if m else None,'printed_page':m[3]if m else None,'locator':e['locator']})
 return out
def section_for_record(rid):
 k=rid.removeprefix(PRE)
 if k in['source-materials','precursor-structures','pdf-procedure']:return'precursors'
 if k in['optical-procedure','optical-results']:return'properties'
 if k in['formation-model','insitu-refinement']:return'intuition'
 if k in['phase-size-results','lab-xrd-procedure','synchrotron-procedure','microscopy-procedure']:return'structures'
 if k=='source-context':return'sources'
 return'protocol'
def add(section,i,title,text,es=(),uid=None,scope='source_context'):
 assert i not in ITEM,i
 item={'id':i,'title':prose(title),'text':prose(text),'source_audit_unit_ids':[uid]if uid else[],'source_fact_ids':[],'evidence':evidence(es),'facts':[],'canonical_links':[],'sample_scope':{'label':scope,'canonical_sample_links':[],'same_batch_verified':False},'original_assets':[],'notes':[],'reviewed':False,'training_eligible':False}
 next(s for s in SECTIONS if s['id']==section)['items'].append(item);ITEM[i]=item
 if uid:UNIT.setdefault(uid,[]).append(i)
 return item
OVERVIEWS={
'precursors':('Distinct formulations and precursor structures','The laboratory microwave/autoclave feed uses nitrate hydrates in demineralized water. The in situ nitrate experiments use a separate concentrated stock, while I15/I16 start from ZnO and Al(OH)3 in Millipore water. D1-D4 are precursor-solution scattering contexts. Water grades, nitrate hydration, ethanol grades, whole-stock charges and reaction aliquots remain distinct. The PDF interpretations identify coordination motifs without resolving every protonation state or solution species.'),
'protocol':('Three laboratory routes and separate in situ experiments','Microwave, supercritical-flow and autoclave syntheses explore different thermal histories and metal-to-hydroxide conditions. Their products undergo the common powder workup separately. The full Table 1 matrix and both microwave heating profiles are retained, including conflicting total times, the S2 temperature discrepancy and the long-autoclave duration difference. In situ reaction monitoring and D-series scattering remain separately identified procedures.'),
'structures':('Phase, size and morphology with sample boundaries','Diffraction follows spinel formation and the competing ZnO and AlOOH phases. The original figures and typed results retain named sample assignments, phase fractions, parenthetic uncertainties and the distinction between diffraction-derived crystallite sizes and TEM observations. Positions and occupancies in the laboratory refinements were fixed to literature values; no complete measured product-coordinate file is supplied.'),
'properties':('Optical comparison without invented precision','Diffuse reflectance compares M2, A2 and S1. The source associates their different apparent band gaps with size and structural disorder, while acknowledging that these effects remain entangled. The original optical expression and plotted curves are retained literally. Unlabeled bar heights do not become precise numeric band-gap labels, and cited prior ranges stay separate from current measurements.'),
'intuition':('Coordination and impurity-mediated formation','The authors propose that aluminum dimers can connect with tetrahedrally coordinated zinc to nucleate spinel. At high M/OH, zinc recoordination may delay this process and favor AlOOH; at low M/OH, ZnO dissolution supplies zinc and may leave residual ZnO. Heating history changes impurity formation and consumption. These explanations are source interpretations, with the contradictory conclusion wording preserved.'),
'sources':('Supplied-main coverage and unresolved SI','The complete 11-page main article and its selected original graphics have been read. The declared Supporting Information PDF was not found in the bounded local source-folder and cached-text searches. References are bibliographic pointers, not newly read papers. All unresolved source conflicts and absent operational, structural and sample-linkage details remain explicit.')}
for sec,(title,text)in OVERVIEWS.items():add(sec,'overview-'+sec,title,text,scope='academic overview')
FIG_PROSE={
'graphical-abstract':'The original graphical abstract summarizes the proposed coordination-dependent nucleation pathways. It contrasts octahedral zinc at high metal-to-hydroxide ratio with a ZnO reservoir at low ratio. The cartoon is an author mechanism, not measured molecular geometry or a separate synthesis specimen.',
'figure-1':'The three literature structure drawings show ZnAl2O4 spinel, ZnO and AlOOH. Orange and green polyhedra represent aluminum and zinc coordination; hydrogen is shown as white spheres. These reference depictions do not supply newly measured coordinates for the current samples.',
'figure-2':'The D3 zinc-nitrate solution at room temperature is fitted with octahedral zinc and nitrate contributions. The original PDF, model and reference-cluster curves remain intact. Broad longer-distance features and unknown protonation do not identify one fully resolved molecular species.',
'figure-3':'The green D1 mixed-solution PDF is compared with the gray sum of the separate D3 zinc and D4 aluminum precursor signals, normalized by time. Similarity supports the authors’ precursor interpretation; it is not proof of an isolated molecular compound or a new product crystal.',
'figure-4':'Panel a fits the basic D2 solution with crystalline ZnO. Panel b compares the residual with the aluminum-only D4 solution according to the caption and prose, while its native legend prints 1:0:0. The discrepancy remains visible and explicitly recorded; the figure is not relabeled.',
'figure-5':'This proposed formation pathway connects aluminum dimers to tetrahedral zinc. At high M/OH, zinc must recoordinate from an octahedral precursor, while at low M/OH it is released from ZnO. The drawing expresses a mechanistic interpretation and leaves protonation, rates and exact intermediates unresolved.',
'figure-6':'Panel a tracks I1 and I2 at 350 and 400 °C before an increase to 430 °C. The prose and caption say approximately 34 min, whereas the native axes say Time(s). Panel b shows I9-I11 at 350, 400 and 430 °C. Phase fractions remain fit-derived results with this unresolved time-unit discrepancy.',
'figure-7':'The two panels compare refined spinel crystallite-size trajectories for I4-I6 and I9-I11, respectively, at 350, 400 and 430 °C. The curves illustrate differences associated with impurity formation and dissolution. No extra exact trajectory coordinates or new growth-rate law are inferred from the plot.',
'figure-8':'Original diffraction patterns compare M1, M2 and M3 at Zn:Al:OH ratios 1:2:6.25, 1:2:7.09 and 1:2:8.34, with separate literature reference patterns for spinel, AlOOH and ZnO. Phase assignments and reported fractions remain sample-specific.',
'figure-9':'The M2 Rietveld plot includes a close-up of the small peak attributed to AlOOH. Although the caption calls the product phase-pure, the text reports this trace impurity below reliable quantification. The unresolved disorder near 15° is not converted into a qualified atomic model.',
'figure-10':'AlOOH fractions are plotted against dwell time for M4-M6 at 250 °C and M2/M7 at 280 °C. Dashed lines are guides to the eye. The printed values are retained in the linked source facts; graph-only intermediate values are not assigned invented precision.',
'figure-11':'The autoclave comparison retains all original points and its legend. Caption colors disagree with the textual impurity assignments, and the A1/A4 and A2/A5 marker identities conflict with Table 1 durations. Both discrepancies remain explicit; points, labels and sample outcomes are not silently exchanged.',
'figure-12':'Panels a, b and c show S1, M2 and A2 with scale bars of 10 nm, 30 nm and 0.25 µm. Their distributions are qualitatively different. Panel d is a spherical-harmonic shape inferred from the S1 Rietveld model, not a measured set of atomic coordinates.',
'figure-13':'The optical comparison shows M2, A2 and S1 and an inset of extracted band gaps. The bars have no printed numerical labels, so the reader preserves the original plot and qualitative comparison without digitizing exact gap values. The cited theoretical and earlier experimental ranges remain separate from these current samples.'}
for uid,u in U.items():
 kind=u['kind'];obj=resolve(D if u['path']=='source-facts.json'else T,u['json_pointer']);oid=u['source_object_id'];bs=UB[uid];sec=section_for_record(bs[0]['record_id']);title=obj.get('title',obj.get('name',oid.replace('-',' ').capitalize()));scope=obj.get('sample_scope',oid);text=title
 if kind=='fact':
  title=obj['title'];text=obj['claim']
  if obj['claim_class']in['author_interpretation','author_assumption','cited_context','reported_model']:sec='intuition'if not oid.endswith('optical-literature')else'properties'
  if oid.endswith(('d3-peaks','d3-fit','d3-solution','d4-solution','d2-pdf','d2-size')):sec='precursors'
  if oid.endswith(('acs-ramp-assumption','heating-background')):sec='protocol'
 elif kind=='material':sec='precursors';text=obj['name']+'. '+obj['scope_note']
 elif kind=='stock':sec='precursors';text=obj['name']+'. '+obj['notes']+' The preparation and later aliquot use remain distinct; the full source formulation is not assigned as an additional reaction charge.'
 elif kind=='sample_context':
  title=obj.get('name',obj['id']+' · source-defined context');text=obj.get('phase_assignment_note',obj.get('name','Named source context')).rstrip('.')+'. This context is not an independently verified physical batch or an exact cross-technique sample pair.'
 elif kind=='figure':text=FIG_PROSE[oid];scope='/'.join(obj['sample_ids']);sec='intuition'if oid in['graphical-abstract','figure-1','figure-5']else'precursors'if oid in['figure-2','figure-3','figure-4']else'properties'if oid=='figure-13'else'structures'
 elif kind=='equation':title=obj['source_label']+' · '+oid.replace('-',' ');text=obj['expression']+'. '+obj.get('notes','The literal source profile is kept distinct from Table 1 total times.');scope='/'.join(obj.get('sample_ids',[]));sec='protocol'if oid.startswith('heating')else'properties'if oid=='kubelka-munk'else'intuition'
 elif kind=='reference':sec='sources';title='Reference '+str(obj['number']);text=obj['citation_as_extracted']+' This is a bibliographic pointer from the main article; its cited full text was not independently read.'
 elif kind in['conflict','gap']:sec='sources';text=obj['description'];scope='source limitation'
 elif kind=='protocol':text=obj['title']+'. This scope retains '+str(len(obj['operations']))+(' action'if len(obj['operations'])==1 else' separate actions')+', its material flow and missing fields. Alternative specimens and methods are not pooled into one reaction.'
 elif kind=='operation':title=obj['action'];text=obj['action']+'. '+obj.get('condition_scope_note','')+' Missing fields: '+(', '.join(obj['missing_fields'])or'none additionally identified')+'.';scope='source operation'
 elif kind=='table':title=obj['title'];text='The complete table contains 37 named contexts and 222 printed body cells, including the sample-label column. M, S and A denote laboratory reactor series; I denotes in situ experiments and D denotes precursor solutions. Day-valued entries, room-temperature text, approximate SCF residence times and the 0–40 min in situ intervals retain their printed meanings. D-series 3.3 min entries are not invented synthesis-heating times.';sec='protocol'
 elif kind=='table_row':
  title='Table 1 · '+obj['row_label'];vals={c['column']:c['raw_text']+(' '+c['unit']if c['unit']and c['unit']not in['ratio_parts','day']else'')for c in obj['cells']};text='The '+obj['row_label']+' row reports NaOH '+vals['C_NaOH']+', temperature '+vals['T_rxn']+', Zn:Al:OH '+vals['Zn_Al_OH']+', total time '+vals['t_rxn']+' and dwell '+vals['t_dwell']+'. These are source conditions or observation intervals, not independent product-performance labels.';scope=obj['sample_id'];sec='protocol'
 elif kind=='footnote':text=obj['text'];sec='protocol'
 else:raise AssertionError(kind)
 item=add(sec,'source-'+norm(uid),title,text,u.get('evidence',obj.get('evidence',[])),uid,scope)
 item['canonical_links']=[{'record_id':b['record_id'],'json_pointer':b['pointer'],'relation':'Exact canonical field for this source unit; no new physical sample join.'}for b in bs]
 if kind=='fact':item['claim_type']=obj['claim_class'];item['notes']+=[next(c['description']for c in D['conflicts']if c['id']==cid)for cid in obj['conflict_ids']]
for rid,r in R.items():
 item=add(section_for_record(rid),'record-'+rid,r['title'].split(' · ',1)[1],r['method']+'. This record groups a source-defined preparation, measurement or interpretation. It does not add an independent physical batch.');item['canonical_links']=[{'record_id':rid,'json_pointer':'','relation':'Private canonical proposal; independent approval remains pending.'}];item['notes']+=r['quality']['missing_fields']+r['quality']['conflicts']
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
OP_PROSE={
'mw-dissolve':'Dissolve 1.425 g zinc nitrate hexahydrate and 3.596 g aluminum nitrate nonahydrate in 20 mL demineralized water. The charge gives Zn:Al 1:2. The water charge is not a measured final solution volume, and the mixing duration is unreported.',
'mw-base':'Prepare separate NaOH-adjusted versions of the mixed-nitrate feed at final concentrations of 1.5, 1.7 and 2.0 M. These are alternative formulations, not one combined charge. Exact NaOH masses and final mixture volumes are absent.',
'mw-load':'Transfer a 10 mL aliquot to an 80 mL thick-walled quartz vessel in the Anton Paar Multiwave 3000. The pressure and temperature sensors sit inside a sapphire immersion tube.',
'mw-heat':'Use profile 2 only for M4-M6 and profile 1 for M1-M3 and M7-M9, followed by each Table 1 dwell. The reaction pressure is approximately 40-60 bar. Both printed ramp sequences and the separately reported total times remain visible because they do not reconcile directly; unavailable SI Figure S30 contains further settings.',
'scf-feed':'Supply the precursor and solvent streams at 5 and 14.5 mL/min, respectively. The source gives 0.18 M OH and Zn:Al:OH 1:2:7 but does not reproduce a complete feed formulation or reactor design from the cited apparatus papers.',
'scf-react':'The flow reactor operates at 250 bar. Table 1 and the results identify S1 at 450 °C and S2 at 380 °C, whereas the methods say 450 °C for each synthesis. Both statements remain explicit, together with the approximate one-minute table time and zero dwell.',
'acs-load':'Place 10 mL of a source-defined laboratory feed in a 20.0 mL Teflon-lined stainless-steel autoclave. The source does not state the autoclave pressure.',
'acs-heat':'Heat the separately prepared autoclave samples at 220 °C. Short experiments last one day. The methods call the long treatment 2.5 weeks, while the table and results give 17 days. The 45-60 min approach to the set point is an author assumption based on prior studies, not a measured trace for each current sample.',
'lab-separate':'Process each microwave, SCF or autoclave powder separately. Centrifuge and remove supernatant until the solution appears colorless, retaining the powder. The rotor speed and duration are not reported; products from different reactors are not pooled.',
'lab-wash':'Wash each retained powder three times with demineralized water and once with 96% ethanol. Wash volumes and further centrifuge settings are absent. The washed powder, rather than the wash supernatants, proceeds to drying.',
'lab-dry':'Dry the retained powder in a Thermo Scientific Heraeus vacuum oven at 50 °C for 4 h. Vacuum pressure and isolated yield are unreported.',
'insitu-stock':'Prepare a 30.0 mL water-based solution containing 8.552 g zinc nitrate hexahydrate and 21.572 g aluminum nitrate nonahydrate. This 1:2 Zn:Al stock differs from the microwave/autoclave feed; its water grade is unspecified.',
'insitu-mix':'Combine 1.00 mL of varying NaOH(aq) with 1.00 mL of the concentrated nitrate stock. The mixed reaction has 0.480 M Zn and 0.960 M Al. These final metal concentrations do not describe the NaOH stock. The table NaOH basis and the zero-base rows’ diluent remain unresolved.',
'insitu-stir-load':'Vigorously stir the nitrate-based mixture for about 5 min, then inject its white slurry into a single-crystal sapphire capillary with 0.6 mm inner and 1.1 mm outer diameter.',
'insitu-heat':'Heat each nitrate-based experiment under its own Table 1 conditions while following diffraction. I1/I2 receive the separately reported increase to 430 °C after about 34 min; the corresponding figure axes instead say seconds. The 0-40 min table entries are observation intervals, not one mandatory fixed endpoint for every experiment.',
'oxide-slurry':'For I15/I16, mix 0.8141 g nanosized ZnO with 1.561 g Al(OH)3 in Millipore water and stir for 4 h. The stated metal concentrations are 0.5 M Zn and 1 M Al. The total water volume is not supplied.',
'oxide-load':'Inject the oxide/hydroxide suspension into the sapphire capillary. This branch follows its own four-hour stirring treatment; the nitrate branch’s five-minute stirring is not copied into it. Injected suspension volume is unreported.',
'oxide-heat':'Follow the separate oxide-feed experiments at 425 °C for I15 and 400 °C for I16. The reported conversion differs between them, but exact completion times and isolated yields are not supplied.',
'insitu-fit':'Use sequential Fullprof fits to follow phase fractions and size, with the stated constrained antisite/interstitial model. ADPs are allowed to vary and become high under the limited-q, noisy, high-temperature conditions. Detailed refined values remain in unavailable Table S7; this procedure does not supply a qualified atomic structure.',
'pdf-solutions':'Keep the four precursor solutions separate: D3 is zinc-only, D4 aluminum-only, D1 their mixture without base and D2 the base-added mixture. Their exact stated ratios and available concentrations are retained. D-series table times describe scattering contexts and do not establish a heated synthesis protocol.',
'pdf-acquire':'Collect total scattering at PETRA III P02.1 and matching deionized-water background in the same capillary type and at the same temperatures. Integrate with Fit2D and obtain PDFs using PDFgetX3; LaB6 NIST 660b provides the instrumental damping reference.',
'pdf-reduce-fit':'Fit the D3 cluster and crystalline D2 ZnO within their distinct model scopes. The source specifies fixed literature ADPs, a spheroidal size model for D2 and a separate reciprocal-space refinement. Missing SI parameter tables prevent treating these descriptions as complete recovered coordinate sets.',
'lab-xrd-acquire':'Measure laboratory powders with Rigaku SmartLab Cu Kalpha1 diffraction in Bragg-Brentano geometry. LaB6 NIST 660A provides the resolution reference; scan interval, step and exposure are not reproduced in the main.',
'lab-xrd-fit':'Use Fullprof with the stated background, peak-shape and spherical-harmonic size models. Laboratory-sample atomic positions and occupancies stay fixed to literature values, ADPs are refined by atom type and microstrain is omitted. Refined phase fractions and sizes retain their sample-specific scope.',
'synchrotron-load-acquire':'For M1-M3, M7, S1 and A1-A2, pack rotating 0.3 mm glass capillaries and measure at SPring-8 BL44B2 in Debye-Scherrer geometry. The wavelength is 0.50054(6) Å, calibrated with CeO2. Packing mass and exposure are unreported.',
'synchrotron-fit':'Refine the selected synchrotron patterns in MAUD with four polynomial functions, two background features for small-angle scattering/glass and three spherical-harmonic size functions. The source retains literature-fixed positions and occupancies; the full refinement outputs are not available locally.',
'microscopy-disperse':'Disperse dried powders in 99% ethanol and sonicate. The source does not specify the dispersion concentration or sonication settings, and this ethanol grade is distinct from the 96% workup solvent.',
'microscopy-deposit':'Place individual drops on 200-mesh copper grids with Formvar/carbon support and dry in ambient atmosphere. Drop volume and unique per-grid batch identifiers are absent.',
'microscopy-acquire':'Use the TALOS F200A configuration for bright-field TEM, HAADF-STEM and Super-X EDS acquisition. Esprit controls the EDS collection and Hyperspy plots the results. The instrument model name is not substituted for an explicit accelerating voltage; detailed SI maps remain unavailable.',
'optical-acquire':'Measure M2, A2 and S1 diffuse reflectance at room temperature against BaSO4 using the Shimadzu UV-3101 PC over 200-2500 nm. A separate quantitative optical specimen-preparation procedure is not given.',
'optical-transform':'Apply the literal printed expression and the authors’ linear Tauc treatment. The source uses x=1/2 and refers to unavailable Figure S31. Preserve that convention and the original curves without correcting the formula or deriving exact numbers from unlabeled inset bars.'}
for rid,r in R.items():
 for j,op in enumerate(r['operations']):
  ptr=f'/operations/{j}';uid='operation:'+op['id'];item=ITEM[UNIT[uid][0]];item['text']=op['description'];names={m['id']:m['name']for m in r['materials']}|{s['id']:s['name']for s in r['stocks']}|{s['id']:s['name']for s in r['material_states']}
  item['text']=OP_PROSE[op['id']]
  item['operation_context']={'record_id':rid,'operation_id':op['id'],'json_pointer':ptr,**{k:deepcopy(op[k])for k in['stage','branch','depends_on','environment','inputs','outputs','retained_fraction','endpoint']},'material_flow_labels':{k:names[k]for k in op['inputs']+op['outputs']},'diagram_binding_status':'pending_independent_visual_binding'}
  item['notes']+=['Inputs: '+', '.join(names[k]for k in op['inputs'])+'.','Outputs: '+', '.join(names[k]for k in op['outputs'])+'.'];OPS[rid+'::'+op['id']]=item['id']
  if op['retained_fraction']:item['notes'].append('Retained fraction: '+names[op['retained_fraction']]+'.')
  for k,q in op['parameters'].items():attach(item,rid,ptr+'/parameters/'+esc(k),k.replace('_',' ').capitalize(),q)
  for k in['environment','endpoint']:attach(item,rid,ptr+'/'+k,k.capitalize(),op[k])
 for j,m in enumerate(r['materials']):
  item=ITEM[UNIT['material:'+m['id']][0]];ptr=f'/materials/{j}';item.setdefault('material_identities',[]).append({'source_material_id':m['id'],'name':m['name'],'formula':m['formula'],'role':m['role'],'stage':m['stage'],'canonical_record_id':rid,'json_pointer':ptr,'exact_molecular_asset_binding_approved':False});item['notes']+=m['notes'];MAT[rid+'::'+m['id']]=item['id']
  for k,q in m['quantities'].items():attach(item,rid,ptr+'/quantities/'+esc(k),m['name']+' · '+k,q)
 for j,st in enumerate(r['stocks']):
  item=ITEM[UNIT['stock:'+st['id']][0]];ptr=f'/stocks/{j}';item.setdefault('stock_contexts',[]).append({'record_id':rid,'json_pointer':ptr,**deepcopy(st),'molecular_bindings_approved':False});item['text']=st['name']+'. '+st['scope'];STOCK[rid+'::'+st['id']]=item['id']
  for k,q in st['concentrations'].items():attach(item,rid,ptr+'/concentrations/'+esc(k),k.replace('_',' ').capitalize(),q)
  for n,c in enumerate(st['components']):
   for k,q in c['quantities'].items():attach(item,rid,ptr+f'/components/{n}/quantities/'+esc(k),c['material_id']+' · '+k,q)
 for j,opt in enumerate(r['condition_options']):
  ptr=f'/condition_options/{j}';uid=PTRUNIT.get((rid,ptr),'fact:'+SID+'-'+opt['id']if opt['id'].startswith('mw-profile')else'table:table-1');item=ITEM[UNIT[uid][0]];item['canonical_links'].append({'record_id':rid,'json_pointer':ptr,'relation':'Separate source-defined condition option; not a simultaneous combined program.'})
  for k,q in opt['parameters'].items():attach(item,rid,ptr+'/parameters/'+esc(k),opt['label']+' · '+k,q)
 for j,m in enumerate(r['measurements']):
  ptr=f'/measurements/{j}/value';uid=PTRUNIT[(rid,ptr)];item=ITEM[UNIT[uid][0]];out=attach(item,rid,ptr,m['property'].replace('_',' ').capitalize(),m['value'],m['sample_id']);MEAS[rid+'::'+m['id']]=item['id']
  if(rid,ptr)in TD:out['value']=json.loads(m['value']['value']);out['label']='Table headings, column order, footnotes and source scope';out['presentation_kind']='curated_source_inventory';out['basis']='exact_canonical_payload_with_academic_display'
 for j,p in enumerate(r['products']):
  ptr=f'/products/{j}';item=ITEM['record-'+rid];item.setdefault('product_contexts',[]).append({'record_id':rid,'json_pointer':ptr,**deepcopy(p),'atomic_asset_binding_approved':False});item['canonical_links'].append({'record_id':rid,'json_pointer':ptr,'relation':'Source-defined specimen or interpretation context; no newly verified exact pair.'});PRODUCT[rid+'::'+p['sample_id']]=item['id']
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
ASSET_UNITS={a['id']:['figure:'+a['id']]for a in A['assets']if a['id']in {f['id']for f in D['figures']}}
ASSET_UNITS.update({'table-1':['table:table-1'],'heating-profiles':['equation:heating-profile-1','equation:heating-profile-2'],'spinel-defect-expression':['equation:spinel-defects'],'optical-transform':['equation:kubelka-munk'],'zn-hydrolysis-expression':['equation:zn-hydrolysis'],'zn-dissolution-expression':['equation:zn-dissolution']})
GROUP={k:[]for k in['figures','tables','schemes','equations','source_notes']};PUBLIC=[]
for a in A['assets']:
 assert sha(a['path'])==a['sha256']and not a['contains_complete_source_page'];ids=ASSET_UNITS[a['id']];uid=ids[0];item=ITEM[UNIT[uid][0]];kind=uid.split(':')[0];group={'figure':'figures','table':'tables','equation':'equations'}[kind];public='assets/figures/'+SID+'/'+Path(a['path']).name
 rids=sorted({b['record_id']for u in ids for b in UB[u]})
 entry={'id':SID+'-'+a['id'],'label':a['label']+' · '+a['title'],'caption_paraphrase':item['text'],'document_role':'main','page':a['pdf_page'],'printed_page':a['printed_page'],'sample_scope':deepcopy(item['sample_scope']),'sample_links':rids,'sample_linkage':'Source-defined context only; no exact same-aliquot or atomic-coordinate join.','public_asset':public,'public_asset_sha256':a['sha256'],'asset_provenance':{'source_sha256':a['source_sha256'],'source_pdf_page':a['pdf_page'],'crop_normalized':a['normalized_bbox'],'source_render_scale':a['render_scale'],'pixel_dimensions':[a['width'],a['height']],'transformation':'Selected original crop; no plot reconstruction, relabeling or whole-page attachment.'},'source_locators':[e['locator']for e in a['evidence']],'notes':item['notes'].copy(),'reader_render_verified':False,'reviewed':False,'training_eligible':False}
 if kind=='table':entry.update(source_rows=deepcopy(TM['table-1']['rows']),source_notes=deepcopy(TM['table-1']['notes']))
 GROUP[group].append(entry);PUBLIC.append({'id':entry['id'],'private_path':a['path'],'public_asset':public,'sha256':a['sha256'],'selected_original_only':True,'publication_approved':False})
 for u in ids:ITEM[UNIT[u][0]]['original_assets'].append({'id':entry['id'],'label':'Open original '+entry['label'],'public_asset':public,'public_asset_sha256':a['sha256']})
for item in ITEM.values():
 item['canonical_links']=uniq(item['canonical_links']);item['notes']=uniq(item['notes']);item['source_fact_ids']=uniq(item['source_fact_ids'])
 for q in item['facts']:
  if q.get('sample_id'):
   rid=q['canonical_record_id'];n=next(i for i,p in enumerate(R[rid]['products'])if p['sample_id']==q['sample_id']);item['sample_scope']['canonical_sample_links'].append({'record_id':rid,'sample_id':q['sample_id'],'json_pointer':f'/products/{n}','relation':'Exact existing canonical source context; no additional physical sample join.'})
 for b in item['canonical_links']:
  if b['json_pointer'].startswith('/measurements/'):
   m=resolve(R[b['record_id']],'/'.join(b['json_pointer'].split('/')[:3]));n=next(i for i,p in enumerate(R[b['record_id']]['products'])if p['sample_id']==m['sample_id']);item['sample_scope']['canonical_sample_links'].append({'record_id':b['record_id'],'sample_id':m['sample_id'],'json_pointer':f'/products/{n}','relation':'Source-scoped measurement context.'})
  elif b['json_pointer'].startswith('/products/'):
   p=resolve(R[b['record_id']],b['json_pointer']);item['sample_scope']['canonical_sample_links'].append({'record_id':b['record_id'],'sample_id':p['sample_id'],'json_pointer':b['json_pointer'],'recipe_link':p['recipe_link'],'relation':'Exact canonical product/context pointer.'})
 item['sample_scope']['canonical_sample_links']=list({(b['record_id'],b['json_pointer']):b for b in item['sample_scope']['canonical_sample_links']}.values())
for fig in D['figures']:
 item=ITEM[UNIT['figure:'+fig['id']][0]]
 for label in fig['sample_ids']:
  if not re.fullmatch(r'[MSAID]\d+',label):continue
  owner='mw-route'if label[0]=='M'else'scf-route'if label[0]=='S'else'acs-route'if label[0]=='A'else'insitu-oxide'if label in['I15','I16']else'insitu-nitrate'if label[0]=='I'else'pdf-procedure';rid=PRE+owner;n=next(j for j,p in enumerate(R[rid]['products'])if p['source_sample_label']==label)
  item['sample_scope']['canonical_sample_links'].append({'record_id':rid,'sample_id':R[rid]['products'][n]['sample_id'],'json_pointer':f'/products/{n}','relation':'The source explicitly names this Table 1 sample in the figure scope; physical same-aliquot identity remains unverified.'})
 item['sample_scope']['canonical_sample_links']=list({(b['record_id'],b['json_pointer']):b for b in item['sample_scope']['canonical_sample_links']}.values())
# Refresh grouped figure/table/equation scopes after canonical links have been collected.
for entries in GROUP.values():
 for e in entries:
  aid=e['id'].removeprefix(SID+'-');e['sample_scope']=deepcopy(ITEM[UNIT[ASSET_UNITS[aid][0]][0]]['sample_scope'])
docs=[{'role':'main','filename':'10.1021_acs.cgd.9b01519.pdf','sha256':PC['pages'][0]['source_sha256'],'page_count':11,'pages':[{'page':p['pdf_page'],'printed_page':p['printed_page'],'text_read':p['text_read'],'visual_review':p['native_page_visually_inspected'],'sections':[p['coverage_notes']]}for p in PC['pages']]}]
routes={PRE+k:[rid for rid in R if rid!=PRE+k]for k in['mw-route','scf-route','acs-route']}
counts={'reader_items':len(ITEM),'source_units':len(UNIT),'source_facts':len(FACTMAP),'source_fact_bindings':sum(map(len,FACTMAP.values())),'source_table_cells':len(TABLEMAP),'typed_reader_fields':len(FIELD),'canonical_records':len(R),'operations':len(OPS),'material_slots':len(MAT),'stock_slots':len(STOCK),'sample_context_slots':len(PRODUCT),'measurements':len(MEAS),'selected_original_assets':len(PUBLIC),'full_page_public_assets':0,'main_pages':11,'si_pages_read':0,'eligible_training_rows':0,'atomic_structure_assets':0}
source_status='The distinct supplied-main source audit passed; canonical and reader independent approval remain pending.'if PASSED else'The supplied-main source audit is pending; canonical and reader independent approval also remain pending.'
review={'schema_version':'1.0','paper_id':SID,'doi':D['doi'],'title':D['title'],'paper':{'authors':D['authors'],'year':2020,'journal':'Crystal Growth & Design','volume':20,'pages':'1789–1799'},'source_group':SID,'review_scope':'supplied_main_only_si_unverified','documents':docs,'supporting_information':{'status':'declared_locally_unlocated_unverified','matched_local_si_count':0,'pdf_pages':None,'scope':'The 11-page main article was read and visually inspected. Its page 9 declares an SI PDF; bounded source-folder and existing-cache searches found no matched local SI. No SI tables or figures are claimed read.'},'document_identity_verification':{'method':'Exact matching hashes of incoming/legacy main copies; title, authors, DOI and printed pagination agree.'},'coverage_status':'private_author_reader_proposal','independent_audit':source_status+' Historical source-payload pending flags record the author-freeze stage, not later audit status.','publication_status':'Private unapproved proposal only.','source_review_promoted':False,'training_eligible':False,'recipe_inventory':[{'id':rid,'label':r['title'],'record_ids':[rid],'record_type':r['record_type'],'status':'author_draft_pending_independent_review','scope':'Three laboratory synthesis families and distinct supporting procedures/observations. IDs do not count independent physical batches.','gaps':r['quality']['missing_fields']}for rid,r in R.items()],'characterization_inventory':{'reader_item_ids':[i['id']for s in SECTIONS if s['id']in['structures','properties']for i in s['items']]},'chemical_intuition':{'reader_item_ids':[i['id']for s in SECTIONS if s['id']=='intuition'for i in s['items']]},'reader_contract':{'version':'1.0','section_ids':[s['id']for s in SECTIONS]},'reader_sections':SECTIONS,**GROUP,'remaining_gaps':[g['description']for g in D['missingness']]+[source_status,'Molecular, apparatus, product-context, browser and publication gates remain separate.'],'evidence_conflicts':deepcopy(D['conflicts']),'route_evidence_contexts':routes,'route_evidence_scope_notes':{'all':'Linked records are study context; their figures are not automatically measurements of the exact product of each route.','preparation':'Laboratory and in situ nitrate stocks have distinct masses and volumes. Stock preparation, reaction aliquots and sample-specific NaOH formulations remain separate.','time':'Both printed microwave profiles and Table 1 total/dwell times are retained. ACS 17 days versus 2.5 weeks and SCF 450 versus 380 °C are unresolved.','structure':'Literature-fixed positions/occupancies, partial defect expressions and morphology/phase fits do not provide a measured atomic CIF or exact structure–recipe label.','optics':'The optical formula is reproduced literally and current sample bar values are not digitized into invented precision.','scope':'SI remains unlocated; no source gaps are closed by defaults or external-paper assumptions.'},'material_evidence_records':{'ZnAl2O4':[rid for rid,r in R.items()if r['material']['formula']=='ZnAl2O4']},'counts':counts}
save(SID+'.json',review);save('reader-bindings-proposal.json',{'source_id':SID,'status':'private_unapproved','reader_sha256':sha(O/(SID+'.json')),'original_assets':PUBLIC,'operation_to_reader_item':OPS,'material_to_reader_item':MAT,'stock_to_reader_item':STOCK,'product_to_reader_item':PRODUCT,'molecular_apparatus_bindings_approved':False,'publication_approved':False})
save('source-item-coverage.json',{'source_units':UNIT,'source_facts':FACTMAP,'table_cells':TABLEMAP,'canonical_field_map':[{'record_id':rid,'json_pointer':ptr,'reader_item_id':v[0],'reader_fact_id':v[1]['id']}for(rid,ptr),v in FIELD.items()],'measurement_to_reader_item':MEAS,'private_canonical_manifest_sha256':sha(C/'record-manifest.json')})
checks=[]
def ck(n,ok):checks.append({'check':n,'passed':bool(ok)})
for(rid,ptr),(iid,q)in FIELD.items():ck(iid+' '+ptr+' exact canonical equality',resolve(R[rid],ptr)==q['canonical_quantity'])
for item in ITEM.values():
 for b in item['canonical_links']:ck(item['id']+' canonical pointer',resolve(R[b['record_id']],b['json_pointer'])is not None)
 for b in item['sample_scope']['canonical_sample_links']:ck(item['id']+' sample pointer',resolve(R[b['record_id']],b['json_pointer'])['sample_id']==b['sample_id'])
for a in PUBLIC:ck(a['id']+' crop hash',sha(a['private_path'])==a['sha256'])
ck('All 332 source units, 65 facts and 222 table cells',set(UNIT)==set(U)and set(FACTMAP)==set(FM)and len(TABLEMAP)==222)
ck('All canonical slots exactly covered',len(OPS)==CM['counts']['operations']and len(MAT)==CM['counts']['material_slots']and len(STOCK)==CM['counts']['stock_slots']and len(PRODUCT)==CM['counts']['sample_context_slots']and len(MEAS)==CM['counts']['measurements'])
ck('Five academic sections plus sources',[s['id']for s in SECTIONS]==['precursors','protocol','structures','properties','intuition','sources'])
ck('20 selected original assets, no complete page',len(PUBLIC)==20 and all(not a['contains_complete_source_page']for a in A['assets']))
ck('No raw local source paths',not re.search(r'[A-Z]:[\\/]',json.dumps(review)))
ck('Three route context arrays contain valid IDs',len(routes)==3 and all(isinstance(a,list)and all(r in R for r in a)for a in routes.values()))
all_typed=set()
def walk(v,p,rid):
 if isinstance(v,dict):
  if {'value','status','evidence'}<=v.keys():all_typed.add((rid,p));return
  for k,x in v.items():walk(x,p+'/'+esc(k),rid)
 elif isinstance(v,list):
  for j,x in enumerate(v):walk(x,p+'/'+str(j),rid)
for rid,r in R.items():walk(r,'',rid)
ck('Every canonical typed field represented',all_typed==set(FIELD));ck('Source and canonical inputs unchanged',all(sha(p)==h for p,h in FR['bound_files'].items())and all(sha(x['path'])==x['sha256']for x in CM['records']))
assert all(c['passed']for c in checks),[c for c in checks if not c['passed']]
save('author-validation.json',{'status':'author_pointer_transport_contract_checks_passed','author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'check_count':len(checks),'checks':checks,'counts':counts,'independent_source_audit':'passed'if PASSED else'pending','independent_canonical_reader_audit':'pending','browser_visual_gate':'not_performed','site_written':False,'published':False})
inputpaths=[P/'package-freeze.json',P/'source-facts.json',P/'source-inventory.json',P/'source-tables.json',P/'page-coverage.json',P/'original-assets-manifest.json',C/'record-manifest.json',C/'source-to-field-coverage.json',S/'scripts/build_paper_reviews.py',S/'dist/source-evidence.mjs']+([AP]if PASSED else[])
save('reader-manifest.json',{'schema':'mattersyn-private-reader-proposal/1','source_id':SID,'version':1,'author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'status':'private_author_draft_pending_distinct_review','input_hashes':{str(p):sha(p)for p in inputpaths},'outputs':{n:sha(O/n)for n in[SID+'.json','reader-bindings-proposal.json','source-item-coverage.json','author-validation.json']},'author_script_sha256':sha(__file__),'counts':counts,'published':False})
print(json.dumps(counts));print('READER',sha(O/(SID+'.json')))
