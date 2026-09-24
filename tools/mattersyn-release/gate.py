"""Validate a prepared MatterSyn public stage and emit external receipts.

Example:
  python gate.py --root SITE_STAGE --allowlist release-allowlist.json \
    --registry asset-rights-registry.json --policy history-policy.json \
    --repo mattersyn-site --manifest-out ../release-manifest.json \
    --report-out ../boundary-report.json

Receipts must live outside `--root`; they are not website assets. This command
does not copy, delete, commit, push, or deploy any file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from public_release_guard import BoundaryError, _is_within, _resolved_future_path, load_config, validate_stage


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="prepared, isolated public stage")
    parser.add_argument("--allowlist", required=True, help="exact path/hash manifest for staged files")
    parser.add_argument("--registry", required=True, help="figure rights registry from the independent inventory")
    parser.add_argument("--policy", required=True, help="reviewed path/class rules")
    parser.add_argument("--repo", required=True, choices=["mattersyn", "mattersyn-site"])
    parser.add_argument("--manifest-out", required=True, help="release manifest output outside --root")
    parser.add_argument("--report-out", required=True, help="diagnostic report output outside --root")
    args = parser.parse_args()
    try:
        config = load_config(args.policy, args.registry)
        policy_raw = Path(args.policy).read_bytes()
        config["policy_sha256"] = hashlib.sha256(policy_raw).hexdigest()
        root = Path(args.root).resolve(strict=True)
        outputs = [_resolved_future_path(args.manifest_out), _resolved_future_path(args.report_out)]
        for out in outputs:
            if _is_within(out, root):
                raise BoundaryError("receipt_must_be_outside_stage")
            if out.exists():
                raise BoundaryError("receipt_must_not_overwrite_existing_file")
        if outputs[0] == outputs[1]:
            raise BoundaryError("receipt_paths_must_be_distinct")
        manifest, report = validate_stage(root, args.allowlist, config, args.repo)
        outputs[0].parent.mkdir(parents=True, exist_ok=True)
        outputs[1].parent.mkdir(parents=True, exist_ok=True)
        with outputs[0].open("x", encoding="utf-8") as manifest_file:
            manifest_file.write(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        with outputs[1].open("x", encoding="utf-8") as report_file:
            report_file.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({
            "status": report["status"], "checked_files": report["checked_files"],
            "passed_files": report["passed_files"], "failure_count": report["failure_count"],
            "manifest_sha256": hashlib.sha256(outputs[0].read_bytes()).hexdigest(),
            "report_sha256": hashlib.sha256(outputs[1].read_bytes()).hexdigest(),
            "report": str(outputs[1]),
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
