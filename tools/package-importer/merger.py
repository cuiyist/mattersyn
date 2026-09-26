"""Stage a small declarative additive overlay without mutating its checkout."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True


class MergeRejected(ValueError):
    pass


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_importer(path: Path):
    path = path.resolve(strict=True)
    spec = importlib.util.spec_from_file_location("mattersyn_package_importer", path)
    if spec is None or spec.loader is None:
        raise MergeRejected("Could not load the pinned package-importer helpers")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Use one rejection type across the declarative layer and the pinned helper
    # functions, so the CLI can fail closed without swallowing unrelated errors.
    module.ImportRejected = MergeRejected
    return module


def overlaps(path: Path, root: Path) -> bool:
    path, root = path.resolve(), root.resolve()
    return path == root or path in root.parents or root in path.parents


def reject_sensitive_target(relative: str) -> None:
    parts = [part.casefold() for part in relative.split("/")]
    if any("asset-rights-registry" in part or "public-release-policy" in part for part in parts):
        raise MergeRejected("Rights and release-policy files require a separate explicit review")


def pointer_parts(pointer: str) -> list[str]:
    if not isinstance(pointer, str) or (pointer and not pointer.startswith("/")):
        raise MergeRejected("JSON pointer must be empty or start with '/'")
    if pointer == "":
        return []
    parts = pointer[1:].split("/")
    if any(not part or re.search(r"~(?![01])", part) for part in parts):
        raise MergeRejected("Empty or malformed JSON-pointer segment")
    return [part.replace("~1", "/").replace("~0", "~") for part in parts]


def at_pointer(value, pointer: str):
    current = value
    for part in pointer_parts(pointer):
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list) and part.isdigit() and str(int(part)) == part and int(part) < len(current):
            current = current[int(part)]
        else:
            raise MergeRejected(f"JSON pointer does not resolve: {pointer}")
    return current


def canonical_json(value) -> str:
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise MergeRejected("Merge values must be finite, valid JSON data") from exc


def identity(item: dict, keys: list[str]) -> str:
    if not isinstance(item, dict) or any(key not in item for key in keys):
        raise MergeRejected("Append item lacks one or more declared identity fields")
    return canonical_json([item[key] for key in keys])


def inspect_payload(payload: Path, entries: list[dict], helper) -> dict[str, bytes]:
    if not isinstance(entries, list):
        raise MergeRejected("create_files must be a list")
    listed: dict[str, bytes] = {}
    target_names: set[str] = set()
    source_names: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"source", "target", "sha256", "bytes"}:
            raise MergeRejected("Each create_files entry needs exactly source, target, sha256 and bytes")
        source = helper.posix_relative(entry.get("source", "")).as_posix()
        target = helper.posix_relative(entry.get("target", "")).as_posix()
        reject_sensitive_target(target)
        if source.casefold() in source_names:
            raise MergeRejected(f"Duplicate create-file source: {source}")
        source_names.add(source.casefold())
        if target.casefold() in target_names:
            raise MergeRejected(f"Duplicate or case-colliding target: {target}")
        target_names.add(target.casefold())
        path = helper.require_no_link_components(payload, helper.posix_relative(source))
        expected_hash, expected_size = entry.get("sha256"), entry.get("bytes")
        if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
            raise MergeRejected(f"Invalid SHA-256 for payload file {source}")
        if not isinstance(expected_size, int) or isinstance(expected_size, bool) or expected_size < 0:
            raise MergeRejected(f"Invalid byte count for payload file {source}")
        helper.assert_hash(path, expected_hash, f"payload file {source}")
        if path.stat().st_size != expected_size:
            raise MergeRejected(f"Payload byte count mismatch: {source}")
        listed[target] = path.read_bytes()
    actual: set[str] = set()
    for path in payload.rglob("*"):
        if path.is_symlink():
            raise MergeRejected("Symlinks are not allowed in the package payload")
        if path.is_file():
            actual.add(path.relative_to(payload).as_posix().casefold())
    if actual != source_names:
        raise MergeRejected(f"Payload file set differs from contract: extras={sorted(actual-source_names)}, missing={sorted(source_names-actual)}")
    return listed


def merge_plan(checkout: Path, payload: Path, contract: dict, output: Path, importer_path: Path) -> dict:
    helper = load_importer(importer_path)
    checkout = checkout.resolve(strict=True)
    payload = payload.resolve(strict=True)
    output = output.resolve()
    if output.exists():
        raise MergeRejected("Output directory must be new; existing output is never overwritten")
    if overlaps(output, checkout) or overlaps(output, payload):
        raise MergeRejected("Output must be outside the checkout and package payload")
    if contract.get("schema_version") != "mattersyn-declarative-additive-merge/1":
        raise MergeRejected("Unsupported additive-merge contract version")
    if set(contract) - {"schema_version", "base_commit", "base_files", "create_files", "json_operations"}:
        raise MergeRejected("Unknown contract keys; fix the contract instead of silently ignoring fields")

    base_commit = contract.get("base_commit")
    if base_commit is not None:
        if not isinstance(base_commit, str) or not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", base_commit):
            raise MergeRejected("base_commit must be a full hexadecimal Git object ID or null")
        actual_head = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
        if actual_head != base_commit:
            raise MergeRejected(f"Stale base commit: expected {base_commit}, found {actual_head}")
    base_files = contract.get("base_files")
    if not isinstance(base_files, dict) or not base_files:
        raise MergeRejected("base_files must map every JSON target to its expected SHA-256")
    originals: dict[str, bytes] = {}
    pinned_hashes: dict[str, str] = {}
    pinned_names: set[str] = set()
    for name, expected in base_files.items():
        relative = helper.posix_relative(name).as_posix()
        if relative != name or relative.casefold() in pinned_names:
            raise MergeRejected(f"Noncanonical or case-colliding base path: {name}")
        pinned_names.add(relative.casefold())
        reject_sensitive_target(relative)
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise MergeRejected(f"Invalid SHA-256 for base file {relative}")
        path = helper.require_no_link_components(checkout, helper.posix_relative(relative))
        helper.assert_hash(path, expected, f"base file {relative}")
        originals[relative] = path.read_bytes()
        pinned_hashes[relative] = expected

    created = inspect_payload(payload, contract.get("create_files", []), helper)
    target_names = {name.casefold() for name in created}
    merged: dict[str, object] = {}
    operation_log: list[dict] = []
    operations = contract.get("json_operations", [])
    if not isinstance(operations, list):
        raise MergeRejected("json_operations must be a list")
    for operation in operations:
        if not isinstance(operation, dict) or not isinstance(operation.get("op"), str):
            raise MergeRejected("Each JSON operation must be an object with an op")
        kind = operation.get("op")
        target = helper.posix_relative(operation.get("target", "")).as_posix()
        reject_sensitive_target(target)
        if target not in originals:
            raise MergeRejected(f"JSON target is not pinned in base_files: {target}")
        if operation.get("base_sha256") != pinned_hashes[target]:
            raise MergeRejected(f"JSON operation base hash differs from pinned base file: {target}")
        if target.casefold() in target_names:
            raise MergeRejected(f"Target is both create-only and JSON-merge input: {target}")
        if target not in merged:
            try:
                merged[target] = json.loads(originals[target].decode("utf-8-sig"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise MergeRejected(f"Pinned JSON target is not valid UTF-8 JSON: {target}") from exc
        root = merged[target]
        pointer = operation.get("pointer", "")
        node = at_pointer(root, pointer)
        if kind == "add_keys":
            if set(operation) != {"op", "target", "base_sha256", "pointer", "items"}:
                raise MergeRejected("add_keys operation has unknown or missing fields")
            items = operation.get("items")
            if not isinstance(node, dict) or not isinstance(items, dict) or not items or any(not isinstance(k, str) for k in items):
                raise MergeRejected("add_keys needs an object target and a nonempty object of new keys")
            collisions = set(node) & set(items)
            if collisions:
                raise MergeRejected(f"add_keys cannot overwrite existing keys: {sorted(collisions)}")
            node.update(json.loads(json.dumps(items, ensure_ascii=False)))
            operation_log.append({"op": kind, "target": target, "pointer": pointer, "added_keys": sorted(items)})
        elif kind == "append_unique":
            if set(operation) != {"op", "target", "base_sha256", "pointer", "items", "identity_keys"}:
                raise MergeRejected("append_unique operation has unknown or missing fields")
            items, keys = operation.get("items"), operation.get("identity_keys")
            if not isinstance(node, list) or not isinstance(items, list) or not isinstance(keys, list) or not keys or not all(isinstance(k, str) for k in keys):
                raise MergeRejected("append_unique needs a list target, item list and explicit identity_keys")
            existing = {}
            for item in node:
                key = identity(item, keys)
                if key in existing:
                    raise MergeRejected("Base list already contains duplicate declared identities")
                existing[key] = item
            incoming: set[str] = set()
            appended, identical = 0, 0
            for item in items:
                key = identity(item, keys)
                if key in incoming:
                    raise MergeRejected("Incoming list contains duplicate declared identities")
                incoming.add(key)
                if key in existing:
                    if canonical_json(existing[key]) != canonical_json(item):
                        raise MergeRejected("append_unique identity collides with different prior data")
                    identical += 1
                else:
                    node.append(json.loads(json.dumps(item, ensure_ascii=False)))
                    existing[key] = item
                    appended += 1
            operation_log.append({"op": kind, "target": target, "pointer": pointer, "appended": appended, "identical_prior_items": identical, "identity_keys": keys})
        else:
            raise MergeRejected(f"Unsupported JSON operation: {kind!r}")

    for relative in created:
        destination = helper.require_no_link_components(checkout, helper.posix_relative(relative))
        if destination.exists():
            raise MergeRejected(f"Create-only target already exists: {relative}")
    for target in merged:
        if target.casefold() in target_names:
            raise MergeRejected(f"JSON target collides with create-only target: {target}")
    files: dict[str, bytes] = {relative: raw for relative, raw in created.items()}
    for target, value in merged.items():
        files[target] = helper.json_bytes(value)

    output.mkdir(parents=True, exist_ok=False)
    file_manifest = []
    for relative, raw in sorted(files.items()):
        safe = helper.posix_relative(relative)
        staged = helper.require_no_link_components(output / "overlay", safe)
        helper.write_bytes(staged, raw)
        file_manifest.append({"path": relative, "sha256": sha(raw), "bytes": len(raw), "mode": "create_only" if relative in created else "additive_json_candidate"})
    importer_hash = helper.digest_file(importer_path)
    receipt = {
        "schema_version": "mattersyn-additive-merge-stage/1", "base_commit": base_commit,
        "base_files": {name: {"sha256": expected, "bytes": len(originals[name])} for name, expected in pinned_hashes.items()},
        "contract_sha256": sha(json.dumps(contract, ensure_ascii=False, sort_keys=True).encode("utf-8")),
        "package_files": file_manifest, "operations": operation_log, "package_importer_sha256": importer_hash,
        "scope": "Private overlay staging only. Existing aggregates are compare-and-swap candidates; run the repository additive preflight and independent release gates before integration or publication.",
        "publication_approved": False,
    }
    helper.write_bytes(output / "merge-manifest.json", helper.json_bytes(receipt))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", required=True, type=Path)
    parser.add_argument("--payload", required=True, type=Path)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--importer", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, help="New private staging directory outside checkout and payload")
    args = parser.parse_args()
    try:
        contract = json.loads(args.contract.read_text(encoding="utf-8-sig"))
        result = merge_plan(args.checkout, args.payload, contract, args.output, args.importer)
    except (MergeRejected, OSError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        parser.error(str(exc))
    print(json.dumps({"status": "staged", "files": len(result["package_files"]), "publication_approved": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
