"""Private, deterministic silver monitoring. No source reads, model calls or publication."""
from __future__ import annotations

import argparse
from collections import defaultdict
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import math
from pathlib import Path
import re

VERSION = "mattersyn-silver-monitor/1"
BANDS = {"high": .98, "medium": .95, "low": .90}
FIELDS = frozenset({"reaction_temperature", "duration", "precursor_amount", "solvent_volume",
                    "concentration", "particle_diameter", "core_diameter", "shell_thickness",
                    "hydrodynamic_diameter", "crystallite_size", "phase", "morphology", "precursor_identity"})
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,119}$")
HASH = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
LIMITS = ("Observed errors describe reviewed instances in sampled primary sources. "
          "Daily cohorts round 5% up to a whole source. Instances within a source can be correlated. "
          "Binomial bounds are nominal IID sensitivity summaries, not per-value probabilities, "
          "simultaneous guarantees, or repeated-look confidence sequences. No inference about gold. "
          "Receipt assertions and precommit timing require independent verification. No publication is performed.")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def ident(value):
    return isinstance(value, str) and bool(ID.fullmatch(value))


def sha(value):
    return isinstance(value, str) and bool(HASH.fullmatch(value))


def timestamp(value):
    require(isinstance(value, str), "Timestamp required")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(result.tzinfo is not None, "Timezone required")
    return result.astimezone(timezone.utc)


def iso(value):
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def window_check(window):
    require(window.get("schema") == VERSION + "/window", "Window schema mismatch")
    require(ident(window.get("window_id")) and ident(window.get("pipeline_id")), "Window/pipeline ID invalid")
    require(sha(window.get("pipeline_sha256")) and sha(window.get("baseline_calibration_sha256")), "Frozen pipeline/calibration missing")
    require(sha(window.get("seed")), "Precommitted 256-bit seed required")
    require(window.get("sampling_fraction") == .05, "Sampling fraction must be 5%")
    require(window.get("thresholds") == BANDS, "Confirmed thresholds required")
    start, end = timestamp(window.get("start")), timestamp(window.get("end_exclusive"))
    require(start < end and start.hour == start.minute == start.second == start.microsecond == 0,
            "Start must be UTC midnight")
    require(end.hour == end.minute == end.second == end.microsecond == 0, "End must be UTC midnight")
    require(timestamp(window.get("registered_at")) < start, "Seed/window must be registered before monitoring starts")
    require(window.get("scope") == "first_verified_silver_release_per_primary_source", "Explicit first-release scope required")
    cells = window.get("cells")
    require(isinstance(cells, list) and cells, "Predeclared field/band cells required")
    require(all(isinstance(c, dict) and set(c) == {"band", "field"} and c["band"] in BANDS and c["field"] in FIELDS for c in cells), "Unsupported field/band cell")
    keys = [(c["band"], c["field"]) for c in cells]
    require(len(set(keys)) == len(keys), "Duplicate window cell")
    return start, end, set(keys)


def unique_events(events):
    require(isinstance(events, list), "Event list required")
    result = {}
    for event in events:
        require(isinstance(event, dict) and ident(event.get("event_id")), "Invalid event ID")
        eid = event["event_id"]
        require(eid not in result or result[eid] == event, "Conflicting duplicate event")
        result[eid] = event
    return result


def manifest_check(claims, cells):
    require(isinstance(claims, list) and claims, "Published claim manifest required")
    out = {}
    for claim in claims:
        require(isinstance(claim, dict), "Invalid published claim")
        require(ident(claim.get("claim_id")), "Public claim ID invalid")
        require((claim.get("band"), claim.get("field")) in cells, "Published field/band outside frozen window")
        require(claim.get("tier") == "silver" and claim.get("state") == "accepted_auto_checked", "Only accepted silver claims may be monitored")
        require(sha(claim.get("claim_sha256")), "Published scientific claim fingerprint required")
        require(claim["claim_id"] not in out, "Duplicate published claim ID")
        out[claim["claim_id"]] = {k: claim[k] for k in ("claim_id", "band", "field", "claim_sha256")}
    return sorted(out.values(), key=lambda c: c["claim_id"])


