"""Project the accepted screen's work, excluding raw sources and unfinished work."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT/'research-assets'))
import public_projection_policy as policy
GIT = r'C:\Program Files\Git\cmd\git.exe'
PREFIX = 'research-assets/pair-priority-screen-20260922/'
local = [
    'SCREENING_POLICY.md', 'activate_pair_priority.py', 'save_screening_milestone.py',
    'inspect_manual_screen_holds.py', 'manual-text-screen-holds.json',
    'screening-result-public.json', 'automation-screened-checkpoint-receipt.json',
    'check_public_source_boundary.py', 'source-cue-public-boundary.json',
    'sync_screening_milestone.py', 'verify_public_progress.py', 'record_screen_delivery.py',
    'publication-before-accepted-screen.json', 'live-progress-delivery-79cd5205ea15.json',
    'live-progress-delivery.json',
    'activation-20260922/activation-proof.json',
    'activation-20260922/pair-nomination-policy-report.json',
    'activation-20260922/priority-policy.json',
    'ranker-proposal/rank_pairs.py', 'ranker-proposal/test_rank_pairs.py',
    'ranker-proposal/README.md', 'ranker-proposal/generation-context.json',
    'ranker-proposal/author-freeze.json', 'ranker-proposal/freeze_proposal.py',
    'ranker-proposal/author-regression-checks.json',
    'ranker-proposal/final-run-v2/summary.json',
    'ranker-proposal/final-run-v2/progress.json',
    'ranker-proposal/final-run-v2/ranked-scopes.jsonl',
    'ranker-proposal/final-run-v2/cache-binding-manifest.jsonl',
    'ranker-proposal/final-run-v2/file-dispositions.jsonl',
    'ranker-proposal/final-run-v2/nested-held.json',
    'ranker-audit/independent-audit.json', 'ranker-audit/independent-audit.md',
    'ranker-audit/audit-freeze-v1.json', 'ranker-audit/audit_frozen_run.py',
    'ranker-audit/finalize_independent_audit.py',
    'ranker-audit/run-integrity-481580484429.json',
    'ranker-audit/independent-probe-cases.json',
    'ranker-audit/run_independent_probes.py', 'ranker-audit/run_supplemental_probes.py',
    'ranker-audit/probe-results-481580484429.json',
    'ranker-audit/supplemental-probes-481580484429.json',
    'ranker-audit/generation-dispatch-holds.json', 'ranker-audit/current-scope-recheck.json',
    'ranker-audit/activation-adapter-audit.json',
    'ranker-audit/probe_activation_adapter.py', 'ranker-audit/recheck_activation_adapter.py',
    'rubric-audit/README.md', 'rubric-audit/pair-quality-rubric.json',
    'rubric-audit/pair-candidate.schema.json', 'rubric-audit/verified-benchmark-rows.json',
    'rubric-audit/counterexamples.json', 'rubric-audit/validation.json',
    'rubric-audit/schema-test-result.json', 'rubric-audit/package-manifest.json',
    'rubric-audit/test_schema.py', 'rubric-audit/build_rubric_proposal.py',
    'rubric-audit/ranker-benchmark-check/independent-benchmark-audit.json',
    'rubric-audit/ranker-benchmark-check/independent-benchmark-audit.md',
    'rubric-audit/ranker-benchmark-check/initial-benchmark-findings.json',
    'rubric-audit/ranker-benchmark-check/finalize_benchmark_audit.py',
]
files = [
    'MEMORY.md', 'skills/mattersyn-paper-to-site/references/incoming-corpus.md',
    'research-assets/public_projection_policy.py',
    'research-assets/incoming-paper-monitor/monitor.py',
    'research-assets/incoming-paper-monitor/build_public_progress.py',
    'research-assets/incoming-paper-monitor/review-control.json',
    'research-assets/incoming-paper-monitor/ledger.json',
    'research-assets/incoming-paper-monitor/queue-status.json',
    'research-assets/incoming-paper-monitor/queue-status.md',
    'research-assets/incoming-paper-monitor/queue-status.html',
    'research-assets/incoming-paper-monitor/public-progress-editorial.json',
    'research-assets/incoming-paper-monitor/latest-publication.json',
    'recipe-atlas/dist/index.html', 'recipe-atlas/dist/data/review-progress.json',
] + [PREFIX + rel for rel in local]
assert len(files) == len(set(files))
for rel in files:
    assert (ROOT/rel).is_file(), 'Missing explicit projection input: '+rel
    assert policy.exclude_path(rel) is None, 'Excluded projection input: '+rel
for path in HERE.rglob('source-cues.jsonl'):
    assert policy.exclude_path(path.relative_to(ROOT).as_posix()), 'Raw source cues must stay private'
receipt = []
for kind, dest, name in (
    ('project', ROOT.parent/'mattersyn-github-project', 'mattersyn'),
    ('site', ROOT.parent/'mattersyn-github-public-clean/mattersyn-site', 'mattersyn-site'),
):
    origin = subprocess.check_output([GIT, '-c', 'safe.directory='+dest.as_posix(), '-C', str(dest), 'remote', 'get-url', 'origin'], text=True).strip()
    assert origin == 'https://github.com/cuiyist/'+name+'.git'
    selected = files if kind == 'project' else ['recipe-atlas/dist/index.html', 'recipe-atlas/dist/data/review-progress.json']
    for rel in selected:
        raw, stats = policy.project_bytes(rel, (ROOT/rel).read_bytes())
        target = dest/(rel if kind == 'project' else rel.removeprefix('recipe-atlas/dist/'))
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or target.read_bytes() != raw:
            target.write_bytes(raw)
        receipt.append({'kind': kind, 'path': rel, 'sha256': hashlib.sha256(raw).hexdigest(), 'projection': stats})
report = {'at': datetime.now(timezone.utc).isoformat(), 'policy_version': policy.POLICY_VERSION,
          'project_files': len(files), 'site_files': 2, 'files': receipt,
          'raw_sources_or_excerpts_published': False, 'unfrozen_recovery_or_shortlist_work_copied': False}
(HERE/'screening-public-projection-receipt.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k != 'files'}))
