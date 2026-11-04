#!/usr/bin/env python3
"""Build, check and publish the MatterSyn site from GitHub Actions.

This is the GitHub-hosted counterpart of `release_batch.py`. It runs the same
build commands and release checks, in the same order, and reuses that helper's
functions, so the site is built exactly as the local release builds it:

  build   1. make_runtime_snapshot.py binds the clean source commit
          2. build_release.py --candidate (complete build and every build test/check)
          3. prepare_allowlist.py derives the site allowlist from the candidate
          4. build_release.py with --gate/--allowlist/--policy (final gated build)
          5. the final tree must equal the candidate tree byte for byte
  stage   6. the exact site tree: final dist + the site's own control paths
             (.github, tools, .gitattributes) + refreshed .release-control
             (release_batch.stage_controls)
          7. the site boundary gate (export_release.py from the site's own tools,
             as the site's Pages workflow runs it)
          8. comparison with mattersyn-site main by Git blob id, using a blobless
             clone without checkout, so the site's 4.7 GB is never downloaded
  push    9. one ordinary commit on top of the site's main, pushed without force.
             Nothing is pushed when nothing changed; a moved site main fails.
  verify 10. wait for the site's Pages run, then release_batch.verify_live
             (the local release's anonymous live check)

`compare` (dry run) classifies every difference between the staged tree and the
site's main without printing file contents. Paper text is never read.
Standard library only.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import release_batch as rb  # noqa: E402  (same directory; reuses the local release helpers)

RAW_INPUT_DIRS = ('scripts', 'templates', 'data', 'static', 'tests')
REFRESHED_CONTROLS = ('site-allowlist.json', 'asset-rights-registry.json', 'site-policy.json')
PAGES_WORKFLOW = 'MatterSyn validated Pages release'
ZERO_OID = '0' * 40
TIMESTAMP = re.compile(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?')
DIST = Path('final/project/recipe-atlas/dist')


def log(message):
    print(f'[{dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")}] {message}', flush=True)


def fail(message):
    print(f'::error::{message}', flush=True)
    raise SystemExit(1)


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def step(name, cmd, cwd=None):
    """Run one release command, log its duration, and fail with its output tail."""
    started = time.monotonic()
    log(f'start: {name}')
    rb.run(cmd, cwd=cwd)
    log(f'done: {name} ({time.monotonic() - started:.0f} s)')


def git(repo, *args, env=None, input=None):
    result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, env=env, input=input)
    if result.returncode:
        fail(f'git {" ".join(args[:3])} failed: {result.stderr.decode("utf-8", "replace")[-2000:]}')
    return result.stdout.decode('utf-8')


def ls_tree(repo, rev='HEAD'):
    """path -> (mode, oid) from tree objects only; a blobless clone needs no blob for this."""
    out = {}
    for item in git(repo, 'ls-tree', '-r', '-z', '--full-tree', rev).split('\0'):
        if item:
            meta, path = item.split('\t', 1)
            mode, kind, oid = meta.split()
            if kind == 'blob':
                out[path] = (mode, oid)
    return out


def hash_objects(repo, paths, write=False):
    """Raw Git blob ids of local files (no filters), one git process for all files."""
    if not paths:
        return []
    args = ['hash-object', '--no-filters', '--stdin-paths'] + (['-w'] if write else [])
    out = git(repo, *args, input=('\n'.join(str(p) for p in paths) + '\n').encode('utf-8')).split()
    if len(out) != len(paths):
        fail('git hash-object returned the wrong number of ids')
    return out


def link_tree(source, destination):
    """Hard-link copy (no extra disk); falls back to a byte copy across filesystems."""
    def link(src, dst):
        try:
            os.link(src, dst)
        except OSError:
            shutil.copyfile(src, dst)
    shutil.copytree(source, destination, copy_function=link)


def diff_trees(preview, site):
    """Return (rows, added, changed, removed) for the staged tree against the site's HEAD."""
    head = ls_tree(site)
    files = rb.tree_files(preview)
    names = sorted(files)
    oids = dict(zip(names, hash_objects(site, [files[n] for n in names])))
    rows, added, changed = {}, [], []
    for name in names:
        before = head.get(name)
        mode = before[0] if before else '100644'
        rows[name] = (mode, oids[name])
        if before is None:
            added.append(name)
        elif before[1] != oids[name]:
            changed.append(name)
    removed = sorted(set(head) - set(files))
    return rows, added, changed, removed


