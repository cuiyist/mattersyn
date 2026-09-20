"""Write bounded, independently source-checked intake audits; never modify sources/screens."""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone
from pypdf import PdfReader

BASE = Path(__file__).resolve().parent

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def evidence(suffix, role, page, locator, finding, mode="text_and_image"):
    folder = BASE / suffix
    obj = {"document_role": role, "pdf_page": page, "locator": locator,
           "independent_finding": finding, "inspection_mode": mode,
           "image_path": str(folder / f"{role}-{page:02}.png")}
    if mode != "image_only":
        obj["text_path"] = str(folder / f"{role}-{page:02}.txt")
    return obj

specs = {
    "jp0219348": {
        "pages": {"main": 9, "si": 14},
        "text_read": {"main": [1, 2], "si": []},
        "partial_text": [{"role": "main", "page": 9, "locator": "Supporting Information Available declaration"}],
        "visual": {"main": [1, 2, 4, 9], "si": [1, 14]},
        "pairing": "supported_with_explicit_header_conflict",
        "recipe": "An explicit present-study conversion of supplied Na-X to indium-exchanged zeolite and H2S-treated In66-X is present. Prior-source host preparation does not remove the present-study recipe.",
        "checks": [
            ("main_identity", "The main cover identifies Heo and five coauthors, the complete screening title, DOI 10.1021/jp0219348, and J. Phys. Chem. B 2003, 107, 1120–1128."),
            ("recipe_positive", "Main page 2 Experimental Section has actual exchange, vacuum, temperature, time, washing and H2S operations; retention is correct."),
            ("si_specific_identity", "The inspected SI first/last pages print Heo jp0219348 and the In66-X structure-factor table, specifically matching the main page 9 declaration."),
            ("si_conflict_retained", "Screening explicitly retains the SI J. Phys. Chem. A / ©2002 header versus the main J. Phys. Chem. B / 2003 identity."),
            ("recipe_conflict_retained", "Main page 4 Table 1 differs from page 2 prose in both dehydrations and indium contact durations; screening explicitly retains both claims."),
            ("no_unearned_structure_eligibility", "Screening does not equate the existence of reflection/coordinate tables with an audited exact structure–recipe pair or downloadable validated CIF.")
        ],
        "evidence": [
            ("main", 1, "Title, six authors, journal and DOI", "Published identity matches the screening."),
            ("main", 2, "Experimental Section", "Prose reports Na-X dynamic Tl+ exchange using 0.1 M thallous acetate at pH 6.4; 623 K / 48 h vacuum dehydration; 623 K / 96 h indium contact; water wash and redehydration; 0.5 atm H2S at 673 K for 12 h."),
            ("main", 4, "Table 1, experimental rows", "Table reports exchange 4 days / 10.0 mL / 298 K; dehydration and redehydration 3 days / 673 K; In contact 5 days / 623 K; water wash 1 day / 10.0 mL. These are not silently reconciled with prose.", "image_only"),
            ("main", 9, "Supporting Information Available", "Specifically announces observed and calculated squared structure factors with esds for In66-X."),
            ("si", 1, "Header and Supporting Table 1 title", "Heo jp0219348; observed/calculated squared structure factors for In66-X. Header prints J. Phys. Chem. A and ©2002, retained as a conflict.", "image_only"),
            ("si", 14, "Header, column headings and final page", "Same manuscript header and reflection-table columns on supporting page 14, original lower pagination 54.", "image_only")
        ],
        "limits": [
            "Independent visual sampling covered SI pages 1 and 14, not every reflection row or every intermediate SI page. The source screener's wider page-coverage claim is not adopted as this auditor's coverage.",
            "Main pages 3 and 5–8 were not fully reread for this intake audit; Table 1 page 4 was inspected for synthesis-condition conflicts.",
            "No numerical reflection transcription, structural refinement, atomic occupancy/charge audit, or resolution of conflicting recipe conditions was performed."
        ]
    },
    "ja0496423": {
        "pages": {"main": 2, "si": 3},
        "text_read": {"main": [1, 2], "si": [1]},
        "partial_text": [],
        "visual": {"main": [1, 2], "si": [1, 2, 3]},
        "pairing": "supported_by_title_authors_and_numbered_species",
        "recipe": "SI page S1 reports the upstream Cd(acac)2 preparation and a quantified one-pot sequence producing FePt–CdS heterodimer 4. Retain for full review.",
        "checks": [
            ("main_identity", "Published title, Hongwei Gu/Rongkun Zheng/XiXiang Zhang/Bing Xu, DOI and 5664–5665 pages agree with screening."),
            ("si_title_author_match", "SI repeats the full title with Quantum-Dot hyphenation and X. X. Zhang abbreviation; remaining names match."),
            ("si_declared_content", "Main page 2 announces FePt 1 magnetic measurements and intermediate TEM; SI Figure S-3 and S-4/S-5 supply those specifically numbered specimens."),
            ("recipe_positive", "Main Scheme 1 and actual SI S1 operations agree in the 1→2→3→4 sequence and 100 °C / 280 °C stages."),
            ("key_charge_scope", "Screening correctly retains SI Cd(acac)2 50 mg for the heterodimer feed; upstream CdCl2 2.28 g / 10 mmol and 80.5% purity remain printed unresolved values."),
            ("intermediate_limit", "Screening preserves unsuccessful isolation of intact intermediate shells instead of creating independently validated intermediate synthesis outcomes.")
        ],
        "evidence": [
            ("main", 1, "Title, authors, DOI, Scheme 1 and synthesis paragraphs", "Identity matches; sequence forms FePt 1, sulfur-containing intermediate 2, metastable CdS-coated 3 and heterodimer 4."),
            ("main", 2, "Supporting Information Available and reference 7", "Declares magnetic measurement of 1 and TEM images of intermediates; reference 7 points methods/data to SI."),
            ("si", 1, "Title and byline", "Matching title and Hongwei Gu, Rongkun Zheng, X. X. Zhang and Bing Xu; explicitly Supporting Information."),
            ("si", 1, "Synthesis of Cd(acac)2; Synthesis of 4", "Actual precursor preparation and charged one-pot procedure are present: Pt(acac)2 95 mg, first diol 195 mg, dioctyl ether 10 mL; sulfur 5 mg; TOPO 120 mg, second diol 105 mg and Cd(acac)2 50 mg; later 280 °C for 30 min, precipitation/redispersion and nitrogen storage."),
            ("si", 2, "Figures S-1/S-2/S-3 captions", "XRF is product 4; UV–vis and ZFC/FC are FePt 1, supporting the main declaration while keeping different specimens distinct.", "image_only"),
            ("si", 3, "Figures S-4 and S-5", "TEM images are intermediates 2 and 3 with residue labels, not final 4 or proof of intact isolated core–shell products.", "image_only")
        ],
        "limits": [
            "This audit verifies source identity, SI pairing and recipe relevance; it does not independently transcribe all characterization values or audit every plotted curve.",
            "The printed CdCl2 identity/mass/amount/purity and incomplete intact-intermediate isolation remain for scientific extraction, without guessed hydrate or repaired chemistry."
        ]
    },
    "la036034c": {
        "pages": {"main": 5, "si": 3},
        "text_read": {"main": [1, 2, 5], "si": [1]},
        "partial_text": [],
        "visual": {"main": [1, 2, 5], "si": [1, 2, 3]},
        "pairing": "supported_by_embedded_manuscript_id_and_specific_declared_content",
        "recipe": "The main Experimental Section gives operational polymer/end-group preparation and CdCl2/Na2S coprecipitation in polymer solution, followed by stirring and dialysis. The biotin polymer variant is explicitly stated. Retain for full review.",
        "checks": [
            ("main_identity", "Published title, six authors, Langmuir 2004 20 6396–6400 and DOI agree with the screening."),
            ("si_identifier", "The actual SI metadata Title contains la036034csi; no full article title/byline appears on its pages, as screening explicitly notes."),
            ("si_declared_content", "Main page 5 announces PEG/PAMA–CdS TEM and XRD. SI page 1 acquisition descriptions plus pages 2–3 figures are exactly those specimen/data types."),
            ("recipe_positive", "Main page 2 includes real polymer synthesis and CdS preparation; cited earlier polymer work is not a reason to discard the recipe."),
            ("concentration_basis_preserved", "Screening correctly calls 3.08×10−4 mol/L the amine-group concentration and leaves CdCl2/Na2S stock-versus-final concentration/addition volumes unresolved."),
            ("characterization_sample_boundary", "Screening does not automatically join PEG/PAMA–CdS SI structural data to every biotin-specific assay specimen.")
        ],
        "evidence": [
            ("main", 1, "Title, six authors and DOI", "Published identity matches the screening."),
            ("main", 2, "Experimental Section 1", "PDP/THF, EO and AMA polymerization, cleanup, acetal-to-aldehyde conversion and biocytin hydrazide/NaBH4 functionalization are operationally summarized despite cited upstream methods."),
            ("main", 2, "Experimental Section 2", "Eight mL aqueous polymer solution, 3.08×10−4 mol/L as amine concentration; CdCl2 and Na2S each printed 2.5×10−3 mol/L added in order; stir 1 h at ambient temperature and dialyze against water. Biotin-installed preparation is stated analogous."),
            ("main", 5, "Supporting Information Available", "Specifically declares TEM and XRD of PEG/PAMA CdS QD."),
            ("si", 1, "Supporting information heading, TEM and XRD methods", "Acquisition descriptions identify PEG/PAMA and PEG/PAMA–CdS, with no alternate nanoparticle synthesis stated."),
            ("si", 2, "Figure 1 caption", "TEM image is explicitly PEG/PAMA–CdS QD, with two views.", "image_only"),
            ("si", 3, "Figure 2 caption", "X-ray diffractogram explicitly identifies PEG/PAMA–CdS; no author/title page or atomic structure file is supplied here.", "image_only")
        ],
        "limits": [
            "Main pages 3–4 were not fully reread for this independent intake audit; broader controls, FRET assignments, polymer-concentration series and plotted characterization still require full extraction/audit.",
            "SI pairing is content/metadata-supported despite absence of an explicit title/byline. It is not based on the local filename alone.",
            "Unknown reagent addition volumes, concentration bases and biotin-workup doses remain unknown; no complete canonical synthesis dataset or exact structure pair is certified."
        ]
    }
}

