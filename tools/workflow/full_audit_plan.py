"""Private, append-only full-audit cohort ledger; no scientific approval or publication.

This companion supersedes hash-selected quick-audit sampling for NEW full-audit
cohorts. It never edits the historical quick checklist, canonical data, policy or
allowlist. Supplied human/source receipts remain assertions to verify separately.
Use --help for read-only validation/reporting. Ledger writers must be single-owner.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys

SCHEMA = "mattersyn-full-audit-ledger/1"
SHA = re.compile(r"^[0-9a-f]{64}$")
RUNTIME_WORKER_LIMIT = 4
PAIR_STEPS = (4, 8, 12, 16)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def stamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.tzinfo is not None, "timestamps require a timezone")
    return parsed


def identity(value):
    require(isinstance(value, str) and bool(value.strip()), "nonempty identity required")
    return value.strip()


def identities(value):
    require(isinstance(value, list), "agent identities must be a list")
    normalized = [identity(item) for item in value]
    require(len(normalized) == len(set(normalized)), "duplicate agent identity")
    return normalized


def carried_admission(value, admitted_at):
    """Pin genuine work already underway when this cohort ledger was introduced.

    `at` always describes an actual event; late insertions add `recorded_at`.
    No timestamp is inferred from an audit/checklist result. The admission receipt
    must document the package, source freeze, checker run and auditor dispatch.
    """
    require(isinstance(value, dict) and set(value) == {
        "receipt_sha256", "package_sha256", "frozen_at", "check_at",
        "check_report_sha256", "audit_started_at", "auditor_id"},
        "carried-in admission requires an exact prior-work receipt")
    for name in ("receipt_sha256", "package_sha256", "check_report_sha256"):
        sha(value[name])
    identity(value["auditor_id"])
    require(stamp(value["frozen_at"]) <= stamp(value["check_at"]) <
            stamp(value["audit_started_at"]) <= stamp(admitted_at),
            "carried-in freeze/check/dispatch chronology is invalid")
    return value


def sha(value):
    require(isinstance(value, str) and SHA.fullmatch(value), "SHA-256 required")
    return value


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def selected_slot(seed, block, width):
    """One precommitted ordinal per block; NEVER depends on a package hash."""
    require(width in (4, 10) and type(block) is int and block >= 0, "invalid block")
    return int(digest([identity(seed), block, width])[:16], 16) % width


def first_forty_slots(seed):
    return [block * 4 + selected_slot(seed, block, 4) + 1 for block in range(10)]


def pages(value):
    require(isinstance(value, dict) and value, "scoped source pages required")
    for document, numbers in value.items():
        identity(document)
        require(isinstance(numbers, list) and numbers and
                all(type(n) is int and n > 0 for n in numbers) and
                len(numbers) == len(set(numbers)), "invalid scoped source pages")
    return {document: set(numbers) for document, numbers in value.items()}


def check_receipt(package_path, report_path, exit_code, at, resolutions=None):
    """Wrap a REAL check_records.py run; flags remain advisory until source resolved.

    Caller supplies the actual process exit code/time; this function does not
    execute the checker and must not be used to invent a successful run.
    Resolutions map string flag indexes to {disposition, source_locator, note}.
    """
    package = json.loads(Path(package_path).read_text(encoding="utf-8-sig"))
    report = json.loads(Path(report_path).read_text(encoding="utf-8-sig"))
    source = identity(package["source"]["primary_source_id"])
    require(exit_code == 0, "check_records.py did not complete successfully")
    stamp(at)
    require(isinstance(report.get("flags"), list), "checker flags missing")
    records = package.get("records", [])
    require(records and report.get("summary", {}).get("records") == len(records),
            "checker did not cover all package records")
    require(set(report.get("summary", {}).get("by_paper", {})) == {source},
            "checker source does not match package")
    resolutions = resolutions or {}
    require(set(resolutions) <= {str(i) for i in range(len(report["flags"]))},
            "source disposition references unknown flag")
    for resolution in resolutions.values():
        require(resolution.get("disposition") in
                ("confirmed_source", "corrected", "not_applicable_source_checked"),
                "unresolved advisory flag")
        identity(resolution.get("source_locator"))
        identity(resolution.get("note"))
    return {"tool": "check_records.py", "exit_code": 0, "at": at,
            "primary_source_id": source, "package_sha256":
            hashlib.sha256(Path(package_path).read_bytes()).hexdigest(),
            "report_sha256": hashlib.sha256(Path(report_path).read_bytes()).hexdigest(),
            "record_count": len(records), "flag_count": len(report["flags"]),
            "source_resolutions": resolutions}


def validate_check(receipt, paper, at, require_resolutions=True):
    require(receipt.get("tool") == "check_records.py" and
            type(receipt.get("exit_code")) is int and receipt["exit_code"] == 0,
            "successful check_records.py run required before each audit")
    require(identity(receipt.get("primary_source_id")) == paper["primary_source_id"] and
            receipt.get("package_sha256") == paper["package_sha256"],
            "checker receipt is stale or belongs to another paper")
    sha(receipt.get("report_sha256"))
    require(stamp(paper["frozen_at"]) <= stamp(receipt["at"]) < stamp(at),
            "checker must run after freeze and BEFORE this audit")
    require(receipt.get("record_count") == len(paper["record_ids"]),
            "checker record count mismatch")
    flags = receipt.get("flag_count")
    require(type(flags) is int and flags >= 0, "invalid flag count")
    resolved = receipt.get("source_resolutions", {})
    require(set(resolved) <= {str(i) for i in range(flags)}, "unknown checker flag")
    if require_resolutions:
        require(set(resolved) == {str(i) for i in range(flags)}, "unresolved checker flags at audit acceptance")
    for item in resolved.values():
        require(item.get("disposition") in
                ("confirmed_source", "corrected", "not_applicable_source_checked"),
                "unresolved checker flag")
        identity(item.get("source_locator")); identity(item.get("note"))


def finding_rows(value):
    require(isinstance(value, list), "findings must be an explicit list")
    seen = set()
    for finding in value:
        fid = identity(finding.get("finding_id"))
        require(fid not in seen, "duplicate finding id")
        seen.add(fid)
        require(finding.get("severity") in ("S1", "S2", "S3", "S4"), "unknown severity")
        identity(finding.get("error_type"))
    return value


def sample_results(cohort):
    # All original findings survive later fixes/re-audits. One paper is one result.
    return sorted([p for p in cohort["papers"].values() if p.get("deep_completed_at")],
                  key=lambda p: (stamp(p["deep_completed_at"]), p["primary_source_id"]))


def stopped(cohort):
    last = sample_results(cohort)[-50:]
    return cohort.get("stop_latched", False) or sum(p["deep_s1_s2_ever"] for p in last) > 5


def first_forty(cohort):
    first = sorted([p for p in cohort["papers"].values() if p.get("ordinal", 41) <= 40],
                   key=lambda p: p["ordinal"])
    completed = [p for p in first if p.get("full_accepted") and p.get("integrated")]
    samples = [p for p in first if p.get("sample_required")]
    done = [p for p in samples if p.get("deep_completed_at")]
    positives = sum(p["deep_s1_s2_ever"] for p in done)
    ready = len(first) == 40 and len(completed) == 40 and len(done) == 10
    return {"cohort_papers": len(first), "audited_and_integrated": len(completed),
            "deep_samples_completed": len(done), "deep_s1_s2_papers": positives,
            "report_ready": ready, "may_reduce_to_ten_percent": ready and positives <= 1}


def ramp_gate(cohort, requested_pairs, capacity, backlog_batches, queue_counts, at):
    """Report conditions; never launches workers or invents machine capacity."""
    current = cohort["pair_step"]
    samples = [p for p in sample_results(cohort) if p["pair_step"] == current]
    reasons = []
    if current == 16 or requested_pairs != PAIR_STEPS[PAIR_STEPS.index(current) + 1]:
        reasons.append("ramp must follow 4, 8, 12, 16")
    if len(samples) < 10:
        reasons.append("current step needs at least ten completed deep audits")
    if sum(p["deep_s1_s2_ever"] for p in samples[-10:]) > 1:
        reasons.append("more than one S1/S2-positive paper among last ten deep audits")
    if cohort["collisions"].get(current, 0):
        reasons.append("claim collision recorded in current step")
    if type(backlog_batches) is not int or not 0 <= backlog_batches <= 2:
        reasons.append("integrator backlog exceeds two batches or is unknown")
    try:
        observed = stamp(capacity["observed_at"])
        age = (stamp(at) - observed).total_seconds()
        limit = capacity["runtime_worker_limit"]
        active = capacity["active_workers"]
        require(type(limit) is int and 1 <= limit <= RUNTIME_WORKER_LIMIT,
                "runtime limit cannot exceed actual four-worker quota")
        require(type(active) is int and 0 <= active <= limit and 0 <= age <= 600,
                "current capacity observation required")
        require(capacity.get("machine_spare_capacity") is True and
                bool(capacity.get("measurement_receipt")), "measured spare machine capacity required")
        if 2 * requested_pairs + 1 > limit:
            reasons.append("requested concurrent pairs plus integrator exceed runtime worker quota")
        if active >= limit:
            reasons.append("no spare runtime worker slots")
    except (ValueError, KeyError, TypeError):
        reasons.append("valid recent runtime and machine capacity measurements required")
    if set(queue_counts) != {"qd", "metal"} or not all(type(v) is int and v >= 0 for v in queue_counts.values()):
        reasons.append("remaining QD and metal queue counts required")
    if stopped(cohort):
        reasons.append("quality stop active")
    return {"allowed": not reasons, "requested_pairs": requested_pairs, "reasons": reasons,
            "remaining_queue": queue_counts, "deep_samples_in_step": len(samples),
            "runtime_worker_limit": RUNTIME_WORKER_LIMIT}


def replay(events):
    """Validate append order and reconstruct state without mutating input or history."""
    cohorts, seen, checks_used = {}, {}, set()
    last_recorded_time = None
    for original in events:
        e = json.loads(json.dumps(original))
        eid = identity(e.get("event_id"))
        if eid in seen:
            require(seen[eid] == e, "conflicting duplicate event id")
            continue
        seen[eid] = e
        t = stamp(e["at"])
        recorded = stamp(e.get("recorded_at", e["at"]))
        require(t <= recorded, "actual event time cannot follow ledger insertion")
        require(last_recorded_time is None or recorded >= last_recorded_time,
                "ledger insertion timestamps must be append ordered")
        last_recorded_time = recorded
        cid = identity(e.get("cohort_id")); stage = e.get("stage")
        if stage == "cohort_started":
            require(cid not in cohorts, "cohort cannot be restarted or overwritten")
            identity(e.get("owner_resume_receipt"))
            seed = identity(e.get("sampling_seed"))
            baseline = e.get("baseline_live_source_ids", [])
            require(isinstance(baseline, list) and len(baseline) == len(set(baseline)), "invalid live baseline")
            cohorts[cid] = {"cohort_id": cid, "started_at": e["at"], "sampling_seed": seed,
                "precommitted_first40_slots": first_forty_slots(seed), "baseline_live_source_ids": baseline,
                "owner_resume_receipt": e["owner_resume_receipt"], "papers": {}, "pair_step": 4,
                "collisions": {}, "reduced_at_ordinal": None, "stop_latched": False, "events": [e]}
            continue
        require(cid in cohorts, "explicit owner-resumed cohort required")
        c = cohorts[cid]; c["events"].append(e)
        if stage == "reduce_sampling":
            require(first_forty(c)["may_reduce_to_ten_percent"] and not stopped(c),
                    "ten-percent reduction gate failed")
            require(c["reduced_at_ordinal"] is None, "sampling was already reduced")
            c["reduced_at_ordinal"] = 1 + sum("ordinal" in p for p in c["papers"].values())
            continue
        if stage == "ramp":
            gate = ramp_gate(c, e["requested_pairs"], e["capacity"], e["backlog_batches"], e["queue_counts"], e["at"])
            require(gate["allowed"], "; ".join(gate["reasons"]))
            c["pair_step"] = e["requested_pairs"]
            continue
        if stage == "claim_collision":
            identity(e.get("receipt_id"))
            c["collisions"][c["pair_step"]] = c["collisions"].get(c["pair_step"], 0) + 1
            continue
        source = identity(e.get("primary_source_id"))
        if stage == "claimed":
            require(not stopped(c), "quality stop: no new source claims")
            require(source not in c["papers"], "primary paper already claimed; retain original claim")
            claim = identity(e.get("claim_id"))
            require(all(p["claim_id"] != claim for p in c["papers"].values()), "claim collision")
            require(t >= stamp(c["started_at"]), "claim must be admitted in current owner-resumed cohort")
            extractor = identity(e.get("extractor_id"))
            authors = identities(e.get("scientific_author_ids", [extractor]))
            require(extractor in authors, "scientific authors must include original extractor")
            carried = carried_admission(e["carried_in"], e["at"]) if e.get("carried_in") else None
            c["papers"][source] = {"primary_source_id": source, "claim_id": claim,
                "extractor_id": extractor, "scientific_author_ids": authors,
                "metadata_author_ids": identities(e.get("metadata_author_ids", [])),
                "claimed_at": e["at"], "carried_in": carried, "pair_step": c["pair_step"],
                "full_s1_s2_ever": False, "deep_s1_s2_ever": False, "findings": [], "stage": stage}
            continue
        require(source in c["papers"], "unclaimed primary paper")
        p = c["papers"][source]
        require(e.get("claim_id") == p["claim_id"], "claim identity changed")
        if t < stamp(p["claimed_at"]):
            prior = p.get("carried_in")
            require(prior is not None and stage in ("extraction_frozen", "full_audit_started"),
                    "pre-admission event requires an explicit carried-in freeze or audit-start receipt")
            timestamp_key = "frozen_at" if stage == "extraction_frozen" else "audit_started_at"
            require(t == stamp(prior[timestamp_key]) and
                    e.get("package_sha256") == prior["package_sha256"],
                    "carried-in event does not match original time and package")
        if stage == "extraction_frozen":
            require(source not in c["baseline_live_source_ids"],
                    "baseline published paper requires separate reassessment receipts, not first40 cohort credit")
            require(identity(e.get("extractor_id")) == p["extractor_id"], "one extractor per paper")
            require(not stopped(c) or "package_sha256" in p, "quality stop: only existing corrections permitted")
            sha(e.get("package_sha256")); pages(e.get("scoped_pages"))
            ids = e.get("record_ids")
            require(isinstance(ids, list) and ids and len(ids) == len(set(ids)), "exact unique records required")
            if t < stamp(p["claimed_at"]):
                require("package_sha256" not in p, "cannot replay carried-in freeze as a new revision")
            authors = identities(e.get("scientific_author_ids", p["scientific_author_ids"]))
            require(set(p["scientific_author_ids"]) <= set(authors), "prior scientific authors cannot be removed")
            p["scientific_author_ids"] = authors
            metadata = identities(e.get("metadata_author_ids", p["metadata_author_ids"]))
            require(set(p["metadata_author_ids"]) <= set(metadata), "metadata author history cannot be removed")
            p["metadata_author_ids"] = metadata
            if "ordinal" not in p:
                ordinal = 1 + sum("ordinal" in q for q in c["papers"].values())
                p["ordinal"] = ordinal
                reduced = c["reduced_at_ordinal"]
                width, offset = (10, reduced - 1) if reduced else (4, 0)
                block, position = divmod(ordinal - offset - 1, width)
                p["sample_required"] = position == selected_slot(c["sampling_seed"], block, width)
            p.update(package_sha256=e["package_sha256"], scoped_pages=e["scoped_pages"],
                     record_ids=ids, frozen_at=e["at"], full_accepted=False, deep_accepted=False, integrated=False)
        elif stage in ("full_audit_started", "deep_audit_started"):
            require(not p.get("active_audit"), "paper already has an active audit")
            require("package_sha256" in p, "extraction must be frozen before audit")
            require(e.get("package_sha256") == p["package_sha256"], "audit belongs to stale extraction")
            auditor = identity(e.get("auditor_id"))
            require(auditor not in p["scientific_author_ids"],
                    "auditor must differ from extractor and every scientific author")
            if stage == "full_audit_started":
                require(not p.get("auditor_id") or p["auditor_id"] == auditor, "full auditor identity changed")
                p["auditor_id"] = auditor
            else:
                require(p.get("full_accepted") and p.get("sample_required"), "deep audit requires accepted sampled paper")
                require(auditor != p["auditor_id"], "deep auditor must be a third distinct agent")
            check = e.get("check_receipt", {})
            if t < stamp(p["claimed_at"]):
                prior = p["carried_in"]
                require(auditor == prior["auditor_id"] and
                        check.get("report_sha256") == prior["check_report_sha256"] and
                        stamp(check["at"]) == stamp(prior["check_at"]),
                        "carried-in audit does not match original checker and auditor dispatch")
            validate_check(check, p, e["at"], require_resolutions=False)
            check_id = (check["report_sha256"], check["at"], check["package_sha256"])
            require(check_id not in checks_used, "run check_records.py again before EACH audit")
            checks_used.add(check_id)
            p["active_audit"] = {"event_id": eid, "stage": stage, "at": e["at"],
                                 "auditor_id": auditor, "check_receipt": check,
                                 "package_sha256": p["package_sha256"]}
        elif stage in ("full_audit", "deep_audit"):
            active = p.get("active_audit", {})
            require(e.get("audit_started_event_id") == active.get("event_id") and
                    active.get("stage") == stage + "_started", "matching audit start required")
            require(e.get("package_sha256") == p.get("package_sha256") == active.get("package_sha256"),
                    "audit belongs to stale extraction")
            require(identity(e.get("auditor_id")) == active["auditor_id"], "audit identity changed")
            check = e.get("check_receipt", {})
            require({k: v for k, v in check.items() if k != "source_resolutions"} ==
                    {k: v for k, v in active["check_receipt"].items() if k != "source_resolutions"},
                    "checker metadata changed during audit")
            validate_check(check, p, active["at"], require_resolutions=e.get("accepted") is True)
            read = pages(e.get("source_pages_read"))
            require(all(doc in read and nums <= read[doc] for doc, nums in pages(p["scoped_pages"]).items()),
                    "auditor did not read all scoped source pages")
            sha(e.get("audit_receipt_sha256"))
            findings = finding_rows(e.get("findings"))
            require(type(e.get("accepted")) is bool, "explicit audit acceptance required")
            if e["accepted"]:
                for finding in findings:
                    if finding["severity"] in ("S1", "S2"):
                        require(finding.get("resolution_status") == "corrected_verified" and
                                bool(finding.get("resolution_receipt")),
                                "accepted audit cannot contain unresolved S1/S2 findings")
            p["findings"].extend(dict(f, audit_stage=stage, event_id=eid) for f in findings)
            prefix = "full" if stage == "full_audit" else "deep"
            p[prefix + "_s1_s2_ever"] |= any(f["severity"] in ("S1", "S2") for f in findings)
            p[prefix + "_accepted"] = e["accepted"]
            if stage == "deep_audit":
                p.setdefault("deep_completed_at", e["at"])
                c["stop_latched"] = stopped(c)
            p.pop("active_audit")
        elif stage == "integrated":
            require(p.get("full_accepted") and
                    (not p.get("sample_required") or p.get("deep_accepted")), "scientific audit gates incomplete")
            require(e.get("package_sha256") == p["package_sha256"], "integration has stale science")
            require(not stopped(c), "quality stop: publication intake is held")
            sha(e.get("integration_receipt_sha256")); p["integrated"] = True
        elif stage == "live_verified":
            require(p.get("integrated") and e.get("package_sha256") == p["package_sha256"], "unintegrated or stale publication")
            require(p.get("full_accepted") and
                    (not p.get("sample_required") or p.get("deep_accepted")),
                    "rejected science cannot receive live publication credit")
            v = e.get("verification", {})
            require(v.get("anonymous") is True and v.get("passed") is True, "anonymous verification required")
            sha(v.get("receipt_sha256"))
            require(re.fullmatch(r"[0-9a-f]{40}", e.get("site_commit", "")) and
                    str(e.get("url", "")).startswith("https://"), "actual deployed commit and URL required")
            p.setdefault("live_at", e["at"])
        elif stage in ("skipped", "held"):
            identity(e.get("reason")); identity(e.get("receipt_id"))
            if stage == "skipped":
                identity(e.get("source_locator"))
                require("ordinal" not in p, "eligible paper cannot escape its cohort/sample via skip")
            p["decision"] = stage
        else:
            raise ValueError("unknown stage: " + str(stage))
        p["stage"] = stage
    return cohorts


def report(events, cohort_id, start, end):
    begin, finish = stamp(start), stamp(end)
    require(finish > begin, "positive elapsed interval required")
    cohorts = replay([e for e in events if stamp(e["at"]) < finish]); c = cohorts[cohort_id]
    require(begin >= stamp(c["started_at"]), "report starts before owner-resumed cohort")
    interval = [e for e in c["events"] if begin <= stamp(e["at"]) < finish]
    # Earliest verified publication across ALL supplied cohorts excludes repeat credit.
    first_live = {}
    baseline = set(c["baseline_live_source_ids"])
    for co in cohorts.values():
        baseline.update(co["baseline_live_source_ids"])
        for p in co["papers"].values():
            if p.get("live_at"):
                source = p["primary_source_id"]
                first_live[source] = min(stamp(p["live_at"]), first_live.get(source, stamp(p["live_at"])))
    live = [s for s, at in first_live.items() if s not in baseline and begin <= at < finish and s in c["papers"]]
    stages = {stage: len({e["primary_source_id"] for e in interval if e["stage"] == stage})
              for stage in ("extraction_frozen", "full_audit", "deep_audit", "integrated", "live_verified", "skipped", "held")}
    stages["new_distinct_live_papers"] = len(live)
    stages["full_audit_accepted"] = len({e["primary_source_id"] for e in interval
                                         if e["stage"] == "full_audit" and e["accepted"]})
    stages["full_audit_rejected"] = len({e["primary_source_id"] for e in interval
                                         if e["stage"] == "full_audit" and not e["accepted"]})
    hours = (finish - begin).total_seconds() / 3600
    return {"schema": SCHEMA, "cohort_id": cohort_id, "start": start, "end_exclusive": end,
            "elapsed_hours": hours, "new_live_papers": sorted(live), "papers_per_elapsed_hour": len(live) / hours,
            "distinct_papers_by_stage": stages, "stage_event_counts": dict(Counter(e["stage"] for e in interval)),
            "carried_in_primary_source_ids": sorted(p["primary_source_id"] for p in c["papers"].values()
                                                     if p.get("carried_in")),
            "late_recorded_events_use_actual_occurrence_times": True,
            "first40": first_forty(c), "stop_required": stopped(c),
            "last50_sampled_s1_s2_papers": sum(p["deep_s1_s2_ever"] for p in sample_results(c)[-50:]),
            "skips_and_holds_never_pad_first40": True,
            "active_worker_time_not_inferred": True, "complete_ledger_history_required": True,
            "scientific_acceptance_supplied_not_inferred": True, "publication_authorized": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    cmd = sub.add_parser("sample-slots"); cmd.add_argument("--seed", required=True)
    cmd = sub.add_parser("validate"); cmd.add_argument("ledger")
    cmd = sub.add_parser("report"); cmd.add_argument("ledger"); cmd.add_argument("--cohort", required=True)
    cmd.add_argument("--start", required=True); cmd.add_argument("--end", required=True)
    cmd = sub.add_parser("check-receipt"); cmd.add_argument("--package", required=True)
    cmd.add_argument("--checker-report", required=True); cmd.add_argument("--exit-code", required=True, type=int)
    cmd.add_argument("--at", required=True); cmd.add_argument("--resolutions", required=True)
    parser.add_argument("--output", help="write new JSON receipt; existing files are never overwritten")
    args = parser.parse_args()
    if args.command == "sample-slots":
        result = {"first40_deep_slots": first_forty_slots(args.seed), "seed": args.seed}
    elif args.command == "check-receipt":
        result = check_receipt(args.package, args.checker_report, args.exit_code, args.at,
                               json.loads(Path(args.resolutions).read_text(encoding="utf-8-sig")))
    else:
        events = [json.loads(line) for line in Path(args.ledger).read_text(encoding="utf-8-sig").splitlines() if line.strip()]
        if args.command == "report":
            result = report(events, args.cohort, args.start, args.end)
        else:
            cohorts = replay(events)
            result = {"passed": True, "cohorts": {k: {"first40": first_forty(c), "stop_required": stopped(c)} for k, c in cohorts.items()}}
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        with Path(args.output).open("x", encoding="utf-8") as out:
            out.write(rendered)
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)