# --------------------------------------------------------------------- build
def cmd_build(a):
    src, work = a.source.resolve(), a.work.resolve()
    if work == src or work.is_relative_to(src):
        fail('--work must be outside the source checkout')
    if rb.git(src, 'status', '--porcelain', '--untracked-files=all'):
        fail(f'source checkout is not clean: {src}')
    commit = rb.git(src, 'rev-parse', 'HEAD')
    if a.expect_commit and commit != a.expect_commit:
        fail(f'source checkout is {commit}, expected {a.expect_commit}')
    work.mkdir(parents=True, exist_ok=False)
    receipts = work / 'receipts'
    receipts.mkdir()
    py = sys.executable
    snap = work / 'snapshot.json'
    step('runtime snapshot', [py, src / 'recipe-atlas/scripts/make_runtime_snapshot.py', '--root', src,
                              '--blueprint', src / 'publication/build-inputs.json', '--output', snap], cwd=src)
    common = ['--snapshot', snap, '--registry', src / 'publication/asset-rights-registry.json',
              '--artifact-transform', src / 'tools/publication/source_link_artifacts.py']
    step('candidate build and build checks',
         [py, src / 'recipe-atlas/scripts/build_release.py', '--candidate', '--output', work / 'candidate', *common], cwd=src)
    cand = work / 'candidate/project/recipe-atlas/dist'
    candidate_hash = rb.tree_digest(cand)
    allow = work / 'site-allowlist.json'
    step('site allowlist from the candidate',
         [py, src / 'tools/publication/prepare_allowlist.py', '--root', cand,
          '--guard', src / 'tools/mattersyn-release/public_release_guard.py',
          '--policy', src / 'publication/public-release-policy.json',
          '--registry', src / 'publication/asset-rights-registry.json', '--repo', 'mattersyn-site',
          '--source-commit', commit, '--release-id', a.release_id, '--reviewer', a.reviewer, '--out', allow], cwd=src)
    shutil.copyfile(work / 'candidate/candidate-manifest.json', receipts / 'candidate-manifest.json')
    # The candidate's digest is kept; its bytes are removed before the final build
    # so the runner never holds two complete builds at once.
    shutil.rmtree(work / 'candidate')
    step('final gated build and build checks',
         [py, src / 'recipe-atlas/scripts/build_release.py', '--output', work / 'final', *common,
          '--gate', src / 'tools/mattersyn-release/gate.py', '--allowlist', allow,
          '--policy', src / 'publication/public-release-policy.json'], cwd=src)
    final = work / DIST
    final_hash = rb.tree_digest(final)
    if final_hash != candidate_hash:
        fail('final build differs from the candidate build; stop and investigate')
    log(f'final build equals the candidate: {final_hash}')
    for name in ('release-manifest.json', 'boundary-report.json'):
        if (work / 'final' / name).is_file():
            shutil.copyfile(work / 'final' / name, receipts / f'final-{name}')
    for name in RAW_INPUT_DIRS:  # copied build inputs; every later step reads only dist
        shutil.rmtree(work / 'final/project/recipe-atlas' / name, ignore_errors=True)
    rb.write_json(work / 'build.json', {
        'schema': 'mattersyn-ci-site-build/1', 'source_commit': commit, 'release_id': a.release_id,
        'reviewer': a.reviewer, 'candidate_tree_sha256': candidate_hash, 'final_tree_sha256': final_hash,
        'allowlist_sha256': rb.sha256(allow), 'built_at': rb.now()})
    return 0


