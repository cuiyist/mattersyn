"""Read saved review evidence only; write ETA support beside this script."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import statistics

OUTPUT = Path(__file__).resolve().parent
MONITOR = OUTPUT.parents[2] / "incoming-paper-monitor"
LEDGER = MONITOR / "ledger.json"
ROLLING = MONITOR / "batches/20260920-rolling-pipeline"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def date(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def statistics_for(values):
    return {"count": len(values), "mean": statistics.mean(values),
            "median": statistics.median(values), "minimum": min(values), "maximum": max(values)}


def window(start, end, count, meaning):
    hours = (date(end) - date(start)).total_seconds() / 3600
    return {"start": start, "end": end, "elapsed_hours": hours,
            "event_count": count, "events_per_elapsed_hour": count / hours, "meaning": meaning}


raw = LEDGER.read_bytes()
ledger = json.loads(raw)
batch = next(batch for batch in ledger["batch_history"] if batch["closed_at"].startswith("2026-09-20"))
claims = [claim for claim in batch["papers"] if claim["claimed_at"].startswith("2026-09-20")]
rows = []
for claim in claims:
    group_id = claim["group_id"]
    suffix = group_id.split("10.1021_", 1)[1]
    review = ledger["groups"][group_id]["review"]
    closure = next(event for event in review["history"] if event["status"] == "complete")
    directory = ROLLING / suffix
    if suffix == "ja103805s":
        audit_path = directory / "source-scientific-audit.json"
    else:
        audit_path = directory / "source-independent-audit" / ("independent-audit-v1.json" if suffix == "la8031286" else "independent-audit-v2.json")
    audit = read(audit_path)
    timestamp_key = next(key for key in ("at", "created_at", "created_at_utc") if key in audit)
    audit_at = audit[timestamp_key]
    verification_path = directory / "site-integration-proposal/science-release-anonymous-verification.json"
    verification = read(verification_path)
    rows.append({"group_id": group_id, "source_id": audit.get("source_id", audit.get("paper_id")),
                 "claimed_at": claim["claimed_at"], "closed_at": closure["at"],
                 "source_audit_passed_at": audit_at, "source_audit_status": audit["status"],
                 "source_audit_path": str(audit_path), "source_audit_time_field": timestamp_key,
                 "source_audit_sha256": hashlib.sha256(audit_path.read_bytes()).hexdigest(),
                 "public_verification_at": verification["verified_at"],
                 "public_verification_path": str(verification_path),
                 "public_verification_status": verification["status"],
                 "claim_to_source_audit_elapsed_minutes": (date(audit_at) - date(claim["claimed_at"])).total_seconds() / 60,
                 "claim_to_closure_elapsed_minutes": (date(closure["at"]) - date(claim["claimed_at"])).total_seconds() / 60,
                 "source_scope_note": review["milestones"]["read"].get("note"),
                 "closure_note": closure["note"]})

rows.sort(key=lambda row: row["claimed_at"])
publication_history = []
for path in sorted(ROLLING.glob("*/site-integration-proposal/prior-latest-publication.json")) + [MONITOR / "latest-publication.json"]:
    publication = read(path)
    publication_history.append({"path": str(path), "source_ids": publication.get("new_source_ids"),
                                "dataset_version": publication.get("dataset_version"),
                                "scientific_dataset_published_at": publication.get("scientific_dataset_published_at"),
                                "published_at": publication.get("published_at"),
                                "progress_only_update": publication.get("progress_only_update"),
                                "publication_scope": publication.get("publication_scope")})

closures = sorted(row["closed_at"] for row in rows)
gaps = [(date(end) - date(start)).total_seconds() / 60 for start, end in zip(closures, closures[1:])]
source_passes = sorted(row["source_audit_passed_at"] for row in rows)
carryover = ledger["groups"]["10.1021_jp0219348"]["review"]
carryover_closed = next(event["at"] for event in carryover["history"] if event["status"] == "complete")
report = {
    "schema": "mattersyn.observed-throughput-support/1",
    "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    "ledger_path": str(LEDGER), "ledger_sha256_at_read": hashlib.sha256(raw).hexdigest(),
    "scope": "Saved 20260920 rolling cohort; read-only evidence analysis. No scans, claims, controls or source edits.",
    "claim_evidence_locator": "ledger.batch_history[0].papers[]",
    "closure_evidence_locator": "ledger.groups[group_id].review.history[status=complete]",
    "rows": rows,
    "windows": {
        "new_cohort_claim_to_last_verified_closure": window(rows[0]["claimed_at"], closures[-1], len(rows), "Nine new source scopes admitted and eventually closed in the window; includes overlapping work and pipeline fill/drain."),
        "new_cohort_between_first_and_last_closure": window(closures[0], closures[-1], len(rows) - 1, "Eight additional closures across eight intervals, not nine independent complete-review durations."),
        "new_cohort_claim_to_last_source_audit": window(rows[0]["claimed_at"], source_passes[-1], len(rows), "Nine supplied-source extraction/audit passes only; downstream canonical, illustration, browser and publication gates excluded."),
    },
    "claim_to_closure_minutes": statistics_for([row["claim_to_closure_elapsed_minutes"] for row in rows]),
    "claim_to_source_audit_minutes": statistics_for([row["claim_to_source_audit_elapsed_minutes"] for row in rows]),
    "inter_closure_minutes": statistics_for(gaps),
    "inter_closure_intervals_minutes": gaps,
    "carryover": {"group_id": "10.1021_jp0219348", "claimed_at": batch["papers"][0]["claimed_at"], "closed_at": carryover_closed,
                  "meaning": "Heo closure falls inside the rolling window but substantial source work started the previous day; adding this closure does not make ten new full reviews."},
    "publication_history": publication_history,
    "caveats": [
        "These are elapsed-time observations from one selected, concurrent, nine-scope cohort, not measured agent labor or an independent-paper sample.",
        "One source scope is a supplied main/SI/version review unit; these nine correspond to nine named sources, but this does not establish unique-paper counts for the overall backlog.",
        "Eight of nine scopes include supplied main and matched SI. Sommer has eleven supplied main pages; missing SI remains unlocated/unverified. Other missing declared attachments remain out of scope.",
        "Source-audit timestamps document recorded pass points. Claim-to-pass includes intake, authoring, independent reading, corrections and waits; it is not pure reading time.",
        "Ledger read/extract milestone updated_at values can be overwritten during later integration checkpoints; authoritative source-stage times here come from passed audit artifacts.",
        "Scientific publication times are separated from progress-only releases. Latest generic published_at may refer to metadata/progress, so use scientific_dataset_published_at and exact scientific release verification.",
        "No projection of six-hour/eight-hour days, 24/7 runtime, future screen yield, or thousands of paper completions is a measured throughput fact.",
        "Repeated audit revisions, alias reconciliation, cached source copies, progress publications and multiple records from one source are not additional paper completions."
    ]
}
OUTPUT.mkdir(parents=True, exist_ok=True)
(OUTPUT / "observed-throughput.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
lines = ["# Observed rolling-pipeline throughput", "", "All times are UTC. This is an elapsed-time cohort observation, not agent labor or a promised future capacity.", "",
         "| Source scope | Claimed | Source audit passed | Verified closure | Claim to closure (min) |", "|---|---|---|---|---:|"]
for row in rows:
    lines.append(f"| {row['source_id']} | {row['claimed_at']} | {row['source_audit_passed_at']} | {row['closed_at']} | {row['claim_to_closure_elapsed_minutes']:.2f} |")
lines += ["", *[f"- {key}: {value['event_count']} events / {value['elapsed_hours']:.5f} elapsed hours = {value['events_per_elapsed_hour']:.5f}/h; {value['meaning']}" for key, value in report["windows"].items()], "", *["- " + caveat for caveat in report["caveats"]], "", "Exact evidence paths, fields and source hashes are in observed-throughput.json.", ""]
(OUTPUT / "observed-throughput.md").write_text("\n".join(lines), encoding="utf-8")
print(json.dumps({"output": str(OUTPUT), "windows": report["windows"], "claim_to_source_audit_minutes": report["claim_to_source_audit_minutes"]}, indent=2))
