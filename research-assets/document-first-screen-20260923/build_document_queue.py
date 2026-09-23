"""Build a document-first scheduling snapshot from frozen metadata, not sources.

No PDF access, text extraction, source rehash, shared-ledger edit or publication.
Run using the existing Python runtime. All outputs stay beside this utility.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import re

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent
INPUTS = {
    "documents": ASSETS / "incoming-paper-monitor/deadline-20260920/workflow-20260920T0412/screen/documents.jsonl",
    "ranked_scopes": ASSETS / "pair-priority-screen-20260922/ranker-proposal/final-run-v2/ranked-scopes.jsonl",
    "cutoff_inventory": ASSETS / "incoming-paper-monitor/deadline-20260920/cutoff-20260920T033439542641Z/file-inventory.json",
    "known_exceptions": ASSETS / "one-month-20260922/duplicate-audit/pair-source-validity-overlay.json",
    "mixed_partial_01": ASSETS / "methods-triage-20260923/mixed-batch-01/notes.json",
    "mixed_partial_02": ASSETS / "methods-triage-20260923/mixed-batch-02/notes.json",
}


def load(path):
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    return json.loads(path.read_text(encoding="utf-8"))


def relative(path):
    return "research-assets/" + path.relative_to(ASSETS).as_posix()


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    inputs = {name: load(path) for name, path in INPUTS.items()}
    docs = inputs["documents"]
    ranks = inputs["ranked_scopes"]
    inventory = inputs["cutoff_inventory"]
    by_key = {row["file_key"]: row for row in docs}
    assert len(by_key) == len(docs), "Duplicate original-file keys"
    key_ranks = defaultdict(list)
    for rank in ranks:
        for key in rank["file_keys"]:
            key_ranks[key].append(rank)
    fixed_keys = set(key_ranks)
    inventory_keys = {row["ledger_file_key"] for row in inventory["entries"] if row.get("monitor_eligible")}
    assert fixed_keys == inventory_keys, "Accepted fixed membership differs from cutoff inventory"
    assert fixed_keys <= by_key.keys(), "Missing fixed copy in extraction snapshot"
    exceptions = {(x["file_key"], x["source_sha256"]): x for x in inputs["known_exceptions"]["files"]}
    partial = defaultdict(list)
    all_hashes = {row["sha256"] for row in docs}
    for name in ("mixed_partial_01", "mixed_partial_02"):
        for note in inputs[name]:
            for prefix, pages in note.get("read_pages", {}).items():
                matched = [digest for digest in all_hashes if digest.startswith(prefix)]
                assert len(matched) == 1, "Ambiguous partial-receipt hash prefix"
                partial[matched[0]].append({
                    "receipt": relative(INPUTS[name]), "case": note["case"],
                    "pages_reported_read": pages,
                    "scope": "partial_page_coverage_only_not_whole_document_screening",
                })
    peer_hashes = [digest for digest in all_hashes if digest.startswith("16aa8f655474")]
    assert len(peer_hashes) == 1
    peer_hash = peer_hashes[0]
    buckets = defaultdict(list)
    for key in sorted(fixed_keys):
        row = by_key[key]
        digest = row.get("sha256")
        assert row.get("hash_computed") and re.fullmatch(r"[0-9a-f]{64}", digest or "")
        exception = exceptions.get((key, digest))
        role = row.get("role_candidate")
        checked_role = None
        if exception and exception.get("role_validity") == "not_main_article":
            checked_role = "supporting_information"
        elif exception and exception.get("role_validity") == "not_article":
            checked_role = "nonarticle_promotion"
        if digest == peer_hash:
            checked_role = "peer_review_file"
        source_copy = {
            "file_key": key, "source_collection": row["source_collection"],
            "original_filename": row["original_filename"],
            "source_relative_path": key.removeprefix("legacy::"),
            "historical_group_hint": row.get("group_id"),
            "origin_group_hint": row.get("origin_group_id"),
            "source_generation_at_historical_screen": row.get("source_generation"),
            "historical_signature": row.get("observed_signature"),
            "role_candidate": role, "role_candidates": row.get("role_candidates", []),
            "role_ambiguous": row.get("role_ambiguous", False),
            "role_provenance": "historical_screen_metadata_not_verified_publication_identity",
            "checked_role_from_existing_receipt": checked_role,
            "doi_candidates_not_verified": row.get("doi_candidates", []),
            "known_file_exception": ({k: exception.get(k) for k in (
                "role_validity", "source_validity_category", "source_validity_action",
                "block_positive_pair_admission_from_this_file", "must_not_mark_no_recipe_or_complete"
            )} if exception else None),
            "historical_group_priority_hints": [{
                "group_id": r["group_id"], "rank": r["candidate_inspection_rank"],
                "band": r["priority_band"], "group_source_hold_not_inherited": r["source_hold"],
            } for r in key_ranks[key]],
            "historical_format_status": {
                "detected_format": row.get("detected_format"),
                "extraction_status": row.get("extraction_status"),
                "screen_status": row.get("status"),
                "manual_flags": row.get("manual_flags", []),
                "empty_text_pages": row.get("empty_text_pages", []),
                "failed_text_pages": row.get("failed_text_pages", []),
            },
            "same_document_machine_cues_not_verified": row.get("features", {}).get("counts", {}),
        }
        buckets[digest].append(source_copy)
    queue = []
    for digest, copies in buckets.items():
        roles = {copy["checked_role_from_existing_receipt"] for copy in copies}
        if "nonarticle_promotion" in roles:
            state = "parked_known_nonarticle_content"
        elif "peer_review_file" in roles:
            state = "queued_peer_review_document_independent_relevance_check"
        elif all(copy["historical_format_status"]["screen_status"] == "manual_format_or_text_review_required" for copy in copies):
            state = "parked_document_format_or_text_review"
        else:
            state = "queued_independent_document_screen"
        queue.append({
            "document_id": "document-sha256-" + digest,
            "source_sha256_at_historical_screen": digest,
            "hash_verification": "historical_bytes_verified_not_rehashed_for_this_snapshot",
            "current_source_hash_check_required_before_read_or_cache_reuse": True,
            "deduplication": "same_recorded_verified_sha256_only_retain_all_original_copies",
            "scheduling_state": state,
            "companion_required_for_screening": False,
            "paired_main_si_required_for_screening": False,
            "publication_identity": "not_established_by_document_id_or_group_hint",
            "screening_coverage": "document_level_completion_not_imported_or_inferred_from_group_status",
            "partial_coverage_receipts": partial.get(digest, []),
            "other_existing_review_receipts": "reconcile_by_current_hash_and_exact_coverage_at_dispatch_do_not_reset_existing_reviews",
            "screening_plan": ["Check this document's own Methods or preparation content", "If usable preparation is present, inspect this document's structural evidence", "Record references to other sources as unresolved links; do not wait for a companion document"],
            "initial_outcome": "unassessed_by_this_snapshot",
            "automatically_excluded_for_no_synthesis": False,
            "full_review_state": "not_imported_no_existing_review_reset",
            "training_approved_by_this_snapshot": False,
            "best_historical_group_rank_for_order_only": min(r["rank"] for c in copies for r in c["historical_group_priority_hints"]),
            "source_copies": copies,
        })
    queue.sort(key=lambda row: (row["scheduling_state"].startswith("parked"), row["best_historical_group_rank_for_order_only"], row["document_id"]))
    for number, row in enumerate(queue, 1):
        row["document_queue_order"] = number
    nested = [{
        "source_collection": x["source_id"], "source_relative_path": x["relative_path"],
        "document_id": "unhashed-copy-" + sha256((x["source_id"] + "::" + x["relative_path"]).encode()).hexdigest(),
        "historical_signature": {"bytes": x["size_bytes"], "mtime_ns": x["mtime_ns"]},
        "role_candidate": x.get("filename_role_candidate"),
        "group_hint_not_verified": x.get("filename_group_candidate_not_verified"),
        "sha256": x.get("last_known_sha256_not_recomputed"),
        "status": "preserved_nested_document_candidate_outside_accepted_top_level_scope_identity_unresolved",
    } for x in inventory["entries"] if x.get("disposition", "").startswith("nested_document")]
    keys_out = [copy["file_key"] for row in queue for copy in row["source_copies"]]
    assert len(keys_out) == len(set(keys_out)) == len(fixed_keys)
    assert set(keys_out) == fixed_keys
    assert len({row["document_id"] for row in queue}) == len(queue)
    assert all(not row["paired_main_si_required_for_screening"] for row in queue)
    output = HERE / "document-screening-queue.jsonl"
    output.write_text("".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in queue), encoding="utf-8")
    dump(HERE / "nested-document-inventory.json", nested)
    summary = {
        "schema": "mattersyn-document-first-screen-snapshot/1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "fixed_cutoff_at": inventory["cutoff_at"],
        "status": "scheduling_snapshot_only_no_new_source_reading_or_completion_claims",
        "input_bindings": {name: {"path": relative(path), "sha256": sha256(path.read_bytes()).hexdigest()} for name, path in INPUTS.items()},
        "counts": {
            "fixed_original_copies_preserved": len(keys_out),
            "distinct_historically_hashed_document_contents": len(queue),
            "identical_content_additional_copies_retained": len(keys_out) - len(queue),
            "nested_candidates_preserved_separately": len(nested),
            "later_snapshot_copies_outside_fixed_membership": len(docs) - len(keys_out),
            "copies_by_role_candidate": dict(Counter(copy["role_candidate"] for row in queue for copy in row["source_copies"])),
            "unique_contents_by_scheduling_state": dict(Counter(row["scheduling_state"] for row in queue)),
            "documents_with_partial_mixed_batch_receipt": sum(bool(row["partial_coverage_receipts"]) for row in queue),
            "historical_cache_extraction_status_by_fixed_copy": dict(Counter(by_key[key].get("extraction_status") for key in fixed_keys)),
            "historical_cache_source_by_fixed_copy": dict(Counter(by_key[key].get("cache_source", "unrecorded") for key in fixed_keys)),
            "distinct_contents_with_some_extracted_text_cache": sum(any(by_key[c["file_key"]].get("text_characters_screened", 0) > 0 for c in row["source_copies"]) for row in queue),
            "source_pdfs_read_this_pass": 0, "sources_rehashed_this_pass": 0,
            "new_document_screen_completions": 0, "new_no_synthesis_exclusions": 0,
        },
        "checks": {"fixed_copy_membership_conserved": True, "document_ids_unique": True, "no_pairing_enqueue_gate": True, "no_group_completion_inherited": True},
        "queue_sha256": sha256(output.read_bytes()).hexdigest(),
        "limitations": [
            "Hash grouping uses previously verified content, not a fresh source-byte comparison. Rehash a selected source copy before reading or reusing its cache; changed content needs a new document ID.",
            "Historical group ranks are scheduling hints only. They do not establish synthesis or structure within an individual document.",
            "A supporting document is an independent screening unit, not a separate scientific publication or automatic training example.",
            "Partial mixed-batch page receipts are referenced; other completed review and audit receipts must be reconciled by exact document hash and covered scope at dispatch. No historical review is reset.",
            "Known format and nonarticle issues remain explicit. Missing companions and paper-group source holds do not block independently readable documents.",
            "Known wrong article identity is retained on its source copy; establish the actual document identity before attributing any useful evidence.",
            "Three nested inventory candidates are preserved outside the 13,831-copy accepted top-level scope; their identity/content has not been read or hashed here.",
            "No negative synthesis decisions, publication approvals, scientific records or training pairs are created by this utility.",
        ],
    }
    dump(HERE / "summary.json", summary)
    print(json.dumps(summary["counts"], indent=2))


if __name__ == "__main__":
    main()
