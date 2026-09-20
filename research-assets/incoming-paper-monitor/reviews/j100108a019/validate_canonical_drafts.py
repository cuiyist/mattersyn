from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, r'[local path redacted]')
from dataset_lib import validate_record, eligibility

files = sorted((ROOT / 'canonical-drafts').glob('*.json'))
assert len(files) == 3
results = []
errors = []
for path in files:
    r = json.loads(path.read_text(encoding='utf-8'))
    issues = validate_record(r)
    errors.extend(issues)
    assert not any(v['eligible'] for v in eligibility(r).values())
    assert r['quality']['review_status'] == 'imported_unreviewed'
    assert r['operations'][1]['parameters']['residence_time']['unit'] == 'ms'
    assert r['operations'][0]['parameters']['stock_gas_flow']['unit'] == 'sccm'
    assert r['operations'][-1]['parameters']['collection_pressure']['value'] is None
    assert not any(m['property'].startswith('PL') for m in r['measurements'])
    if path.stem.endswith('1p0'):
        assert r['products'][0]['phase']['value'] is None
        assert next(m for m in r['measurements'] if m['property']=='coherence_length')['value']['value'] is None
    results.append({'record':path.stem,'errors':issues,'eligible_training_tasks':[]})
report={'validation_scope':'Schema, graph, selected scientific separation invariants and training gates only; independent canonical audit and page approval pending.',
        'status':'passed' if not errors else 'failed','records':results}
(ROOT/'canonical-drafts-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
assert not errors
