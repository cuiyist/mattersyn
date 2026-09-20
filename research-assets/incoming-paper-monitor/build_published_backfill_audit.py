from pathlib import Path
import json, hashlib, tarfile
from datetime import datetime, timezone

ROOT = Path(r'[local path redacted]')
SITE = ROOT / 'recipe-atlas'
OUT = ROOT / 'research-assets/incoming-paper-monitor'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_text(encoding='utf-8'))
inventory_path = SITE / 'data/inventory-summary.json'
inventory = load(inventory_path)
release_path = ROOT / 'research-assets/quality-20260918/release-checkpoint.json'
release = load(release_path)
legacy = load(SITE / 'dist/data/paper-evidence/murray1993.json')
seed_audit = load(ROOT / 'research-assets/training-migration/new-families-audit.json')
source_seed = {s['id']: s for s in seed_audit['sources']}
selected_audit_path = ROOT / 'research-assets/quality-20260918/selected-figures/independent-audit.json'
selected_audit = load(selected_audit_path)

backfill = {
 'murray1993': {
  'completed_scope': 'All 10 main pages and all 15 main figures have documented text/visual characterization coverage; six selected CdSe canonical records exist. Precursor-reference extraction is separately scoped. No matching SI verified.',
  'independent_scope': 'Read-only migration audit and later complete-main characterization audit exist; not a formal all-route main-plus-SI independent coverage ledger.',
  'reuse': ['Six canonical CdSe records and their bounded method/procedure evidence.', 'All 15 original main-figure crops, figure-specific facts and conservative unresolved sample joins.', 'Separate precursor-reference preparation boundary and -35 C Murray storage attribution.'],
  'backfill': ['Create a unified formal coverage ledger without losing existing reviewed characterization evidence.', 'Review and migrate source-described CdS/CdTe method variants and small-species cases separately; they were explicitly left as future variants in migration audit.', 'Inventory every original equation and precursor/reference preparation disposition alongside figure coverage; do not substitute an ideal CIF for faulted experimental particles.', 'Check newly arriving local SI candidates by identity and content; absent SI remains unverified.'],
  'irreducible_gaps': ['No exact figure-specimen-to-Method-1/Method-2 operating tuple or uniquely identified physical batch.', 'No measured atomic coordinates; SAED described in text but no main-article SAED image.', 'No raw-curve digitization, precise growth-time size series, or source-wide complete laboratory SOP.'],
  'source_evidence': ['dist/data/paper-evidence/murray1993.json', '../research-assets/training-migration/murray-audit.json'],
 },
 'peng2000': {
  'completed_scope': 'Three-page main extraction, later all-three-page bounded characterization/SAED inspection and four-figure inventory; two partial CdSe synthesis records. Matching SI unverified.',
  'independent_scope': 'Migration audit independently rechecked main page 2 visually and page 3 text, plus later bounded three-page SAED/figure audit; not a formal comprehensive paper/SI second read.',
  'reuse': ['Two canonical typical/high-aspect protocol families, explicit thermal alternatives and missingness.', 'Existing four-figure technique/sample inventory; Figure 2 is XRD, Figure 4c is shell-grown optical context.'],
  'backfill': ['Make a formal complete main-item/method/variant ledger and check any new local SI.', 'Extract and independently check original Figures 1–4; no attributed public Peng original-figure crop package was found in the checked assets/ledgers.', 'Reconcile existing partial HPA condition-series observations with canonical representations without manufacturing fully quantified runs.', 'Bring the legacy alivisatos-2000.html reader to the current academic five-section presentation. It retains promotional headings and the older four-section design; a publication badge does not establish CdSe-standard parity.'],
  'irreducible_gaps': ['Growth duration, stock concentration/amounts, gas/pressure, full workup, and exact recipe-to-figure joins are incomplete.', 'No SAED image in supplied main article; shell-related optical values cannot become bare-core recipe outcomes.'],
  'source_evidence': ['dist/data/paper-evidence/murray1993.json#/related_paper_saed_check/peng2000', '../research-assets/training-migration/other-records-audit.json', 'dist/alivisatos-2000.html'],
 },
 'tessier2015': {
  'completed_scope': 'Selected InP Reference 1 preparation, relevant characterization and three main/SI original figure crops; matched local main/SI identity. Not a whole-document review.',
  'independent_scope': 'Independent audit of the selected preparation and three figures/sample assignments; expressly whole_paper_review=false.',
  'reuse': ['One InP core record, provenance-linked quantities and source conflicts.', 'Three visually verified crops: Figure 1, S3, S4; 20-minute characterization not asserted to be the 30-minute Reference 1 specimen.'],
  'backfill': ['Read remaining pages of the 6-page main and 20-page SI before declaring full coverage.', 'Inventory all halide/precursor/condition comparisons, shell-growth routes, precursor preparations, controls and workup/sample branches.', 'Extract all remaining figures/tables/equations and properties with specimen assignments; audit new records independently.'],
  'irreducible_gaps': ['30-minute recipe versus 20-minute characterization and 33-minute SI trace remain distinct.', 'Full-chemical-yield heading versus 75–80% contextual yield; do not make an exact 100% isolated-yield label.', 'ZnCl2 addition does not establish a quantified InZnP alloy; exact sample atomic coordinates absent.'],
  'source_evidence': ['dist/data/recipe-figures/tessier2015.json', '../research-assets/training-migration/new-families-audit.json', '../research-assets/quality-20260918/selected-figures/independent-audit.json'],
 },
 'zhang2019': {
  'completed_scope': 'Selected TDPA-only CsPbBr3 protocol with selected optical/structural facts and six original figure/table crops; matched local main/SI identity. Not a whole-document review.',
  'independent_scope': 'Independent selected-figure/sample/crop audit passed after corrections; explicitly not full main/SI coverage.',
  'reuse': ['One TDPA-only canonical record and its source conflicts.', 'Six reviewed crops with correct TDPA-only versus mixed-ligand panel assignments, fit components and FTIR interpretation.'],
  'backfill': ['Read remaining pages of the 8-page main and 13-page SI.', 'Extract distinct mixed-ligand formulations, stability/control experiments and their own synthesis/property tuples; never copy TDPA-only labels.', 'Review remaining NMR, ligand chemistry, computations and other source items, separating measured data from author models.', 'Create a full coverage ledger and independent complete extraction audit before expanding training scope.'],
  'irreducible_gaps': ['Cs2CO3 printed mass/amount basis conflict; DLS radius/diameter wording conflict; orthorhombic phase versus cubic facet nomenclature.', 'SI S3 plot/caption panel mismatch remains documented; fitted decay components are not separate sample lifetimes.', 'No sample-specific atomistic CIF, exact batch/repeat IDs or fully specified workup.'],
  'source_evidence': ['dist/data/recipe-figures/zhang2019.json', '../research-assets/training-migration/new-families-audit.json', '../research-assets/quality-20260918/selected-figures/independent-audit.json'],
 },
 'voznyy2019': {
  'completed_scope': 'Published full.dat numerical import of 2,552 rows validated; 100 coverage-selected rows canonical/public (95 optical targets and five failure-coded rows). Source method/data semantics and author code inspected in bounded scope. No full main/SI coverage ledger.',
  'independent_scope': 'Independent numerical validation reproduces all rows, failure handling, cohort rule, selected-row mapping, grouped splits and baseline predictions; this is not full-source scientific curation.',
  'reuse': ['Verified numerical source hashes, 100 exact selected rows, source feature definitions, CC BY-NC attribution and failure-null handling.', 'Full 2,552-row local numerical benchmark and separately validated baselines; no author code execution needed.'],
  'backfill': ['Read/inventory complete local main and SI, including synthesis stock preparation, structure/property characterization, controls and original figures.', 'Separately curate the six experimentally verified optimized Table 1 variants after full source/sample audit; do not equate these to model sweeps.', 'Keep benchmark optical supervision separate from full recipe-generation records and reader material pages.', 'Retain author-pooled/rescaled chloride semantics and unknown physical-run dates; never fill per-row species/time from generic prose.'],
  'irreducible_gaps': ['Per-row duration, exact historical chloride identity, direct diameter, crystal phase/coordinates and complete workup/storage absent from numeric table.', 'Seasonal outdoor temperature is a proxy, not measured lab temperature.', 'Author cohorts are a code rule, not verified chronology; generated/model-predicted sweeps are not experiments.'],
  'source_evidence': ['data/README.md', 'benchmarks/README.md', '../research-assets/training-migration/pbs2019-benchmark-validation.json', '../research-assets/training-migration/pbs2019-data-block-assessment.json'],
 },
 'feld2019': {
  'completed_scope': 'Full supplied 11-page main and 19-page matched SI reading/visual ledger, all 36 original graphics/equation crops, nine canonical records.',
  'independent_scope': 'Targeted audit of quantities, precursor/aliquot joins, FFT/SAED distinction and all nine record summaries; explicitly not a second complete 30-page read.',
  'reuse': ['Full first-pass page/item inventory, nine canonical records, 36 crops and detailed 15-conflict ledger.', 'Explicit phase/stoichiometry-unresolved Fe–O identity and excluded exact-structure/diameter assumptions.'],
  'backfill': ['Perform a second full-page independent check only if required by the new completeness gate; current independent evidence is targeted.', 'Reconcile all noncanonical mechanistic/characterization facts and all 14 inventoried recipe/procedure/context items with explicit canonical/context dispositions.', 'Recheck source-to-record-to-reader joins for any new property fields; numeric curve digitization is separate optional work, not already done.'],
 },
 'fu2007': {
  'completed_scope': 'Full supplied five-page main/four-page matched SI ledger; seven main figures, three SI figures and one unnumbered surface-reaction scheme; six canonical records.',
  'independent_scope': 'Documented independent full nine-page text/visual and numerical/variant/specimen audit, with corrections and regeneration validation.',
  'reuse': ['Full page/item coverage and six corrected S1–S4/post-treatment records.', 'Eleven original figure/scheme crops; confinement equation and mechanistic model context inventoried separately.'],
  'backfill': ['Verify that every covered model/property fact is exposed with the correct measured/author-derived distinction when richer property fields are added.', 'Retain S1/S2 and acid/OA post-treatment sample states, precursor substitutions and unresolved quantities; do not infer their missing settings.', 'Recheck only affected source/record/view joins after schema changes or newly arrived SI; existing unchanged reviewed assets need not be regenerated.'],
 },
 'nakonechnyi2017': {
  'completed_scope': 'Full supplied nine-page main/seven-page matched SI reading and visual ledger; eight numbered figures, two unnumbered graphics, two tables; 17 canonical records including nine controls.',
  'independent_scope': 'Targeted independent audit of all 17 record quantities/flow/lineage, relevant original methods, Figures 1,2,4,S1,S2 and Table 1; not a second whole-source claim.',
  'reuse': ['Full 16-page first-pass ledger, 12 original crops and 17 corrected records.', 'Actual SAED core/shell-family evidence with conservative seed/sample joins and separate simulation model inventory.'],
  'backfill': ['A full second-page independent audit is not documented; do it only if the new gate requires it, preserving prior targeted checks.', 'Audit disposition of 25 inventory entries versus 17 canonical records: supporting stocks/control contexts/models must remain explicitly contextual where unparameterized.', 'If locally available cited original preparations are later reviewed in queue order, join them as separate source records; do not borrow upstream conditions now.', 'Do not multiply unassigned ZnSe characterization into three measured outcomes for 25/50/100 nmol seed variants.'],
 },
 'saha2019': {
  'completed_scope': 'Full supplied seven-page main/three-page matched SI, eight numbered figures plus graphical abstract, one table, two equations; four canonical records and 19 observations.',
  'independent_scope': 'Independent all-ten-page, all-12-crop, four-record and 19-measurement source-consistency audit documented.',
  'reuse': ['Two synthesis routes plus two supporting acquisition/assay records and 12 original crops.', 'Correct acetate identities, 15/30-minute lineage and CoFe2O4-as-shell scope with six unresolved source conflicts.'],
  'backfill': ['Retain 15-minute aliquot as distinct incompletely characterized lineage; do not transfer 30-minute TEM/magnetism.', 'Any expanded magnetic/property normalization must retain full powder mass, sedimentation and source cooling/color conflicts.', 'No standalone CoFe2O4 recipe should be created from this source; material/component hub remains architectural context.', 'Recheck affected view/record paths after schema changes, not an unnecessary repeat of unchanged complete source reading.'],
 },
 'stowell2005': {
  'completed_scope': 'Full supplied five-page main/four-page matched SI; five original figures and two original equation crops; four synthesis variants plus five supporting/assay records.',
  'independent_scope': 'Independent all-nine-page, five-figure and equation audit documented; corrected OA/oleylamine surface label and preserved source conflicts.',
  'reuse': ['Nine canonical records, seven original crops, radius-model/TOF formulas and independent audit corrections.', 'Distinct initial/recycled TOPB series and ligand-dependent assay state semantics.'],
  'backfill': ['Audit explicit disposition of 11 recipe/context inventory items versus nine records, preserving unparameterized overwashing/context as such.', 'Richer catalytic-property fields must keep total-surface-site normalization, distinct activation/recycling cohorts and unresolved TOF differences.', 'Do not repair the printed microlitre ligand amounts, formula or pressure/solvent conflicts without new source evidence.', 'No repeat whole-source read required solely because new schema fields are introduced; audit affected source/record/view mapping.'],
 },
}

