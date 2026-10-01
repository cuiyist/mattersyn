#!/usr/bin/env python3
"""Write the exact-change review receipt that prepare_source_release.py needs.

Run after `git add` of reviewed changes, before `prepare_source_release.py --apply`:

  python tools/publication/make_review_receipt.py --root . \
    --reviewer "<who reviewed these exact changes>" --out <private-receipt.json>

One row per staged change versus HEAD: new/modified files bind their previous and staged
SHA-256, byte count and Git mode; deletions get a `delete` row with the previous SHA-256.
The two generated control files are excluded (the preparer generates them). The receipt
only records who reviewed which exact bytes; it never approves scientific content.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, subprocess, sys
from pathlib import Path

CONTROLS = {'publication/project-allowlist.json', 'publication/build-inputs.json'}


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args])


def blob(root, spec):
    r = subprocess.run(['git', '-C', str(root), 'show', spec], capture_output=True)
    return r.stdout if r.returncode == 0 else None  # None: path is new (not in HEAD)


def build_receipt(root, reviewer, at=None):
    if not reviewer or not reviewer.strip():
        raise SystemExit('--reviewer is required')
    root = Path(root).resolve()
    head = git(root, 'rev-parse', 'HEAD').decode().strip()
    at = at or dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    rows = []
    for line in git(root, 'diff', '--cached', '--name-status', '--no-renames').decode().splitlines():
        status, path = line.split('\t', 1)
        if path in CONTROLS:
            continue
        before = blob(root, f'HEAD:{path}')
        before_sha = hashlib.sha256(before).hexdigest() if before is not None else None
        common = {'path': path, 'before_sha256': before_sha, 'review_status': 'approved', 'reviewer': reviewer,
                  'reviewed_at': at, 'source_refs': []}
        if status.startswith('D'):
            rows.append({**common, 'decision': 'delete'})
            continue
        staged = blob(root, f':{path}')
        mode = git(root, 'ls-files', '-s', '--', path).decode().split()[0]
        rows.append({**common, 'decision': 'allow', 'sha256': hashlib.sha256(staged).hexdigest(), 'bytes': len(staged), 'git_mode': mode})
    if not rows:
        raise SystemExit('nothing staged: git add the reviewed changes first')
    return {'schema': 'mattersyn-reviewed-source-changes/1', 'base_commit': head, 'files': rows}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--root', type=Path, default=Path('.'))
    ap.add_argument('--reviewer', required=True)
    ap.add_argument('--out', type=Path, required=True, help='new file outside the checkout')
    a = ap.parse_args()
    out = a.out.resolve()
    if out.is_relative_to(a.root.resolve()):
        raise SystemExit('write the receipt outside the checkout')
    if out.exists():
        raise SystemExit('receipt exists; choose a new path')
    receipt = build_receipt(a.root, a.reviewer)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({'files': len(receipt['files']), 'base_commit': receipt['base_commit'], 'receipt': str(out)}))


if __name__ == '__main__':
    sys.exit(main())
