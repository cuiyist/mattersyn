"""Prepare exact source controls in one transaction; never commit or publish.

Stage the reviewed payload first. Changed payloads need exact review receipts;
the unchanged rows retain their previous approvals. Derived control files are
generated, boundary scanned, and staged together. A content binding removes the
otherwise circular dependence on the not-yet-created commit ID.
"""
from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile

MANIFEST = 'publication/project-allowlist.json'
BLUEPRINT = 'publication/build-inputs.json'
CONTROLS = {MANIFEST, BLUEPRINT}
BINDING_SCHEMA = 'mattersyn-source-payload-binding/1'


class PreparationError(ValueError):
    pass


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def git(root, *args, env=None, input=None):
    return subprocess.check_output(['git', '-C', str(root), *args], env=env, input=input, stderr=subprocess.PIPE)


def relative(name):
    if not isinstance(name, str) or not name or '\\' in name or ':' in name or '\x00' in name:
        raise PreparationError('Noncanonical source path')
    if PurePosixPath(name).is_absolute() or any(p in ('', '.', '..') for p in name.split('/')):
        raise PreparationError('Noncanonical source path')
    return name


def member(root, name):
    name = relative(name)
    path = root / name
    for parent in (path, *path.parents):
        if parent == root:
            break
        if parent.is_symlink():
            raise PreparationError('Symlink source path is not allowed: ' + name)
    if not path.resolve().is_relative_to(root):
        raise PreparationError('Source path escapes root')
    return path


def index_files(root):
    result = {}
    seen = set()
    for item in git(root, 'ls-files', '--stage', '-z').split(b'\0'):
        if not item:
            continue
        meta, raw_name = item.split(b'\t', 1)
        mode, oid, stage = meta.decode().split()
        name = relative(raw_name.decode())
        if stage != '0' or mode not in {'100644', '100755'}:
            raise PreparationError('Unmerged, symlink or submodule index entry: ' + name)
        if name.casefold() in seen:
            raise PreparationError('Case-colliding source paths')
        seen.add(name.casefold())
        result[name] = {'mode': mode, 'oid': oid}
    return result


def payload_binding(rows):
    identities = sorted(({'path': r['path'], 'sha256': r['sha256'], 'bytes': r['bytes'],
                          'git_mode': r.get('git_mode', '100644')} for r in rows), key=lambda r: r['path'])
    return {'schema': BINDING_SCHEMA, 'sha256': sha(canonical(identities)),
            'file_count': len(identities), 'excludes': [MANIFEST]}


def load_module(path, name='release_guard'):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def review_map(receipt, head):
    if receipt.get('schema') != 'mattersyn-reviewed-source-changes/1' or receipt.get('base_commit') != head:
        raise PreparationError('Review receipt schema or base commit mismatch')
    rows = {}
    for row in receipt.get('files', []):
        name = relative(row.get('path'))
        if name in rows or name in CONTROLS:
            raise PreparationError('Duplicate review or generated-control approval')
        if row.get('decision') not in {'allow', 'delete'} or row.get('review_status') != 'approved':
            raise PreparationError('Changed file is not approved: ' + name)
        if not row.get('reviewer') or not row.get('reviewed_at'):
            raise PreparationError('Missing reviewer identity or timestamp: ' + name)
        rows[name] = row
    return rows


