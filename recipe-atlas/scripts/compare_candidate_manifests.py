"""Compare every artifact byte binding from two unapproved, frozen-input builds."""
import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key: ' + key)
        result[key] = value
    return result


def validate(manifest):
    if not isinstance(manifest, dict):
        raise ValueError('Candidate manifest must be an object')
    if manifest.get('schema') != 'mattersyn-unapproved-build-candidate/1':
        raise ValueError('Expected an unapproved build candidate')
    if manifest.get('status') != 'UNAPPROVED' or any(
        manifest.get(key) is not False
        for key in ('release_eligible', 'boundary_gate_passed', 'published')
    ):
        raise ValueError('Comparison must not approve or publish a candidate')
    if not re.fullmatch(r'[0-9a-f]{40}', manifest.get('source_commit', '')):
        raise ValueError('Missing exact source commit')
    if not re.fullmatch(r'[0-9a-f]{64}', manifest.get('snapshot_sha256', '')):
        raise ValueError('Missing exact frozen snapshot hash')
    if not isinstance(manifest.get('release_id'), str) or not manifest['release_id']:
        raise ValueError('Missing release identifier')
    if not isinstance(manifest.get('metadata'), dict):
        raise ValueError('Missing release metadata bindings')
    rows = manifest.get('files')
    if not isinstance(rows, list) or not rows:
        raise ValueError('Empty or invalid artifact inventory')
    files = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Invalid artifact row')
        path = row.get('path')
        if not isinstance(path, str) or not path or '\\' in path or ':' in path:
            raise ValueError('Invalid relative artifact path')
        parts = path.split('/')
        if PurePosixPath(path).is_absolute() or any(p in ('', '.', '..') for p in parts):
            raise ValueError('Artifact path leaves its root')
        if path in files:
            raise ValueError('Duplicate artifact path: ' + path)
        if not re.fullmatch(r'[0-9a-f]{64}', row.get('sha256', '')):
            raise ValueError('Invalid artifact SHA-256: ' + path)
        if type(row.get('bytes')) is not int or row['bytes'] < 0:
            raise ValueError('Invalid artifact size: ' + path)
        files[path] = row
    return files


def compare(left, right):
    left_files, right_files = validate(left), validate(right)
    left_bindings = {k: v for k, v in left.items() if k != 'files'}
    right_bindings = {k: v for k, v in right.items() if k != 'files'}
    binding_differences = sorted(
        k for k in set(left_bindings) | set(right_bindings)
        if k not in left_bindings or k not in right_bindings or left_bindings[k] != right_bindings[k]
    )
    left_only = sorted(set(left_files) - set(right_files))
    right_only = sorted(set(right_files) - set(left_files))
    changed = sorted(k for k in set(left_files) & set(right_files) if left_files[k] != right_files[k])
    return {
        'schema': 'mattersyn-cross-platform-candidate-comparison/1',
        'passed': not (binding_differences or left_only or right_only or changed),
        'source_commit': left['source_commit'],
        'snapshot_sha256': left['snapshot_sha256'],
        'left_file_count': len(left_files),
        'right_file_count': len(right_files),
        'binding_differences': binding_differences,
        'left_only': left_only,
        'right_only': right_only,
        'changed_files': changed,
        'excluded_artifact_paths': [],
        'release_eligible': False,
        'scope': 'Exact artifact membership, size and SHA-256 plus all source/snapshot metadata. No normalization, ignored files or publication approval.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--left', type=Path, required=True)
    parser.add_argument('--right', type=Path, required=True)
    parser.add_argument('--report-out', type=Path, required=True)
    args = parser.parse_args()
    left_raw, right_raw = args.left.read_bytes(), args.right.read_bytes()
    result = compare(json.loads(left_raw, object_pairs_hook=unique_object),
                     json.loads(right_raw, object_pairs_hook=unique_object))
    result.update(left_manifest_sha256=hashlib.sha256(left_raw).hexdigest(),
                  right_manifest_sha256=hashlib.sha256(right_raw).hexdigest())
    with args.report_out.open('x', encoding='utf-8', newline='\n') as output:
        json.dump(result, output, indent=2)
        output.write('\n')
    print(json.dumps({k: result[k] for k in ('passed', 'left_file_count', 'right_file_count', 'binding_differences')}))
    raise SystemExit(0 if result['passed'] else 1)


if __name__ == '__main__':
    main()
