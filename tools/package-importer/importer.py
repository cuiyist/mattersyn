from __future__ import annotations

"""Hash-pinned, additive importer for accepted MatterSyn paper packages.

This first fixture supports the frozen Thomson et al. Bi2S3 package. It writes
only a new, private overlay directory; it never writes to --checkout. Existing
aggregate JSON files are emitted as compare-and-swap replacement candidates,
bound to their exact base hashes. A root integrator must apply them only to a
private checkout at the recorded base, then run repository builders and the
release gates.
"""

import argparse
import collections
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path, PurePosixPath

# The checkout is input-only. Never create __pycache__ files there, even when
# this CLI is run without Python's -B flag.
sys.dont_write_bytecode = True


HERE = Path(__file__).resolve().parent
CONTRACT_PATH = HERE / "contracts" / "thomson2010-bi2s3.json"


class ImportRejected(ValueError):
    pass


def digest_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def digest_file(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def write_bytes(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)


def is_control_artifact(relative_path: str) -> bool:
    return relative_path.startswith("integration-metadata/") or relative_path == "publication/asset-rights-registry.delta.json"


def posix_relative(value: str) -> PurePosixPath:
    # PurePosixPath normalizes repeated separators and dot segments, so inspect
    # the unnormalized spelling first and fail closed on ambiguous inputs.
    if not isinstance(value, str) or not value or value.startswith("/") or any(
        part in {"", ".", ".."} for part in value.split("/")
    ):
        raise ImportRejected(f"Unsafe package-relative path: {value!r}")
    if "\\" in value or ":" in value:
        raise ImportRejected(f"Non-portable package-relative path: {value!r}")
    p = PurePosixPath(value)
    if p.is_absolute():
        raise ImportRejected(f"Unsafe package-relative path: {value!r}")
    return p


def contained(root: Path, candidate: Path) -> bool:
    root_r = root.resolve()
    cand_r = candidate.resolve()
    return cand_r == root_r or root_r in cand_r.parents


def require_no_link_components(root: Path, rel: PurePosixPath) -> Path:
    current = root
    for component in rel.parts:
        current = current / component
        if current.exists() and current.is_symlink():
            raise ImportRejected(f"Symlinked package path is not accepted: {rel.as_posix()}")
    if not contained(root, current):
        raise ImportRejected(f"Package path escapes root: {rel.as_posix()}")
    return current


def assert_hash(path: Path, expected: str, label: str) -> None:
    if not path.is_file():
        raise ImportRejected(f"Missing {label}")
    actual = digest_file(path)
    if actual != expected:
        raise ImportRejected(f"Stale {label}: expected {expected}, got {actual}")


def verify_contract_checkout(checkout: Path, contract: dict) -> dict:
    checkout = checkout.resolve(strict=True)
    head = subprocess.check_output(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True
    ).strip()
    expected_head = contract["repository"]["expected_head"]
    if head != expected_head:
        raise ImportRejected(f"Checkout HEAD mismatch: expected {expected_head}, got {head}")
    dependencies = {}
    for rel, expected in contract["repository"]["files"].items():
        safe = posix_relative(rel)
        path = require_no_link_components(checkout, safe)
        assert_hash(path, expected, f"checkout dependency {rel}")
        dependencies[rel] = {"sha256": expected, "bytes": path.stat().st_size}
    policy_delta = contract["repository"]["operational_policy_delta"]
    policy_rel = posix_relative(policy_delta["path"])
    base_policy_raw = subprocess.check_output([
        "git", "-C", str(checkout), "show",
        f"{policy_delta['base_head']}:{policy_rel.as_posix()}",
    ])
    if digest_bytes(base_policy_raw) != policy_delta["base_sha256"]:
        raise ImportRejected("Operational policy base blob differs from the reviewed contract")
    current_policy_path = require_no_link_components(checkout, policy_rel)
    current_policy_raw = current_policy_path.read_bytes()
    if digest_bytes(current_policy_raw) != policy_delta["worktree_sha256"]:
        raise ImportRejected("Operational policy worktree blob differs from the reviewed two-rule delta")
    base_policy, current_policy = json.loads(base_policy_raw), json.loads(current_policy_raw)
    add_ids = set(policy_delta["added_rule_ids"])
    base_rules = base_policy.get("path_rules", [])
    current_rules = current_policy.get("path_rules", [])
    added_rules = [rule for rule in current_rules if rule.get("rule_id") in add_ids]
    retained_rules = [rule for rule in current_rules if rule.get("rule_id") not in add_ids]
    if len(added_rules) != len(add_ids) or added_rules != policy_delta["added_rules"]:
        raise ImportRejected("Operational policy does not contain exactly the two reviewed path-rule additions")
    if len(retained_rules) != len(current_rules) - len(add_ids) or retained_rules != base_rules:
        raise ImportRejected("Operational policy contains changes beyond the two reviewed path-rule additions")
    base_without_rules = {k: v for k, v in base_policy.items() if k != "path_rules"}
    current_without_rules = {k: v for k, v in current_policy.items() if k != "path_rules"}
    if base_without_rules != current_without_rules:
        raise ImportRejected("Operational policy changed outside the reviewed path-rule additions")
    status = subprocess.check_output(
        ["git", "-C", str(checkout), "status", "--porcelain=v1", "--untracked-files=no"],
        text=True,
    )
    # Concurrent project-memory/build changes are allowed only when none of the
    # pinned importer dependencies changed; record the status without disclosing
    # absolute machine paths in the staged public-facing payload.
    return {
        "head": head,
        "dependency_files": dependencies,
        "tracked_worktree_dirty": bool(status.strip()),
        "tracked_worktree_status_lines": len([line for line in status.splitlines() if line.strip()]),
        "operational_policy_delta": {
            "path": policy_rel.as_posix(),
            "base_sha256": policy_delta["base_sha256"],
            "worktree_sha256": policy_delta["worktree_sha256"],
            "added_rule_ids": sorted(add_ids),
            "only_reviewed_rules_added": True,
        },
    }


def verify_evidence(evidence_root: Path, source_pdf: Path, contract: dict) -> dict:
    package = contract["package"]
    assert_hash(source_pdf, package["source_pdf_sha256"], "original main PDF")
    verified = {"source_pdf_sha256": digest_file(source_pdf), "receipts": {}}
    fixed = {
        "author_freeze": ("author-package-r3/freeze-manifest.json", package["author_freeze_sha256"]),
        "reader_freeze": ("reader-integration-r3/freeze-manifest.json", package["reader_freeze_sha256"]),
        "chemical_freeze": ("chemical-display-r1/freeze.json", package["chemical_freeze_sha256"]),
    }
    for key, (rel, expected) in fixed.items():
        path = evidence_root / Path(*posix_relative(rel).parts)
        assert_hash(path, expected, key.replace("_", " "))
        verified["receipts"][key] = {"relative_path": rel, "sha256": expected}
    for key, item in package["audits"].items():
        rel = posix_relative(item["path"])
        path = require_no_link_components(evidence_root, rel)
        assert_hash(path, item["sha256"], f"independent audit receipt {key}")
        verified["receipts"][key] = {"relative_path": rel.as_posix(), "sha256": item["sha256"]}
    return verified


def verify_bundle(package_dir: Path, contract: dict) -> tuple[dict, dict]:
    mf_rel = posix_relative(contract["paths"]["bundle_manifest"])
    mf_path = require_no_link_components(package_dir, mf_rel)
    assert_hash(mf_path, contract["package"]["bundle_manifest_sha256"], "frozen overlay manifest")
    manifest = read_json(mf_path)
    listed = manifest.get("files")
    if not isinstance(listed, list) or not listed:
        raise ImportRejected("Frozen overlay manifest has no file inventory")
    seen = set()
    verified_files = {}
    for entry in listed:
        rel = posix_relative(entry.get("path", ""))
        key = rel.as_posix()
        if key in seen:
            raise ImportRejected(f"Duplicate manifest path: {key}")
        seen.add(key)
        path = require_no_link_components(package_dir, rel)
        if not path.is_file() or path.stat().st_size != entry.get("bytes"):
            raise ImportRejected(f"Missing or wrong-sized frozen input: {key}")
        actual = digest_file(path)
        if actual != entry.get("sha256"):
            raise ImportRejected(f"Frozen input hash mismatch: {key}")
        verified_files[key] = {"sha256": actual, "bytes": path.stat().st_size}
    actual_files = {
        p.relative_to(package_dir.resolve()).as_posix()
        for p in package_dir.rglob("*")
        if p.is_file()
    }
    expected_files = seen | {mf_rel.as_posix()}
    if actual_files != expected_files:
        extras = sorted(actual_files - expected_files)
        missing = sorted(expected_files - actual_files)
        raise ImportRejected(f"Bundle file set differs from freeze: extras={extras}, missing={missing}")
    return manifest, verified_files


def reader_figure_counts(payload: dict) -> tuple[int, int]:
    # The summary counts figure identities across both the source gallery and
    # per-record Reader cards. Those two views deliberately share figure IDs.
    figure_has_asset: dict[tuple[str, str], bool] = {}
    for figures in payload.get("figures_by_source", {}).values():
        for figure in figures:
            source_id, figure_id = figure.get("source_id"), figure.get("id")
            if not source_id or not figure_id:
                raise ImportRejected("Reader source gallery contains an unidentified figure")
            key = (source_id, figure_id)
            figure_has_asset[key] = figure_has_asset.get(key, False) or bool(figure.get("public_asset"))
    for row in payload.get("records", {}).values():
        for figure in row.get("figures", []):
            source_id, figure_id = figure.get("source_id"), figure.get("id")
            if not source_id or not figure_id:
                raise ImportRejected("Reader record contains an unidentified figure")
            key = (source_id, figure_id)
            figure_has_asset[key] = figure_has_asset.get(key, False) or bool(figure.get("public_asset"))
    return len(figure_has_asset), sum(figure_has_asset.values())


def merge_reader(
    base: dict,
    delta: dict,
    record: dict,
    reader_dir: Path,
    base_route_count: int,
    base_route_source_ids: set[str],
) -> tuple[dict, dict]:
    rid = record["record_id"]
    source_id = record["lineage"]["source_group"]
    if rid in base["records"]:
        raise ImportRejected(f"Reader record already exists: {rid}")
    if source_id in base["figures_by_source"]:
        raise ImportRejected(f"Reader source group already exists: {source_id}")
    delta_records = delta.get("records", {})
    delta_figures = delta.get("figures_by_source", {})
    if set(delta_records) != {rid} or set(delta_figures) != {source_id}:
        raise ImportRejected("Reader delta must contain exactly the canonical record and its source gallery")
    row = delta_records[rid]
    if row.get("source_id") != source_id or row.get("material_formula") != record["material"]["formula"]:
        raise ImportRejected("Reader record identity/material does not match canonical record")
    if not isinstance(row.get("figures"), list) or not isinstance(row.get("scopeLabel"), str):
        raise ImportRejected("Reader row is missing visible scope or per-record figure list")
    for figure in row["figures"]:
        if figure.get("source_id") != source_id:
            raise ImportRejected("Per-record figure cites a different source group")
        if rid not in figure.get("record_links", []):
            raise ImportRejected(f"Reader figure is not bound to this record: {figure.get('id')}")
    for figure in delta_figures[source_id]:
        if figure.get("source_id") != source_id:
            raise ImportRejected("Source gallery contains a foreign source ID")

    # Reuse the current repository's material slug function and reader validator.
    scripts = reader_dir / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    import build_atlas
    import build_reader_metadata
    if not build_atlas.synthesis_route(record):
        raise ImportRejected("Canonical record does not qualify as a Reader synthesis route")
    build_reader_metadata.validate_reader_view(rid, row)
    formula = record["material"]["formula"]
    material_id = build_atlas.slug(formula)
    if material_id in base["materials"]:
        raise ImportRejected(f"Material Reader hub already exists: {material_id}")

    merged = json.loads(json.dumps(base))
    merged["records"][rid] = row
    merged["figures_by_source"][source_id] = delta_figures[source_id]
    unique = {(f.get("source_id"), f.get("id")) for f in row["figures"]}
    property_unique = {
        (f.get("source_id"), f.get("id"))
        for f in row["figures"]
        if "property" in f.get("categories", [f.get("category")])
    }
    merged["materials"][material_id] = {
        "id": material_id,
        "formula": formula,
        "record_ids": [rid],
        "component_only": False,
        "scopeLabel": "Source-specific methods and samples are kept separate.",
        "source": {"data_path": f"dist/data/materials/{material_id}.json", "json_pointer": ""},
        "figure_count": len(unique),
        "property_figure_count": len(property_unique),
    }
    old_counts = base.get("counts", {})
    # Counts use the existing presentation-proposal definitions. Assert each
    # old field against the actual base rows before recalculating it.
    base_unique_figures, base_public_figures = reader_figure_counts(base)
    actual_base_counts = {
        "materials": len(base["materials"]),
        "routes": base_route_count,
        "source_groups": len(base_route_source_ids),
        "unique_figures": base_unique_figures,
        "full_readers": len(list((reader_dir / "data" / "paper-reviews").glob("*.json"))),
        "figures_with_public_asset": base_public_figures,
    }
    for key, val in actual_base_counts.items():
        if old_counts.get(key) != val:
            raise ImportRejected(f"Reader count baseline is stale for {key}: stored={old_counts.get(key)}, actual={val}")
    new_unique_figures, new_public_figures = reader_figure_counts(merged)
    merged["counts"].update({
        "materials": len(merged["materials"]),
        "routes": base_route_count + 1,
        "source_groups": len(base_route_source_ids | {source_id}),
        "unique_figures": new_unique_figures,
        "full_readers": actual_base_counts["full_readers"] + 1,
        "figures_with_public_asset": new_public_figures,
        # Selection/legacy counts are held constant; this accepted source is a
        # formal main-only review, not a legacy or selected-evidence reader.
    })
    return merged, {"material_hub_id": material_id, "new_material_reader_sha_pending": True}


def merge_chemical_registry(registry: dict, delta: dict) -> dict:
    out = json.loads(json.dumps(registry))
    existing = {x["id"] for x in out["entries"]}
    new = delta.get("entries", [])
    new_ids = [x.get("id") for x in new]
    if len(new_ids) != len(set(new_ids)) or existing.intersection(new_ids):
        raise ImportRejected("Chemical registry entry ID collision")
    if any(not x.get("id") or x.get("depictionKind") != "molecule" for x in new):
        raise ImportRejected("Chemical registry delta has an unsupported or incomplete identity entry")
    out["entries"].extend(new)
    kinds = collections.Counter(x.get("depictionKind", "unknown") for x in out["entries"])
    out["summary"]["entryCount"] = len(out["entries"])
    # The record and binding totals are refreshed after the exact record
    # binding merge below; existing aggregate fields are never nulled.
    out["summary"]["depictionKinds"] = dict(sorted(kinds.items()))
    out["summary"]["twoDimensionalModels"] = sum(bool(x.get("model2dPath")) for x in out["entries"])
    out["summary"]["rotatableThreeDimensionalModels"] = sum(bool(x.get("model3dPath")) for x in out["entries"])
    return out


def merge_chemical_bindings(
    bindings: dict,
    chemistry: dict,
    record: dict,
    record_sha: str,
    base_registry_sha: str,
    merged_registry_ids: set[str],
) -> tuple[dict, list[dict]]:
    out = json.loads(json.dumps(bindings))
    rid = record["record_id"]
    if rid in out["recordBindings"] or rid in out["sourceRecordSha256"]:
        raise ImportRejected(f"Chemical binding already exists for record: {rid}")
    if chemistry.get("source_record_sha256") != record_sha:
        raise ImportRejected("Chemical binding sidecar is stale against canonical record")
    if chemistry.get("current_registry_sha256") != base_registry_sha:
        raise ImportRejected("Chemical binding sidecar is stale against the exact base registry")
    material_bindings = chemistry.get("material_bindings", {})
    added_ids = set(chemistry.get("candidate_registry_ids_added", {}).values())
    bound_ids = set(material_bindings.values())
    if not bound_ids.issubset(merged_registry_ids):
        raise ImportRejected("Chemical binding refers to a missing registry identity")
    if not added_ids.issubset(merged_registry_ids):
        raise ImportRejected("Candidate chemical IDs are missing from the merged registry")
    out["recordBindings"][rid] = material_bindings
    out["bindingNotes"][rid] = chemistry.get("binding_notes", {})
    out["sourceRecordSha256"][rid] = record_sha
    return out, [
        {"record_id": rid, "source_record_sha256": record_sha, "material_bindings": material_bindings,
         "binding_notes": chemistry.get("binding_notes", {})}
    ]


def merge_solution_components(base: dict, record: dict, chemistry: dict) -> dict:
    out = json.loads(json.dumps(base))
    rid = record["record_id"]
    if any(x.get("record_id") == rid for x in out.get("contexts", [])):
        raise ImportRejected(f"Solution component context already exists: {rid}")
    by_material = {m["id"]: m for m in record.get("materials", [])}
    ids = chemistry.get("material_bindings", {})
    contexts = []
    for stock in record.get("stocks", []):
        components = []
        for component in stock.get("components", []):
            material_id = component["material_id"]
            if material_id not in ids:
                raise ImportRejected(f"Stock component lacks a reviewed registry binding: {material_id}")
            material = by_material[material_id]
            components.append({
                "registry_id": ids[material_id],
                "role": material.get("role", "source-reported stock component"),
                "viewOverrides": {},
            })
        contexts.append({
            "record_id": rid,
            "label": stock["name"],
            "scope": "Identity references only. Quantities and concentration reporting remain in the canonical record; no solution geometry is asserted.",
            "components": components,
        })
    if not contexts:
        return out
    existing_keys = {(x.get("record_id"), x.get("label")) for x in out["contexts"]}
    if any((x["record_id"], x["label"]) in existing_keys for x in contexts):
        raise ImportRejected("Solution component context label collision")
    out["contexts"].extend(contexts)
    return out


def patch_protocol_router(router: bytes, module: bytes, registration: dict) -> bytes:
    text = router.decode("utf-8")
    module_text = module.decode("utf-8")
    builder = registration["scene_builder"]
    art = registration["art_builder"]
    if f"export function {builder}" not in module_text or f"export function {art}" not in module_text:
        raise ImportRejected("Protocol module does not export the registered scene and art functions")
    import_line = registration["import_line"]
    if import_line in text or f"{builder}(o,r)" in text:
        raise ImportRejected("Protocol module already appears registered")
    replacements = [
        (registration["import_anchor"], import_line + "\n" + registration["import_anchor"], 1),
        ("const sourceArt=createYu1998Art(o,r)||", f"const sourceArt={art}(o,r)||createYu1998Art(o,r)||", 1),
        ("const yu=buildYu1998Scene(o,r),", f"const thomson={builder}(o,r),yu=buildYu1998Scene(o,r),", 1),
        ("el('p',yu?.caption||", f"el('p',thomson?.caption||yu?.caption||", 1),
        ("if(yu||costanzo||", "if(thomson||yu||costanzo||", 2),
    ]
    for old, new, expected_count in replacements:
        count = text.count(old)
        if count != expected_count:
            raise ImportRejected(f"Protocol registration anchor count must be {expected_count}, got {count}: {old[:80]}")
        text = text.replace(old, new)
    return text.encode("utf-8")


def verify_rights_delta(rights_delta: dict, bundle: Path, contract: dict, base_registry_sha: str) -> tuple[list[dict], dict[str, tuple[Path, str]]]:
    if rights_delta.get("base_registry_sha256") != base_registry_sha:
        raise ImportRejected("Rights delta is bound to another base rights registry")
    assets = rights_delta.get("assets", [])
    if len(assets) != 18:
        raise ImportRejected(f"Expected 18 independently mapped asset rights entries, found {len(assets)}")
    staged = {}
    seen_deliveries: set[tuple[str, str]] = set()
    for row in assets:
        digest = row.get("asset_hash")
        if not re.fullmatch(r"[0-9a-f]{64}", str(digest)):
            raise ImportRejected("Rights entry has invalid asset hash")
        paths = row.get("delivery_paths", [])
        by_repo = {p.get("repo"): p for p in paths}
        if set(by_repo) != {"mattersyn", "mattersyn-site"}:
            raise ImportRejected("Every delivered asset must have exact source and site paths")
        src_rel = posix_relative(by_repo["mattersyn"].get("path", ""))
        site_rel = posix_relative(by_repo["mattersyn-site"].get("path", ""))
        for repo_name, delivery in by_repo.items():
            key = (repo_name, posix_relative(delivery.get("path", "")).as_posix())
            if key in seen_deliveries:
                raise ImportRejected(f"Duplicate delivery path within rights delta: {key[0]} {key[1]}")
            seen_deliveries.add(key)
        prefix = PurePosixPath("recipe-atlas/static")
        if src_rel.parts[:2] != prefix.parts or PurePosixPath(*src_rel.parts[2:]) != site_rel:
            raise ImportRejected("Dual delivery paths are not a one-to-one source/site mapping")
        source_path = bundle.joinpath(*src_rel.parts)
        if not source_path.is_file() or digest_file(source_path) != digest:
            raise ImportRejected(f"Rights asset bytes do not match source delivery path {src_rel}")
        if source_path.stat().st_size != by_repo["mattersyn"].get("bytes") or source_path.stat().st_size != by_repo["mattersyn-site"].get("bytes"):
            raise ImportRejected(f"Rights asset size mismatch: {src_rel}")
        if site_rel.as_posix() in staged:
            raise ImportRejected(f"Duplicate site asset delivery path: {site_rel}")
        staged[site_rel.as_posix()] = (source_path, digest)
        cls = row.get("classification")
        status = row.get("rights", {}).get("status")
        if cls == "source_figure":
            if status != "user_directed_display" or row.get("rights", {}).get("copyright_permission_verified") is not False:
                raise ImportRejected("Source figure rights status must preserve user direction without claiming permission")
        elif cls in {"authored_diagram", "authored_molecule"}:
            if status != "not_source_derived":
                raise ImportRejected("Authored image rights classification is not source-derived")
        else:
            raise ImportRejected(f"Unsupported asset classification: {cls}")
    expected_classes = collections.Counter(x["classification"] for x in assets)
    if expected_classes != collections.Counter({"source_figure": 12, "authored_diagram": 2, "authored_molecule": 4}):
        raise ImportRejected(f"Asset category count differs from accepted package: {expected_classes}")
    return assets, staged


def require_absent(checkout: Path, relative_paths: list[str]) -> None:
    for raw in relative_paths:
        rel = posix_relative(raw)
        target = require_no_link_components(checkout, rel)
        if target.exists():
            raise ImportRejected(f"Refusing to overwrite an existing target: {raw}")


def build_overlay(checkout: Path, package_dir: Path, evidence_root: Path, source_pdf: Path, contract: dict) -> tuple[dict[str, bytes], dict]:
    p = contract["package"]
    manifest, package_files = verify_bundle(package_dir, contract)
    evidence = verify_evidence(evidence_root, source_pdf, contract)
    checkout_info = verify_contract_checkout(checkout, contract)

    def pfile(rel):
        return package_dir.joinpath(*posix_relative(rel).parts)

    preflight = read_json(pfile(contract["paths"]["preflight"]))
    digest_bindings = read_json(pfile(contract["paths"]["digest_bindings"]))
    record_path = package_dir / "recipe-atlas/data/records" / (p["record_id"] + ".json")
    review_path = package_dir / "recipe-atlas/data/paper-reviews" / (p["paper_id"] + ".json")
    record_raw, review_raw = record_path.read_bytes(), review_path.read_bytes()
    record, review = json.loads(record_raw), json.loads(review_raw)
    if digest_file(record_path) != p["record_sha256"] or digest_file(review_path) != p["review_sha256"]:
        raise ImportRejected("Canonical record or final Reader review hash differs from accepted closeout")
    if digest_bindings.get("record_sha256") != p["record_sha256"] or digest_bindings.get("paper_review_sha256") != p["review_sha256"]:
        raise ImportRejected("Source digest sidecar does not bind the frozen record and Reader review")
    if preflight.get("source", {}).get("author_freeze_sha256") != p["author_freeze_sha256"] or preflight.get("source", {}).get("reader_freeze_sha256") != p["reader_freeze_sha256"]:
        raise ImportRejected("Preflight source freeze dependencies differ from the contract")
    if preflight.get("source", {}).get("chemical_freeze_sha256") != p["chemical_freeze_sha256"]:
        raise ImportRejected("Chemical dependency freeze differs from the contract")
    if preflight.get("canonical", {}).get("training_eligible") is not False or preflight.get("canonical", {}).get("si_unverified") is not True:
        raise ImportRejected("Frozen preflight eligibility/SI missingness changed")

    scripts = checkout / "recipe-atlas" / "scripts"
    sys.path.insert(0, str(scripts))
    import dataset_lib
    import review_scope
    schema_errors = dataset_lib.validate_record(record)
    if schema_errors:
        raise ImportRejected(f"Canonical schema/DAG validation failed: {schema_errors}")
    if record.get("record_id") != p["record_id"] or record.get("lineage", {}).get("source_group") != p["paper_id"]:
        raise ImportRejected("Canonical IDs/source-group do not match contract")
    if record["sources"][0].get("doi", "").lower() != p["doi"].lower() or review.get("doi", "").lower() != p["doi"].lower():
        raise ImportRejected("Canonical/review DOI mismatch")
    scope = review_scope.source_review_scope(review)
    if scope["scope"] != review_scope.MAIN_ONLY or review.get("review_status") != "main_only_reviewed":
        raise ImportRejected("Expected reviewed supplied main only; SI remains unverified")
    docs = review.get("documents", [])
    if len(docs) != 1 or docs[0].get("role") != "main" or docs[0].get("sha256") != p["source_pdf_sha256"] or docs[0].get("page_count") != 11:
        raise ImportRejected("Paper review does not describe exactly the accepted 11-page main article")
    if review.get("training_eligible") is not False and review.get("training_status") != "ineligible":
        # In this schema the canonical record is authoritative for training; the
        # explicit sidecar marker remains optional across review revisions.
        if record.get("quality", {}).get("requested_tasks") != []:
            raise ImportRejected("Review scope unexpectedly declares training work")

    corpus = read_json(checkout / "recipe-atlas/data/corpus/library-source.json")
    if any(str(row.get("doi", "")).lower() == p["doi"].lower() for row in corpus.get("papers", [])):
        raise ImportRejected("DOI already exists in the indexed source library")
    existing_review_dois = []
    for path in (checkout / "recipe-atlas/data/paper-reviews").glob("*.json"):
        try:
            existing = read_json(path)
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        if str(existing.get("doi", "")).lower() == p["doi"].lower():
            existing_review_dois.append(path.name)
    if existing_review_dois:
        raise ImportRejected(f"DOI already has a paper review: {existing_review_dois}")

    # Establish the displayed route/group counters with the repository's own
    # route predicate rather than equating all canonical records with recipes.
    canonical_scripts = checkout / "recipe-atlas" / "scripts"
    if str(canonical_scripts) not in sys.path:
        sys.path.insert(0, str(canonical_scripts))
    import build_atlas
    canonical_record_dir = checkout / "recipe-atlas" / "data" / "records"
    base_canonical_records = [read_json(path) for path in canonical_record_dir.glob("*.json")]
    base_routes = [row for row in base_canonical_records if build_atlas.synthesis_route(row)]
    base_route_source_ids = {
        row.get("lineage", {}).get("source_group") for row in base_routes
        if row.get("lineage", {}).get("source_group")
    }

    # Repository scripts and review counts must come from the exact base
    # checkout, while the candidate row itself comes only from the frozen delta.
    reader_dir = checkout / "recipe-atlas"
    presentation_path = checkout / "recipe-atlas/data/reader-presentation-reviewed.json"
    registry_path = checkout / "recipe-atlas/static/assets/chemical-registry/registry.json"
    bindings_path = checkout / "recipe-atlas/static/assets/chemical-registry/bindings.json"
    solutions_path = checkout / "recipe-atlas/static/assets/chemical-registry/solution-components.json"
    rights_path = checkout / "publication/asset-rights-registry.json"
    expected_base = contract["repository"]["files"]
    base_paths = {
        "recipe-atlas/data/reader-presentation-reviewed.json": presentation_path,
        "recipe-atlas/static/assets/chemical-registry/registry.json": registry_path,
        "recipe-atlas/static/assets/chemical-registry/bindings.json": bindings_path,
        "recipe-atlas/static/assets/chemical-registry/solution-components.json": solutions_path,
        "publication/asset-rights-registry.json": rights_path,
    }
    for rel, path in base_paths.items():
        assert_hash(path, expected_base[rel], f"merge base {rel}")

    # Create-only checks cover all record/review/assets/module paths. Aggregate
    # JSON replacements are permitted only through the bound merge outputs.
    create_targets = [
        f"recipe-atlas/data/records/{p['record_id']}.json",
        f"recipe-atlas/data/paper-reviews/{p['paper_id']}.json",
        "recipe-atlas/static/thomson2010-protocol.mjs",
    ]

    delta_reader = read_json(pfile(contract["paths"]["presentation_delta"]))
    reader_merged, material_info = merge_reader(
        read_json(presentation_path), delta_reader, record, reader_dir,
        len(base_routes), base_route_source_ids,
    )
    reader_review_source = package_dir / "recipe-atlas/data/paper-reviews" / f"{p['paper_id']}.json"
    if digest_file(reader_review_source) != p["review_sha256"]:
        raise ImportRejected("Final Reader review is not the exact bound R3 review")

    registry = read_json(registry_path)
    registry_ids = {x["id"] for x in registry["entries"]}
    chem_binding = read_json(pfile(contract["paths"]["chemical_bindings"]))
    if chem_binding.get("current_registry_sha256") != expected_base["recipe-atlas/static/assets/chemical-registry/registry.json"]:
        raise ImportRejected("Reader chemistry bindings were prepared against a different registry")
    chemical_delta = read_json(pfile(contract["paths"]["chemical_registry_delta"]))
    registry_merged = merge_chemical_registry(registry, chemical_delta)
    merged_registry_ids = {x["id"] for x in registry_merged["entries"]}
    bindings = read_json(bindings_path)
    bindings_merged, binding_delta = merge_chemical_bindings(
        bindings, chem_binding, record, p["record_sha256"],
        expected_base["recipe-atlas/static/assets/chemical-registry/registry.json"],
        merged_registry_ids,
    )
    registry_merged["summary"]["recordCount"] = len(bindings_merged["recordBindings"])
    registry_merged["summary"]["bindingCount"] = sum(len(v) for v in bindings_merged["recordBindings"].values())
    solutions_merged = merge_solution_components(read_json(solutions_path), record, chem_binding)

    rights_delta = read_json(pfile(contract["paths"]["rights_delta"]))
    rights_entries, rights_assets = verify_rights_delta(
        rights_delta, package_dir, contract, expected_base["publication/asset-rights-registry.json"]
    )
    existing_rights = read_json(rights_path)
    existing_delivery_keys = {
        (path.get("repo"), path.get("path"))
        for x in existing_rights.get("assets", []) for path in x.get("delivery_paths", [])
    }
    for row in rights_entries:
        for path in row["delivery_paths"]:
            key = (path["repo"], path["path"])
            if key in existing_delivery_keys:
                raise ImportRejected(f"Asset rights delivery path already exists: {key[0]} {key[1]}")

    # Validate policy transformations of authored scientific JSON before any
    # output is created. Rights assets were checked against both delivery paths.
    guard_path = checkout / "tools/mattersyn-release/public_release_guard.py"
    spec = importlib.util.spec_from_file_location("matter_release_guard", guard_path)
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    policy = guard.load_config(checkout / "publication/public-release-policy.json", rights_path)
    policy["asset_registry_indexes"] = guard._build_asset_indexes(existing_rights)
    for rel, raw in [
        (f"recipe-atlas/data/records/{p['record_id']}.json", record_raw),
        (f"recipe-atlas/data/paper-reviews/{p['paper_id']}.json", review_raw),
    ]:
        result = guard.history_project("mattersyn", rel, raw, policy)
        if result.get("action") != "allow" or result.get("content") != raw:
            raise ImportRejected(f"Public projection would reject or rewrite authored JSON: {rel}")

    assets_to_stage = {}
    for site_rel, (source_path, hash_value) in rights_assets.items():
        source_rel = PurePosixPath("recipe-atlas/static") / PurePosixPath(site_rel)
        assets_to_stage[source_rel.as_posix()] = (source_path.read_bytes(), hash_value)
    # Validate source/site path permissions after append-only rights proposal.
    proposed_rights = json.loads(json.dumps(existing_rights))
    proposed_rights["assets"].extend(rights_entries)
    for target_rel, (raw, expected_hash) in assets_to_stage.items():
        repo_rel = PurePosixPath(target_rel).as_posix()
        site_rel = repo_rel.removeprefix("recipe-atlas/static/")
        for repo_kind, path in (("mattersyn", repo_rel), ("mattersyn-site", site_rel)):
            error = guard._rights_result(path, raw, repo_kind, proposed_rights)
            if error:
                raise ImportRejected(f"Asset rights preflight failed for {repo_kind}:{path}: {error}")
        if digest_bytes(raw) != expected_hash:
            raise ImportRejected(f"Asset bytes changed during preflight: {target_rel}")

    router_path = checkout / "recipe-atlas/static/protocol-visuals.mjs"
    router_bytes = router_path.read_bytes()
    registration_txt = pfile(contract["paths"]["protocol_registration"]).read_text(encoding="utf-8")
    module_rel = contract["paths"]["protocol_module"]
    module_path = package_dir / Path(*posix_relative(module_rel).parts)
    module_bytes = module_path.read_bytes()
    registration = {
        "scene_builder": "buildThomson2010Scene",
        "art_builder": "createThomson2010Art",
        "import_line": "import {buildThomson2010Scene,createThomson2010Art} from './thomson2010-protocol.mjs?v=0.39.1';",
        "import_anchor": "import {buildYu1998Scene,createYu1998Art} from './yu1998-protocol.mjs?v=0.39.1';",
    }
    if registration["import_line"] not in registration_txt:
        raise ImportRejected("Protocol registration proposal does not match the frozen module exports")
    patched_router = patch_protocol_router(router_bytes, module_bytes, registration)

    # Proposed public paths are exact output paths only. The public policy itself
    # is not edited here; its allowlist must be merged and rerun by the release owner.
    staged = {
        f"recipe-atlas/data/records/{p['record_id']}.json": record_raw,
        f"recipe-atlas/data/paper-reviews/{p['paper_id']}.json": review_raw,
        "recipe-atlas/data/reader-presentation-reviewed.json": json_bytes(reader_merged),
        "recipe-atlas/static/assets/chemical-registry/registry.json": json_bytes(registry_merged),
        "recipe-atlas/static/assets/chemical-registry/bindings.json": json_bytes(bindings_merged),
        "recipe-atlas/static/assets/chemical-registry/solution-components.json": json_bytes(solutions_merged),
        "recipe-atlas/static/protocol-visuals.mjs": patched_router,
        module_rel: module_bytes,
    }
    staged["publication/asset-rights-registry.json"] = json_bytes(proposed_rights)
    staged.update({
        rel: raw for rel, (raw, _) in assets_to_stage.items()
    })
    staged["publication/asset-rights-registry.delta.json"] = pfile(contract["paths"]["rights_delta"]).read_bytes()
    staged["integration-metadata/reader-chemical-bindings.json"] = pfile(contract["paths"]["chemical_bindings"]).read_bytes()
    staged["integration-metadata/reader-figure-map.json"] = pfile(contract["paths"]["figure_map"]).read_bytes()
    staged["integration-metadata/apparatus-stage-map.json"] = pfile(contract["paths"]["apparatus_map"]).read_bytes()
    staged["integration-metadata/reader-presentation-reviewed.delta.json"] = pfile(contract["paths"]["presentation_delta"]).read_bytes()
    staged["integration-metadata/chemical-registry-entries.delta.json"] = pfile(contract["paths"]["chemical_registry_delta"]).read_bytes()
    staged["integration-metadata/protocol-visuals-registration.txt"] = pfile(contract["paths"]["protocol_registration"]).read_bytes()
    staged["integration-metadata/source-record-digest-bindings.json"] = pfile(contract["paths"]["digest_bindings"]).read_bytes()

    public_path_proposal = {
        "schema_version": "mattersyn-public-path-proposal/1",
        "status": "proposal_only_not_applied",
        "repo_payloads": [
            {"repo": "mattersyn", "path": rel, "sha256": digest_bytes(raw), "bytes": len(raw)}
            for rel, raw in sorted(staged.items()) if not is_control_artifact(rel)
        ],
        "site_asset_deliveries": [
            {
                "repo": path["repo"], "path": path["path"],
                "asset_hash": row["asset_hash"], "bytes": path["bytes"],
                "rights_status": row.get("rights", {}).get("status"),
                "publisher_permission_verified": row.get("rights", {}).get("copyright_permission_verified", False),
            }
            for row in rights_entries for path in row.get("delivery_paths", [])
            if path.get("repo") == "mattersyn-site"
        ],
        "note": "Release-path policy changes and generated dist paths require separate owner review; these entries are not applied automatically.",
    }
    staged["integration-metadata/public-path-proposal.json"] = json_bytes(public_path_proposal)

    # Final source-repository projection is checked for every actual repo file,
    # not just the canonical record. Control artifacts are private and excluded.
    policy["asset_registry_indexes"] = guard._build_asset_indexes(proposed_rights)
    projection_checks = 0
    for rel, raw in staged.items():
        if is_control_artifact(rel):
            continue
        projected = guard.history_project("mattersyn", rel, raw, policy)
        if projected.get("action") != "allow" or projected.get("content") != raw:
            raise ImportRejected(f"Public projection would reject or rewrite staged repository file: {rel}")
        projection_checks += 1

    existing_registry_id_collision = registry_ids.intersection(
        x["id"] for x in chemical_delta.get("entries", [])
    )
    if existing_registry_id_collision:
        raise ImportRejected(f"Chemical identity IDs already exist: {sorted(existing_registry_id_collision)}")
    require_absent(checkout, create_targets + list(assets_to_stage) + [module_rel])

    base_replacements = {
        "recipe-atlas/data/reader-presentation-reviewed.json": expected_base["recipe-atlas/data/reader-presentation-reviewed.json"],
        "recipe-atlas/static/assets/chemical-registry/registry.json": expected_base["recipe-atlas/static/assets/chemical-registry/registry.json"],
        "recipe-atlas/static/assets/chemical-registry/bindings.json": expected_base["recipe-atlas/static/assets/chemical-registry/bindings.json"],
        "recipe-atlas/static/assets/chemical-registry/solution-components.json": expected_base["recipe-atlas/static/assets/chemical-registry/solution-components.json"],
        "recipe-atlas/static/protocol-visuals.mjs": expected_base["recipe-atlas/static/protocol-visuals.mjs"],
        "publication/asset-rights-registry.json": expected_base["publication/asset-rights-registry.json"],
    }
    operations = []
    for rel, raw in sorted(staged.items()):
        if is_control_artifact(rel):
            operations.append({"path": rel, "target_repo_path": None, "operation": "control_only_not_applied_to_repository", "sha256": digest_bytes(raw), "bytes": len(raw)})
        elif rel in base_replacements:
            operations.append({"path": rel, "target_repo_path": rel, "operation": "replace_if_exact_base_sha256", "expected_base_sha256": base_replacements[rel], "sha256": digest_bytes(raw), "bytes": len(raw)})
        elif rel == "publication/asset-rights-registry.delta.json":
            operations.append({"path": rel, "target_repo_path": None, "operation": "control_only_not_applied_to_repository", "expected_base_sha256": expected_base["publication/asset-rights-registry.json"], "sha256": digest_bytes(raw), "bytes": len(raw)})
        else:
            operations.append({"path": rel, "target_repo_path": rel, "operation": "create_only", "expected_absent": True, "sha256": digest_bytes(raw), "bytes": len(raw)})

    plan = {
        "schema_version": "mattersyn-package-import-plan/1",
        "status": "private_staged_overlay; not applied or published",
        "target_base_head": checkout_info["head"],
        "source": {"doi": p["doi"], "source_pdf_sha256": p["source_pdf_sha256"], "record_id": p["record_id"], "paper_id": p["paper_id"]},
        "input_bindings": {
            "bundle_manifest_sha256": p["bundle_manifest_sha256"],
            "author_freeze_sha256": p["author_freeze_sha256"],
            "reader_freeze_sha256": p["reader_freeze_sha256"],
            "chemical_freeze_sha256": p["chemical_freeze_sha256"],
            "evidence_receipts": evidence["receipts"],
            "checkout_dependencies": checkout_info["dependency_files"],
            "operational_policy_delta": checkout_info["operational_policy_delta"],
        },
        "canonical": {"record_sha256": p["record_sha256"], "review_sha256": p["review_sha256"], "review_scope": scope["scope"], "si_unverified": True, "training_eligible": False, "schema_dag_errors": 0},
        "reader": {"material_hub_id": material_info["material_hub_id"], "records_added": 1, "figures_by_source_added": 12, "final_review_count_for_source": 1, "full_reader_counts_updated": True},
        "chemical": {"registry_entries_added": len(chemical_delta.get("entries", [])), "record_binding_added": 1, "solution_contexts_added": len(record.get("stocks", [])), "unbound_material_ids": chem_binding.get("unbound_material_ids", [])},
        "rights": {"asset_entries": len(rights_entries), "delivery_path_entries": sum(len(x.get("delivery_paths", [])) for x in rights_entries), "publisher_permission_verified": False},
        "release_projection": {"repository_files_checked": projection_checks, "all_allow_byte_identical": True, "policy_modified": False},
        "operations": operations,
        "deferred": contract["deferred"],
        "limits": ["No files were written into the target checkout.", "No full site build or post-import browser QA was performed.", "No public release-path policy was modified.", "The target material hub input hash is generated by the later atlas build and must be refreshed before a final Reader build.", "Source PDFs/SI and private audit working files are not part of the overlay."],
    }
    return staged, plan


def stage_overlay(output: Path, stage_root: Path, staged: dict[str, bytes], plan: dict) -> tuple[str, int]:
    output = output.resolve(strict=False)
    root = stage_root.resolve(strict=True)
    if not contained(root, output) or output == root:
        raise ImportRejected("Output must be a new child of the explicit private staging root")
    if output.exists():
        raise ImportRejected("Refusing to overwrite an existing stage directory")
    # The private overlay is kept separate from the inspected checkout and source bundle.
    tmp = Path(tempfile.mkdtemp(prefix=".staging-", dir=root))
    try:
        payload_root = tmp / "repo"
        files = []
        for rel, raw in sorted(staged.items()):
            safe = posix_relative(rel)
            control_only = is_control_artifact(safe.as_posix())
            destination_rel = PurePosixPath("control") / safe if control_only else PurePosixPath("repo") / safe
            target = require_no_link_components(tmp, destination_rel)
            write_bytes(target, raw)
            files.append({
                "path": destination_rel.as_posix(),
                "target_path": None if control_only else safe.as_posix(),
                "sha256": digest_bytes(raw),
                "bytes": len(raw),
            })
        control_readme = (
            "# Private package-import control files\n\n"
            "Only files under `repo/` are compare-and-swap/create-only repository candidates. "
            "Files under `control/` are importer inputs, audit bindings, and proposals; never copy them into a public repository. "
            "Use `import-plan.json` to apply exact operations after reviewing the private overlay. "
            "This staged overlay is not applied, built, or published.\n"
        ).encode("utf-8")
        write_bytes(tmp / "control" / "README.md", control_readme)
        files.append({"path": "control/README.md", "target_path": None, "sha256": digest_bytes(control_readme), "bytes": len(control_readme)})
        plan_raw = json_bytes(plan)
        write_bytes(tmp / "control" / "import-plan.json", plan_raw)
        files.append({"path": "control/import-plan.json", "target_path": None, "sha256": digest_bytes(plan_raw), "bytes": len(plan_raw)})
        manifest = {
            "schema_version": "mattersyn-private-import-overlay/1",
            "status": "staged_private_overlay_not_applied_or_published",
            "files": files,
            "import_plan_sha256": digest_bytes(plan_raw),
        }
        manifest_raw = json_bytes(manifest)
        write_bytes(tmp / "overlay-manifest.json", manifest_raw)
        if output.exists():
            raise ImportRejected("Output appeared concurrently; refusing replacement")
        tmp.rename(output)
        return digest_bytes(manifest_raw), len(files)
    except Exception:
        if tmp.exists() and contained(root, tmp):
            shutil.rmtree(tmp)
        raise


def verify_staged_overlay(stage_dir: Path, expected_manifest_sha256: str | None = None) -> dict:
    stage_dir = stage_dir.resolve(strict=True)
    manifest_path = stage_dir / "overlay-manifest.json"
    assert_hash(manifest_path, expected_manifest_sha256, "staged overlay manifest") if expected_manifest_sha256 else None
    manifest_raw = manifest_path.read_bytes()
    manifest = json.loads(manifest_raw)
    if manifest.get("status") != "staged_private_overlay_not_applied_or_published":
        raise ImportRejected("Stage manifest does not identify a private, unapplied overlay")
    entries = manifest.get("files")
    if not isinstance(entries, list) or not entries:
        raise ImportRejected("Stage manifest has no artifact inventory")
    seen: set[str] = set()
    target_paths: set[str] = set()
    for row in entries:
        rel = posix_relative(row.get("path", ""))
        rel_text = rel.as_posix()
        if rel_text in seen:
            raise ImportRejected(f"Duplicate staged file path: {rel_text}")
        seen.add(rel_text)
        if rel.parts[0] not in {"repo", "control"}:
            raise ImportRejected(f"Staged file is outside repo/control separation: {rel_text}")
        if rel.parts[0] == "repo":
            target = posix_relative(row.get("target_path", ""))
            if target.as_posix() != PurePosixPath(*rel.parts[1:]).as_posix():
                raise ImportRejected(f"Repository target path does not match staged location: {rel_text}")
            target_paths.add(target.as_posix())
        elif row.get("target_path") is not None:
            raise ImportRejected(f"Control artifact has a repository target: {rel_text}")
        path = require_no_link_components(stage_dir, rel)
        if not path.is_file() or path.stat().st_size != row.get("bytes") or digest_file(path) != row.get("sha256"):
            raise ImportRejected(f"Staged file hash/size mismatch: {rel_text}")
    plan_path = stage_dir / "control/import-plan.json"
    if digest_file(plan_path) != manifest.get("import_plan_sha256"):
        raise ImportRejected("Import plan digest differs from the overlay manifest")
    plan = read_json(plan_path)
    planned_targets = {
        row["target_repo_path"] for row in plan.get("operations", [])
        if row.get("target_repo_path") is not None
    }
    if planned_targets != target_paths:
        raise ImportRejected("Repo payload file set differs from the exact apply-operation set")
    actual = {
        p.relative_to(stage_dir).as_posix()
        for p in stage_dir.rglob("*") if p.is_file()
    }
    expected = seen | {"overlay-manifest.json"}
    if actual != expected:
        raise ImportRejected(f"Staged file set differs from manifest: extras={sorted(actual-expected)}, missing={sorted(expected-actual)}")
    return {
        "overlay_manifest_sha256": digest_bytes(manifest_raw),
        "import_plan_sha256": digest_file(plan_path),
        "staged_files": len(entries),
        "repo_payload_files": len(target_paths),
        "control_files": sum(path.startswith("control/") for path in seen),
        "status": manifest["status"],
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Preflight/stage one independently accepted MatterSyn package into a private overlay.")
    parser.add_argument("--checkout", type=Path, required=True, help="Explicit clean source checkout used as the contract; never written.")
    parser.add_argument("--package", type=Path, required=True, help="Frozen package overlay directory.")
    parser.add_argument("--evidence-root", type=Path, required=True, help="Private root containing the exact author and independent audit freezes.")
    parser.add_argument("--source-pdf", type=Path, required=True, help="Original local source PDF whose hash is in the frozen contract.")
    parser.add_argument("--output-root", type=Path, required=True, help="Existing explicit private directory for new overlay stages; never the checkout/package/evidence tree.")
    parser.add_argument("--stage-name", required=True, help="New private staging directory name; never reused.")
    parser.add_argument("--stage", action="store_true", help="Materialize the private overlay after every check passes; otherwise preflight only.")
    parser.add_argument("--contract", type=Path, default=CONTRACT_PATH)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    t0 = time.perf_counter()
    contract = read_json(args.contract)
    if digest_file(args.contract) != "5327cb186f5b2a0c7fd797c76864f5563bf42fa44f9ed6b8fd2c72e99f0c67c7":
        raise ImportRejected("Importer contract changed; independently review/refreeze before reuse")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,63}", args.stage_name):
        raise ImportRejected("Stage name must be a lower-case slug of 3–64 characters")
    stage_root = args.output_root.resolve(strict=True)
    if not stage_root.is_dir():
        raise ImportRejected("Explicit output root must already exist as a directory")
    out = stage_root / args.stage_name
    resolved_checkout = args.checkout.resolve(strict=True)
    protected_roots = (
        args.package.resolve(strict=True), args.evidence_root.resolve(strict=True),
        args.source_pdf.resolve(strict=True), resolved_checkout,
    )
    for protected in protected_roots:
        if contained(protected, stage_root) or contained(stage_root, protected):
            raise ImportRejected("Private output may not overlap checkout, source package, source PDF, or audit evidence")
    if out.exists():
        raise ImportRejected("Refusing to overwrite an existing stage directory")
    staged, plan = build_overlay(resolved_checkout, args.package.resolve(strict=True), args.evidence_root.resolve(strict=True), args.source_pdf.resolve(strict=True), contract)
    plan["runtime_bindings"] = {
        "importer_sha256": digest_file(Path(__file__).resolve()),
        "contract_sha256": digest_file(args.contract.resolve(strict=True)),
        "python_version": sys.version.split()[0],
    }
    result = {"status": "PREFLIGHT_PASS_NO_FILES_WRITTEN", "operation_count": len(staged), "stage_path": str(out), "plan": plan}
    if args.stage:
        manifest_sha, staged_count = stage_overlay(out, stage_root, staged, plan)
        result.update({"status": "PRIVATE_OVERLAY_STAGED_NOT_APPLIED", "overlay_manifest_sha256": manifest_sha, "staged_files": staged_count})
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 3)
    result["mechanical_elapsed_ms"] = elapsed_ms
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    try:
        main()
    except ImportRejected as exc:
        print(json.dumps({"status": "REJECTED", "reason": str(exc)}, ensure_ascii=False))
        raise SystemExit(2)