def walk(o):
    if isinstance(o, dict):
        yield o
        for v in o.values(): yield from walk(v)
    elif isinstance(o, list):
        for v in o: yield from walk(v)

checked_inputs = {str(inventory_path.relative_to(ROOT)): sha(inventory_path), str(release_path.relative_to(ROOT)): sha(release_path), str(selected_audit_path.relative_to(ROOT)): sha(selected_audit_path)}
results=[]
archive_checks={}
source_roots=[ROOT/'downloaded_papers', Path(r'[local path redacted]'), ROOT/'research-assets']
for entry in inventory['per_paper']:
    sid=entry['source_group'];info=backfill[sid];ledger_path=SITE/f'data/paper-reviews/{sid}.json'
    ledger=load(ledger_path) if ledger_path.exists() else None
    if ledger:
        ev=ledger
        checked_inputs[str(ledger_path.relative_to(ROOT))]=sha(ledger_path)
        documents=ledger['documents']
        info['irreducible_gaps']=ledger.get('remaining_gaps',[])
        info['source_evidence']=[f'data/paper-reviews/{sid}.json']
        item_counts={k:len(ledger.get(k,[])) for k in ['figures','tables','equations','schemes','recipe_inventory']}
        audit_detail=ledger.get('audit_details')
    else:
        if sid=='murray1993':ev=legacy;documents=[{'role':'main','source_file':'10.1021_ja00072a025.pdf','sha256':legacy['source']['sha256'],'page_count':10}]
        elif sid=='peng2000':ev=legacy['related_paper_saed_check']['peng2000'];documents=[{'role':'main','source_file':'35003535.pdf','sha256':ev['sha256'],'page_count':3}]
        elif sid in source_seed:
            ev=load(SITE/f'dist/data/recipe-figures/{sid}.json');s=source_seed[sid]
            documents=[{'role':role,'source_file':Path(s[role+'_file']).name,'page_count':s[role+'_page_count']} for role in ['main','si']]
            for doc in documents:
                matches=[f['source_sha256'] for f in ev['figures'] if f['document_role']==doc['role']]
                if matches:doc['sha256']=matches[0]
        else:ev={};documents=[]
        item_counts={'retained_original_items':len(ev.get('figures',[])) if sid!='peng2000' else 0,'full_source_item_inventory_complete':False}
        audit_detail=info['independent_scope']
    docs=[]
    for doc in documents:
        available=[]
        for base in source_roots:
            p=base/doc['source_file']
            if p.exists():available.append(p)
        if sid=='murray1993' and not available:available=[ROOT/'research-assets/murray1993-main.pdf']
        doc_check={'role':doc['role'],'file':doc['source_file'],'recorded_pages':doc['page_count'],'recorded_sha256':doc.get('sha256'),'locally_found':bool(available),'first_pass_text_pages_recorded':sum(bool(x.get('text_read')) for x in doc.get('pages',[])) if 'pages'in doc else None,'first_pass_visual_pages_recorded':sum(bool(x.get('visual_review')) for x in doc.get('pages',[])) if 'pages'in doc else None}
        if available:
            doc_check['checked_path']=str(available[0]);doc_check['current_sha256']=sha(available[0]);doc_check['hash_matches_record']=doc.get('sha256')==doc_check['current_sha256'] if doc.get('sha256') else None
        docs.append(doc_check)
    assets={}
    for node in walk(ev):
        if 'public_asset'in node and isinstance(node['public_asset'],str):assets[node['public_asset']]=node.get('public_asset_sha256')
        if sid=='murray1993' and 'original_figure_asset'in node:
            a=node['original_figure_asset']
            if isinstance(a,dict) and a.get('file'):assets[a['file']]=a.get('sha256')
    # Murray nested related-paper evidence is not Murray's original item set.
    if sid=='murray1993':assets={k:v for k,v in assets.items() if '/murray1993-figures/'in k}
    asset_checks=[]
    for path,expected in assets.items():
        p=SITE/'dist'/path;actual=sha(p) if p.exists() else None
        asset_checks.append({'path':path,'recorded_sha256':expected,'current_sha256':actual,'exists':p.exists(),'hash_matches_record':expected==actual if expected else None})
        archive_checks['dist/'+path]=actual
    canon=[];missing=[];conflicts=[];statuses=set();scopes=set()
    for rid in entry['record_ids']:
        p=SITE/'data/records'/f'{rid}.json';pub=SITE/'dist/data/records'/f'{rid}.json';h=SITE/'dist/records'/f'{rid}.html';rec=load(p)
        quality=rec.get('quality',{});missing.extend(quality.get('missing_fields',[]));conflicts.extend(quality.get('conflicts',[]));statuses.add(quality.get('review_status'));scopes.add(quality.get('review_scope',''))
        canon.append({'record_id':rid,'canonical_sha256':sha(p),'public_json_exists':pub.exists(),'canonical_equals_public_json':pub.exists() and rec==load(pub),'html_exists':h.exists()})
        if pub.exists():archive_checks['dist/data/records/'+rid+'.json']=sha(pub)
        if h.exists():archive_checks['dist/records/'+rid+'.html']=sha(h)
    evidence_path=entry['evidence_locator'].split('#')[0]
    if (SITE/evidence_path).exists():checked_inputs[str((SITE/evidence_path).relative_to(ROOT))]=sha(SITE/evidence_path)
    result={'source_group':sid,'doi':entry['doi'],'title':entry['title'],'counts':{'canonical_records':entry['canonical_record_count'],'synthesis_route_variant_records':entry['synthesis_route_variant_count'],'contextual_control_records':entry['contextual_control_count'],'supporting_procedures':entry['procedure_count'],'benchmark_rows':entry['benchmark_row_count']},'inventory_review_status':entry['review_status'],'quality_statuses':sorted(statuses),'documents':docs,'item_counts_as_represented_in_ledger':item_counts,'original_public_asset_count':len(asset_checks),'original_public_assets':asset_checks,'independent_audit_details_as_recorded':audit_detail,'canonical_checks':canon,'canonical_missing_fields':sorted(set(missing)),'canonical_conflicts':sorted(set(conflicts)),'canonical_review_scopes':sorted(scopes),'source_evidence_conflicts':ledger.get('evidence_conflicts',[]) if ledger else [],'reusable_and_backfill':info,'complete_for_all_information_and_training':False}
    results.append(result)

