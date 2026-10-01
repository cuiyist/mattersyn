#!/usr/bin/env python3
"""Prepare a reviewed batch, then publish its exact candidate and check it live.

Runs the existing build, allowlist and boundary gates in this order:
  1. check: clean source and site checkouts; source HEAD passed source CI on GitHub
  2. snapshot  (recipe-atlas/scripts/make_runtime_snapshot.py)
  3. candidate (recipe-atlas/scripts/build_release.py --candidate)
  4. site allowlist from the candidate (tools/publication/prepare_allowlist.py; the guard
     refuses any file the policy does not allow)
  5. final gated build with that allowlist (build_release.py --gate ...), which must
     reproduce the candidate byte for byte
  6. stage the final dist into an isolated site worktree and refresh .release-control
  7. site boundary gate, exactly as the site's Pages workflow runs it
  8. review that exact local candidate in a browser; provide a pinned review receipt
  9. --push: commit and push those exact bytes (its Pages workflow deploys)
 10. --verify: anonymous live check of new paper and affected material routes; optional ledger events

The first invocation is always a dry run and leaves the live site checkout clean.
Reuse its --work path with --review-receipt and --push --verify after browser review.
Reuse the same path with --verify alone to retry a timed-out live check.
Paper text is never read.
Standard library only; works on Windows, macOS and Linux.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, random, shutil, subprocess, sys, time, urllib.error, urllib.parse, urllib.request
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


def tree_digest(root, skip_top=()):
    """Stable digest of file names and bytes; directories and file times do not matter."""
    rows = {name: sha256(path) for name, path in tree_files(root, skip_top).items()}
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


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


def relative_route(route, dist):
    parsed = urllib.parse.urlsplit(route)
    path = parsed.path
    if (parsed.scheme or parsed.netloc or parsed.fragment or not path or path.startswith('/') or '\\' in path or
            any(part in ('', '.', '..') for part in path.split('/')) or
            not (Path(dist) / path).is_file()):
        raise SystemExit(f'paper route is not a local built page: {route}')
    return path


def new_paper_routes(dist, papers):
    """Bind each new primary source to its built paper page and backing public data."""
    if not papers:
        return {}
    index = json.loads((Path(dist) / 'data/paper-review-index.json').read_text(encoding='utf-8'))
    rows = index.get('papers', [])
    out = {}
    for source, ids in sorted(papers.items()):
        matches = [row for row in rows if row.get('id') == source or
                   set(ids).issubset(set(row.get('record_ids', [])))]
        if len(matches) != 1:
            raise SystemExit(f'expected one paper review route for new source {source}; found {len(matches)}')
        row = matches[0]
        if not set(ids).issubset(set(row.get('record_ids', []))):
            raise SystemExit(f'paper review route omits new records for {source}')
        route = row.get('url', '')
        page = relative_route(route, dist)
        if page in ('paper-review.html', 'paper.html') and urllib.parse.parse_qs(
                urllib.parse.urlsplit(route).query).get('id') != [row['id']]:
            raise SystemExit(f'paper route does not select the new source review: {source}')
        data = f"data/paper-reviews/{row['id']}.json"
        if not (Path(dist) / data).is_file():
            raise SystemExit(f'paper review data missing for {source}: {data}')
        out[source] = {'route': route, 'page': page, 'data': data}
    return out


def new_material_routes(dist, papers):
    """Every material hub touched by a new paper, including component and existing hubs."""
    if not papers:
        return {}
    index_path = Path(dist) / 'data/materials-index.json'
    index = json.loads(index_path.read_text(encoding='utf-8'))
    out = {source: [] for source in papers}
    for row in index.get('materials', []):
        material_id = row['id']
        data = f'data/materials/{material_id}.json'
        shard_path = Path(dist) / data
        if not shard_path.is_file():
            raise SystemExit(f'material shard missing: {data}')
        shard = json.loads(shard_path.read_text(encoding='utf-8'))
        if shard.get('id') != material_id:
            raise SystemExit(f'material shard identity differs from index: {data}')
        members = set(shard.get('record_ids', []))
        affected = [source for source, ids in papers.items() if members.intersection(ids)]
        if not affected:
            continue
        route = row.get('url', '')
        page = relative_route(route, dist)
        if page == 'material.html' and urllib.parse.parse_qs(
                urllib.parse.urlsplit(route).query).get('id') != [material_id]:
            raise SystemExit(f'material route does not select its indexed hub: {material_id}')
        binding = {'id': material_id, 'route': route, 'page': page, 'data': data}
        for source in affected:
            out[source].append(binding)
    for source, bindings in out.items():
        if not bindings:
            raise SystemExit(f'new paper has no material hub containing its synthesis records: {source}')
    return {source: sorted(bindings, key=lambda item: item['route']) for source, bindings in out.items()}


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


def papers_added_by_last_site_commit(site):
    """Papers whose records were added by the site's HEAD commit (for re-verifying a pushed release)."""
    names = run(['git', '-C', site, 'diff', '--name-only', '--diff-filter=A', 'HEAD~1', 'HEAD', '--', 'data/records']).split()
    out = {}
    for rel in names:
        if not rel.endswith('.json'):
            continue
        rec = json.loads((Path(site) / rel).read_text(encoding='utf-8'))
        src = (rec.get('lineage') or {}).get('source_group')
        if src:
            out.setdefault(src, []).append(rec['record_id'])
    return {k: sorted(v) for k, v in out.items()}


