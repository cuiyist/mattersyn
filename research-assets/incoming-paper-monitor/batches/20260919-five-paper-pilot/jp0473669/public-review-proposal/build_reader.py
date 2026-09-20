"""Author a private, source-bound Ribeiro reader. No Site or source mutation."""
from pathlib import Path
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timezone
import hashlib, json, re

O=Path(__file__).resolve().parent
B=O.parent
SITE=Path(r'[local path redacted]')
SID='ribeiro2004'; P='ribeiro-2004-'
def read(p): return json.loads(Path(p).read_text(encoding='utf8'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def objsha(x): return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def write(n,x): (O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def uniq(xs): return list({json.dumps(x,ensure_ascii=False,sort_keys=True):x for x in xs}.values())
def resolve(x,p):
    for k in p.strip('/').split('/') if p else []:
        k=k.replace('~1','/').replace('~0','~');x=x[int(k)] if isinstance(x,list) else x[k]
    return x
def prose(s):
    # Presentation spacing only; formulas, raw source strings and typed values stay exact.
    s=str(s).replace('in this extraction','in the supplied-source review').replace('No external downloads performed.','')
    for a,b in {'approximately500':'approximately 500','approximately8.5':'approximately 8.5','pHapproximately':'pH approximately','After24':'After 24','after24':'after 24','for2min':'for 2 min','for20s':'for 20 s','Add0.4M':'Add 0.4 M','to1.5':'to 1.5','states6.0':'states 6.0','and2.7':'and 2.7','refs7/25':'references 7 and 25','Refs7/25':'References 7 and 25','ref28':'reference 28','Numberperliter':'Number per liter','perarea':'per area'}.items():s=s.replace(a,b)
    s=re.sub(r'\bFigure(?=\d)', 'Figure ', s)
    s=re.sub(r'\bEquation(?=\d)', 'Equation ', s)
    s=s.replace('24h','24 h').replace('pH2.7','pH 2.7').replace('pH6.0','pH 6.0').replace('pH3.1','pH 3.1')
    return s.strip()

inv=read(B/'source-inventory.json');fs=read(B/'source-facts.json');cov=read(B/'canonical-source-coverage.json')
units=read(B/'canonical-source-unit-index.json')['units'];uby={u['id']:u for u in units}
manifest=read(B/'canonical-record-manifest.json');audit=read(B/'canonical-records-audit.json')
records={p.stem:read(p) for p in sorted((B/'canonical-drafts').glob('*.json'))}
input_paths=[B/n for n in ['source-inventory.json','source-facts.json','canonical-source-coverage.json','canonical-source-unit-index.json','canonical-record-manifest.json','canonical-records-audit.json','source-scientific-audit.json','page-coverage.json','intake-manifest.json']]
input_paths+=list((B/'canonical-drafts').glob('*.json'))+[B/a['filename'] for a in inv['assets']]
frozen={str(p):sha(p) for p in input_paths}
assert audit['status']=='passed_with_preserved_source_limits'
assert all(sha(B/'canonical-drafts'/f'{rid}.json')==h for rid,h in audit['record_hashes'].items())
assert all(sha(p)==h for p,h in manifest['source_pdf_hashes'].items())
assert all(sha(B/a['filename'])==a['sha256'] for a in inv['assets'])

SECTIONS=[('precursors','Precursors'),('protocol','Synthesis protocol'),('structures','Final structures'),('properties','Properties'),('intuition','Chemical intuition'),('sources','Sources and limitations')]
sections=[{'id':i,'title':t,'items':[]} for i,t in SECTIONS];items={};unit_map={u['id']:[] for u in units}
LIMIT='Source-defined cohort or analytical context; matching concentration or pH labels do not establish identical physical batches or aliquots across techniques.'
def evidence(es):
    out=[]
    for e in es:
        m=re.search(r'Main PDF p\. (\d+)',e.get('locator',''));n=e.get('pdf_page') or (int(m[1]) if m else None)
        loc=e.get('locator') or f'Main PDF p. {n} (printed p. {15611+n}), '+e.get('section','source excerpt')
        out.append({'source_id':SID,'document_role':'main','pdf_page':n,'printed_page':15611+n if n else None,'locator':prose(loc)})
    return uniq(out)
def add(sec,key,title,text,es=(),kind='reported_source_fact',scope='source_cohort'):
    assert key not in items,key
    ee=evidence(es)
    x={'id':key,'title':title,'text':prose(text),'claim_type':kind,'sample_scope':{'formulations':[],'physical_batch_id':None,'scope_kind':scope,'state':title,'link_limit':LIMIT,'canonical_sample_links':[]},'evidence':ee,'source_locators':[e['locator'] for e in ee],'canonical_links':[],'notes':[],'facts':[],'source_audit_unit_ids':[],'source_fact_ids':[],'original_assets':[],'training_eligible':False}
    items[key]=x;next(s for s in sections if s['id']==sec)['items'].append(x);return x
def link(key,rid,ptr,relation='Exact typed canonical field; source and specimen scope retained.'):
    resolve(records[rid],ptr)
    items[key]['canonical_links'].append({'record_id':rid,'json_pointer':ptr,'relation':relation})
def mapunit(uid,key):
    if key not in unit_map[uid]:unit_map[uid].append(key)
    x=items[key];x['source_audit_unit_ids'].append(uid)
    # The derived inventory index uses page 1 as a generic administrative
    # locator for /schemes and /tables. Keep that pointer in the private map,
    # while the reader uses actual Figure 3 / complete-page evidence above.
    if uid not in ['schemes','tables']:x['evidence']=uniq(x['evidence']+evidence(uby[uid]['evidence']))

OVERVIEWS={
'hydrolysis':('protocol','Controlled hydrolysis and the concentration series',
'Tin(II) chloride dihydrate in absolute ethanol is hydrolyzed at room temperature, producing a white turbid suspension. Dialysis against deionized water removes chloride and leaves clear tin-dioxide colloids at approximately pH 8.5. The reported 0.0025–0.1 mol/L range describes the initial ethanolic Sn(II) concentration, not a measured final colloid concentration or a fully enumerated batch list. The main article delegates fuller preparation details to references 7 and 25. Absolute charges, water dosing and hydrolysis time remain unreported.'),
'ph-treatment':('protocol','Acid-set aging and optical redispersion',
'This branch uses colloids originating from 0.025 mol/L ethanolic Sn(II). Dilute nitric acid lowers the initially approximately 8.5 pH to treatment values extending to 1.5. After 24 h, the authors add 0.4 mol/L aqueous tetrabutylammonium hydroxide and probe-sonicate for 2 min for spectroscopy. The TBAOH dose and final measurement pH are absent. Treatment labels therefore remain distinct from the pH after adding this base; the optical preparation is not automatically assigned to TEM or zeta-potential specimens.'),
'microscopy':('structures','TEM specimen preparation and acquisition',
'A drop of colloid wets a carbon-coated copper grid for 20 s, followed by drying in air. Imaging uses a Philips CM200 microscope at 200 kV; the method measures at least 200 particles for a size distribution. The particle count is not a count of independent syntheses. Grid drying does not establish a powder-isolation procedure, and the source does not supply a drying time, grid mesh or complete specimen-to-aliquot mapping.'),
'concentration-structure':('structures','Concentration-dependent morphology and radius distributions',
'Figure 4 compares HRTEM specimens originating from 0.1 mol/L (a) and 0.0025 mol/L (b) precursor solutions. The authors identify imperfect-coalescence defects, including dislocations and twin boundaries, more often at high concentration. Both scale bars are 4 nm, not assigned particle diameters. Figure 5 retains three TEM histograms for 0.025, 0.005 and 0.0025 mol/L; their horizontal axis is particle radius. Higher concentration broadens the distribution and shifts it toward larger radius. No exact fitted means, widths or particle list are recovered from the plot.'),
'uv-visible':('properties','Absorption and concentration-dependent optical shifts',
'Perkin-Elmer equipment records the colloidal absorption spectra over 220–360 nm at room temperature; the model, path length and dilution are not specified. Figure 1a uses normalized intensities and a narrower displayed interval. Increasing initial precursor concentration shifts absorption toward longer wavelength, but a complete curve-to-concentration key and numerical onset table are absent. Monitoring of a 0.0025 mol/L-origin suspension up to 2 h is an observation window, not an instructed reaction hold.'),
'photoluminescence':('properties','Photoluminescence acquisition and comparison',
'The Jobin-Yvon Fluorolog FL3-12 uses Xe-lamp excitation at 250 nm and a photomultiplier-tube detector; the experimental text reports a 250–400 nm collection interval. Figure 1b shows normalized emission on its printed wavelength axis. Higher initial precursor concentration shifts emission toward longer wavelength. The acquisition interval and displayed figure limits remain separate. The pH-dependent spectra concern redispersed optical specimens, whose final pH after TBAOH addition is unknown. No quantum yield or lifetime is reported.'),
'zeta-potential':('properties','Electrokinetic behavior of the pH series',
'Brookhaven Instruments Zetaplus measurements concern 0.025 mol/L-origin colloids. Figure 6a places the estimated isoelectric point at approximately pH 3.1. This is an electrokinetic result rather than a synthesis setpoint. The source does not state that the zeta-potential specimens received the TBAOH and probe-sonication treatment explicitly described for spectroscopy.'),
'ph-comparison':('structures','Treatment-dependent coarsening and HRTEM',
'Figure 6b reports a PL-model-derived particle radius versus acid-set treatment pH, although its vertical axis says “Size.” Figure 7 compares 0.025 mol/L-origin samples treated at pH 6.0 (a) and 2.7 (b), with 4 nm scale bars. The pH 2.7 specimen has larger irregular particles and imperfect-attachment-like defects; the pH 6.0 specimen resembles the original suspension. No numerical TEM diameters or post-TBAOH measurement pH are inferred from these labels.'),
'optical-size-model':('intuition','Effective-mass analysis of optical radii',
'The authors use Equation 1 to infer particle radius from either absorption onset or PL peak position. They use an approximately 3.6 eV bulk gap and an approximately 2.7 nm exciton Bohr radius as reference context. Absorption-derived gaps exceed PL-derived gaps, and the authors favor PL radii using the earlier calibration cited as reference 28. That cited work has not been inspected here. These remain optical model estimates, distinct from directly measured TEM radii; no new radius calculation or curve digitization is performed.'),
'growth-model':('intuition','Nucleation, coarsening and oriented attachment',
'The authors infer that all studied solutions exceed saturation because precipitation occurs. From rapid early change they assume concentration-independent supersaturation and mean nucleus size in dilute suspensions, then attribute later size differences to growth and coarsening. They propose Sn(OH)4 formation followed by polycondensation to SnO2, while the conclusion also uses ion-deposition language. Neither phrasing establishes measured solution speciation or resolves the Sn(II)-to-Sn(IV) oxidation pathway. Their collision model permits attachment of compatible faces, including imperfect coalescence. These hypotheses are distinguished from the microscopy observations and do not define atomistic trajectories.'),
'source-context':('sources','Paper identity, source scope and prior literature',
'Ribeiro and coauthors report a controlled-hydrolysis study of tin-dioxide growth in The Journal of Physical Chemistry B 108 (2004), 15612–15617, DOI 10.1021/jp0473669. All six supplied main-article pages were read and visually inspected in the independently audited extraction. Supporting information was not located or verified; its absence is not established. The 31 printed references are retained as citations, with their external full texts uninspected. The earlier 2–6 nm size description belongs to a cited Leite route, not to an exact current-study specimen or an identified radius/diameter measurement.')}
record_items={}
for suffix,(sec,title,text) in OVERVIEWS.items():
    rid=P+suffix;r=records[rid];key='overview-'+suffix
    es=[e for m in r['measurements'] for e in m['evidence']]
    add(sec,key,title,text,es,'author_model_and_interpretation' if suffix in ['growth-model','optical-size-model'] else 'source_review_context' if suffix=='source-context' else 'reported_source_fact','model_context' if suffix in ['growth-model','optical-size-model'] else 'source_metadata' if suffix=='source-context' else 'source_cohort')
    record_items[rid]=key;link(key,rid,'','Source-scoped record; this context is not an additional synthesis replicate.')

material_map={};operation_map={};stock_map={};product_map={};measurement_map={};field_map={}
for m in inv['materials']:
    mid=m['id'];key='material-'+mid;sec='intuition' if mid=='sn-hydroxide-model' else 'structures' if mid in ['sno2-colloid','carbon-copper-grid'] else 'precursors'
    text=f'{m["name"]}. Formula or component description: {m["formula"]}. Source role: {m["role"]}.'
    if m.get('supplier'):text+=' Supplier: '+m['supplier']+'.'
    if m.get('amount_status'):text+=' '+prose(m['amount_status'])+'.'
    if mid=='tbaoh-aqueous':text+=' The aqueous stock is 0.4 mol/L; this is not the final sample concentration.'
    if mid=='sn-hydroxide-model':text+=' An author-proposed intermediate, not a supplied or isolated precursor stock; no measured solution geometry is established.'
    if mid=='sno2-colloid':text+=' Cassiterite is assigned in the authors’ XRD prose. The supplied article contains no XRD trace, SAED pattern, unit-cell parameters or atom coordinates.'
    ii=add(sec,key,m['name'],text,m['evidence'],'author_proposed_intermediate' if mid=='sn-hydroxide-model' else 'source_material_inventory','model_context' if mid=='sn-hydroxide-model' else 'method_context')
    ii['material_identity']={'source_material_id':mid,'name':m['name'],'formula':m['formula'],'exact_molecular_asset_binding_approved':False}
    for rid,r in records.items():
        for n,mat in enumerate(r['materials']):
            if mat['id']!=mid:continue
            ptr=f'/materials/{n}';link(key,rid,ptr);material_map[rid+'::'+mid]=key
            ii['notes']+= [prose(v) for v in mat.get('notes',[]) if v]
for rid,r in records.items():
    for n,op in enumerate(r['operations']):
        key='operation-'+op['id'];sec='protocol' if rid in [P+'hydrolysis',P+'ph-treatment'] else 'structures' if rid==P+'microscopy' else 'properties'
        ii=add(sec,key,op['label'],op['description'],op['evidence'],'source_preparation_operation' if not op['id'].endswith('acquisition') else 'source_acquisition_operation','method_context')
        link(key,rid,f'/operations/{n}');operation_map[rid+'::'+op['id']]=key
        ii['operation_context']={'record_id':rid,'operation_id':op['id'],'stage':op['stage'],'branch':op['branch'],'depends_on':deepcopy(op['depends_on']),'inputs':deepcopy(op['inputs']),'outputs':deepcopy(op['outputs']),'retained_fraction':op.get('retained_fraction'),'optional':op['optional'],'apparatus_binding_approved':False}
    for n,st in enumerate(r.get('stocks',[])):
        key='stock-'+st['id'];ii=add('precursors',key,st['name'],st['scope'],st['evidence'],'source_stock_series','method_context');link(key,rid,f'/stocks/{n}')
        ii['notes']=['Components: '+', '.join(next(m['name'] for m in r['materials'] if m['id']==c['material_id']) for c in st['components'])+'. Absolute component quantities and final stock volumes are unreported.']
        stock_map[rid+'::'+st['id']]=key
    for n,p in enumerate(r['products']):
        key=record_items[rid];ptr=f'/products/{n}'
        entry={'record_id':rid,'sample_id':p['sample_id'],'source_label':p['source_sample_label'],'json_pointer':ptr,'recipe_link':p['recipe_link'],'relation':LIMIT}
        items[key]['sample_scope']['canonical_sample_links'].append(entry)
        items[key]['sample_scope']['formulations'].append(p['source_sample_label'])
        items[key]['notes'] += [prose(t) for t in p['notes'] if t]
        link(key,rid,ptr);product_map[rid+'::'+p['sample_id']]=key

FIG_SECTION={1:'properties',2:'intuition',3:'intuition',4:'structures',5:'structures',6:'properties',7:'structures'}
FIG_TEXT={
1:'Panel a shows normalized absorption and panel b photoluminescence for colloids prepared across the initial Sn(II) concentration range of 0.0025–0.1 mol/L. The arrows indicate the direction of increasing concentration. The source does not provide a complete numerical curve-to-concentration key; no exact onset or peak positions are reconstructed.',
2:'Panel a gives particle radii estimated from absorption onset, while panel b uses PL peak position. Both estimates use the effective-mass model. The insets show the authors’ corresponding particle-number estimates per litre. These are model-derived radii and counts, not a table of directly measured particles.',
3:'The authors’ oriented-attachment schematic contrasts collisions of crystallographically incompatible faces in panel a with compatible faces in panel b. Compatible collisions may yield perfect or imperfect coalescence, including twin-boundary defects. This conceptual scheme is numbered Figure 3 by the source; it is not a microscopy image or atomic structure.',
4:'HRTEM panel a represents particles originating from 0.1 mol/L initial Sn(II), and panel b represents 0.0025 mol/L. Both panels carry 4 nm scale bars. The authors associate the marked defects with imperfect coalescence, including dislocations and twin boundaries. The nearby prose refers to Figure 3a/b, whereas the actual images and caption are Figure 4; that discrepancy is preserved.',
5:'The top, middle and bottom TEM histograms correspond to initial Sn(II) concentrations of 0.025, 0.005 and 0.0025 mol/L, respectively. The horizontal axis explicitly reports particle radius in nanometres. Higher concentration broadens the radius distribution and shifts it toward larger radius. No raw particle list or tabulated fit parameters are supplied.',
6:'Panel a shows zeta potential versus pH for 0.025 mol/L-origin colloids, with an estimated isoelectric point near pH 3.1. Panel b shows PL-derived particle radius versus treatment pH, with the original PL spectra in the inset; its ordinate uses the generic word “Size.” The acid-set treatment pH must be distinguished from the unreported final measurement pH after TBAOH addition. The source does not establish whether those numerical pH values differ.',
7:'The HRTEM specimens originate from 0.025 mol/L initial Sn(II) and are labeled by treatment pH: 6.0 in panel a and 2.7 in panel b. Both scale bars are 4 nm. The pH 2.7 specimen shows larger irregular particles and defects associated by the authors with imperfect attachment. These labels do not establish the final pH after redispersion or an exact physical-aliquot link to the optical data.'}
for f in inv['figures']:
    add(FIG_SECTION[f['number']],'figure-'+str(f['number']),f'Figure {f["number"]}: '+f['title'],FIG_TEXT[f['number']],[{'pdf_page':f['pdf_page'],'section':f'Figure {f["number"]}'}], 'author_model_figure' if f['number'] in [2,3] else 'mixed_measurement_and_author_model' if f['number']==6 else 'original_experimental_figure')
EQ_TEXT={1:'E_g^eff = E_g + ℏ²π²/(2μR²). R is particle radius and μ the effective reduced mass. No numerical μ is supplied. Absorption-onset and emission-peak inputs remain distinct.',2:'R_c = 2Mγ̄/[RTρ ln(a/a₀)]. R here denotes the universal gas constant; M is molecular weight, γ̄ interfacial energy per area, ρ density, T absolute temperature and a/a₀ activity ratio. The authors approximate the activity ratio by a concentration ratio; no new nucleation calculation is made.',3:'N = cM/(ραR_p³), with α = 4π/3 for a sphere. c is initial concentration and R_p particle radius. N is an author estimate of particle number per litre, not a direct count; consistent unit conversions are required.',4:'N = (2.16 ± 0.14) × 10¹⁸ + (1.15 ± 0.07) × 10²⁰ c. The PL-derived relation is discussed for c < 0.04 mol/L; its coefficients and printed uncertainties are retained without extrapolation. No confidence level is specified.'}
for e in inv['equations']:add('intuition','equation-'+str(e['number']),f'Equation {e["number"]}: '+{1:'optical radius',2:'critical nucleus radius',3:'particle-number estimate',4:'reported linear fit'}[e['number']],EQ_TEXT[e['number']],[{'pdf_page':e['pdf_page'],'section':f'Equation {e["number"]}'}],'author_model_equation','model_context')
for ref in inv['references']:
    x=add('sources','reference-'+str(ref['number']),f'Reference {ref["number"]}',ref['raw_bibliographic_text'],ref['evidence'],'cited_reference','cited_context');x['notes']=[ref['source_access']]
    if ref['number'] in [7,25]:x['notes'].append('Cited for fuller synthesis preparation. This reader does not import uninspected conditions from this reference.')
    if ref['number']==28:x['notes'].append('Cited by the authors for optical-size calibration; no new calibration or exact specimen equivalence is established here.')
GAP_TITLES=['Supporting information','Cited upstream preparation','Reaction quantities and control','Dialysis details','Treatment and measurement conditions','Numerical curves and distributions','Crystallography and atom coordinates','Unreported isolation and measurements','Mechanism and solution speciation']
GAP_TEXT=[
'Only the supplied main article was reviewed. Supporting information was not located or verified, and its existence or absence remains unestablished.',
'The main article directs readers to references 7 and 25 for fuller preparation details. Those external texts have not been inspected in this source review, so their procedures cannot supply missing fields here.',
'The paper does not provide absolute precursor, ethanol or water charges; the water-ratio basis, addition order and rate; mixing conditions, vessel or atmosphere; hydrolysis duration; or oxidation conditions.',
'The dialysis membrane, water volume and exchange schedule, duration, and chloride-removal endpoint are not reported.',
'The acid concentration and dose, TBAOH addition volume, final pH after redispersion, sonication power and final colloid concentration are not reported.',
'Full numerical spectra, tabulated peak and radius values, raw histogram particle measurements, and uncertainties for optical-derived radii are not supplied. The original plots are retained without invented digitization.',
'Cassiterite is assigned in the authors’ XRD prose, but the supplied main contains no XRD trace or SAED pattern. Unit-cell constants, measured atom coordinates, CIF, surface-ligand specification and a complete particle atom model are unavailable.',
'The supplied article does not report a powder-isolation protocol, quantitative yield, PL quantum yield or lifetime, Raman data, or a sensor/device test.',
'The mechanistic conclusions rely on author assumptions, models and cited studies. Atomistic dynamics and solution oxidation or speciation were not directly measured.'
]
for n,g in enumerate(GAP_TEXT,1):add('sources',f'gap-{n}',GAP_TITLES[n-1],g,uby[f'remaining_gaps-{n}']['evidence'],'source_missingness','curator_interpretation')
CONFLICT_TITLES={'hrtem-reference-typo':'Figure 3/4 reference discrepancy','radius-size-wording':'Radius versus generic size labels','treatment-measurement-ph':'Treatment pH and final measurement pH','growth-language':'Polycondensation and ion-deposition wording'}
CONFLICT_TEXT={
'hrtem-reference-typo':'The discussion refers to Figure 3a/b when describing HRTEM, but Figure 3 is the mechanism schematic. The actual images and caption in Figure 4 establish the HRTEM panel assignments; the prose cross-reference is retained as a source discrepancy.',
'radius-size-wording':'Figure 5 explicitly labels its horizontal axis particle radius, despite generic size wording in its caption. Figure 6b labels the ordinate Size while its caption defines a radius calculated from PL. The reader preserves radius and does not convert either result into an asserted diameter.',
'treatment-measurement-ph':'The paper labels acid-set treatment pH, then adds basic TBAOH after 24 h for spectroscopy without reporting the final pH. Treatment labels cannot establish the final measurement pH; the source does not establish whether their numerical values differ.',
'growth-language':'The growth discussion on main page 3 proposes polycondensation rather than direct ion deposition, while the conclusion on main page 6 uses ion-deposition wording. Both remain author interpretations; the source does not establish one uniquely measured microscopic pathway.'}
for c in inv['evidence_conflicts']:add('sources','conflict-'+c['id'],CONFLICT_TITLES[c['id']],CONFLICT_TEXT[c['id']],c['evidence'],'unresolved_source_conflict','curator_interpretation')
add('sources','page-coverage','Complete supplied-main coverage','All six supplied main pages were read and visually inspected in the separately passed source extraction and independent source audit. The main contains seven numbered figures, including the Figure 3 mechanism schematic, four numbered equations and 31 references. No separate numbered table is present. SI remains unverified.',[{'pdf_page':n,'section':'Complete page; captions, notes and continuation text'} for n in range(1,7)],'source_coverage','source_metadata')
add('sources','acknowledgment','Acknowledgment','The paper acknowledges FAPESP and CNPq.',inv['acknowledgment']['evidence'],'source_metadata','source_metadata')
add('protocol','experimental-excerpt','Original experimental procedure','The retained experimental excerpt covers the synthesis framework, pH-treatment branch, microscopy preparation and acquisition conditions. Those activities remain separately scoped in the linked records.',[{'pdf_page':2,'section':'Experimental Procedure'}],'original_source_excerpt','method_context')
add('protocol','water-ratio-excerpt','Water ratio in the growth discussion','The approximately 500:1 water/Sn²⁺ ratio appears in the Results discussion. The source does not identify a molar, mass or volume basis or a water dose. The same excerpt contains the authors’ rapid-nucleation and supersaturation assumptions; those assumptions are not additional measured reaction conditions.',[{'pdf_page':3,'section':'Hydrolysis and supersaturation discussion'}],'original_source_excerpt','method_context')

def unit_target(uid):
    if uid=='identity':return 'overview-source-context'
    if uid.startswith('materials-'):return 'material-'+uid.removeprefix('materials-')
    if uid.startswith('protocols-'):return 'overview-'+{'tem-preparation':'microscopy'}.get(uid.removeprefix('protocols-'),uid.removeprefix('protocols-'))
    if uid.startswith('step-'):return 'operation-'+uid.removeprefix('step-')
    if uid.startswith('figures-'):return uid.removeprefix('figures-')
    if uid.startswith('equations-'):return uid.removeprefix('equations-')
    if uid.startswith('references-'):return 'reference-'+uid.removeprefix('references-')
    if uid.startswith('remaining_gaps-'):return 'gap-'+uid.removeprefix('remaining_gaps-')
    if uid.startswith('evidence_conflicts-'):return 'conflict-'+uid.removeprefix('evidence_conflicts-')
    if uid.startswith('source_pages-') or uid=='tables':return 'page-coverage'
    if uid=='schemes':return 'figure-3'
    if uid=='acknowledgment':return uid
    if uid.startswith('assets-'):
        k=uid.removeprefix('assets-')
        return {'experimental-procedure':'experimental-excerpt','water-ratio-context':'water-ratio-excerpt','references':'overview-source-context','references-continuation':'overview-source-context'}.get(k,k)
    raise ValueError(uid)

context_targets={}
for row in cov['source_units']:
    uid=row['source_unit_id'];key=unit_target(uid);mapunit(uid,key)
    for b in row['canonical_bindings']:
        rid,ptr=b['record_id'],b['pointer'];link(key,rid,ptr)
        if ptr.startswith('/measurements/'):context_targets[(rid,ptr.rsplit('/value',1)[0])]=key

def display(q):
    if q.get('value') is not None:return q['value']
    lo,hi=q.get('minimum'),q.get('maximum')
    if lo is not None and hi is not None:return f'{lo:g}–{hi:g}'
    if lo is not None:return ('> ' if q.get('minimum_exclusive') else '≥ ')+f'{lo:g}'
    if hi is not None:return ('< ' if q.get('maximum_exclusive') else '≤ ')+f'{hi:g}'
    return 'Not reported'
def quantity(key,rid,ptr,q,label,basis,es=None,sample=None):
    assert resolve(records[rid],ptr)==q
    fid=rid+'::'+ptr;qual=' '.join(prose(q[k]) for k in ['qualifier','note','basis'] if q.get(k))
    f={'id':fid,'label':label,'value':display(q),'unit':q.get('unit'),'status':q.get('status'),'approximate':q.get('approximate',False),'qualifier':qual,'basis':basis,'canonical_record_id':rid,'json_pointer':ptr,'canonical_quantity':deepcopy(q),'evidence':evidence(es or q.get('evidence',[])),'training_eligible':False}
    if sample:f['sample_id']=sample
    if 'water_to_tin_relative_ratio' in ptr:f['value']='500:1';f['unit']='water:Sn²⁺; basis unreported';f['presentation_note']='Displays the exact reported ratio; canonical scalar denotes water parts relative to one Sn(II) part.'
    items[key]['facts'].append(f);link(key,rid,ptr)
    field_map[rid+'::'+ptr]={'record_id':rid,'json_pointer':ptr,'reader_item_id':key,'reader_fact_id':fid,'canonical_value_sha256':objsha(q),'rendering':'typed_quantity'}
    return f

for rid,r in records.items():
    for n,m in enumerate(r['measurements']):
        ptr=f'/measurements/{n}';key=context_targets.get((rid,ptr),record_items[rid]);measurement_map[rid+'::'+m['id']]={'record_id':rid,'json_pointer':ptr,'reader_item_id':key,'sample_id':m['sample_id'],'canonical_value_sha256':objsha(m),'rendering':'source_context_prose' if m['id'].startswith('source-') else 'typed_quantity'}
        if m['id'].startswith('source-'):
            # Source context JSON is faithfully linked and mapped privately, not printed as an implementation dump.
            link(key,rid,ptr);field_map[rid+'::'+ptr+'/value']={'record_id':rid,'json_pointer':ptr+'/value','reader_item_id':key,'canonical_value_sha256':objsha(m['value']),'rendering':'source_context_prose'}
        else:quantity(key,rid,ptr+'/value',m['value'],m['property'].replace('_',' ').capitalize(),'canonical_'+m['value']['status'],m['evidence'],m['sample_id'])
    for n,op in enumerate(r['operations']):
        key=operation_map[rid+'::'+op['id']]
        for name,q in op['parameters'].items():quantity(key,rid,f'/operations/{n}/parameters/{name}',q,name.replace('_',' ').capitalize(),'operation_parameter')
        for name in ['environment','endpoint']:quantity(key,rid,f'/operations/{n}/'+name,op[name],name.capitalize(),'operation_state')
    for n,m in enumerate(r['materials']):
        key=material_map[rid+'::'+m['id']]
        for name,q in m.get('quantities',{}).items():quantity(key,rid,f'/materials/{n}/quantities/{name}',q,name.replace('_',' ').capitalize(),'reagent_specification')
    for n,st in enumerate(r.get('stocks',[])):
        key=stock_map[rid+'::'+st['id']]
        for name,q in st.get('concentrations',{}).items():quantity(key,rid,f'/stocks/{n}/concentrations/{name}',q,name.replace('_',' ').capitalize(),'initial_stock_series')

def target_pointer(rid,ptr):
    if rid+'::'+ptr in field_map:return field_map[rid+'::'+ptr]['reader_item_id']
    bits=ptr.strip('/').split('/');obj=records[rid][bits[0]][int(bits[1])]
    return {'materials':material_map,'operations':operation_map,'stocks':stock_map,'products':product_map,'measurements':measurement_map}[bits[0]][rid+'::'+obj.get('id',obj.get('sample_id'))] if bits[0]!='measurements' else measurement_map[rid+'::'+obj['id']]['reader_item_id']
fact_map={}
for row in cov['facts']:
    dest=[]
    for b in row['canonical_bindings']:
        key=target_pointer(b['record_id'],b['pointer']);items[key]['source_fact_ids'].append(row['source_fact_id']);link(key,b['record_id'],b['pointer'])
        dest.append({**b,'reader_item_id':key})
    fact_map[row['source_fact_id']]={'reader_item_ids':list(dict.fromkeys(d['reader_item_id'] for d in dest)),'canonical_bindings':dest,'source_fact_sha256':objsha(row['source_fact'])}

ASSET_CONTEXTS={
'figure-1':[('uv-visible','concentration-series'),('photoluminescence','concentration-series')],
'figure-2':[('optical-size-model','abs-radius'),('optical-size-model','pl-radius'),('growth-model','number-model')],
'figure-3':[('growth-model','attachment-model')],
'figure-4':[('concentration-structure',p) for p in ['hrtem-a','hrtem-b','hrtem-comparison']],
'figure-5':[('concentration-structure',p) for p in ['hist-025','hist-005','hist-0025','hist-comparison']],
'figure-6':[('zeta-potential','zeta-series'),('ph-comparison','pl-radius-series'),('photoluminescence','ph-optical-series')],
'figure-7':[('ph-comparison',p) for p in ['hrtem-ph6','hrtem-ph27','hrtem-comparison']],
'equation-1':[('optical-size-model','radius-analysis')], 'equation-2':[('growth-model','nucleus-model')],
'equation-3':[('growth-model','number-model')], 'equation-4':[('growth-model','number-model')],
'experimental-procedure':[], 'water-ratio-context':[('growth-model','nucleus-model')], 'references':[('source-context','references')], 'references-continuation':[('source-context','references')]}
ASSET_NOTES={
'figure-1':['Panels a/b show normalized absorption/emission. Figure axes are retained exactly; acquisition windows are separately reported. No per-curve concentration assignments or peak coordinates are reconstructed.'],
'figure-2':['Panels a/b use absorption-onset/PL-derived radii; insets are author-estimated particle number per litre. All are model-derived rather than direct particle counts.'],
'figure-3':['Source-numbered Figure 3 is a mechanism schematic. It is not TEM, SAED or atomic coordinates.'],
'figure-4':['Panel a: 0.1 mol/L; b: 0.0025 mol/L initial Sn(II). Both scale bars: 4 nm. The prose reference to Figure 3a/b is a preserved source discrepancy.'],
'figure-5':['Printed top/middle/bottom concentration labels: 0.025/0.005/0.0025 mol/L. The horizontal axis is radius. No bin table, mean or width is transcribed.'],
'figure-6':['Panel a is zeta potential versus pH. Panel b and its PL inset retain acid-set treatment labels; final pH after TBAOH is not supplied. Caption says particle radius although the ordinate says Size. These are distinct analytical contexts.'],
'figure-7':['Panel a treatment pH 6.0; b treatment pH 2.7; both originate from 0.025 mol/L precursor and carry 4 nm scale bars. No final measurement pH or exact optical-to-TEM aliquot join is established.']}
groups={k:[] for k in ['figures','tables','schemes','equations','source_notes']};asset_map=[]
for a in inv['assets']:
    short=a['id'].removeprefix(SID+'-');key=unit_target('assets-'+short);public='assets/figures/'+SID+'/'+Path(a['filename']).name
    # pathlib on Windows handles both source separators; public paths always use POSIX separators.
    public='assets/figures/'+SID+'/'+a['filename'].replace('\\','/').split('/')[-1]
    refs=[]
    for suffix,sample in ASSET_CONTEXTS[short]:
        rid=P+suffix;n=next(i for i,p in enumerate(records[rid]['products']) if p['sample_id']==sample)
        refs.append({'record_id':rid,'sample_id':sample,'json_pointer':f'/products/{n}','relation':LIMIT})
    group='figures' if short.startswith('figure-') else 'equations' if short.startswith('equation-') else 'source_notes'
    aa={'id':a['id'],'label':items[key]['title'] if not short.startswith('references') else 'References 1–11' if short=='references' else 'References 12–31','document_role':'main','page':a['pdf_page'],'printed_page':a['printed_page'],'caption_paraphrase':items[key]['text'],'sample_scope':LIMIT,'canonical_sample_links':refs,'sample_links':list(dict.fromkeys(x['record_id'] for x in refs)),'sample_linkage':LIMIT,'evidence_class':'author_model' if short in ['figure-2','figure-3'] or group=='equations' else 'mixed_measurement_and_author_model' if short=='figure-6' else 'original_experimental_figure' if group=='figures' else 'direct_source_excerpt','public_asset':public,'public_asset_sha256':a['sha256'],'asset_provenance':{'source_file':'10.1021_jp0473669.pdf','source_sha256':a['source_sha256'],'source_pdf_page':a['pdf_page'],'crop_reference_pixels':deepcopy(a['crop_reference_pixels']),'transformation':'Original rendered source crop; no redraw, enhancement or numerical digitization.'},'notes':ASSET_NOTES.get(short,[]),'panels':[],'source_unit_ids':['assets-'+short],'source_locators':[f'Main PDF p. {a["pdf_page"]}, '+short.replace('-',' ')],'text_reviewed':True,'visual_reviewed':True,'reviewed':False,'reader_render_verified':False,'training_eligible':False}
    groups[group].append(aa);asset_map.append({'id':a['id'],'private_path':str(B/a['filename']),'public_asset':public,'sha256':a['sha256'],'reader_item_ids':[key],'binding_approved':False})
    item_asset={'id':a['id'],'label':'Original '+aa['label'],'public_asset':public,'public_asset_sha256':a['sha256']};items[key]['original_assets'].append(item_asset)
    for j in refs:
        source_sample=resolve(records[j['record_id']],j['json_pointer'])
        items[key]['sample_scope']['canonical_sample_links'].append({**j,'source_label':source_sample['source_sample_label'],'recipe_link':source_sample['recipe_link']})
    for j in refs:
        overview=record_items[j['record_id']]
        items[overview]['original_assets'].append(item_asset)
    if short.startswith('references'):
        for num in range(1,12) if short=='references' else range(12,32):items[f'reference-{num}']['original_assets'].append(item_asset)
groups['schemes']=[{'id':SID+'-scheme-as-figure-3','label':'Oriented-attachment mechanism','same_as_figure_id':SID+'-figure-3','numbered_as':'Figure 3','separate_asset_count':0,'disposition':'Included in the seven numbered figures, not an eighth figure or additional measured structure.'}]

for ii in items.values():
    for k in ['canonical_links','notes','source_fact_ids','source_audit_unit_ids','original_assets']:ii[k]=uniq(ii[k])
    ii['source_locators']=uniq([e['locator'] for e in ii['evidence']])
    for f in ii['facts']:
        if f.get('sample_id'):
            rid=f['canonical_record_id'];p=next(x for x in records[rid]['products'] if x['sample_id']==f['sample_id']);n=records[rid]['products'].index(p)
            ii['sample_scope']['canonical_sample_links'].append({'record_id':rid,'sample_id':p['sample_id'],'source_label':p['source_sample_label'],'json_pointer':f'/products/{n}','relation':LIMIT})
    by_pointer={}
    for j in ii['sample_scope']['canonical_sample_links']:
        signature=(j['record_id'],j['json_pointer'])
        existing=by_pointer.setdefault(signature,{})
        for name,value in j.items():existing.setdefault(name,value)
    ii['sample_scope']['canonical_sample_links']=list(by_pointer.values())
    ii['sample_scope']['formulations']=uniq(ii['sample_scope']['formulations']+[j['source_label'] for j in ii['sample_scope']['canonical_sample_links'] if 'source_label' in j])

# Conflicts stay visible at the affected figure and result, as well as in Sources.
for cid,keys in {
    'hrtem-reference-typo':['figure-4','overview-concentration-structure'],
    'radius-size-wording':['figure-5','figure-6','overview-concentration-structure','overview-ph-comparison'],
    'treatment-measurement-ph':['figure-6','figure-7','overview-ph-treatment','overview-ph-comparison','operation-ph-treatment-redisperse','overview-photoluminescence'],
    'growth-language':['overview-growth-model','material-sn-hydroxide-model']
}.items():
    c=next(c for c in inv['evidence_conflicts'] if c['id']==cid)
    for key in keys:
        items[key].setdefault('evidence_conflict_ids',[]).append(cid)
        items[key]['notes'].append(CONFLICT_TEXT[cid])
for a in groups['source_notes']:
    if a['id'].endswith('references-continuation'):a['caption_paraphrase']='Original continuation containing references 12–31. External full texts are uninspected.'
    elif a['id'].endswith('references'):a['caption_paraphrase']='Original bibliography opening containing references 1–11. External full texts are uninspected.'

pagecov=read(B/'page-coverage.json');docs=[{'role':'main','filename':'10.1021_jp0473669.pdf','sha256':inv['source_sha256'],'page_count':6,'pages':[{'page':p['pdf_page'],'printed_page':p['printed_page'],'text_read':p['text_read'],'visual_review':p['visually_inspected'],'sections':inv['source_pages'][p['pdf_page']-1]['sections']} for p in pagecov['documents'][0]['pages']]}]
corpus=next(p for p in read(SITE/'data/corpus/library-source.json')['papers'] if p.get('doi','').lower()==inv['doi'])
counts={'reader_items':len(items),'records':len(records),'record_types':dict(Counter(r['record_type'] for r in records.values())),'linked_operations':len(operation_map),'source_preparation_operations':9,'acquisition_operations':4,'typed_measurement_and_context_entries':len(measurement_map),'visible_typed_facts':sum(len(x['facts']) for x in items.values()),'material_slots':len(material_map),'distinct_source_materials':len(inv['materials']),'stock_contexts':len(stock_map),'sample_and_context_ids':len(product_map),'source_facts':len(fact_map),'source_fact_bindings':sum(len(x['canonical_bindings']) for x in fact_map.values()),'source_inventory_units':len(unit_map),'figures':7,'tables':0,'schemes_within_numbered_figures':1,'numbered_equations':4,'source_note_assets':4,'original_assets':len(asset_map),'references':31,'supplied_main_pages':6,'matched_si_pages':0}
out={'schema_version':'1.0','paper_id':SID,'doi':inv['doi'],'title':inv['title'],'paper':{k:inv[k] for k in ['authors','journal','year','volume','issue','pages','online_publication_date','received','final_form']},'source_group':SID,'corpus_paper_id':corpus['id'],'corpus_document_id':corpus['titleMetadata']['evidenceDocumentId'],'corpus_document_ids':corpus['documentIds'],'review_scope':'supplied_main_only_si_unverified','supporting_information':{'status':'not_located_or_verified','matched_local_si_count':0,'scope':'Supporting information was not located or verified. Its existence and absence both remain unestablished.'},'documents':docs,'document_identity_verification':{'method':'Source title, authors, DOI and six-page content verified in the independent source audit; both local main copies have the same rechecked SHA-256.'},'coverage_status':'private_reader_proposal_pending_independent_audit','independent_audit':'Source extraction and canonical scientific audits passed separately. This reader awaits a different independent reader auditor.','publication_status':'Private proposal; not integrated or published.','source_review_promoted':False,'training_eligible':False,'training_note':'One partial synthesis framework, five procedures and five observation/context records. No task admission is granted; missing SI, recipe details, raw numerical curves and atom coordinates remain explicit.','recipe_inventory':[{'id':rid,'label':r['title'],'record_ids':[rid],'record_type':r['record_type'],'status':'canonical_source_audit_passed_reader_pending','scope':'One source-defined framework, procedure or analytical/model context; not an independent replicate.','gaps':[],'canonical_draft_present':True} for rid,r in records.items()],'characterization_inventory':{'reader_item_ids':[i['id'] for s in sections if s['id'] in ['structures','properties'] for i in s['items']]},'chemical_intuition':{'reader_item_ids':[i['id'] for s in sections if s['id']=='intuition' for i in s['items']],'scope':'Original authors’ models, interpretations and uninspected cited context; no later-source conditions or new mechanistic proof are introduced.'},'reader_contract':{'version':'1.0','section_ids':[s['id'] for s in sections],'item_fields':['id','title','text','claim_type','sample_scope','evidence','source_locators','canonical_links','notes','facts','training_eligible']},'reader_sections':sections,**groups,'referenced_methods':[{'id':SID+'-reference-'+str(r['number']),'citation':r['raw_bibliographic_text'],'context':'Fuller preparation cited' if r['number'] in [7,25] else 'Optical calibration cited' if r['number']==28 else 'Bibliographic context','inspection_status':r['source_access'],'reader_item_id':'reference-'+str(r['number']),'doi':None} for r in inv['references']],'remaining_gaps':[prose(g) for g in inv['remaining_gaps']],'evidence_conflicts':[{'id':c['id'],'text':prose(c['description']),'source_locators':[e['locator'] for e in evidence(c['evidence'])],'reader_item_id':'conflict-'+c['id']} for c in inv['evidence_conflicts']],'record_formulation_labels':{rid:[p['sample_id'] for p in r['products']] for rid,r in records.items()},'record_formulation_scope_note':LIMIT,'material_evidence_records':{'SnO2':list(records)},'material_evidence_scope_notes':{'SnO2':'Controlled-hydrolysis study and separately scoped preparation, microscopy, optical, electrokinetic and model contexts. Author phase assignment does not supply an exact crystal structure.'},'material_original_asset_ids':{'SnO2':[a['id'] for a in asset_map]},'material_asset_scope_note':'Figures preserve original panels and source labels; nominal composition or shared concentration labels do not establish exact sample joins.','route_evidence_contexts':{P+'hydrolysis':[rid for rid in records if rid!=P+'hydrolysis']},'presentation_gates':{'molecular_bindings':'pending','apparatus_bindings':'pending','independent_reader_audit':'pending','browser_qa':'not_performed','atomic_geometry':'not_supplied'},'counts':counts}
out['remaining_gaps']=GAP_TEXT
for conflict in out['evidence_conflicts']:conflict['text']=CONFLICT_TEXT[conflict['id']]
write(SID+'.json',out)
write('source-item-coverage.json',{'schema':'mattersyn-reader-source-coverage/1','source_id':SID,'source_inventory_sha256':sha(B/'source-inventory.json'),'source_facts_sha256':sha(B/'source-facts.json'),'unit_to_reader_items':unit_map,'fact_to_reader':fact_map,'unmapped_units':[],'unmapped_facts':[]})
write('canonical-field-coverage.json',{'schema':'mattersyn-reader-canonical-field-coverage/1','source_id':SID,'measurement_to_reader':measurement_map,'operation_to_reader_item':operation_map,'material_slot_to_reader_item':material_map,'stock_to_reader_item':stock_map,'sample_context_to_reader_item':product_map,'typed_field_to_reader':field_map,'record_hashes':{rid:sha(B/'canonical-drafts'/f'{rid}.json') for rid in records},'context_rendering_note':'All 147 canonical measurement/context objects have exact typed pointers. Source-inventory JSON contexts appear as curated prose and original assets, not raw metadata dumps; original values remain unchanged in canonical records.'})
write('reader-bindings-proposal.json',{'schema':'mattersyn-private-reader-bindings/1','source_id':SID,'status':'proposed_not_approved','reader_sha256':sha(O/(SID+'.json')),'canonical_records':{rid:sha(B/'canonical-drafts'/f'{rid}.json') for rid in records},'original_assets':asset_map,'operation_to_reader_item':operation_map,'molecular_or_apparatus_bindings_approved':False,'publication_approved':False})
write('reader-author-manifest.json',{'schema':'mattersyn-private-reader-author-manifest/1','source_id':SID,'author':'/root/backlog_eta','created_at':datetime.now(timezone.utc).isoformat(),'status':'author_generated_pending_validation_and_independent_reader_audit','input_hashes':frozen,'source_pdf_hashes':manifest['source_pdf_hashes'],'builder_sha256':sha(__file__),'site_readonly_contract_hashes':{str(SITE/p):sha(SITE/p) for p in ['scripts/build_paper_reviews.py','scripts/review_scope.py','dist/source-evidence.mjs']},'output_hashes':{n:sha(O/n) for n in [SID+'.json','source-item-coverage.json','canonical-field-coverage.json','reader-bindings-proposal.json']},'counts':counts,'site_modified':False,'source_modified':False,'canonical_modified':False,'ledger_modified':False,'downloads':False,'independent_reader_audit':False})
assert all(sha(p)==h for p,h in frozen.items()),'Source/canonical boundary changed while building.'
assert all(unit_map.values()),'Unmapped inventory unit'
print(json.dumps(counts))
