"""Nagasaki 2004 reader authoring from frozen source and canonical packages.
Writes private proposals only. No Site, original PDF, canonical or ledger changes.
"""
from pathlib import Path
from collections import defaultdict,Counter
from copy import deepcopy
from datetime import datetime,timezone
import json,hashlib,re
O=Path(__file__).resolve().parent;B=O.parent
S=Path(r'[local path redacted]')
SID='nagasaki2004';P='nagasaki-2004-'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(n,v):(O/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def uniq(v):return list({json.dumps(x,ensure_ascii=False,sort_keys=True):x for x in v}.values())
def ptr(v,p):
 for k in p.strip('/').split('/') if p else []:
  k=k.replace('~1','/').replace('~0','~');v=v[int(k)] if isinstance(v,list) else v[k]
 return v
F=read(B/'source-facts.json');I=read(B/'source-inventory.json');C=read(B/'canonical-source-coverage.json');M=read(B/'canonical-record-manifest.json')
A=read(B/'canonical-records-audit.json');SA=read(B/'source-scientific-audit.json')
R={x['record_id']:read(x['path']) for x in M['records']}
frozen={str(B/n):sha(B/n) for n in ['source-facts.json','source-inventory.json','canonical-source-coverage.json','canonical-record-manifest.json','canonical-records-audit.json','source-scientific-audit.json','page-coverage.json']}
for x in M['records']:
 assert sha(x['path'])==x['sha256'];frozen[x['path']]=x['sha256']
for x in M['original_sources']:
 p=x['path'];h=x['sha256'];assert sha(p)==h;frozen[p]=h
for a in I['assets']:assert sha(a['path'])==a['sha256'];frozen[a['path']]=a['sha256']
sections=[{'id':k,'title':v,'items':[]} for k,v in [('precursors','Precursors'),('protocol','Synthesis protocol'),('structures','Final structures'),('properties','Properties'),('intuition','Chemical intuition'),('sources','Sources and limitations')]]
items={};unit_items={u['id']:[] for u in I['source_units']};U={u['id']:u for u in I['source_units']}
LIMIT='Each sample identifier is scoped to its canonical record. Similar formulations do not establish identical batches or aliquots; assay, polymer and instrument contexts are not independent CdS syntheses.'
def evidence(es):
 out=[]
 for e in es:
  if 'locator' in e:
   match=re.search(r'(Main|SI) PDF p\. (\d+)',e['locator']);role='si' if match and match[1]=='SI' else 'main';page=int(match[2]) if match else None
   out.append({'source_id':SID,'document_role':role,'pdf_page':page,'printed_page':str(6395+page) if page and role=='main' else None,'locator':e['locator']})
  else:
   role='si' if e['source_id'].endswith('-si') else 'main';page=e['pdf_page'];loc='; '.join(str(e[k]) for k in ['section','item'] if e.get(k))
   out.append({'source_id':SID,'document_role':role,'pdf_page':page,'printed_page':e.get('printed_page'),'locator':f'{"SI" if role=="si" else "Main"} PDF p. {page}, {loc}'})
 return uniq(out)
def add(sec,key,title,text,es=None,uids=None,kind='source_reported_context'):
 assert key not in items,key
 uids=uids or [];es=evidence(es or [e for u in uids for e in U[u]['evidence']])
 x={'id':key,'title':title,'text':text,'claim_type':kind,'sample_scope':{'formulations':[],'physical_batch_id':None,'scope_kind':'source_scoped_context','state':title,'link_limit':LIMIT},'evidence':es,'source_locators':[e['locator']for e in es],'canonical_links':[],'notes':[],'facts':[],'source_audit_unit_ids':uids,'source_fact_ids':[],'original_assets':[],'training_eligible':False}
 items[key]=x;next(s for s in sections if s['id']==sec)['items'].append(x)
 for u in uids:unit_items[u].append(key)
 return x
def link(key,rid,p,relation='Exact canonical source context; quantities and specimen limits remain scoped to this record.'):
 items[key]['canonical_links'].append({'record_id':rid,'json_pointer':p,'relation':relation})
def note(key,text):
 if text:items[key]['notes'].append(text)
TEXT={
 'pdp-preparation':('precursors','PDP initiator preparation','Potassium 3,3-diethoxypropanolate (PDP) is prepared from the corresponding alcohol and potassium naphthalene in THF. The paper summarizes the method while citing references 14a and 14b. Individual precursor charges and the initiator-forming conditions are not supplied.'),
 'acetal-block-polymer':('precursors','Sequential PEG/PAMA block-polymer preparation','Condensed ethylene oxide is delivered through a cooled syringe to the PDP solution. After the EO reaction, AMA is added for the separate ambient-temperature block-polymerization stage. The polymer is precipitated into excess 2-propanol; PAMA is protonated and remaining PEG prepolymer is removed by THF Soxhlet extraction. The protonating reagent is not identified.'),
 'aldehyde-polymer':('precursors','Acetal-to-aldehyde conversion','Acetal-ended PEG/PAMA is treated in acetic acid/water, then neutralized with NaOH. Water dialysis provides the aldehyde-polymer branch. The biotin branch diverges before that dialysis.'),
 'biotin-polymer':('precursors','Biotin installation before dialysis','Biocytin hydrazide is added to the aldehyde-polymer solution before dialysis. The reported condensation is followed by NaBH4 reduction of the source-described Schiff base. Reagent amounts, reduction conditions and final biotin functionality are not quantified.'),
 'cho-cds-representative':('protocol','Representative aqueous CdS coprecipitation','CdCl2 is added to the aqueous CHO-PEG/PAMA medium in a glass vial, followed by Na2S. Ambient stirring precedes dialysis against water. The initial polymer-solution volume is reported; neither precursor addition volume nor an unequivocal stock-versus-final concentration basis is given. Added moles and final reaction volume therefore remain unknown.'),
 'biotin-cds':('protocol','Biotin-PEG/PAMA–CdS variant','The biotin polymer is installed before CdS formation and used in a similar coprecipitation procedure. The source does not provide a separately quantified biotin-polymer formulation. This variant retains its own missing quantities rather than copying the representative CHO recipe.'),
 'no-polymer-control':('protocol','Coprecipitation without polymer','The no-polymer comparison precipitates under the tested conditions. Its source-defined control context is retained; separate whole-batch quantities and workup details are not supplied.'),
 'peg-control':('protocol','PEG-OH control','Commercial PEG-OH does not prevent precipitation in the tested comparison. Its reported molecular-weight number is a control-polymer specification, distinct from the PEG segment in the block copolymer.'),
 'pama-control':('protocol','PAMA homopolymer control','PAMA homopolymer gives a transparent pale-yellow low-salt dispersion but precipitates when salt concentration increases. Its fluorescence is weak in the reported comparison. This is not the same polymer as the PAMA segment of PEG/PAMA.'),
 'cho-cds-low-amine':('protocol','Figure 2a concentration variant','The caption identifies curve a as the lower amine-group concentration. It is a formulation comparison, not a timed aliquot. C1 preserves the conflict between the caption/curve ordering and the prose trend.'),
 'cho-cds-high-amine':('protocol','Figure 2c concentration variant','The caption identifies curve c as the higher amine-group concentration. No independently quantified scale or reagent-addition volumes are supplied. The unresolved C1 trend must remain attached to this comparison.'),
 'salt-challenge':('properties','Salt-dependent dispersion comparison','The original photographs compare no polymer, PEG-OH, PAMA and CHO-PEG/PAMA at three printed ionic-strength labels. These are comparison conditions, not successive synthesis stages. The e/f emission axes are scaled differently.'),
 'zeta-assay':('properties','Preparation for the zeta-potential assay','The dispersion is measured in a NaCl electrolyte while pH is adjusted with HCl or NaOH. These assay conditions are separate from synthesis, salt challenge and the FRET medium. Figure 3 refers to the Figure 2 sample without resolving its particular concentration member.'),
 'fret-assay':('properties','Biotin–streptavidin recognition assay','Biotin-functional CdS is mixed with TexasRed-labeled streptavidin. The nominal CdS concentration is not particle-number molarity. The FRET medium ionic strength is reported, but electrolyte identity, mixing volumes, incubation time and dye/protein stoichiometry are not.'),
 'streptavidin-competition':('properties','Unlabeled streptavidin competition','Unlabeled streptavidin is mixed with biotinylated CdS before TexasRed-streptavidin is added. The reported FRET signal decreases. The varied concentration identity in Figure 5 remains unresolved under C2.'),
 'bsa-control':('properties','Bovine serum albumin control','Unlabeled BSA is a separate biological control. The source reports slight initial signal enhancement followed by little further change, rather than inhibition. C2 prevents treating the plotted abscissa as a resolved quantitative competitor concentration.'),
 'tem-preparation':('structures','TEM specimen preparation','A drop of dilute dispersion is deposited on the source-described formval film-coated Cu grid and dried in air. Sample dilution, deposited volume and drying conditions are unreported. Imaging voltage is an acquisition setting, not a synthesis condition.'),
 'xrd-preparation':('structures','Powder-XRD specimen preparation','PEG/PAMA and PEG/PAMA–CdS are named as separately freeze-dried samples supported on glass slides. The supplied figure identifies only the PEG/PAMA–CdS diffractogram; a separately labeled polymer-only trace or background subtraction is not supplied.'),
 'uv-vis-measurement':('properties','UV–visible absorption acquisition','Absorption is recorded on a Shimadzu UV-2400PC with a quartz cell. Figure 2d is the source absorption trace, and its exact concentration-series membership is not resolved.'),
 'fluorescence-measurement':('properties','Steady-state fluorescence acquisition','A Hitachi F-2500 records fluorescence with the reported excitation and emission bandwidths. A common excitation setting does not establish a common specimen. Raw spectra, absolute quantum yields and transfer efficiencies are not supplied.'),
 'zeta-measurement':('properties','Zeta potential and pH','The LEZA-600 measurements show positive potential in the acidic region and slightly negative potential in the alkaline region, while the source reports no coagulation. The quoted potentials are region-level values, not a fitted pKa or isoelectric point.'),
 'si-tem':('structures','Original TEM evidence','Both supplied EF-TEM views show generic PEG/PAMA–CdS, with separate scale bars. The source does not identify a CHO/biotin end group or a particular Figure 2 specimen. No particle histogram, counted population or mean size is newly extracted from these images.'),
 'si-xrd':('structures','Powder diffraction and phase assignment','The main text assigns the PEG/PAMA–CdS powder pattern to hexagonal wurtzite. The SI preserves one trace and unlabeled reference sticks. No indexed peak table, phase-card identity, refinement, measured lattice parameter or atomic coordinates are supplied.'),
 'polymer-nmr':('precursors','End-acetal functionality by ¹H NMR','The source describes end-acetal functionality as almost quantitative from ¹H NMR. It supplies neither a numerical percentage nor a spectrum, integration, solvent or instrument frequency. This result does not establish the later biotin end-group functionality.'),
 'purified-acetal-block-polymer':('precursors','Block-polymer characterization','The two segment molecular-weight numbers and the resulting block-polymer Mw/Mn are reported separately. The molecular-weight units and separate averaging definitions are not explicit. Polymer dispersity is not a CdS particle-size distribution.'),
 'figure2-series':('properties','Concentration-dependent spectra: scope and C1','Three caption-defined amine-group concentrations are compared. Solutions remain transparent in the tested region. The prose says intensity increases with polymer concentration, whereas the plotted a/b/c ordering has the opposite amplitude direction. The original wording and all labels remain unresolved.'),
 'cho-cds-salt-challenge':('properties','Stability of CHO-PEG/PAMA–CdS in salt','The source reports strong fluorescence and no precipitation during the stated NaCl challenge for several days. The duration is qualitative; batch identity, exact observation times and independent repeats are not provided.'),
 'figure2-absorption-sample-unresolved':('structures','Optical size estimate with unresolved specimen identity','The reported absorption edge is used with the cited Henglein band-gap theory to estimate CdS size. This is an author-model estimate, not a separately quantified TEM distribution. The particular a/b/c preparation behind absorption trace d is unknown.'),
 'cho-cds-generic':('properties','Emission of CHO-PEG/PAMA–CdS','The source reports a strong CdS emission band for the CHO-ended block-polymer material. This generic optical statement does not identify an exact TEM/XRD specimen or an absolute quantum yield.'),
 'biotin-cds-generic':('properties','Emission of biotin-PEG/PAMA–CdS','The biotin-ended material is reported to retain strong emission. This separate optical claim does not demonstrate a shared physical batch, end-group loading or SI structural-sample identity.'),
 'figure4-fret-series':('properties','Figure 4 protein-concentration legend','All eleven printed TexasRed-streptavidin concentration labels are retained as one spectral-series legend. They are not eleven newly constructed synthesis records. The graph abbreviation Tex-Avidin is preserved while the text/caption protein identity remains streptavidin (C4).'),
 'abstract-biotin-cds':('structures','Abstract-level size summary','The abstract gives an approximate CdS size in the biotin-polymer context. This overview is retained separately from the optical size estimate and the unresolved generic SI images; it does not define a second independently measured size target.')}
for uid,u in U.items():
 sec,title,text=TEXT[uid];add(sec,uid,title,text,uids=[uid])

OBJ={};object_targets={}
def object_key(cat,oid):return cat+'::'+str(oid)
for cat in ['materials','stocks','protocols','samples','measurements','observations','author_interpretations_and_outlook','figures','references','contradictions','gaps','unperformed_options']:
 for n,x in enumerate(F[cat]):OBJ[object_key(cat,x.get('id',str(n)))]=x
for x in I['administrative_and_footnote_units']:OBJ[object_key('administrative_and_footnote_units',x['id'])]=x
OBJ['bibliography::identity']={'title':F['title'],'authors':F['authors'],**F['bibliography']};OBJ['structure_status::scope']=F['structure_status']
# Source identities: complete inventory, including media, analytical reagents and removed fractions.
for m in F['materials']:
 key='material-'+m['id'];uids=[u for u in m['scope_ids'] if u in U]
 x=add('precursors',key,m['name'],m['role'].capitalize()+'. '+m['notes'],m['evidence'],uids,'source_material_identity')
 note(key,'Supplier: '+(m['supplier_as_reported'] or 'not reported')+'. Purity, pretreatment and storage are unreported unless explicitly described in the linked procedure.')
 if m['formula_as_printed']:note(key,'Formula printed in this source: '+m['formula_as_printed']+'. Hydration, polymer-chain distribution and solution speciation are not inferred.')
 else:note(key,'No unique molecular formula is printed for this source entry. A future reference depiction cannot establish polymer length, protein conformation or solution speciation.')
 x['material_identity']={'source_material_id':m['id'],'name':m['name'],'formula_as_printed':m['formula_as_printed'],'exact_molecular_asset_binding_approved':False}
 object_targets[object_key('materials',m['id'])]=key
for st in F['stocks']:
 key='stock-'+st['id'];unit=st.get('preparation_protocol');uids=[unit] if unit in U else ['cho-cds-representative']
 title={'pdp-thf-solution':'PDP in THF','aqueous-polymer-medium':'Aqueous CHO-PEG/PAMA medium','cdcl2-na2s-concentration-statements':'CdCl₂ and Na₂S concentration statements'}[st['id']]
 text={'pdp-thf-solution':'The initiator amount and THF medium volume are retained without calculating a stock concentration or assuming volume additivity. Storage is not reported.', 'aqueous-polymer-medium':'The initial aqueous-medium volume and amine-group concentration are specified. This is not whole-polymer-chain molarity; preparation and storage details are incomplete.', 'cdcl2-na2s-concentration-statements':'The source reports equal concentration numbers for the two successively added precursors. Their addition volumes, separate stock formulations and stock-versus-final basis are unresolved. They are not one premixed Cd/S stock.'}[st['id']]
 add('precursors',key,title,text,uids=uids,kind='source_stock_scope');object_targets[object_key('stocks',st['id'])]=key
for p in F['protocols']:object_targets[object_key('protocols',p['id'])]=p['id']
for s in F['samples']:
 key='sample-'+s['id'];uids=[u for u in [s['protocol_id'],s['id']] if u in U]
 sec='structures' if s['id'].startswith('si-') or 'absorption-sample' in s['id'] else 'protocol' if s['id']=='cho-cds-representative' else 'properties'
 es=[e for u in uids for e in U[u]['evidence']]
 if not es:es=F['figures'][5 if s['id']=='figure6-response-series' else 4]['evidence']
 add(sec,key,'Specimen context: '+s['id'].replace('-',' '),s['state'].capitalize()+'. '+s['measurement_scope'],es,uids,'source_sample_scope')
 note(key,'Source association: '+s['link_status']+'. Independent batch or replicate identity is not established.')
 object_targets[object_key('samples',s['id'])]=key
for m in F['measurements']:object_targets[object_key('measurements',m['id'])]=m['id']
obs_titles=['Precipitation in no-polymer and PEG controls','PAMA: low-salt dispersion and high-salt failure','CHO-polymer salt stability','Transparency and unresolved concentration trend','Dispersion across the zeta-potential series','Acceptor emission under CdS excitation','Specific competition and the BSA comparison']
obs_text=['CdS precipitates in the no-polymer and PEG-OH comparisons. These are reported stabilization failures, not evidence that CdS did not form.','PAMA gives a pale-yellow transparent low-salt solution, but precipitates when salt increases and shows little emission at the reported excitation.','CHO-PEG/PAMA–CdS retains strong fluorescence and the source reports no precipitation in the stated NaCl challenge for several days.','All three tested concentrations remain transparent. Their fluorescence trend retains the unresolved C1 caption/prose discrepancy.','The source reports no coagulation across the measurement pH region despite the sign change in zeta potential.','The TexasRed-associated emission increases with labeled-protein concentration under the reported CdS excitation; numerical transfer efficiency is not supplied.','Unlabeled streptavidin reduces FRET; BSA does not inhibit and initially gives slight enhancement. C2 leaves the exact varying concentration unresolved.']
for n,o in enumerate(F['observations']):
 key='observation-'+str(n);add('properties',key,obs_titles[n],obs_text[n],o['evidence'],kind=o['status']);object_targets[object_key('observations',str(n))]=key
for x in F['author_interpretations_and_outlook']:
 title={'author-coordination':'Polyamine anchoring and PEG steric stabilization','author-segregation':'Proposed block segregation at the interface','author-size-control':'Limits of the proposed growth-control relationship','author-phase':'Scope of the wurtzite assignment','author-fret':'Recognition-mediated energy transfer','author-bsa':'Proposed excluded-volume effect of BSA','outlook':'Proposed bioanalytical applications'}[x['id']]
 add('structures' if x['id']=='author-phase' else 'intuition',x['id'],title,x['claim'],x['evidence'],kind=x['status']);note(x['id'],x['limits']);object_targets[object_key('author_interpretations_and_outlook',x['id'])]=x['id']
for x in F['references']:
 key=x['id'];add('sources',key,'Reference '+x['printed_label'],x['bibliography_as_printed_normalized_spacing'],x['evidence'],kind='cited_reference_not_independently_inspected');note(key,'Context: '+x['use_in_current_paper']+'. '+x['access_level']+'.');object_targets[object_key('references',key)]=key
for x in F['contradictions']:
 key='conflict-'+x['id'];add('properties',key,x['id']+': '+x['topic'],x['source_claim']+' '+x['visual_observation'],x['evidence'],kind='unresolved_source_conflict');note(key,x['resolution']);object_targets[object_key('contradictions',x['id'])]=key
for x in F['gaps']:
 gap_units={'G1':['pdp-preparation','acetal-block-polymer'],'G2':['aldehyde-polymer','biotin-polymer'],'G3':['aldehyde-polymer','biotin-polymer','cho-cds-representative'],'G4':['cho-cds-representative'],'G5':['no-polymer-control','peg-control','pama-control','figure2-series'],'G6':['figure2-absorption-sample-unresolved','zeta-assay','si-tem','si-xrd'],'G7':['figure2-absorption-sample-unresolved','si-tem','si-xrd'],'G8':['fret-assay','streptavidin-competition','bsa-control'],'G9':['tem-preparation','xrd-preparation'],'G10':['pdp-preparation','figure2-absorption-sample-unresolved','fret-assay']}[x['id']]
 key='gap-'+x['id'];add('sources',key,x['id']+': '+x['scope'],x['missing'],uids=gap_units,kind='source_missingness');note(key,x['impact']);object_targets[object_key('gaps',x['id'])]=key
for x in F['unperformed_options']:
 add('intuition',x['id'],'Alternative ligand-installation order',x['description'],x['evidence'],kind='discussed_not_performed');object_targets[object_key('unperformed_options',x['id'])]=x['id']
admin_text={'identity-and-dates':'The title, six authors, journal and publication dates belong to the supplied main article. These metadata identify the contribution, not an experimental sample.', 'author-footnotes':'The source lists Tokyo University of Science and University of Tokyo affiliations, correspondence footnotes and Hidenori Otsuka’s present-address note. These are administrative source context.', 'reference-note11':'The authors characterize the cited PEG/PEI architecture as a graft copolymer rather than the block-copolymer wording of the earlier source. This is their correction; the earlier full paper was not inspected here.', 'acknowledgment':'The authors acknowledge the Special Coordination Funds, Ministry of Education, Science and Sports, Japan.', 'si-declaration':'The main article declares TEM and XRD of PEG/PAMA–CdS. Those contents, the embedded manuscript identity and the independently audited local pairing identify the supplied three-page SI.', 'inline-math':'The source uses concentration expressions, Mw/Mn, signed zeta potentials and 2θ scan notation. It supplies no numbered equation or the full derivation of its cited band-gap size model.'}
for x in I['administrative_and_footnote_units']:
 key='source-'+x['id'];add('sources',key,x['id'].replace('-',' ').capitalize(),admin_text[x['id']],x['evidence'],kind='source_identity_or_context');object_targets[object_key('administrative_and_footnote_units',x['id'])]=key
add('sources','source-bibliography','Article identity',F['title'],I['administrative_and_footnote_units'][0]['evidence']);object_targets['bibliography::identity']='source-bibliography'
add('structures','atomic-structure-availability','Atomic structure and coordinate-file availability','The reported wurtzite assignment does not provide an atomically resolved particle, polymer coating or protein complex. No supplied CIF, atomic coordinates, measured lattice parameters or validated recipe-to-structure specimen join is available.',U['si-xrd']['evidence'],kind='explicit_structure_missingness');object_targets['structure_status::scope']='atomic-structure-availability'

# Every original figure retains its own panel and specimen scope.
fig_items={}
for f in F['figures']:
 key=f['id'];title={'main-figure1':'Figure 1: polymer and salt comparisons','main-figure2':'Figure 2: fluorescence and absorption','main-figure3':'Figure 3: zeta potential','main-figure4':'Figure 4: labeled-protein spectral series','main-figure5':'Figure 5: recognition controls','main-figure6':'Figure 6: concentration response and inset','si-figure1':'SI Figure 1: two TEM views','si-figure2':'SI Figure 2: powder diffractogram'}[key]
 x=add('structures' if key.startswith('si-') else 'properties',key,title,f['content'],f['evidence'],kind='original_source_figure');x['notes'].extend([f['disposition'],{'Original axes, ticks and labels':f['axes_and_labels']}]);object_targets[object_key('figures',key)]=key;fig_items[key]=x

# Source objects and units establish exact, immutable canonical pointer destinations.
targets=defaultdict(list)
for row in C['source_objects']:
 key=object_targets[object_key(row['category'],row['source_object_id'])];targets[(row['record_id'],row['pointer'])].append(key);link(key,row['record_id'],row['pointer'])
for row in C['source_units']:
 for z in row['canonical_bindings']:targets[(z['record_id'],z['pointer'])].append(row['source_unit_id']);link(row['source_unit_id'],z['record_id'],z['pointer'])
for row in C['facts']:
 for z in row['canonical_bindings']:targets[(z['record_id'],z['pointer'])].append(row['source_fact']['source_unit_id'])
def record_section(rid):
 s=rid.removeprefix(P)
 return 'precursors' if s in ['polymer-preparation','aldehyde-polymer','biotin-polymer'] else 'protocol' if s in ['cho-cds','biotin-cds','stabilizer-controls','concentration-series'] else 'structures' if s in ['tem','xrd'] else 'intuition' if s=='chemical-intuition' else 'sources' if s=='source-context' else 'properties'
record_item={}
for rid,r in R.items():
 key='record-'+rid.removeprefix(P);record_item[rid]=key
 record_evidence=r['intended_target']['composition']['evidence']
 if rid==P+'cho-cds':record_evidence=U['cho-cds-representative']['evidence']
 elif rid==P+'biotin-cds':record_evidence=U['biotin-cds']['evidence']
 add(record_section(rid),key,r['title'].split(' · ')[-1],r['method']+'. '+LIMIT,record_evidence,kind='canonical_record_scope');link(key,rid,'')

def qvalue(q):
 if q.get('value') is not None:return q['value']
 lo,hi=q.get('minimum'),q.get('maximum')
 if lo is not None and hi is not None:return f'{lo:g}–{hi:g}'
 if lo is not None:return ('> ' if q.get('minimum_exclusive') else '≥ ')+f'{lo:g}'
 if hi is not None:return ('< ' if q.get('maximum_exclusive') else '≤ ')+f'{hi:g}'
 return 'Not reported' if q.get('status')=='not_reported' else q.get('raw_text') or q.get('status','Not reported')
fact_targets={};measurement_map={};operation_map={};parameter_map={};material_map={};stock_map={};material_slots={};sample_map={}
OP_TEXT={
 'pdp-form':'Prepare PDP by reacting the corresponding alcohol with potassium naphthalene in THF. Separate reagent charges, reaction conditions and potassium-naphthalene preparation are not supplied. The paper cites methods 14a and 14b; their full procedures were not inspected.',
 'eo-add':'Add condensed ethylene oxide to the PDP solution through a cooled syringe. Syringe temperature, delivery rate, reaction temperature and atmosphere are not stated. The cooled delivery device does not establish the temperature of the polymerization.',
 'eo-react':'Allow the ethylene oxide reaction to proceed for two days before adding AMA. Reaction temperature and stirring speed are not reported.',
 'ama-block':'Add AMA to the reaction mixture and stir for a further 60 minutes at ambient temperature. The addition rate, numerical temperature and stirring speed are not supplied.',
 'polymer-precipitate':'Precipitate the block copolymer into a large excess of 2-propanol. Retain the polymer fraction; the mother liquor is not characterized. Precipitant volume, collection method, drying and yield are not reported.',
 'pama-protonate':'Protonate the PAMA segment before the THF Soxhlet extraction. The protonating reagent, amount, temperature and treatment duration are not identified.',
 'soxhlet-clean':'Remove the small residual PEG-prepolymer fraction by Soxhlet extraction with THF. The PEG impurity leaves with the extract. Solvent volume, extraction duration, drying and isolated yield are not reported.',
 'polymer-nmr':'Assess end-acetal functionality by ¹H NMR. The authors describe it as almost quantitative without supplying a spectrum, numerical percentage, integrations, solvent or instrument frequency. This does not quantify subsequent biotin functionalization.',
 'hydrolyze-acetal':'Dissolve the block copolymer in acetic acid/water at a 10:1 volume ratio and stir for five hours at 35 °C. The polymer charge and total solvent volume are not given.',
 'neutralize':'Neutralize the reacted polymer solution with NaOH. The NaOH concentration, amount and endpoint pH are not reported.',
 'dialyze-polymer':'Dialyze the CHO-polymer solution against water. The membrane, molecular-weight cutoff, duration, water-exchange schedule and temperature are unspecified. Final concentration, yield and storage are also not reported.',
 'biotin-condense':'Before the stated polymer-dialysis stage, add biocytin hydrazide to the aldehyde-polymer solution and react for two hours. Hydrazide and polymer amounts, pH, temperature and site conversion are not quantified. Biotin installation precedes CdS formation.',
 'biotin-reduce':'Add NaBH₄ to reduce the source-described Schiff base. The reductant charge, reaction time, temperature and quench are not supplied. This is part of the branch inserted before polymer dialysis, not post-synthesis CdS conjugation.',
 'biotin-dialysis-context':'Retain the biotin branch at its reported position before water dialysis. The paper does not give a separately detailed purification for the biotin polymer. Dialysis settings, final concentration, biotin functionality and storage remain unknown.',
 'polymer-medium':'Place 8 mL of aqueous block-copolymer solution in a glass vial. Its concentration is specified on an amine-group basis. Polymer mass, chain molarity, pH and vial capacity are not supplied.',
 'cd-add':'Add CdCl₂ to the polymer medium first. The concentration number is reported, but addition volume, stock-versus-final basis, delivery rate and mixing conditions are not.',
 's-add':'Add Na₂S after CdCl₂. Its addition volume, stock-versus-final concentration basis and delivery rate are not supplied. The two precursor solutions are not described as a premixed stock.',
 'cds-stir':'Stir the coprecipitation mixture for one hour at ambient temperature. A numerical temperature, atmosphere and stirring speed are not reported.',
 'cds-dialyze':'Purify the CdS dispersion by dialysis against water. Diffusible solutes are not individually identified. Membrane specifications, duration, water exchanges, temperature, final volume, concentration, yield and storage are not given.',
 'biotin-cds-coprecipitate':'Use biotin-PEG/PAMA instead of CHO-PEG/PAMA in the preparation described as similar. The paper provides a shared qualitative coprecipitation and dialysis framework, without a separately quantified biotin formulation. Exact batch linkage and biotin surface density are unknown.',
 'no-polymer-control-prepare':'Compare CdCl₂/Na₂S coprecipitation without a polymer. The source reports precipitation and attributes it to crystal growth. Independent reaction volumes, workup and replicate counts are not supplied; this comparison is not an additional fully quantified synthesis.',
 'peg-control-prepare':'Compare CdCl₂/Na₂S coprecipitation with commercial PEG-OH. PEG-OH does not prevent precipitation under the tested conditions. Separate reaction volumes, workup and replicate counts are unreported.',
 'pama-control-prepare':'Compare CdCl₂/Na₂S coprecipitation with PAMA homopolymer. It gives a transparent pale-yellow low-salt dispersion, but increasing salt causes immediate precipitation and the reported fluorescence is weak. Independent batch quantities, workup and repeats are not specified.',
 'cho-cds-low-amine-prepare':'Retain Figure 2a as the caption-defined lower-amine formulation within the common aqueous preparation. Separate addition volumes, yield and physical-batch identity are not supplied. The caption and prose trend remain inconsistent under C1.',
 'cho-cds-high-amine-prepare':'Retain Figure 2c as the caption-defined higher-amine formulation within the common aqueous preparation. Separate addition volumes, yield and physical-batch identity are not supplied. C1 prevents using the conflicting trend as a resolved growth-control relationship.',
 'tem-grid-dry':'Deposit a drop of dilute dispersion on the source-described formval-film-coated Cu grid and let it dry in air. Dilution, drop volume, drying time and source batch are not stated. The specimen is labeled generically as PEG/PAMA–CdS.',
 'tem-acquire':'Acquire energy-filtered TEM images with a LEO 922 OMEGA at 200 kV. The two original images retain their individual scale bars. Imaging settings do not provide a quantified particle-size distribution or establish a biotin-ended specimen.',
 'xrd-freeze-dry':'Freeze-dry PEG/PAMA and PEG/PAMA–CdS as separate samples and support them on glass slides. Drying conditions, loading masses and dispersion batches are unknown. No separately labeled polymer-only diffractogram or background subtraction is supplied.',
 'xrd-scan':'Measure powder diffraction with a vertical goniometer and Cu Kα radiation on a Shimadzu LabX XRD-6100. The reported voltage, current, scan range and step remain linked below. Dwell time, scan rate and reference-stick provenance are not given.',
 'salt-expose':'Compare the separate prepared dispersions at the three Figure 1 ionic-strength labels. The text reports CHO-polymer CdS stability in 0.3 M NaCl for several days. Salt-addition volumes, individual exposure times and precise specimen lineage are unknown. This challenge is separate from the base synthesis.',
 'uv-vis':'Measure absorption with a Shimadzu UV-2400PC and quartz cell. The particular concentration-series member behind Figure 2d is unresolved.',
 'fluorescence':'Record steady-state fluorescence with a Hitachi F-2500 using the linked excitation and bandwidth settings. Shared instrument settings do not establish a shared physical specimen across polymer comparisons and recognition assays.',
 'zeta-medium':'Measure zeta potential with a LEZA-600 in 7.5 mM NaCl over pH 2–11, adjusting with the source-described HCl or NaOH solutions. The adjusters are alternatives, not simultaneous additions or a specified titration sequence. Sample concentration, exact Figure 2 member, temperature and equilibration time are unknown.',
 'fret-mix':'Mix biotinylated CdS with TexasRed-streptavidin and acquire fluorescence with 400 nm excitation. Volumes, electrolyte identity, incubation, temperature, dye-labeling ratio and dilution lineage are unspecified. Figure 4 spectra and Figure 6 response plots are related assay contexts without exact point-to-spectrum joins.',
 'streptavidin-competition-premix':'Premix biotinylated CdS with unlabeled streptavidin, then add TexasRed-streptavidin and monitor FRET. The signal decreases, which the authors interpret as specific competition. The Figure 5 caption inherits common Figure 4 settings, but volumes, incubation and the exact varied concentration remain unresolved under C2.',
 'bsa-control-premix':'Premix biotinylated CdS with unlabeled BSA before adding TexasRed-streptavidin. The source reports slight initial enhancement followed by little change. The proposed excluded-volume explanation remains an interpretation. Mixing details and the Figure 5 varied concentration are not resolved; only the caption-stated common Figure 4 settings are inherited.'}
def attach(key,rid,p,label,q,basis,identifier,sample=None,extra=None):
 assert (rid,p) not in fact_targets,(rid,p)
 item=items[key];f={'id':rid+'::'+identifier,'label':label,'value':qvalue(q),'unit':q.get('unit'),'status':q['status'],'approximate':q.get('approximate',False),'qualifier':' '.join(str(t) for t in [q.get('basis'),q.get('qualifier'),q.get('note'),extra] if t),'basis':basis,'evidence':evidence(q.get('evidence',[])),'canonical_record_id':rid,'json_pointer':p,'canonical_quantity':deepcopy(q),'training_eligible':False}
 if sample:f['sample_id']=sample
 item['facts'].append(f);link(key,rid,p);item['evidence']=uniq(item['evidence']+f['evidence']);item['source_locators']=uniq(item['source_locators']+[e['locator']for e in f['evidence']]);fact_targets[(rid,p)]=(key,f)
 return f
def destination(rid,p):return targets[(rid,p)][0] if targets[(rid,p)] else record_item[rid]
for rid,r in R.items():
 for n,m in enumerate(r['measurements']):
  p=f'/measurements/{n}/value';key=destination(rid,p);f=attach(key,rid,p,m['property'].replace('_',' ').capitalize(),m['value'],m['technique'],m['id'],m['sample_id'],m.get('conditions'));f['canonical_measurement_id']=m['id'];measurement_map[rid+'::'+m['id']]=key
 for n,o in enumerate(r['operations']):
  p=f'/operations/{n}';key='operation-'+rid.removeprefix(P)+'-'+o['id'];us=[]
  for row in C['source_units']:
   if any(z['record_id']==rid and z['pointer']==p for z in row['canonical_bindings']):us.append(row['source_unit_id'])
  add(record_section(rid),key,o['label'],OP_TEXT[o['id']],o['evidence'],us,'source_procedure_stage');link(key,rid,p)
  items[key]['operation_context']={'record_id':rid,'operation_id':o['id'],'inputs':deepcopy(o['inputs']),'outputs':deepcopy(o['outputs']),'environment':deepcopy(o.get('environment')),'condition_options':deepcopy(o.get('condition_options',[])),'retained_fraction':deepcopy(o.get('retained_fraction'))}
  note(key,'Environment: '+str(o.get('environment',{}).get('value') or 'not reported')+'. '+o.get('environment',{}).get('note',''))
  note(key,{'Inputs and output states':{'inputs':o['inputs'],'outputs':o['outputs'],'retained_fraction':o.get('retained_fraction')}})
  operation_map[rid+'::'+o['id']]=key
  for name,q in o['parameters'].items():
   f=attach(key,rid,p+'/parameters/'+name,o['label']+' · '+name.replace('_',' '),q,'operation_parameter','operation-'+o['id']+'-'+name);f['canonical_operation_id']=o['id'];parameter_map[rid+'::'+o['id']+'::'+name]=key
  for j,opt in enumerate(o.get('condition_options',[])):
   for name,q in opt.get('parameters',{}).items():attach(key,rid,p+f'/condition_options/{j}/parameters/'+name,name.replace('_',' '),q,'alternative_operation_parameter',f'option-{o["id"]}-{j}-{name}',extra='Alternative condition, not simultaneous.')
 for n,m in enumerate(r['materials']):
  p=f'/materials/{n}';key='material-'+m['id'] if 'material-'+m['id'] in items else record_item[rid];link(key,rid,p);material_slots[rid+'::'+m['id']]={'reader_item_id':key,'json_pointer':p}
  if key.startswith('material-'):
   items[key].setdefault('canonical_material_slots',[]).append({'record_id':rid,'material_id':m['id'],'json_pointer':p,'formula':m.get('formula'),'role':m.get('role'),'name':m['name']})
   if m.get('formula'):note(key,'Canonical named-identity formula: '+m['formula']+'. This reference identity does not establish an unreported hydrate, solution coordination structure or exact molecular-viewer binding.')
  else:note(key,{'Scoped material or specimen':{'id':m['id'],'name':m['name'],'role':m['role'],'formula':m.get('formula'),'notes':m.get('notes','')}})
  for name,q in m.get('quantities',{}).items():
   f=attach(key,rid,p+'/quantities/'+name,m['name']+' · '+name.replace('_',' '),q,'reagent_specification','material-'+m['id']+'-'+name);f['canonical_material_id']=m['id'];material_map[rid+'::'+m['id']+'::'+name]=key
 for n,st in enumerate(r.get('stocks',[])):
  p=f'/stocks/{n}';key=destination(rid,p);link(key,rid,p);note(key,st['scope'])
  for name,q in st.get('concentrations',{}).items():attach(key,rid,p+'/concentrations/'+name,st['name']+' · '+name.replace('_',' '),q,'stock_concentration','stock-'+st['id']+'-'+name);stock_map[rid+'::'+st['id']+'::'+name]=key
  for j,comp in enumerate(st['components']):
   for name,q in comp.get('quantities',{}).items():attach(key,rid,p+f'/components/{j}/quantities/'+name,comp['material_id']+' · '+name.replace('_',' '),q,'stock_component_quantity',f'stock-{st["id"]}-{j}-{name}');stock_map[rid+'::'+st['id']+'::'+str(j)+'::'+name]=key
 for n,s in enumerate(r['products']):
  p=f'/products/{n}';key=destination(rid,p);link(key,rid,p);sample_map[rid+'::'+s['sample_id']]={'reader_item_id':key,'json_pointer':p}
  items[key].setdefault('canonical_sample_contexts',[]).append({'record_id':rid,'json_pointer':p,'sample':deepcopy(s)})
  note(key,{'Canonical specimen':{'source_sample_label':s['source_sample_label'],'recipe_link':s['recipe_link'],'notes':s.get('notes',''),'composition':s['composition'],'phase':s['phase']}})

# Each source fact maps to its original source-unit view and every precise reader quantity.
sfmap={}
for row in C['facts']:
 uid=row['source_fact']['source_unit_id'];fid=row['source_fact_id'];items[uid]['source_fact_ids'].append(fid);links=[]
 for z in row['canonical_bindings']:
  key,f=fact_targets[(z['record_id'],z['pointer'])];f.setdefault('source_fact_ids',[]).append(fid);items[key]['source_fact_ids'].append(fid);links.append({**z,'reader_item_id':key,'reader_fact_id':f['id']})
 sfmap[fid]={'source_unit_id':uid,'reader_item_ids':list(dict.fromkeys([uid]+[z['reader_item_id']for z in links])),'canonical_bindings':links,'original_source_fact':deepcopy(row['source_fact'])}
for row in C['source_units']:
 for z in row['canonical_bindings']:
  candidates=[k for (rid,p),(k,f) in fact_targets.items() if rid==z['record_id'] and (p==z['pointer'] or p.startswith(z['pointer']+'/'))]
  candidates+=targets[(z['record_id'],z['pointer'])]
  for key in candidates:
   if key not in unit_items[row['source_unit_id']]:unit_items[row['source_unit_id']].append(key)
   if row['source_unit_id'] not in items[key]['source_audit_unit_ids']:items[key]['source_audit_unit_ids'].append(row['source_unit_id'])
# Original object payloads remain exact in a private audit-side map; readable views
# above expose them as prose, scope notes, figures and precise canonical links.
object_map=[]
for row in C['source_objects']:
 k=object_key(row['category'],row['source_object_id']);object_map.append({**row,'reader_item_id':object_targets[k],'source_object_payload':deepcopy(OBJ[k])})

assets=[];private_assets=[]
for a in I['assets']:
 f=next(f for f in F['figures']if f['asset_id']==a['id']);key=f['id'];path='assets/figures/'+SID+'/'+Path(a['path']).name
 joins=[]
 for sample in f['sample_ids']:
  for rid,r in R.items():
   if any(p['sample_id']==sample for p in r['products']):joins.append({'record_id':rid,'sample_id':sample,'relation':'Original figure association at the source-defined specimen/context level; no physical-batch equivalence inferred.'})
 aa={'id':SID+'-'+a['id'],'label':items[key]['title'],'document_role':a['source_role'],'page':a['pdf_page'],'printed_page':str(6395+a['pdf_page']) if a['source_role']=='main' else None,'caption_paraphrase':items[key]['text'],'sample_scope':' / '.join(f['sample_ids']),'sample_links':list(dict.fromkeys(j['record_id'] for j in joins)),'canonical_sample_links':joins,'sample_linkage':LIMIT,'evidence_class':'original_experimental_figure','public_asset':path,'public_asset_sha256':a['sha256'],'asset_provenance':{'source_file':Path(next(d['original_path']for d in I['documents']if d['role']==a['source_role'])).name,'source_sha256':a['source_sha256'],'source_pdf_page':a['pdf_page'],'crop_normalized':a['crop_rectangle_fraction_top_origin'],'crop_pdf_points':a['crop_rectangle_pdf_points_top_origin'],'render_scale':a['render_scale'],'pixel_dimensions':a['pixel_size'],'transformation':a['creation']},'notes':[f['disposition'],{'Original axes and labels':f['axes_and_labels']}],'source_locators':[e['locator']for e in evidence(f['evidence'])],'text_reviewed':True,'visual_reviewed':True,'reviewed':False,'reader_render_verified':False,'training_eligible':False}
 conflicts={'main-figure2':['C1'],'main-figure4':['C4'],'main-figure5':['C2'],'main-figure6':['C3','C4']}.get(key,[])
 for c in conflicts:aa['notes'].append(items['conflict-'+c]['text']+' '+items['conflict-'+c]['notes'][0])
 if key.startswith('si-'):aa['notes'].append('Generic PEG/PAMA–CdS specimen; CHO/biotin end group, Figure 2 formulation and assay batch identity are unresolved.')
 assets.append(aa);private_assets.append({'id':aa['id'],'private_path':a['path'],'public_asset':path,'sha256':a['sha256'],'reviewed':False,'reader_render_verified':False})
 view={'id':aa['id'],'label':'Original '+items[key]['title'],'public_asset':path,'public_asset_sha256':a['sha256']};items[key]['original_assets'].append(view)
 for c in conflicts:items['conflict-'+c]['original_assets'].append(view)
 # Exact sample views, source-unit views and record context can reach the original.
 for j in joins:
  rkey=record_item[j['record_id']];items[rkey]['original_assets'].append(view)
  for ik,it in items.items():
   if any(z.get('canonical_record_id')==j['record_id'] and z.get('sample_id')==j['sample_id'] for z in it['facts']):it['original_assets'].append(view)
  sk=sample_map[j['record_id']+'::'+j['sample_id']]['reader_item_id'];items[sk]['original_assets'].append(view)
for key in ['figure2-series','cho-cds-low-amine','cho-cds-high-amine','figure2-absorption-sample-unresolved']:
 note(key,'C1 is unresolved; see the original Figure 2 caption, curve labels and the dedicated conflict item.');items[key]['original_assets']+=items['main-figure2']['original_assets']
for key in ['si-tem','tem-preparation']:items[key]['original_assets']+=items['si-figure1']['original_assets']
for key in ['si-xrd','xrd-preparation','author-phase','atomic-structure-availability']:items[key]['original_assets']+=items['si-figure2']['original_assets']
for key in ['fret-assay','figure4-fret-series']:items[key]['original_assets']+=items['main-figure4']['original_assets']
for key in ['streptavidin-competition','bsa-control']:items[key]['original_assets']+=items['main-figure5']['original_assets']
for it in items.values():
 joins=[]
 for f in it['facts']:
  if f.get('sample_id'):
   rid=f['canonical_record_id'];n=next(n for n,p in enumerate(R[rid]['products']) if p['sample_id']==f['sample_id']);joins.append({'record_id':rid,'sample_id':f['sample_id'],'json_pointer':f'/products/{n}','source_label':R[rid]['products'][n]['source_sample_label'],'relation':LIMIT})
 it['sample_scope']['canonical_sample_links']=uniq(joins);it['sample_scope']['formulations']=[j['record_id']+' / '+j['sample_id']for j in uniq(joins)]
 for field in ['canonical_links','notes','original_assets','source_audit_unit_ids','source_fact_ids']:it[field]=uniq(it[field])
docs=[{'role':d['role'],'filename':d['original_filename'],'sha256':d['source_sha256'],'page_count':d['page_count'],'pages':[{'page':p['pdf_page'],'printed_page':p['printed_page'],'text_read':True,'visual_review':True,'sections':['Complete supplied page read and visually inspected in the passed source audit; independently reopened for reader authoring.']}for p in d['pages']]}for d in I['documents']]
corp=next(x for x in read(S/'data/corpus/library-source.json')['papers']if x.get('doi','').lower()==F['doi'].lower())
counts={'reader_items':len(items),'source_audit_units':len(unit_items),'source_facts':len(sfmap),'records':len(R),'record_types':dict(Counter(r['record_type']for r in R.values())),'linked_operations':len(operation_map),'typed_characterization_rows':len(measurement_map),'operation_parameter_facts':len(parameter_map),'reagent_quantity_facts':len(material_map),'stock_quantity_facts':len(stock_map),'typed_facts':sum(len(x['facts'])for x in items.values()),'canonical_material_slots':len(material_slots),'canonical_stocks':sum(len(r.get('stocks',[]))for r in R.values()),'canonical_sample_contexts':len(sample_map),'source_object_bindings':len(object_map),'main_figures':6,'si_figures':2,'figures':8,'original_assets':len(assets),'tables':0,'schemes':0,'numbered_equations':0,'references':25,'numbered_reference_groups_excluding_note11':21,'substantive_reference_notes':1,'supplied_main_pages':5,'matched_si_pages':3}
gaps=[x['scope']+': '+x['missing']+' '+x['impact']for x in F['gaps']]
polymers=[P+x for x in ['polymer-preparation','aldehyde-polymer','biotin-polymer']]
cds=[rid for rid in R if rid not in polymers]
out={'schema_version':'1.0','paper_id':SID,'source_group':SID,'doi':F['doi'],'title':F['title'],'paper':{'authors':F['authors'],**F['bibliography']},'corpus_paper_id':corp['id'],'corpus_document_id':corp['titleMetadata']['evidenceDocumentId'],'corpus_document_ids':corp['documentIds'],'review_scope':'supplied_main_and_matched_si','supporting_information':{'status':'matched_and_reviewed','matched_local_si_count':1,'scientific_pages':3,'administrative_cover_pages':0,'scope':'TEM and XRD declaration, embedded manuscript identity and actual contents support independently audited pairing; all supplied main/SI pages reviewed.'},'documents':docs,'document_identity_verification':{'method':'Actual title/authors/DOI, manuscript identity and content-based main/SI match; unchanged SHA256 values bound to passed independent source and canonical audits.'},'coverage_status':'private_reader_proposal_pending_independent_audit','independent_audit':'Source extraction and canonical scientific audits passed separately. This reader, its figure/sample associations and presentation await independent review.','publication_status':'Private proposal; not integrated or published.','source_review_promoted':False,'training_eligible':False,'training_note':'One representative CdS route and one incompletely quantified biotin variant; polymer procedures, controls and assays are separately scoped. No recipe–exact-structure label or task admission is granted.','recipe_inventory':[{'id':rid,'label':r['title'],'record_ids':[rid],'record_type':r['record_type'],'status':'canonical_source_audit_passed_reader_pending','scope':LIMIT,'gaps':gaps if rid in [P+'cho-cds',P+'biotin-cds']else ['Viewer bindings and presentation review pending.'],'canonical_draft_present':True}for rid,r in R.items()],'characterization_inventory':{'reader_item_ids':[x['id']for s in sections if s['id']in['structures','properties']for x in s['items']]},'chemical_intuition':{'reader_item_ids':[x['id']for s in sections if s['id']=='intuition'for x in s['items']],'scope':'Original author explanations and proposed applications retain hypothesis status; no external full-text evidence has been imported.'},'reader_contract':{'version':'1.0','section_ids':[s['id']for s in sections],'item_fields':['id','title','text','claim_type','sample_scope','evidence','source_locators','canonical_links','notes','facts','training_eligible']},'reader_sections':sections,'figures':assets,'tables':[],'schemes':[],'equations':[],'source_notes':[],'referenced_methods':[{'id':x['id'],'citation':x['bibliography_as_printed_normalized_spacing'],'context':x['use_in_current_paper'],'inspection_status':x['access_level'],'reader_item_id':x['id']}for x in F['references']],'remaining_gaps':gaps+['Molecular, polymer, protein, apparatus and crystal-reference bindings remain pending; no source-specific 3D geometry is approved by this proposal.'],'evidence_conflicts':[{'id':x['id'],'text':items['conflict-'+x['id']]['text'],'handling':x['resolution'],'source_locators':items['conflict-'+x['id']]['source_locators']}for x in F['contradictions']],'record_formulation_labels':{rid:[p['sample_id']for p in r['products']]for rid,r in R.items()},'record_formulation_scope_note':LIMIT,'material_evidence_records':{'CdS':cds,'PEG/PAMA':[P+'polymer-preparation'],'CHO-PEG/PAMA':[P+'aldehyde-polymer'],'biotin-PEG/PAMA':[P+'biotin-polymer']},'material_evidence_scope_notes':{'CdS':'Polymer-stabilized CdS routes with separately scoped spectroscopy, structural specimens, controls and assays. Generic SI structure cannot be relabeled as specifically biotin-ended.','PEG/PAMA':'Upstream polymer-only preparation; not CdS or measured atomistic polymer geometry.','CHO-PEG/PAMA':'Aldehyde end-group preparation context. CdS measurements do not describe the isolated polymer.','biotin-PEG/PAMA':'Biotin-functional polymer preparation before CdS synthesis; molecular and protein structural bindings remain pending.'},'material_original_asset_ids':{'CdS':[a['id']for a in assets],'PEG/PAMA':[],'CHO-PEG/PAMA':[],'biotin-PEG/PAMA':[]},'material_asset_scope_note':'All original CdS figures retain their panel and sample labels; polymer-only routes do not inherit CdS structure or biological-assay measurements.','route_evidence_contexts':{P+'cho-cds':polymers[:2]+[P+x for x in ['stabilizer-controls','concentration-series','salt-challenge','optical','zeta','tem','xrd','chemical-intuition','source-context']],P+'biotin-cds':polymers+[P+x for x in ['optical','fret','recognition-controls','chemical-intuition','source-context']]},'counts':counts}
write('nagasaki2004.json',out)
write('source-item-coverage.json',{'source_id':SID,'source_inventory_sha256':sha(B/'source-inventory.json'),'source_facts_sha256':sha(B/'source-facts.json'),'canonical_coverage_sha256':sha(B/'canonical-source-coverage.json'),'mapped_unit_count':len(unit_items),'unit_to_reader_items':unit_items,'unmapped_units':[],'fact_to_reader':sfmap,'source_objects_to_reader':object_map})
write('canonical-measurement-coverage.json',{'measurement_count':len(measurement_map),'measurement_to_reader_item':measurement_map,'operation_count':len(operation_map),'operation_to_reader_item':operation_map,'operation_original_descriptions':{rid+'::'+o['id']:o['description']for rid,r in R.items()for o in r['operations']},'operation_parameter_count':len(parameter_map),'operation_parameter_to_reader_item':parameter_map,'material_quantity_count':len(material_map),'material_quantity_to_reader_item':material_map,'stock_quantity_count':len(stock_map),'stock_quantity_to_reader_item':stock_map,'canonical_material_slots':material_slots,'canonical_sample_contexts':sample_map,'draft_sha256':{rid:sha(B/'canonical-drafts'/f'{rid}.json')for rid in R}})
write('reader-bindings-proposal.json',{'schema':'mattersyn-private-reader-bindings/1','source_id':SID,'status':'proposed_not_approved','reader_sha256':sha(O/'nagasaki2004.json'),'canonical_records':{rid:sha(B/'canonical-drafts'/f'{rid}.json')for rid in R},'original_assets':private_assets,'operation_to_reader_item':operation_map,'molecular_or_apparatus_bindings_approved':False,'publication_approved':False})
write('reader-items-summary.json',[{'id':x['id'],'title':x['title'],'section':s['id'],'source_unit_ids':x['source_audit_unit_ids'],'facts':len(x['facts'])}for s in sections for x in s['items']])
write('reader-authoring-inputs.json',{'source_id':SID,'created_at':datetime.now(timezone.utc).isoformat(),'input_hashes':frozen,'reader_original_text_pages':{'main':[1,2,3,4,5],'si':[1]},'reader_visual_pages':{'main':[1,2,3,4,5],'si':[1,2,3]},'si_scanned_figure_pages':[2,3],'scope':'Reader authoring and source reinspection, not an independent audit. All source facts and canonical links derive from frozen audited package.'})
assert all(sha(p)==h for p,h in frozen.items()),'Frozen inputs changed during reader authoring.'
print(json.dumps(counts,ensure_ascii=False))