def site_built_from(site, commit):
    snap = Path(site) / 'data' / 'release-snapshot.json'
    return snap.exists() and json.loads(snap.read_text(encoding='utf-8')).get('source_commit') == commit


def source_ci_passed(repo_slug, commit, opener=None):
    url = f'https://api.github.com/repos/{repo_slug}/actions/runs?head_sha={commit}&per_page=50'
    runs = json.loads(http_get(url, {'Accept': 'application/vnd.github+json'}, opener)).get('workflow_runs', [])
    mine = [x for x in runs if x.get('name') == CI_WORKFLOW]
    return any(x.get('conclusion') == 'success' for x in mine), [(x.get('status'), x.get('conclusion')) for x in mine]


def wait_for_ci(repo_slug, commit, minutes, opener=None, sleep=time.sleep, poll_s=30):
    """Poll source CI for this commit. Returns (passed, runs). Stops early on a completed failure."""
    deadline = time.monotonic() + minutes * 60
    while True:
        ok, runs = source_ci_passed(repo_slug, commit, opener)
        finished = runs and all(status == 'completed' for status, _ in runs)
        if ok or finished or time.monotonic() > deadline:
            return ok, runs
        sleep(poll_s)


def fetch(url, opener=None):
    return http_get(url, {'Cache-Control': 'no-cache'}, opener)  # anonymous: no cookies, no credentials


def verify_live(site_url, dist, source_commit, paper_routes=None, material_routes=None,
                sample=40, timeout_s=1800, poll_s=20, opener=None, sleep=time.sleep):
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
    if material_routes:
        if 'data/materials-index.json' not in files:
            return {'passed': False, 'reason': 'built material index is missing', 'anonymous': True}
        must.append('data/materials-index.json')
    rest = sorted(set(files) - set(must)); random.Random(source_commit).shuffle(rest)
    checked, mismatched = [], []
    for rel in must + rest[:max(0, sample - len(must))]:
        try:
            live = hashlib.sha256(fetch(f'{base}{rel}?v={int(time.time())}', opener)).hexdigest()
            (checked if live == sha256(files[rel]) else mismatched).append(rel)
        except Exception:
            mismatched.append(rel)
    def check_route(binding):
        route = binding['route']
        route_url = urllib.parse.urljoin(base, route)
        route_url += ('&' if '?' in route_url else '?') + f'v={int(time.time())}'
        try:
            page_ok = hashlib.sha256(fetch(route_url, opener)).hexdigest() == sha256(files[binding['page']])
            data_ok = hashlib.sha256(fetch(f"{base}{binding['data']}?v={int(time.time())}", opener)).hexdigest() == sha256(files[binding['data']])
        except Exception:
            return False
        return page_ok and data_ok

    checked_routes, failed_routes = [], []
    for source, binding in sorted((paper_routes or {}).items()):
        (checked_routes if check_route(binding) else failed_routes).append(source)
    checked_materials, failed_materials = [], []
    for source, bindings in sorted((material_routes or {}).items()):
        for binding in bindings:
            label = f"{source}:{binding['id']}"
            (checked_materials if check_route(binding) else failed_materials).append(label)
    return {'passed': not mismatched and not failed_routes and not failed_materials and bool(checked), 'anonymous': True,
            'checked_files': len(checked), 'mismatched_files': mismatched,
            'checked_paper_routes': checked_routes, 'failed_paper_routes': failed_routes,
            'checked_material_routes': checked_materials, 'failed_material_routes': failed_materials,
            'source_commit': source_commit, 'verified_at': now(), 'site_url': base}


