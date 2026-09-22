"""Offline, private candidate ranking. Never approves a pair or excludes a paper.

Reads only the frozen corpus metadata and its existing hash-named text caches.
Source SHA binding is historical; current source bytes are not rehashed here.
No source, shared ledger, website, network, or installed-skill writes.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import time
import unicodedata

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent.parent
MONITOR = ASSETS / "incoming-paper-monitor"
SCREEN = MONITOR / "deadline-20260920/workflow-20260920T0412/screen"
VERSION = "offline-evidence-link-candidates-0.2"
INPUTS = {
    "documents": (SCREEN / "documents.jsonl", "2080a1670705ff95b974eb8b7bcb568c4f1350cd9884f515531ca54d15b911b9"),
    "screen_report": (SCREEN / "ranked-scopes.json", "b702062046c5f7d3bfff9a632305959a90590085264c473a6b9d7e0ed649c2bd"),
    "partition": (MONITOR / "deadline-20260920/resume-20260922/resume-partition.json", "7d9c710adf853e1a8f6a9c91d2f82c062e34fe1cff3b2e23be813450d8a5451f"),
    "partition_ledger": (MONITOR / "deadline-20260920/resume-20260922/activation/ledger-before-activation.json", "bfa88ac323d11223c968bc4bbd801e2391b11ddeedab6228cf78c0713f1909be"),
    "inventory": (MONITOR / "deadline-20260920/cutoff-20260920T033439542641Z/file-inventory.json", "f136130e5ada95206cd90499bc7241ba17ec64ab466fd01a224dc771fa475971"),
    "validity_overlay": (ASSETS / "one-month-20260922/duplicate-audit/pair-source-validity-overlay.json", "71ee670ef8b9604d5692a3c8147101f309fe541d7eeb8e85c90ded0a4d949ae9"),
    "rubric": (HERE.parent / "rubric-audit/pair-quality-rubric.json", "281a9b061a473161a8bfa66b594c95eb40ef0fa42b2bf59acd29a9d6f46808c3"),
    "nested_screen": (MONITOR / "deadline-20260920/workflow-20260920T0412/screen-coverage-check.json", "2618e069e7feadb3435825e4056cac2e1db90ac0ecc1f64f0e1e8cfaec7954e1"),
}
MARKER = re.compile(r"\n\n--- (PAGE \d+|OOXML PART [^\n]+|ARCHIVE MEMBER [^\n]+) ---\n\n")

def rx(pattern):
    return re.compile(pattern, re.I)

OPERATION = rx(r"\b(?:dissolv\w*|inject\w*|stirr?\w*|heat\w*|anneal\w*|calcin\w*|reflux\w*|centrifug\w*|wash\w*|degas\w*|precipitat\w*|dropwise|autoclave|electrodeposit\w*|spin.coat\w*|evaporat\w*|mix(?:ed|ing)|dry(?:ing|ied)|dried)\b")
METHOD = rx(r"\b(?:synthes(?:is|ized)|prepar(?:ation|ed)|fabricat(?:ion|ed)|growth procedure|experimental(?: section)?|materials and methods)\b")
FIELDS = {
    "amount": rx(r"(?<!\w)\d+(?:\.\d+)?\s*(?:[µμu]?mol|mmol|mol|[µμm]?g|[µμm]?l|mL|M|mM)\b"),
    "temperature": rx(r"\d+(?:\.\d+)?\s*(?:[°º]\s*[CF]|kelvin|[CK]\b)|room temperature|ambient temperature"),
    "duration": rx(r"\d+(?:\.\d+)?\s*(?:min(?:utes?)?|hours?|hrs?|h|seconds?|sec|s)\b|overnight"),
    "solvent": rx(r"\b(?:solvent|solution|water|aqueous|ethanol|methanol|toluene|hexane|octadecene|oleylamine|chloroform|acetone|DMF|DMSO|THF)\b"),
    "atmosphere": rx(r"\b(?:under (?:nitrogen|argon|vacuum)|inert atmosphere|N2 atmosphere|Ar atmosphere|degass\w*)\b"),
    "workup": rx(r"\b(?:centrifug\w*|wash\w*|precipitat\w*|filtrat\w*|filtered|dialys\w*|purif\w*|redispers\w*)\b"),
}
COORD = rx(r"_atom_site_(?:fract|cartn)_[xyz]|\b(?:(?:fractional|Cartesian|atomic)(?: atomic)? (?:coordinates|positions)|positional(?:,? thermal)?(?:,? and)? occupancy parameters[a-z]?|crystallographic information file)\b")
AXES = rx(r"\bx(?:\s*/\s*a)?\s+y(?:\s*/\s*b)?\s+z(?:\s*/\s*c)?\b|_atom_site_(?:fract|cartn)_[xyz]")
ATOM_ROW = re.compile(r"^\s*(\([A-Z][a-z]?(?:,[A-Z][a-z]?)+\)|[A-Z][a-z]?(?:\d+[A-Za-z]?|\([^\s)]+\))?)\s+(.+)$")
ELEMENTS = set("H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og".split())
NUMBER = re.compile(r"(?<![\w.])[-+−]?(?:\d+\.\d*|\.\d+|\d+)(?:\(\d+\))?(?![\w.])")
MEASURED = rx(r"\b(?:Rietveld|single.crystal (?:X.ray|diffraction)|X.ray (?:crystal )?structure (?:analysis|determination)|refined (?:atomic |fractional )?(?:coordinates|positions)|(?:atomic |fractional )?(?:coordinates|positions) (?:was |were )?refined|(?:crystal )?structure (?:of sample [A-Z0-9.-]+ )?(?:was |were )?(?:solved|refined)|crystallographic refinement)\b|_refine_ls_R_factor|_diffrn_measurement")
DEPOSIT = rx(r"\b(?:CCDC\s*(?:no\.?|number|nos\.?)?\s*[:#]?\s*\d{4,}|deposited.{0,100}(?:crystallographic|CIF|CCDC|CSD)|(?:CIF|crystallographic data).{0,80}deposited)\b")
PHASE = rx(r"\b(?:X.ray diffraction|XRD|powder diffraction|SAED|space group|lattice (?:parameter|constant)|unit.cell|crystal(?:line)? phase|Rietveld)\b")
MORPH = rx(r"\b(?:HRTEM|HR.TEM|TEM|SEM|transmission electron microscop\w*|scanning electron microscop\w*|morphology|particle size|size distribution|diameter|nanocubes?|nanorods?|nanoplates?)\b")
ORIGINS = {
    "theory_or_optimized_model": rx(r"\b(?:density functional|DFT|theoretical|computed|computational|geometry optimi[sz]|optimi[sz]ed (?:Cartesian|atomic|geometry)|molecular dynamics|simulated (?:structure|model)|calculated (?:atomic|Cartesian) coordinates)\b"),
    "external_or_reference": rx(r"\b(?:ICSD|COD\s*\d|JCPDS|PDF card|reference (?:structure|pattern)|bulk reference|taken from (?:the )?literature|coordinates.{0,60}(?:from|reported by)|structure.{0,50}(?:adopted from|taken from))\b"),
    "precursor_or_molecular_context": rx(r"\b(?:precursor (?:crystal|structure|complex)|(?:structure|coordinates|crystal).{0,60}(?:molecular precursor|precursor complex)|molecular (?:complex|crystal|structure)|organic molecule)\b"),
    "fixed_or_constrained_positions": rx(r"\b(?:(?:atomic |fractional )?(?:coordinates|positions).{0,90}(?:fixed|constrained)|(?:fixed|constrained).{0,90}(?:coordinates|positions)|fixed (?:these |the |atomic )?parameters|could not be refined)\b"),
    "negated_or_prior_work_structure": rx(r"\b(?:not (?:be )?refined|no (?:crystal )?structure was determined|(?:coordinates|refinement).{0,80}reported previously|could not (?:be )?(?:refine|determine))\b"),
}
INSTRUMENT = rx(r"\b(?:recorded (?:on|using|with)|scan rate|diffractometer|spectrometer|instrument calibration)\b")
REFERENCES = rx(r"^\s*(?:\d+\.?\s+)?(?:references|bibliography|literature cited)\s*$")
SAMPLE = re.compile(r"\b(?i:sample|specimen|batch)\s*(?:(?i:no)\.?\s*)?[:#-]?\s*((?:[A-Z]{1,6}[-:]?\d+(?:\.\d+)?[A-Za-z]?|\d+[A-Za-z]?|[A-Z])(?:[-:]\d+(?:\.\d+)?[A-Za-z]?)*)\b|(?<!\w)(S\d+(?:\.\d+)?(?:[-:]\d+(?:\.\d+)?[A-Za-z]?)*)(?![\w.-])")
EXPLICIT_PRODUCT = rx(r"\b(?:as.synthesized|as.prepared|as.obtained|freshly (?:synthesized|prepared)|synthesized (?:nanocrystals|nanoparticles|samples)|prepared (?:nanocrystals|nanoparticles|samples)|obtained (?:nanocrystals|nanoparticles|samples))\b")
FIGTABLE = rx(r"\b(?:Figure|Fig\.?|Table|Scheme)\s+[S]?\d+[a-z]?\b")
LINK_METHOD = "No formula-only, same-page-only or cross-source association is treated as an explicit sample link."
BANDS = ["A_atomic_with_local_link_candidate", "B_atomic_link_unknown_candidate", "C_phase_with_local_link_candidate", "D_morphology_with_local_link_candidate", "E_non_target_coordinate_context_candidate", "R_recipe_only_or_structure_link_unknown", "U_insufficient_or_manual_review"]

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def normal(text):
    return unicodedata.normalize("NFKC", text.replace("\ufffe", "")).replace("−", "-")

def split_blocks(text):
    parts = MARKER.split(text)
    result = [(None, parts[0])] if parts[0].strip() else []
    return result + [(parts[n], parts[n+1]) for n in range(1, len(parts)-1, 2)]

def tokens(text):
    text = FIGTABLE.sub(" ", text)
    text = rx(r"\b(?:section|equation|eq\.?)\s+S\d+(?:\.\d+)?\b").sub(" ", text)
    return sorted({a or b for a, b in SAMPLE.findall(text)})

def atom_row(line):
    match = ATOM_ROW.match(normal(line))
    if not match:
        return False
    symbols = re.findall(r"[A-Z][a-z]?", match[1])
    return bool(symbols and symbols[0] in ELEMENTS and len(NUMBER.findall(match[2])) >= 3)

def cue_window(text):
    """Cue extraction, not interpretation or chemistry verification."""
    row_text = normal(text)
    n = " ".join(row_text.split())
    fields = [key for key, pattern in FIELDS.items() if pattern.search(n)]
    operations = len(OPERATION.findall(n))
    recipe = bool((operations >= 2 or (operations >= 1 and METHOD.search(n))) and "amount" in fields and ("temperature" in fields or "duration" in fields or "workup" in fields))
    if INSTRUMENT.search(n) and not METHOD.search(n):
        recipe = False
    partial = bool(METHOD.search(n)) and operations > 0
    coordinate_mention = bool(COORD.search(n))
    atom_rows = []
    for line in row_text.splitlines():
        if atom_row(line):
            atom_rows.append(line.strip())
    table = coordinate_mention and bool(AXES.search(n)) and len(atom_rows) >= 2
    explicit_refined_positions = bool(rx(r"\b(?:atomic positions|fractional coordinates|atomic coordinates).{0,160}\b(?:were|was) refined\b").search(n))
    measured = bool(MEASURED.search(n)) or explicit_refined_positions
    deposited = bool(DEPOSIT.search(n))
    origins = [key for key, pattern in ORIGINS.items() if pattern.search(n)]
    atomic = table or deposited or (coordinate_mention and measured)
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", n)
    recipe_sentences = [s for s in sentences if OPERATION.search(s) and (METHOD.search(s) or FIELDS["amount"].search(s))]
    structure_sentences = [s for s in sentences if COORD.search(s) or PHASE.search(s) or MORPH.search(s)]
    recipe_tokens = sorted({t for s in recipe_sentences for t in tokens(s)})
    structure_tokens = sorted({t for s in structure_sentences for t in tokens(s)})
    return {"recipe_candidate": recipe, "partial_procedure_candidate": partial,
            "procedure_field_cues": fields, "operation_cues": operations,
            "coordinate_mention": coordinate_mention, "numeric_atom_table_candidate": table,
            "numeric_atom_row_count": len(atom_rows) if coordinate_mention else 0,
            "experimental_refinement_cue": measured, "deposit_identifier_cue": deposited,
            "explicit_refined_positions_statement": explicit_refined_positions,
            "atomic_evidence_candidate": atomic,
            "phase_cue": bool(PHASE.search(n)), "morphology_cue": bool(MORPH.search(n)),
            "origin_warnings": origins, "sample_tokens": tokens(n),
            "recipe_sample_tokens": recipe_tokens, "structure_sample_tokens": structure_tokens,
            "different_recipe_structure_samples": bool(recipe_tokens and structure_tokens and not set(recipe_tokens).intersection(structure_tokens)),
            "explicit_synthesis_product_reference": any(EXPLICIT_PRODUCT.search(s) for s in structure_sentences),
            "figure_table_labels": sorted(set(FIGTABLE.findall(n)))}

def atomic_table_windows(blocks, digest):
    """Page-aware table cues and actual CIF atom-site loops.

    A header may continue only onto the immediately following text block with
    leading atom rows/coordinate axes. New table captions end that association.
    Origin qualifiers stay with the inherited header; components are not joined.
    """
    result, previous = [], None
    for block_no, (marker, body) in enumerate(blocks, 1):
        lines = body.splitlines()
        if "_atom_site_" in body:
            for begin, line in enumerate(lines):
                if line.strip().lower() != "loop_":
                    continue
                tags, cursor = [], begin + 1
                while cursor < len(lines) and (not lines[cursor].strip() or lines[cursor].strip().startswith("_")):
                    if lines[cursor].strip():
                        tags.append(lines[cursor].strip().split()[0].lower())
                    cursor += 1
                axes = [f"_atom_site_fract_{x}" for x in "xyz"]
                if not all(t in tags for t in axes):
                    axes = [f"_atom_site_cartn_{x}" for x in "xyz"]
                if not all(t in tags for t in axes) or "_atom_site_label" not in tags:
                    continue
                end = cursor
                while end < len(lines) and not lines[end].strip().lower().startswith(("loop_", "data_", "_")):
                    end += 1
                row_count = sum(atom_row(x) for x in lines[cursor:end])
                if row_count < 2:
                    continue
                begin_context = max(0, begin-35)
                excerpt = "\n".join(lines[begin_context:end])
                features = cue_window(excerpt)
                features.update(coordinate_mention=True, numeric_atom_table_candidate=True, numeric_atom_row_count=row_count, atomic_evidence_candidate=True)
                result.append({"cue_id": f"{digest[:16]}:b{block_no}:cif{begin+1}", "source_sha256": digest,
                               "locator": {"page": None, "text_block": marker, "block_index": block_no, "line_start": begin+1, "line_end": end},
                               **features, "reference_section_candidate": False, "table_detection": "actual_cif_atom_site_loop",
                               "coordinate_axis_tags": axes, "target_identity_status": "coordinate_file_target_and_product_link_unknown",
                               "text_excerpt": " ".join(normal(excerpt).split())[:1700]})
            previous = None
            continue
        starts = [i for i, line in enumerate(lines) if re.match(r"\s*Table\s+S?\d+[.:]?", line, re.I)]
        starts = sorted(set([0] + starts))
        next_previous = None
        for segment_index, start in enumerate(starts):
            stop = starts[segment_index+1] if segment_index+1 < len(starts) else len(lines)
            segment = lines[start:stop]
            flat = " ".join(normal("\n".join(segment)).split())
            own_header = bool(COORD.search(flat))
            nonempty = [(i, x) for i, x in enumerate(segment) if x.strip()]
            new_caption = bool(nonempty and re.match(r"\s*Table\s+S?\d+", nonempty[0][1], re.I))
            leading_table = any(atom_row(x) or AXES.search(x) for _, x in nonempty[:5])
            inherit = previous if start == 0 and not new_caption and not own_header and leading_table else None
            if not own_header and not inherit:
                continue
            rows = [i for i, line in enumerate(segment) if atom_row(line)]
            has_axes = bool(AXES.search(flat)) or bool(inherit and inherit["has_axes"])
            if own_header:
                coord_lines = [i for i in range(len(segment)) if COORD.search(" ".join(normal(" ".join(segment[i:i+3])).split()))]
                header_start = max(0, min(coord_lines, default=0)-1)
                # Do not take unrelated atom-like rows before a late table caption.
                rows = [i for i in rows if i >= header_start]
                first_row = min(rows, default=len(segment))
                header = "\n".join(segment[header_start:first_row])
                header_locator = {"page": int(marker[5:]) if marker and marker.startswith("PAGE ") else None,
                                  "text_block": marker, "line_start": start+header_start+1}
            else:
                header, header_locator = inherit["header"], inherit["header_locator"]
                header_start = 0
            if len(rows) >= 2 and has_axes:
                end = min(len(segment), max(rows)+9)
                excerpt = (header + "\n" if inherit else "") + "\n".join(segment[header_start:end])
                features = cue_window(excerpt)
                features.update(coordinate_mention=True, numeric_atom_table_candidate=True, numeric_atom_row_count=len(rows), atomic_evidence_candidate=True)
                result.append({"cue_id": f"{digest[:16]}:b{block_no}:table{start+1}", "source_sha256": digest,
                               "locator": {"page": int(marker[5:]) if marker and marker.startswith("PAGE ") else None,
                                           "text_block": marker, "block_index": block_no, "line_start": start+header_start+1, "line_end": start+end},
                               **features, "reference_section_candidate": False,
                               "table_detection": "adjacent_page_header_continuation_candidate" if inherit else "page_table_header_and_atom_rows",
                               "table_header_locator": header_locator,
                               "component_assignment": "unresolved_do_not_transfer_refined_or_fixed_origin_between_components",
                               "text_excerpt": " ".join(normal(excerpt).split())[:1700]})
            # Carry a last-page table or dangling coordinate caption forward,
            # never a general mention elsewhere on the page.
            if segment_index == len(starts)-1 and (rows or (own_header and (new_caption or header_start >= max(0, len(segment)-15)))):
                next_previous = {"header": header, "header_locator": header_locator, "has_axes": has_axes}
        previous = next_previous
    return result

def scan_text(text, digest):
    blocks = split_blocks(text)
    windows = []
    in_refs = False
    ref_count = 0
    for block_no, (marker, body) in enumerate(blocks, 1):
        lines = body.splitlines()
        # SI commonly resumes tables/spectra after its references. Do not
        # suppress the rest of that source merely because references appeared.
        if in_refs and any(re.match(r"\s*(?:Table|Figure|Scheme)\s+S?\d+\b|\s*(?:Experimental|Synthesis|Atomic coordinates|Fractional coordinates)\b", line, re.I) for line in lines[:20]):
            in_refs = False
        # Overlapping 14-line windows retain nearby row labels and units. The
        # relation rule below still requires named/referring product language.
        for start in range(0, len(lines), 7):
            selected = lines[start:start+14]
            reference_heading = any(REFERENCES.match(line.strip()) for line in selected)
            if reference_heading:
                in_refs = True
            chunk = "\n".join(selected)
            features = cue_window(chunk)
            interesting = any(features[k] for k in ("recipe_candidate", "partial_procedure_candidate", "coordinate_mention", "atomic_evidence_candidate", "phase_cue", "morphology_cue"))
            if not interesting:
                continue
            if in_refs:
                ref_count += 1
            locator = {"page": int(marker[5:]) if marker and marker.startswith("PAGE ") else None,
                       "text_block": marker, "block_index": block_no, "line_start": start+1, "line_end": min(start+14, len(lines))}
            windows.append({"cue_id": f"{digest[:16]}:b{block_no}:l{start+1}", "source_sha256": digest,
                            "locator": locator, **features, "reference_section_candidate": in_refs,
                            "text_excerpt": " ".join(normal(chunk).split())[:1700]})
    windows.extend(atomic_table_windows(blocks, digest))
    eligible = [w for w in windows if not w["reference_section_candidate"]]
    recipes = [w for w in eligible if w["recipe_candidate"]]
    links = []
    for w in eligible:
        if not (w["atomic_evidence_candidate"] or w["phase_cue"] or w["morphology_cue"]):
            continue
        candidate_recipes = []
        local_shared = sorted(set(w["recipe_sample_tokens"]) & set(w["structure_sample_tokens"]))
        unambiguous_local_ids = len(w["recipe_sample_tokens"]) <= 1 and len(w["structure_sample_tokens"]) <= 1
        if w["recipe_candidate"] and unambiguous_local_ids and not w["different_recipe_structure_samples"] and (local_shared or w["explicit_synthesis_product_reference"]):
            candidate_recipes.append((w, "local_procedure_with_named_or_explicitly_synthesized_product_cue", local_shared))
        for r in recipes:
            shared = sorted(set(r["recipe_sample_tokens"]) & set(w["structure_sample_tokens"]))
            if r["cue_id"] != w["cue_id"] and shared and len(r["recipe_sample_tokens"]) == 1 and len(w["structure_sample_tokens"]) == 1:
                candidate_recipes.append((r, "same_source_explicit_sample_token_recurrence_candidate", shared))
        # A local 'as-prepared' measurement may nominate a referential link to
        # a separately located procedure in the same source; no batch join.
        referential_recipes = [r for r in recipes if len(r["recipe_sample_tokens"]) <= 1 and len(w["structure_sample_tokens"]) <= 1 and not (r["recipe_sample_tokens"] and w["structure_sample_tokens"] and not set(r["recipe_sample_tokens"]).intersection(w["structure_sample_tokens"]))]
        if not candidate_recipes and w["explicit_synthesis_product_reference"] and referential_recipes:
            candidate_recipes.append((referential_recipes[0], "same_source_as_synthesized_reference_candidate_identity_unresolved", []))
        for r, basis, shared in candidate_recipes[:3]:
            links.append({"recipe_cue_id": r["cue_id"], "structure_cue_id": w["cue_id"], "basis": basis,
                          "shared_sample_tokens": shared, "status": "machine_relation_candidate_not_verified_sample_join"})
    return {"source_sha256": digest, "text_blocks_examined": len(blocks),
            "all_text_characters_examined": sum(len(b.strip()) for _, b in blocks),
            "recipe_cue_count": len(recipes), "reference_candidate_windows_retained": ref_count,
            "cues": windows, "link_candidates": links}

def jsonline(stream, obj):
    stream.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n")

def load_inputs():
    loaded, bindings = {}, {}
    for key, (path, expected) in INPUTS.items():
        raw = path.read_bytes()
        actual = sha(raw)
        if actual != expected:
            raise ValueError(f"Frozen {key} hash mismatch: {actual}")
        loaded[key] = [json.loads(line) for line in raw.decode("utf-8").splitlines()] if key == "documents" else json.loads(raw)
        bindings[key] = {"path": str(path), "sha256": actual, "bytes": len(raw)}
    return loaded, bindings

def cache_binding(doc):
    digest, supplied = doc.get("sha256"), doc.get("text_path")
    base = {"source_sha256": digest, "text_path": supplied,
            "binding_basis": "frozen_hashed_documents_metadata_and_hash_named_cached_text",
            "current_source_bytes_rehashed": False,
            "historical_text_hash_available": False,
            "historical_text_authentication_limit": "Original screening did not store text SHA256; current cache bytes are newly hashed and historically bound by source metadata/path and character count, not cryptographic equality to original text."}
    if not digest or not supplied or not doc.get("hash_computed") or not doc.get("source_unchanged_from_snapshot"):
        return {**base, "status": "missing_or_untrusted_historical_source_binding"}, None
    path = Path(supplied)
    allowed = [ASSETS / "corpus-20260917/private/text", MONITOR / "corpus-screening/20260919/cache/text", SCREEN / "cache/text"]
    if path.resolve().parent not in [p.resolve() for p in allowed] or path.stem != digest:
        return {**base, "status": "cache_path_binding_mismatch"}, None
    if not path.is_file():
        return {**base, "status": "cache_missing"}, None
    before = path.stat()
    raw = path.read_bytes()
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        return {**base, "status": "cache_changed_during_read"}, None
    # The first-stage scanner used Path.read_text(), whose universal-newline
    # translation differs from bytes.decode() on Windows CRLF caches.
    text = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    count = sum(len(b.strip()) for _, b in split_blocks(text))
    expected = (doc.get("features") or {}).get("all_text_characters_examined")
    status = "historically_bound_cache_candidate" if expected == count else "cache_character_count_mismatch_hold"
    return {**base, "text_sha256": sha(raw), "text_bytes": len(raw), "text_characters": count,
            "frozen_screen_characters": expected, "status": status}, text if expected == count else None

def summarize_scope(group, docs, scans, file_states):
    usable = {d["sha256"] for d in docs if file_states[d["file_key"]]["eligible_for_candidate_cues"]}
    cues, links = [], []
    for digest in sorted(usable):
        cues += [c for c in scans[digest]["cues"] if not c["reference_section_candidate"]]
        links += scans[digest]["link_candidates"]
    byid = {c["cue_id"]: c for c in cues}
    mixed = [c for c in cues if c["numeric_atom_table_candidate"] and c.get("explicit_refined_positions_statement") and c["origin_warnings"] == ["fixed_or_constrained_positions"]]
    atomic = [c for c in cues if c["atomic_evidence_candidate"] and not c["origin_warnings"]] + mixed
    # Deposited/CIF tables without local experimental cues are retained as
    # atomic candidates of UNKNOWN origin; they cannot enter the top band.
    measured = [c for c in atomic if c["experimental_refinement_cue"] and not c["origin_warnings"]]
    linked_ids = {x["structure_cue_id"] for x in links}
    recipes = [c for c in cues if c["recipe_candidate"]]
    explicit_link_ids = {x["structure_cue_id"] for x in links if x["shared_sample_tokens"] or x["basis"] == "local_procedure_with_named_or_explicitly_synthesized_product_cue"}
    linked_measured = [c for c in measured if c["numeric_atom_table_candidate"] and c["cue_id"] in explicit_link_ids]
    linked_phase = [c for c in cues if c["phase_cue"] and not c["origin_warnings"] and c["cue_id"] in linked_ids]
    linked_morph = [c for c in cues if c["morphology_cue"] and not c["origin_warnings"] and c["cue_id"] in linked_ids]
    contextual = [c for c in cues if c["coordinate_mention"] and c["origin_warnings"]]
    index = 0 if linked_measured else 1 if atomic else 2 if linked_phase else 3 if linked_morph else 4 if contextual else 5 if recipes else 6
    selected = linked_measured or atomic or linked_phase or linked_morph or contextual or recipes
    # Completeness is per procedure window; never union unrelated recipes.
    best_fields = max((c["procedure_field_cues"] for c in recipes), key=len, default=[])
    states = [file_states[d["file_key"]] for d in docs]
    effective_roles = {s["effective_role_candidate"] for s in states if s["eligible_for_candidate_cues"]}
    gaps = []
    if "main" not in effective_roles:
        gaps.append("main_absent_unreadable_or_role_unresolved")
    if "si" not in effective_roles:
        gaps.append("si_not_present_or_not_readable_pairing_unknown")
    if any(d.get("role_ambiguous") for d in docs):
        gaps.append("source_role_ambiguous")
    if len({d["sha256"] for d in docs if d.get("role_candidate") == "main"}) > 1:
        gaps.append("multiple_distinct_main_candidates")
    if any(s["known_positive_admission_block"] for s in states):
        gaps.append("known_file_identity_or_role_exception_repair_required")
    if any(not s["eligible_for_candidate_cues"] for s in states):
        gaps.append("some_source_content_unavailable_for_candidate_screen")
    if any(d.get("empty_text_pages") or d.get("failed_text_pages") for d in docs):
        gaps.append("image_only_or_failed_text_pages_need_visual_review")
    if any(s["manual_text_hold"] for s in states):
        gaps.append("original_manual_format_or_text_state_retained")
    if any("fixed_or_constrained_positions" in c["origin_warnings"] for c in cues):
        gaps.append("fixed_or_mixed_phase_coordinates_require_component_specific_review")
    selected_ids = {c["cue_id"] for c in selected}
    return {"group_id": group["group_id"], "queue_order": group["queue_order"],
            "source_generation_in_partition": group["source_generation"],
            "review_status_in_partition": group["review_status"], "priority_band": BANDS[index],
            "source_hold": any(s["known_positive_admission_block"] for s in states),
            "manual_text_hold": any(s["manual_text_hold"] for s in states),
            "dispatch_status": "source_identity_or_role_repair_required" if any(s["known_positive_admission_block"] for s in states) else "independent_source_and_pair_review_required",
            "band_order": index, "procedure_completeness_cue_count": len(best_fields),
            "best_local_procedure_field_cues": best_fields,
            "recipe_candidate_windows": len(recipes), "atomic_candidate_windows": len(atomic),
            "measured_refined_coordinate_candidate_windows": len(measured),
            "mixed_refined_fixed_atomic_table_windows": len(mixed),
            "origin_context_counts": dict(collections.Counter(o for c in cues for o in c["origin_warnings"])),
            "structure_origin": "experimental_refinement_cue_needs_review" if measured else "unknown_or_contextual",
            "structure_representation": "not_determined_average_or_finite_particle_identity_requires_review",
            "coordinate_file_availability": [{"file_key": d["file_key"], "source_sha256": d.get("sha256"), "format": d.get("detected_format")} for d in docs if d.get("detected_format") == "cif"],
            "source_hashes": sorted({d["sha256"] for d in docs if d.get("sha256")}),
            "file_keys": [d["file_key"] for d in docs], "source_gaps": gaps,
            "candidate_evidence": [{"cue_id": c["cue_id"], "source_sha256": c["source_sha256"], "locator": c["locator"], "figure_table_labels": c["figure_table_labels"]} for c in selected[:10]],
            "procedure_evidence": [{"cue_id": c["cue_id"], "source_sha256": c["source_sha256"], "locator": c["locator"], "field_cues": c["procedure_field_cues"]} for c in sorted(recipes, key=lambda c: -len(c["procedure_field_cues"]))[:5]],
            "link_candidates": [x for x in links if x["structure_cue_id"] in selected_ids][:12],
            "linkage_status": "unverified_local_relation_candidates" if selected and any(c["cue_id"] in linked_ids for c in selected) else "unknown_no_qualifying_local_link_cue",
            "main_si_pairing": "unverified_candidate_group_only",
            "source_validity": "known_exceptions_applied_others_unassessed",
            "verified_pair": False, "task_ready": False, "automatic_exclusion": False,
            "status": "offline_machine_nomination_only_no_scientific_approval"}

def run(output):
    started = time.perf_counter()
    output = output.resolve()
    if not output.is_relative_to(HERE) or output == HERE:
        raise ValueError("Output must be a child directory of ranker-proposal")
    if output.exists() and any(output.iterdir()):
        raise ValueError("Use a new empty output directory; prior dry runs are preserved")
    data, bindings = load_inputs()
    output.mkdir(parents=True, exist_ok=True)
    (output / "private").mkdir()
    partition = data["partition"]
    group_ids = set(partition["included_canonical_group_ids"])
    path_members = {str(Path(e["absolute_path"]).resolve()).lower() for e in data["inventory"]["entries"] if e.get("kind") == "regular_file" and e.get("top_level") and e.get("monitor_eligible")}
    def canonical(group_id):
        visited = set()
        while data["partition_ledger"]["groups"].get(group_id, {}).get("alias_of"):
            if group_id in visited:
                raise ValueError("Alias cycle in frozen partition ledger")
            visited.add(group_id)
            group_id = data["partition_ledger"]["groups"][group_id]["alias_of"]
        return group_id
    docs = [{**d, "frozen_screen_group_id": d["group_id"], "group_id": canonical(d["group_id"])} for d in data["documents"]
            if canonical(d["group_id"]) in group_ids and str(Path(d["source_path"]).resolve()).lower() in path_members]
    if len(docs) != 13831:
        raise ValueError(f"Cutoff copy coverage mismatch: {len(docs)} instead of 13831")
    bygroup = collections.defaultdict(list)
    for d in docs:
        bygroup[d["group_id"]].append(d)
    overlay = {(x["file_key"], x["source_sha256"]): x for x in data["validity_overlay"]["files"]}
    states, scans, cache_states, nested_results = {}, {}, {}, []
    counts = collections.Counter()
    with (output / "private/source-cues.jsonl").open("w", encoding="utf-8") as cuefile, (output / "cache-binding-manifest.jsonl").open("w", encoding="utf-8") as cachefile, (output / "file-dispositions.jsonl").open("w", encoding="utf-8") as fileout:
        for n, doc in enumerate(docs, 1):
            digest = doc.get("sha256")
            exception = overlay.get((doc["file_key"], digest))
            blocked = bool(exception and exception["block_positive_pair_admission_from_this_file"])
            if digest not in scans:
                binding, text = cache_binding(doc)
                cache_states[digest] = binding
                scans[digest] = scan_text(text, digest) if text is not None else {"cues": [], "link_candidates": [], "all_text_characters_examined": 0}
                jsonline(cachefile, binding)
                jsonline(cuefile, {"source_sha256": digest, "text_sha256": binding.get("text_sha256"), **scans[digest]})
                scans[digest]["cues"] = [{k: v for k, v in c.items() if k != "text_excerpt"} for c in scans[digest]["cues"] if not c["reference_section_candidate"]]
                counts["unique_cached_sources_processed"] += 1
                counts["text_characters_examined"] += scans[digest]["all_text_characters_examined"]
            state = {"file_key": doc["file_key"], "group_id": doc["group_id"], "source_path": doc["source_path"],
                     "frozen_screen_group_id": doc["frozen_screen_group_id"],
                     "source_sha256": digest, "screen_extraction_status": doc.get("extraction_status"),
                     "screen_manual_flags": doc.get("manual_flags", []), "cache_status": cache_states[digest]["status"],
                     "manual_text_hold": doc["status"] == "manual_format_or_text_review_required",
                     "effective_role_candidate": "si" if exception and exception.get("role_validity") == "not_main_article" else doc.get("role_candidate"),
                     "role_status": exception.get("role_validity") if exception else "unassessed_filename_or_ledger_candidate",
                     "known_positive_admission_block": blocked,
                     "source_validity_category": exception.get("source_validity_category") if exception else "unassessed",
                     "eligible_for_candidate_cues": not blocked and cache_states[digest]["status"] == "historically_bound_cache_candidate",
                     "page_count": doc.get("page_count"), "empty_text_pages": doc.get("empty_text_pages", []),
                     "failed_text_pages": doc.get("failed_text_pages", []), "excluded_paper": False}
            states[doc["file_key"]] = state
            jsonline(fileout, state)
            if n % 1000 == 0:
                (output / "progress.json").write_text(json.dumps({"status": "running_not_a_complete_report", "file_dispositions_processed": n, "expected": len(docs), "unique_caches_processed": len(scans), "wall_seconds": round(time.perf_counter()-started, 2)}), encoding="utf-8")
                print(f"processed {n}/{len(docs)} file dispositions; {len(scans)} unique cached sources; {time.perf_counter()-started:.1f}s", flush=True)
        nested_paths = {str(Path(d["absolute_path"]).resolve()).lower() for d in partition["nested_cutoff_candidates_held_for_scope_review"]}
        for item in data["nested_screen"]["held_nested_copy_dispositions"]:
            if str(Path(item["source_path"]).resolve()).lower() not in nested_paths:
                raise ValueError("Unexpected nested screen member")
            digest = item["sha256"]
            doc = {**item, "hash_computed": item["actual_bytes_hashed"], "source_unchanged_from_snapshot": item["source_unchanged_from_cutoff"]}
            if digest not in scans:
                binding, text = cache_binding(doc)
                cache_states[digest] = binding
                scans[digest] = scan_text(text, digest) if text is not None else {"cues": [], "link_candidates": [], "all_text_characters_examined": 0}
                jsonline(cachefile, binding)
                jsonline(cuefile, {"source_sha256": digest, "text_sha256": binding.get("text_sha256"), **scans[digest]})
                counts["unique_cached_sources_processed"] += 1
                counts["text_characters_examined"] += scans[digest]["all_text_characters_examined"]
            nested_results.append({"source_path": item["source_path"], "source_sha256": digest,
                                   "cache_status": cache_states[digest]["status"],
                                   "text_blocks_examined": scans[digest].get("text_blocks_examined", 0),
                                   "candidate_cues": len(scans[digest]["cues"]),
                                   "candidate_relation_cues": len(scans[digest]["link_candidates"]),
                                   "status": "second_stage_text_screened_identity_held_no_canonical_group_assigned",
                                   "verified_pair": False, "automatic_exclusion": False})
        if len(nested_results) != 3:
            raise ValueError("Nested held-file coverage mismatch")
    results = [summarize_scope(g, bygroup[g["group_id"]], scans, states) for g in partition["included_groups"]]
    results.sort(key=lambda x: (x["band_order"], -x["procedure_completeness_cue_count"], x["queue_order"], x["group_id"]))
    with (output / "ranked-scopes.jsonl").open("w", encoding="utf-8") as stream:
        for rank, item in enumerate(results, 1):
            jsonline(stream, {"candidate_inspection_rank": rank, **item})
    nested = partition["nested_cutoff_candidates_held_for_scope_review"]
    # They are already text-screened separately, but have no admitted paper
    # identity. Retain them explicitly; do not invent canonical groups.
    (output / "nested-held.json").write_text(json.dumps({"status": "retained_unadmitted_identity_and_pairing_review_required", "files": nested, "second_stage_screen": nested_results, "automatic_exclusion": False}, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {"schema": "mattersyn-offline-pair-candidate-screen/1", "version": VERSION,
               "status": "dry_run_proposal_not_activated_not_independently_audited",
               "input_bindings": bindings, "script_sha256": sha(Path(__file__).read_bytes()),
               "fixed_cutoff_scopes_expected": len(group_ids), "fixed_cutoff_scopes_output": len(results),
               "all_scope_ids_exactly_once": len(results) == len(group_ids) and {r["group_id"] for r in results} == group_ids,
               "fixed_cutoff_file_dispositions": len(docs), "nested_held_files_preserved": len(nested),
               "nested_held_files_second_stage_screened": sum(x["cache_status"] == "historically_bound_cache_candidate" for x in nested_results),
               "missing_scope_metadata_ids": sorted(group_ids - {s["group_id"] for s in data["screen_report"]["scopes"]}),
               "groups_without_matched_frozen_documents": sorted(group_ids - set(bygroup)),
               "priority_bands": dict(collections.Counter(r["priority_band"] for r in results)),
               "rubric_mapping": {"A": "A nomination only, never independently inspected rubric A", "B": "B review nomination; origin may be unknown and must be checked", "C": "C nomination for phase/cell linkage review", "D": "D nomination for morphology/size linkage review", "E": "E contextual coordinate channel", "R": "U recipe present but selected structural linkage unresolved", "U": "U manual/insufficient evidence"},
               "cache_status_counts": dict(collections.Counter(b["status"] for b in cache_states.values())),
               "file_validity_categories": dict(collections.Counter(s["source_validity_category"] for s in states.values())),
               "known_positive_blocks_applied": sum(s["known_positive_admission_block"] for s in states.values()),
               "source_identity_or_role_hold_groups": sum(r["source_hold"] for r in results),
               "manual_text_hold_groups": sum(r["manual_text_hold"] for r in results),
               "frozen_manual_format_or_text_copies_retained": sum(d["status"] == "manual_format_or_text_review_required" for d in docs),
               "counts": dict(counts), "wall_seconds": round(time.perf_counter()-started, 2),
               "verified_pair_count": 0, "automatic_exclusions": 0, "task_ready_count": 0,
               "shared_state_written": False, "source_files_written": False, "source_pdfs_reextracted": False,
               "network_used": False, "current_source_bytes_rehashed": False,
               "limitations": [LINK_METHOD, "All links, roles and structure origins remain machine candidates requiring page/figure review.", "No low score or missing text means no synthesis. Unsupported, image-only and corrupt content remain manual work.", "CCDC/CIF numeric tables can describe molecules or external structures; no finite nanoparticle coordinates are inferred.", "Experimental/refinement words plus coordinates are cue evidence, never verified atomic positions.", "Text-cache SHA256 is captured now; frozen screening metadata did not contain historical text hashes.", "Main/SI candidate grouping is inherited for navigation only. No cross-source sample join is asserted.", "Known source-validity exceptions are blocked; lack of an exception is not source approval.", "No performance/coverage estimate here is a deadline promise."]}
    (output / "progress.json").write_text(json.dumps({"status": "completed_dry_run_not_activated", "file_dispositions_processed": len(docs), "expected": len(docs), "unique_caches_processed": len(scans), "wall_seconds": summary["wall_seconds"]}), encoding="utf-8")
    outputs = {}
    for path in sorted(output.rglob("*")):
        if path.is_file():
            outputs[path.relative_to(output).as_posix()] = {"sha256": sha(path.read_bytes()), "bytes": path.stat().st_size}
    summary["output_bindings"] = outputs
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("fixed_cutoff_scopes_output", "priority_bands", "cache_status_counts", "known_positive_blocks_applied", "wall_seconds")}, indent=2), flush=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE / "dry-run")
    args = parser.parse_args()
    run(args.output)