archive_path=SITE/'.sites-runtime/site-v11.tar.gz';archive_results={}
with tarfile.open(archive_path,'r:gz') as tf:
    for member in tf:
        if member.name in archive_checks:
            digest=hashlib.sha256(tf.extractfile(member).read()).hexdigest()
            archive_results[member.name]={'archived_sha256':digest,'current_bytes_match_published_archive':digest==archive_checks[member.name]}
for result in results:
    prefixes=[f"dist/data/records/{c['record_id']}.json" for c in result['canonical_checks']]+[f"dist/records/{c['record_id']}.html" for c in result['canonical_checks']]+['dist/'+a['path']for a in result['original_public_assets']]
    result['publication_evidence']={'recorded_public_version':release['public_live_version'],'recorded_deployment_status':release['deployment_status'],'artifact_count_checked':len(prefixes),'all_present_and_matching_version11_archive':all(archive_results.get(p,{}).get('current_bytes_match_published_archive',False)for p in prefixes),'live_site_fetched_in_this_audit':False,'browser_behaviour_rechecked':False}

report={'audit_version':'published-source-backfill-1','created_utc':datetime.now(timezone.utc).isoformat(),'scope':'Read-only evidence-file bookkeeping for exactly ten source groups in the published version11 inventory. No research papers read, no downloads, no Site writes/lifecycle calls, no claims about unreviewed corpus or current incoming collection totals. Hash checks do not validate scientific truth.','evidence_inputs':checked_inputs,'publication_checkpoint':release,'publication_archive_sha256':sha(archive_path),'publication_archive_matches_recorded_sha256':sha(archive_path)==release['archive_sha256'],'sources':results,'summary':{'source_groups':len(results),'canonical_records':sum(x['counts']['canonical_records']for x in results),'formal_main_si_first_pass_sources':5,'formal_main_si_first_pass_pages':74,'independent_full_supplied_page_audits_documented':['fu2007','saha2019','stowell2005'],'independent_targeted_audits_of_full_first_pass_sources':['feld2019','nakonechnyi2017'],'legacy_main_only_sources':['murray1993','peng2000'],'selected_recipe_figure_sources':['tessier2015','zhang2019'],'numeric_benchmark_sources':['voznyy2019'],'source_original_asset_count_checked':sum(x['original_public_asset_count']for x in results),'all_current_records_match_generated_public_json':all(c['canonical_equals_public_json']for x in results for c in x['canonical_checks']),'all_known_original_assets_present_and_hash_verified':all(a['exists']and a['hash_matches_record']for x in results for a in x['original_public_assets']),'all_record_html_json_and_known_original_assets_match_version11_archive':all(x['publication_evidence']['all_present_and_matching_version11_archive']for x in results),'verified_exact_structure_recipe_pairs_as_inventory':inventory['summary']['verified_exact_structure_recipe_pairs']},'reuse_policy':['Reuse unchanged source hashes, reviewed extracted facts, original-item crops, existing canonical records and source-specific scientific caveats within their documented scope.','Newly arriving SI or changed source content reopens the affected source review; retain earlier provenance instead of silently replacing it.','First-pass complete reading, independent audit, item coverage, typed extraction, display integration, successful deployment and task-specific training eligibility are separate states.','Do not treat source_reviewed or deployment success as comprehensive extraction, laboratory reproduction, full numerical-data recovery, or reader-quality parity.','Present known source omissions/conflicts as such. Backfill means recovering neglected local source information, not guessing or downloading without renewed user instruction.','No source in this map is declared complete for every possible property/recipe/atomic-structure training task.'], 'new_findings':[{'source_group':'peng2000','issue':'Legacy public reader has older promotional headings/four-section structure and lacks an attributed original-figure crop package in checked public assets; it needs a reader-quality backfill despite published canonical routes.','evidence':'dist/alivisatos-2000.html and public asset filename inventory'}]}
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'published-source-backfill-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=['# Published-source backfill audit','','Evidence-file audit only: no new papers read, no downloads, no website edits. Covers exactly the ten source groups in the version11 publication snapshot. Successful publication and `source_reviewed` do not mean comprehensive data extraction, fully specified SOPs, or all-task training readiness.','','## Verified reuse boundary','',f"The saved version11 publication archive matches its checkpoint hash. Checked {report['summary']['canonical_records']} canonical-to-public JSON pairs and {report['summary']['source_original_asset_count_checked']} attributed original assets. All semantic record copies match: {report['summary']['all_current_records_match_generated_public_json']}. All listed asset hashes match: {report['summary']['all_known_original_assets_present_and_hash_verified']}. All checked public record pages/data/assets match the version11 archive: {report['summary']['all_record_html_json_and_known_original_assets_match_version11_archive']}.",'','Five ledgers document74 fully read/visually inspected main+SI pages. Only Fu, Stowell and Saha document a second full supplied-page independent audit; Feld and Nakonechnyi have substantial targeted independent audits. Murray/Peng are legacy main-only; Tessier/Zhang selected-only; Voznyy a numerical benchmark. This does not downgrade completed checks; it prevents extending their scope.','','| Source | Main/SI review scope | Canonical units | Retained original items | Principal backfill |','|---|---|---:|---:|---|']
for x in results:
    b=x['reusable_and_backfill'];lines.append(f"| {x['source_group']} | {x['inventory_review_status']} | {x['counts']['canonical_records']} | {x['original_public_asset_count']} | {b['backfill'][0]} |")
