#!/usr/bin/env python3
"""One-command batch release: source main -> gated site build -> site commit -> live check.

Runs the existing release steps in order, unchanged:
  1. check: clean source and site checkouts; source HEAD passed source CI on GitHub
  2. snapshot  (recipe-atlas/scripts/make_runtime_snapshot.py)
  3. candidate (recipe-atlas/scripts/build_release.py --candidate)
  4. site allowlist from the candidate (tools/publication/prepare_allowlist.py; the guard
     refuses any file the policy does not allow)
  5. final gated build with that allowlist (build_release.py --gate ...), which must
     reproduce the candidate byte for byte
  6. stage the final dist into the site checkout and refresh .release-control
  7. site boundary gate, exactly as the site's Pages workflow runs it
  8. --push: commit and push the site (its Pages workflow deploys)
  9. --verify: anonymous live check against the final manifest; optional ledger events

Without --push nothing leaves this machine (dry run). Paper text is never read.
Standard library only; works on Windows, macOS and Linux.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, os, random, shutil, subprocess, sys, time, urllib.error, urllib.request
from pathlib import Path

SITE_CONTROL = {'.git', '.github', '.release-control', 'tools', '.gitattributes'}  # never replaced by the build
CI_WORKFLOW = 'MatterSyn source and build checks'


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def run(cmd, cwd=None):
    r = subprocess.run([str(c) for c in cmd], cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        raise SystemExit(f'FAILED: {" ".join(map(str, cmd))}\n{r.stdout[-3000:]}\n{r.stderr[-3000:]}')
    return r.stdout


def git(repo, *args):
    return run(['git', '-C', repo, *args]).strip()


def tree_files(root, skip_top=()):
    """Relative POSIX path -> absolute path for every file, skipping top-level names in skip_top."""
    root = Path(root); out = {}
    for path in root.rglob('*'):
        rel = path.relative_to(root)
        if rel.parts[0] in skip_top or not path.is_file():
            continue
        out[rel.as_posix()] = path
    return out


def stage_dist(dist, site):
    """Make the site worktree equal to dist outside the control paths. Returns (added, changed, removed)."""
    dist_files = tree_files(dist); site_files = tree_files(site, SITE_CONTROL)
    added, changed, removed = [], [], []
    for rel, path in site_files.items():
        if rel not in dist_files:
            path.unlink(); removed.append(rel)
    for rel, src in dist_files.items():
        if rel.split('/')[0] in SITE_CONTROL:
            raise SystemExit(f'build output must not contain site control path: {rel}')
        dst = Path(site) / rel
        if dst.exists():
            if sha256(dst) == sha256(src):
                continue
            changed.append(rel)
        else:
            added.append(rel)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    for d in sorted({p for p in Path(site).rglob('*') if p.is_dir()}, key=lambda p: -len(p.parts)):
        if d.relative_to(site).parts[0] not in SITE_CONTROL and not any(d.iterdir()):
            d.rmdir()
    return sorted(added), sorted(changed), sorted(removed)


def papers_in(dist):
    """primary source group -> sorted record ids, from the built records."""
    out = {}
    for f in sorted((Path(dist) / 'data' / 'records').glob('*.json')):
        rec = json.loads(f.read_text(encoding='utf-8'))
        src = (rec.get('lineage') or {}).get('source_group') or next((s.get('id') for s in rec.get('sources', []) if s.get('id')), None)
        if src:
            out.setdefault(src, []).append(rec['record_id'])
    return {k: sorted(v) for k, v in out.items()}


def new_papers(old_dist, new_dist):
    old = papers_in(old_dist) if (Path(old_dist) / 'data' / 'records').is_dir() else {}
    new = papers_in(new_dist)
    return {k: v for k, v in new.items() if k not in old}


def http_get(url, headers=None, opener=None):
    """Anonymous HTTPS GET (no cookies or credentials). Falls back to the system curl when this
    Python has no CA bundle (common with python.org installers on macOS)."""
    req = urllib.request.Request(url, headers={'User-Agent': 'mattersyn-release-check', **(headers or {})})
    try:
        with (opener or urllib.request.urlopen)(req, timeout=60) as r:
            return r.read()
    except urllib.error.URLError as exc:
        if opener is not None or 'CERTIFICATE_VERIFY_FAILED' not in str(exc) or not shutil.which('curl'):
            raise
        cmd = ['curl', '-fsSL', '--max-time', '60'] + [x for k, v in (headers or {}).items() for x in ('-H', f'{k}: {v}')] + [url]
        return subprocess.run(cmd, capture_output=True, check=True).stdout


def source_ci_passed(repo_slug, commit, opener=None):
    url = f'https://api.github.com/repos/{repo_slug}/actions/runs?head_sha={commit}&per_page=50'
    runs = json.loads(http_get(url, {'Accept': 'application/vnd.github+json'}, opener)).get('workflow_runs', [])
    mine = [x for x in runs if x.get('name') == CI_WORKFLOW]
    return any(x.get('conclusion') == 'success' for x in mine), [(x.get('status'), x.get('conclusion')) for x in mine]


def fetch(url, opener=None):
    return http_get(url, {'Cache-Control': 'no-cache'}, opener)  # anonymous: no cookies, no credentials


def verify_live(site_url, dist, source_commit, sample=40, timeout_s=1800, poll_s=20, opener=None, sleep=time.sleep):
    base = site_url.rstrip('/') + '/'
    deadline = time.monotonic() + timeout_s
    while True:
        try:
            snap = json.loads(fetch(f'{base}data/release-snapshot.json?v={int(time.time())}', opener))
            if snap.get('source_commit') == source_commit:
                break
        except Exception:
            pass
        if time.monotonic() > deadline:
            return {'passed': False, 'reason': 'live release-snapshot never showed the source commit', 'anonymous': True}
        sleep(poll_s)
    files = tree_files(dist)
    must = [p for p in ('index.html', 'data/dataset-manifest.json', 'data/release-snapshot.json') if p in files]
    rest = sorted(set(files) - set(must)); random.Random(source_commit).shuffle(rest)
    checked, mismatched = [], []
    for rel in must + rest[:max(0, sample - len(must))]:
        live = hashlib.sha256(fetch(f'{base}{rel}?v={int(time.time())}', opener)).hexdigest()
        (checked if live == sha256(files[rel]) else mismatched).append(rel)
    return {'passed': not mismatched and bool(checked), 'anonymous': True, 'checked_files': len(checked),
            'mismatched_files': mismatched, 'source_commit': source_commit, 'verified_at': now(), 'site_url': base}


def ledger_events(papers, source_commit, site_url, receipt_sha256, at):
    return [{'event_id': f'live:{src}:{source_commit[:12]}', 'at': at, 'stage': 'live_verified', 'package_id': src,
             'primary_source_id': src, 'source_identity_verified': True, 'tier': 'gold', 'record_ids': ids,
             'commit': source_commit, 'url': site_url,
             'verification': {'anonymous': True, 'passed': True, 'receipt_sha256': receipt_sha256}}
            for src, ids in sorted(papers.items())]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--source', required=True, type=Path, help='clean source checkout at the commit to release')
    ap.add_argument('--site', required=True, type=Path, help='clean mattersyn-site checkout on main')
    ap.add_argument('--work', required=True, type=Path, help='new working directory outside both checkouts')
    ap.add_argument('--release-id', required=True)
    ap.add_argument('--reviewer', required=True, help='who approved the papers in this batch (quick audit)')
    ap.add_argument('--push', action='store_true', help='commit and push the site (otherwise dry run)')
    ap.add_argument('--verify', action='store_true', help='after --push, wait for the live site and check it anonymously')
    ap.add_argument('--ledger', type=Path, help='private metrics ledger (JSONL) to append live_verified events to')
    ap.add_argument('--sync-gate-tools', action='store_true', help='also copy tools/mattersyn-release into the site')
    ap.add_argument('--source-repo', default='cuiyist/mattersyn')
    ap.add_argument('--site-url', default='https://cuiyist.github.io/mattersyn-site/')
    ap.add_argument('--skip-ci-check', action='store_true', help='dry runs only: do not require source CI success')
    a = ap.parse_args()
    py = sys.executable
    src, site, work = a.source.resolve(), a.site.resolve(), a.work.resolve()
    times = {}; t0 = time.monotonic()
    def mark(stage): times[stage] = round(time.monotonic() - t0, 1)

    for repo in (src, site):
        if work == repo or work.is_relative_to(repo):
            raise SystemExit('--work must be outside both checkouts')
        if git(repo, 'status', '--porcelain', '--untracked-files=all'):
            raise SystemExit(f'checkout is not clean: {repo}')
    if work.exists() and any(work.iterdir()):
        raise SystemExit('--work must be new or empty')
    if a.verify and not a.push:
        raise SystemExit('--verify needs --push')
    if a.push and a.skip_ci_check:
        raise SystemExit('--skip-ci-check is only for dry runs')
    work.mkdir(parents=True, exist_ok=True)
    commit = git(src, 'rev-parse', 'HEAD')
    if not a.skip_ci_check:
        ok, seen = source_ci_passed(a.source_repo, commit)
        if not ok:
            raise SystemExit(f'source CI has not passed for {commit} (runs: {seen}); push it and wait for CI')
    mark('checks')

    snap = work / 'snapshot.json'
    run([py, src / 'recipe-atlas/scripts/make_runtime_snapshot.py', '--root', src, '--blueprint', src / 'publication/build-inputs.json', '--output', snap], cwd=src)
    common = ['--snapshot', snap, '--registry', src / 'publication/asset-rights-registry.json',
              '--artifact-transform', src / 'tools/publication/source_link_artifacts.py']
    run([py, src / 'recipe-atlas/scripts/build_release.py', '--candidate', '--output', work / 'candidate', *common], cwd=src)
    cand = work / 'candidate/project/recipe-atlas/dist'
    mark('candidate_build')

    allow = work / 'site-allowlist.json'
    run([py, src / 'tools/publication/prepare_allowlist.py', '--root', cand, '--guard', src / 'tools/mattersyn-release/public_release_guard.py',
         '--policy', src / 'publication/public-release-policy.json', '--registry', src / 'publication/asset-rights-registry.json',
         '--repo', 'mattersyn-site', '--source-commit', commit, '--release-id', a.release_id, '--reviewer', a.reviewer, '--out', allow], cwd=src)
    run([py, src / 'recipe-atlas/scripts/build_release.py', '--output', work / 'final', *common,
         '--gate', src / 'tools/mattersyn-release/gate.py', '--allowlist', allow, '--policy', src / 'publication/public-release-policy.json'], cwd=src)
    final = work / 'final/project/recipe-atlas/dist'
    cand_h = {k: sha256(v) for k, v in tree_files(cand).items()}; final_h = {k: sha256(v) for k, v in tree_files(final).items()}
    if cand_h != final_h:
        raise SystemExit('final build differs from the reviewed candidate; stop and investigate')
    mark('final_build')

    added_papers = new_papers(site, final)
    added, changed, removed = stage_dist(final, site)
    rc = site / '.release-control'
    shutil.copyfile(allow, rc / 'site-allowlist.json')
    shutil.copyfile(src / 'publication/asset-rights-registry.json', rc / 'asset-rights-registry.json')
    shutil.copyfile(src / 'publication/public-release-policy.json', rc / 'site-policy.json')
    if a.sync_gate_tools:
        shutil.rmtree(site / 'tools/mattersyn-release'); shutil.copytree(src / 'tools/mattersyn-release', site / 'tools/mattersyn-release',
                                                                         ignore=shutil.ignore_patterns('__pycache__'))
    run([py, site / 'tools/mattersyn-release/export_release.py', '--source-root', site, '--destination', work / 'site-stage',
         '--allowlist', rc / 'site-allowlist.json', '--registry', rc / 'asset-rights-registry.json', '--policy', rc / 'site-policy.json',
         '--repo', 'mattersyn-site', '--manifest-out', work / 'site-manifest.json', '--report-out', work / 'site-boundary.json'], cwd=site)
    mark('stage_and_site_gate')

    summary = {'release_id': a.release_id, 'source_commit': commit, 'new_papers': sorted(added_papers),
               'new_records': sum(len(v) for v in added_papers.values()), 'files_added': len(added),
               'files_changed': len(changed), 'files_removed': len(removed), 'pushed': False, 'stage_seconds': times}
    if not (added or changed or removed):
        summary['note'] = 'website content unchanged; nothing to publish'
        git(site, 'checkout', '--', '.release-control'); git(site, 'clean', '-fdq', '--', '.release-control')
        print(json.dumps(summary, indent=1)); (work / 'release-summary.json').write_text(json.dumps(summary, indent=1)); return 0

    if a.push:
        git(site, 'add', '-A')
        body = '\n'.join(f'- {p} ({len(added_papers[p])} records)' for p in sorted(added_papers)) or '- no new source papers'
        run(['git', '-C', site, 'commit', '-q', '-m', f'Publish {len(added_papers)} papers ({a.release_id})', '-m',
             f'Built from cuiyist/mattersyn {commit}.\n\n{body}'])
        run(['git', '-C', site, 'push', '-q', 'origin', 'HEAD:main'])
        summary.update(pushed=True, site_commit=git(site, 'rev-parse', 'HEAD')); mark('push')
        if a.verify:
            result = verify_live(a.site_url, final, commit)
            receipt = work / 'live-verification.json'; receipt.write_text(json.dumps(result, indent=1) + '\n')
            summary['live_verification'] = {k: result.get(k) for k in ('passed', 'checked_files', 'mismatched_files', 'reason')}
            mark('live_verification')
            if result['passed'] and a.ledger:
                with a.ledger.open('a', encoding='utf-8') as f:
                    for e in ledger_events(added_papers, commit, a.site_url, sha256(receipt), result['verified_at']):
                        f.write(json.dumps(e) + '\n')
                summary['ledger_events'] = len(added_papers)
    summary['stage_seconds'] = times
    (work / 'release-summary.json').write_text(json.dumps(summary, indent=1) + '\n')
    print(json.dumps(summary, indent=1))
    return 0 if not a.verify or summary.get('live_verification', {}).get('passed') else 1


if __name__ == '__main__':
    sys.exit(main())
