"""Read-only incoming-paper queue; all state stays beside this script.

Scanning establishes file stability, never scientific review completeness.

Priority is explicitly activated with ``set-priority --data POLICY_JSON``.
Evidence policy payload: {"mode": "evidence_richness", "source_report":
"C:/absolute/ranked-scopes.json", "source_report_sha256": "<64 hex digits>",
"screened_at": "<ISO8601 timestamp with timezone>", "require_screened": true,
"rankings": [{"group_id": "<canonical group>", "score": 12.5,
"source_generation": 1}]}. The source report must exist and match its digest;
each ranking must match the current ledger generation. This records screening
priority only, never scientific review or a no-recipe disposition. Changed and
unranked scopes remain queued, but cannot receive a new claim until re-screened.
Existing claims, checkpoints and arrival queue_order values are preserved.
To explicitly restore the original order use {"mode": "arrival_order"}.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile
import time

DEFAULT_SOURCE = Path(r"[local path redacted]")
DEFAULT_LEDGER = Path(__file__).with_name("ledger.json")
DEFAULT_LEGACY = Path(r"[local path redacted]")
DEFAULT_MANIFEST = Path(r"[local path redacted]")
DEFAULT_INVENTORY = DEFAULT_MANIFEST.with_name("inventory.json")
DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip", ".csv", ".cif", ".tif", ".tiff", ".png", ".jpg", ".jpeg", ".txt", ".xml", ".ppt", ".pptx"}
TERMINAL_STATUSES = {"complete", "no_useful_information", "no_synthesis_recipe"}
REVIEW_STATUSES = {"queued", "in_progress", "blocked"} | TERMINAL_STATUSES
SECOND = 1_000_000_000
MILESTONES = ("read", "extract", "audit", "integrate", "publish")
MAX_BATCH_SIZE = 5


def pending_milestones():
    return {stage: {"status": "pending", "evidence": []} for stage in MILESTONES}


def normalized_doi(value):
    text = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", str(value).strip(), flags=re.I)
    text = re.sub(r"^doi:\s*", "", text, flags=re.I).lower()
    return text if re.fullmatch(r"10\.\d{4,9}/\S+", text) else None


def filename_doi(group):
    # This is a candidate only: DOI suffix underscores need not represent slashes.
    return normalized_doi(group.replace("_", "/", 1))


def canonical_group(ledger, key):
    seen = set()
    while key in ledger.get("group_aliases", {}):
        if key in seen:
            raise ValueError("Cyclic group aliases")
        seen.add(key)
        key = ledger["group_aliases"][key]
    return key


def active_claims(ledger):
    """Read current claims without changing a saved ledger or its checkpoints."""
    batch = ledger.get("current_batch")
    if batch:
        return [claim for claim in batch["papers"] if
                ledger["groups"][claim["group_id"]]["needs_recheck"] or
                ledger["groups"][claim["group_id"]]["review"]["status"] not in TERMINAL_STATUSES]
    return [ledger["current_paper"]] if ledger.get("current_paper") else []


def sync_batch(ledger, now):
    """Keep the legacy pointer accurate; archive only a fully closed batch."""
    batch = ledger.get("current_batch")
    if not batch:
        return
    claims = active_claims(ledger)
    ledger["current_paper"] = claims[0] if claims else None
    if not claims:
        ledger.setdefault("batch_history", []).append({**batch, "closed_at": iso(now)})
        ledger["current_batch"] = None


def selected_claim(ledger, reviewer, group_id, operation):
    batch = ledger.get("current_batch")
    if batch and not group_id:
        raise RuntimeError(f"{operation} requires explicit --group for each batch paper.")
    claims = active_claims(ledger)
    selected = next((claim for claim in claims if group_id is None or claim["group_id"] == group_id), None)
    if not selected or selected["reviewer"] != reviewer:
        raise RuntimeError(f"{operation} requires an active claim owned by this reviewer for the selected group.")
    return selected


def evidence_files_exist(references, base):
    if not isinstance(references, list) or not references or not all(isinstance(ref, str) and ref.strip() for ref in references):
        raise ValueError("Screening evidence requires nonempty file references.")
    for reference in references:
        candidate = Path(reference)
        if not (candidate if candidate.is_absolute() else base / candidate).is_file():
            raise ValueError("Screening evidence file does not exist: " + reference)


def validate_screening(record, group, reviewer, base):
    """Validate a scoped no-recipe disposition; never infer scientific absence."""
    if not isinstance(record, dict) or record.get("outcome") != "no_synthesis_recipe":
        raise ValueError("no_synthesis_recipe requires checkpoint.screening with that explicit outcome.")
    if type(record.get("source_generation")) is not int or record["source_generation"] != group["generation"]:
        raise ValueError("Screening must explicitly identify the current source_generation.")
    for field in ("scope", "reason"):
        if not isinstance(record.get(field), str) or not record[field].strip():
            raise ValueError("Screening requires an explicit supplied-source scope and reason.")
    evidence_files_exist(record.get("evidence"), base)
    audit = record.get("independent_audit")
    if not isinstance(audit, dict) or audit.get("status") != "passed":
        raise ValueError("Screening requires a passed independent screening audit.")
    auditor = audit.get("reviewer")
    primary = record.get("reviewer")
    if primary is not None and (not isinstance(primary, str) or not primary.strip()):
        raise ValueError("Primary screening reviewer must be a nonempty identifier when supplied.")
    if not isinstance(auditor, str) or not auditor.strip() or auditor in {reviewer, primary}:
        raise ValueError("Screening auditor must be identified and independent of the owner and primary screener.")
    evidence_files_exist(audit.get("evidence"), base)


def file_path(ledger, key):
    item = ledger["files"][key]
    root = ledger.get("source_paths", {"incoming": ledger["source_path"]})[item.get("source_id", "incoming")]
    return Path(root) / item.get("relative_filename", key)


def inventory_sources(ledger):
    if ledger.get("schema_version", 1) == 1:
        return inventory(Path(ledger["source_path"]))
    observed = {}
    for alias, source in ledger["source_paths"].items():
        for name, data in inventory(Path(source)).items():
            key = name if alias == "incoming" else alias + "::" + name
            origin = data["group_id"] if alias == "incoming" else alias + "::" + data["group_id"]
            old = ledger["files"].get(key, {})
            data.update(source_id=alias, relative_filename=name, origin_group_id=origin)
            data["doi_candidates"] = [filename_doi(data["group_id"])] if filename_doi(data["group_id"]) else []
            for field in ("doi_candidates", "role_candidates", "role_ambiguous", "detected_format", "legacy_manifest"):
                if field in old:
                    data[field] = old[field]
            if "role" in old:
                data["role"] = old["role"]
            data["group_id"] = canonical_group(ledger, old.get("group_id", origin))
            observed[key] = data
    return observed


def reconcile_content(ledger):
    """Merge review units only on confirmed main bytes; DOI alone is a link."""
    if ledger.get("schema_version", 1) < 2:
        return
    groups = ledger["groups"]
    # A prior byte match is not permanent identity if either source copy changes.
    for alias, target in list(ledger.get("group_aliases", {}).items()):
        target = canonical_group(ledger, target)
        alias_files = [name for name, item in ledger["files"].items() if item["exists"] and item.get("origin_group_id") == alias]
        target_files = [name for name in groups[target]["files"] if ledger["files"][name].get("origin_group_id") == target]
        alias_main = {ledger["files"][name].get("sha256") for name in alias_files if ledger["files"][name]["role"] == "main"}
        target_main = {ledger["files"][name].get("sha256") for name in target_files if ledger["files"][name]["role"] == "main"}
        if len(alias_main) == 1 and None not in alias_main and alias_main == target_main:
            continue
        del ledger["group_aliases"][alias]
        groups[alias].pop("alias_of", None)
        groups[alias].pop("alias_basis", None)
        groups[alias]["files"] = sorted(alias_files)
        for name in alias_files:
            ledger["files"][name]["group_id"] = alias
        groups[target]["files"] = sorted(set(groups[target]["files"]) - set(alias_files))
        if alias in groups[target].get("linked_review_groups", []):
            groups[target]["linked_review_groups"].remove(alias)
        for key in (alias, target):
            groups[key]["generation"] += 1
            groups[key]["needs_recheck"] = True
            groups[key]["identity_recheck_reason"] = "Previously identical main source changed, disappeared, or lacks a current confirmed hash."
    hash_groups = {}
    for key, group in groups.items():
        if group.get("alias_of"):
            continue
        for name in group["files"]:
            item = ledger["files"][name]
            if item["role"] == "main" and item.get("sha256"):
                hash_groups.setdefault(item["sha256"], set()).add(key)
    current = (ledger.get("current_paper") or {}).get("group_id")
    batch_members = {claim["group_id"] for claim in (ledger.get("current_batch") or {}).get("papers", [])}
    for digest, candidates in hash_groups.items():
        active = {canonical_group(ledger, key) for key in candidates}
        if len(active) < 2:
            continue
        ordered = sorted(active, key=lambda key: (key not in batch_members, key != current, groups[key]["queue_order"]))
        target = ordered[0]
        # A multi-main group with conflicting versions cannot be collapsed by one shared hash.
        def main_set(key):
            items = [ledger["files"][name] for name in groups[key]["files"] if ledger["files"][name]["role"] == "main"]
            return {x.get("sha256") for x in items}
        for other in ordered[1:]:
            if main_set(target) != {digest} or main_set(other) != {digest}:
                continue
            # Each batch member owns independent evidence. Reconcile these only
            # after the fixed batch closes, rather than silently emptying a claim.
            if target in batch_members and other in batch_members:
                continue
            ledger.setdefault("group_aliases", {})[other] = target
            groups[other]["alias_of"] = target
            groups[other]["alias_basis"] = {"kind": "confirmed_identical_main_sha256", "sha256": digest}
            groups[target].setdefault("linked_review_groups", []).append(other)
            for name in groups[other]["files"]:
                ledger["files"][name]["group_id"] = target
            groups[target]["files"] = sorted(set(groups[target]["files"] + groups[other]["files"]))
            groups[other]["files"] = []
            groups[target]["generation"] += 1
            groups[target]["needs_recheck"] = True
            groups[target]["review"].setdefault("milestones", pending_milestones())
    doi_index = {}
    for key, group in groups.items():
        if group.get("alias_of"):
            continue
        group["doi_candidates"] = sorted({doi for name in group["files"] for doi in ledger["files"][name].get("doi_candidates", [])})
        for doi in group["doi_candidates"]:
            doi_index.setdefault(doi, []).append(key)
    ledger["doi_candidate_index"] = doi_index
    for key, group in groups.items():
        related = sorted({other for doi in group.get("doi_candidates", []) for other in doi_index.get(doi, []) if other != key})
        group["same_doi_candidates"] = related
        own = {ledger["files"][name].get("sha256") for name in group["files"] if ledger["files"][name]["role"] == "main"}
        own.discard(None)
        group["same_doi_differing_main_hash"] = [other for other in related if own and
            (other_hashes := {ledger["files"][name].get("sha256") for name in groups[other]["files"] if ledger["files"][name]["role"] == "main"})
            and None not in other_hashes and own.isdisjoint(other_hashes)]
        by_content = {}
        for name in group["files"]:
            if digest := ledger["files"][name].get("sha256"):
                by_content.setdefault(digest, []).append(name)
        group["confirmed_content_copies"] = by_content
        group["unhashed_file_copies"] = [name for name in group["files"] if not ledger["files"][name].get("sha256")]


def upgrade_two_sources(path: Path, legacy: Path, manifest_path: Path, inventory_path: Path, now=None):
    now = time.time_ns() if now is None else now
    with locked_ledger(path):
        ledger = read_ledger(path)
        if ledger.get("schema_version") >= 2:
            if Path(ledger["source_paths"]["legacy"]).resolve() != legacy.resolve():
                raise ValueError("Legacy source differs from migrated ledger")
            return {"already_migrated": True, **summary(ledger, now)}
        # Save the original claim/checkpoint verbatim before introducing a second source.
        backup = path.with_name("ledger.schema1-before-two-folder.json")
        if not backup.exists():
            save_ledger(backup, ledger)
        docs = json.loads(manifest_path.read_text(encoding="utf-8"))["documents"]
        roles = {doc["relativeFilename"]: doc for doc in json.loads(inventory_path.read_text(encoding="utf-8"))["documents"]}
        cached = {doc["sourceRelativeFilename"]: doc for doc in docs}
        ledger.update(schema_version=2, source_paths={"incoming": ledger["source_path"], "legacy": str(legacy.resolve())}, group_aliases={})
        for name, item in ledger["files"].items():
            doi = filename_doi(item["group_id"])
            item.update(source_id="incoming", relative_filename=name, origin_group_id=item["group_id"], doi_candidates=[doi] if doi else [])
        for group in ledger["groups"].values():
            group["review"].setdefault("milestones", pending_milestones())
            if group["review"]["status"] in TERMINAL_STATUSES:
                group["needs_recheck"] = True
                group["re_audit_reason"] = "Two-folder completeness audit requested; past publication does not complete it."
        observed = inventory_sources(ledger)
        reused = 0
        for key, item in observed.items():
            if item["source_id"] != "legacy":
                continue
            name = item["relative_filename"]
            doc = cached.get(name)
            associations = roles.get(name, {}).get("associations", [])
            item["doi_candidates"] = sorted({value for row in associations if (value := normalized_doi(row.get("doi", "")))}) or item["doi_candidates"]
            item["role_candidates"] = sorted({role for row in associations for role in row.get("roleCandidates", [])})
            if item["role_candidates"] == ["main_candidate"]:
                item["role"] = "main"
            elif item["role_candidates"] in (["si_candidate"], ["supporting_candidate"]):
                item["role"] = "si"
            item["role_ambiguous"] = len(item["role_candidates"]) != 1 or bool((doc or {}).get("roleMismatchFlag"))
            if doc:
                item["detected_format"] = doc.get("detectedFormat")
                item["legacy_manifest"] = {"path": str(manifest_path), "document_id": doc["id"],
                    "inventory_path": str(inventory_path), "role_basis": "candidate_metadata_requires_source_review"}
                fp = doc.get("fingerprint", {})
                if fp.get("bytes") == item["size"] and fp.get("mtimeNs") == item["mtime_ns"] and re.fullmatch(r"[0-9a-f]{64}", doc.get("sha256", "")):
                    item["sha256"] = doc["sha256"]
                    item["hash_evidence"] = {"kind": "exact_size_mtime_legacy_manifest_reuse", "manifest": str(manifest_path),
                        "document_id": doc["id"], "size": item["size"], "mtime_ns": item["mtime_ns"], "actual_selected_hash_required_before_completion": True}
                    reused += 1
        result = scan_state(ledger, observed, now, legacy_first=True)
        for group in ledger["groups"].values():
            group["review"].setdefault("milestones", pending_milestones())
        reconcile_content(ledger)
        sync_batch(ledger, now)
        ledger["two_folder_backfill"] = {"migrated_at": iso(now), "cached_hashes_reused": reused,
            "manifest": str(manifest_path), "inventory": str(inventory_path), "initial_legacy_backlog_enqueued_before_future_arrivals": True,
            "past_publication_is_not_a_completion_signal": True}
        save_ledger(path, ledger)
        return {"cached_hashes_reused": reused, **result, **summary(ledger, now)}


def iso(ns: int) -> str:
    return dt.datetime.fromtimestamp(ns / SECOND, dt.timezone.utc).isoformat()


def classification(name: str):
    """Preserve DOI underscores; only strip an anchored SI-number suffix."""
    p = Path(name)
    if name.startswith(("_", ".")) or p.suffix.lower() in {".log", ".jsonl", ".tmp", ".part", ".crdownload", ".download"}:
        return None
    if p.suffix.lower() not in DOCUMENT_EXTENSIONS and not name.startswith("10."):
        return None
    match = re.fullmatch(r"(.+)_si_(\d+)", p.stem, re.IGNORECASE)
    if match:
        return match[1], "si"
    if p.suffix.lower() == ".pdf":
        return p.stem, "main"
    return p.stem, "unsupported"


def stat_info(path: Path):
    s = path.stat()
    birth = getattr(s, "st_birthtime_ns", None)
    if birth is None:
        birth = s.st_ctime_ns
        basis = "windows_creation_time" if os.name == "nt" else "ctime_fallback"
    else:
        basis = "birth_time"
    return {"size": s.st_size, "mtime_ns": s.st_mtime_ns, "birthtime_ns": birth, "birthtime_basis": basis}


def signature(item):
    return item["size"], item["mtime_ns"], item["birthtime_ns"]


def inventory(source: Path):
    result = {}
    for p in source.iterdir():
        if p.is_symlink() or not p.is_file():
            continue
        label = classification(p.name)
        if label:
            result[p.name] = {"group_id": label[0], "role": label[1], **stat_info(p)}
    return result


def new_ledger(source: Path, now: int):
    return {"schema_version": 1, "source_path": str(source.resolve()), "created_at": iso(now), "last_scan_at": None,
            "next_queue_order": 1, "files": {}, "groups": {}, "current_paper": None}


def read_ledger(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_ledger(path: Path, ledger):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(ledger, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


@contextlib.contextmanager
def locked_ledger(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_suffix(path.suffix + ".lock")
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise RuntimeError(f"Queue lock exists: {lock}. Inspect its PID before manually removing a stale lock.") from exc
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump({"pid": os.getpid(), "created_at": iso(time.time_ns())}, stream)
        yield
    finally:
        lock.unlink(missing_ok=True)


def scan_state(ledger, observed, now, legacy_first=False):
    initial = ledger["last_scan_at"] is None
    changed_groups = set()
    groups_seen = {}
    for name, data in observed.items():
        groups_seen.setdefault(data["group_id"], []).append((name, data))
        previous = ledger["files"].get(name)
        if previous is None:
            ledger["files"][name] = {**data, "first_seen_at": iso(now), "same_since_ns": now,
                                      "observations": 1, "last_observed_ns": now, "exists": True}
            changed_groups.add(data["group_id"])
        elif not previous["exists"] or signature(previous) != signature(data):
            previous.update(data, exists=True, same_since_ns=now, observations=1, last_observed_ns=now)
            previous.pop("sha256", None)
            previous.pop("hash_evidence", None)
            changed_groups.add(data["group_id"])
        elif now > previous["last_observed_ns"]:
            previous["observations"] += 1
            previous["last_observed_ns"] = now
    for name, old in ledger["files"].items():
        if name not in observed and old["exists"]:
            old["exists"] = False
            old.pop("sha256", None)
            old.pop("hash_evidence", None)
            changed_groups.add(old["group_id"])

    new_groups = [key for key in groups_seen if key not in ledger["groups"]]
    def arrival(key):
        entries = groups_seen[key]
        mains = [item for _, item in entries if item["role"] == "main"]
        return min(item["birthtime_ns"] for item in mains or [item for _, item in entries]), key
    # Fixed initial backlog uses actual main-PDF arrival, never copied mtime.
    # Later scans append newcomers; birth time breaks ties only inside that scan.
    new_groups.sort(key=lambda key: (not any(data.get("source_id") == "legacy" for _, data in groups_seen[key]), arrival(key)) if legacy_first else arrival(key))
    for key in new_groups:
        ledger["groups"][key] = {"queue_order": ledger["next_queue_order"], "first_seen_at": iso(now),
            "order_basis": "initial_main_birthtime" if initial else "later_first_seen_scan",
            "files": [], "generation": 1, "needs_recheck": False,
            "review": {"status": "queued", "checkpoint": {}, "history": [], "milestones": pending_milestones()}}
        ledger["next_queue_order"] += 1
    for key, group in ledger["groups"].items():
        group["files"] = sorted(name for name, item in ledger["files"].items() if item["group_id"] == key and item["exists"])
        if key in changed_groups and key not in new_groups:
            group["generation"] += 1
            group["needs_recheck"] = True
            group["last_change_at"] = iso(now)
            # The manual status/checkpoint/history is deliberately never overwritten.
    ledger["last_scan_at"] = iso(now)
    return {"new_groups": len(new_groups), "changed_existing_groups": len(changed_groups - set(new_groups))}


def scan(path: Path, source: Path, now=None):
    now = time.time_ns() if now is None else now
    with locked_ledger(path):
        ledger = read_ledger(path) if path.exists() else new_ledger(source, now)
        if Path(ledger["source_path"]).resolve() != source.resolve():
            raise ValueError("Ledger source differs from requested source.")
        result = scan_state(ledger, inventory_sources(ledger), now)
        reconcile_content(ledger)
        sync_batch(ledger, now)
        save_ledger(path, ledger)
    return {**result, **summary(ledger, now)}


def eligible(ledger, key, now, require_main=True):
    group = ledger["groups"][key]
    entries = [ledger["files"][name] for name in group["files"]]
    if require_main and not any(item["role"] == "main" for item in entries):
        return False
    return bool(entries) and all(item["size"] > 0 and item["observations"] >= 2
        and item["last_observed_ns"] - item["same_since_ns"] >= 60 * SECOND
        and now - max(item["birthtime_ns"], item["mtime_ns"]) >= 120 * SECOND for item in entries)


def priority_index(ledger):
    """Build once per queue/report operation; never change the stored ledger."""
    policy = ledger.get("selection_policy") or {"mode": "arrival_order"}
    mode = policy.get("mode")
    if mode == "arrival_order":
        return {}
    if mode != "evidence_richness" or policy.get("require_screened") is not True:
        raise ValueError("Invalid stored selection policy; explicitly set a validated policy before new selection.")
    return {row["group_id"]: row for row in policy["rankings"]}


def priority_state(ledger, key, rankings=None):
    """Describe selection coverage separately from file stability and review."""
    group = ledger["groups"][key]
    mode = (ledger.get("selection_policy") or {}).get("mode", "arrival_order")
    rankings = priority_index(ledger) if rankings is None else rankings
    state = {"mode": mode, "status": "arrival_order", "screened": False,
             "eligible_for_selection": True, "score": None,
             "source_generation": group["generation"], "ranked_source_generation": None}
    if group.get("alias_of") or canonical_group(ledger, key) != key:
        return {**state, "status": "alias", "eligible_for_selection": False}
    if mode == "arrival_order":
        return state
    if mode != "evidence_richness":
        raise ValueError("Invalid stored selection policy mode.")
    row = rankings.get(key)
    if row is None:
        return {**state, "status": "pending_unranked", "eligible_for_selection": False}
    state["ranked_source_generation"] = row["source_generation"]
    if row["source_generation"] != group["generation"]:
        return {**state, "status": "pending_source_changed", "eligible_for_selection": False}
    return {**state, "status": "screened", "screened": True, "score": row["score"]}


def claimable(ledger, key, now, require_main=True, rankings=None):
    """New claims require both stable files and current priority coverage."""
    return (priority_state(ledger, key, rankings)["eligible_for_selection"]
            and eligible(ledger, key, now, require_main=require_main))


def set_priority(path: Path, policy, now=None, expected_ledger_sha256=None):
    """Validate and atomically activate explicit selection policy under the lock."""
    now = time.time_ns() if now is None else now
    with locked_ledger(path):
        if expected_ledger_sha256 is not None:
            if not isinstance(expected_ledger_sha256, str) or not re.fullmatch(r'[0-9a-f]{64}', expected_ledger_sha256):
                raise ValueError('Expected ledger SHA256 must be a lowercase SHA256 digest.')
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected_ledger_sha256:
                raise RuntimeError('Ledger changed before priority activation; refresh the partition and proposal.')
        ledger = read_ledger(path)
        if not isinstance(policy, dict):
            raise ValueError("Priority policy must be an object.")
        mode = policy.get("mode")
        if mode == "arrival_order":
            validated = {"mode": mode}
        elif mode == "evidence_richness":
            if policy.get("require_screened") is not True:
                raise ValueError("Evidence priority requires require_screened=true.")
            report_value = policy.get("source_report")
            if not isinstance(report_value, str) or not report_value.strip():
                raise ValueError("Priority policy requires an absolute source_report path.")
            report_path = Path(report_value)
            if not report_path.is_absolute() or not report_path.is_file():
                raise ValueError("Priority source_report must be an existing absolute file path.")
            digest = policy.get("source_report_sha256")
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
                raise ValueError("Priority source_report_sha256 must be a SHA256 digest.")
            if hashlib.sha256(report_path.read_bytes()).hexdigest() != digest.lower():
                raise ValueError("Priority source report SHA256 does not match.")
            screened_at = policy.get("screened_at")
            try:
                parsed_time = dt.datetime.fromisoformat(screened_at.replace("Z", "+00:00"))
                if parsed_time.utcoffset() is None:
                    raise ValueError("Timezone required")
            except (AttributeError, TypeError, ValueError) as exc:
                raise ValueError("screened_at must be an ISO8601 timestamp with timezone.") from exc
            rows = policy.get("rankings")
            if not isinstance(rows, list):
                raise ValueError("Priority rankings must be a list.")
            rankings, seen = [], set()
            for row in rows:
                if not isinstance(row, dict):
                    raise ValueError("Each priority ranking must be an object.")
                key = row.get("group_id")
                if not isinstance(key, str) or key not in ledger["groups"]:
                    raise ValueError("Priority ranking has an unknown group_id.")
                if key in seen:
                    raise ValueError("Priority rankings require unique group IDs.")
                if canonical_group(ledger, key) != key or ledger["groups"][key].get("alias_of"):
                    raise ValueError("Priority ranking must use a nonalias canonical group ID: " + key)
                score = row.get("score")
                try:
                    finite = type(score) in (int, float) and math.isfinite(score)
                except OverflowError:
                    finite = False
                if not finite:
                    raise ValueError("Priority scores must be finite numbers, not Boolean values.")
                generation = row.get("source_generation")
                if type(generation) is not int or generation != ledger["groups"][key]["generation"]:
                    raise ValueError("Priority source_generation is stale or invalid for " + key)
                seen.add(key)
                rankings.append({"group_id": key, "score": score, "source_generation": generation})
            validated = {"mode": mode, "source_report": str(report_path.resolve()),
                         "source_report_sha256": digest.lower(), "screened_at": screened_at,
                         "require_screened": True, "rankings": rankings}
        else:
            raise ValueError("Priority mode must explicitly be evidence_richness or arrival_order.")
        validated["applied_at"] = iso(now)
        ledger["selection_policy"] = validated
        save_ledger(path, ledger)
    return {"selection_policy": validated, "current_batch_preserved": True,
            "active_review_claims": len(active_claims(ledger)),
            "note": "Selection priority only; no source review status or arrival order changed."}


def queued(ledger):
    rankings = priority_index(ledger)
    def order(pair):
        key, group = pair
        state = priority_state(ledger, key, rankings)
        return (not state["eligible_for_selection"], -(state["score"] or 0), group["queue_order"], key)
    return [key for key, group in sorted(ledger["groups"].items(), key=order)
            if not group.get("alias_of") and (group["needs_recheck"] or group["review"]["status"] not in TERMINAL_STATUSES)]


def summary(ledger, now=None):
    now = time.time_ns() if now is None else now
    pending = queued(ledger)
    rankings = priority_index(ledger)
    next_key = next((key for key in pending if claimable(ledger, key, now, rankings=rankings)), None)
    priority_counts = {}
    for key in pending:
        status = priority_state(ledger, key, rankings)["status"]
        priority_counts[status] = priority_counts.get(status, 0) + 1
    main_groups = sum(any(ledger["files"][name]["role"] == "main" for name in group["files"]) for group in ledger["groups"].values())
    result = {"source_path": ledger["source_path"], "groups": len(ledger["groups"]), "main_paper_groups": main_groups,
            "groups_without_main_pdf": len(ledger["groups"]) - main_groups,
            "present_files": sum(item["exists"] for item in ledger["files"].values()),
            "pending_groups": len(pending), "needs_recheck": sum(g["needs_recheck"] for g in ledger["groups"].values()),
            "current_paper": ledger["current_paper"], "next_eligible_group": next_key,
            "last_scan_at": ledger["last_scan_at"]}
    claims = active_claims(ledger)
    claimed_keys = {claim["group_id"] for claim in claims}
    result.update(current_batch=ledger.get("current_batch"), active_papers=claims,
                  active_review_claims=len(claims),
                  waiting_review_scopes=sum(key not in claimed_keys for key in pending),
                  selection_policy_mode=(ledger.get("selection_policy") or {}).get("mode", "arrival_order"),
                  priority_status_counts=priority_counts,
                  priority_pending_unscreened_scopes=sum(priority_counts.get(status, 0) for status in ("pending_unranked", "pending_source_changed")),
                  priority_pending_waiting_scopes=sum(key not in claimed_keys and not priority_state(ledger, key, rankings)["eligible_for_selection"] for key in pending))
    if ledger.get("schema_version", 1) >= 2:
        present = [item for item in ledger["files"].values() if item["exists"]]
        known = [item["sha256"] for item in present if item.get("sha256")]
        result.update(source_paths=ledger["source_paths"], source_document_copies={alias: sum(item.get("source_id") == alias for item in present) for alias in ledger["source_paths"]},
            canonical_review_units=sum(not g.get("alias_of") for g in ledger["groups"].values()),
            confirmed_duplicate_main_aliases=sum(bool(g.get("alias_of")) for g in ledger["groups"].values()),
            known_unique_document_hashes=len(set(known)), confirmed_duplicate_document_copies=len(known)-len(set(known)),
            document_copies_not_yet_hashed=len(present)-len(known), normalized_doi_candidates=len(ledger.get("doi_candidate_index", {})),
            distinct_paper_total=None, count_note="Review units and DOI candidates are worklist scopes, not a verified unique-paper/material/recipe total; unconfirmed cross-folder duplicates remain unresolved.")
        result.pop("groups_without_main_pdf", None)
        result["groups_without_main_candidate"] = sum(not group.get("alias_of") and not any(ledger["files"][name]["role"] == "main" for name in group["files"]) for group in ledger["groups"].values())
        result["ambiguous_role_document_copies"] = sum(bool(item.get("role_ambiguous")) for item in present)
    return result


def claim(path: Path, reviewer: str, group_id=None, now=None, allow_incomplete_bundle=False):
    now = time.time_ns() if now is None else now
    with locked_ledger(path):
        ledger = read_ledger(path)
        if ledger.get("current_batch"):
            raise RuntimeError("Batch already active; use claim-batch with its owner to resume the entire batch.")
        current = ledger["current_paper"]
        if current:
            if current["reviewer"] != reviewer:
                raise RuntimeError(f"Single reviewer already active: {current['reviewer']} / {current['group_id']}")
            if group_id and group_id != current["group_id"]:
                raise RuntimeError("Finish or explicitly checkpoint the current paper before claiming another.")
            return {**current, "resumed": True, "needs_recheck": ledger["groups"][current["group_id"]]["needs_recheck"]}
        rankings = priority_index(ledger)
        key = canonical_group(ledger, group_id) if group_id else next((key for key in queued(ledger) if claimable(ledger, key, now, rankings=rankings)), None)
        if allow_incomplete_bundle and not group_id:
            raise ValueError("Incomplete-bundle review must explicitly select a group")
        if key is None or not eligible(ledger, key, now, require_main=not allow_incomplete_bundle):
            raise RuntimeError("No eligible selected group: scan twice >=60 seconds apart and require file age >=120 seconds.")
        if not priority_state(ledger, key, rankings)["eligible_for_selection"]:
            raise RuntimeError("Selected group needs current source screening before a new priority claim.")
        group = ledger["groups"][key]
        if group["review"]["status"] in TERMINAL_STATUSES and not group["needs_recheck"]:
            raise RuntimeError("This group is already manually completed and unchanged.")
        if group["review"]["status"] in TERMINAL_STATUSES:
            group["review"]["history"].append({"previous_status": group["review"]["status"], "reopened_at": iso(now)})
        group["review"].update(status="in_progress", reviewer=reviewer, updated_at=iso(now))
        current = {"group_id": key, "reviewer": reviewer, "claimed_at": iso(now), "generation_at_claim": group["generation"]}
        if allow_incomplete_bundle:
            current["allow_incomplete_bundle"] = True
        ledger["current_paper"] = current
        save_ledger(path, ledger)
        return {**current, "resumed": False, "files": group["files"], "needs_recheck": group["needs_recheck"]}


def claim_batch(path: Path, reviewer: str, size=MAX_BATCH_SIZE, now=None, refill=False):
    """Resume a batch; explicitly requested refill uses free active-paper slots.

    Historical completed members remain attached to their original audit/release.
    The size bound applies to active papers, never simultaneous agent count.
    """
    if type(size) is not int or not 1 <= size <= MAX_BATCH_SIZE:
        raise ValueError(f"Batch size must be between 1 and {MAX_BATCH_SIZE}.")
    now = time.time_ns() if now is None else now
    with locked_ledger(path):
        ledger = read_ledger(path)
        batch = ledger.get("current_batch")
        current = ledger.get("current_paper")
        owner = batch["reviewer"] if batch else (current or {}).get("reviewer")
        if owner is not None and owner != reviewer:
            raise RuntimeError(f"Single reviewer already active: {owner}")
        resumed = bool(batch or current)
        if batch:
            # Reopened or blocked members retain their original reservation.
            sync_batch(ledger, now)
            batch = ledger.get("current_batch")
        if not batch:
            current = ledger.get("current_paper")
            papers = [dict(current)] if current else []
            if not papers:
                rankings = priority_index(ledger)
                keys = [key for key in queued(ledger) if claimable(ledger, key, now, rankings=rankings)][:size]
                if not keys:
                    raise RuntimeError("No eligible groups: require stable files and current screening under the active selection policy.")
                for key in keys:
                    group = ledger["groups"][key]
                    review = group["review"]
                    if review["status"] in TERMINAL_STATUSES:
                        review["history"].append({"previous_status": review["status"], "reopened_at": iso(now)})
                    review.update(status="in_progress", reviewer=reviewer, updated_at=iso(now))
                    papers.append({"group_id": key, "reviewer": reviewer, "claimed_at": iso(now),
                                   "generation_at_claim": group["generation"]})
                resumed = False
            # A pre-existing single claim is a one-member batch: finish it first.
            sequence = ledger.get("next_batch_sequence", 1)
            ledger["next_batch_sequence"] = sequence + 1
            batch = {"batch_id": f"batch-{now}-{sequence}", "reviewer": reviewer, "claimed_at": iso(now),
                     "size_limit": size, "papers": papers}
            ledger["current_batch"] = batch
        sync_batch(ledger, now)
        if refill and ledger.get("current_batch"):
            batch = ledger["current_batch"]
            free_slots = max(0, size - len(active_claims(ledger)))
            existing = {p["group_id"] for p in batch["papers"]}
            rankings = priority_index(ledger)
            additions = [key for key in queued(ledger) if key not in existing
                         and claimable(ledger, key, now, rankings=rankings)][:free_slots]
            for key in additions:
                group = ledger["groups"][key]
                review = group["review"]
                if review["status"] in TERMINAL_STATUSES:
                    review["history"].append({"previous_status": review["status"], "reopened_at": iso(now)})
                review.update(status="in_progress", reviewer=reviewer, updated_at=iso(now))
                batch["papers"].append({"group_id": key, "reviewer": reviewer,
                    "claimed_at": iso(now), "generation_at_claim": group["generation"]})
            if additions:
                batch.setdefault("admissions", []).append({"at": iso(now), "group_ids": additions,
                    "reason": "Explicit rolling pipeline refill; earlier claims/audits/releases preserved."})
                batch["size_limit"] = max(batch["size_limit"], size)
            sync_batch(ledger, now)
        save_ledger(path, ledger)
        return {**batch, "resumed": resumed, "active_papers": active_claims(ledger),
                "active_review_claims": len(active_claims(ledger)),
                "refill_policy": "Explicit --refill may admit screened papers into free active slots; existing paper audits and releases are retained."}


def fingerprint(path: Path, reviewer: str, now=None, group_id=None):
    now = time.time_ns() if now is None else now
    with locked_ledger(path):
        ledger = read_ledger(path)
        current = selected_claim(ledger, reviewer, group_id, "Fingerprint")
        key = current["group_id"]
        group = ledger["groups"][key]
        if not eligible(ledger, key, now, require_main=not current.get("allow_incomplete_bundle", False)):
            raise RuntimeError("Selected group has not reached file stability thresholds.")
        hashes = {}
        for name in group["files"]:
            file = file_path(ledger, name)
            before = stat_info(file)
            if signature(before) != signature(ledger["files"][name]):
                raise RuntimeError("File changed since scan; rescan before hashing: " + name)
            h = hashlib.sha256()
            with file.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    h.update(block)
            if signature(stat_info(file)) != signature(before):
                raise RuntimeError("File changed during hashing: " + name)
            hashes[name] = h.hexdigest()
        siblings = sorted(name for name, item in inventory_sources(ledger).items() if item["group_id"] == key)
        if siblings != group["files"]:
            raise RuntimeError("Group membership changed during hashing; rescan.")
        # Content bundle identity ignores filenames; main hash also catches renamed duplicates.
        bundle = hashlib.sha256(json.dumps(sorted(set(hashes.values())), separators=(",", ":")).encode()).hexdigest()
        main_hashes = sorted({hashes[name] for name in hashes if ledger["files"][name]["role"] == "main"})
        duplicates = []
        for other, data in ledger["groups"].items():
            old = data.get("fingerprint", {})
            if other != key and old.get("generation") == data["generation"]:
                if old.get("bundle_sha256") == bundle or set(main_hashes).intersection(old.get("main_sha256", [])):
                    duplicates.append({"group_id": other, "same_bundle": old.get("bundle_sha256") == bundle,
                                       "same_main": bool(set(main_hashes).intersection(old.get("main_sha256", [])))})
        group["fingerprint"] = {"generation": group["generation"], "created_at": iso(now), "files": hashes,
                                 "bundle_sha256": bundle, "main_sha256": main_hashes, "duplicates": duplicates,
                                 "unique_content_files": {digest: sorted(name for name in hashes if hashes[name] == digest) for digest in sorted(set(hashes.values()))}}
        for name, digest in hashes.items():
            ledger["files"][name]["sha256"] = digest
            ledger["files"][name]["hash_evidence"] = {"kind": "selected_group_actual_sha256", "at": iso(now), "generation": group["generation"]}
        reconcile_content(ledger)
        sync_batch(ledger, now)
        if group["fingerprint"]["generation"] != group["generation"]:
            group["fingerprint"]["reconciliation_requires_refingerprint"] = True
        save_ledger(path, ledger)
        return {"group_id": key, **group["fingerprint"]}


def checkpoint(path: Path, reviewer: str, status="in_progress", data=None, note=None, now=None, milestones=None, group_id=None):
    now = time.time_ns() if now is None else now
    if status not in REVIEW_STATUSES - {"queued"}:
        raise ValueError("Invalid checkpoint status.")
    with locked_ledger(path):
        ledger = read_ledger(path)
        current = selected_claim(ledger, reviewer, group_id, "Checkpoint")
        group = ledger["groups"][current["group_id"]]
        review = group["review"]
        if data is not None:
            if not isinstance(data, dict):
                raise ValueError("Checkpoint data must be a JSON object.")
            review["checkpoint"].update(data)
        screening_closure = status == "no_synthesis_recipe"
        if screening_closure:
            validate_screening(review["checkpoint"].get("screening"), group, reviewer, path.parent)
        if milestones:
            for stage, record in milestones.items():
                if stage not in MILESTONES or not isinstance(record, dict) or record.get("status") not in {"pending", "partial", "complete", "not_applicable"}:
                    raise ValueError("Invalid milestone stage/status")
                evidence = record.get("evidence", [])
                if not isinstance(evidence, list) or not all(isinstance(ref, str) and ref.strip() for ref in evidence):
                    raise ValueError("Milestone evidence must be a list of nonempty references")
                if record["status"] in {"complete", "not_applicable"} and not evidence:
                    raise ValueError("Completed/not-applicable milestones require evidence references")
                if record["status"] == "not_applicable" and (stage == "audit" or (stage == "read" and not screening_closure)
                        or not isinstance(record.get("note"), str) or not record["note"].strip()):
                    raise ValueError("Audit cannot be skipped; read requires full review or audited screening; not-applicable milestones require a reason")
                review.setdefault("milestones", pending_milestones())[stage] = {**record, "evidence": evidence, "updated_at": iso(now), "generation": group["generation"]}
        if status in TERMINAL_STATUSES:
            stamp = group.get("fingerprint", {})
            if stamp.get("generation") != group["generation"]:
                raise RuntimeError("Manual completion requires a fingerprint of the current file generation.")
            if ledger.get("schema_version", 1) >= 2 or screening_closure:
                stages = review.get("milestones", {})
                unfinished = [stage for stage in MILESTONES if stages.get(stage, {}).get("status") not in {"complete", "not_applicable"}
                    or stages[stage].get("generation") != group["generation"] or not stages[stage].get("evidence")]
                if unfinished:
                    raise RuntimeError("Current-generation evidence milestones incomplete: " + ", ".join(unfinished))
                if screening_closure:
                    if stages["audit"]["status"] != "complete":
                        raise ValueError("Independent screening audit milestone must be complete.")
                    for stage in MILESTONES:
                        evidence_files_exist(stages[stage]["evidence"], path.parent)
            live = inventory_sources(ledger)
            siblings = {name: item for name, item in live.items() if item["group_id"] == current["group_id"]}
            if set(siblings) != set(group["files"]) or any(signature(item) != signature(ledger["files"][name]) for name, item in siblings.items()):
                raise RuntimeError("Source changed since fingerprint; rescan/review before completion.")
        review.update(status=status, reviewer=reviewer, updated_at=iso(now))
        review["history"].append({"status": status, "at": iso(now), "note": note})
        if status in TERMINAL_STATUSES:
            group["needs_recheck"] = False
            review["completed_generation"] = group["generation"]
            if not ledger.get("current_batch"):
                ledger["current_paper"] = None
        sync_batch(ledger, now)
        # A blocked paper retains its claim/checkpoint until the same reviewer resumes it.
        save_ledger(path, ledger)
        return {"group_id": current["group_id"], "status": status, "checkpoint": review["checkpoint"],
                "claim_retained": any(claim["group_id"] == current["group_id"] for claim in active_claims(ledger)),
                "active_review_claims": len(active_claims(ledger)), "batch_retained": bool(ledger.get("current_batch"))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("scan")
    sub.add_parser("status")
    priority = sub.add_parser("set-priority", help="Explicitly activate a hash-bound evidence ranking, or restore arrival_order; preserves active claims")
    priority.add_argument("--data", type=Path, required=True, help="Policy JSON; evidence_richness requires absolute source_report, matching SHA256, screened_at, require_screened=true and current-generation rankings. See module docstring.")
    migrate = sub.add_parser("migrate-two-folders")
    migrate.add_argument("--legacy", type=Path, default=DEFAULT_LEGACY)
    migrate.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    migrate.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    c = sub.add_parser("claim")
    c.add_argument("--reviewer", required=True)
    c.add_argument("--group")
    c.add_argument("--allow-incomplete-bundle", action="store_true", help="Explicitly review a stable main-missing/ambiguous group; never infer a complete paper scope")
    b = sub.add_parser("claim-batch", help="Claim up to five eligible scopes in active policy order, or resume an unfinished fixed batch")
    b.add_argument("--reviewer", required=True)
    b.add_argument("--size", type=int, default=MAX_BATCH_SIZE)
    b.add_argument("--refill", action="store_true", help="Explicitly fill free active-paper slots; preserves all earlier batch members and their audits")
    f = sub.add_parser("fingerprint")
    f.add_argument("--reviewer", required=True)
    f.add_argument("--group", help="Exact claimed group ID; required in batch mode")
    p = sub.add_parser("checkpoint")
    p.add_argument("--reviewer", required=True)
    p.add_argument("--group", help="Exact claimed group ID; required in batch mode")
    p.add_argument("--status", choices=sorted(REVIEW_STATUSES - {"queued"}), default="in_progress")
    p.add_argument("--data", type=Path, help="Private JSON object to merge into the current checkpoint")
    p.add_argument("--note")
    p.add_argument("--milestones", type=Path, help="JSON object keyed by read/extract/audit/integrate/publish with status and evidence references")
    args = parser.parse_args()
    try:
        if args.command == "scan":
            result = scan(args.ledger, args.source)
        elif args.command == "status":
            result = summary(read_ledger(args.ledger))
        elif args.command == "set-priority":
            result = set_priority(args.ledger, json.loads(args.data.read_text(encoding="utf-8")))
        elif args.command == "migrate-two-folders":
            result = upgrade_two_sources(args.ledger, args.legacy, args.manifest, args.inventory)
        elif args.command == "claim":
            result = claim(args.ledger, args.reviewer, args.group, allow_incomplete_bundle=args.allow_incomplete_bundle)
        elif args.command == "claim-batch":
            result = claim_batch(args.ledger, args.reviewer, args.size, refill=args.refill)
        elif args.command == "fingerprint":
            result = fingerprint(args.ledger, args.reviewer, group_id=args.group)
        else:
            data = json.loads(args.data.read_text(encoding="utf-8")) if args.data else None
            stages = json.loads(args.milestones.read_text(encoding="utf-8")) if args.milestones else None
            result = checkpoint(args.ledger, args.reviewer, args.status, data, args.note, milestones=stages, group_id=args.group)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError, RuntimeError, KeyError) as exc:
        parser.exit(1, f"Queue error: {exc}\n")


if __name__ == "__main__":
    main()
