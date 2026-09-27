"""Resolve a prepared content-bound source allowlist to clean HEAD for export.

The output is private build-time control metadata. Never commit it. The unchanged
boundary exporter receives its existing schema with the actual release commit.
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess

from check_project_manifest import check


def bind(root, output):
    root, output = Path(root).resolve(strict=True), Path(output).resolve()
    if output.is_relative_to(root) or output.exists():
        raise ValueError('Runtime allowlist must be a new external file')
    check(root, pre_push=True)
    path = root / 'publication/project-allowlist.json'
    data = json.loads(path.read_bytes())
    original = data['source_commit']
    head = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    data['source_commit'] = head
    data['source_commit_role'] = 'verified_runtime_release_commit'
    data['preparation_base_commit'] = original
    data['committed_allowlist_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    return {'source_commit': head, 'prepared_from': original, 'boundary_gate_passed': False,
            'runtime_allowlist_sha256': hashlib.sha256(output.read_bytes()).hexdigest()}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path('.'))
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(bind(a.root, a.output)))


if __name__ == '__main__':
    main()