# --------------------------------------------------------------------- stage
def cmd_stage(a):
    src, work, site = a.source.resolve(), a.work.resolve(), a.site.resolve()
    build = read_json(work / 'build.json')
    if rb.git(src, 'rev-parse', 'HEAD') != build['source_commit']:
        fail('source checkout changed since the build')
    final = work / DIST
    if rb.tree_digest(final) != build['final_tree_sha256']:
        fail('final build changed since it was checked')
    preview = work / 'site-preview'
    if preview.exists():
        fail('site preview already exists')
    site_base = rb.git(site, 'rev-parse', 'HEAD')
    head = ls_tree(site)
    for rel in rb.tree_files(final):
        if rel.split('/')[0] in rb.SITE_CONTROL:
            fail(f'build output must not contain site control path: {rel}')
    log('assemble the site tree: final dist (hard links) + site control paths')
    link_tree(final, preview)
    carried = []
    for path, (mode, oid) in sorted(head.items()):
        top = path.split('/')[0]
        if top not in rb.SITE_CONTROL or top == '.git':
            continue
        if top == '.release-control' and path.split('/', 1)[1] in REFRESHED_CONTROLS:
            continue  # replaced below, exactly as release_batch.stage_controls replaces them
        target = preview / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(subprocess.run(['git', '-C', str(site), 'cat-file', 'blob', oid],
                                          capture_output=True, check=True).stdout)
        carried.append(path)
    rb.stage_controls(src, preview, work / 'site-allowlist.json', a.sync_gate_tools)
    rc = preview / '.release-control'
    started = time.monotonic()
    log('start: site boundary gate')
    rb.run([sys.executable, '-B', preview / 'tools/mattersyn-release/export_release.py', '--source-root', preview,
            '--destination', work / 'site-stage', '--allowlist', rc / 'site-allowlist.json',
            '--registry', rc / 'asset-rights-registry.json', '--policy', rc / 'site-policy.json',
            '--repo', 'mattersyn-site', '--manifest-out', work / 'receipts/site-manifest.json',
            '--report-out', work / 'receipts/site-boundary.json'], cwd=preview)
    boundary = read_json(work / 'receipts/site-boundary.json')
    if boundary.get('status') != 'passed':
        fail('site boundary gate did not pass')
    stage_digest = rb.tree_digest(work / 'site-stage')
    shutil.rmtree(work / 'site-stage')  # the gate's copy; its digest is kept
    log(f'done: site boundary gate ({time.monotonic() - started:.0f} s, '
        f'{boundary.get("checked_files")} files checked)')
    rows, added, changed, removed = diff_trees(preview, site)
    added_papers = rb.new_papers(site, final)
    paper_routes = rb.new_paper_routes(final, added_papers)
    material_routes = rb.new_material_routes(final, added_papers)
    review_routes = sorted({b['route'] for b in paper_routes.values()} |
                           {b['route'] for bs in material_routes.values() for b in bs}) or ['index.html']
    stage = {'schema': 'mattersyn-ci-site-stage/1', 'source_commit': build['source_commit'],
             'release_id': build['release_id'], 'site_base_commit': site_base,
             'preview_tree_sha256': rb.tree_digest(preview), 'site_stage_tree_sha256': stage_digest,
             'carried_site_control_files': carried, 'new_papers': added_papers,
             'paper_routes': paper_routes, 'material_routes': material_routes, 'review_routes': review_routes,
             'files_added': added, 'files_changed': changed, 'files_removed': removed,
             'entries': {p: rows[p] for p in added + changed}}
    rb.write_json(work / 'stage.json', stage)
    rb.write_json(work / 'receipts/review-routes.json', review_routes)
    log(f'site main {site_base[:12]}: {len(added)} added, {len(changed)} changed, {len(removed)} removed; '
        f'{len(added_papers)} new papers, {len(review_routes)} affected routes')
    return 0