def prepare(root, receipt, release_id, guard, config, now=None):
    """Return two control byte strings and a plan; make no changes."""
    root = Path(root).resolve(strict=True)
    if not isinstance(release_id, str) or not release_id.strip():
        raise PreparationError('Release identity is required')
    if Path(git(root, 'rev-parse', '--show-toplevel').decode().strip()).resolve() != root:
        raise PreparationError('Root must be a Git repository root')
    if git(root, 'diff', '--name-only', '-z'):
        raise PreparationError('Stage all reviewed changes first; unstaged tracked edits are not admitted')
    if git(root, 'ls-files', '--others', '--exclude-standard', '-z'):
        raise PreparationError('Untracked files are not implicitly admitted; stage reviewed files or keep drafts outside the checkout')
    head = git(root, 'rev-parse', 'HEAD').decode().strip()
    rows = review_map(receipt, head)
    staged = index_files(root)
    raw = {}
    for name, info in staged.items():
        path = member(root, name)
        content = path.read_bytes()
        # --no-filters catches CRLF and clean-filter changes as well as a raced edit.
        # Compute the exact Git blob identity in-process, avoiding one Git
        # process per file. No clean filters or newline transformations apply.
        algorithm = 'sha1' if len(info['oid']) == 40 else 'sha256'
        actual = hashlib.new(algorithm, b'blob ' + str(len(content)).encode() + b'\0' + content).hexdigest()
        if actual != info['oid']:
            raise PreparationError('Working file differs from exact staged bytes: ' + name)
        raw[name] = content
    previous = json.loads(git(root, 'show', 'HEAD:' + MANIFEST))
    if previous.get('schema_version') != 'mattersyn-public-release-allowlist/1' or previous.get('repo') != 'mattersyn':
        raise PreparationError('Invalid existing source allowlist')
    old = {r['path']: r for r in previous['files']}
    if len(old) != len(previous['files']):
        raise PreparationError('Duplicate existing allowlist rows')
    at = now or datetime.datetime.now(datetime.timezone.utc).isoformat()
    inputs = json.loads(raw[BLUEPRINT])
    if inputs.get('schema') != 'mattersyn-build-input-blueprint/1':
        raise PreparationError('Invalid build blueprint schema')
    old_inputs = json.loads(git(root, 'show', 'HEAD:' + BLUEPRINT))
    generated_keys = {'input_files', 'release_id', 'updated_at'}
    metadata = {k: v for k, v in inputs.items() if k not in generated_keys}
    old_metadata = {k: v for k, v in old_inputs.items() if k not in generated_keys}
    metadata_review = receipt.get('blueprint_metadata_review')
    if metadata != old_metadata:
        if not isinstance(metadata_review, dict) or any(metadata_review.get(k) != v for k, v in {
                'before_sha256': sha(canonical(old_metadata)), 'sha256': sha(canonical(metadata)),
                'decision': 'allow', 'review_status': 'approved'}.items()):
            raise PreparationError('Changed blueprint authorization metadata requires exact separate review')
        if not metadata_review.get('reviewer') or not metadata_review.get('reviewed_at'):
            raise PreparationError('Blueprint metadata reviewer identity is missing')
    elif metadata_review is not None:
        raise PreparationError('Unused blueprint metadata review')
    # Counts and inventory remain authored inputs until their dedicated generator
    # is adopted; this tool never fabricates new dataset totals.
    inputs.update(release_id=release_id, updated_at=at)
    inputs['input_files'] = [{'path': n, 'sha256': sha(b), 'bytes': len(b)}
                            for n, b in sorted(raw.items()) if n not in CONTROLS]
    raw[BLUEPRINT] = encoded(inputs)
    used = set()
    approved = []
    for name, content in sorted(raw.items()):
        if name == MANIFEST:
            continue
        decision = guard.history_project('mattersyn', name, content, config)
        if decision.get('action') != 'allow' or decision.get('content') != content:
            raise PreparationError('Boundary rejected source bytes: ' + name)
        identity = {'path': name, 'sha256': sha(content), 'bytes': len(content), 'git_mode': staged[name]['mode']}
        former = old.get(name)
        same = former and all(former.get(k) == identity[k] for k in ('sha256', 'bytes'))
        if same and former.get('git_mode', '100644') != identity['git_mode']:
            same = False
        if name == BLUEPRINT:
            row = {**identity, 'decision': 'allow', 'review_status': 'approved',
                   'reviewer': 'deterministic-source-control-generator', 'reviewed_at': at,
                   'content_class': decision['content_class'], 'source_refs': [],
                   'approval_scope': 'Generated exact input identities only; no scientific approval'}
            if metadata_review:
                row['metadata_review'] = {k: metadata_review[k] for k in (
                    'before_sha256', 'sha256', 'reviewer', 'reviewed_at')}
        elif same:
            row = {**copy.deepcopy(former), **identity}
        else:
            review = rows.get(name)
            if not review or review.get('decision') != 'allow':
                raise PreparationError('Missing exact changed-file review: ' + name)
            expected_before = former.get('sha256') if former else None
            if review.get('before_sha256') != expected_before:
                raise PreparationError('Stale review base identity: ' + name)
            if any(review.get(k) != identity[k] for k in ('sha256', 'bytes')):
                raise PreparationError('Review does not bind current staged bytes: ' + name)
            if review.get('git_mode', '100644') != identity['git_mode']:
                raise PreparationError('Review does not bind staged mode: ' + name)
            row = {**identity, **{k: review[k] for k in ('decision', 'review_status', 'reviewer', 'reviewed_at')},
                   'content_class': decision['content_class'], 'source_refs': review.get('source_refs', [])}
            used.add(name)
        _, error = guard.validate_allowlist_entry(name, content, row, config, 'mattersyn')
        if error:
            raise PreparationError('Exact release entry rejected for ' + name + ': ' + error)
        approved.append(row)
    for name, former in old.items():
        if name in raw or name in CONTROLS:
            continue
        review = rows.get(name)
        if not review or review.get('decision') != 'delete' or review.get('before_sha256') != former['sha256']:
            raise PreparationError('Missing exact deletion review: ' + name)
        used.add(name)
    if set(rows) != used:
        raise PreparationError('Review contains unused or mismatched paths')
    if config.get('policy_sha256') != sha(raw['publication/public-release-policy.json']) or config.get('asset_rights_registry_sha256') != sha(raw['publication/asset-rights-registry.json']):
        raise PreparationError('Guard configuration does not match staged policy and registry')
    manifest = {'schema_version': 'mattersyn-public-release-allowlist/1', 'release_id': release_id,
                'repo': 'mattersyn', 'source_commit': head, 'source_commit_role': 'preparation_base',
                'source_payload_binding': payload_binding(approved),
                'policy_sha256': config['policy_sha256'],
                'asset_rights_registry_sha256': config['asset_rights_registry_sha256'],
                'review_scope': 'Exact staged payload identities. Scientific review remains separately bound to paper content.',
                'files': approved}
    controls = {BLUEPRINT: raw[BLUEPRINT], MANIFEST: encoded(manifest)}
    plan = {'schema': 'mattersyn-source-preparation/1', 'base_commit': head,
            'index_tree_before': git(root, 'write-tree').decode().strip(),
            'source_payload_binding': manifest['source_payload_binding'],
            'changed_reviewed_paths': sorted(used), 'controls': [{
                'path': n, 'sha256': sha(b), 'bytes': len(b)} for n, b in sorted(controls.items())],
            'commit_ready': False, 'published': False,
            'scope': 'Control preparation only. Scientific, build, browser and publication checks remain required.'}
    return controls, plan