def plan(window, ledger, through, previous=None):
    """Select ceil(5% of each closed UTC daily source cohort), including every prior cohort.

    The supplied ledger must be a complete lifetime event history. A source enters only on
    its first verified silver release; SI, corrections and promotion never add a source.
    Prior receipts bind past population and seed, so replay cannot drop selected failures.
    """
    start, end, cells = window_check(window)
    through = timestamp(through)
    require(start < through <= end and through.hour == through.minute == through.second == through.microsecond == 0,
            "Through must close a whole day inside the frozen window")
    require(ledger.get("schema") == VERSION + "/deployment-ledger", "Deployment ledger schema mismatch")
    require(ledger.get("complete_lifetime_history") is True, "Complete lifetime deployment history required")
    require(timestamp(ledger.get("complete_through")) >= through, "Ledger coverage incomplete")
    unique = unique_events(ledger.get("events"))
    ordered = sorted(unique.values(), key=lambda e: (timestamp(e.get("at")), e["event_id"]))
    receipts, deployed, seen, cohorts = {}, {}, set(), defaultdict(list)
    excluded = 0
    for event in ordered:
        at = timestamp(event["at"])
        if at >= through:
            continue
        receipts[event["event_id"]] = {"sha256": digest(event), "at": iso(at)}
        if event.get("tier") != "silver" or event.get("stage") not in {"deployed", "live_verified"}:
            excluded += 1
            continue
        require(ident(event.get("package_id")) and ident(event.get("primary_source_id")), "Public package/source ID invalid")
        require(event.get("source_identity_verified") is True, "Primary source identity must be verified")
        require(COMMIT.fullmatch(event.get("commit", "")) and sha(event.get("manifest_sha256")), "Deployment fingerprints required")
        require(ident(event.get("pipeline_id")) and sha(event.get("pipeline_sha256")), "Pipeline provenance required")
        source = event["primary_source_id"]
        key = (event["package_id"], source, event["commit"], event["manifest_sha256"], event["pipeline_id"], event["pipeline_sha256"])
        if event["stage"] == "deployed":
            deployed[key] = event
            continue
        verification = event.get("verification", {})
        if not (verification.get("anonymous") is True and verification.get("passed") is True
                and sha(verification.get("receipt_sha256"))):
            excluded += 1
            continue
        require(key in deployed and timestamp(deployed[key]["at"]) <= at, "Live verification lacks matching deployment")
        if source in seen:
            continue
        seen.add(source)
        if at < start:
            continue
        if event["pipeline_id"] != window["pipeline_id"] or event["pipeline_sha256"] != window["pipeline_sha256"]:
            excluded += 1
            continue
        claims = manifest_check(event.get("published_claims"), cells)
        require(digest(event["published_claims"]) == event["manifest_sha256"], "Published manifest digest mismatch")
        cohorts[at.date().isoformat()].append({"source_id": source, "verified_event_id": event["event_id"], "verified_at": iso(at),
                                              "manifest_sha256": event["manifest_sha256"], "claims": claims,
                                              "verification_event": copy.deepcopy(event), "deployment_event": copy.deepcopy(deployed[key])})
    days = []
    for i in range((through - start).days):
        day = (start + timedelta(days=i)).date().isoformat()
        population = sorted(cohorts.get(day, []), key=lambda s: s["source_id"])
        def score(source):
            message = json.dumps([window["window_id"], day, source["source_id"]], separators=(",", ":")).encode()
            return hmac.new(bytes.fromhex(window["seed"]), message, hashlib.sha256).hexdigest(), source["source_id"]
        size = (len(population) + 19) // 20
        selected = sorted(sorted(population, key=score)[:size], key=lambda s: s["source_id"])
        days.append({"day": day, "deployed_distinct_silver_sources": len(population), "sample_size": size,
                     "effective_sampling_fraction": size / len(population) if population else None,
                     "population_sha256": digest(population), "population": population, "selected": selected})
    result = {"schema": VERSION + "/sample-plan-private", "window": copy.deepcopy(window), "window_sha256": digest(window),
              "through": iso(through), "ledger": copy.deepcopy(ledger), "ledger_receipts": receipts, "days": days,
              "excluded_noneligible_events": excluded, "publication_enabled": False}
    if previous is not None:
        plan_check(previous)
        require(previous["window_sha256"] == result["window_sha256"], "Window/seed changed after freeze")
        require(timestamp(previous["through"]) <= through, "Cannot roll monitoring cutoff backward")
        prior_receipts = {k: v for k, v in receipts.items() if timestamp(v["at"]) < timestamp(previous["through"])}
        require(prior_receipts == previous["ledger_receipts"], "Past ledger was changed, dropped or backfilled")
        require(days[:len(previous["days"])] == previous["days"], "Past cohort/sample changed")
    return result


