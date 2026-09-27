"""Private, text-only MatterSyn silver reconciliation/calibration. No network/model calls."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

VERSION = "mattersyn-silver/0.1"
BANDS = {"high": .98, "medium": .95, "low": .90}
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:+/() -]{0,119}$")
HASH = re.compile(r"^[a-f0-9]{64}$")
PATH = re.compile(r"(?:[A-Za-z]:[\\/]|\\\\|file://|/Users/|/home/|/tmp/)")
FIELDS = {
    "reaction_temperature": ("temperature", None), "duration": ("time", None),
    "precursor_amount": ("amount", None), "solvent_volume": ("volume", None),
    "concentration": ("concentration", None),
    "particle_diameter": ("length", {"TEM", "SEM"}),
    "core_diameter": ("length", {"TEM", "SEM"}),
    "shell_thickness": ("length", {"TEM", "SEM"}),
    "hydrodynamic_diameter": ("length", {"DLS"}),
    "crystallite_size": ("length", {"XRD"}),
    "phase": (None, {"XRD", "SAED", "electron diffraction"}),
    "morphology": (None, {"TEM", "SEM"}), "precursor_identity": (None, None),
}
# unit -> dimension, canonical unit, multiplier, additive offset
UNITS = {
    "°C": ("temperature", "°C", 1, 0), "K": ("temperature", "°C", 1, -273.15),
    "s": ("time", "s", 1, 0), "min": ("time", "s", 60, 0),
    "h": ("time", "s", 3600, 0), "d": ("time", "s", 86400, 0),
    "mol": ("amount", "mol", 1, 0), "mmol": ("amount", "mol", .001, 0),
    "µmol": ("amount", "mol", .000001, 0),
    "g": ("amount", "g", 1, 0), "mg": ("amount", "g", .001, 0),
    "L": ("volume", "L", 1, 0), "mL": ("volume", "L", .001, 0),
    "µL": ("volume", "L", .000001, 0),
    "mol/L": ("concentration", "mol/L", 1, 0), "M": ("concentration", "mol/L", 1, 0),
    "mM": ("concentration", "mol/L", .001, 0),
    "nm": ("length", "nm", 1, 0), "µm": ("length", "nm", 1000, 0),
    "Å": ("length", "nm", .1, 0),
}
CLAIM_KEYS = {"recipe_id", "sample_id", "slot_id", "field", "value", "unit", "value_text",
              "unit_text", "document_id", "page", "quote", "link_quote", "link_page",
              "modality", "technique", "technique_quote", "technique_page", "chemical_id"}


def digest(data):
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def normalize(text):
    """Same wrapping policy as project's quote validator; retain case and units."""
    text = unicodedata.normalize("NFKC", text).replace("\r", "")
    text = re.sub(r"(?<=\w)-\n[ \t]*(?=\w)", "", text)
    return re.sub(r"\s+", " ", text).strip()


def token_in(token, text):
    anchor = normalize(token)
    boundary = r"[\w.]" if re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?", anchor) else r"\w"
    return bool(re.search(r"(?<!" + boundary + ")" + re.escape(anchor) + r"(?!" + boundary + ")", normalize(text)))


def valid_id(value):
    return isinstance(value, str) and bool(ID.fullmatch(value)) and not PATH.search(value)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def policy_check(policy):
    require(policy.get("schema") == VERSION + "/policy", "Wrong policy schema")
    require(policy.get("thresholds_confirmed") is True, "Thresholds require owner confirmation")
    require(policy.get("thresholds") == BANDS, "Unexpected precision thresholds")
    require(policy.get("confidence") == .95, "Expected one-sided 95% confidence")
    require(isinstance(policy.get("family_bands"), dict), "Frozen family bands missing")
    require(all(valid_id(k) and v in BANDS for k, v in policy["family_bands"].items()), "Invalid family bands")
    require(HASH.fullmatch(policy.get("family_count_snapshot_sha256", "")), "Family-count snapshot hash required")
    require(valid_id(policy.get("pipeline_id")), "Pipeline ID required")
    require(HASH.fullmatch(policy.get("pipeline_sha256", "")), "Frozen pipeline config hash required")