# ------------------------------------------------------------------- compare
def _json_differences(old, new, pointer=''):
    """Yield (pointer, timestamp_only) for each differing JSON leaf; values are never returned."""
    if isinstance(old, dict) and isinstance(new, dict):
        for key in sorted(set(old) | set(new)):
            sub = f'{pointer}/{key}'
            if key not in old or key not in new:
                yield sub, False
            else:
                yield from _json_differences(old[key], new[key], sub)
    elif isinstance(old, list) and isinstance(new, list) and len(old) == len(new):
        for index, (x, y) in enumerate(zip(old, new)):
            yield from _json_differences(x, y, f'{pointer}/{index}')
    elif old != new:
        stamp = isinstance(old, str) and isinstance(new, str) and bool(TIMESTAMP.fullmatch(old)) and bool(TIMESTAMP.fullmatch(new))
        yield pointer or '/', stamp


def _allowlist_difference(old, new):
    keep = ('sha256', 'bytes', 'content_class', 'decision', 'review_status', 'source_refs')
    o = {r['path']: r for r in old.get('files', [])}
    n = {r['path']: r for r in new.get('files', [])}
    differing = sorted(p for p in set(o) & set(n) if any(o[p].get(k) != n[p].get(k) for k in keep))
    return {'top_level_keys_differing': sorted(k for k in set(old) | set(new)
                                               if k != 'files' and old.get(k) != new.get(k)),
            'rows_only_on_site': len(set(o) - set(n)), 'rows_only_in_build': len(set(n) - set(o)),
            'rows_with_different_file_identity_or_class': len(differing), 'examples': differing[:20],
            'reviewer_values_site': sorted({r.get('reviewer', '') for r in o.values()})[:5],
            'reviewer_values_build': sorted({r.get('reviewer', '') for r in n.values()})[:5],
            'note': 'reviewer and reviewed_at are written when an allowlist is prepared'}


def classify(path, old, new):
    if path == '.release-control/site-allowlist.json':
        try:
            diff = _allowlist_difference(json.loads(old), json.loads(new))
        except ValueError:
            diff = None
        if diff is not None:
            same_rows = not (diff['rows_only_on_site'] or diff['rows_only_in_build'] or
                             diff['rows_with_different_file_identity_or_class'] or diff['top_level_keys_differing'])
            return {'class': 'allowlist review stamps only' if same_rows else 'content', **diff}
    try:
        diffs = list(_json_differences(json.loads(old), json.loads(new)))
        content = [p for p, stamp in diffs if not stamp]
        if not content:
            return {'class': 'timestamp-only', 'json_pointers': [p for p, _ in diffs][:20]}
        return {'class': 'content', 'json_pointers': content[:20], 'differing_values': len(content)}
    except ValueError:
        pass
    try:
        if TIMESTAMP.sub('<t>', old.decode('utf-8')) == TIMESTAMP.sub('<t>', new.decode('utf-8')):
            return {'class': 'timestamp-only'}
    except UnicodeDecodeError:
        pass
    return {'class': 'content', 'bytes_site': len(old), 'bytes_build': len(new)}