def plan_check(sample):
    require(sample.get("schema") == VERSION + "/sample-plan-private", "Sample plan schema mismatch")
    require(sample == plan(sample["window"], sample["ledger"], sample["through"]),
            "Sample plan differs from frozen deployment ledger; population/claims/selection changed")
    start, end, cells = window_check(sample["window"])
    require(sample["window_sha256"] == digest(sample["window"]), "Sample window hash mismatch")
    require(sample.get("publication_enabled") is False, "Plans cannot publish")
    through = timestamp(sample["through"])
    require(start < through <= end and through.hour == through.minute == through.second == through.microsecond == 0,
            "Invalid sample cutoff")
    require(len(sample["days"]) == (through - start).days, "Missing daily cohorts")
    seen = set()
    for i, day in enumerate(sample["days"]):
        require(day["day"] == (start + timedelta(days=i)).date().isoformat(), "Daily cohort altered")
        population = day["population"]
        require(day["population_sha256"] == digest(population), "Population digest mismatch")
        require(day["deployed_distinct_silver_sources"] == len(population), "Population size mismatch")
        for source in population:
            require(ident(source["source_id"]) and source["source_id"] not in seen, "Invalid/duplicate population source")
            seen.add(source["source_id"])
            require(sha(source["manifest_sha256"]) and ident(source["verified_event_id"]), "Invalid deployment binding")
            require(source["verified_event_id"] in sample["ledger_receipts"], "Source absent from ledger receipts")
            require(timestamp(source["verified_at"]).date().isoformat() == day["day"], "Source in wrong day")
            require(sample["ledger_receipts"][source["verified_event_id"]]["at"] == source["verified_at"], "Verification time mismatch")
            verified, deployed = source["verification_event"], source["deployment_event"]
            require(verified.get("event_id") == source["verified_event_id"] and verified.get("stage") == "live_verified"
                    and deployed.get("stage") == "deployed", "Missing exact deployment events")
            for event in (verified, deployed):
                receipt = sample["ledger_receipts"].get(event.get("event_id"), {})
                require(receipt.get("sha256") == digest(event) and receipt.get("at") == iso(timestamp(event.get("at"))),
                        "Deployment event differs from frozen ledger receipt")
                require(event.get("primary_source_id") == source["source_id"] and event.get("source_identity_verified") is True
                        and event.get("tier") == "silver" and event.get("manifest_sha256") == source["manifest_sha256"]
                        and event.get("pipeline_id") == sample["window"]["pipeline_id"]
                        and event.get("pipeline_sha256") == sample["window"]["pipeline_sha256"], "Deployment provenance changed")
            require(deployed.get("package_id") == verified.get("package_id") and deployed.get("commit") == verified.get("commit")
                    and timestamp(deployed["at"]) <= timestamp(verified["at"]), "Mismatched deployed/verified release")
            verification = verified.get("verification", {})
            require(verification.get("anonymous") is True and verification.get("passed") is True
                    and sha(verification.get("receipt_sha256")), "Missing anonymous verification")
            require(digest(verified["published_claims"]) == source["manifest_sha256"], "Published manifest digest changed")
            require(source["claims"] == manifest_check(verified["published_claims"], cells), "Sample claims differ from deployed manifest")
            claims = source["claims"]
            require(isinstance(claims, list) and claims, "Empty sampled manifest")
            require(all(set(c) == {"claim_id", "band", "field", "claim_sha256"}
                        and ident(c["claim_id"]) and sha(c["claim_sha256"])
                        and (c["band"], c["field"]) in cells for c in claims), "Malformed sampled manifest")
            require(len({c["claim_id"] for c in claims}) == len(claims), "Duplicate sampled claim")
        def score(source):
            msg = json.dumps([sample["window"]["window_id"], day["day"], source["source_id"]], separators=(",", ":")).encode()
            return hmac.new(bytes.fromhex(sample["window"]["seed"]), msg, hashlib.sha256).hexdigest(), source["source_id"]
        size = (len(population) + 19) // 20
        expected = sorted(sorted(population, key=score)[:size], key=lambda s: s["source_id"])
        require(day["sample_size"] == size and day["selected"] == expected, "Sample changed/cherry picked")