for x in results:
    b=x['reusable_and_backfill'];lines+=['',f"## {x['source_group']} — {x['title']}",'',b['completed_scope'],'',f"Independent check: {b['independent_scope']}",'','Reusable evidence:','']+['- '+s for s in b['reuse']]+['','Backfill/recheck:','']+['- '+s for s in b['backfill']]+['','Remaining source limitations:','']+['- '+s for s in b.get('irreducible_gaps',[])]+['','Evidence: '+', '.join(b['source_evidence'])+'.']
lines+=['','## Limits and next-pass rules','','No browser controls were exercised in this audit. Archive presence proves publication of bytes, not a well-rendered scientific explanation on every route. Full ledgers already preserve original-item inventories; their raw curves remain undigitized and many specimen identities are irrecoverable from supplied sources. External methods cited by the papers remain separate unreviewed originals unless an existing audit explicitly says otherwise.','','Keep existing verified evidence and hashes. Reopen only changed/newly supplied source sections and affected mappings when appropriate. The next curation gate should record main reading, SI identity/reading, extraction, independent scope, original-item disposition, reader integration, and publication separately. Do not mark any of the ten sources “all information complete” from a single badge.']
(OUT/'published-source-backfill-audit.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps(report['summary'],indent=2))
print('Saved private published-source-backfill-audit.json and .md')
