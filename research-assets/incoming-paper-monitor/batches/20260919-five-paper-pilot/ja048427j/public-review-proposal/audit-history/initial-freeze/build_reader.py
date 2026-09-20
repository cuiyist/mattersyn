"""Private Norberg academic reader. No Site, source or canonical record writes."""
from pathlib import Path
from collections import Counter,defaultdict
from copy import deepcopy
from datetime import datetime,timezone
import hashlib,json,re,sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;B=O.parent
SITE=Path(r'[local path redacted]');SID='norberg2004';PRE='norberg-2004-'
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(n,d):(O/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def norm(x):return re.sub('[^a-z0-9]+','-',x.lower()).strip('-')
def uniq(x):return list({json.dumps(i,sort_keys=True,ensure_ascii=False):i for i in x}.values())
def resolve(o,p):
    for s in p.strip('/').split('/') if p else []:
        s=s.replace('~1','/').replace('~0','~');o=o[int(s)] if isinstance(o,list) else o[s]
    return o
def esc(s):return s.replace('~','~0').replace('/','~1')
I=read(B/'source-inventory.json');F=read(B/'source-facts.json');COV=read(B/'canonical-source-coverage.json');MAN=read(B/'canonical-record-manifest.json');AUD=read(B/'canonical-records-audit.json');SA=read(B/'source-scientific-audit.json');PC=read(B/'page-coverage.json');AM=read(B/'reader-assets/asset-manifest.json')
assert AUD['status']=='passed' and AUD['manifest_sha256']==sha(B/'canonical-record-manifest.json')
assert SA['status']=='passed'
R={m['record_id']:read(m['path']) for m in MAN['records']}
for m in MAN['records']:assert sha(m['path'])==m['sha256']==AUD['record_hashes'][m['record_id']]
FROZEN={str(p):sha(p) for p in [B/'source-inventory.json',B/'source-facts.json',B/'canonical-source-coverage.json',B/'canonical-record-manifest.json',B/'canonical-records-audit.json',B/'source-scientific-audit.json',B/'page-coverage.json',B/'reader-assets/asset-manifest.json']+list((B/'canonical-drafts').glob('*.json'))}
SECTIONS=[{'id':i,'title':t,'items':[]} for i,t in [('precursors','Precursors'),('protocol','Synthesis protocol'),('structures','Final structures'),('properties','Properties'),('intuition','Chemical intuition'),('sources','Sources and limitations')]]
ITEMS={};UNIT_ITEMS={u['source_unit_id']:[] for u in COV['source_units']};OBJ_ITEMS={};PTR_ITEM={};DISPLAY={}
MATS={m['id']:m for m in I['materials']};PRO={p['id']:p for p in I['protocols']};ST={s['id']:s for s in I['stocks']};SAMPLES={s['id']:s for s in I['samples']};GAPS={g['id']:g for g in I['gaps']};ASSETS={a['id']:a for a in AM['assets']}
OBJ={}
for category in ['materials','stocks','protocols','samples','figures_tables_schemes','equations','tables','chemical_intuition','references','gaps','other_source_content']:
    for n,obj in enumerate(I[category]):OBJ[(category,obj.get('id',obj.get('kind',str(n))))]=(n,obj)
SCOPES={'source_cohort':'Source specimen, state or comparison group. Repeated labels do not establish identical physical aliquots across all techniques.','method_context':'Preparation or acquisition context with explicit missing conditions. A procedure is not a separate synthesis replicate.','model_context':'Author model, fit, interpretation or hypothesis. It is not a direct atomic structure, measured mechanism or new synthesis.','cited_context':'Cited reference-system context. The cited full works were not inspected as part of this supplied-source review.','source_metadata':'Source identity, citation, note or coverage information; not an experimental result.','curator_interpretation':'Source limitation or discrepancy retained without silently filling or reconciling historical fields.'}
RECORD_SEC={'hydrolysis':'protocol','amine-cleaning':'protocol','surface-control':'protocol','titration':'protocol','topo':'protocol','films-a-c':'protocol','films-d-f':'properties','oxidation-controls':'precursors','growth-series':'protocol','structure':'structures','optical':'properties','magnetism':'properties','epr-model':'intuition','charge-transfer-model':'intuition','dopant-statistics':'intuition','reagent-properties':'precursors','acquisition-methods':'properties','chemical-intuition':'intuition','source-context':'sources'}
def ce(es):
    out=[]
    for e in es:
        match=re.search(r'(Main|SI) PDF p\. (\d+)',e.get('locator',''));role='si' if match and match[1]=='SI' else 'main';n=int(match[2]) if match else None
        out.append({'source_id':SID,'document_role':role,'pdf_page':n,'printed_page':('S-'+str(n) if role=='si' else str(9386+n)) if n else None,'locator':e.get('locator','Supplied source scope')})
    return out
def se(es):
    return [{'source_id':SID,'document_role':e.get('source_role','si' if e.get('source_id','').endswith('-si') else 'main'),'pdf_page':e['pdf_page'],'printed_page':e.get('printed_page'),'locator':e.get('locator','Source text')} for e in es]
def unit_evidence(uid):
    es=[]
    for (cat,key),(n,obj) in OBJ.items():
        if key==uid:es+=se(obj.get('evidence',[]))
    for f in F['facts']:
        if f['source_unit_id']==uid:es+=se(f['evidence'])
    if not es:
        for u in COV['source_units']:
            if u['source_unit_id']==uid:
                for b in u['canonical_bindings']:
                    q=resolve(R[b['record_id']],b['pointer'])
                    if isinstance(q,dict):es+=ce(q.get('evidence',q.get('link_evidence',[])))
    return uniq(es) or [{'source_id':SID,'document_role':'main','pdf_page':None,'printed_page':None,'locator':'Supplied main and matched SI: '+uid}]
def add(sec,key,title,text,units=None,scope='source_cohort',claim='reported_source_fact',ev=None):
    assert key not in ITEMS,key
    units=units or [];es=uniq((ev or [])+[e for u in units for e in unit_evidence(u)])
    ii={'id':key,'title':title,'text':text,'claim_type':claim,'sample_scope':{'formulations':[],'physical_batch_id':None,'scope_kind':scope,'state':title,'link_limit':SCOPES[scope],'canonical_sample_links':[]},'evidence':es,'source_locators':[e['locator'] for e in es],'canonical_links':[],'notes':[],'facts':[],'source_audit_unit_ids':units,'source_fact_ids':[],'original_assets':[],'training_eligible':False}
    ITEMS[key]=ii;next(s for s in SECTIONS if s['id']==sec)['items'].append(ii)
    for u in units:
        if u in UNIT_ITEMS:UNIT_ITEMS[u].append(key)
    return key
ACADEMIC={
'protocol-hydrolysis':('Common hydrolysis and condensation route','Prepare the combined Mn/Zn acetate solution in DMSO and add ethanolic tetramethylammonium hydroxide dropwise under constant stirring at room temperature. Initial growth occurs over minutes. Subsequent ambient ripening over several days and heating near 60 °C are alternatives. The initial precipitation, iterative washing, dodecylamine capping and toluene transfer remain distinct stages. Absolute scale and several workup conditions are not reported.'),
'protocol-amine-cleaning':('Dodecylamine surface cleaning','Heat the capped colloids in dodecylamine at 180 °C for approximately 30 min under nitrogen, cool strictly below 80 °C, precipitate and wash with ethanol, and redisperse in toluene or another nonpolar solvent. The authors associate this treatment with removal of surface-exposed Mn and further ripening. Initial capping is a separate, incompletely specified operation.'),
'protocol-surface-control':('Deliberately surface-bound Mn control','Prepare pure ZnO without manganese feed, wash and resuspend it in ethanol, then add a small manganese acetate charge and ethanolic LiOH. Wash, cap with dodecylamine and transfer into toluene for EPR. This deliberately surface-bound reference does not receive the later 180 °C surface-stripping treatment. The LiOH concentration and equivalent reference are not stated.'),
'protocol-titration':('Base-addition titration and spectral aliquots','The 2% Mn/98% Zn feed titration follows successive base additions. The absorption onset and clouding observations belong to this progression. An aliquot is measured, diluted 70-fold and remeasured; these two spectral scales do not create independent synthesis experiments. The 1.65-equivalent solid trace is distinct from the common preparation using 1.7 equivalents.'),
'protocol-topo':('Alternative TOPO treatment and MCD specimen','The alternative treatment heats nanocrystals in technical-grade TOPO following reference 32. Its temperature, duration and amounts are not restated. TOPO-capped 1.1% Mn colloids are drop-coated on quartz disks as frozen solutions for MCD. No dodecylamine treatment condition or 0.20% specimen identity is transferred to this sample.'),
'protocol-films':('Film A–C coating and annealing','Spin-coat the dodecylamine-treated 0.20 ± 0.01% Mn colloids onto 1 × 0.5 cm fused silica. Anneal in air at 525 °C for two minutes after each deposited layer. A has 40 layers; B and C have 20 each. Films D–F retain separate SI outcomes because their individual coating counts, parent batches and annealing details are not independently restated.'),
'protocol-oxidation-controls':('Manganese precursor oxidation controls','Compare the manganese acetate solution in DMSO under air, with added zinc acetate, under anaerobic conditions, with sodium acetate, or with manganese nitrate replacing the acetate salt. The solutions are separate controls, not ingredients combined into one synthesis. The five-day absorption observations preserve both inhibition and negative results; the anaerobic gas and measured pH are unreported.'),
'cleaned-0.20pct':('Measured 0.20% Mn colloids','A 0.50% initial Mn feed gives a product containing 0.20 ± 0.01% Mn by ICP-AES after amine treatment. The same identified colloid supports the reported microscopy and film A precursor relationship. Nominal Zn0.998Mn0.002O is not a refined occupancy model. TEM, Scherrer and absorption-derived sizes remain separate estimands.'),
'cleaned-0.20pct-powder':('Rapidly precipitated 0.20% Mn powder','The free-standing powder is prepared by rapid precipitation from the toluene colloid. Powder XRD and magnetometry refer to this material state. Individual physical aliquot identities are not supplied. The wurtzite assignment and Scherrer size do not provide atomic coordinates or a CIF.'),
'growth-0.02pct-series':('0.02% Mn feed growth progression','The early aliquot, later heated aliquot and cleaned product form one growth progression. The 0.02% label is explicitly feed-based or nominal; a final sample-specific ICP concentration is not stated. Later material is not made by recycling an earlier analyzed aliquot.'),
'growth-02-b':('Early growth aliquot b','The early washed and capped specimen is taken ten minutes after base addition. Its approximately 4.0 nm diameter is estimated from absorption. Its surface-dopant fraction is a statistical estimate, not a directly counted atomic population.'),
'growth-02-c':('Later growth aliquot c','The original reaction continues for two hours at 60 °C before the later specimen is taken. Its approximately 5.6 nm diameter is absorption-derived. The specimen does not consume the already measured early aliquot.'),
'growth-02-d':('Amine-treated growth specimen d','The washed later-growth nanocrystal product is treated at 180 °C for 30 min in the specific specimen description. Figure 5 corresponds to Figure 2d. Hyperfine splitting is measured from the spectrum; g, A, D and D-strain are fitted parameters with a separate model basis.'),
'surface-control-epr':('Surface-bound Mn EPR reference','This deliberately surface-doped ZnO control defines the broad surface-bound EPR comparison. The approximately 2% addition is a precursor charge relative to Zn, not an ICP product composition or an internal Mn fraction.'),
'topo-1.1pct':('TOPO-capped 1.1% Mn absorption and MCD','The absorption/MCD specimen is explicitly the TOPO-capped 1.1% sample. Its initial Mn feed and sample-specific concentration uncertainty are not given. A frozen drop-coated solution is distinct from the spin-coated ferromagnetic films. The field-dependent curve and Brillouin comparison remain separate measured and model information.'),
'optical-pure-zno':('Undoped ZnO optical control','The undoped, dodecylamine-treated ZnO optical specimen provides the visible and ultraviolet emission reference. Its physical batch is not automatically identical to the undoped material used to prepare the surface-bound Mn control.'),
'optical-0.13pct':('Estimated 0.13% Mn optical specimen','The lower-dopant optical specimen is reported at an estimated 0.13% Mn. Visible and ultraviolet quenching are relative to the undoped reference. The SI statistics use an assumed uniform particle size; they do not establish measured dopant counts.'),
'optical-1.3pct':('Reported 1.3% Mn optical specimen','The higher-dopant optical specimen is reported at 1.3% Mn without a sample-specific ICP uncertainty. Visible emission is strongly quenched. The weak remaining ultraviolet intensity may be scattering rather than an excitonic feature; that source qualification is retained.'),
'optical-series':('Optical normalization and negative emission result','The undoped, estimated 0.13% and reported 1.3% specimens remain distinct. Absorption is normalized at the excitation energy and emission scaled proportionally. Mn ligand-field emission was not observed: this is a reported negative observation, not an unperformed measurement.'),
'films-a-b-c':('Collective magnetic results for films A–C','Collective remanence and coercivity statistics apply to the film set. Tc exceeds the instrument ceiling of 350 K; the transition temperature was not measured exactly. These statistics do not create additional preparation replicates.'),
'films-a-b':('Zero-field-cooled measurements of films A and B','The ZFC series at 80 Oe shows no transition within 5–350 K. The authors use this behavior when discussing impurity alternatives, without establishing a universal impurity-detection limit.'),
'ct-model':('Tentative charge-transfer assignment','Ligand-field and optical-electronegativity models compare possible assignments for the sub-bandgap absorption. The authors tentatively favor Mn²⁺ to conduction-band charge transfer while retaining an intensity-based alternative. Estimated parameters and predicted energies are not direct measurements of the nanocrystal interface or electronic structure.'),
'bulk-mn-zno-reference':('Bulk Mn:ZnO EPR reference constants','Parallel and perpendicular bulk reference constants are cited for comparison with the powder-averaged nanocrystal fit. They are not newly measured nanocrystal parameters.'),
'theory-context':('Cited carrier-density prediction','The p-type carrier concentration belongs to cited theoretical work. Carrier polarity and density were not measured for these films.'),
'solubility-reference':('Cited manganese solubility conditions','The cited solubility comparison at 525 °C and 1 kbar is a different experimental system. One kilobar is not assigned as the annealing pressure of the present films.'),
'oxidation-reference':('Cited high-temperature oxygen-pressure comparison','The oxygen-pressure bound for maintaining MnO at 900 °C is literature context, not a condition for this room-temperature colloidal synthesis.'),
'zno-reference':('ZnO exciton reference length','The cited ZnO Bohr radius provides context for weak quantum confinement. It is not a measured particle radius in this preparation.'),
'spectral-aliquots':('Spectral remeasurement of titration aliquots','A 70-fold dilution allows weak and intense bands to be observed on different scales. The remeasurement is tied to the same withdrawn aliquot; it is not a separate synthesis or a general dilution required for every absorption spectrum.'),
'cleaned-final-colloids':('Final colloidal dispersion and storage limitation','The cleaned product forms optically high-quality dispersions in toluene or other nonpolar solvents, reported stable for several months. Storage temperature, atmosphere and illumination are not specified.'),
'oxidation-controls':('Five-day precursor stability comparison','The manganese acetate concentration, five-day aging period and absorption probe define the solution-control experiment. It is separate from the nanocrystal synthesis, despite using some of the same precursor chemicals.'),
'oxidation-air':('Manganese acetate aged in air','The initially colorless manganese acetate solution in DMSO becomes brown after five days in air, with a broad absorption tail and shoulder near 20,000 cm⁻¹. No precise oxide stoichiometry is established.'),
'oxidation-zinc-series':('Zinc acetate inhibition series','Increasing the Zn:Mn ratio suppresses the brown absorption intensity, with near-complete inhibition around a 3:1 ratio. The full set of raw absorbance points has not been digitized.'),
'oxidation-anoxic':('Anaerobic oxidation control','The anaerobic manganese acetate solution shows reduced discoloration relative to air. The gas identity and handling details are not stated.'),
'oxidation-naoac':('Sodium acetate oxidation control','Sodium acetate increases the absorption relative to the manganese acetate air control. This separate control does not supply sodium acetate to the ZnO synthesis.'),
'oxidation-nitrate':('Manganese nitrate substitution control','Replacing manganese acetate with manganese nitrate gives little or no discoloration after five days. Nitrate is a substitution control, not an additional synthesis reagent.')}
for letter in 'abcdef':
    uid='film-'+letter
    ACADEMIC[uid]=('Film '+letter.upper()+': preparation and outcome scope','Film '+letter.upper()+(' belongs to the A–C preparation with a stated coating count and per-layer air annealing. Main and SI masses are separately reported and consistent with rounding. Magnetic and structural measurements retain their own source conditions.' if letter in 'abc' else ' has SI mass and magnetization values, but its coating count, individual parent batch and independently restated annealing conditions are missing. The D/F curve-versus-table assignment conflict remains unresolved; printed values are retained without swapping labels.'))
TABLE_TITLES={'table-s1':'Table S1: cited ligand-field systems','table-s2':'Table S2: parameter estimates from literature ratios','table-s3':'Table S3: calculated transitions and cited ZnS comparison','table-s4':'Table S4: film A–F masses and saturation moments'}
ACADEMIC['titration-series']=('Titration-series source observations',ACADEMIC['protocol-titration'][1])
def unit_spec(uid):
    if uid in MATS:
        m=MATS[uid];return 'precursors',m['name'],m['name']+' is listed for '+', '.join(m['roles'])+'. '+('Formula: '+m['formula']+'. ' if m.get('formula') else 'No single molecular formula is assigned. ')+('Supplier: '+m['supplier']+'. ' if m.get('supplier') else 'Supplier is not reported. ')+(m.get('notes') or ''),'method_context'
    if uid in ST:
        s=ST[uid];names=', '.join(MATS[k]['name'] for k in s['components']);return 'precursors',names+' stock',names+' in '+MATS[s['solvent']]['name']+'. Absolute stock volume is not supplied. Concentration, composition and handling retain their exact source scope.','method_context'
    if uid in ACADEMIC:
        title,text=ACADEMIC[uid]
        if uid in PRO:sec='precursors' if uid=='protocol-oxidation-controls' else 'protocol';scope='method_context'
        elif uid.startswith(('growth-','spectral-','titration-','surface-control')):sec='protocol';scope='source_cohort'
        elif uid.startswith('cleaned-0.20'):sec='structures';scope='source_cohort'
        elif uid=='zno-reference':sec='structures';scope='cited_context'
        elif uid.startswith(('oxidation-','stock-')):sec='precursors';scope='source_cohort'
        elif uid in ['ct-model','bulk-mn-zno-reference','theory-context','solubility-reference','oxidation-reference']:sec='intuition';scope='model_context' if uid=='ct-model' else 'cited_context'
        else:sec='properties';scope='source_cohort'
        return sec,title,text,scope
    if uid.startswith('measurement-'):
        f=next(f for f in F['facts'] if f['source_unit_id']==uid);x=f['value'];return ('structures' if uid.endswith(('tem','icp','xrd-powder','xrd-film')) else 'properties'),x['technique']+' acquisition',x['technique']+' using '+x['instrument']+'. The original instrument settings and sample context appear below. Shared instrument descriptions do not establish the same physical aliquot across all techniques.','method_context'
    if uid in TABLE_TITLES:return ('properties' if uid=='table-s4' else 'intuition'),TABLE_TITLES[uid],('The table preserves each film’s printed mass and magnetic result at 300 K. Figure S3b orders D/F differently; both representations remain visible and unresolved.' if uid=='table-s4' else 'The complete printed table is retained with column-specific distinction between reference inputs, author estimates and calculated transitions. These numbers are not additional measurements of the synthesized Mn:ZnO particles.'),'source_cohort' if uid=='table-s4' else 'model_context'
    for category in ['figures_tables_schemes','equations','references']:
        if (category,uid) in OBJ:
            obj=OBJ[(category,uid)][1]
            if category=='references':return 'sources',('SI' if obj['source_role']=='si' else 'Main')+' reference '+str(obj['reference_number']),obj.get('bibliography_extracted_text',obj.get('bibliography_transcription')),'cited_context'
            if category=='equations':return 'intuition' if uid!='mcd-definition' else 'properties',('MCD normalization' if uid=='mcd-definition' else uid.replace('-',' ').capitalize()),obj['meaning'],'model_context' if uid!='mcd-definition' else 'method_context'
            sec='structures' if uid=='figure-3' else 'protocol' if uid in ['figure-1','figure-2'] else 'precursors' if uid=='figure-4' else 'intuition' if uid in ['figure-5','figure-s1-equations','scheme-1'] else 'properties'
            return sec,obj.get('title',uid.replace('-',' ').capitalize()),{'figure-1':'Panel a follows base titration; panel b compares the identified 0.20% colloid with film A. The two panels are separate experiments.','figure-2':'The surface-bound reference and growth aliquots b–d retain their separate preparation histories.','figure-3':'Powder/film XRD, the TEM size histogram and HRTEM spacings retain their panel-specific specimen and technique scopes.','figure-4':'Chemical and atmospheric controls of manganese precursor oxidation, not nanocrystal phase analysis.','figure-5':'Measured X/Q-band spectra and model traces remain explicitly distinct. D-strain is a fit parameter, not refined atomic geometry.','figure-6':'Absorption and MCD of the TOPO-capped 1.1% specimen, with measured field dependence and a Brillouin comparison.','figure-7':'Absorption and normalized emission of three distinct optical specimens, including negative Mn ligand-field emission.','figure-8':'Colloid powder and films A–C have distinct magnetic behavior. The S > 800 estimate applies collectively, not to film A alone.','figure-9':'ZFC and paramagnetic residual data retain field, temperature and Brillouin-model distinctions.','figure-10':'The original precursor-colloid and film A EPR spectra include a new sharp film resonance with a tentative interpretation.','figure-s1-equations':'Calculated dopant-number distributions assume uniform 6.5 nm particles. The printed statistical notation remains ambiguous.','figure-s2':'Temperature-dependent film A–C hysteresis parameters do not locate Tc within the measurement window.','figure-s3':'The six printed film curves are preserved. The D/F ordering in the mass-normalized panel disagrees with Table S4.','scheme-1':'The authors propose inhibition of manganese oxidation by zinc acetate. The schematic is not a measured mechanistic intermediate.'}.get(uid,obj.get('notes','Source evidence with original scope retained.')),'model_context' if uid in ['figure-5','figure-s1-equations','scheme-1'] else 'source_cohort'
    if uid.startswith('context-'):
        f=next(f for f in F['facts'] if f['source_unit_id']==uid);return 'intuition',f['property'],f['property']+' is cited or assumed context. It is not a measured outcome of the present nanocrystal or film specimens.','model_context' if f['status'].startswith('author_') else 'cited_context'
    raise AssertionError(('Missing academic source-unit label',uid))
for u in COV['source_units']:
    uid=u['source_unit_id'];sec,title,text,scope=unit_spec(uid);key=add(sec,'u-'+norm(uid),title,text,[uid],scope)
    for b in u['canonical_bindings']:ITEMS[key]['canonical_links'].append({'record_id':b['record_id'],'json_pointer':b['pointer'],'relation':SCOPES[scope]})
def uid_item(uid):return UNIT_ITEMS[uid][0]
for (cat,key),(n,obj) in OBJ.items():
    if key in UNIT_ITEMS:iid=uid_item(key)
    elif cat=='chemical_intuition':iid=add('intuition','intuition-'+norm(key),{'homogeneous-feed':'Composition control by solution chemistry','induction':'Nucleation induction and precursor clusters','amine-clean':'Surface cleaning and concurrent ripening','air-protection':'Proposed inhibition of Mn oxidation','dstrain':'Interpreting the EPR D-strain','ct':'Tentative charge-transfer assignment','luminescence':'Proposed emission-quenching pathways','ferromagnetism':'Evidence and alternatives for film ferromagnetism','carrier-hypothesis':'Unverified carrier and nitrogen hypotheses'}[key],obj['claim'],scope='model_context',claim=obj['classification'],ev=se(obj['evidence']))
    elif cat=='gaps':iid=add('sources','gap-'+norm(key),obj['scope'],obj['issue']+' '+obj['resolution'],scope='curator_interpretation',ev=[{'source_id':SID,'document_role':'main','pdf_page':None,'printed_page':None,'locator':'Complete supplied main and SI source review; '+obj['scope']}])
    elif cat=='other_source_content':iid=add('sources','note-'+norm(key),{'acknowledgment':'Acknowledgments and research support','copyright/accessfooter':'Source copyright and access footer','unpublishedreference60':'Unpublished comparison in reference 60'}[key],{'acknowledgment':'Funding and instrument assistance are reported in the acknowledgment. They are source context, not experimental conditions.','copyright/accessfooter':'The original source footer is retained as publication metadata. It does not supply an experimental method.','unpublishedreference60':'Reference 60 describes an unpublished Co:ZnO comparison. No independently available experiment is extracted from that citation.'}[key],scope='source_metadata',ev=se(obj['evidence']))
    else:raise AssertionError((cat,key))
    OBJ_ITEMS[(cat,key)]=iid
    for b in COV['source_objects']:
        if b['category']==cat and b['source_object_id']==key:
            ITEMS[iid]['canonical_links'].append({'record_id':b['record_id'],'json_pointer':b['pointer'],'relation':'Exact source-object destination; original classification and specimen scope are preserved.'})
            PTR_ITEM[(b['record_id'],b['pointer'])]=iid
for u in COV['source_units']:
    for b in u['canonical_bindings']:PTR_ITEM.setdefault((b['record_id'],b['pointer']),uid_item(u['source_unit_id']))

def record_item(rid):
    key='record-'+rid.removeprefix(PRE)
    if key not in ITEMS:
        r=R[rid];suffix=rid.removeprefix(PRE)
        add(RECORD_SEC[suffix],key,r['title'].split(' · ',1)[1],r['method']+'. This is a '+('common source preparation' if r['record_type']=='literature_protocol' else 'separate supporting procedure or evidence context')+'. Specimen identities and missing conditions remain explicit.',scope='method_context',ev=ce(r['sources'] and [{'source_id':SID,'locator':'Supplied main and matched SI, source-scoped record'}]))
        ITEMS[key]['canonical_links'].append({'record_id':rid,'json_pointer':'','relation':'Exact audited source record; one record is not necessarily a separate synthesis experiment.'})
    return key
def display(q):
    if q.get('value') is not None:return q['value']
    lo,hi=q.get('minimum'),q.get('maximum')
    if lo is not None and hi is not None:return f'{lo:g}–{hi:g}'
    if lo is not None:return ('> ' if q.get('minimum_exclusive') else '≥ ')+f'{lo:g}'
    if hi is not None:return ('< ' if q.get('maximum_exclusive') else '≤ ')+f'{hi:g}'
    return 'Not reported' if q.get('status')=='not_reported' else q.get('raw_text') or q.get('status','Unspecified')
def attach(iid,rid,ptr,label,q,ev,sid=None,basis='source_record_field',extra='',kind='exact_quantity',display_override=None):
    assert (rid,ptr) not in DISPLAY,('Displayed twice',rid,ptr)
    value=display(q) if display_override is None else display_override
    f={'id':rid+'::'+ptr,'label':label,'value':value,'unit':q.get('unit'),'approximate':q.get('approximate',False),'status':q.get('status'),'basis':basis,'qualifier':' '.join(x for x in [q.get('basis',''),q.get('qualifier',''),q.get('note',''),extra] if x),'evidence':ce(ev),'canonical_record_id':rid,'json_pointer':ptr,'canonical_quantity':deepcopy(q),'presentation_kind':kind,'training_eligible':False}
    if sid:f['sample_id']=sid
    ii=ITEMS[iid];ii['facts'].append(f);ii['canonical_links'].append({'record_id':rid,'json_pointer':ptr,'relation':SCOPES[ii['sample_scope']['scope_kind']]});ii['evidence']=uniq(ii['evidence']+f['evidence']);ii['source_locators']=uniq(ii['source_locators']+[e['locator'] for e in f['evidence']]);DISPLAY[(rid,ptr)]=(iid,f)
    return f
OPS={};OPPARAM={};MEASURE={};MATERIAL={};MATQ={};STOCKS={};STOCKQ={};PRODUCTS={};PRODQ={};OPTIONS={};ENV={}
# Every operation has its own source-stage card and exact operation JSON pointer.
for rid,r in R.items():
    for n,op in enumerate(r['operations']):
        ptr=f'/operations/{n}';iid='operation-'+op['id'];sec=RECORD_SEC[rid.removeprefix(PRE)]
        if op['stage']=='characterization' and sec=='protocol':sec='properties'
        if rid.endswith('acquisition-methods') and any(s in op['id'] for s in ['-tem','-icp','-xrd']):sec='structures'
        units=[u['source_unit_id'] for u in COV['source_units'] if any(b['record_id']==rid and b['pointer']==ptr for b in u['canonical_bindings'])]
        add(sec,iid,op['label'],op['description'],units,'method_context','source_operation',ce(op['evidence']))
        ii=ITEMS[iid];ii['canonical_links'].append({'record_id':rid,'json_pointer':ptr,'relation':'Exact source operation, with stage-specific inputs, outputs, conditions and retained fraction.'})
        labels={m['id']:m['name'] for m in r['materials']}|{s['id']:s['name'] for s in r['stocks']}|{s['id']:s['name'] for s in r['material_states']}
        ii['operation_context']={'record_id':rid,'operation_id':op['id'],'json_pointer':ptr,'stage':op['stage'],'branch':op['branch'],'depends_on':deepcopy(op['depends_on']),'environment':deepcopy(op['environment']),'inputs':deepcopy(op['inputs']),'optional_inputs':deepcopy(op.get('optional_inputs',[])),'outputs':deepcopy(op['outputs']),'retained_fraction':op['retained_fraction'],'endpoint':deepcopy(op['endpoint']),'material_flow_labels':{k:labels[k] for k in op['inputs']+op.get('optional_inputs',[])+op['outputs']},'diagram_binding_status':'pending_independent_visual_binding','condition_options':deepcopy(r['condition_options'])}
        ii['notes'].append('Inputs: '+', '.join(labels[k] for k in op['inputs'])+'.')
        if op.get('optional_inputs'):ii['notes'].append('Alternative inputs across separate controls: '+', '.join(labels[k] for k in op['optional_inputs'])+'. These are not all charged together.')
        ii['notes'].append('Output: '+', '.join(labels[k] for k in op['outputs'])+'.')
        if op['retained_fraction']:ii['notes'].append('Retained fraction: '+labels[op['retained_fraction']]+'.')
        OPS[rid+'::'+op['id']]=iid;PTR_ITEM[(rid,ptr)]=iid
        for name,q in op['parameters'].items():
            p=ptr+'/parameters/'+esc(name);f=attach(iid,rid,p,name.replace('_',' ').capitalize(),q,q.get('evidence',op['evidence']),basis='operation_parameter');f.update(canonical_operation_id=op['id'],canonical_parameter=name);OPPARAM[rid+'::'+op['id']+'::'+name]=iid
        for name in ['environment','endpoint']:
            q=op[name];p=ptr+'/'+name;attach(iid,rid,p,'Atmosphere' if name=='environment' else 'Endpoint',q,q.get('evidence',op['evidence']),basis='operation_'+name);ENV[rid+'::'+op['id']+'::'+name]=iid
    for n,m in enumerate(r['materials']):
        iid=uid_item(m['id']) if m['id'] in UNIT_ITEMS else record_item(rid);ptr=f'/materials/{n}';MATERIAL[rid+'::'+m['id']]=iid
        ii=ITEMS[iid];ii['canonical_links'].append({'record_id':rid,'json_pointer':ptr,'relation':'Source material or preformed specimen; formula does not supply molecular coordinates.'})
        ii.setdefault('material_identities',[]).append({'source_material_id':m['id'],'name':m['name'],'formula':m['formula'],'role':m['role'],'canonical_record_id':rid,'json_pointer':ptr,'exact_molecular_asset_binding_approved':False})
        ii['notes']+=m['notes']
        if m['id'] not in MATS:ii['notes'].append('Specimen or input identity: '+m['name']+('. Formula: '+m['formula'] if m['formula'] else '')+'.')
        for name,q in m['quantities'].items():
            f=attach(iid,rid,ptr+'/quantities/'+esc(name),m['name']+' · '+name.replace('_',' '),q,q.get('evidence',m['evidence']),basis='reagent_specification');f['canonical_material_id']=m['id'];MATQ[rid+'::'+m['id']+'::'+name]=iid
    for n,s in enumerate(r['stocks']):
        iid=uid_item(s['id']);ptr=f'/stocks/{n}';ii=ITEMS[iid];STOCKS[rid+'::'+s['id']]=iid
        ii['canonical_links'].append({'record_id':rid,'json_pointer':ptr,'relation':'Source stock, its solute/solvent components and exact concentration basis.'})
        ii.setdefault('stock_contexts',[]).append({'record_id':rid,'json_pointer':ptr,'stock_id':s['id'],'name':s['name'],'components':deepcopy(s['components']),'preparation_operation_ids':deepcopy(s['preparation_operation_ids']),'scope':s['scope'],'molecular_bindings_approved':False})
        ii['notes'].append(s['scope'])
        for name,q in s['concentrations'].items():attach(iid,rid,ptr+'/concentrations/'+esc(name),name.replace('_',' ').capitalize(),q,q.get('evidence',s['evidence']),basis='stock_concentration');STOCKQ[rid+'::'+s['id']+'::'+name]=iid
        for c,component in enumerate(s['components']):
            for name,q in component.get('quantities',{}).items():attach(iid,rid,ptr+f'/components/{c}/quantities/'+esc(name),component['material_id']+' · '+name,q,q.get('evidence',s['evidence']),basis='stock_component');STOCKQ[rid+'::'+s['id']+'::'+str(c)+'::'+name]=iid
    for n,option in enumerate(r['condition_options']):
        iid=record_item(rid);ptr=f'/condition_options/{n}';ii=ITEMS[iid];ii['notes'].append(option['label'])
        for name,q in option['parameters'].items():attach(iid,rid,ptr+'/parameters/'+esc(name),option['label']+' · '+name.replace('_',' '),q,q.get('evidence',option['evidence']),basis='separate_condition_option');OPTIONS[rid+'::'+option['id']+'::'+name]=iid

PAYLOAD={(b['record_id'],b['pointer']):(b['category'],b['source_object_id']) for b in COV['source_objects'] if b['mode']=='lossless_inventory_context_payload'}
def inventory_summary(cat,key,obj):
    iid=OBJ_ITEMS[(cat,key)]
    # Full scientific content stays in exact canonical_quantity and its JSON link;
    # academic prose replaces a machine JSON dump in the visible value only.
    text=ITEMS[iid]['text']
    if cat=='tables':return {'scope':text,'columns':obj['columns'],'rows':[' · '.join(str(v) for v in row) for row in obj['rows']],**({'final averages':obj['final_averages']} if 'final_averages' in obj else {})}
    if cat=='equations':return {'expression':obj['expression'],'meaning':obj['meaning'],'classification':obj['classification']}
    if cat=='protocols':return {'scope':text,'stages':[op['action'].replace('_',' ')+' — '+op['conditions'] for op in obj['operations']],'unreported':obj['missing_fields']}
    if cat=='materials':return {'chemical':obj['name'],'formula':obj.get('formula'),'roles':obj['roles'],'purity (%)':obj.get('purity_percent'),'supplier':obj.get('supplier'),'pretreatment':obj.get('pretreatment'),'source note':obj.get('notes') or 'No additional source note.'}
    if cat=='stocks':return {'solution':text,'solute components':[MATS[k]['name'] for k in obj['components']],'solvent':MATS[obj['solvent']]['name'],'concentration':obj.get('total_concentration',obj.get('concentration')),'volume':obj.get('volume'),'storage':obj.get('storage')}
    if cat=='samples':return {'scope':text,'source composition':obj.get('composition'),'source state':obj.get('state'),'linked items':obj.get('linked_items',[]),'link limitation':obj.get('link_status'),'additional limitation':obj.get('missing')}
    if cat=='gaps':return obj['issue']+' '+obj['resolution']
    if cat=='chemical_intuition':return obj['claim']
    if cat=='references':return obj.get('bibliography_extracted_text',obj.get('bibliography_transcription'))
    if cat=='figures_tables_schemes':return text
    return text
for rid,r in R.items():
    for n,m in enumerate(r['measurements']):
        ptr=f'/measurements/{n}/value';iid=PTR_ITEM.get((rid,ptr));assert iid,(rid,m['id'],'unmapped canonical measurement')
        if (rid,ptr) in PAYLOAD:
            cat,key=PAYLOAD[(rid,ptr)];obj=OBJ[(cat,key)][1];visible=inventory_summary(cat,key,obj);kind='academic_inventory_summary';label=ITEMS[iid]['title']+' · complete source entry'
        else:visible=None;kind='exact_quantity';label=m['property'].replace('_',' ').capitalize()
        f=attach(iid,rid,ptr,label,m['value'],m['evidence'],m['sample_id'],basis='canonical_'+m['value']['status'],extra=m.get('conditions',''),kind=kind,display_override=visible)
        f['canonical_measurement_id']=m['id'];MEASURE[rid+'::'+m['id']]=iid
        if kind=='academic_inventory_summary':f['source_inventory_identity']={'category':cat,'source_object_id':key}
    for n,p in enumerate(r['products']):
        ptr=f'/products/{n}';iid=uid_item(p['sample_id']) if p['sample_id'] in UNIT_ITEMS else record_item(rid);PRODUCTS[rid+'::'+p['sample_id']]=iid
        ii=ITEMS[iid];ii['canonical_links'].append({'record_id':rid,'json_pointer':ptr,'relation':'Exact specimen/context identity, not a verified independent batch.'})
        ii.setdefault('product_contexts',[]).append({'record_id':rid,'json_pointer':ptr,'sample_id':p['sample_id'],'source_label':p['source_sample_label'],'material_state_id':p['material_state_id'],'parent_sample_id':p['parent_sample_id'],'recipe_link':p['recipe_link'],'notes':deepcopy(p['notes']),'atomic_asset_binding_approved':False})
        for name in ['composition','phase','morphology','surface']:
            pp=ptr+'/'+name;q=p[name]
            if (rid,pp) in DISPLAY:continue
            attach(iid,rid,pp,p['sample_id'].replace('-',' ')+' · '+name,q,q.get('evidence',[]),basis='specimen_'+name);PRODQ[rid+'::'+p['sample_id']+'::'+name]=iid

# Exact fact and unit/object maps form a bridge from source through canonical data
# to visible reader entries. Numeric facts never bind to a prose-only replacement.
FACT_MAP={}
for entry in COV['facts']:
    fid=entry['source_fact_id'];unit=entry['source_fact']['source_unit_id'];out=[]
    for b in entry['canonical_bindings']:
        iid,f=DISPLAY[(b['record_id'],b['pointer'])];f.setdefault('source_fact_ids',[]).append(fid);ITEMS[iid]['source_fact_ids'].append(fid)
        out.append({**b,'reader_item_id':iid,'reader_fact_id':f['id']})
        assert f['presentation_kind']=='exact_quantity',(fid,'Source numerical fact must preserve exact display')
    FACT_MAP[fid]={'source_unit_id':unit,'reader_item_ids':uniq([uid_item(unit)]+[b['reader_item_id'] for b in out]),'canonical_bindings':out}
for ii in ITEMS.values():
    joins=[]
    for f in ii['facts']:
        if f.get('sample_id'):
            rid=f['canonical_record_id'];sid=f['sample_id'];pidx=next(n for n,p in enumerate(R[rid]['products']) if p['sample_id']==sid)
            joins.append({'record_id':rid,'sample_id':sid,'json_pointer':f'/products/{pidx}','source_label':R[rid]['products'][pidx]['source_sample_label'],'relation':SCOPES[ii['sample_scope']['scope_kind']]})
    ii['sample_scope']['canonical_sample_links']=uniq(joins);ii['sample_scope']['formulations']=[j['record_id']+' / '+j['sample_id'] for j in uniq(joins)]
    ii['canonical_links']=uniq(ii['canonical_links']);ii['notes']=uniq(ii['notes']);ii['source_fact_ids']=uniq(ii['source_fact_ids'])
    if len(ii.get('material_identities',[]))==1:ii['material_identity']=ii['material_identities'][0]

# Original assets retain their exact bytes, captions, axes and source-panel scopes.
GROUPS={k:[] for k in ['figures','tables','equations','schemes','source_notes']};PUBLIC_ASSETS={};PRIVATE_ASSETS=[]
FIGINV={x['id']:x for x in I['figures_tables_schemes']}
def sample_links(sids):
    links=[]
    for sid in sids:
        # Link each known record-scoped specimen without asserting those analytical
        # contexts are the same physical aliquot. No universal sample ID is used.
        for rid,r in R.items():
            for n,p in enumerate(r['products']):
                if p['sample_id']==sid:links.append({'record_id':rid,'sample_id':sid,'json_pointer':f'/products/{n}','relation':'Source specimen/material association; record-scoped context, not identical physical aliquots across all techniques.'})
    return links
def asset_item(a,key=None,group=None,label=None,sids=None,notes=None):
    key=key or a['id'];role=a['source_role'];page=a['pdf_page'];full=a['kind']=='full_page';public='assets/figures/norberg2004/'+Path(a['path']).name
    if full:public='assets/figures/norberg2004/pages/'+Path(a['path']).name
    desc=label or TABLE_TITLES.get(key) or (FIGINV[key].get('title') if key in FIGINV else None) or key.replace('-',' ').capitalize()
    links=sample_links(sids or []);group=group or ('figures' if key.startswith('figure-') else 'tables' if key.startswith('table-') else 'schemes' if key.startswith('scheme-') else 'equations' if key.startswith('equation-') else 'source_notes')
    model=key in ['figure-s1-equations','figure-5','scheme-1'] or group=='equations'
    entry={'id':SID+'-'+key,'label':desc,'document_role':role,'page':page,'printed_page':'S-'+str(page) if role=='si' else str(9386+page),'caption_paraphrase':desc,'sample_scope':('Complete original page; separate sections retain their own specimen, model and citation scopes.' if full else ITEMS[uid_item(key)]['text'] if key in UNIT_ITEMS else desc),'sample_links':uniq([j['record_id'] for j in links]),'canonical_sample_links':links,'sample_linkage':'Original panel/source associations; no universal physical batch or sample equality is inferred.','evidence_class':'author_model_or_measured_model_comparison' if model else 'direct_source_excerpt' if full or key in ['materials','sample-preparation'] else 'original_experimental_figure' if group=='figures' else 'source_table_with_column_specific_status','public_asset':public,'public_asset_sha256':a['sha256'],'asset_provenance':{'source_file':'10.1021_ja048427j'+('_si_1' if role=='si' else '')+'.pdf','source_sha256':a['source_sha256'],'source_pdf_page':page,'crop_pixel_bbox':(a.get('crop') or {}).get('bounds'),'source_page_dimensions':(a.get('crop') or {}).get('page_dimensions'),'render_dpi':AM['dpi'],'pixel_dimensions':a['dimensions'],'renderer':AM['render_engine'],'transformation':'Original rendered source page or rectangular crop; no redraw, retouching, inferred spectrum or plot digitization.'},'notes':notes or [],'panels':[],'source_locators':[('SI' if role=='si' else 'Main')+f' PDF p. {page}, '+desc],'source_unit_ids':[key] if key in UNIT_ITEMS else [],'text_reviewed':True,'visual_reviewed':True,'source_review_basis':'Previously passed complete source audit and frozen original assets. Reader rendering and independent presentation review remain pending.','reviewed':False,'reader_render_verified':False,'training_eligible':False}
    GROUPS[group].append(entry)
    return entry
for aid,a in ASSETS.items():
    assert sha(B/a['path'])==a['sha256'],aid
    sids=FIGINV.get(aid,{}).get('sample_ids',[])
    if aid=='equation-1':sids=['growth-02-d']
    if aid=='equation-4':sids=['cleaned-0.20pct-powder','film-a']
    notes=[]
    if aid=='figure-3':notes=['A: powder and film XRD plus wurtzite reference positions. B: TEM with 50 nm scale bar. C: 100-particle diameter histogram. D: HRTEM with 5 nm scale bar and 2.34/2.74 Å spacings.','No SAED, refined lattice constants, atomic coordinates or supplied CIF is present.']
    elif aid=='figure-8':notes=['The domain-spin estimate S > 800 is collective A–C/unspecified individual film, not a film-A-specific quantity.']
    elif aid in ['figure-s3','table-s4']:notes=['Unresolved g-si-curve-table: Figure S3b orders mass-normalized D > E > F, while Table S4 lists D = 0.038, E = 0.059 and F = 0.076 emu/g. Do not swap labels or resolve D/F outcomes for training.','D–F coat counts, individual parent batches and independently stated annealing details are missing.']
    elif aid in ['figure-s1-equations','table-s1','table-s2','table-s3']:notes=['Model/reference content; not a counted dopant population or a newly measured atomic structure.','The SI statistical notation gap is retained for Figure S1. Table S1 lists cited ligand-field systems, Table S2 estimates parameters and Table S3 separates calculated and cited experimental columns.']
    elif aid=='figure-6':notes=['TOPO-capped 1.1% Mn sample: frozen-solution MCD on quartz. Initial feed and detailed TOPO treatment are unreported; do not transfer the 0.20% colloid or 180 °C amine conditions.']
    elif aid=='sample-preparation':notes=['The full preparation excerpt contains the common route, surface-bound control, amine/TOPO alternatives and A–C film processing. They remain separate procedures.']
    aa=asset_item(a,notes=notes,sids=sids);PUBLIC_ASSETS[aid]=aa
    PRIVATE_ASSETS.append({'id':aa['id'],'source_asset_id':aid,'private_path':str(B/a['path']),'public_asset':aa['public_asset'],'sha256':a['sha256'],'reviewed':False,'reader_render_verified':False})
    targets=[]
    if aid in UNIT_ITEMS:targets+=UNIT_ITEMS[aid]
    if a['kind']=='full_page':
        iid=add('sources','original-'+aid,('SI' if a['source_role']=='si' else 'Main')+' original page '+str(a['pdf_page']),'The complete original page is available with its source identity and printed page number. Figures, methods, reference systems and author interpretations retain their own scopes.',scope='source_metadata',ev=[{'source_id':SID,'document_role':a['source_role'],'pdf_page':a['pdf_page'],'printed_page':aa['printed_page'],'locator':'Complete original page'}]);targets.append(iid)
    if aid=='materials':targets += [uid_item(m) for m in MATS]
    if aid=='sample-preparation':targets += [uid_item(p) for p in PRO if p!='protocol-oxidation-controls']+[iid for key,iid in OPS.items() if any(s in key for s in ['hydrolysis','amine-cleaning','surface-control','topo','films-a-c'])]
    for sid in sids:
        if sid in UNIT_ITEMS:targets += UNIT_ITEMS[sid]
    assert targets,('Unreachable original asset',aid)
    for iid in uniq(targets):ITEMS[iid]['original_assets'].append({'id':aa['id'],'label':'Original '+aa['label'],'public_asset':aa['public_asset'],'public_asset_sha256':aa['public_asset_sha256']})
# Two SI equations share the actual original Figure S1/equation crop; MCD
# normalization uses the actual main page. No synthetic equation screenshot.
for eq in I['equations']:
    if eq['id'] in ASSETS:continue
    original=ASSETS[eq['asset']];aa=asset_item(original,key=eq['id'],group='equations',label=eq['expression'],notes=[eq['meaning'],'Original equation and notation preserved; no silent mathematical repair.'])
    aa['source_asset_type']='equation_within_existing_original_asset'
    iid=uid_item(eq['id']);ITEMS[iid]['original_assets'].append({'id':aa['id'],'label':'Original '+eq['id'].replace('-',' '),'public_asset':aa['public_asset'],'public_asset_sha256':aa['public_asset_sha256']})
for table in I['tables']:
    aa=next(a for a in GROUPS['tables'] if a['id']==SID+'-'+table['id']);aa.update(row_count=len(table['rows']),columns=table['columns'],table_status=table['status'],source_rows=deepcopy(table['rows']))
    if 'final_averages' in table:aa['source_final_averages']=deepcopy(table['final_averages'])
    if 'temperature_K' in table:aa['source_temperature_K']=table['temperature_K']
for ii in ITEMS.values():ii['original_assets']=uniq(ii['original_assets'])

docs=[]
for doc in I['source_documents']:
    role=doc['role'];pages=[p for p in PC['pages'] if p['source_role']==role]
    docs.append({'role':role,'filename':'10.1021_ja048427j'+('_si_1' if role=='si' else '')+'.pdf','sha256':doc['sha256'],'page_count':doc['pages'],'pages':[{'page':p['pdf_page'],'printed_page':p['printed_page'],'text_read':p['text_read'],'visual_review':p['visual_inspection'],'sections':[p['scope']]} for p in pages]})
library=read(SITE/'data/corpus/library-source.json');corp=next((p for p in library['papers'] if p.get('doi','').lower()==I['doi'].lower()),None)
assert corp,'Existing corpus identity not located'
gaps=[g['scope']+': '+g['issue']+' '+g['resolution'] for g in I['gaps']]
counts={'reader_items':len(ITEMS),'source_unit_universe':len(UNIT_ITEMS),'independently_audited_inventory_unit_ids':144,'source_facts':len(FACT_MAP),'source_objects':len(OBJ),'lossless_inventory_payloads':len(PAYLOAD),'canonical_records':len(R),'record_types':dict(Counter(r['record_type'] for r in R.values())),'true_common_nanocrystal_routes':1,'complete_laboratory_SOPs':0,'linked_operations':len(OPS),'canonical_measurement_and_context_entries':len(MEASURE),'linked_material_slots':len(MATERIAL),'linked_stock_slots':len(STOCKS),'linked_sample_and_context_slots':len(PRODUCTS),'operation_parameters':len(OPPARAM),'material_quantities':len(MATQ),'stock_quantities':len(STOCKQ),'condition_option_quantities':len(OPTIONS),'operation_environment_and_endpoint_facts':len(ENV),'product_context_facts':len(PRODQ),'typed_reader_facts':len(DISPLAY),'main_figures':10,'si_figures':3,'figure_table_scheme_items':18,'tables':4,'table_rows':sum(len(t['rows']) for t in I['tables']),'equations':7,'schemes':1,'references':68,'unique_original_assets':40,'main_pages':12,'si_pages':4}
review={'schema_version':'1.0','paper_id':SID,'doi':I['doi'],'title':I['title'],'paper':{'authors':I['authors'],'journal':I['journal'],'year':I['year'],'volume':I['volume'],'pages':I['pages'],'online_publication_date':I['published_online']},'source_group':SID,'corpus_paper_id':corp['id'],'corpus_document_id':corp['titleMetadata']['evidenceDocumentId'],'corpus_document_ids':corp['documentIds'],'review_scope':'supplied_main_and_matched_si','supporting_information':{'status':'matched_and_reviewed','matched_local_si_count':1,'scientific_pages':3,'administrative_cover_pages':1,'scope':'All four supplied SI pages were read and visually inspected in the passed independent source audit, including its cover, four tables, three figures, equations and references. Main-text announcement of three SI tables does not omit the fourth supplied table.'},'documents':docs,'document_identity_verification':{'method':'Actual manuscript identity and matched source contents; original hashes bound to the passed full-source audit.'},'coverage_status':'private_reader_proposal_pending_independent_reader_audit','independent_audit':'Full supplied-source and canonical scientific audits passed separately. Reader prose, specimen labels and presentation/bindings require their own independent review.','publication_status':'Private proposal; no integration or publication performed.','source_review_promoted':False,'training_eligible':False,'training_note':'One partial common nanocrystal route, with separate surface/control/film/acquisition/model contexts. No complete-SOP, exact atomic-structure, resolved D/F magnetic target, calibrated success or training admission is granted.','recipe_inventory':[{'id':rid,'label':r['title'],'record_ids':[rid],'record_type':r['record_type'],'status':'canonical_source_audit_passed_reader_pending','scope':'One source preparation, supporting procedure or observation context. Record count is not an independent synthesis-recipe count.','gaps':gaps if rid==PRE+'hydrolysis' else ['Independent reader and visual-binding review pending.'],'canonical_draft_present':True} for rid,r in R.items()],'characterization_inventory':{'reader_item_ids':[i['id'] for s in SECTIONS if s['id'] in ['structures','properties'] for i in s['items']]},'chemical_intuition':{'reader_item_ids':[i['id'] for s in SECTIONS if s['id']=='intuition' for i in s['items']],'scope':'Original author hypotheses, fits and cited models remain distinct from measurement and from uninspected follow-up papers.'},'reader_contract':{'version':'1.0','section_ids':[s['id'] for s in SECTIONS],'item_fields':['id','title','text','claim_type','sample_scope','evidence','source_locators','canonical_links','notes','facts','training_eligible']},'reader_sections':SECTIONS,**GROUPS,'referenced_methods':[{'id':ref['id'],'citation':ref.get('bibliography_extracted_text',ref.get('bibliography_transcription')),'context':ref['role'],'inspection_status':ref['inspection_status'],'reader_item_id':uid_item(ref['id'])} for ref in I['references']],'remaining_gaps':gaps+['Molecular, apparatus, product/crystal visual assets and their exact source bindings remain pending separate review. No CIF or exact atomic coordinates are supplied.'],'evidence_conflicts':[{'id':g['id'],'text':g['issue']+' '+g['resolution'],'reader_item_id':OBJ_ITEMS[('gaps',g['id'])]} for g in I['gaps'] if g['id'] in ['g-tmah-formula','g-base','g-s4-count','g-poisson','g-si-curve-table']],'record_formulation_labels':{rid:[p['sample_id'] for p in r['products']] for rid,r in R.items()},'record_formulation_scope_note':'Pair each specimen with its record. A–F name films; growth b–d name a progression; technique/model contexts do not establish universal physical aliquot IDs.','material_evidence_records':{'Mn:ZnO':list(R),'ZnO':[rid for rid in R if rid.endswith(('hydrolysis','surface-control','optical','structure','chemical-intuition','source-context'))]},'material_evidence_scope_notes':{'Mn:ZnO':'Doped nanocrystal and processed-film contribution with controls, models and references; one common synthesis route.','ZnO':'Host phase and explicitly undoped control context. Doped-particle and film properties are not relabeled as measured undoped-ZnO outcomes.'},'material_original_asset_ids':{'Mn:ZnO':[a['id'] for a in PUBLIC_ASSETS.values()],'ZnO':[PUBLIC_ASSETS[x]['id'] for x in ['figure-2','figure-3','figure-7','sample-preparation']]},'material_asset_scope_note':'Multi-panel original figures preserve complete panel labels and captions. Host/control context does not transfer Mn-doped properties to undoped ZnO.','route_evidence_contexts':{PRE+'hydrolysis':[rid for rid in R if rid!=PRE+'hydrolysis']},'counts':counts}
write('norberg2004.json',review)
write('source-item-coverage.json',{'schema':'mattersyn-reader-source-coverage/1','source_id':SID,'source_inventory_sha256':sha(B/'source-inventory.json'),'source_facts_sha256':sha(B/'source-facts.json'),'canonical_coverage_sha256':sha(B/'canonical-source-coverage.json'),'unit_to_reader_items':UNIT_ITEMS,'unmapped_units':[],'fact_to_reader':FACT_MAP,'source_objects':[{'category':cat,'source_object_id':key,'source_pointer':f'/{cat}/{n}','reader_item_id':OBJ_ITEMS[(cat,key)],'canonical_bindings':[b for b in COV['source_objects'] if b['category']==cat and b['source_object_id']==key]} for (cat,key),(n,obj) in OBJ.items()],'lossless_inventory_payload_map':[{'record_id':rid,'json_pointer':ptr,'category':cat,'source_object_id':key,'reader_item_id':DISPLAY[(rid,ptr)][0],'reader_fact_id':DISPLAY[(rid,ptr)][1]['id'],'presentation':'Academic summary in visible value; exact unchanged canonical_quantity plus JSON pointer retains full source object.'} for (rid,ptr),(cat,key) in PAYLOAD.items()]})
write('canonical-measurement-coverage.json',{'measurement_to_reader_item':MEASURE,'operation_to_reader_item':OPS,'operation_parameter_to_reader_item':OPPARAM,'material_to_reader_item':MATERIAL,'material_quantity_to_reader_item':MATQ,'stock_to_reader_item':STOCKS,'stock_quantity_to_reader_item':STOCKQ,'product_to_reader_item':PRODUCTS,'product_quantity_to_reader_item':PRODQ,'condition_option_quantity_to_reader_item':OPTIONS,'operation_environment_endpoint_to_reader_item':ENV,'displayed_field_map':[{'record_id':rid,'json_pointer':ptr,'reader_item_id':iid,'reader_fact_id':f['id']} for (rid,ptr),(iid,f) in DISPLAY.items()],'draft_sha256':{m['record_id']:m['sha256'] for m in MAN['records']}})
write('reader-bindings-proposal.json',{'schema':'mattersyn-private-reader-bindings/1','source_id':SID,'status':'proposed_not_approved','reader_sha256':sha(O/'norberg2004.json'),'source_fact_count':201,'source_unit_count':180,'canonical_records':{m['record_id']:m['sha256'] for m in MAN['records']},'original_assets':PRIVATE_ASSETS,'operation_to_reader_item':OPS,'molecular_or_apparatus_bindings_approved':False,'publication_approved':False})
write('reader-items-summary.json',[{'id':i['id'],'title':i['title'],'section':s['id'],'source_unit_ids':i['source_audit_unit_ids'],'facts':len(i['facts'])} for s in SECTIONS for i in s['items']])
assert all(sha(p)==h for p,h in FROZEN.items()),'Frozen source or canonical bytes changed'
write('reader-author-manifest.json',{'schema':'mattersyn-private-reader-author-manifest/1','source_id':SID,'created_at':datetime.now(timezone.utc).isoformat(),'status':'author_draft_pending_validation_and_independent_review','counts':counts,'input_hashes':FROZEN,'builder_sha256':sha(__file__),'current_readonly_site_contracts':{str(p):sha(p) for p in [SITE/'scripts/build_paper_reviews.py',SITE/'scripts/review_scope.py',SITE/'dist/source-evidence.mjs']},'outputs':{n:sha(O/n) for n in ['norberg2004.json','source-item-coverage.json','canonical-measurement-coverage.json','reader-bindings-proposal.json','reader-items-summary.json']},'training_eligible':False,'published':False})
print(json.dumps(counts,ensure_ascii=False))
