"""Refresh the saved progress report from scoped overnight audit receipts."""
import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[3]
SITE = PROJECT.parent / 'mattersyn-github-public-clean' / 'mattersyn-site'
DEST = Path(__file__).parent
EVIDENCE = {
    'acs_r2_author_qa': ('research-assets/detailed-reviews/acsnano1c00502/site-candidate-r2/candidate-qa-report.json', '43013b4c41138ceee93b75252e0d133661833bc31efca8c24a6f9d5c03f41a16'),
    'wu_independent_site_audit': ('research-assets/deep-review-screen-passes-20260924/copper-sulfide/independent-site-audit-agent-chen-20260924/audit-report.json', '8f165edc9eb37278dedfea95b2f38170893badb813572d8a6298907ae1bf7926'),
    'dhaene_locator_proposal': ('research-assets/deep-review-screen-passes-20260924/phosphinate-cdse/site-candidate-r1/locator-correction-proposal/proposal-freeze.json', '292d0df9f689d2adfc1bb1e09c832d29b6aff531034ae2a7f4ed39eb4584c079'),
}
for label, (rel, expected) in EVIDENCE.items():
    assert hashlib.sha256((PROJECT / rel).read_bytes()).hexdigest() == expected, label

path = SITE / 'data' / 'review-progress.json'
data = json.loads(path.read_text(encoding='utf-8-sig'))
before_counts = copy.deepcopy(data['published'])
now = datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
data['updated_at'] = now
by_name = {x['short_label']: x for x in data['current_work']}

def stage(label, status, detail):
    return {'label': label, 'status': status, 'detail': detail}

overview = by_name['Pass-set curation']
overview['stage'] = 'Overnight candidates and audits saved; no new source paper published. Three bounded review/correction tasks were restarted this morning.'
overview['summary'] = 'Public scientific totals remain 698 records, 140 routes, 52 material hubs and 37 formal source readers; exact coordinate-recipe pairs remain 0. The ACS Nano R2 reader passed author browser checks and is now under independent acceptance review. Wu Cu2S requires illustration, asset and molecular-binding fixes after its independent site audit. Dhaene CdSe has an SI page-locator correction undergoing independent recheck. Existing Chen/Banerjee page corrections are excluded from the new-paper count. These are saved work states, not proof of continuous overnight execution.'
overview['stages'] = [
    stage('Initial source screen', 'in_progress', '10,702/10,802 distinct contents screened; 100 remain access-blocked and unreviewed. No new screening credited in this checkpoint.'),
    stage('Independent reader acceptance', 'in_progress', 'ACS Nano CoNi2S4 R2: source claims, original figures, molecular drawings and browser behavior are being independently checked.'),
    stage('Reader corrections', 'in_progress', 'Wu Cu2S: prepare a separate R2 with substrate-specific device-heating scenes, the missing product-context endpoint and correct download wording; complete molecular/solution bindings.'),
    stage('Source-locator correction', 'in_progress', 'Dhaene CdSe: independent recheck of all 24 SI page labels and the Figure S15 location; preserve the 1 h/30 min source disagreement.'),
    stage('500/day requirement', 'in_progress', 'No newly completed paper contributions today. The target remains unachieved; drafts, corrections and unpublished candidates are excluded.'),
]

acs = by_name['ACS Nano · 10.1021/acsnano.1c00502']
acs['stage'] = 'R2 reader candidate frozen; author mechanical/browser checks passed. Independent reader acceptance is now active.'
acs['summary'] = 'The source extraction correction previously passed its separate 450-check re-audit. The R2 site candidate contains 14 source figure crops, 8 molecular SVGs and 15 downloads. All 16 issue records remain; 13 disagreements have separately cited claim pairs. Author checks passed at 1440/768/390 px with all images/downloads loading. Those checks do not replace independent scientific/visual acceptance. The candidate remains isolated and unpublished; no training admission.'
acs['stages'] = acs['stages'][:3] + [
    stage('Reader candidate and author QA', 'complete', 'Isolated R2 frozen; author reports 24/24 mechanical checks and three-width browser QA passed.'),
    stage('Independent reader acceptance', 'in_progress', 'Recheck prior blockers and new figure/molecular/source bindings against the frozen candidate and original evidence.'),
    stage('Canonical integration and publication', 'pending', 'Requires independent acceptance, integration and live verification; no paper completion credited.'),
]

