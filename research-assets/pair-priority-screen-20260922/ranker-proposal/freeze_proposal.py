"""Verify completed local output bytes and freeze this proposal for audit."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE / "final-run-v2"

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    summary = json.loads((RUN / "summary.json").read_text(encoding="utf-8"))
    assert summary["script_sha256"] == digest(HERE / "rank_pairs.py")
    assert summary["fixed_cutoff_scopes_output"] == 9532 and summary["all_scope_ids_exactly_once"]
    assert summary["fixed_cutoff_file_dispositions"] == 13831
    assert summary["nested_held_files_preserved"] == summary["nested_held_files_second_stage_screened"] == 3
    assert summary["frozen_manual_format_or_text_copies_retained"] == 238
    assert summary["verified_pair_count"] == summary["automatic_exclusions"] == summary["task_ready_count"] == 0
    for rel, binding in summary["output_bindings"].items():
        assert digest(RUN / rel) == binding["sha256"], rel
        assert (RUN / rel).stat().st_size == binding["bytes"], rel
    paths = [HERE / n for n in ("rank_pairs.py", "test_rank_pairs.py", "freeze_proposal.py", "author-regression-checks.json", "generation-context.json", "README.md")]
    paths += sorted(p for p in RUN.rglob("*") if p.is_file())
    freeze = {"schema": "mattersyn-offline-ranker-author-freeze/1", "status": "author_frozen_for_independent_audit_not_activated",
              "run": "final-run-v2", "script_sha256": summary["script_sha256"],
              "coverage": {"scopes": 9532, "document_copies": 13831, "nested_held_files": 3, "original_manual_cases_retained": 238},
              "no_scientific_pair_approval": True, "no_auto_exclusion": True,
              "no_shared_ledger_or_site_writes": True,
              "private_artifact_rule": "Every source-cues file remains under private/. Publish only independently reviewed compact counts/provenance, never private excerpts or original documents.",
              "excluded_diagnostics": ["dry-run", "dry-run-v2", "dry-run-final", "final-run", "diagnostics"],
              "known_limits": ["Historical source/cache binding is not revalidation of current source bytes.", "Atomic candidate B is origin/target agnostic when text does not bind molecular precursor versus nanomaterial; existing source benchmarks remain the authority for those roles.", "Mixed refined/fixed tables retain both qualifiers; no component coordinate transfer is performed.", "Candidate count is not a count of verified pairs or task-ready datasets."],
              "files": [{"path": p.relative_to(HERE).as_posix(), "sha256": digest(p), "bytes": p.stat().st_size, "private": "private" in p.parts} for p in paths]}
    path = HERE / "author-freeze.json"
    path.write_text(json.dumps(freeze, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"freeze_path": str(path), "sha256": digest(path), "files": len(paths)}))

if __name__ == "__main__":
    main()