def claim_key(c):
    slot = c.get("slot_id")
    # Formatting only: retain chemical words/numbers; do not fuzzy-match aliases.
    if isinstance(slot, str):
        slot = re.sub(r"[\W_]+", "-", unicodedata.normalize("NFKC", slot).casefold()).strip("-")
    return c.get("recipe_id"), c.get("sample_id"), slot, c.get("field")


def canonical(value, unit):
    if unit is None:
        return normalize(value) if isinstance(value, str) else value, None
    dim, out, factor, offset = UNITS[unit]
    return round(value * factor + offset, 10), out


def equivalent(a, b):
    return canonical(a["value"], a.get("unit")) == canonical(b["value"], b.get("unit"))


def validate_claim(claim, pages, source_id, chemistry):
    """Necessary mechanical checks; does not prove semantic support or sample identity."""
    errors = []
    if not isinstance(claim, dict):
        return ["claim_not_object"]
    if set(claim) - CLAIM_KEYS:
        errors.append("unknown_claim_keys")
    for k in ("recipe_id", "slot_id", "document_id"):
        if not valid_id(claim.get(k)):
            errors.append("invalid_" + k)
    field = claim.get("field")
    if field not in FIELDS:
        return errors + ["unsupported_field"]
    structural = FIELDS[field][1] is not None
    if (structural or claim.get("sample_id") is not None) and not valid_id(claim.get("sample_id")):
        errors.append("invalid_sample_id")
    if claim.get("modality") != "explicit_text":
        errors.append("not_explicit_text")
    doc = pages.get("documents", {}).get(claim.get("document_id"), {})
    if doc.get("source_id") != source_id:
        errors.append("wrong_source_document")
    quote = claim.get("quote")
    page = claim.get("page")
    source = doc.get("pages", {}).get(str(page), "")
    if type(page) is not int or not isinstance(quote, str) or len(quote.strip()) < 8 or not source or normalize(quote) not in normalize(source):
        errors.append("quote_page_mismatch")
    quote = quote if isinstance(quote, str) else ""
    text = claim.get("value_text")
    if not isinstance(text, str) or not text or not token_in(text, quote):
        errors.append("value_not_in_quote")
    dim, techniques = FIELDS[field]
    value = claim.get("value")
    unit = claim.get("unit")
    if dim:
        numeric_text = text
        if isinstance(text, str) and isinstance(unit, str):
            lexical = re.fullmatch(r"([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?)(?:\s*" + re.escape(normalize(unit)) + r")?", normalize(text))
            if lexical:
                numeric_text = lexical.group(1)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            errors.append("invalid_numeric_value")
        else:
            try:
                if float(numeric_text) != value:
                    errors.append("numeric_anchor_mismatch")
            except (TypeError, ValueError):
                errors.append("numeric_anchor_not_scalar")
        if unit not in UNITS or UNITS[unit][0] != dim:
            errors.append("invalid_unit")
        elif claim.get("unit_text") != unit or not token_in(unit, quote):
            errors.append("unit_anchor_mismatch")
        elif isinstance(numeric_text, str):
            nq = normalize(quote)
            matches = list(re.finditer(r"(?<![\w.])" + re.escape(normalize(numeric_text)) + r"\s*" + re.escape(normalize(unit)) + r"(?!\w)", nq))
            if not matches:
                errors.append("numeric_unit_pair_not_in_quote")
            else:
                approximate = r"(?:~|≈|about|approximately|ca\.|around|at least|up to|[<>≤≥])\s*$"
                range_before = r"\d[\d.]*\s*(?:°C|K|nm|h|min|s)?\s*(?:-|–|—|to)\s*$"
                range_after = r"^\s*(?:-|–|—|to)\s*\d"
                if all(re.search(approximate, nq[:m.start()], re.I) or re.search(range_before, nq[:m.start()], re.I)
                       or re.search(range_after, nq[m.end():], re.I) for m in matches):
                    errors.append("range_or_approximation_not_scalar")
        if not any(x in errors for x in ("invalid_numeric_value", "invalid_unit")):
            v, _ = canonical(value, unit)
            if (dim == "temperature" and not -273.15 <= v <= 5000) or (dim != "temperature" and v <= 0):
                errors.append("physical_range")
    elif not isinstance(value, str) or not value or len(value) > 120 or unit is not None or text != value or PATH.search(value):
        errors.append("invalid_text_value")
    if techniques and claim.get("technique") not in techniques:
        errors.append("descriptor_technique_mismatch")
    elif techniques and not token_in(claim["technique"], quote):
        tq, tp = claim.get("technique_quote"), claim.get("technique_page")
        ts = doc.get("pages", {}).get(str(tp), "")
        if (not isinstance(tq, str) or type(tp) is not int or not ts or normalize(tq) not in normalize(ts)
                or not token_in(claim["technique"], tq)):
            errors.append("technique_source_anchor_missing")
    if field == "precursor_identity":
        entry = chemistry.get(claim.get("chemical_id"), {})
        if value not in entry.get("source_aliases", []):
            errors.append("unresolved_chemical_identity")
    # Source labels, never fabricated UUIDs, must co-occur in an exact source span.
    # Presence is not a semantic proof; the heldout scientific calibration must test linkage.
    link = claim.get("link_quote", "")
    link_page = claim.get("link_page")
    link_text = doc.get("pages", {}).get(str(link_page), "")
    if (type(link_page) is not int or not isinstance(link, str) or not link or not link_text
            or normalize(link) not in normalize(link_text)
            or not token_in(str(claim.get("recipe_id", "")), link)
            or (claim.get("sample_id") is not None and not token_in(str(claim["sample_id"]), link))):
        errors.append("explicit_sample_link_missing")
    return errors


