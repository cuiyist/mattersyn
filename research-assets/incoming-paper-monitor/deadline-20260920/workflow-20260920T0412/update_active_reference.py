from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
HERE=Path(__file__).resolve().parent
path=HERE.parent/'active-cutoff.json'
prior=HERE/'active-cutoff-before-activation.json'
if not prior.exists():prior.write_bytes(path.read_bytes())
d=json.loads(path.read_bytes());part=json.loads((HERE/'scope-partition.json').read_bytes())
proof=HERE/'activation/activation-proof.json'
d.update(recorded_at=datetime.now(timezone.utc).isoformat(),
         status='activated_cutoff_filtered_priority_policy',
         monitor_selection_filter_activated=True,
         shared_ledger_changed=True,
         counts=part['counts'],
         current_activation={'path':str(proof),'sha256':hashlib.sha256(proof.read_bytes()).hexdigest()},
         nested_screening={'path':str(HERE/'screen-coverage-check.json'),
             'status':'three_unique_nested_PDFs_text_screened_identity_and_queue_reconciliation_pending'},
         note='Original immutable cutoff membership unchanged. Current priority ranks include cutoff scopes only; later arrivals remain unranked. No scientific completion assigned.')
path.write_text(json.dumps(d,indent=2)+'\n',encoding='utf8')
print(json.dumps({'cutoff_filter_active':True,'included_scopes':d['counts']['included_known_canonical_groups']}))
