"""Private prototype: one existing full build, sealed evidence, fresh boundary.

No network, source writes, git mutations, publishing, retroactive seals, or skip-
tests option. Reviewed external SHA pins and an exclusively owned local workspace
are trust requirements; hashes are not signatures or an OS-level writer lock.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
import unicodedata

BUILD = 'recipe-atlas/scripts/build_release.py'
COMPARE = 'recipe-atlas/scripts/compare_candidate_manifests.py'
GATE = 'tools/mattersyn-release/gate.py'
TRANSFORM = 'tools/publication/source_link_artifacts.py'
POLICY = 'publication/public-release-policy.json'
REGISTRY = 'publication/asset-rights-registry.json'
COPY_DIRS = tuple('recipe-atlas/' + n for n in ('scripts', 'templates', 'data', 'static', 'tests'))
CODE = (BUILD, COMPARE, GATE, TRANSFORM, 'tools/mattersyn-release/public_release_guard.py')
BUILDERS = ('build_dataset.py', 'build_reader_views.py', 'build_evidence_views.py',
            'build_paper_reviews.py', 'build_atlas.py', 'build_inventory.py', 'build_reader_metadata.py')
HEX64 = re.compile(r'[0-9a-f]{64}\Z')


class Rejected(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise Rejected(reason)


def unique(pairs):
    result = {}
    for k, v in pairs:
        require(k not in result, 'duplicate_json_key')
        result[k] = v
    return result


def loads(raw):
    return json.loads(raw, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(Rejected('nonfinite_json')))


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def path_name(name):
    require(isinstance(name, str) and name and '\\' not in name and ':' not in name,
            'invalid_relative_path')
    require(unicodedata.normalize('NFC', name) == name, 'noncanonical_unicode_path')
    for part in name.split('/'):
        require(part not in ('', '.', '..') and part.rstrip(' .') == part and
                not re.search(r'[\x00-\x1f<>"|?*]', part), 'unsafe_path_segment')
        require(not re.fullmatch(r'(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?', part, re.I),
                'windows_device_path')
    return name


def no_link(path):
    # Check every existing ancestor as well as the leaf; resolve alone conceals links.
    path = Path(os.path.abspath(path))
    for p in (path, *path.parents):
        try:
            s = p.lstat()
        except FileNotFoundError:
            # New output paths may not exist; their existing ancestors still must pass.
            continue
        require(not stat.S_ISLNK(s.st_mode) and
                not (getattr(s, 'st_file_attributes', 0) & 0x400), 'symlink_or_reparse')
    return path


def runtime_binding(path):
    # Only the operator-managed Python executable may traverse runtime links.
    # Bind the invoked spelling, every ancestor identity, and the resolved target;
    # source/artifact callers continue through no_link without this exception.
    invoked = Path(os.path.abspath(path))
    require(invoked == Path(os.path.abspath(sys.executable)), 'not_trusted_runtime_executable')
    resolved = invoked.resolve(strict=True)
    ancestry = []
    for member in (invoked, *invoked.parents):
        s = member.lstat()
        attrs = getattr(s, 'st_file_attributes', 0)
        row = {'path': str(member), 'identity': [s.st_dev, s.st_ino, s.st_mode, attrs]}
        if stat.S_ISLNK(s.st_mode) or attrs & 0x400:
            row['link_identity'] = [s.st_size, s.st_mtime_ns, s.st_ctime_ns]
        ancestry.append(row)
    target = no_link(resolved).stat()
    require(stat.S_ISREG(target.st_mode), 'not_regular_runtime_executable')
    return {'invoked_path': str(invoked), 'resolved_path': str(resolved),
            'ancestry': ancestry,
            'target_identity': [target.st_dev, target.st_ino, target.st_size,
                                target.st_mtime_ns, target.st_ctime_ns]}


def stable_bytes(path, *, runtime_executable=False):
    runtime = runtime_binding(path) if runtime_executable else None
    if runtime is not None:
        path = runtime['resolved_path']
    path = no_link(path)
    before = path.stat()
    require(stat.S_ISREG(before.st_mode) and (runtime_executable or before.st_nlink == 1), 'not_unique_regular_file')
    with path.open('rb') as f:
        opened = os.fstat(f.fileno())
        raw = f.read()
        f.seek(0)
        confirm = f.read()
        closed = os.fstat(f.fileno())
    after = path.stat()
    key = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    # Windows stat/fstat can report different ctime semantics. Compare ctime
    # within each API, but inode/device/size/mtime across both; reread exact bytes.
    require(key(before) == key(after) and key(opened) == key(closed) and
            key(before)[:-1] == key(opened)[:-1] and raw == confirm and len(raw) == after.st_size,
            'file_changed_during_read')
    no_link(path)
    if runtime is not None:
        require(runtime_binding(runtime['invoked_path']) == runtime, 'runtime_identity_changed_during_read')
    return raw


def sha(path):
    return digest(stable_bytes(path))


def read(path):
    return loads(stable_bytes(path))


def pinned(binding):
    require(set(binding) == {'path', 'sha256'} and isinstance(binding['sha256'], str) and
            HEX64.fullmatch(binding['sha256']), 'invalid_pin')
    raw = stable_bytes(binding['path'])
    require(digest(raw) == binding['sha256'], 'pin_drift:' + str(binding['path']))
    return raw


def pin(path):
    return {'path': str(no_link(path)), 'sha256': sha(path)}


def write_new(path, obj):
    no_link(path)
    with Path(path).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')


def listing(root):
    root = no_link(root)
    require(root.is_dir(), 'missing_directory')
    files, folded = [], set()
    for parent, directories, names in os.walk(root, followlinks=False):
        for name in sorted(directories + names):
            p = no_link(Path(parent) / name)
            rel = path_name(p.relative_to(root).as_posix())
            require(rel.casefold() not in folded, 'case_colliding_path')
            folded.add(rel.casefold())
            if p.is_file():
                files.append(rel)
            else:
                require(p.is_dir(), 'special_file')
    return sorted(files)


def inventory(root):
    paths = listing(root)
    rows = []
    for name in paths:
        raw = stable_bytes(Path(root) / name)
        rows.append({'path': name, 'sha256': digest(raw), 'bytes': len(raw)})
    require(listing(root) == paths, 'directory_membership_race')
    return rows


def rows_map(rows):
    require(isinstance(rows, list) and rows, 'empty_inventory')
    result, folded = {}, set()
    for row in rows:
        require(set(row) == {'path', 'sha256', 'bytes'}, 'invalid_file_row')
        name = path_name(row['path'])
        require(name.casefold() not in folded, 'duplicate_or_case_colliding_path')
        require(isinstance(row['sha256'], str) and HEX64.fullmatch(row['sha256']) and
                type(row['bytes']) is int and row['bytes'] >= 0, 'invalid_file_digest_or_size')
        result[name] = row
        folded.add(name.casefold())
    return result


def git(source, *args):
    return subprocess.check_output(['git', '-C', str(source), *args], env=run_env())


def run_env():
    # Do not inherit secrets, Python import overrides, or Git command/config
    # overrides. Bind the exact small environment used by all child processes.
    allowed = {'PATH', 'PATHEXT', 'SYSTEMROOT', 'WINDIR', 'COMSPEC', 'TEMP', 'TMP',
               'HOME', 'USERPROFILE', 'LOCALAPPDATA', 'APPDATA', 'LANG', 'LC_ALL', 'TZ'}
    env = {k: v for k, v in os.environ.items() if k.upper() in allowed}
    env.update(PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1')
    return env


def source_state(source, head):
    source = no_link(source)
    require(Path(git(source, 'rev-parse', '--show-toplevel').decode().strip()).resolve() == source.resolve(),
            'not_git_root')
    require(git(source, 'rev-parse', 'HEAD').decode().strip() == head, 'source_head_drift')
    require(not git(source, 'status', '--porcelain', '--untracked-files=all').strip(), 'dirty_source')
    rows = []
    for entry in git(source, 'ls-tree', '-rz', '--full-tree', 'HEAD').split(b'\0'):
        if not entry:
            continue
        meta, raw_path = entry.split(b'\t', 1)
        mode, kind, oid = meta.decode().split()
        require(mode in ('100644', '100755') and kind == 'blob', 'unsupported_git_entry')
        name = path_name(raw_path.decode('utf-8'))
        raw = stable_bytes(source / name)
        # Git status alone can miss same-stat or skip-worktree changes.
        require(hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == oid,
                'working_bytes_differ_from_commit:' + name)
        rows.append({'path': name, 'sha256': digest(raw), 'bytes': len(raw)})
    mapped = rows_map(rows)
    # Ignored files can enter copytree or shadow imports even while Git is clean.
    for scope in (*COPY_DIRS, 'tools'):
        actual = {scope + '/' + n for n in listing(source / scope)}
        expected = {n for n in mapped if n.startswith(scope + '/')}
        require(actual == expected, 'untracked_or_ignored_build_input:' + scope)
    require(git(source, 'rev-parse', 'HEAD').decode().strip() == head and
            not git(source, 'status', '--porcelain', '--untracked-files=all').strip(), 'source_race')
    return sorted(rows, key=lambda x: x['path'])


def runtime_state():
    # Runtime is a trusted operator-managed environment, not a hermetic sandbox.
    # Versions/executable/env are bound to detect ordinary changes. Fresh guard
    # executes again; no runtime-dependent policy verdict is reused.
    # Conda hardlinks and hosted Linux symlinks are allowed only for this runtime.
    runtime = runtime_binding(sys.executable)
    executable_sha256 = digest(stable_bytes(sys.executable, runtime_executable=True))
    require(runtime_binding(sys.executable) == runtime, 'runtime_identity_changed_during_read')
    return {'python_sha256': executable_sha256, 'python_executable': runtime, 'python_version': sys.version,
            'prefix': sys.prefix, 'platform': sys.platform,
            'packages': sorted([d.metadata.get('Name', ''), d.metadata.get('Version', '')]
                               for d in importlib.metadata.distributions()),
            'environment': {k: v for k, v in sorted(run_env().items()) if k not in ('_', 'PROMPT')}}


def comparator(source):
    spec = importlib.util.spec_from_file_location('_reviewed_candidate_compare', Path(source) / COMPARE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def disjoint_new(out, roots):
    out = no_link(out)
    require(not out.exists() and out.parent.is_dir(), 'output_exists_or_parent_missing')
    for root in roots:
        root = no_link(root)
        require(not out.is_relative_to(root) and not root.is_relative_to(out), 'output_not_disjoint')
    return out


def snapshot_check(source, path, head, source_rows):
    require(not no_link(path).is_relative_to(no_link(source)), 'snapshot_inside_source')
    snapshot = read(path)
    require(snapshot.get('schema') == 'mattersyn-release-snapshot/1' and snapshot.get('source_commit') == head,
            'snapshot_identity')
    blueprint_path = Path(source) / 'publication/build-inputs.json'
    blueprint = read(blueprint_path)
    require(snapshot.get('blueprint_sha256') == sha(blueprint_path), 'snapshot_blueprint_drift')
    expected = {k: v for k, v in blueprint.items() if k not in ('schema', 'note')}
    expected.update(schema='mattersyn-release-snapshot/1', source_commit=head, blueprint_sha256=sha(blueprint_path))
    require(snapshot == expected, 'snapshot_not_exact_blueprint_projection')
    source_rows = rows_map(source_rows)
    for name, row in rows_map(snapshot['input_files']).items():
        require(source_rows.get(name) == row, 'snapshot_input_drift')
    return snapshot


def commands(source, candidate):
    python = sys.executable
    work = Path(candidate) / 'project/recipe-atlas'
    def transform(phase):
        return [python, str((Path(source) / TRANSFORM).resolve()), '--phase', phase,
                '--root', str((work / 'dist').resolve()), '--source-root', str(work.resolve()),
                '--registry', str((Path(source) / REGISTRY).resolve())]
    return [transform('prebuild'), *[[python, 'scripts/' + n] for n in BUILDERS],
            transform('postbuild'), [python, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
            *[[python, 'scripts/' + n] for n in ('check_site.py', 'check_atlas.py', 'check_quality.py')]]


def check_log(source, candidate, expected_tests):
    log = read(Path(candidate) / 'build-log.json')
    require(type(expected_tests) is int and expected_tests > 0, 'missing_expected_test_count')
    require(isinstance(log, list) and len(log) == 13, 'incomplete_build_log')
    require([r.get('command') for r in log] == commands(source, candidate), 'build_stage_order_or_command_drift')
    require(all(type(r.get('returncode')) is int and r['returncode'] == 0 for r in log), 'failed_build_stage')
    summary = re.search(r'Ran (\d+) tests? in [\d.]+s\s+OK\s*\Z', log[9]['stderr'])
    require(summary and int(summary[1]) == expected_tests, 'test_discovery_or_success_drift')
    qa = loads(log[-1]['stdout'])
    require(qa.get('passed') is True and qa.get('errors') == [] and qa.get('warnings') == [] and
            type(qa.get('counts', {}).get('checks')) is int and qa['counts']['checks'] > 0, 'quality_failed')
    return {'tests': expected_tests, 'quality_checks': qa['counts']['checks'], 'stages': 13}


def execute(command, cwd):
    start = time.perf_counter()
    result = subprocess.run(command, cwd=cwd, env=run_env(), text=True, encoding='utf-8',
                            errors='replace', capture_output=True)
    return {'command': command, 'returncode': result.returncode, 'stdout': result.stdout,
            'stderr': result.stderr, 'elapsed_seconds': time.perf_counter() - start}


def build(source, snapshot_path, out, contract_path, contract_sha):
    source, snapshot_path = no_link(source), no_link(snapshot_path)
    contract_pin = {'path': str(no_link(contract_path)), 'sha256': contract_sha}
    contract = loads(pinned(contract_pin))
    require(contract.get('schema') == 'mattersyn-one-build-contract/1', 'contract_schema')
    head = contract['source_commit']
    require(re.fullmatch('[0-9a-f]{40}', head), 'invalid_head')
    require(contract.get('snapshot_sha256') == sha(snapshot_path), 'contract_snapshot_drift')
    require(set(contract['code_sha256']) == set(CODE), 'incomplete_code_contract')
    require(all(sha(source / n) == h for n, h in contract['code_sha256'].items()), 'code_contract_drift')
    before = source_state(source, head)
    snapshot_check(source, snapshot_path, head, before)
    runtime = runtime_state()
    out = disjoint_new(out, [source, snapshot_path, contract_path])
    wrapper_sha = sha(__file__)
    run = execute([sys.executable, str(source / BUILD), '--candidate', '--output', str(out),
                   '--snapshot', str(snapshot_path), '--registry', str(source / REGISTRY),
                   '--artifact-transform', str(source / TRANSFORM)], source)
    if out.is_dir():
        write_new(out / 'wrapper-build-run.private.json', run)
    require(run['returncode'] == 0, 'full_build_failed')
    checks = check_log(source, out, contract['expected_tests'])
    manifest = read(out / 'candidate-manifest.json')
    comparator(source).validate(manifest)
    require(manifest['source_commit'] == head and manifest['snapshot_sha256'] == sha(snapshot_path), 'candidate_identity')
    require(rows_map(manifest['files']) == rows_map(inventory(out / 'project/recipe-atlas/dist')), 'candidate_inventory_drift')
    require(source_state(source, head) == before and runtime_state() == runtime and
            sha(__file__) == wrapper_sha, 'inputs_or_runtime_changed_during_build')
    pinned(contract_pin)
    require(sha(snapshot_path) == contract['snapshot_sha256'], 'snapshot_race')
    seal = {'schema': 'mattersyn-one-build-seal/1', 'status': 'SEALED_UNAPPROVED_CANDIDATE',
            'source_root': str(source), 'source_commit': head, 'source_files': before,
            'runtime': runtime, 'wrapper_sha256': wrapper_sha, 'contract': contract_pin,
            'snapshot': pin(snapshot_path), 'candidate_manifest': pin(out / 'candidate-manifest.json'),
            'build_log': pin(out / 'build-log.json'), 'wrapper_run': pin(out / 'wrapper-build-run.private.json'),
            'checks': checks, 'published': False}
    write_new(out / 'build-seal.private.json', seal)
    return pin(out / 'build-seal.private.json')


def verify_seal(source, candidate, seal_sha):
    seal = loads(pinned({'path': str(Path(candidate) / 'build-seal.private.json'), 'sha256': seal_sha}))
    require(seal['schema'] == 'mattersyn-one-build-seal/1' and seal['published'] is False and
            seal['status'] == 'SEALED_UNAPPROVED_CANDIDATE', 'invalid_seal')
    require(no_link(source) == Path(seal['source_root']) and sha(__file__) == seal['wrapper_sha256'], 'seal_tool_or_source')
    require(source_state(source, seal['source_commit']) == seal['source_files'], 'source_input_drift')
    require(runtime_state() == seal['runtime'], 'runtime_drift')
    for key, name in [('candidate_manifest', 'candidate-manifest.json'), ('build_log', 'build-log.json'),
                      ('wrapper_run', 'wrapper-build-run.private.json')]:
        require(Path(seal[key]['path']) == no_link(Path(candidate) / name), 'candidate_location_drift')
        pinned(seal[key])
    contract = loads(pinned(seal['contract']))
    pinned(seal['snapshot'])
    snapshot_check(source, seal['snapshot']['path'], seal['source_commit'], seal['source_files'])
    require(check_log(source, candidate, contract['expected_tests']) == seal['checks'], 'build_receipt_drift')
    manifest = loads(pinned(seal['candidate_manifest']))
    comparator(source).validate(manifest)
    require(rows_map(manifest['files']) == rows_map(inventory(Path(candidate) / 'project/recipe-atlas/dist')),
            'candidate_inventory_drift')
    return seal, manifest


def boundary_ok(report, repo, count):
    require(type(count) is int and count > 0 and
            all(type(report.get(k)) is int for k in ('failure_count', 'checked_files', 'passed_files')) and
            report.get('schema_version') == 'mattersyn-public-boundary-report/1' and
            report.get('repo') == repo and report.get('status') == 'passed' and
            report.get('failure_count') == 0 and report.get('checked_files') == count and
            report.get('passed_files') == count, 'boundary_failed_or_incomplete')


def verify_evidence(source, manifest, review):
    require(review.get('schema') == 'mattersyn-one-build-promotion-review/1' and
            review.get('status') == 'REVIEWED_PENDING_FRESH_BOUNDARY' and
            review.get('source_commit') == manifest['source_commit'], 'review_identity')
    # This independently reviewed descriptor attests real scientific/browser
    # review and CI artifact provenance. The tool cannot authenticate fabricated
    # offline receipts. Root pins its SHA only after inspecting that provenance.
    for key in ('science_receipts', 'browser_receipts'):
        require(isinstance(review.get(key), list) and review[key], 'missing_' + key)
        for receipt in review[key]:
            pinned(receipt)
    require(review.get('browser_artifact_files'), 'missing_browser_byte_bindings')
    actual = rows_map(manifest['files'])
    for row in review['browser_artifact_files']:
        require(actual.get(path_name(row['path'])) == row, 'browser_artifact_drift')
    ci = loads(pinned(review['source_ci']))
    require(isinstance(ci, list), 'ci_schema')
    runs = [r for r in ci if r.get('repo') == 'mattersyn' and r.get('head_sha') == manifest['source_commit']]
    require(len(runs) == 1, 'missing_or_ambiguous_exact_head_ci')
    run = runs[0]
    require(run.get('status') == 'completed' and run.get('conclusion') == 'success', 'ci_not_successful')
    jobs = run.get('jobs', [])
    for name in ('validate (windows-latest)', 'validate (ubuntu-latest)', 'compare-artifacts'):
        matches = [j for j in jobs if j.get('name') == name]
        require(len(matches) == 1 and matches[0].get('status') == 'completed' and
                matches[0].get('conclusion') == 'success' and not matches[0].get('failed_steps'), 'ci_required_job_failed')
    comparison = comparator(source)
    require(set(review['ci_manifests']) == {'windows-latest', 'ubuntu-latest'}, 'missing_ci_manifest')
    for binding in review['ci_manifests'].values():
        require(comparison.compare(manifest, loads(pinned(binding)))['passed'], 'ci_artifact_not_identical')
    source_manifest = loads(pinned(review['source_boundary_manifest']))
    source_report = loads(pinned(review['source_boundary_report']))
    require(source_manifest.get('source_commit') == manifest['source_commit'] and
            source_manifest.get('policy_sha256') == sha(Path(source) / POLICY) and
            source_manifest.get('asset_rights_registry_sha256') == sha(Path(source) / REGISTRY) and
            source_manifest.get('status') == 'passed', 'source_export_binding')
    boundary_ok(source_report, 'mattersyn', source_manifest['file_count'])
    pinned(review['allowlist'])


def copy_exact(origin, destination, rows):
    destination.mkdir()
    for name, row in sorted(rows_map(rows).items()):
        raw = stable_bytes(Path(origin) / name)
        require(digest(raw) == row['sha256'] and len(raw) == row['bytes'], 'copy_input_drift')
        target = no_link(destination / name)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as f:
            f.write(raw)
    require(rows_map(inventory(destination)) == rows_map(rows), 'copy_output_drift')


def promote(source, candidate, seal_sha, out, review_path, review_sha):
    source, candidate = no_link(source), no_link(candidate)
    seal, manifest = verify_seal(source, candidate, seal_sha)
    review_pin = {'path': str(no_link(review_path)), 'sha256': review_sha}
    review = loads(pinned(review_pin))
    require(review.get('candidate_manifest_sha256') == seal['candidate_manifest']['sha256'] and
            review.get('build_seal_sha256') == seal_sha, 'review_candidate_drift')
    verify_evidence(source, manifest, review)
    out = disjoint_new(out, [source, candidate, review_path, seal['snapshot']['path']])
    out.mkdir()
    # No pipeline or source write. The candidate stays UNAPPROVED and intact.
    copy_exact(candidate / 'project/recipe-atlas/dist', out / 'dist', manifest['files'])
    command = [sys.executable, str(source / GATE), '--root', str(out / 'dist'),
               '--policy', str(source / POLICY), '--registry', str(source / REGISTRY),
               '--allowlist', review['allowlist']['path'], '--repo', 'mattersyn-site',
               '--manifest-out', str(out / 'boundary-manifest.json'), '--report-out', str(out / 'boundary-report.json')]
    run = execute(command, out)
    write_new(out / 'fresh-boundary-run.private.json', run)
    require(run['returncode'] == 0, 'fresh_boundary_command_failed')
    report, boundary = read(out / 'boundary-report.json'), read(out / 'boundary-manifest.json')
    boundary_ok(report, 'mattersyn-site', len(manifest['files']))
    require(boundary.get('schema_version') == 'mattersyn-public-release-manifest/1' and
            boundary.get('repo') == 'mattersyn-site' and boundary.get('file_count') == len(manifest['files']) and
            boundary.get('release_id') == manifest['release_id'] and boundary.get('source_commit') == seal['source_commit'] and
            boundary.get('policy_sha256') == sha(source / POLICY) and
            boundary.get('asset_rights_registry_sha256') == sha(source / REGISTRY), 'fresh_boundary_binding')
    require(rows_map([{k: r[k] for k in ('path', 'sha256', 'bytes')} for r in boundary.get('files', [])]) ==
            rows_map(manifest['files']), 'fresh_boundary_inventory')
    require(rows_map(inventory(out / 'dist')) == rows_map(manifest['files']), 'post_boundary_artifact_drift')
    verify_seal(source, candidate, seal_sha)
    pinned(review_pin)
    verify_evidence(source, manifest, review)
    receipt = {'schema': 'mattersyn-one-build-promoted-artifact/1',
               'status': 'FRESH_BOUNDARY_PASSED_PENDING_SITE_CI_AND_ANONYMOUS_VERIFICATION',
               'source_commit': seal['source_commit'], 'release_id': manifest['release_id'],
               'snapshot_sha256': manifest['snapshot_sha256'], 'candidate_seal_sha256': seal_sha,
               'candidate_manifest_sha256': seal['candidate_manifest']['sha256'],
               'review_sha256': review_sha, 'boundary_manifest_sha256': sha(out / 'boundary-manifest.json'),
               'boundary_report_sha256': sha(out / 'boundary-report.json'),
               'build_checks_reused': seal['checks'], 'new_local_builds': 0,
               'files': manifest['files'], 'metadata': manifest['metadata'],
               'published': False, 'publication_credit': 0,
               'scope': 'Exact sealed full-build reuse plus fresh full boundary; no science/browser/CI exemption. Not a deployment receipt.'}
    write_new(out / 'promotion-receipt.private.json', receipt)
    return pin(out / 'promotion-receipt.private.json')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands_parser = parser.add_subparsers(dest='action', required=True)
    b = commands_parser.add_parser('build')
    for flag in ('source', 'snapshot', 'out', 'contract', 'contract-sha'):
        b.add_argument('--' + flag, required=True)
    p = commands_parser.add_parser('promote')
    for flag in ('source', 'candidate', 'seal-sha', 'out', 'review', 'review-sha'):
        p.add_argument('--' + flag, required=True)
    a = parser.parse_args()
    try:
        if a.action == 'build':
            result = build(a.source, a.snapshot, a.out, a.contract, a.contract_sha)
        else:
            result = promote(a.source, a.candidate, a.seal_sha, a.out, a.review, a.review_sha)
        print(json.dumps(result))
    except (Rejected, ValueError, KeyError, OSError, subprocess.CalledProcessError) as e:
        print(json.dumps({'status': 'REJECTED', 'reason': str(e)}), file=sys.stderr)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