def reconciled_contract(reconciled, policy):
    """Reject malformed/tampered private artifacts before calibration or projection."""
    require(reconciled.get("schema") == VERSION + "/reconciled-private", "Reconciled schema mismatch")
    require(reconciled.get("policy_sha256") == digest(policy) and reconciled.get("pipeline_id") == policy["pipeline_id"], "Reconciled policy/pipeline mismatch")
    require(valid_id(reconciled.get("source_id")) and valid_id(reconciled.get("family_id")), "Invalid public source/family ID")
    require(policy["family_bands"].get(reconciled["family_id"]) == reconciled.get("band"), "Reconciled family/band mismatch")
    require(reconciled.get("machine_passes_are_scientific_audit") is False and reconciled.get("publication_enabled") is False, "Reconciled tier flags invalid")
    require(isinstance(reconciled.get("claims"), list), "Reconciled claims missing")
    seen = set()
    for row in reconciled["claims"]:
        require(isinstance(row, dict) and isinstance(row.get("key"), list) and len(row["key"]) == 4, "Malformed reconciled claim key")
        recipe, sample, slot, field = row["key"]
        require(valid_id(recipe) and (sample is None or valid_id(sample)) and valid_id(slot) and isinstance(field, str), "Invalid public claim IDs")
        key = tuple(row["key"])
        require(key not in seen, "Duplicate reconciled claim key")
        seen.add(key)
        alts = row.get("alternatives")
        errors = row.get("validation_errors")
        counts = row.get("pass_alternative_counts")
        require(isinstance(alts, list) and alts and isinstance(errors, list) and len(alts) == len(errors), "Malformed alternative/error contract")
        require(all(isinstance(e, list) and all(isinstance(x, str) for x in e) for e in errors), "Malformed validation error lists")
        require(isinstance(counts, list) and len(counts) == 2 and all(type(c) is int and c >= 0 for c in counts) and sum(counts) == len(alts), "Malformed pass alternative counts")
        require(all(isinstance(c, dict) and claim_key(c) == key for c in alts), "Reconciled key differs from source alternatives")
        require(row.get("state") in {"agreed", "uncertain", "withheld"}, "Unknown reconciled state")
        require(row.get("training_masked") is (row["state"] != "agreed"), "Reconciled training mask mismatch")
        if row["state"] == "agreed":
            require(field in FIELDS and counts == [1,1] and not any(errors) and equivalent(*alts), "Invalid reconciled agreement")


