#!/usr/bin/env python3
"""One CI entry point for synthetic simple-pipeline engineering regressions.

Runs no extraction, source-paper reading, model server or publication.
PDF rendering uses synthetic fixtures only.
The project release guard must be available beside this installed package.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def result(returncode, stderr):
    count = re.search(r'^Ran (\d+) tests? in ', stderr, flags=re.M)
    tests = int(count[1]) if count else 0
    skipped = bool(re.search(r'\bskipped=', stderr))
    return {'status': 'passed' if returncode == 0 and tests > 0 and not skipped else 'failed',
            'tests_run': tests, 'skipped_tests_present': skipped, 'test_process_returncode': returncode,
            'scope': 'synthetic engineering regressions only; no extraction accuracy or release credit'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', help='optional metadata-only result JSON')
    args = parser.parse_args()
    process = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(HERE),
                              '-p', 'test_*.py', '-v'], cwd=HERE, text=True, encoding='utf-8',
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    sys.stdout.write(process.stdout)
    sys.stderr.write(process.stderr)
    report = result(process.returncode, process.stderr)
    if args.report:
        Path(args.report).write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(report, indent=2))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