def cmd_compare(a):
    work, site = a.work.resolve(), a.site.resolve()
    stage = read_json(work / 'stage.json')
    head = ls_tree(site)
    preview = work / 'site-preview'
    details = []
    for path in stage['files_changed'][:a.limit]:
        old = subprocess.run(['git', '-C', str(site), 'cat-file', 'blob', head[path][1]],
                             capture_output=True, check=True).stdout
        details.append({'path': path, **classify(path, old, (preview / path).read_bytes())})
    classes = {}
    for row in details:
        classes[row['class']] = classes.get(row['class'], 0) + 1
    report = {'schema': 'mattersyn-ci-site-comparison/1', 'source_commit': stage['source_commit'],
              'site_commit': stage['site_base_commit'], 'files_compared': len(rb.tree_files(preview)),
              'identical_files': len(rb.tree_files(preview)) - len(stage['files_added']) - len(stage['files_changed']),
              'files_added': stage['files_added'], 'files_removed': stage['files_removed'],
              'files_changed': len(stage['files_changed']), 'changed_classified': len(details),
              'changed_by_class': classes, 'changed': details,
              'build_only_matches_site': not stage['files_added'] and not stage['files_removed'] and
              all(r['class'] in ('timestamp-only', 'allowlist review stamps only') for r in details) and
              len(details) == len(stage['files_changed'])}
    rb.write_json(work / 'receipts/site-comparison.json', report)
    log(f"comparison: {report['identical_files']} identical, {len(report['files_added'])} only in build, "
        f"{len(report['files_removed'])} only on site, {report['files_changed']} differing {classes}")
    return 0


# ---------------------------------------------------------------------- push
def cmd_push(a):
    work, site = a.work.resolve(), a.site.resolve()
    stage = read_json(work / 'stage.json')
    result = {'schema': 'mattersyn-ci-site-push/1', 'source_commit': stage['source_commit'],
              'site_base_commit': stage['site_base_commit'], 'pushed': False}
    if not (stage['files_added'] or stage['files_changed'] or stage['files_removed']):
        log('website content unchanged; nothing to publish')
        rb.write_json(work / 'push.json', {**result, 'reason': 'unchanged'})
        return 0
    token = os.environ.get(a.token_env, '').strip()
    if not token:
        print(f'::warning::{a.token_env} is not set: the site was built and checked, but nothing was pushed.', flush=True)
        rb.write_json(work / 'push.json', {**result, 'reason': f'{a.token_env} not set'})
        return 0
    preview = work / 'site-preview'
    if rb.tree_digest(preview) != stage['preview_tree_sha256']:
        fail('staged site tree changed after its boundary gate')
    base = stage['site_base_commit']
    remote = git(site, 'ls-remote', 'origin', 'refs/heads/main').split()
    if not remote or remote[0] != base:
        fail(f'mattersyn-site main moved during this run (was {base}, now {remote[0] if remote else "missing"}); '
             'nothing was pushed. Re-run this workflow to build on top of the new site main.')
    write = stage['files_added'] + stage['files_changed']
    written = hash_objects(site, [preview / p for p in write], write=True)
    if written != [stage['entries'][p][1] for p in write]:
        fail('staged file bytes changed before the commit')
    env = {**os.environ, 'GIT_INDEX_FILE': str(work / 'site-publish.index')}
    git(site, 'read-tree', base, env=env)
    lines = [f'{stage["entries"][p][0]} {stage["entries"][p][1]}\t{p}' for p in write]
    lines += [f'0 {ZERO_OID}\t{p}' for p in stage['files_removed']]
    git(site, 'update-index', '--index-info', env=env, input=('\n'.join(lines) + '\n').encode('utf-8'))
    tree = git(site, 'write-tree', '--missing-ok', env=env).strip()
    names = {line.split('\t', 1)[1] for line in git(site, 'diff-tree', '-r', '--no-renames', '--name-status', base, tree).splitlines() if line}
    if names != set(write) | set(stage['files_removed']):
        fail('the publish tree does not contain exactly the staged changes')
    short = stage['source_commit'][:7]
    body = f'Built from cuiyist/mattersyn {stage["source_commit"]} by the site publish workflow'
    if a.run_url:
        body += f' ({a.run_url})'
    papers = stage['new_papers']
    body += '.\n\n' + ('\n'.join(f'- {p} ({len(papers[p])} records)' for p in sorted(papers)) or '- no new source papers')
    who = {'GIT_AUTHOR_NAME': 'github-actions[bot]', 'GIT_COMMITTER_NAME': 'github-actions[bot]',
           'GIT_AUTHOR_EMAIL': '41898282+github-actions[bot]@users.noreply.github.com',
           'GIT_COMMITTER_EMAIL': '41898282+github-actions[bot]@users.noreply.github.com'}
    commit = git(site, 'commit-tree', tree, '-p', base, '-m', f'Publish site from source {short}', '-m', body,
                 env={**os.environ, **who}).strip()
    header = 'AUTHORIZATION: basic ' + base64.b64encode(f'x-access-token:{token}'.encode()).decode()
    pushed = subprocess.run(['git', '-C', str(site), '-c', f'http.https://github.com/.extraheader={header}',
                             'push', '--no-thin', '--porcelain', 'origin', f'{commit}:refs/heads/main'],
                            capture_output=True, text=True)
    if pushed.returncode:
        now_remote = git(site, 'ls-remote', 'origin', 'refs/heads/main').split()
        moved = now_remote and now_remote[0] != base
        fail(('mattersyn-site main moved during this run; ' if moved else '') +
             'the site push was refused and nothing was published: ' + (pushed.stdout + pushed.stderr)[-1500:].replace(token, '***'))
    result.update(pushed=True, site_commit=commit, pushed_at=rb.now(),
                  files_added=len(stage['files_added']), files_changed=len(stage['files_changed']),
                  files_removed=len(stage['files_removed']))
    rb.write_json(work / 'push.json', result)
    log(f'pushed site commit {commit} ("Publish site from source {short}")')
    return 0


