"""Read-only independent validation of staged Friedfeld records."""
import datetime
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
M = Path('[local path redacted]')
O = Path(__file__).parent
V = O.parent / 'site-integration-proposal/v1'
sys.path.insert(0, str(M / 'research-assets'))
from sync_github_public import io_path
sys.path.insert(0, str(M / 'recipe-atlas/scripts'))
import dataset_lib

def sha(p):
    return hashlib.sha256(io_path(p).read_bytes()).hexdigest()

rows = []
bound = {}
for p in sorted((V / 'records').glob('*.json')):
    r = json.loads(io_path(p).read_text(encoding='utf-8-sig'))
    errors = dataset_lib.validate_record(r)
    tasks = dataset_lib.eligibility(r)
    rows.append({'record_id': r['record_id'], 'validation_errors': errors,
                 'requested_tasks': r['quality']['requested_tasks'],
                 'eligibility': tasks,
                 'passed': not errors and r['quality']['requested_tasks'] == []
                    and all(not t['eligible'] for t in tasks.values())})
    bound[str(p)] = sha(p)
for name in ['dataset_lib.py', 'schema_definition.py']:
    p = M / 'recipe-atlas/scripts' / name
    bound[str(p)] = sha(p)
bound[str(Path(__file__))] = sha(Path(__file__))
out = {'author': '/root', 'auditor': '/root/backlog_eta',
       'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
       'runtime': sys.executable, 'proposal_freeze_sha256': sha(V/'package-freeze.json'),
       'record_count': len(rows), 'passed': len(rows) == 30 and all(x['passed'] for x in rows),
       'records': rows, 'bound_files': bound,
       'scope': 'Actual current schema/semantic and explicitly requested training-task gate; no Site mutation.'}
io_path(O/'current-schema-checks.json').write_text(json.dumps(out, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'passed': out['passed'], 'record_count': len(rows),
                  'failures': [x for x in rows if not x['passed']]}, indent=2))
