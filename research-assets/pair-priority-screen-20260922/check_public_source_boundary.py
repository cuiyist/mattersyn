"""Verify raw ranking cues stay local, including rejected historical dry runs."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'research-assets'))
import public_projection_policy as policy

GIT = r'C:\Program Files\Git\cmd\git.exe'
rows = []
for path in sorted(HERE.rglob('source-cues.jsonl')):
    rel = path.relative_to(ROOT).as_posix()
    reason = policy.exclude_path(rel)
    assert reason in ('private_source_excerpt_corpus', 'explicit_private_source_workspace'), rel
    try:
        policy.project_bytes(rel, b'{}\n')
    except policy.ProjectionError:
        pass
    else:
        raise AssertionError('Source-cue projection was not rejected')
    rows.append({'path': rel, 'exclusion': reason})
assert rows, 'Expected current ranker source-cue outputs'
for rel in (
    'research-assets/pair-priority-screen-20260922/ranker-proposal/rank_pairs.py',
    'research-assets/pair-priority-screen-20260922/ranker-proposal/final-run/summary.json',
):
    assert policy.exclude_path(rel) is None

repos = []
for checkout, name in (
    (ROOT.parent / 'mattersyn-github-project', 'mattersyn'),
    (ROOT.parent / 'mattersyn-github-public-clean/mattersyn-site', 'mattersyn-site'),
):
    base = [GIT, '-c', 'safe.directory=' + checkout.as_posix(), '-C', str(checkout)]
    remote = subprocess.check_output(base + ['remote', 'get-url', 'origin'], text=True).strip()
    assert remote == 'https://github.com/cuiyist/' + name + '.git'
    tracked = subprocess.check_output(base + ['ls-files', '-z'], text=True).split('\0')
    cue_paths = [p for p in tracked if Path(p).name == 'source-cues.jsonl']
    assert not cue_paths, 'Private source cue file is tracked in public checkout'
    repos.append({'repository': name, 'tracked_source_cue_files': len(cue_paths)})
report = {
    'at': datetime.now(timezone.utc).isoformat(),
    'policy_version': policy.POLICY_VERSION,
    'policy_sha256': hashlib.sha256((ROOT/'research-assets/public_projection_policy.py').read_bytes()).hexdigest(),
    'raw_cue_paths_checked': rows,
    'public_checkouts': repos,
    'passed': True,
    'scope': 'Specific raw-cue boundary and current tracked paths; not a new general publication or source-science audit.',
}
(HERE/'source-cue-public-boundary.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
print(json.dumps({'passed': True, 'raw_cue_paths_excluded': len(rows), 'public_checkouts': len(repos)}))
