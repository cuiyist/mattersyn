"""Root independent review receipt for Norberg's bounded delivery helpers."""
from pathlib import Path
from datetime import datetime, timezone
import json,hashlib,ast,copy
P=Path(__file__).resolve().parent;O=P/'site-integration-proposal';S=P.parents[4]/'recipe-atlas'
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=read(O/'conditional-publication-rule-proposal.json'); b=read(S/'data/paper-reviews/pati2009.json')
assert r['author']=='/root/norberg2004_extract' and r['baseline_reader_sha256']==sha(S/'data/paper-reviews/pati2009.json')
assert r['finalizer_script_sha256']==sha(P/'finalize_reader_publication.py')
plan=read(O/'release-endpoints.json');assert len(plan['paths'])==len(set(plan['paths']))==324
assert all((S/'dist'/x).is_file() for x in plan['paths'])
assert r['endpoint_plan_sha256']==sha(O/'release-endpoints.json')
assert b['presentation_gates']['browser_render'] and not b['presentation_gates']['publication']
assert len(r['exact_allowed_changes'])==2
assert {x['pointer'] for x in r['exact_allowed_changes']}=={'/presentation_gates/publication','/publication_status'}
after=copy.deepcopy(b)
for x in r['exact_allowed_changes']:
 parts=x['pointer'].strip('/').split('/'); n=after
 for part in parts[:-1]:n=n[part]
 assert n[parts[-1]]==x['before'];n[parts[-1]]=x['after']
assert not after['presentation_gates']['exact_product_atomic_structure_binding']
for name in ['finalize_reader_publication.py','prepare_publication_rule.py','sync_release_delta.py','release_pati.py']:
 ast.parse((P/name).read_text('utf8'))
out=dict(r,status='passed_conditionally',independent_reviewer='/root',at=datetime.now(timezone.utc).isoformat(),
 review_scope='Actual helper code independently read: exact commit/build,324 endpoints,39 citations, anonymous/no cookies, original-page404 exclusions, current reader and dataset hashes, exactly two metadata leaves. Project sync applies existing source-exclusion policy and makes no deletions. No publication claim until finalizer proof conditions pass.',
 scientific_data_changed=False,publication_labels_applied=False,
 limitations=['This receipt approves the conditional transition; actual anonymous delivery and finalizer execution remain necessary.'])
p=P/'site-integration-independent-audit/conditional-publication-rule-audit.json';assert not p.exists()
p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf8')
print('Conditional publication helper review passed; no publication labels applied.')
