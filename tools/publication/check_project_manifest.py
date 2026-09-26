"""Read-only closure checks for reviewed source releases; never approve or publish.

Run with --pre-push from the final, clean closure commit before git push.
The full boundary export and build remain separate mandatory release gates.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import re
import subprocess


class ManifestError(RuntimeError):
    pass


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root)


def names(raw):
    return {item.decode('utf-8') for item in raw.split(b'\0') if item}


def fail_paths(message, paths):
    ordered = sorted(paths)
    sample = ', '.join(ordered[:20])
    remainder = f' (+{len(ordered) - 20} more)' if len(ordered) > 20 else ''
    raise ManifestError(f'{message}: {sample}{remainder}')


def member(root, relative):
    if not isinstance(relative, str):
        raise ManifestError('File path must be a repository-relative string')
    parts = PurePosixPath(relative).parts
    if not parts or relative.startswith('/') or '\\' in relative or ':' in relative or '..' in parts or PurePosixPath(relative).as_posix() != relative:
        raise ManifestError('File path must be canonical and repository-relative')
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ManifestError('File path escapes the source repository')
    return path


def verify_rows(root, rows, label):
    seen = set()
    mismatches = set()
    for row in rows:
        relative = row['path']
        path = member(root, relative)
        if relative in seen:
            fail_paths(f'Duplicate {label} paths', {relative})
        seen.add(relative)
        digest = row.get('sha256')
        if not isinstance(digest, str) or not re.fullmatch(r'[a-f0-9]{64}', digest):
            fail_paths(f'Invalid {label} digest', {relative})
        if not path.is_file():
            mismatches.add(relative)
            continue
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != digest or ('bytes' in row and row['bytes'] != len(content)):
            mismatches.add(relative)
    if mismatches:
        fail_paths(f'{label} hash/size mismatch or missing file', mismatches)
    return seen


def check(root, manifest='publication/project-allowlist.json', pre_push=False, blueprint='publication/build-inputs.json'):
    root = root.resolve()
    if Path(git(root, 'rev-parse', '--show-toplevel').decode().strip()).resolve() != root:
        raise ManifestError('Source root must be the repository root')
    data = json.loads(member(root, manifest).read_bytes())
    if data.get('schema_version') != 'mattersyn-public-release-allowlist/1' or data.get('repo') != 'mattersyn':
        raise ManifestError('Incorrect source manifest schema or repository binding')
    tracked = names(git(root, 'ls-files', '-z'))
    listed = {row['path'] for row in data['files']}
    missing = tracked - listed - {manifest}
    extra = listed - tracked
    if missing or extra:
        parts = []
        if missing:
            parts.append('unlisted tracked files: ' + ', '.join(sorted(missing)[:20]) + (f' (+{len(missing)-20} more)' if len(missing)>20 else ''))
        if extra:
            parts.append('listed but untracked files: ' + ', '.join(sorted(extra)[:20]))
        raise ManifestError('Source manifest coverage mismatch; ' + '; '.join(parts))
    if manifest in listed:
        raise ManifestError('Source manifest must exclude itself')
    if len(listed) != len(data['files']):
        raise ManifestError('Duplicate source manifest paths')
    changed = names(git(root, 'diff', '--name-only', '-z', data['source_commit'], 'HEAD')) - {manifest}
    if changed:
        fail_paths('Source changed since its approved manifest commit', changed)
    verify_rows(root, data['files'], 'Source manifest')
    result = {'tracked_files': len(tracked), 'approved_payload_files': len(listed), 'manifest_self_exclusion': manifest, 'status': 'passed'}
    if pre_push:
        if git(root, 'status', '--porcelain', '--untracked-files=all').strip():
            raise ManifestError('Pre-push requires a clean final closure commit; commit reviewed changes and regenerate release metadata before pushing')
        if blueprint not in tracked:
            raise ManifestError('Build blueprint must be tracked')
        inputs = json.loads(member(root, blueprint).read_bytes())
        if inputs.get('schema') != 'mattersyn-build-input-blueprint/1':
            raise ManifestError('Incorrect build blueprint schema')
        input_names = verify_rows(root, inputs['input_files'], 'Build blueprint')
        if input_names - tracked:
            fail_paths('Build blueprint contains untracked files', input_names - tracked)
        required = {path for path in tracked if path.startswith(tuple('recipe-atlas/' + name + '/' for name in ('scripts', 'templates', 'data', 'static', 'tests')))}
        if 'README.md' in tracked:
            required.add('README.md')
        if required - input_names:
            fail_paths('Build blueprint omits build inputs', required - input_names)
        result.update(pre_push=True, blueprint_input_count=len(input_names), gate_scope='Source closure only; boundary export, scientific audit, build and browser checks remain mandatory')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--manifest', default='publication/project-allowlist.json')
    parser.add_argument('--blueprint', default='publication/build-inputs.json')
    parser.add_argument('--pre-push', action='store_true')
    args = parser.parse_args()
    try:
        print(json.dumps(check(args.root, args.manifest, args.pre_push, args.blueprint)))
    except (ManifestError, subprocess.CalledProcessError, KeyError, ValueError) as error:
        parser.exit(1, f'Source release preflight failed: {error}\n')


if __name__ == '__main__':
    main()