def reconcile(a, b, pages, policy, chemistry=None):
    policy_check(policy)
    chemistry = chemistry or {}
    for draft in (a, b):
        require(draft.get("schema") == VERSION + "/draft", "Wrong draft schema")
        require(draft.get("pipeline_id") == policy["pipeline_id"], "Pipeline mismatch")
        require(draft.get("pipeline_sha256") == policy["pipeline_sha256"], "Pipeline configuration mismatch")
        require(draft.get("runner") == "local" and draft.get("saw_other_draft") is False, "Separate local passes required")
        require(valid_id(draft.get("pass_id")) and HASH.fullmatch(draft.get("prompt_sha256", "")), "Pass provenance missing")
        require(HASH.fullmatch(draft.get("model_sha256", "")), "Model fingerprint missing")
        require(valid_id(draft.get("source_id")), "Primary source-group ID required")
        require(isinstance(draft.get("claims"), list), "Claims must be a list")
    require(a["pass_id"] != b["pass_id"], "Same extraction pass supplied twice")
    require(a["source_id"] == b["source_id"] and a.get("family_id") == b.get("family_id"), "Source/family mismatch")
    band = policy["family_bands"].get(a.get("family_id"))
    require(band in BANDS, "Family not present in frozen band inventory")
    rows = []
    indexes = []
    for draft in (a, b):
        index = {}
        for c in draft["claims"]:
            require(isinstance(c, dict), "Claim must be object")
            key = claim_key(c)
            require(all(isinstance(x, str) for i, x in enumerate(key) if i != 1) and (key[1] is None or isinstance(key[1], str)), "Claim identity fields required")
            index.setdefault(key, []).append(c)
        indexes.append(index)
    for key in sorted(set(indexes[0]) | set(indexes[1]), key=lambda x: json.dumps(x)):
        counts = [len(index.get(key, [])) for index in indexes]
        alternatives = [copy.deepcopy(c) for index in indexes for c in index.get(key, [])]
        validations = [validate_claim(c, pages, a["source_id"], chemistry) for c in alternatives]
        valid = counts == [1, 1] and not any(validations)
        agreed = valid and equivalent(*alternatives)
        state = "agreed" if agreed else "withheld" if band == "high" or any(validations) else "uncertain"
        rows.append({"key": list(key), "state": state, "alternatives": alternatives,
                     "pass_alternative_counts": counts, "validation_errors": validations,
                     "training_masked": state != "agreed"})
    # A complete core/shell triplet must be geometrically consistent. Withhold the whole triplet.
    groups = defaultdict(lambda: defaultdict(list))
    for row in rows:
        if row["state"] == "agreed" and row["key"][3] in {"core_diameter", "shell_thickness", "particle_diameter"}:
            groups[tuple(row["key"][:2])][row["key"][3]].append(row)
    for group in groups.values():
        reason = None
        if any(len(rows) != 1 for rows in group.values()):
            reason = "ambiguous_dimension_slots"
        elif len(group) == 3:
            vals = {f: canonical(rows[0]["alternatives"][0]["value"], rows[0]["alternatives"][0]["unit"])[0] for f, rows in group.items()}
            expected = vals["core_diameter"] + 2 * vals["shell_thickness"]
            if abs(expected - vals["particle_diameter"]) > .05 * max(expected, vals["particle_diameter"]):
                reason = "core_shell_size_inconsistent"
        if reason:
            for rows in group.values():
                for row in rows:
                    row.update(state="withheld", training_masked=True)
                    for errors in row["validation_errors"]:
                        errors.append(reason)
    return {"schema": VERSION + "/reconciled-private", "pipeline_id": policy["pipeline_id"],
            "policy_sha256": digest(policy), "source_id": a["source_id"], "family_id": a["family_id"], "band": band,
            "draft_sha256": [digest(a), digest(b)], "pages_sha256": digest(pages),
            "machine_passes_are_scientific_audit": False, "publication_enabled": False, "claims": rows}


