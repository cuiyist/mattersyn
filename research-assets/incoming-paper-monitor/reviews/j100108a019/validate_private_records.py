"""Schema/graph and disabled-export checks; not a scientific approval."""
from pathlib import Path
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, r'[local path redacted]')
from dataset_lib import validate_record, eligibility, build_groups

records, results, errors = [], [], []
for folder in ['canonical-drafts', 'procedure-drafts', 'context-drafts']:
    for path in sorted((HERE / folder).glob('*.json')):
        r = json.loads(path.read_text(encoding='utf-8'))
        if 'record_id' not in r:
            continue
        issues = validate_record(r)
        eligible = [key for key, value in eligibility(r).items() if value['eligible']]
        if eligible:
            issues.append('Private draft enabled training tasks: ' + ', '.join(eligible))
        if r['quality']['review_status'] != 'imported_unreviewed':
            issues.append('Private draft review status was prematurely promoted.')
        if r['record_id'] == 'littau-1993-aks41-context':
            if r['record_type'] != 'observation' or r['operations']:
                issues.append('AKS41 context must not pretend to reconstruct a synthesis.')
            by_property = {m['property']: m for m in r['measurements']}
            if by_property['mean_individual_particle_size']['sample_id'] == by_property['crystalline_core_diameter']['sample_id']:
                issues.append('Single depicted particle and population mean share one sample ID.')
        errors.extend(issues)
        results.append({'path': str(path.relative_to(HERE)), 'record_id': r['record_id'],
                        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'measurement_count': len(r['measurements']), 'issues': issues})
        records.append(r)
ids = [r['record_id'] for r in records]
if len(ids) != len(set(ids)):
    errors.append('Duplicate record IDs across private draft directories.')
groups = build_groups(records)
if len(set(groups.values())) != 1:
    errors.append('Single-source drafts unexpectedly form independent evaluation groups.')
report = {'status': 'passed' if not errors else 'failed',
          'scope': 'Schema, material/sample/evidence graph, single-source grouping, selected specimen separation, and disabled training gates; not a full independent scientific audit or public approval.',
          'record_count': len(records), 'measurement_count': sum(len(r['measurements']) for r in records),
          'records': results, 'errors': errors, 'published': False}
(HERE / 'private-records-validation.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'status': report['status'], 'record_count': report['record_count'],
                  'measurement_count': report['measurement_count'], 'errors': errors}, indent=2))
if errors:
    raise SystemExit(1)
