from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
B=Path(__file__).resolve().parent;M=B.parents[3]
p=M/'skills/mattersyn-paper-to-site/references/incoming-corpus.md';t=p.read_text(encoding='utf8');heading='## Timing estimates and structure-conditioning counts'
lesson='''

## Timing estimates and structure-conditioning counts

- For whole-folder estimates, distinguish incoming-only from the combined legacy/incoming worklist, document copies from provisional review groups, and a frozen backlog from continued arrivals. Use dated measured publication intervals as a limited elapsed-cadence sample, not claimed active processing time. State runtime availability and source relevance/duplicate uncertainty; never imply a finite catch-up date when the arrival rate exceeds verified review capacity.
- A zero measured-coordinate–recipe count does not mean zero structure information. Keep product phase, morphology, dimensions and architecture availability separate from sample-coordinate eligibility. Imported numeric benchmark rows are a separate collection, not the atlas material scope or individually reviewed papers.
- Historical product outcomes may become inverse-design conditioning fields only with explicit observed-outcome provenance and verified sample/recipe linkage. Do not rewrite them as prospective author intentions. Reference-prototype conditioning is distinct from measured sample atomic coordinates, and task-specific recipe completeness should be tracked independently of every optional unknown. Candidate field counts are not already audited training pairs.
- Validate reader facts against alternative condition-option quantities as well as primary operation parameters. Ensure literature collection metadata is present during promotion, and preserve existing verified checksum aliases when integrating source figures. Version changed shared viewer imports so cached code cannot hide a validated renderer update.
'''
assert heading not in t;p.write_text(t+lesson,encoding='utf8')
mem=M/'MEMORY.md';t=mem.read_text(encoding='utf8');extra='\nPost-publication queue snapshot at 19:28 UTC: 23 further document groups arrived during this review; 13,453 copies across both folders, 9,153 waiting scopes, 18 source scopes closed, no active claim. The dated ETA remains a frozen-snapshot scenario. Version 28 also publishes the clarified dataset metric labels and definitions.\n\n';i=t.index('\n\n');t=t[:i]+extra+t[i+2:];mem.write_text(t,encoding='utf8')
q=B/'memory-skill-checkpoint.json';d=json.loads(q.read_text(encoding='utf8'));d.update(project_skill_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),training_and_eta_memory='training-plan-and-eta.json',latest_waiting_scopes=9153);q.write_text(json.dumps(d,indent=2)+'\n',encoding='utf8')
print('Saved final queue state and reusable ETA/training-count lessons.')
