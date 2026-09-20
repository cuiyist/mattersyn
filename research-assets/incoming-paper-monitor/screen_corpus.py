"""Hash and provisionally rank a frozen local corpus; never change review state.

All outputs are private. A candidate score is a navigation aid, not a synthesis
claim, a negative screening disposition, a scientific audit, or a sample join.
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import re
import time
import unicodedata
import zipfile
from xml.etree import ElementTree as ET

import monitor

VERSION = "corpus-priority-screen-1.1"
HERE = Path(__file__).resolve().parent
LEGACY_MANIFEST = HERE.parent / "corpus-20260917/private/document-manifest.json"
MAX_MEMBER_BYTES = 32 * 1024 * 1024
MAX_ARCHIVE_BYTES = 96 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 4096
LEGACY = {}
OUTPUT = None


class ManualReaderLimit(ValueError):
    def __init__(self, message, detected_format, details):
        super().__init__(message)
        self.detected_format = detected_format
        self.details = details


def replace_with_retry(temporary, path):
    # Windows readers/antivirus may briefly deny replacing an existing cache
    # while another exact-content worker is reading it. Source files are never
    # replaced; this bounded retry applies only to our private output files.
    for attempt in range(80):
        try:
            os.replace(temporary, path)
            return
        except PermissionError:
            if attempt == 79:
                raise
            time.sleep(0.025)


def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".{os.getpid()}.tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    replace_with_retry(temporary, path)


def read_cache_json(path):
    # On Windows an atomic replacement can briefly deny a concurrent reader.
    # Retry private cache reads only; source-read errors retain their disposition.
    for attempt in range(80):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except PermissionError:
            if attempt == 79:
                raise
            time.sleep(0.025)


def sha_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def signature(path):
    item = path.stat()
    return {"bytes": item.st_size, "mtime_ns": item.st_mtime_ns}


def legacy_index(path):
    if not path.is_file():
        return {}
    root = path.parent.parent
    documents = json.loads(path.read_text(encoding="utf-8"))["documents"]
    return {item["sha256"]: {
        "sha256": item["sha256"],
        "text_path": str(root / item["textPath"]) if item.get("textPath") else None,
        "extraction_status": item["extractionStatus"], "detected_format": item.get("detectedFormat"),
        "page_count": item.get("pageCount"), "page_results": item.get("pageResults", []),
        "embedded_image_count": item.get("embeddedImageCount"), "legacy_cache": str(path),
    } for item in documents if item.get("sha256")}


def initialize_worker(index, output):
    global LEGACY, OUTPUT
    LEGACY, OUTPUT = index, Path(output).resolve()


OPERATION = re.compile(r"\b(?:dissolv\w*|inject\w*|stir\w*|heat\w*|anneal\w*|calcin\w*|reflux\w*|centrifug\w*|wash\w*|degas\w*|precipitat\w*|dropwise|autoclave|electrodeposit\w*|spin.coat\w*|cation.exchange|ligand.exchange)\b", re.I)
QUANTITY = re.compile(r"(?<![A-Za-z])\d+(?:\.\d+)?\s*(?:[µμu]?mol|mmol|mol|[µμum]?g|[µμum]?l|ml|[°º]\s*c|kelvin|\bK\b|min(?:utes?)?|hours?|hrs?|\bh\b|rpm|M\b|mM\b|vol\.?\s*%)", re.I)
METHOD = re.compile(r"\b(?:experimental(?: section)?|materials and methods|synthe(?:sis|size|sized)|prepar(?:ation|ed)|synthetic procedure|growth procedure)\b", re.I)
STRUCTURE = {
    "refinement": re.compile(r"\b(?:Rietveld|single.crystal X.ray|structure refinement|crystal structure determination|CCDC\s*\d|CSD\s*\d|refined atomic|anisotropic displacement)\b", re.I),
    "lattice_phase": re.compile(r"\b(?:space group|lattice (?:constant|parameter)|unit.cell|crystal phase|crystalline phase|zinc.blende|wurtzite|rock.salt|chalcopyrite|perovskite)\b", re.I),
    "diffraction": re.compile(r"\b(?:X.ray diffraction|powder diffraction|XRD|SAED|selected.area electron diffraction|Bragg|interplanar spacing|lattice fringes)\b", re.I),
    "morphology": re.compile(r"\b(?:HRTEM|HR.TEM|TEM|SEM|nanorod|nanoplate|morphology|core.shell|diameter|particle size)\b", re.I),
}
MODEL = re.compile(r"\b(?:density functional|DFT|simulat\w*|theoretical|model structure|bulk reference|reference pattern|reference structure|optimi[sz]ed (?:Cartesian|atomic|geometry|geometries)|geometry optimi[sz]ation|computed (?:atomic|Cartesian|molecular))\b", re.I)
COORDINATE = re.compile(r"_atom_site_(?:fract|cartn)_[xyz]|\b(?:(?:fractional|Cartesian|atomic)(?: atomic)? coordinates|crystallographic information file|(?:atomic )?positional,? thermal,? (?:and )?occupancy parameters[a-z]?)\b", re.I)
COORDINATE_AXES = re.compile(r"\bx\s+y\s+z\b|_atom_site_(?:fract|cartn)_[xyz]", re.I)
COORDINATE_NUMBERS = re.compile(r"(?<![\w.])[-+−]?\d+\.\d+(?:\(\d+\))?|(?<![\w.])[-+−]?\d+\(\d+\)")
MOLECULAR_CONTEXT = re.compile(r"\b(?:complex(?:es)?|molecular|precursor|reagent)\b", re.I)
# Only explicit nearby naming is associated across blocks of the SAME source.
# This narrow lexical association is a warning, never a product/sample join.
PRECURSOR_NAME = re.compile(r"\b[A-Z][A-Za-z0-9]*(?:\([A-Za-z0-9]+\)\d*)+(?![\w(])")
SAMPLE = re.compile(r"\b(?i:sample|specimen|batch|product)\s*(?:(?i:no)\.?\s*)?[:#-]?\s*([A-Z][A-Z0-9-]{0,12}|\d+[A-Za-z]?)\b")
FAILURE = re.compile(r"\b(?:no (?:particles|nanocrystals|precipitate|product)|failed|unsuccessful|amorphous|impurity|aggregation|decompos\w*|no growth)\b", re.I)
TRIGGER = re.compile(r"synthe|prepar|experiment|dissolv|inject|stir|heat|anneal|calcin|reflux|centrif|wash|degas|precipitat|dropwise|autoclave|coat|exchange|coordina|positional|_atom_site|refin|rietveld|crystal|lattice|diffraction|XRD|SAED|HRTEM|TEM|SEM|morpholog|diameter|particle size|sample|specimen|fail|amorphous|no growth", re.I)


def named_precursor_contexts(blocks, source_sha):
    contexts = {}
    for marker, body in blocks:
        normalized = unicodedata.normalize("NFKC", body)
        for match in re.finditer(r"\bprecursor\b", normalized, re.I):
            local = normalized[max(0, match.start() - 65):match.end() + 65]
            for name in PRECURSOR_NAME.findall(local):
                contexts.setdefault(name, {"source_sha256": source_sha, "text_block": marker,
                                          "text": " ".join(local.split()), "association": "same_source_name_near_precursor_word_not_verified_identity"})
    return contexts


def coordinate_features(window, precursor_contexts):
    if not COORDINATE.search(window):
        return [], []
    numbers = COORDINATE_NUMBERS.findall(window)
    if "_atom_site_" in window.lower():
        numbers = re.findall(r"(?<![\w.])[-+−]?\d+(?:\.\d+)?(?![\w.])", window)
    table_data = bool(COORDINATE_AXES.search(window)) and len(numbers) >= 3
    labels = ["coordinate_numeric_table_candidate" if table_data else "coordinate_mention_without_local_numeric_table"]
    named = [dict(precursor_contexts[name], name=name) for name in precursor_contexts if re.search(r"(?<!\w)" + re.escape(name) + r"(?![\w(])", window)]
    computed = bool(MODEL.search(window))
    contextual = bool(MOLECULAR_CONTEXT.search(window)) or bool(named)
    if computed:
        labels.append("computed_or_reference_coordinate_context")
    if contextual:
        labels.append("molecular_or_precursor_context_product_link_unknown")
    if named:
        labels.append("same_source_named_precursor_context_association")
    # A numeric table earns the strongest navigation bonus only in the absence
    # of explicit contextual warnings. Even then target identity stays unknown.
    feature = "coordinate_data" if table_data and not (computed or contextual) else "contextual_coordinate_data" if table_data else "coordinate_mention"
    labels += [feature + "_candidate", "coordinate_product_sample_link_unverified"]
    return labels, named


def text_features(text, source_sha):
    """Read every text block; keep bounded candidate snippets, never negatives."""
    pieces = re.split(r"\n\n--- (PAGE \d+|OOXML PART [^\n]+|ARCHIVE MEMBER [^\n]+) ---\n\n", text)
    blocks = [(None, pieces[0])] if pieces[0].strip() else []
    blocks += [(pieces[i], pieces[i + 1]) for i in range(1, len(pieces) - 1, 2)]
    precursor_contexts = named_precursor_contexts(blocks, source_sha)
    hits = collections.Counter()
    snippets = []
    coordinate_snippets = []
    samples = set()
    for marker, body in blocks:
        lines = body.splitlines()
        last_end = -1
        for index, line in enumerate(lines):
            if index < last_end or not TRIGGER.search(line):
                continue
            begin, end = max(0, index - 2), min(len(lines), index + 6)
            window = " ".join(unicodedata.normalize("NFKC", " ".join(lines[begin:end])).split())
            if COORDINATE.search(window):
                end = min(len(lines), index + 14)
                window = " ".join(unicodedata.normalize("NFKC", " ".join(lines[begin:end])).split())
            operations = len(OPERATION.findall(window))
            quantities = len(QUANTITY.findall(window))
            method = bool(METHOD.search(window))
            # Quantities alone can be measurement settings; two procedural verbs
            # and local quantities are a stronger navigation cue, not proof.
            recipe = operations >= 2 and quantities >= 2
            labels = []
            if recipe:
                labels.append("procedural_quantitative_candidate")
                hits["recipe_windows"] += 1
            elif method and operations:
                labels.append("partial_procedure_candidate")
                hits["partial_recipe_windows"] += 1
            for category, pattern in STRUCTURE.items():
                if pattern.search(window):
                    hits[category] += 1
                    labels.append(category + "_candidate")
            coordinate_labels, associations = coordinate_features(window, precursor_contexts)
            labels.extend(coordinate_labels)
            for feature in ("coordinate_data", "contextual_coordinate_data", "coordinate_mention"):
                if feature + "_candidate" in coordinate_labels:
                    hits[feature] += 1
            for feature in ("computed_or_reference_coordinate_context", "molecular_or_precursor_context_product_link_unknown", "same_source_named_precursor_context_association"):
                if feature in coordinate_labels:
                    hits[feature] += 1
            if MODEL.search(window):
                hits["model_or_reference_context"] += 1
                labels.append("model_or_reference_context")
            if FAILURE.search(window):
                hits["failure_or_nonideal_outcome"] += 1
                labels.append("failure_or_nonideal_outcome")
            identifiers = SAMPLE.findall(window)
            samples.update(identifiers)
            if identifiers:
                hits["sample_identifier_mentions"] += 1
            if not labels:
                continue
            last_end = end
            priority = (10 if recipe else 3 if method and operations else 0) + max(
                [0] + [weight for category, weight in (("coordinate_data", 16), ("refinement", 10), ("lattice_phase", 6), ("diffraction", 4), ("contextual_coordinate_data", 3), ("coordinate_mention", 2), ("morphology", 1)) if category + "_candidate" in labels])
            snippet = {"source_sha256": source_sha, "page": int(marker[5:]) if marker and marker.startswith("PAGE ") else None,
                             "ooxml_part": marker[11:] if marker and marker.startswith("OOXML PART ") else None,
                             "archive_member": marker[15:] if marker and marker.startswith("ARCHIVE MEMBER ") else None,
                             "line_start_in_text_block": begin + 1, "line_end_in_text_block": end,
                             "categories": labels, "operation_cues": operations, "quantity_cues": quantities,
                             "candidate_priority": priority, "text": window[:1400], "status": "machine_candidate_unreviewed"}
            if coordinate_labels:
                snippet["context_associations"] = associations
                coordinate_snippets.append(snippet)
            snippets.append(snippet)
    snippets.sort(key=lambda item: -item["candidate_priority"])
    return {"counts": dict(hits), "sample_identifier_mentions": sorted(samples)[:30],
            "snippets": snippets[:8], "coordinate_context_snippets": coordinate_snippets[:8], "candidate_windows_detected": len(snippets),
            "snippet_limit": 8, "all_text_characters_examined": sum(len(body.strip()) for _, body in blocks),
            "verified_recipe": False, "verified_structure": False, "verified_sample_join": False}


def safe_member(archive, info, budget):
    detected_format = "xlsx" if info.filename.startswith("xl/") else "docx" if info.filename.startswith("word/") else "zip"
    details = {"archive_member": info.filename, "uncompressed_bytes": info.file_size,
               "compressed_bytes": info.compress_size, "member_byte_limit": MAX_MEMBER_BYTES,
               "total_archive_text_byte_limit": MAX_ARCHIVE_BYTES}
    if info.file_size > MAX_MEMBER_BYTES or budget[0] + info.file_size > MAX_ARCHIVE_BYTES:
        raise ManualReaderLimit("Archive XML/text size limit exceeded; retain for manual review.", detected_format, details)
    if info.file_size > 1024 * 1024 and info.file_size / max(1, info.compress_size) > 500:
        raise ManualReaderLimit("Archive expansion ratio limit exceeded; retain for manual review.", detected_format, details)
    budget[0] += info.file_size
    return archive.read(info)


def extract_source(path, head):
    """Safe text only: PDFium, OOXML, bounded archive text; no macros or OCR."""
    result = {"extraction_status": "unsupported_format", "detected_format": "unknown", "page_count": None,
              "page_results": [], "warnings": [], "embedded_image_count": None}
    if b"%PDF-" in head[:1024]:
        import pypdfium2 as pdfium
        result["detected_format"] = "pdf"
        texts = []
        document = pdfium.PdfDocument(str(path))
        try:
            result["page_count"] = len(document)
            for index in range(len(document)):
                page = textpage = None
                try:
                    page = document[index]
                    textpage = page.get_textpage()
                    content = textpage.get_text_range()
                    result["page_results"].append({"page": index + 1, "characters": len(content), "status": "text" if content.strip() else "no_extractable_text"})
                    texts.append(f"\n\n--- PAGE {index + 1} ---\n\n" + content)
                except Exception as exc:
                    result["page_results"].append({"page": index + 1, "characters": 0, "status": "error", "error": type(exc).__name__})
                finally:
                    if textpage is not None:
                        textpage.close()
                    if page is not None:
                        page.close()
        finally:
            document.close()
        text = "".join(texts)
        result["extraction_status"] = "partial_page_errors" if any(p["status"] == "error" for p in result["page_results"]) else "extracted" if any(p["characters"] for p in result["page_results"]) else "no_extractable_text"
        result["warnings"].append("PDF text layer only; figures, image-only content and equations are not visually reviewed or OCR-transcribed.")
        return result, text
    if head.startswith(bytes.fromhex("D0CF11E0A1B11AE1")):
        result.update(detected_format="legacy_xls" if path.suffix.lower() == ".xls" else "legacy_doc", extraction_status="unsupported_legacy_binary")
        return result, ""
    if head.startswith(b"PK") and zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            if len(infos) > MAX_ARCHIVE_MEMBERS:
                raise ManualReaderLimit("Archive has too many members; manual review required.", "zip", {"member_count": len(infos), "member_limit": MAX_ARCHIVE_MEMBERS})
            names = {info.filename for info in infos}
            budget, texts = [0], []
            if "word/document.xml" in names:
                result["detected_format"] = "docx"
                result["embedded_image_count"] = sum(name.startswith("word/media/") for name in names)
                selected = [info for info in infos if re.fullmatch(r"word/(?:document|footnotes|endnotes|header\d+|footer\d+)\.xml", info.filename)]
                for info in selected:
                    tree = ET.fromstring(safe_member(archive, info, budget))
                    paragraphs = ["".join(node.text or "" for node in paragraph.iter() if node.tag.endswith("}t")) for paragraph in tree.iter() if paragraph.tag.endswith("}p")]
                    texts.append("\n\n--- OOXML PART " + info.filename + " ---\n\n" + "\n".join(paragraphs))
                result["warnings"].append("OOXML text only; embedded images are uninspected and physical page numbers are unknown.")
            elif "xl/workbook.xml" in names:
                result["detected_format"] = "xlsx"
                shared = []
                if "xl/sharedStrings.xml" in names:
                    tree = ET.fromstring(safe_member(archive, archive.getinfo("xl/sharedStrings.xml"), budget))
                    shared = ["".join(node.text or "" for node in item.iter() if node.tag.endswith("}t")) for item in tree if item.tag.endswith("}si")]
                for info in infos:
                    if not re.fullmatch(r"xl/worksheets/sheet\d+\.xml", info.filename):
                        continue
                    tree = ET.fromstring(safe_member(archive, info, budget))
                    cells = []
                    for cell in tree.iter():
                        if not cell.tag.endswith("}c"):
                            continue
                        values = [node.text or "" for node in cell.iter() if node.tag.endswith(("}v", "}t"))]
                        if cell.get("t") == "s" and values and values[0].isdigit() and int(values[0]) < len(shared):
                            values = [shared[int(values[0])]]
                        cells.append(cell.get("r", "?") + ": " + " ".join(values))
                    texts.append("\n\n--- OOXML PART " + info.filename + " ---\n\n" + "\n".join(cells))
                result["warnings"].append("Spreadsheet cell text only; formulas are not executed and table/sample interpretation is unverified.")
            else:
                result["detected_format"] = "zip"
                result["archive_member_names"] = sorted(names)
                for info in infos:
                    if Path(info.filename).suffix.lower() not in {".cif", ".xyz", ".pdb", ".res", ".ins", ".txt", ".csv"}:
                        continue
                    value = safe_member(archive, info, budget).decode("utf-8", errors="replace")
                    texts.append("\n\n--- ARCHIVE MEMBER " + info.filename + " ---\n\n" + value)
                result["warnings"].append("Only bounded plain-text/coordinate members inspected; remaining archive members require separate review. Nothing extracted or executed.")
            text = "".join(texts)
            body = re.sub(r"\n\n--- (?:OOXML PART|ARCHIVE MEMBER) [^\n]+ ---\n\n", "", text).strip()
            result["extraction_status"] = ("partial_archive_text" if result["detected_format"] == "zip" else "extracted") if body else "no_extractable_text"
            return result, text
    if path.suffix.lower() in {".cif", ".txt", ".csv", ".xyz", ".pdb", ".xml"}:
        if path.stat().st_size > MAX_MEMBER_BYTES:
            raise ManualReaderLimit("Plain text source exceeds bounded reader size.", path.suffix.lower()[1:], {"source_bytes": path.stat().st_size, "byte_limit": MAX_MEMBER_BYTES})
        text = path.read_text(encoding="utf-8", errors="replace")
        result.update(detected_format=path.suffix.lower()[1:], extraction_status="extracted" if text.strip() else "no_extractable_text")
        return result, text
    return result, ""


def screen_document(task):
    path = Path(task["source_path"])
    result = {**task, "status": "pending", "sha256": None, "hash_computed": False, "features": None,
              "text_characters_screened": 0, "source_unchanged_from_snapshot": False, "manual_flags": []}
    try:
        before = signature(path)
        digest = sha_file(path)
        result.update(sha256=digest, hash_computed=True, observed_signature=before)
        if signature(path) != before:
            result.update(status="changed_during_hash", manual_flags=["source_changed_during_screening"])
            return result
        unchanged = before == task["snapshot_signature"] and (not task.get("snapshot_sha256") or task["snapshot_sha256"] == digest)
        result["source_unchanged_from_snapshot"] = unchanged
        if not unchanged:
            result.update(status="changed_since_snapshot", manual_flags=["rescan_and_refingerprint_source_before_priority"])
            return result
        cache_path = OUTPUT / "cache/content" / (digest + ".json")
        cached = read_cache_json(cache_path) if cache_path.is_file() else None
        if cached and cached.get("sha256") == digest:
            text_path = cached.get("text_path")
            if text_path and not Path(text_path).is_absolute():
                text_path = str(HERE / text_path)
                cached["text_path"] = text_path
            if text_path and not Path(text_path).is_file():
                cached = None
        if cached and cached.get("version") == VERSION and cached.get("sha256") == digest:
            result.update(cached["extraction"], features=cached["features"], text_path=cached.get("text_path"), cache_source="screen_content_cache")
        else:
            old = LEGACY.get(digest)
            old_path = Path(old["text_path"]) if old and old.get("text_path") else None
            if cached and cached.get("sha256") == digest and "extraction" in cached:
                text_path = cached.get("text_path")
                text = Path(text_path).read_text(encoding="utf-8") if text_path else ""
                extraction = cached["extraction"]
                result["cache_source"] = "screen_raw_text_feature_recomputed"
            elif old_path and old_path.is_file():
                text = old_path.read_text(encoding="utf-8")
                extraction = {key: value for key, value in old.items() if key not in {"sha256", "text_path", "legacy_cache"}}
                extraction["warnings"] = ["Reused full text only after hashing this actual source copy; figures/images remain uninspected."]
                result["cache_source"] = "legacy_exact_sha256_text"
                text_path = str(old_path)
            else:
                with path.open("rb") as stream:
                    head = stream.read(1024)
                extraction, text = extract_source(path, head)
                # Bind newly obtained text to the actual bytes read, not a path
                # whose content may have changed during the extraction call.
                if signature(path) != before or sha_file(path) != digest:
                    result.update(status="changed_during_extraction", manual_flags=["source_changed_during_screening"])
                    return result
                result["cache_source"] = "new_extraction"
                text_path = None
                if text:
                    location = OUTPUT / "cache/text" / (digest + ".txt")
                    location.parent.mkdir(parents=True, exist_ok=True)
                    temporary = location.with_name(location.name + f".{os.getpid()}.tmp")
                    temporary.write_text(text, encoding="utf-8")
                    replace_with_retry(temporary, location)
                    text_path = str(location)
            features = text_features(text, digest)
            cache = {"version": VERSION, "sha256": digest, "text_path": text_path, "extraction": extraction, "features": features}
            atomic_json(cache_path, cache)
            result.update(extraction, features=features, text_path=text_path)
        if signature(path) != before:
            result.update(status="changed_during_screening", features=None, manual_flags=["source_changed_during_screening"])
            return result
        result["text_characters_screened"] = result["features"]["all_text_characters_examined"]
        result["status"] = "text_screened_candidate" if result["text_characters_screened"] else "manual_format_or_text_review_required"
        pages = result.get("page_results", [])
        result["empty_text_pages"] = [page["page"] for page in pages if page.get("status") == "no_extractable_text"]
        result["failed_text_pages"] = [page["page"] for page in pages if page.get("status") == "error"]
        if result["empty_text_pages"] or result["failed_text_pages"]:
            result["manual_flags"].append("some_source_pages_have_no_usable_text")
        if not result["text_characters_screened"]:
            result["manual_flags"].append("no_usable_text_is_not_evidence_of_no_recipe")
        if result.get("detected_format") in {"docx", "xlsx", "zip"}:
            result["manual_flags"].append("embedded_images_or_archive_structure_uninspected")
        if task.get("role_ambiguous"):
            result["manual_flags"].append("main_si_role_ambiguous")
    except ManualReaderLimit as exc:
        # A verified unchanged file outside the bounded parser's size limits is
        # a known manual-inspection obligation, not an unreliable hash or a
        # reason to discard the readable main paper's candidate priority.
        if signature(path) != before or sha_file(path) != digest:
            result.update(status="changed_during_extraction", features=None, manual_flags=["source_changed_during_screening"])
        else:
            result.update(status="manual_format_or_text_review_required", extraction_status="manual_reader_limit",
                          detected_format=exc.detected_format, reader_limit_reason=str(exc), reader_limit_details=exc.details,
                          features=text_features("", digest), cache_source="bounded_reader_manual_disposition",
                          page_results=[], empty_text_pages=[], failed_text_pages=[],
                          manual_flags=["bounded_reader_limit_requires_manual_inspection", "no_usable_text_is_not_evidence_of_no_recipe"])
    except FileNotFoundError as exc:
        result.update(status="source_or_cache_missing", error=str(exc), features=None)
    except Exception as exc:
        result.update(status="reader_or_hash_error", error=type(exc).__name__ + ": " + str(exc)[:400], features=None)
    return result


def tasks_from_ledger(ledger):
    tasks = []
    for name, item in ledger["files"].items():
        if not item.get("exists"):
            continue
        group_id = monitor.canonical_group(ledger, item["group_id"])
        tasks.append({"file_key": name, "source_path": str(monitor.file_path(ledger, name)),
                      "original_filename": item.get("relative_filename", name),
                      "source_collection": item.get("source_id", "incoming"), "group_id": group_id,
                      "origin_group_id": item.get("origin_group_id", item["group_id"]),
                      "source_generation": ledger["groups"][group_id]["generation"],
                      "snapshot_signature": {"bytes": item["size"], "mtime_ns": item["mtime_ns"]},
                      "snapshot_sha256": item.get("sha256"), "role_candidate": item["role"],
                      "role_candidates": item.get("role_candidates", []), "role_ambiguous": bool(item.get("role_ambiguous")),
                      "doi_candidates": item.get("doi_candidates", [])})
    return tasks


def rank_scopes(ledger, documents):
    bygroup = collections.defaultdict(list)
    for document in documents:
        bygroup[document["group_id"]].append(document)
    active = {claim["group_id"] for claim in monitor.active_claims(ledger)}
    main_clusters = collections.defaultdict(list)
    scopes = []
    for key, group in ledger["groups"].items():
        if group.get("alias_of") or key not in bygroup:
            continue
        copies = bygroup[key]
        unique = {item["sha256"]: item for item in copies if item.get("sha256") and item.get("features")}
        counts = collections.Counter()
        snippets, coordinate_snippets, samples = [], [], set()
        for item in unique.values():
            counts.update(item["features"]["counts"])
            snippets.extend(item["features"]["snippets"])
            coordinate_snippets.extend(item["features"].get("coordinate_context_snippets", []))
            samples.update(item["features"]["sample_identifier_mentions"])
        recipe = min(14, counts["recipe_windows"] * 3 + min(3, counts["partial_recipe_windows"]))
        structural = max([0] + [score for feature, score in (("coordinate_data", 16), ("refinement", 11), ("lattice_phase", 7), ("diffraction", 4), ("contextual_coordinate_data", 3), ("coordinate_mention", 2), ("morphology", 1)) if counts[feature]])
        both = recipe >= 3 and structural >= 4
        score = recipe + structural + (8 if both else 0) + (2 if both and samples else 0)
        if recipe >= 3 and counts["coordinate_data"]:
            tier = "A_recipe_and_coordinate_candidates"
        elif recipe >= 3 and (counts["refinement"] or counts["lattice_phase"] or counts["diffraction"]):
            tier = "B_recipe_and_crystalline_evidence_candidates"
        elif recipe >= 3:
            tier = "C_recipe_candidates"
        elif any(not item.get("features") or not item.get("text_characters_screened") for item in copies):
            tier = "U_manual_or_unreadable_scope"
        else:
            tier = "D_low_signal_candidates_not_exclusions"
        unsafe = any(not item.get("source_unchanged_from_snapshot") or item["status"] in {"source_or_cache_missing", "reader_or_hash_error", "changed_during_hash", "changed_during_extraction", "changed_during_screening"} for item in copies)
        flags = sorted({flag for item in copies for flag in item.get("manual_flags", [])})
        if any(counts[feature] for feature in ("coordinate_data", "contextual_coordinate_data", "coordinate_mention")):
            flags.append("coordinate_product_and_sample_identity_requires_manual_review")
        if counts["computed_or_reference_coordinate_context"] or counts["molecular_or_precursor_context_product_link_unknown"]:
            flags.append("contextual_coordinates_do_not_establish_target_product_structure")
        if not any(item["role_candidate"] == "main" for item in copies):
            flags.append("main_document_missing_or_unmatched")
        if not any(item["role_candidate"] == "si" for item in copies):
            flags.append("si_not_present_in_frozen_candidate_group")
        main_hashes = {item["sha256"] for item in copies if item["role_candidate"] == "main" and item.get("sha256")}
        if len(main_hashes) == 1 and not any(item["role_ambiguous"] for item in copies):
            main_clusters[next(iter(main_hashes))].append(key)
        if len(main_hashes) > 1:
            flags.append("multiple_main_versions_require_identity_review")
        snippets.sort(key=lambda item: -item["candidate_priority"])
        scopes.append({"group_id": key, "score": score, "source_generation": group["generation"],
                       "queue_order": group["queue_order"], "first_seen_at": group.get("first_seen_at"),
                       "order_basis": group.get("order_basis"), "doi_candidates": group.get("doi_candidates", []),
                       "priority_tier": tier, "priority_applicable": not unsafe,
                       "current_batch_member": key in active, "saved_review_status": group["review"]["status"],
                       "needs_recheck_in_snapshot": group["needs_recheck"], "file_keys": [item["file_key"] for item in copies],
                       "source_hashes": sorted({item["sha256"] for item in copies if item.get("sha256")}),
                       "main_hashes": sorted(main_hashes), "unique_text_contents": len(unique),
                       "feature_counts": dict(counts), "recipe_score": recipe, "structure_score": structural,
                       "sample_identifier_mentions": sorted(samples)[:30], "candidate_snippets": snippets[:8],
                       "coordinate_context_snippets": coordinate_snippets[:8],
                       "manual_flags": flags, "main_si_pairing_status": "candidate_association_not_verified_by_screen",
                       "sample_join_status": "unverified_no_cross_source_or_cross_specimen_join",
                       "failed_or_nonideal_outcomes_retained": counts["failure_or_nonideal_outcome"] > 0,
                       "screening_status": "automated_candidate_screen_only", "terminal_review_status_assigned": False})
    scopes.sort(key=lambda item: (-item["score"], item["queue_order"], item["group_id"]))
    return scopes, [{"main_sha256": digest, "group_ids": sorted(keys, key=lambda key: ledger["groups"][key]["queue_order"]),
                     "basis": "Actual identical main bytes; supplement association remains candidate and distinct copies retained."}
                    for digest, keys in main_clusters.items() if len(keys) > 1]


def run(snapshot, output, legacy_manifest=LEGACY_MANIFEST, workers=4):
    output = output.resolve()
    raw = snapshot.read_bytes()
    ledger = json.loads(raw)
    tasks = tasks_from_ledger(ledger)
    output.mkdir(parents=True, exist_ok=True)
    index = legacy_index(legacy_manifest)
    started = time.time()
    results = []
    def progress(state):
        data = {"version": VERSION, "state": state, "started_at": monitor.iso(int(started * monitor.SECOND)),
                "updated_at": monitor.iso(time.time_ns()), "snapshot_sha256": hashlib.sha256(raw).hexdigest(),
                "snapshot_present_files": len(tasks), "processed_files": len(results), "remaining_files": len(tasks) - len(results),
                "actual_source_hashes_computed": sum(item.get("hash_computed", False) for item in results),
                "status_counts": dict(collections.Counter(item["status"] for item in results)),
                "cache_counts": dict(collections.Counter(item.get("cache_source", "no_text_screen") for item in results)),
                "elapsed_seconds": round(time.time() - started, 1), "review_state_changed": False}
        atomic_json(output / "progress.json", data)
        print(json.dumps(data), flush=True)
        return data
    progress("running")
    with (output / "documents.jsonl").open("w", encoding="utf-8") as stream:
        with concurrent.futures.ProcessPoolExecutor(max_workers=max(1, min(workers, 4)), initializer=initialize_worker, initargs=(index, str(output))) as pool:
            pending, iterator = {}, iter(tasks)
            def fill():
                while len(pending) < max(1, min(workers, 4)) * 2:
                    task = next(iterator, None)
                    if task is None:
                        break
                    pending[pool.submit(screen_document, task)] = task
            fill()
            last = time.monotonic()
            while pending:
                done, _ = concurrent.futures.wait(pending, timeout=10, return_when=concurrent.futures.FIRST_COMPLETED)
                for future in done:
                    task = pending.pop(future)
                    try:
                        item = future.result()
                    except Exception as exc:
                        item = {**task, "status": "worker_error", "sha256": None, "hash_computed": False, "features": None,
                                "source_unchanged_from_snapshot": False, "error": type(exc).__name__ + ": " + str(exc)[:400],
                                "manual_flags": ["worker_error_requires_review"]}
                    results.append(item)
                    stream.write(json.dumps(item, ensure_ascii=False) + "\n")
                fill()
                if time.monotonic() - last >= 20 or not pending:
                    stream.flush()
                    progress("running")
                    last = time.monotonic()
    if raw != snapshot.read_bytes():
        raise ValueError("Frozen ledger input changed during screening; report not released.")
    scopes, clusters = rank_scopes(ledger, results)
    report = {"schema": "mattersyn-corpus-priority-screen/1", "version": VERSION, "mode": "evidence_richness",
              "screened_at": monitor.iso(time.time_ns()), "require_screened": True,
              "source_snapshot": str(snapshot.resolve()), "source_snapshot_sha256": hashlib.sha256(raw).hexdigest(),
              "source_ledger_last_scan_at": ledger.get("last_scan_at"), "frozen_scope": "Every exists=true file in the immutable input; later arrivals belong to a later snapshot.",
              "current_batch_preserved": ledger.get("current_batch"), "original_arrival_order_preserved": True,
              "review_state_changed": False, "scientific_review_performed": False,
              "rankings": [{key: scope[key] for key in ("group_id", "score", "source_generation", "queue_order", "priority_tier")} for scope in scopes if scope["priority_applicable"]],
              "scopes": scopes, "actual_duplicate_main_clusters": clusters,
              "counts": {"snapshot_present_files": len(tasks), "per_file_dispositions": len(results),
                         "actual_source_hashes_computed": sum(item.get("hash_computed", False) for item in results),
                         "unique_source_hashes": len({item["sha256"] for item in results if item.get("sha256")}),
                         "scope_count": len(scopes), "applicable_priority_scopes": sum(scope["priority_applicable"] for scope in scopes),
                         "text_screened_copies": sum(item.get("text_characters_screened", 0) > 0 for item in results),
                         "unique_text_contents_screened": len({item["sha256"] for item in results if item.get("text_characters_screened", 0) > 0}),
                         "detected_formats": dict(collections.Counter(item.get("detected_format", "not_read") for item in results)),
                         "status_counts": dict(collections.Counter(item["status"] for item in results)),
                         "cache_counts": dict(collections.Counter(item.get("cache_source", "no_text_screen") for item in results)),
                         "copies_with_empty_text_pages": sum(bool(item.get("empty_text_pages")) for item in results),
                         "copies_with_failed_text_pages": sum(bool(item.get("failed_text_pages")) for item in results),
                         "priority_tiers": dict(collections.Counter(scope["priority_tier"] for scope in scopes))},
              "interpretation": ["Scores order candidate inspection only; no paper is declared fully read, audited, published or lacking synthesis.",
                                 "Numeric coordinate-table candidates outrank generic morphology words. Coordinate mentions and explicit computed, reference, molecular or precursor contexts receive lower coordinate bonuses; exact target/sample linkage remains manual.",
                                 "A shared DOI, title, page or main/SI group does not establish specimen identity or a structure-to-recipe training pair.",
                                 "No signal, unsupported files, no-text pages and missing SI retain manual work; failed outcomes and partial recipes remain candidates.",
                                 "All original source names, locations, saved queue orders and current batch claims remain unchanged."]}
    atomic_json(output / "ranked-scopes.json", report)
    lines = ["# Automated corpus candidate screen", "", "Private frozen-snapshot screening; no full scientific reviews or negative synthesis dispositions assigned.", "",
             f"Files accounted for: {len(results):,}/{len(tasks):,}. Actual source hashes: {report['counts']['actual_source_hashes_computed']:,}. Provisional scopes: {len(scopes):,}.", "",
             "| Candidate group | Score | Tier | Original queue order |", "|---|---:|---|---:|"]
    lines += [f"| {scope['group_id']} | {scope['score']} | {scope['priority_tier']} | {scope['queue_order']} |" for scope in scopes[:30]]
    lines += ["", *["- " + value for value in report["interpretation"]], ""]
    (output / "screening-report.md").write_text("\n".join(lines), encoding="utf-8")
    final = progress("complete")
    final.update(report=str(output / "ranked-scopes.json"), report_sha256=sha_file(output / "ranked-scopes.json"))
    atomic_json(output / "progress.json", final)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger-snapshot", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--legacy-manifest", type=Path, default=LEGACY_MANIFEST)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    run(args.ledger_snapshot, args.output_dir, args.legacy_manifest, args.workers)


if __name__ == "__main__":
    main()
