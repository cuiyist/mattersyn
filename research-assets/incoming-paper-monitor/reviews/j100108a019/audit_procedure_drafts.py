"""Record root's bounded manual source audit and verify corrected draft invariants."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
files = sorted((HERE / 'procedure-drafts').glob('*.json'))
assert len(files) == 9
records = {p.stem: json.loads(p.read_text(encoding='utf-8')) for p in files}
prefix = 'littau-1993-si-'
get = lambda suffix: records[prefix + suffix]
assert all(r['quality']['experimental_outcome'] == 'not_established' for r in records.values())
assert all(r['quality']['requested_tasks'] == [] for r in records.values())
assert all(p['recipe_link'] == 'general_context' for r in records.values() for p in r['products'])
assert not get('optical-characterization')['condition_options'], 'Source conflict cannot become selectable experimental alternatives.'
optical_text = json.dumps(get('optical-characterization'), ensure_ascii=False)
assert '350' in optical_text and '355' in optical_text
power = next(o for o in get('xrd-characterization')['operations'] if o['id'] == 'acquire-xrd')['parameters']
assert 'anode_power' not in power
ratings = [q for key, q in power.items() if q['value'] == 12 and q['unit'] == 'kW']
assert len(ratings) == 1 and 'not' in ratings[0]['basis'].lower(), 'Keep equipment specification distinct from operating setting.'
powder = get('powder-preparation')
assert powder['operations'][0]['parameters']['temperature']['value'] is None
assert any('1230' in e['locator'] and '41' in e['locator'] for p in powder['products'] for e in p['composition']['evidence'])
acid = get('acid-activation')
peaks = [m for m in acid['measurements'] if m['property'] == 'PL_emission_peak']
assert {m['value']['value'] for m in peaks} == {970, 770, 660}
assert all(m['sample_id'].startswith('activated-') for m in peaks)
qys = [m for m in acid['measurements'] if m['property'] == 'PL_quantum_yield']
assert len(qys) == 1 and qys[0]['value']['approximate'] and 'slightly_above' in qys[0]['value']['qualifier']
assert acid['stocks'][0]['concentrations']['pH']['value'] == 1
assert 'Added acidic water' in acid['stocks'][0]['concentrations']['pH']['basis']
decay = get('time-resolved-pl')['measurements']
assert {m['value']['value'] for m in decay} == {17, 76}
assert all(m['value']['status'] == 'author_derived' and 'multiexponential' in m['value']['qualifier'] for m in decay)
findings = [
    {'id': 'outcome-semantics', 'issue': 'Incomplete procedure reporting must not be labelled a partially successful experiment.'},
    {'id': 'xray-source-rating', 'issue': 'A 12 kW rotating-anode source description does not establish the operating power used.'},
    {'id': 'excitation-conflict', 'issue': 'Conflicting 350/355 nm source statements are not selectable experimental alternatives.'},
    {'id': 'powder-footnote-evidence', 'issue': 'The unwashed-powder caveat in reference note 41 requires its own page locator.'}]
for finding in findings:
    finding['status'] = 'resolved_in_builder_and_regenerated_records'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
report = {
    'status': 'passed_bounded_independent_source_join_audit',
    'reviewer': 'root; independent of the procedure-draft author',
    'scope': 'All nine private supporting-procedure records, operations and 21 measurement/reference/cohort entries. Manual comparison to source main-text experimental/results sections and existing audited staging; visually rechecked supplied pages 2, 4, 5 and 6. This is not a new full-main/SI review, full item-coverage approval, reader audit or publication.',
    'source_doi': '10.1021/j100108a019',
    'source_extraction_sha256': sha(HERE / 'source-extraction.json'),
    'builder_sha256': sha(HERE / 'stage_procedures.py'),
    'record_count': len(records),
    'measurement_count': sum(len(r['measurements']) for r in records.values()),
    'records': [{'record_id': p.stem, 'sha256': sha(p)} for p in files],
    'findings': findings,
    'outstanding_in_scope_must_fix': [],
    'remaining': ['Full contribution item coverage, including qualitative/model/context evidence',
                  'Original figure and sample-to-reader joins', 'Registry/models/apparatus implementation and reader testing',
                  'Source identity/import/inventory reconciliation and publication', 'SI remains unverified'],
    'training_eligible': False,
    'website_published': False}
assert report['measurement_count'] == 21
(HERE / 'procedure-drafts-independent-audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
(HERE / 'procedure-drafts-independent-audit.md').write_text(
    '# Supporting-procedure independent audit\n\n'
    'Passed for the bounded nine-procedure / 21-entry scope after four corrections. '
    'Root reviewed the draft authoring code and source/sample joins against the supplied main text and audited staging, '
    'with targeted page-image checks. This is not full-paper canonical or reader approval.\n\n'
    + '\n'.join('- '+f['issue']+' **Resolved.**' for f in findings)
    + '\n\nActivated versus as-made optical states, one shared approximate QY estimate, separate drying/concentration settings, '
      'HPLC fractions, alternative TEM/XRD preparations, source-derived dimensions, and multiexponential decay components remain distinct. '
      'SI, exact batch joins and missing procedure details remain explicit. Records stay private with training tasks disabled.\n\n'
      'See the JSON audit for checked hashes and remaining integration work.\n', encoding='utf-8')
print(json.dumps({'status': report['status'], 'records': len(records), 'measurement_entries': report['measurement_count'],
                  'resolved_findings': len(findings)}, indent=2))
