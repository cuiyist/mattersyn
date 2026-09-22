"""Bind this private proposal and read-only inputs; never writes Site."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json

P = Path(__file__).resolve().parent
S = P.parents[2] / 'recipe-atlas'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

qa = json.loads((P / 'qa-report.json').read_text('utf8'))
assert qa['status'] == 'passed'
for path, expected in {**qa['source_record_hashes'], **qa['training_export_hashes']}.items():
    assert sha(Path(path)) == expected, path
base_matches = {}
for rel in ['scripts/dataset_lib.py', 'scripts/catalog_view.py', 'tests/test_dataset.py', 'scripts/schema_definition.py']:
    base_matches[rel] = sha(P / 'base' / rel) == sha(S / rel)
assert all(base_matches.values()), 'A replacement baseline changed; reconcile before freezing.'
private_files = {str(path): sha(path) for path in sorted(P.rglob('*'))
                 if path.is_file() and path.name != 'proposal-manifest.json'}
external_files = {str(P.parent / 'PLAN.md'): sha(P.parent / 'PLAN.md')}
for rel in ['scripts/dataset_lib.py', 'scripts/catalog_view.py', 'scripts/schema_definition.py',
            'tests/test_dataset.py', 'tests/test_host_targets.py', 'tests/test_qualitative_measurements.py',
            'dist/assets/chemical-registry/models/evans2010-species9-reference-3d.json']:
    external_files[str(S / rel)] = sha(S / rel)
manifest = {
    'schema_version': '1.0', 'author': '/root/backlog_eta',
    'status': 'author_proposal_tested_pending_distinct_review_and_integration',
    'frozen_at_utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'Task-specific exact-structure completeness policy and separate coordinate/link/readiness metrics. No Site, canonical or existing export writes.',
    'current_counts': qa['current_counts'], 'representation_counts': qa['current_representation_counts'],
    'tests': {'unit_tests': qa['unit_tests'], 'corpus_regression_checks': qa['regression_checks'],
              'status': qa['status'], 'report_sha256': sha(P / 'qa-report.json')},
    'baseline_matches_at_freeze': base_matches,
    'canonical_record_count': len(qa['source_record_hashes']),
    'unchanged_export_count': len(qa['training_export_hashes']),
    'real_task_profiles_admitted': 0,
    'replacement_files': ['scripts/dataset_lib.py', 'scripts/catalog_view.py', 'tests/test_dataset.py'],
    'new_files': ['scripts/structure_recipe_metrics.py', 'data/structure-task-policy.json', 'tests/test_structure_recipe_metrics.py'],
    'root_integration_instructions': 'INTEGRATION.md',
    'no_build_dataset_replacement': True,
    'limits': ['Author checks are not independent scientific approval.',
               'Counts are scoped to canonical measured-sample coordinate assets, not all literature structures.',
               'Local availability and hash consistency do not newly validate source geometry.',
               'Task-profile audit references are trusted curator metadata; scientific adequacy is a separate review gate.',
               'Integrated build and browser checks remain root work.'],
    'bound_files': {**private_files, **external_files},
}
(P / 'proposal-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', 'utf8')
print(json.dumps({'manifest': str(P / 'proposal-manifest.json'), 'sha256': sha(P / 'proposal-manifest.json'),
                  'bound_files': len(manifest['bound_files']), 'tests': manifest['tests']}, ensure_ascii=False))