def lower_bound(successes, total, alpha=.05):
    """Exact one-sided Clopper-Pearson binomial lower confidence bound (stdlib)."""
    require(type(successes) is int and type(total) is int and 0 <= successes <= total, "Invalid binomial counts")
    if successes == 0 or total == 0:
        return 0.0
    if successes == total:
        return alpha ** (1 / total)
    def tail(p):
        terms = [math.lgamma(total + 1) - math.lgamma(i + 1) - math.lgamma(total - i + 1)
                 + i * math.log(p) + (total-i) * math.log1p(-p) for i in range(successes, total+1)]
        peak = max(terms)
        return math.exp(peak) * sum(math.exp(t - peak) for t in terms)
    lo, hi = 0.0, 1.0
    for _ in range(65):
        mid = (lo + hi) / 2
        if tail(mid) < alpha:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def calibrate(truth, predictions, policy):
    policy_check(policy)
    require(truth.get("schema") == VERSION + "/gold-holdout", "Wrong gold schema")
    require(truth.get("split") == "heldout" and truth.get("frozen_before_extraction") is True, "Heldout freeze missing")
    require(truth.get("independent_scientific_audit") is True, "Gold requires independent scientific audit")
    require(valid_id(truth.get("auditor_id")) and valid_id(truth.get("extractor_id")) and truth.get("auditor_id") != truth.get("extractor_id"), "Separate gold auditor and extractor identities required")
    require(HASH.fullmatch(truth.get("gold_snapshot_sha256", "")), "Gold snapshot hash required")
    require(truth.get("pipeline_id") == policy["pipeline_id"], "Gold pipeline mismatch")
    require(isinstance(truth.get("records"), list), "Gold records required")
    require(isinstance(truth.get("heldout_source_ids"), list), "Heldout source universe required")
    universe = set(truth["heldout_source_ids"])
    require(all(valid_id(s) for s in universe), "Bad heldout source ID")
    for name in ("training_source_ids", "selection_source_ids"):
        require(isinstance(truth.get(name), list) and all(valid_id(s) for s in truth[name]), "Explicit valid source split lists required")
    forbidden = set(truth["training_source_ids"]) | set(truth["selection_source_ids"])
    require(not universe & forbidden, "Heldout leakage: training/model-selection sources overlap")
    expected = {}
    bucket = defaultdict(lambda: {"gold": 0, "tp": 0, "fp": 0, "clusters": defaultdict(list)})
    for g in truth["records"]:
        require(g.get("source_id") in universe and g.get("field") in FIELDS, "Invalid gold identity")
        require(g.get("band") in BANDS, "Invalid gold band")
        key = (g["source_id"], *claim_key(g))
        require(key not in expected, "Duplicate gold key")
        canonical(g["value"], g.get("unit"))
        expected[key] = g
        bucket[(g["band"], g["field"])]["gold"] += 1
    seen_sources, seen_keys = set(), set()
    for p in predictions:
        reconciled_contract(p, policy)
        require(p.get("policy_sha256") == digest(policy) and p.get("pipeline_id") == policy["pipeline_id"], "Stale prediction pipeline/policy")
        require(policy["family_bands"].get(p.get("family_id")) == p.get("band"), "Prediction popularity band mismatch")
        source = p["source_id"]
        require(source in universe and source not in seen_sources, "Unknown/duplicate source calibration package")
        seen_sources.add(source)
        for row in p["claims"]:
            if row["state"] != "agreed":
                continue
            require(not any(row["validation_errors"]) and len(row["alternatives"]) == 2 and equivalent(*row["alternatives"]), "Tampered agreement")
            c = row["alternatives"][0]
            key = (source, *claim_key(c))
            require(key not in seen_keys, "Duplicate predicted claim")
            seen_keys.add(key)
            gold = expected.get(key)
            ok = bool(gold and gold["band"] == p["band"] and equivalent(c, gold))
            b = bucket[(p["band"], c["field"])]
            b["tp" if ok else "fp"] += 1
            b["clusters"][source].append(ok)
    # Missing entire predicted sources are omissions; retain their gold denominator.
    metrics = []
    for (band, field), b in sorted(bucket.items()):
        n = b["tp"] + b["fp"]
        clusters = b["clusters"]
        passing_sources = sum(all(values) for values in clusters.values())
        instance_bound = lower_bound(b["tp"], n)
        source_bound = lower_bound(passing_sources, len(clusters))
        threshold = BANDS[band]
        passes = bool(n and instance_bound >= threshold)
        metrics.append({"band": band, "field": field, "gold_instances": b["gold"], "predicted_instances": n,
                        "true_positive": b["tp"], "false_positive": b["fp"], "false_negative": max(0, b["gold"]-b["tp"]),
                        "precision": b["tp"]/n if n else None, "recall": b["tp"]/b["gold"] if b["gold"] else None,
                        "instance_precision_lower95": instance_bound, "distinct_source_clusters": len(clusters),
                        "all_correct_source_clusters": passing_sources, "source_cluster_lower95": source_bound,
                        "required_precision": threshold, "minimum_zero_error_instances": math.ceil(math.log(.05)/math.log(threshold)),
                        "precision_basis": "field_instance", "iid_assumption": "Instances are treated as independent for the admission interval; this may overstate confidence for correlated paper variants.",
                        "source_dependence_warning": source_bound < threshold,
                        "status": "eligible_for_independent_calibration_review" if passes else "STOP"})
    return {"schema": VERSION + "/calibration", "pipeline_id": policy["pipeline_id"], "policy_sha256": digest(policy),
            "gold_snapshot_sha256": truth["gold_snapshot_sha256"], "truth_sha256": digest(truth),
            "prediction_sha256": digest(predictions), "precision_basis": "field_instance",
            "confidence_method": "one-sided exact binomial 95% on field instances under an IID assumption; source-cluster interval is reported as a dependence sensitivity, not the admission gate",
            "holdout_sources": len(universe), "predicted_sources": len(seen_sources), "metrics": metrics,
            "status": "STOP" if not metrics or not any(m["status"] != "STOP" for m in metrics) else "INDEPENDENT_REVIEW_REQUIRED",
            "publication_enabled": False, "limits": "The admission bound is not dependence-adjusted. Repeated variants from a paper may be correlated; an independent calibration reviewer must explicitly assess the field-instance IID assumption and source-cluster sensitivity."}