def lower_bound(successes, total, alpha=.05):
    """Nominal one-sided exact binomial sensitivity summary, assuming IID instances."""
    if not total or not successes:
        return 0.0
    if successes == total:
        return alpha ** (1 / total)
    def tail(p):
        terms = [math.lgamma(total + 1) - math.lgamma(i + 1) - math.lgamma(total - i + 1)
                 + i * math.log(p) + (total - i) * math.log1p(-p) for i in range(successes, total + 1)]
        peak = max(terms)
        return math.exp(peak) * sum(math.exp(t - peak) for t in terms)
    low, high = 0.0, 1.0
    for _ in range(65):
        middle = (low + high) / 2
        if tail(middle) < alpha:
            low = middle
        else:
            high = middle
    return (low + high) / 2


def evaluate(sample, audit_events, previous=None):
    """Score complete cumulative sampled manifests; absent/unknown truth is never success.

    Audit events are immutable judgments about exact deployed claim fingerprints. The
    independent scientific reviewer produces them outside this program. Conflicting
    labels require a separate reviewed correction process; this tool cannot erase one.
    """
    plan_check(sample)
    window = sample["window"]
    _, end, cells = window_check(window)
    inventory = {}
    for day in sample["days"]:
        require(day["sample_size"] == len(day["selected"]), "Selected sample size changed")
        for source in day["selected"]:
            require(source["source_id"] not in inventory, "Duplicate primary source in sample")
            inventory[source["source_id"]] = source
    audited, receipts, running, crossed = {}, {}, defaultdict(lambda: [0, 0]), set()
    events = unique_events(audit_events)
    for event in sorted(events.values(), key=lambda e: (timestamp(e.get("at")), e["event_id"])):
        require(event.get("schema") == VERSION + "/audit-event", "Audit event schema mismatch")
        require(event.get("window_sha256") == sample["window_sha256"] and event.get("tier") == "silver", "Audit window/tier mismatch")
        source = inventory.get(event.get("source_id"))
        require(source is not None, "Audit source was not randomly selected")
        require(event.get("manifest_sha256") == source["manifest_sha256"], "Audit refers to another deployed version")
        claims = {c["claim_id"]: c for c in source["claims"]}
        claim = claims.get(event.get("claim_id"))
        require(claim is not None and event.get("claim_sha256") == claim["claim_sha256"], "Audit claim was not in deployed manifest")
        require(event.get("judgment") in {"correct", "incorrect", "unknown"}, "Explicit truth judgment required")
        require(event.get("independent_scientific_audit") is True and ident(event.get("auditor_id")), "Independent scientific audit required")
        extractors = event.get("extractor_ids")
        require(isinstance(extractors, list) and extractors and all(ident(e) for e in extractors)
                and event["auditor_id"] not in extractors, "Auditor must differ from extractors")
        require(sha(event.get("truth_receipt_sha256")), "Private truth receipt digest required")
        require(timestamp(event["at"]) >= timestamp(source["verified_at"]), "Audit predates verified deployment")
        key = (event["source_id"], event["claim_id"])
        receipt = digest(event)
        receipts[event["event_id"]] = receipt
        if key in audited:
            require(audited[key]["judgment"] == event["judgment"]
                    and audited[key]["truth_receipt_sha256"] == event["truth_receipt_sha256"], "Conflicting audit for same scientific claim")
            continue
        audited[key] = event
        if event["judgment"] != "unknown":
            cell = (claim["band"], claim["field"])
            running[cell][0] += 1
            running[cell][1] += event["judgment"] == "incorrect"
            # Integer basis avoids floating-point threshold equality surprises.
            allowed_per_hundred = {"high": 2, "medium": 5, "low": 10}[cell[0]]
            if running[cell][1] * 100 > allowed_per_hundred * running[cell][0]:
                crossed.add(cell)
    if previous is not None:
        require(previous.get("schema") == VERSION + "/monitor-report-private"
                and previous.get("window_sha256") == sample["window_sha256"], "Prior report belongs to another window")
        require(timestamp(previous["through"]) <= timestamp(sample["through"]), "Monitoring report cannot roll back")
        require(all(receipts.get(k) == v for k, v in previous["audit_receipts"].items()), "Prior audit event removed or changed")
        require(all(source in inventory and inventory[source]["manifest_sha256"] == fingerprint
                    for source, fingerprint in previous["sampled_manifest_fingerprints"].items()), "Prior sampled source removed or changed")
        crossed.update((m["band"], m["field"]) for m in previous["metrics"] if m["publication_suspended"])
    grouped = defaultdict(list)
    for source_id, source in inventory.items():
        for claim in source["claims"]:
            grouped[(claim["band"], claim["field"])].append((source_id, audited.get((source_id, claim["claim_id"]))))
    metrics = []
    final = timestamp(sample["through"]) == end
    for band, field in sorted(cells):
        rows = grouped[(band, field)]
        correct = sum(e is not None and e["judgment"] == "correct" for _, e in rows)
        errors = sum(e is not None and e["judgment"] == "incorrect" for _, e in rows)
        unknown = sum(e is not None and e["judgment"] == "unknown" for _, e in rows)
        missing = sum(e is None for _, e in rows)
        n = correct + errors
        sources = defaultdict(list)
        for source_id, event in rows:
            sources[source_id].append(event["judgment"] if event else "missing")
        complete_sources = [states for states in sources.values() if all(s in {"correct", "incorrect"} for s in states)]
        bound = lower_bound(correct, n) if n else None
        reasons = []
        if (band, field) in crossed:
            reasons.append("observed_error_stop_latched")
        if final:
            if missing or unknown:
                reasons.append("incomplete_reviewed_truth_at_window_end")
            if bound is None or bound < BANDS[band]:
                reasons.append("insufficient_cumulative_precision_evidence_at_window_end")
        suspended = bool(reasons)
        status = "SUSPEND" if suspended else "INDEPENDENT_REVIEW_REQUIRED" if final else "MONITORING_INCOMPLETE" if missing or unknown else "MONITORING_ONLY"
        metrics.append({"band": band, "field": field, "sampled_instances": len(rows),
                        "reviewed_known_instances": n, "correct_instances": correct, "error_instances": errors,
                        "unknown_truth_instances": unknown, "missing_truth_instances": missing,
                        "observed_error_rate": errors / n if n else None,
                        "required_precision": BANDS[band], "max_observed_error_rate": {"high": .02, "medium": .05, "low": .10}[band],
                        "nominal_instance_precision_lower95": bound,
                        "distinct_sampled_sources": len(sources), "fully_reviewed_sources": len(complete_sources),
                        "nominal_source_cluster_lower95": lower_bound(sum(all(s == "correct" for s in states) for states in complete_sources), len(complete_sources)) if complete_sources else None,
                        "publication_suspended": suspended, "stop_reasons": reasons, "status": status})
    return {"schema": VERSION + "/monitor-report-private", "window_sha256": sample["window_sha256"],
            "pipeline_id": window["pipeline_id"], "pipeline_sha256": window["pipeline_sha256"],
            "baseline_calibration_sha256": window["baseline_calibration_sha256"],
            "through": sample["through"], "phase": "final" if final else "interim",
            "sample_plan_sha256": digest(sample), "audit_receipts": receipts,
            "sampled_manifest_fingerprints": {s: v["manifest_sha256"] for s, v in sorted(inventory.items())},
            "distinct_deployed_silver_sources": sum(d["deployed_distinct_silver_sources"] for d in sample["days"]),
            "distinct_sampled_silver_sources": len(inventory), "metrics": metrics,
            "status": "SUSPEND_AFFECTED_FIELDS" if any(m["publication_suspended"] for m in metrics) else "MONITORING_ONLY",
            "publication_enabled": False, "limits": LIMITS}


