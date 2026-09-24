"""Correct the overnight count using the first publication commit, not a later baseline."""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[3]
SITE = PROJECT.parent / 'mattersyn-github-public-clean' / 'mattersyn-site'
DEST = Path(__file__).parent
DOI = '10.1021/acsami.8b04556'
FIRST = 'a30be07'

def at(ref, filename):
    return subprocess.check_output(['git', '-C', str(SITE), 'show', f'{ref}:{filename}']).decode('utf-8')

prior_index = json.loads(at(FIRST + '^', 'data/paper-review-index.json'))['papers']
first_index = json.loads(at(FIRST, 'data/paper-review-index.json'))['papers']
current_index = json.loads((SITE / 'data/paper-review-index.json').read_text(encoding='utf-8'))['papers']
assert not any(x.get('doi') == DOI for x in prior_index)
first = [x for x in first_index if x.get('doi') == DOI]
current = [x for x in current_index if x.get('doi') == DOI]
assert len(first) == len(current) == 1
required = ['source_extraction_passed', 'canonical_reader_mapping_passed', 'molecular_solution_bindings_passed']
assert all(x in current[0]['independent_audit'] for x in required)
before_rows = [json.loads(s) for s in at(FIRST + '^', 'data/records.jsonl').splitlines() if s.strip()]
after_rows = [json.loads(s) for s in at(FIRST, 'data/records.jsonl').splitlines() if s.strip()]
assert (len(before_rows), len(after_rows), len(first[0]['record_ids'])) == (675, 698, 23)
browser = PROJECT.parent / 'mattersyn/research-assets/incoming-paper-monitor/batches/20260922-resumed-review/legacy--10.1021_acsami.8b04556--261eafeba8a3/browser-qa-20260924/final-browser-qa-receipt.json'
browser_hash = hashlib.sha256(browser.read_bytes()).hexdigest()
assert browser_hash == '15310d2c0cad4eb10b80597f94fe240ba50fb59cca431c78f0be0dc5e3e3b32f'
assert json.loads(browser.read_text(encoding='utf-8'))['status'] == 'local_browser_acceptance_passed_with_nonblocking_diagnostics'
now = datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
first_commit = subprocess.check_output(['git', '-C', str(SITE), 'show', '-s', '--format=%H|%cI', FIRST], text=True).strip().split('|')
proof = {'corrected_at_utc': now, 'doi': DOI, 'source_id': 'chen2018ami', 'first_publication_commit': first_commit[0], 'commit_at': first_commit[1], 'absent_from_parent_review_index': True, 'records_before': 675, 'records_after': 698, 'added_records': 23, 'added_routes': 17, 'current_reader_audit_status': current[0]['independent_audit'], 'browser_receipt_sha256': browser_hash, 'new_papers_published_overnight': 1, 'later_status_corrections_count': 0, 'correction_reason': 'The earlier zero used an after-publication baseline. Chen first entered the published dataset overnight and counts once; its subsequent status corrections add no papers.'}
path = SITE / 'data/review-progress.json'
data = json.loads(path.read_text(encoding='utf-8'))
data['updated_at'] = now
data['daily_throughput']['published_sources_today'] = 1
data['daily_throughput']['completed_papers_today'] = 0
data['daily_throughput']['deployed_pending_closeout'] = 1
data['daily_throughput']['capacity_note'] = 'One distinct Reader contribution was first published overnight: Chen et al. (2018), with 23 records and 17 routes. Later status corrections add zero papers. Final numerical-table/source/browser completion-state reconciliation is pending, so the fully closed counter remains0 and deployed-pending-closeout is1. The earlier zero newly published count used an incorrect after-publication baseline. The500/day completion target remains unmet; training approval is a separate task.'
data['daily_throughput']['completed_paper_ledger'] = [{k: proof[k] for k in ['doi', 'source_id', 'first_publication_commit', 'commit_at', 'added_records', 'added_routes']}]
by_name = {x['short_label']: x for x in data['current_work']}
overview = by_name['Pass-set curation']
overview['stage'] = 'One distinct paper first published overnight (Chen 2018); three other contributions have active review/correction tasks this morning.'
overview['summary'] = 'The overnight Chen contribution increased the dataset from 675 to 698 records, 123 to 140 routes and 50 to 52 material/component hubs. It counts once; later Chen status corrections and Banerjee display improvements add no papers. ACS Nano R2 is under independent reader acceptance, Wu Cu2S R2 corrections are active, and Dhaene CdSe SI page references are being independently rechecked. Exact coordinate-recipe pairs remain 0. These are saved work states, not proof of continuous overnight execution.'
for item in overview['stages']:
    if item['label'] == '500/day requirement':
        item['detail'] = 'One first-published Reader contribution; fully closed count held pending completion-state reconciliation. Later corrections and unpublished candidates are excluded.'
chen = by_name['Chen et al. (2018)']
chen['stage'] = 'First added at 03:32 Chicago time on September 24; later status corrections were audited and live-verified. Count this paper once in the overnight total.'
chen['summary'] = 'The first publication added 23 records and 17 routes for Cs4PbBr6/CsPbBr3 composites. Source extraction, reader mapping, molecular/solution bindings and browser checks passed within their stated scopes; later status corrections updated stale labels. The previous zero daily count mistakenly treated the after-publication snapshot as its starting baseline. This is one new published paper, not 23 independent experiments; training admission and exact coordinate-recipe pairs remain unapproved/zero.'
for item in chen['stages']:
    if item['label'] == 'Structured extraction':
        item['detail'] = '23 source-bound records published in the initial overnight contribution; distinct procedures/controls retain their scope.'
    elif item['label'] == 'Independent audit':
        item['detail'] = 'Source audit, changed-scope reader mapping and molecular/solution binding audits passed; local browser acceptance passed with resolved/nonblocking diagnostics.'
    elif item['label'] == 'Reader and dataset integration':
        item['detail'] = 'First publication added 23 records and 17 routes; later corrected status labels were checked live.'
    elif item['label'] == 'Publication':
        item['detail'] = 'First publication counts once for September 24 Chicago time; subsequent metadata corrections count zero additional papers.'
data['recent_milestones'].insert(0, {'at': now, 'text': 'Corrected overnight paper count to 1: git history proves Chen2018 was first added at 03:32 Chicago time, increasing records675→698 and routes123→140. Earlier zero used an after-publication baseline. Subsequent corrections are not counted again.'})
data['recent_milestones'] = [m for m in data['recent_milestones'] if m.get('text') != 'Morning reconciliation: ACS R2 author QA completed; Wu independent site audit requests corrections; Dhaene SI page-offset correction awaits recheck. Three next tasks resumed. No new published paper or exact coordinate-recipe pair.']
path.write_bytes((json.dumps(data, indent=2, ensure_ascii=False) + '\n').encode('utf-8'))
proof['fully_closed_new_papers_counted'] = 0
proof['deployed_pending_closeout'] = 1
proof['completion_status'] = 'Pending bounded reconciliation of numerical-table scope and stale source/browser flags; training admission is separate.'
proof['progress_json_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
(DEST / 'overnight-count-correction.json').write_bytes((json.dumps(proof, indent=2) + '\n').encode())
print(json.dumps(proof, indent=2))
