"""Build a separate metadata-only proposal; never alter frozen v1 or shared site."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime, timezone
import hashlib, json, re

P = Path(__file__).resolve().parent
B = P.parent
A = B.parent / 'independent-audit-20260924'
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def save(p, x):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def ev(role, page, item):
    return {'source_id':'rusch2026' + ('-si' if role == 'si' else ''),
            'locator':f'{role} PDF p. {page}' + (f' (printed {899+page})' if role == 'main' else '') + ', ' + item}
def add(dst, values):
    for value in values:
        if value not in dst: dst.append(deepcopy(value))
def diff(a, b, path=''):
    if type(a) != type(b): return [{'pointer':path,'before':a,'after':b}]
    if isinstance(a, dict):
        out=[]
        for k in sorted(a.keys() | b.keys()):
            q=path+'/'+k.replace('~','~0').replace('/','~1')
            if k not in a: out.append({'pointer':q,'change':'added','after':b[k]})
            elif k not in b: out.append({'pointer':q,'change':'removed','before':a[k]})
            else: out += diff(a[k],b[k],q)
        return out
    if isinstance(a, list):
        if len(a)!=len(b): return [] if a==b else [{'pointer':path,'before':a,'after':b}]
        return [v for i,(x,y) in enumerate(zip(a,b)) for v in diff(x,y,path+'/'+str(i))]
    return [] if a==b else [{'pointer':path,'before':a,'after':b}]

assert not (P/'correction-manifest.json').exists(), 'Do not overwrite a frozen correction.'
base_freeze = read(B/'author-candidate-freeze.json')
assert sha(B/'author-candidate-freeze.json') == '7459f98c44e546d4007d618bbebc22a4411a1b79ef1ef3f846f4f60372fc7c61'
for x in base_freeze['files']: assert sha(B/x['path'])==x['sha256'], x['path']
for x in read(B/'source-manifest.json'): assert sha(Path(x['path']))==x['sha256']
assert sha(A/'audit-report.json') == 'd8b6932d98f9b0b588ef15ce5e6c654e66dbb0a2ecdeab18d335609da6be89e0'

before_extraction = read(B/'source-extraction-v1.json')
extraction = deepcopy(before_extraction)
records = {p.stem:read(p) for p in (B/'candidate-site/data/records').glob('*.json')}
before_records = deepcopy(records)
result_evidence = {}
for suffix in ['rapid-c4','rapid-c6']:
    si_fig = 'FigureS3' if suffix.endswith('c4') else 'FigureS4'
    result_evidence[suffix] = [ev('main',4,'Results: short-amine controls and mixed bismuth/silver iodides'),ev('si',5,'FigureS2, amine-series powder diffraction'),ev('si',6,si_fig+', short-amine SEM/EDX')]
for suffix in ['rapid-c10','rapid-c12','rapid-c14']:
    result_evidence[suffix] = [ev('main',3,'Figure2, powder diffraction compared with separately resolved crystal models'),ev('main',4,'Results: long-chain amine powder phase and SEM morphology')]
result_evidence['rapid-fpea'] = [ev('main',8,'Results: 4-fluorophenethylamine extension'),ev('si',22,'FiguresS24/S25; product diffraction against literature CCDC2151233 and SEM/EDX')]
for suffix in ['rapid-c12-br','rapid-c12-cl']:
    result_evidence[suffix] = [ev('main',8,'Results: bromide/chloride extension'),ev('si',23,'FigureS26, C12 chloride/bromide/iodide powder diffraction')]
for suffix, evidence in result_evidence.items():
    r = records['rusch2026-'+suffix]
    add(r['products'][0]['phase']['evidence'], evidence)
    if suffix in ['rapid-c10','rapid-c12','rapid-c14']:
        add(r['products'][0]['morphology']['evidence'],[ev('main',4,'Results: polydisperse microcrystals a few micrometers in size'),ev('si',4,'FigureS1, C10/C12/C14 powder SEM')])
    if suffix=='rapid-fpea':
        add(r['products'][0]['composition']['evidence'],evidence)
        add(r['intended_target']['composition']['evidence'],evidence)
for n in [10,12,14]:
    r = records[f'rusch2026-recrystallized-c{n}']
    for key in ['phase','morphology']:
        add(r['products'][0][key]['evidence'],[ev('main',5,'Table1, crystal system/space group/Z and selected-crystal dimensions/morphology')])
r = records['rusch2026-bi-oleate']
r['material']['family']='bismuth-oleate precursor reaction solution'
r['material']['architecture']='unresolved'

hold = {
    'record_id':'rusch2026-study-context','status':'hold',
    'claim_scope':'C12 sample assignment of the visible Figure4C interlayer-spacing inset',
    'reason':'The printed caption names C10 and C12, but a distinct C12 series is not identifiable in the displayed inset. Supplied evidence cannot resolve that assignment.',
    'unaffected_scope':'C10 thermal panels and the independently labeled C12 FigureS14 remain usable with their own source locators.',
    'resolution':'Do not promote this inset as a confirmed C12 measurement or infer a second numerical series.',
    'evidence':[ev('main',6,'Figure4C and printed caption'),ev('si',11,'FigureS14, explicitly labeled C12 thermal data')]
}
r = records['rusch2026-study-context']
r['quality']['conflicts'].append('figure4-inset-sample')
r['quality']['missing_fields'].append('HOLD: separate C12-series assignment in Figure4C inset is unresolved; use FigureS14 for directly identified C12 thermal evidence.')
r['quality']['review_scope'] += ' Hold the C12 assignment of Figure4C inset; the caption alternative is preserved and no separate C12 series is asserted.'
for rid, r in records.items():
    if r != before_records[rid]: r['revision'] += 1
    path=P/'candidate-site/data/records'/(rid+'.json')
    if r == before_records[rid]:
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes((B/'candidate-site/data/records'/(rid+'.json')).read_bytes())
    else: save(path,r)

assets = read(B/'asset-manifest.json')
f4 = next(x for x in assets if x['id']=='figure-4')
f4['caption_paraphrase']='C10 DSC and temperature-dependent diffraction. The visible inset is associated with the C10 diffraction panel; the printed caption additionally names C12 layer spacings, but a distinct C12 series cannot be identified. That inset assignment remains unresolved; SI FigureS14 directly identifies C12 thermal data.'
f4['sample_contexts']=['thermal-c10']
f4['source_caption_contexts_unresolved']=['thermal-c12-context']
add(f4['limitations'],['HOLD: the Figure4 caption names C10 and C12, but the visible inset does not separately identify a C12 series. Preserve this ambiguity; do not infer missing points or reassign the original plot.'])
save(P/'asset-manifest.json',assets)

extraction['revision']=2
extraction['figures_and_tables']=deepcopy(assets)
extraction['conflicts'].append({
    'id':'figure4-inset-sample',
    'claims':['Printed Figure4 caption names layer spacings for C10 and C12.','Visible Figure4C inset shows one series without a separately identified C12 trace.'],
    'scope':['study-context','thermal-c10','thermal-c12-context'],
    'source_locators':deepcopy(hold['evidence']),
    'handling':'Unresolved. Keep the source caption claim and visible-content limitation separate. Hold C12 assignment to this inset; FigureS14 is independent, explicitly labeled C12 evidence.'})
extraction['additional_source_context']['thermal']['figure4_inset_assignment_hold']=deepcopy(hold)
extraction['review_status']['independent_audit']='v1_failed; metadata_corrections_proposed; independent_delta_review_pending'
extraction['correction_provenance']={
    'base_extraction_file':'source-extraction-v1.json','base_extraction_sha256':sha(B/'source-extraction-v1.json'),
    'base_author_freeze_sha256':sha(B/'author-candidate-freeze.json'),
    'independent_audit_sha256':sha(A/'audit-report.json'),
    'issues_addressed':['R1','R2','R3','R4'],
    'scope':'Metadata/provenance proposal only. No numerical recipe/table/property edits, source-interpretation resolution, canonical integration, training admission or publication.',
    'independent_correction_acceptance':'pending',
    'claim_holds':[deepcopy(hold)]}

# Make the pre-existing origin pointers resolve to actual source-backed entries.
# Each entry has local material/operation/result links and exact source locators;
# it does not manufacture a new batch or silently duplicate scientific facts.
extraction['preparation_inventory']={}
extraction['recrystallization']={}
extraction['film_preparation']={}
for ref in extraction['canonical_candidate_records']:
    rid=ref['record_id'];r=records[rid];suffix=rid.removeprefix('rusch2026-')
    record_rel='candidate-site/data/records/'+rid+'.json'
    ref['sha256']=sha(P/record_rel)
    pointer=ref['origin_pointer']
    if pointer=='/stock_preparation': continue
    if suffix.startswith('rapid-'):
        prep=[ev('main',2,'Experimental Section: general silver bismuth halide preparation')]
        results=deepcopy(result_evidence[suffix])
        summary='Named amine/halide branch of the general rapid-precipitation method; common-method inheritance is qualified in the record. No unique physical batch or cross-technique aliquot identity is established.'
    elif suffix.startswith('rate-'):
        prep=[ev('main',2,'Experimental Section: general preparation'),ev('main',7,'Results: slow iodide-delivery controls'),ev('si',18,'FigureS20, C12 rate comparison; two traces per rate')]
        results=[ev('si',18,'FigureS20, rate-specific diffraction evidence')]
        summary='C12 addition-rate comparison. Preserve less-than1s,5min or60min as named; common quantities are inherited from general Methods. Rate-experiment temperature and unique replicate batches are not established.'
    elif suffix.startswith('temperature-'):
        prep=[ev('main',2,'Experimental Section: general preparation'),ev('main',7,'Results: injection-temperature controls'),ev('si',19,'FigureS21, discrete C12 injection temperatures0/21/50°C')]
        results=[ev('si',19,'FigureS21, temperature-specific diffraction evidence')]
        summary='Discrete C12 injection-temperature control; common quantities follow the general method. No interpolated temperature series, unique batch or cross-technique identity is asserted.'
    elif suffix.startswith('recrystallized-'):
        prep=[ev('main',2,'Recrystallization paragraph')]
        results=[ev('main',4,'Figure3 and structural results'),ev('main',5,'Table1, selected single-crystal summary')]
        summary='Separately recrystallized crystal from previously prepared powder dispersion. Acetone amount, evaporation time/temperature and physical parent batch remain unspecified; selected crystal dimensions do not describe initial powder.'
    elif suffix.startswith('film-'):
        prep=[ev('main',2,'Preparation of thin films')]
        results=[ev('main',7,'Figure5A/B, film diffraction and absorption'),ev('si',15,'FigureS16, fitted gap intercepts')]
        summary='Spin-coated film after additional ether washing and drying. Preserve400mg/0.2mL versus~0.2M and Tauc-exponent conflicts. Do not join the film to a unique powder batch or the unresolved PL specimen.'
    elif suffix=='hi-c10':
        prep=[ev('si',20,'FigureS22 caption, comparative aqueous-HI preparation')]
        results=[ev('main',7,'HI-route comparison'),ev('si',20,'FigureS22, main phase plus impurity reflections')]
        summary='Separate C10 route using0.1mmolAgI,0.1mmolBiI3,0.4mmoldecylamine in boiling aqueousHI then slow cooling. HI concentration/volume, numerical temperature and cooling rate remain unspecified.'
    elif suffix=='study-context':
        prep=[]
        results=[ev('main',6,'Thermal and optical/DFT discussion'),ev('main',7,'Control comparisons'),ev('main',8,'Stability and halide extension'),ev('si',11,'FigureS14 C12 thermal data'),ev('si',16,'FiguresS17/S18 PL and computed bands'),ev('si',17,'FigureS19 SOC DOS'),ev('si',21,'FigureS23 aging'),ev('si',24,'FigureS27 halide optics')]
        summary='Non-recipe characterization and theory contexts; detailed statements and exact locators reside in /additional_source_context. C12 Figure4C inset assignment is held; no unique specimen joins or measured local coordinates are admitted.'
    else: raise AssertionError(suffix)
    entry={'record_id':rid,'record_file':record_rel,'record_sha256':ref['sha256'],
        'source_scope':summary,'preparation_evidence':prep,'product_or_context_evidence':results,
        'record_payload_pointers':{'materials':'/materials','stocks':'/stocks','operations':'/operations','products':'/products','measurements':'/measurements'},
        'source_sample_labels':[x['source_sample_label'] for x in r['products']],
        'physical_batch_identity':None,'exact_coordinate_pair_status':'not_established'}
    if suffix=='study-context':entry.update({'context_pointer':'/additional_source_context','status':'hold','hold':deepcopy(hold)})
    parts=pointer.strip('/').split('/')
    if len(parts)==1:extraction[parts[0]]=entry
    else:extraction[parts[0]][parts[1]]=entry
save(P/'source-extraction-v2.json',extraction)
save(P/'candidate-site/data/paper-evidence/rusch2026-source-extraction.json',extraction)

review=read(B/'candidate-site/data/paper-reviews/rusch2026.json')
review['source_payload']=deepcopy(extraction)
review['figures']=[deepcopy(x) for x in assets if x['id'].startswith('figure-')]
review['evidence_conflicts']=deepcopy(extraction['conflicts'])
review['independent_audit']='v1_failed; metadata_corrections_proposed; independent_delta_review_pending'
review['audit_details']='Independent v1 audit found R1–R4. This separate correction candidate supplies metadata/provenance fixes and explicitly holds the unresolved C12 Figure4C inset assignment. Correction acceptance, canonical integration, browser QA, training admission and publication remain unapproved.'
for item in review['recipe_inventory']:
    r=records[item['id']]
    for prod in r['products']:
        for key in ['phase','morphology','composition']:add(item['source_locators'],prod[key]['evidence'])
    if item['id']=='rusch2026-study-context':
        item['status']='hold_unresolved_figure4_c12_inset_assignment'
        item['scope']=r['quality']['review_scope'];item['gaps']=deepcopy(r['quality']['missing_fields'])
save(P/'candidate-site/data/paper-reviews/rusch2026.json',review)
save(P/'claim-holds.json',[hold])

changes=[]
for rel in ['asset-manifest.json','candidate-site/data/paper-evidence/rusch2026-source-extraction.json','candidate-site/data/paper-reviews/rusch2026.json']+[f'candidate-site/data/records/{rid}.json' for rid in sorted(records)]:
    changes.append({'path':rel,'base_path':str(B/rel),'proposed_path':str(P/rel),'before_sha256':sha(B/rel),'after_sha256':sha(P/rel),'changed':sha(B/rel)!=sha(P/rel),'field_deltas':diff(read(B/rel),read(P/rel))})
changes.append({'path':'source-extraction-v2.json','base_path':str(B/'source-extraction-v1.json'),'proposed_path':str(P/'source-extraction-v2.json'),'before_sha256':sha(B/'source-extraction-v1.json'),'after_sha256':sha(P/'source-extraction-v2.json'),'changed':True,'field_deltas':diff(before_extraction,extraction)})
save(P/'field-deltas.json',changes)

tests=[]
def check(name,ok):tests.append({'check':name,'passed':bool(ok)})
for x in base_freeze['files']:check('immutable v1 '+x['path'],sha(B/x['path'])==x['sha256'])
for rid,r in records.items():
    old=before_records[rid]
    for field in ['materials','stocks','operations','condition_options','material_states','measurements','structure_assets','lineage']:
        check(rid+' unchanged '+field,r[field]==old[field])
    check(rid+' no training requested',r['quality']['requested_tasks']==old['quality']['requested_tasks']==[])
    for a,b in zip(old['products'],r['products']):
        check(rid+' product scientific values unchanged',all({k:v for k,v in a[q].items() if k!='evidence'}=={k:v for k,v in b[q].items() if k!='evidence'} for q in ['composition','phase','morphology','surface']))
        check(rid+' no physical batch added',a['batch_id']==b['batch_id']==None)
    for d in diff(old,r):
        q=d['pointer']
        permitted=q=='/revision' or q in ['/material/family','/material/architecture'] and rid=='rusch2026-bi-oleate' or q.startswith(('/products/0/phase/evidence','/products/0/morphology/evidence','/products/0/composition/evidence','/intended_target/composition/evidence')) or q in ['/quality/conflicts','/quality/missing_fields','/quality/review_scope'] and rid=='rusch2026-study-context'
        check(rid+' allowed delta '+q,permitted)
for ref in extraction['canonical_candidate_records']:
    x=extraction
    for part in ref['origin_pointer'].strip('/').split('/'):x=x[part]
    check(ref['record_id']+' origin resolves',isinstance(x,dict))
    check(ref['record_id']+' hash resolves',sha(P/'candidate-site/data/records'/(ref['record_id']+'.json'))==ref['sha256'])
check('all raw numerical tables unchanged',extraction['tables']==before_extraction['tables'])
check('original eight conflicts unchanged',extraction['conflicts'][:8]==before_extraction['conflicts'])
check('source documents unchanged',extraction['documents']==before_extraction['documents'])
check('stock source facts unchanged',extraction['stock_preparation']==before_extraction['stock_preparation'])
check('source extraction mirrored',read(P/'candidate-site/data/paper-evidence/rusch2026-source-extraction.json')==extraction==review['source_payload'])
for old,new in zip(read(B/'asset-manifest.json'),assets):
    check(old['id']+' image/crop binding unchanged',all(old[k]==new[k] for k in ['public_asset','sha256','source_sha256','render_sha256','crop_pixels','crop_normalized','page','document_role']))
check('C12 ambiguous inset removed from confirmed contexts','thermal-c12-context' not in f4['sample_contexts'])
check('C12 printed-caption alternative retained','thermal-c12-context' in f4['source_caption_contexts_unresolved'])
check('hold visible in study context',review['recipe_inventory'][-1]['status']=='hold_unresolved_figure4_c12_inset_assignment')
check('no source media copied',not any(p.suffix.lower() in ['.pdf','.png','.jpg','.txt'] for p in P.rglob('*') if p.is_file()))
save(P/'validation.json',{'passed':all(x['passed'] for x in tests),'checks':tests,'check_count':len(tests),'scope':'Correction-author mechanical/immutability/allowed-delta checks, not independent acceptance or deployment.'})
print(json.dumps({'files':len(changes),'changed_files':sum(x['changed'] for x in changes),'changed_records':sum(x['changed'] for x in changes if '/records/' in x['path']),'checks':len(tests),'failed':[x for x in tests if not x['passed']]}))