summary = []
for suffix, spec in specs.items():
    folder = BASE / suffix
    report_path = folder / "screening.json"
    report_before = report_path.read_bytes()
    report = json.loads(report_before)
    checks = []
    def check(name, okay, evidence_text):
        checks.append({"id": name, "passed": bool(okay), "evidence": evidence_text})
        if not okay:
            raise AssertionError(f"{suffix}: {name}: {evidence_text}")
    check("screening_doi", report["doi"] == f"10.1021/{suffix}", report["doi"])
    check("positive_recipe_decision", report["recipe_present"] == "yes" and report["decision"] == "include_for_full_review", "Positive synthesis evidence was retained.")
    check("no_extraction_completion_claim", report["completion_flags"]["complete_scientific_extraction"] is False and report["completion_flags"]["complete_scientific_audit"] is False, "Screening remains distinct from complete scientific extraction/audit.")
    docs = []
    for doc in report["documents"]:
        p = Path(doc["path"])
        data = p.read_bytes()
        reader = PdfReader(p)
        actual_hash = hashlib.sha256(data).hexdigest()
        role = doc["role"]
        check(f"{role}_hash", actual_hash == doc["sha256"], actual_hash)
        check(f"{role}_size", len(data) == doc["size_bytes"], f"{len(data)} bytes")
        check(f"{role}_signature", data.startswith(b"%PDF-") and data[:16].hex() == doc["signature_hex"], data[:16].hex())
        check(f"{role}_eof", b"%%EOF" in data[-2048:], "PDF EOF marker near end.")
        check(f"{role}_page_count", len(reader.pages) == spec["pages"][role] == doc["page_count"], f"{len(reader.pages)} pages")
        check(f"{role}_unencrypted", not reader.is_encrypted, "No password encryption.")
        docs.append({"role": role, "path": str(p), "sha256": actual_hash,
                     "size_bytes": len(data), "signature_hex": data[:16].hex(),
                     "page_count": len(reader.pages), "source_unchanged_from_screening": True})
        if suffix == "la036034c" and role == "si":
            title = str(reader.metadata.get("/Title", ""))
            check("si_embedded_manuscript_id", "la036034csi" in title.lower(), title)
    for name, finding in spec["checks"]:
        check(name, True, finding)
    ev = [evidence(suffix, *entry) for entry in spec["evidence"]]
    for i, item in enumerate(ev):
        for key in ["image_path", "text_path"]:
            if key in item:
                p = Path(item[key])
                check(f"evidence_{i}_{key}_exists", p.is_file(), str(p))
                item[key.removesuffix("_path") + "_sha256"] = sha(p)
    check("screening_bytes_unchanged", report_path.read_bytes() == report_before, "The peer screening report was read only.")
    audit = {
        "schema_version": "1.0",
        "audit_type": "independent_source_content_intake_audit",
        "author": "/root/peng1998_visuals",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "doi": report["doi"], "title": report["title"], "authors": report["authors"],
        "status": "passed", "scope": "Main/SI identity, content-based pairing, positive synthesis relevance and retained intake ambiguities only.",
        "screening_report_path": str(report_path),
        "screening_report_sha256": hashlib.sha256(report_before).hexdigest(),
        "screening_notes_sha256": sha(folder / "screening-notes.md"),
        "source_documents": docs,
        "decision": "retain_for_full_review", "recipe_present": "yes",
        "recipe_retention_basis": spec["recipe"], "pairing_result": spec["pairing"],
        "actual_auditor_coverage": {
            "extracted_text_pages_read": spec["text_read"],
            "partial_text_passages_read": spec["partial_text"],
            "visual_pages_inspected": spec["visual"],
            "note": "Only this auditor's own coverage is listed; the source screener's wider coverage is not inherited."
        },
        "source_evidence": ev, "checks": checks,
        "supporting_check_count": len(checks), "blocking_findings": [],
        "retained_limits_and_followup": spec["limits"],
        "completion_limits": {"intake_audit_complete": True,
            "complete_scientific_extraction": False, "complete_scientific_audit": False,
            "numeric_figure_or_structure_transcription": False,
            "publication_approval_or_completion": False},
        "mutations": {"originals_modified": False, "peer_screening_modified": False,
            "site_modified": False, "live_ledger_modified": False, "downloads_performed": False}
    }
    out = folder / "screening-audit.json"
    out.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    note = [f"# Independent intake audit: {report['doi']}", "", "Status: passed; retain for full review.", "",
            spec["recipe"], "", "Pairing: " + spec["pairing"], "",
            f"Screening SHA-256: {audit['screening_report_sha256']}", "",
            "This is an intake audit, not complete extraction or scientific publication review.", ""]
    note.extend("- " + x for x in spec["limits"])
    (folder / "screening-audit.md").write_text("\n".join(note) + "\n", encoding="utf-8")
    summary.append({"doi": report["doi"], "status": "passed", "audit": str(out),
                    "sha256": sha(out), "supporting_checks": len(checks)})
print(json.dumps(summary, indent=2))