def project(reconciled, calibration, policy, approval=None, pages=None, chemistry=None):
    """Whitelist public candidate projection only. This module can never deploy."""
    policy_check(policy)
    reconciled_contract(reconciled, policy)
    require(reconciled.get("policy_sha256") == digest(policy) == calibration.get("policy_sha256"), "Policy binding mismatch")
    require(reconciled.get("pipeline_id") == policy["pipeline_id"] == calibration.get("pipeline_id"), "Pipeline binding mismatch")
    approved = bool(approval and approval.get("approved") is True and approval.get("calibration_sha256") == digest(calibration)
                    and valid_id(approval.get("reviewer_id")) and approval.get("independent") is True
                    and isinstance(approval.get("extractor_ids"), list) and approval["extractor_ids"]
                    and approval["reviewer_id"] not in approval["extractor_ids"]
                    and approval.get("field_instance_iid_assumption_reviewed") is True)
    metrics = {(m["band"], m["field"]): m for m in calibration["metrics"]}
    result = []
    for row in reconciled["claims"]:
        field = row["key"][3]
        if field not in FIELDS:
            continue
        metric = metrics.get((reconciled["band"], field))
        eligible = bool(approved and metric and metric["status"] == "eligible_for_independent_calibration_review")
        page_bound = bool(pages and digest(pages) == reconciled.get("pages_sha256"))
        accepted = bool(eligible and page_bound and row["state"] == "agreed" and not any(row["validation_errors"])
                        and all(not validate_claim(c, pages, reconciled["source_id"], chemistry or {}) for c in row["alternatives"]))
        state = "accepted_auto_checked" if accepted else "uncertain" if row["state"] == "uncertain" and eligible else "not_extracted"
        out = {"recipe_id": row["key"][0], "sample_id": row["key"][1], "slot_id": row["key"][2], "field": field,
               "state": state, "value": None, "unit": None, "training_masked": not accepted,
               "training_weight": 0.0, "locators": []}
        if accepted:
            c = row["alternatives"][0]
            out.update(value=c["value"], unit=c.get("unit"), training_weight=min(metric["instance_precision_lower95"], metric["source_cluster_lower95"]))
            out["locators"] = sorted({(x["document_id"], x["page"]) for x in row["alternatives"]})
            out["locators"] = [{"document_id": d, "page": p} for d, p in out["locators"]]
        result.append(out)
    candidate = {"schema": VERSION + "/public-candidate", "tier": "silver", "badge": "Machine-extracted, not reviewed",
                 "source_id": reconciled["source_id"], "family_id": reconciled["family_id"], "band": reconciled["band"],
                 "sparse_data_banner": reconciled["band"] == "low", "publication_enabled": False,
                 "has_publishable_values": any(not r["training_masked"] for r in result), "fields": result,
                 "calibration_sha256": digest(calibration), "scientific_audit": "not performed per paper"}
    require(not PATH.search(json.dumps(candidate)), "Public projection contains local path")
    return candidate


