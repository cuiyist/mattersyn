"""Create an isolated public tree from an exact, reviewed allowlist."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from public_release_guard import BoundaryError, export_public_release, load_config


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, help="read-only source tree")
    parser.add_argument("--destination", required=True, help="must be a new directory disjoint from source")
    parser.add_argument("--allowlist", required=True)
    parser.add_argument("--registry", required=True)
    parser.add_argument("--policy", required=True)
    parser.add_argument("--repo", required=True, choices=["mattersyn", "mattersyn-site"])
    parser.add_argument("--manifest-out", required=True, help="receipt path outside destination")
    parser.add_argument("--report-out", required=True, help="diagnostic path outside destination")
    args = parser.parse_args()
    try:
        config = load_config(args.policy, args.registry)
        config["policy_sha256"] = hashlib.sha256(Path(args.policy).read_bytes()).hexdigest()
        manifest, report = export_public_release(
            args.source_root, args.destination, args.allowlist, config, args.repo,
            args.manifest_out, args.report_out,
        )
        print(json.dumps({
            "status": report["status"], "checked_files": report["checked_files"],
            "passed_files": report["passed_files"], "failure_count": report["failure_count"],
            "manifest_sha256": hashlib.sha256(Path(args.manifest_out).read_bytes()).hexdigest(),
            "report_sha256": hashlib.sha256(Path(args.report_out).read_bytes()).hexdigest(),
        }, indent=2))
        return 0 if report["status"] == "passed" else 1
    except BoundaryError as exc:
        print(json.dumps({"status": "failed", "reason_code": str(exc)}), file=sys.stderr)
        return 2
    except OSError:
        print(json.dumps({"status": "failed", "reason_code": "filesystem_operation_failed"}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