def ledger_events(papers, source_commit, site_url, receipt_sha256, at):
    return [{'event_id': f'live:{src}:{source_commit[:12]}', 'at': at, 'stage': 'live_verified', 'package_id': src,
             'primary_source_id': src, 'source_identity_verified': True, 'tier': 'gold', 'record_ids': ids,
             'commit': source_commit, 'url': site_url,
             'verification': {'anonymous': True, 'passed': True, 'receipt_sha256': receipt_sha256}}
            for src, ids in sorted(papers.items())]


def append_ledger_events(path, events):
    """Retries do not count a paper twice, even when the live receipt time changes."""
    path = Path(path)
    prior = {}
    if path.exists():
        for line in path.read_text(encoding='utf-8').splitlines():
            if line.strip():
                event = json.loads(line)
                if event.get('event_id'):
                    prior[event['event_id']] = event
    fresh = []
    for event in events:
        old = prior.get(event['event_id'])
        if old:
            identity = ('stage', 'package_id', 'primary_source_id', 'commit', 'record_ids')
            if any(old.get(key) != event.get(key) for key in identity):
                raise SystemExit(f"conflicting ledger event id: {event['event_id']}")
        else:
            fresh.append(event)
    if fresh:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('a', encoding='utf-8') as f:
            for event in fresh:
                f.write(json.dumps(event) + '\n')
    return len(fresh)


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def stage_controls(src, site, allow, sync_gate_tools):
    rc = Path(site) / '.release-control'
    rc.mkdir(exist_ok=True)
    shutil.copyfile(allow, rc / 'site-allowlist.json')
    shutil.copyfile(Path(src) / 'publication/asset-rights-registry.json', rc / 'asset-rights-registry.json')
    shutil.copyfile(Path(src) / 'publication/public-release-policy.json', rc / 'site-policy.json')
    if sync_gate_tools:
        tools = Path(site) / 'tools/mattersyn-release'
        if tools.exists():
            shutil.rmtree(tools)
        shutil.copytree(Path(src) / 'tools/mattersyn-release', tools,
                        ignore=shutil.ignore_patterns('__pycache__'))


def validate_browser_review(path, plan):
    if not path or not Path(path).is_file():
        raise SystemExit('--push requires a completed --review-receipt from the exact dry-run candidate')
    review = json.loads(Path(path).read_text(encoding='utf-8'))
    for key in ('source_commit', 'site_base_commit', 'release_id',
                'candidate_tree_sha256', 'preview_tree_sha256'):
        if review.get(key) != plan[key]:
            raise SystemExit(f'browser review does not match the prepared candidate: {key}')
    required = set(plan['review_routes'])
    checked = review.get('checked_routes', [])
    if (review.get('schema') != 'mattersyn-release-browser-review/1' or
            review.get('passed') is not True or not isinstance(review.get('reviewer'), str) or
            not review['reviewer'].strip() or not isinstance(review.get('reviewed_at'), str) or
            not review['reviewed_at'].strip() or not isinstance(checked, list) or
            not all(isinstance(route, str) for route in checked) or not required.issubset(set(checked))):
        raise SystemExit('browser review must attest a passed inspection of every required candidate route')
    return review