def count_sources(candidates):
    """Publication ledger must additionally establish actual deployment and anonymous access."""
    return len({c["source_id"] for c in candidates if c.get("has_publishable_values")})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("reconcile")
    for name in ("draft-a", "draft-b", "pages", "policy", "out"):
        r.add_argument("--"+name, required=True)
    r.add_argument("--chemistry")
    c = sub.add_parser("calibrate")
    for name in ("truth", "predictions", "policy", "out"):
        c.add_argument("--"+name, required=True)
    q = sub.add_parser("project")
    for name in ("input", "calibration", "policy", "out"):
        q.add_argument("--"+name, required=True)
    q.add_argument("--approval")
    q.add_argument("--pages", required=True, help="Revalidate accepted claims against the original private page map")
    q.add_argument("--chemistry")
    args = p.parse_args()
    try:
        policy = read(args.policy)
        if args.command == "reconcile":
            result = reconcile(read(args.draft_a), read(args.draft_b), read(args.pages), policy, read(args.chemistry) if args.chemistry else {})
        elif args.command == "calibrate":
            result = calibrate(read(args.truth), read(args.predictions), policy)
        else:
            result = project(read(args.input), read(args.calibration), policy, read(args.approval) if args.approval else None,
                             read(args.pages), read(args.chemistry) if args.chemistry else {})
        write(args.out, result)
        print(json.dumps({"command": args.command, "status": result.get("status", "PRIVATE_OUTPUT_ONLY"), "publication_enabled": False}))
        return 2 if result.get("status") == "STOP" else 0
    except (ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "STOP", "error": str(exc), "publication_enabled": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