# -------------------------------------------------------------------- verify
def wait_for_pages(site_repo, site_commit, minutes, token=None, sleep=time.sleep, poll_s=30):
    headers = {'Accept': 'application/vnd.github+json', **({'Authorization': f'Bearer {token}'} if token else {})}
    url = f'https://api.github.com/repos/{site_repo}/actions/runs?head_sha={site_commit}&per_page=20'
    deadline = time.monotonic() + minutes * 60
    while True:
        try:
            runs = [r for r in json.loads(rb.http_get(url, headers)).get('workflow_runs', []) if r.get('name') == PAGES_WORKFLOW]
        except Exception as exc:  # transient API failure: keep waiting until the deadline
            log(f'Pages run lookup failed: {exc.__class__.__name__}')
            runs = []
        if runs and all(r.get('status') == 'completed' for r in runs):
            return any(r.get('conclusion') == 'success' for r in runs), [(r.get('id'), r.get('conclusion')) for r in runs]
        if time.monotonic() > deadline:
            return False, [(r.get('id'), r.get('status')) for r in runs]
        sleep(poll_s)


def cmd_verify(a):
    work = a.work.resolve()
    push = read_json(work / 'push.json')
    if not push.get('pushed'):
        log(f'nothing was pushed ({push.get("reason")}); no live check')
        return 0
    stage = read_json(work / 'stage.json')
    log(f'waiting for {PAGES_WORKFLOW} on {push["site_commit"][:12]}')
    ok, runs = wait_for_pages(a.site_repo, push['site_commit'], a.pages_minutes, os.environ.get('GITHUB_TOKEN'))
    if not ok:
        rb.write_json(work / 'receipts/live-verification.json', {'passed': False, 'pages_runs': runs})
        fail(f'the site Pages workflow did not succeed for {push["site_commit"]}: {runs}')
    log(f'Pages run finished: {runs}; anonymous live check')
    result = rb.verify_live(a.site_url, work / DIST, stage['source_commit'], stage['paper_routes'],
                            stage['material_routes'],
                            changed_paths=sorted(set(stage['files_added']) | set(stage['files_changed'])))
    result['pages_runs'] = runs
    rb.write_json(work / 'receipts/live-verification.json', result)
    if not result['passed']:
        fail(f'live check failed: {result.get("reason") or result.get("mismatched_files")[:10]}')
    log(f"live check passed: {result['checked_files']} files, {len(result['checked_paper_routes'])} paper routes, "
        f"{len(result['checked_material_routes'])} material routes")
    return 0