wu = by_name['Wu et al. (2008)']
wu['stage'] = 'Independent R1 site audit preserved source claims but requested corrections. R2 fixes are active.'
wu['summary'] = 'The five-page source extraction and independent source audit were already complete. The R1 reader audit checked four uncertainty groups with eight located claims, 11 routes and 51 operations. Source-value checks passed, but site acceptance failed: device-heating artwork showed vials instead of the appropriate substrates; product-contexts.json was missing; the README overstated exact byte preservation. Molecular/solution bindings remain a separate gate. The next revision retains the source claims and corrects these presentation problems.'
wu['stages'] = [
    stage('Source reading and extraction', 'complete', 'Five-page source and supplied figures read; scoped extraction frozen.'),
    stage('Independent scientific audit', 'complete', 'Source audit and targeted corrections passed; ambiguity remains explicitly qualified.'),
    stage('Independent R1 site audit', 'complete', 'Audit finished with changes requested: 654/658 browser/mechanical checks and 5/5 schema checks; this is not acceptance.'),
    stage('Reader R2 and molecular/solution bindings', 'in_progress', 'Correct the identified art/asset/documentation issues and finish source-appropriate molecular contexts.'),
    stage('Recheck and publication', 'pending', 'No canonical/public promotion or training admission.'),
]

cdse = by_name['Phosphinate-ligated CdSe']
cdse['stage'] = 'Dhaene et al. (2022): SI page-locator correction proposal frozen; independent targeted recheck is active before integration.'
cdse['summary'] = 'The distinct source DOI 10.1021/acsnano.1c08966 is not already represented in the current canonical records. Prior extraction and rechecks covered the supplied 12 main and 24 SI pages. Integration preflight found a wrong universal +1 SI page-offset rule: printed S10/Figure S15 is PDF page 10, not 11. A bounded correction proposal preserves the original evidence and the unresolved 1 h/30 min statements. All 24 page-label mappings are now being independently checked; the source is not yet ready for publication.'
cdse['stages'] = [
    stage('Source reading and extraction', 'complete', 'Supplied main and 24-page SI extraction frozen with separate variants and evidence.'),
    stage('Prior source audits', 'complete', 'Prior receipts retained; the later-discovered locator defect remains explicitly open.'),
    stage('Targeted locator recheck', 'in_progress', 'Check SI page numbering and Figure S15 against original rendered pages and exact frozen hashes.'),
    stage('Reader integration and publication', 'pending', 'Apply accepted locator corrections in a versioned candidate before reader acceptance.'),
]

saini = by_name['Saini et al. (2023)']
saini['stage'] = 'A previous complete independent audit requested DLS/NMR corrections. Author corrections are queued; no active worker is rereading the 119 unchanged pages.'
saini['summary'] = 'The complete 119-page independent audit was found and reconciled with the current frozen inputs. Integrity checks passed 287/287. DLS weighting qualification and three NMR text/plot conflicts still require an author addendum, followed by a targeted independent recheck. The source is not published. The earlier pending-first-audit label was stale.'
for item in saini['stages']:
    if item['label'] == 'Independent audit':
        item.update(status='complete', detail='Prior 119-page audit completed with changes requested; current input bindings checked. Audit completion does not mean acceptance.')
    elif item['label'] == 'Reader and dataset integration':
        item['detail'] = 'Queued after DLS/NMR corrections and targeted acceptance; no promotion.'
saini['stages'].insert(3, stage('Author corrections and targeted recheck', 'pending', 'DLS weighting qualification and three NMR text/plot conflicts; preserve original audit history.'))

by_name['Rusch/Manna · Chem. Mater. 2026']['stage'] = 'Isolated reader candidate prepared; remaining molecular/solution graphics and independent integration/browser acceptance are queued. Figure 4 C12 remains on hold.'
by_name['Tirosh et al. (2006)']['stage'] = 'The source corrections and Fe-alkoxide option-identity targeted recheck passed; final reader/browser integration is queued. The printed 300 K statement remains unresolved.'
data['daily_throughput']['capacity_note'] = 'The 500/day target remains unachieved. Three bounded tasks resumed this morning after the previous assignments finished: ACS Nano reader audit, Wu reader corrections, and Dhaene SI locator recheck. No paid API/cloud run is active. Corrections to existing Chen and Banerjee pages are not new papers.'
data['daily_throughput']['as_of_date'] = '2026-09-24'
data['daily_throughput']['date_timezone'] = 'America/Chicago'
data['recent_milestones'].insert(0, {'at': now, 'text': 'Morning reconciliation: ACS R2 author QA completed; Wu independent site audit requests corrections; Dhaene SI page-offset correction awaits recheck. Three next tasks resumed. No new published paper or exact coordinate-recipe pair.'})
assert data['published'] == before_counts
assert data['daily_throughput']['completed_papers_today'] == 0
path.write_bytes((json.dumps(data, indent=2, ensure_ascii=False) + '\n').encode('utf-8'))
checkpoint = {'timestamp_utc': now, 'scope': 'Saved overnight receipts and morning task restart; no continuous-runtime claim', 'evidence': EVIDENCE, 'new_papers_published': 0, 'scientific_counts_unchanged': True, 'current_tasks': ['ACS Nano R2 independent reader audit', 'Wu Cu2S R2 author corrections', 'Dhaene CdSe SI locator independent recheck'], 'progress_json_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'github_delivery': 'pending'}
(DEST / 'checkpoint.json').write_bytes((json.dumps(checkpoint, indent=2) + '\n').encode('utf-8'))
print(json.dumps(checkpoint, indent=2))