def apply_transaction(root, controls, plan):
    """Stage only generated controls, with index locking and rollback on failure."""
    root = Path(root).resolve(strict=True)
    identities = [{'path': n, 'sha256': sha(b), 'bytes': len(b)} for n, b in sorted(controls.items())]
    if set(controls) != CONTROLS or identities != plan.get('controls'):
        raise PreparationError('Prepared control identities changed')
    index = Path(git(root, 'rev-parse', '--git-path', 'index').decode().strip())
    if not index.is_absolute():
        index = root / index
    lock = index.with_name(index.name + '.lock')
    original = {n: member(root, n).read_bytes() for n in CONTROLS}
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    alternate = None
    moved = []
    temporary_controls = []
    owns_lock = True
    try:
        os.close(fd)
        handle, alternate = tempfile.mkstemp(prefix='mattersyn-index-', dir=index.parent)
        os.close(handle)
        shutil.copyfile(index, alternate)
        env = {**os.environ, 'GIT_INDEX_FILE': str(alternate)}
        if git(root, 'rev-parse', 'HEAD').decode().strip() != plan['base_commit'] or git(root, 'write-tree', env=env).decode().strip() != plan['index_tree_before']:
            raise PreparationError('Git HEAD or index changed during preparation')
        if git(root, 'diff', '--name-only', '-z', env=env):
            raise PreparationError('Working tree changed during preparation')
        modes = index_files(root)
        for name, content in controls.items():
            oid = git(root, 'hash-object', '-w', '--stdin', input=content).decode().strip()
            git(root, 'update-index', '--add', '--cacheinfo', modes[name]['mode'] + ',' + oid + ',' + name, env=env)
        tree_after = git(root, 'write-tree', env=env).decode().strip()
        for name, content in controls.items():
            dest = member(root, name)
            handle, temp = tempfile.mkstemp(prefix='.mattersyn-control-', dir=dest.parent)
            temporary_controls.append(Path(temp))
            with os.fdopen(handle, 'wb') as stream:
                stream.write(content)
            os.replace(temp, dest)
            moved.append(name)
        shutil.copyfile(alternate, lock)
        os.replace(lock, index)
        owns_lock = False
        return {**plan, 'index_tree_after': tree_after, 'commit_ready': True}
    except BaseException:
        for name in moved:
            member(root, name).write_bytes(original[name])
        raise
    finally:
        if alternate and Path(alternate).exists():
            Path(alternate).unlink()
        if owns_lock and lock.exists():
            lock.unlink()
        for temp in temporary_controls:
            if temp.exists():
                temp.unlink()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path('.'))
    p.add_argument('--reviews', type=Path, required=True)
    p.add_argument('--release-id', required=True)
    p.add_argument('--report-out', type=Path, required=True)
    p.add_argument('--apply', action='store_true')
    a = p.parse_args()
    root = a.root.resolve(strict=True)
    output = a.report_out.resolve()
    if output.is_relative_to(root) or output.exists():
        p.error('Report must be a new external file')
    guard = load_module(root / 'tools/mattersyn-release/public_release_guard.py')
    config = guard.load_config(root / 'publication/public-release-policy.json', root / 'publication/asset-rights-registry.json')
    controls, plan = prepare(root, json.loads(a.reviews.read_bytes()), a.release_id, guard, config)
    if a.apply:
        plan = apply_transaction(root, controls, plan)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(encoded(plan))
    print(json.dumps({'commit_ready': plan['commit_ready'], 'files': plan['source_payload_binding']['file_count'], 'published': False}))


if __name__ == '__main__':
    main()