# ------------------------------------------------------------------- summary
def cmd_summary(a):
    work = a.work.resolve()
    lines = ['## MatterSyn site publish', '']
    for name, label in (('build.json', 'Build'), ('stage.json', 'Stage'), ('push.json', 'Push'),
                        ('receipts/site-comparison.json', 'Dry-run comparison'),
                        ('receipts/live-verification.json', 'Live check'), ('receipts/browser/receipt.json', 'Browser check')):
        path = work / name
        if not path.is_file():
            lines.append(f'- {label}: not reached')
            continue
        data = read_json(path)
        if name == 'build.json':
            lines.append(f"- {label}: source `{data['source_commit']}`, final build equals candidate (`{data['final_tree_sha256'][:16]}`)")
        elif name == 'stage.json':
            lines.append(f"- {label}: boundary gate passed; against site `{data['site_base_commit'][:12]}`: "
                         f"{len(data['files_added'])} added, {len(data['files_changed'])} changed, {len(data['files_removed'])} removed")
        elif name == 'push.json':
            lines.append(f"- {label}: " + (f"pushed `{data['site_commit']}`" if data.get('pushed') else f"nothing pushed ({data.get('reason')})"))
        elif name.endswith('site-comparison.json'):
            lines.append(f"- {label}: {data['identical_files']} identical files, {len(data['files_added'])} only in build, "
                         f"{len(data['files_removed'])} only on site, {data['files_changed']} differing {data['changed_by_class']}; "
                         f"matches apart from timestamps and allowlist review stamps: **{data['build_only_matches_site']}**")
        elif name.endswith('live-verification.json'):
            lines.append(f"- {label}: passed **{data.get('passed')}**, {data.get('checked_files')} files")
        else:
            lines.append(f"- {label}: {data.get('summary')}")
    text = '\n'.join(lines) + '\n'
    print(text)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as handle:
            handle.write(text)
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='command', required=True)
    b = sub.add_parser('build')
    b.add_argument('--source', type=Path, required=True)
    b.add_argument('--work', type=Path, required=True)
    b.add_argument('--release-id', required=True)
    b.add_argument('--reviewer', required=True)
    b.add_argument('--expect-commit')
    s = sub.add_parser('stage')
    s.add_argument('--source', type=Path, required=True)
    s.add_argument('--work', type=Path, required=True)
    s.add_argument('--site', type=Path, required=True, help='blobless mattersyn-site clone on main')
    s.add_argument('--sync-gate-tools', action='store_true')
    c = sub.add_parser('compare')
    c.add_argument('--work', type=Path, required=True)
    c.add_argument('--site', type=Path, required=True)
    c.add_argument('--limit', type=int, default=2000)
    u = sub.add_parser('push')
    u.add_argument('--work', type=Path, required=True)
    u.add_argument('--site', type=Path, required=True)
    u.add_argument('--token-env', default='SITE_PUSH_TOKEN')
    u.add_argument('--run-url', default='')
    v = sub.add_parser('verify')
    v.add_argument('--work', type=Path, required=True)
    v.add_argument('--site-repo', default='cuiyist/mattersyn-site')
    v.add_argument('--site-url', default='https://cuiyist.github.io/mattersyn-site/')
    v.add_argument('--pages-minutes', type=float, default=45)
    m = sub.add_parser('summary')
    m.add_argument('--work', type=Path, required=True)
    a = p.parse_args(argv)
    return {'build': cmd_build, 'stage': cmd_stage, 'compare': cmd_compare, 'push': cmd_push,
            'verify': cmd_verify, 'summary': cmd_summary}[a.command](a)


if __name__ == '__main__':
    sys.exit(main())