def projection(report, sample, audit_events, previous=None):
    """Public-safe candidate controls only; no science values, quotes, paths or audit identities.

    This is a proposal for the release owner. It does not edit existing publications.
    A suspension applies to every source in that pipeline/field/band, not just errors.
    """
    require(report.get("schema") == VERSION + "/monitor-report-private", "Monitor report schema mismatch")
    expected = evaluate(sample, audit_events, previous)
    require(all(report.get(key) == value for key, value in expected.items()), "Report differs from recomputed audit result")
    require(sha(report.get("window_sha256")) and report.get("phase") in {"interim", "final"}, "Invalid public report binding")
    require(ident(report.get("pipeline_id")) and sha(report.get("pipeline_sha256"))
            and sha(report.get("baseline_calibration_sha256")), "Invalid public pipeline binding")
    metrics = []
    for row in report["metrics"]:
        require(row["band"] in BANDS and row["field"] in FIELDS, "Invalid projection field/band")
        for name in ("sampled_instances", "reviewed_known_instances", "correct_instances", "error_instances",
                     "unknown_truth_instances", "missing_truth_instances", "distinct_sampled_sources", "fully_reviewed_sources"):
            require(type(row[name]) is int and row[name] >= 0, "Invalid public count")
        for name in ("observed_error_rate", "nominal_instance_precision_lower95", "nominal_source_cluster_lower95"):
            require(row[name] is None or type(row[name]) in (int, float) and math.isfinite(row[name]) and 0 <= row[name] <= 1, "Invalid public ratio")
        require(type(row["publication_suspended"]) is bool and row["status"] in {"SUSPEND", "INDEPENDENT_REVIEW_REQUIRED", "MONITORING_INCOMPLETE", "MONITORING_ONLY"}, "Invalid public state")
        require(row["required_precision"] == BANDS[row["band"]]
                and row["max_observed_error_rate"] == {"high": .02, "medium": .05, "low": .10}[row["band"]], "Invalid public threshold")
        require(isinstance(row["stop_reasons"], list) and all(r in {"observed_error_stop_latched", "incomplete_reviewed_truth_at_window_end", "insufficient_cumulative_precision_evidence_at_window_end"} for r in row["stop_reasons"]), "Invalid public stop reason")
        allowed = ("band", "field", "sampled_instances", "reviewed_known_instances", "correct_instances", "error_instances",
                   "unknown_truth_instances", "missing_truth_instances", "observed_error_rate", "required_precision",
                   "max_observed_error_rate", "nominal_instance_precision_lower95", "distinct_sampled_sources",
                   "fully_reviewed_sources", "nominal_source_cluster_lower95", "publication_suspended", "status", "stop_reasons")
        public = {k: row[k] for k in allowed}
        suspended = row["publication_suspended"]
        public.update(publication_action="suspend_field_band" if suspended else "retain_existing_admission_gates",
                      existing_publication_action="propose_versioned_revocation" if suspended else "none",
                      training_masked=True if suspended else None, training_weight=0.0 if suspended else None)
        metrics.append(public)
    return {"schema": VERSION + "/control-candidate", "tier": "silver", "window_sha256": report["window_sha256"],
            "pipeline_id": report["pipeline_id"], "pipeline_sha256": report["pipeline_sha256"],
            "baseline_calibration_sha256": report["baseline_calibration_sha256"],
            "report_sha256": digest(report), "through": iso(timestamp(report["through"])), "phase": report["phase"],
            "publication_enabled": False, "scientific_values_modified": False, "gold_evaluation_eligible": False,
            "new_admissions_authorized": False, "metrics": metrics, "limits": LIMITS}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_new(path, value):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("plan")
    for flag in ("window", "ledger", "through", "out"):
        p.add_argument("--" + flag, required=True)
    p.add_argument("--previous")
    e = sub.add_parser("evaluate")
    for flag in ("plan", "audits", "out"):
        e.add_argument("--" + flag, required=True)
    e.add_argument("--previous")
    e = sub.add_parser("project")
    for flag in ("report", "plan", "audits", "out"):
        e.add_argument("--" + flag, required=True)
    e.add_argument("--previous")
    args = parser.parse_args()
    try:
        if args.command == "plan":
            result = plan(read(args.window), read(args.ledger), args.through, read(args.previous) if args.previous else None)
        elif args.command == "evaluate":
            result = evaluate(read(args.plan), read(args.audits), read(args.previous) if args.previous else None)
        else:
            result = projection(read(args.report), read(args.plan), read(args.audits), read(args.previous) if args.previous else None)
        write_new(args.out, result)
        print(json.dumps({"status": result.get("status", "PRIVATE_CANDIDATE_ONLY"), "publication_enabled": False}))
        return 2 if result.get("status") == "SUSPEND_AFFECTED_FIELDS" else 0
    except (ValueError, KeyError, TypeError, OSError):
        # Never echo private input or a local path in a receipt/error message.
        print(json.dumps({"status": "STOP_INVALID_INPUT_OR_OUTPUT", "publication_enabled": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
