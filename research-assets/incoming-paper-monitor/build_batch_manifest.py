"""Snapshot a claimed batch without changing any downloaded source filename.

File grouping is provisional until a hash-bound, independently checked pairing
review is supplied. Stability observations never imply scientific completeness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

import monitor

HERE = Path(__file__).resolve().parent


def paper_directory(directory, key):
    mapping_path = directory / "paper-directories.json"
    mapping = json.loads(mapping_path.read_text(encoding="utf-8")) if mapping_path.exists() else {}
    if not isinstance(mapping, dict) or not all(isinstance(v, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", v) for v in mapping.values()):
        raise ValueError("Paper directory mapping must use simple, relative directory names.")
    if len({v.casefold() for v in mapping.values()}) != len(mapping):
        raise ValueError("Paper directory mapping collides; preserve separate source versions.")
    fallback = re.sub(r"[^a-zA-Z0-9._-]", "-", key) + "--" + hashlib.sha256(key.encode()).hexdigest()[:12]
    return directory / mapping.get(key, fallback)


def pairing_review(directory, key, group, hashes):
    path = paper_directory(directory, key) / "pairing-review.json"
    if not path.exists():
        return {"status": "pending", "expected_evidence": str(path)}
    review = json.loads(path.read_text(encoding="utf-8"))
    fp = group["fingerprint"]
    if review.get("group_id") != key or review.get("source_generation") != group["generation"]:
        return {"status": "stale", "evidence": str(path), "reason": "Paper or source generation differs."}
    if review.get("bundle_sha256") != fp.get("bundle_sha256"):
        return {"status": "stale", "evidence": str(path), "reason": "Bundle fingerprint differs."}
    documents = review.get("documents", [])
    if not isinstance(documents, list) or not all(isinstance(item, dict) for item in documents):
        raise ValueError(f"Invalid pairing document list for {key}")
    if len(documents) != len(hashes) or {item.get("sha256") for item in documents} != hashes:
        return {"status": "stale", "evidence": str(path), "reason": "Inspected document set differs."}
    audit = review.get("independent_audit", {})
    author = review.get("reviewer")
    auditor = audit.get("reviewer") if isinstance(audit, dict) else None
    if (review.get("status") != "passed" or not isinstance(author, str) or not author.strip() or
            not isinstance(audit, dict) or audit.get("status") != "passed" or
            not isinstance(auditor, str) or not auditor.strip() or
            auditor.strip() == author.strip()):
        return {"status": "pending", "evidence": str(path), "reason": "Separate pairing author and passed auditor required."}
    refs = review.get("evidence", []) + audit.get("evidence", [])
    if not review.get("evidence") or not audit.get("evidence") or any(not Path(ref).is_file() for ref in refs):
        raise ValueError(f"Pairing evidence does not exist for {key}")
    for item in documents:
        if item.get("role") not in {"main", "si", "other"} or not isinstance(item.get("basis"), str) or not item["basis"].strip():
            raise ValueError(f"Missing document role/basis in pairing review for {key}")
    if not any(item["role"] == "main" for item in documents):
        raise ValueError(f"No identified main article in passed pairing review for {key}")
    return {"status": "passed", "evidence": str(path), "review": review}


def build(ledger, output_dir):
    claims = monitor.active_claims(ledger)
    if not claims:
        raise ValueError("No claimed papers: select/resume a batch first.")
    live = monitor.inventory_sources(ledger)
    directories = [str(paper_directory(output_dir, claim["group_id"])).casefold() for claim in claims]
    if len(set(directories)) != len(directories):
        raise ValueError("Batch paper directories collide.")
    result = {
        "schema": "mattersyn-batch-intake-manifest/1",
        "generated_at": monitor.iso(__import__("time").time_ns()),
        "batch_id": (ledger.get("current_batch") or {}).get("batch_id"),
        "source_filename_policy": "Preserve existing names and locations; aliases only in this manifest.",
        "download_completion_signal": "Not supplied by downloader; stable observations are a separate check.",
        "scientific_scope": "Intake and pairing only; not full extraction, full scientific audit or publication.",
        "papers": [],
    }
    for claim in claims:
        key = claim["group_id"]
        group = ledger["groups"][key]
        fp = group.get("fingerprint", {})
        if fp.get("generation") != group["generation"]:
            raise ValueError(f"Fingerprint current source generation before manifesting {key}")
        siblings = {name for name, item in live.items() if item["group_id"] == key}
        if siblings != set(group["files"]):
            raise ValueError(f"Source membership changed for {key}; scan and fingerprint before manifesting.")
        if fp.get("files") != {name: ledger["files"][name].get("sha256") for name in group["files"]}:
            raise ValueError(f"Fingerprint file hashes differ from ledger for {key}")
        files = []
        for name in group["files"]:
            item = ledger["files"][name]
            path = monitor.file_path(ledger, name)
            signature = path.stat()
            digest = item.get("sha256", "")
            if not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise ValueError(f"Missing source content hash for {name}")
            if not item.get("exists") or signature.st_size != item["size"] or signature.st_mtime_ns != item["mtime_ns"]:
                raise ValueError(f"Source changed since fingerprint: {name}. Scan and fingerprint again.")
            current_hash = hashlib.sha256()
            with path.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    current_hash.update(block)
            after = path.stat()
            if current_hash.hexdigest() != digest or after.st_size != signature.st_size or after.st_mtime_ns != signature.st_mtime_ns:
                raise ValueError(f"Source bytes changed since fingerprint: {name}")
            files.append({
                "file_key": name, "source_path": str(path), "original_filename": path.name,
                "source_collection": item.get("source_id", "incoming"),
                "document_id": "sha256:" + digest, "sha256": digest,
                "role_candidate": item["role"], "bytes": item["size"],
                "mtime_ns": item["mtime_ns"], "candidate_parent": key,
                "alias": re.sub(r"[^a-zA-Z0-9._-]", "-", key) + "--" + item["role"] + "--" + digest[:16] + path.suffix,
            })
        hashes = {item["sha256"] for item in files}
        result["papers"].append({
            "paper_id": key, "queue_order": group["queue_order"],
            "doi_candidates": group.get("doi_candidates", []),
            "source_generation": group["generation"], "bundle_sha256": fp.get("bundle_sha256"),
            "file_copies": files, "unique_document_count": len(hashes),
            "main_si_pairing": pairing_review(output_dir, key, group, hashes),
            "review_directory": str(paper_directory(output_dir, key)),
        })
    latest = monitor.inventory_sources(ledger)
    for claim in claims:
        key = claim["group_id"]
        if {name for name, item in latest.items() if item["group_id"] == key} != set(ledger["groups"][key]["files"]):
            raise ValueError(f"Source membership changed while building manifest for {key}")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=HERE / "ledger.json")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    # Atomic ledger replacement makes this an internally consistent snapshot.
    before = args.ledger.read_bytes()
    result = build(json.loads(before), args.output_dir)
    result["ledger_sha256"] = hashlib.sha256(before).hexdigest()
    if before != args.ledger.read_bytes():
        raise ValueError("Ledger changed during manifest generation; retry from fresh snapshot.")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    archive = args.output_dir / "manifest-history" / (digest + ".json")
    archive.parent.mkdir(exist_ok=True)
    if not archive.exists():
        archive.write_bytes(raw)
    (args.output_dir / "intake-manifest.json").write_bytes(raw)
    print(json.dumps({"manifest": str(args.output_dir / "intake-manifest.json"),
                      "sha256": digest, "paper_count": len(result["papers"]),
                      "verified_pairings": sum(p["main_si_pairing"]["status"] == "passed" for p in result["papers"]),
                      "source_files_renamed_or_modified": False}, indent=2))


if __name__ == "__main__":
    main()