def validate_prepared(work, src, site, release_id, reviewer, sync_gate_tools, source_repo, site_url):
    path = Path(work) / 'release-plan.json'
    if not path.is_file():
        raise SystemExit('--push/--verify requires an existing --work from a successful dry run')
    plan = json.loads(path.read_text(encoding='utf-8'))
    if (plan.get('schema') != 'mattersyn-release-plan/1' or plan.get('source_path') != str(src) or
            plan.get('site_path') != str(site) or plan.get('release_id') != release_id or
            plan.get('reviewer') != reviewer or plan.get('sync_gate_tools') != sync_gate_tools or
            plan.get('source_repo') != source_repo or plan.get('site_url') != site_url):
        raise SystemExit('prepared release arguments differ from the dry run')
    if git(src, 'rev-parse', 'HEAD') != plan['source_commit']:
        raise SystemExit('source HEAD changed since candidate review')
    cand = Path(work) / 'candidate/project/recipe-atlas/dist'
    final = Path(work) / 'final/project/recipe-atlas/dist'
    preview = Path(work) / 'site-preview'
    for name, root, skip in (('candidate_tree_sha256', cand, ()), ('final_tree_sha256', final, ()),
                             ('preview_tree_sha256', preview, ('.git',))):
        if not root.is_dir() or tree_digest(root, skip) != plan[name]:
            raise SystemExit(f'prepared release changed since browser review: {name}')
    if plan['candidate_tree_sha256'] != plan['final_tree_sha256']:
        raise SystemExit('final build differs from the reviewed candidate')
    if (new_paper_routes(final, plan['new_papers']) != plan['paper_routes'] or
            new_material_routes(final, plan['new_papers']) != plan['material_routes']):
        raise SystemExit('required paper or material routes changed since browser review')
    required = sorted({binding['route'] for binding in plan['paper_routes'].values()} |
                      {binding['route'] for bindings in plan['material_routes'].values() for binding in bindings}) or ['index.html']
    if plan['review_routes'] != required:
        raise SystemExit('required browser routes changed since candidate review')
    if sha256(Path(work) / 'site-allowlist.json') != plan['allowlist_sha256']:
        raise SystemExit('site allowlist changed since the dry run')
    for name, file in (('site_manifest_sha256', 'site-manifest.json'),
                       ('site_boundary_sha256', 'site-boundary.json')):
        if sha256(Path(work) / file) != plan[name]:
            raise SystemExit(f'prepared site gate receipt changed since the dry run: {file}')
    if tree_digest(Path(work) / 'site-stage') != plan['site_stage_tree_sha256']:
        raise SystemExit('prepared site boundary output changed since the dry run')
    boundary = json.loads((Path(work) / 'site-boundary.json').read_text(encoding='utf-8'))
    if boundary.get('status') != 'passed':
        raise SystemExit('prepared site boundary gate did not pass')
    return plan


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--source', required=True, type=Path, help='clean source checkout at the commit to release')
    ap.add_argument('--site', required=True, type=Path, help='clean mattersyn-site checkout on main')
    ap.add_argument('--work', required=True, type=Path, help='new for dry run; reuse for push and live re-verification')
    ap.add_argument('--release-id', required=True)
    ap.add_argument('--reviewer', required=True, help='who approved the papers in this batch (quick audit)')
    ap.add_argument('--review-receipt', type=Path, help='completed browser review of the exact dry-run candidate; required for --push')
    ap.add_argument('--push', action='store_true', help='publish the previously prepared and browser-reviewed candidate')
    ap.add_argument('--verify', action='store_true', help='after --push check live, or retry checking a previously pushed release')
    ap.add_argument('--ledger', type=Path, help='private metrics ledger (JSONL) to append live_verified events to')
    ap.add_argument('--sync-gate-tools', action='store_true', help='also copy tools/mattersyn-release into the site')
    ap.add_argument('--source-repo', default='cuiyist/mattersyn')
    ap.add_argument('--site-url', default='https://cuiyist.github.io/mattersyn-site/')
    ap.add_argument('--skip-ci-check', action='store_true', help='dry runs only: do not require source CI success')
    ap.add_argument('--wait-ci', type=float, default=0, metavar='MINUTES', help='wait up to MINUTES for source CI to finish')
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
    if a.push and a.skip_ci_check:
        raise SystemExit('--skip-ci-check is only for dry runs')
    if a.push and not a.verify:
        raise SystemExit('--push requires --verify so every new paper route is checked after deployment')
    if a.push or a.verify:
        plan = validate_prepared(work, src, site, a.release_id, a.reviewer, a.sync_gate_tools,
                                 a.source_repo, a.site_url)
        commit = plan['source_commit']
        final = work / 'final/project/recipe-atlas/dist'
        summary = json.loads((work / 'release-summary.json').read_text(encoding='utf-8'))
        if a.push:
            if not any(plan[key] for key in ('files_added', 'files_changed', 'files_removed')):
                raise SystemExit('website content unchanged; nothing to publish')
            if (work / 'push-receipt.json').exists():
                raise SystemExit('this release was already pushed; use --verify alone to retry the live check')
            if git(site, 'rev-parse', 'HEAD') != plan['site_base_commit']:
                raise SystemExit('site HEAD changed since candidate review')
            validate_browser_review(a.review_receipt, plan)
            ok, seen = wait_for_ci(a.source_repo, commit, a.wait_ci)
            if not ok:
                raise SystemExit(f'source CI has not passed for {commit} (runs: {seen}); wait for CI')
            added_papers = plan['new_papers']
            stage_dist(final, site)
            stage_controls(src, site, work / 'site-allowlist.json', a.sync_gate_tools)
            if tree_digest(site, ('.git',)) != plan['preview_tree_sha256']:
                raise SystemExit('site staging differs from the reviewed, gated preview')
            git(site, 'add', '-A')
            body = '\n'.join(f'- {p} ({len(added_papers[p])} records)' for p in sorted(added_papers)) or '- no new source papers'
            run(['git', '-C', site, 'commit', '-q', '-m', f'Publish {len(added_papers)} papers ({a.release_id})', '-m',
                 f'Built from cuiyist/mattersyn {commit}.\n\n{body}'])
            run(['git', '-C', site, 'push', '-q', 'origin', 'HEAD:main'])
            pushed = {'source_commit': commit, 'site_commit': git(site, 'rev-parse', 'HEAD'), 'pushed_at': now()}
            write_json(work / 'push-receipt.json', pushed)
            summary.update(pushed=True, site_commit=pushed['site_commit'])
            mark('push')
        else:
            pushed_path = work / 'push-receipt.json'
            if not pushed_path.is_file():
                raise SystemExit('--verify without --push requires a previously pushed release in this --work path')
            pushed = json.loads(pushed_path.read_text(encoding='utf-8'))
            if (pushed.get('source_commit') != commit or git(site, 'rev-parse', 'HEAD') != pushed.get('site_commit') or
                    not site_built_from(site, commit)):
                raise SystemExit('site checkout no longer matches the pushed release')
        result = verify_live(a.site_url, final, commit, plan['paper_routes'], plan['material_routes'])
        receipt = work / 'live-verification.json'
        write_json(receipt, result)
        summary['live_verification'] = {k: result.get(k) for k in
                                        ('passed', 'checked_files', 'mismatched_files', 'checked_paper_routes',
                                         'failed_paper_routes', 'checked_material_routes',
                                         'failed_material_routes', 'reason')}
        mark('live_verification')
        if result['passed'] and a.ledger:
            events = ledger_events(plan['new_papers'], commit, a.site_url, sha256(receipt), result['verified_at'])
            summary['ledger_events'] = append_ledger_events(a.ledger, events)
        summary['stage_seconds'] = times
        write_json(work / 'release-summary.json', summary)
        print(json.dumps(summary, indent=1))
        return 0 if result['passed'] else 1

    if work.exists() and any(work.iterdir()):
        raise SystemExit('dry-run --work must be new or empty')
    commit = git(src, 'rev-parse', 'HEAD')
    site_base = git(site, 'rev-parse', 'HEAD')
    if not a.skip_ci_check:
        ok, seen = wait_for_ci(a.source_repo, commit, a.wait_ci)
        if not ok:
            raise SystemExit(f'source CI has not passed for {commit} (runs: {seen}); push it and wait for CI')
    work.mkdir(parents=True, exist_ok=True)
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
    candidate_hash = tree_digest(cand)
    if candidate_hash != tree_digest(final):
        raise SystemExit('final build differs from the reviewed candidate; stop and investigate')
    mark('final_build')
    added_papers = new_papers(site, final)
    paper_routes = new_paper_routes(final, added_papers)
    material_routes = new_material_routes(final, added_papers)
    preview = work / 'site-preview'
    git(site, 'worktree', 'add', '--detach', str(preview), 'HEAD')
    added, changed, removed = stage_dist(final, preview)
    stage_controls(src, preview, allow, a.sync_gate_tools)
    rc = preview / '.release-control'
    # The site boundary gate executes from the reviewed preview worktree. Suppress
    # Python bytecode there: an incidental __pycache__ would otherwise enter the
    # preview tree hash but never be staged into the publish checkout.
    run([py, '-B', preview / 'tools/mattersyn-release/export_release.py', '--source-root', preview,
         '--destination', work / 'site-stage', '--allowlist', rc / 'site-allowlist.json',
         '--registry', rc / 'asset-rights-registry.json', '--policy', rc / 'site-policy.json',
         '--repo', 'mattersyn-site', '--manifest-out', work / 'site-manifest.json',
         '--report-out', work / 'site-boundary.json'], cwd=preview)
    mark('stage_and_site_gate')
    review_routes = sorted({binding['route'] for binding in paper_routes.values()} |
                           {binding['route'] for bindings in material_routes.values() for binding in bindings}) or ['index.html']
    plan = {'schema': 'mattersyn-release-plan/1', 'source_path': str(src), 'site_path': str(site),
            'release_id': a.release_id, 'reviewer': a.reviewer, 'sync_gate_tools': a.sync_gate_tools,
            'source_repo': a.source_repo, 'site_url': a.site_url,
            'source_commit': commit, 'site_base_commit': site_base, 'new_papers': added_papers,
            'paper_routes': paper_routes, 'material_routes': material_routes, 'review_routes': review_routes,
            'candidate_tree_sha256': candidate_hash, 'final_tree_sha256': tree_digest(final),
            'preview_tree_sha256': tree_digest(preview, ('.git',)), 'allowlist_sha256': sha256(allow),
            'site_manifest_sha256': sha256(work / 'site-manifest.json'),
            'site_boundary_sha256': sha256(work / 'site-boundary.json'),
            'site_stage_tree_sha256': tree_digest(work / 'site-stage'),
            'files_added': added, 'files_changed': changed, 'files_removed': removed}
    write_json(work / 'release-plan.json', plan)
    template = {'schema': 'mattersyn-release-browser-review/1', 'source_commit': commit,
                'site_base_commit': site_base, 'release_id': a.release_id,
                'candidate_tree_sha256': candidate_hash, 'preview_tree_sha256': plan['preview_tree_sha256'],
                'passed': False, 'reviewer': '', 'reviewed_at': '',
                'checked_routes': [], 'required_routes': review_routes, 'notes': ''}
    write_json(work / 'browser-review.template.json', template)
    summary = {'release_id': a.release_id, 'source_commit': commit, 'new_papers': sorted(added_papers),
               'new_records': sum(len(v) for v in added_papers.values()), 'files_added': len(added),
               'files_changed': len(changed), 'files_removed': len(removed), 'pushed': False,
               'candidate_tree_sha256': candidate_hash, 'required_browser_routes': review_routes,
               'preview_path': str(preview), 'stage_seconds': times}
    if not (added or changed or removed):
        summary['note'] = 'website content unchanged; nothing to publish'
    write_json(work / 'release-summary.json', summary)
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
