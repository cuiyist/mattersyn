"""Small scientific false-join regressions; no scientific approval."""
import json
from pathlib import Path
import rank_pairs as r

HERE = Path(__file__).resolve().parent
DIGEST = "f" * 64

def classify(text):
    scan = r.scan_text(text, DIGEST)
    doc = {"file_key": "synthetic.pdf", "sha256": DIGEST, "role_candidate": "main", "detected_format": "pdf"}
    state = {"eligible_for_candidate_cues": True, "known_positive_admission_block": False, "manual_text_hold": False, "effective_role_candidate": "main"}
    row = r.summarize_scope({"group_id": "synthetic", "queue_order": 1, "source_generation": 1, "review_status": "unreviewed"}, [doc], {DIGEST: scan}, {"synthetic.pdf": state})
    return scan, row

def main():
    checks = []
    def check(name, condition):
        assert condition, name
        checks.append({"name": name, "passed": True})
    check("formula_not_sample", r.tokens("CsPbBr3 and Cs4PbBr6") == [])
    check("figure_and_table_not_sample", r.tokens("Figure S1; Table S2; Section S3") == [])
    check("hyphenated_variants_remain_distinct", r.tokens("Samples S4-1 and S4-2; sample S2.5-1") == ["S2.5-1", "S4-1", "S4-2"])
    recipe = "Sample S1 was synthesized by mixing 0.22 mmol PbBr2 in 0.5 mL DMSO and stirring for 12 h at room temperature. "
    scan, row = classify(recipe + "The crystal structure of sample S2 was refined by X-ray diffraction. Atomic fractional coordinates of S2 are reported.")
    check("different_recipe_and_structure_ids_unlinked", not scan["link_candidates"])
    scan, row = classify(recipe + "Rietveld refinement of sample S1 yielded atomic fractional coordinates in Table S2.")
    check("mentioned_table_is_not_present_table_A", row["priority_band"].startswith("B_"))
    table = "Refined atomic coordinates of sample S1\nAtom x y z occupancy\nCs1 0 0.5 0.25 1\nPb 0 0 0 1"
    scan, row = classify(recipe + table)
    check("integer_and_fractional_atom_rows_detected", any(c["numeric_atom_table_candidate"] for c in scan["cues"]))
    check("linked_local_numeric_refined_rows_nominate_A", row["priority_band"].startswith("A_"))
    check("A_is_never_verified_or_task_ready", not row["verified_pair"] and not row["task_ready"] and not row["automatic_exclusion"])
    check("reflection_table_not_atomic", not r.cue_window("Diffraction refinement\nh k l Fobs Fcalc\n1 0 0 0.53 0.51\n1 1 0 0.41 0.39")["numeric_atom_table_candidate"])
    scan, row = classify(recipe + table + "\nAtomic positions were fixed; these are reference coordinates taken from the ICSD.")
    check("fixed_reference_coordinates_not_A", not row["priority_band"].startswith("A_"))
    scan, row = classify(recipe + table + "\nThese atomic coordinates were optimized using density functional theory.")
    check("theory_coordinates_not_A", not row["priority_band"].startswith("A_"))
    scan, row = classify("Sample A was prepared by injecting 0.4 mL cesium oleate into 0.188 mmol PbBr2 at 170 C for 5 s. TEM of sample A showed cubes of 9 nm.")
    check("short_quantitative_morphology_recipe_retained", row["priority_band"].startswith("D_"))
    check("negated_refinement_flagged", "negated_or_prior_work_structure" in r.cue_window("Atomic coordinates could not be refined. No crystal structure was determined.")["origin_warnings"])
    continued = "\n\n--- PAGE 1 ---\n\nTable S6. Atomic coordinates for compound A.\n\n--- PAGE 2 ---\n\nAtom x y z\nCd(1) 0 0.5 0.25\n(Si,Al) 0.25 0.25 0.25\n\n--- PAGE 3 ---\n\nTable S7. Anisotropic displacement parameters\nAtom U11 U22 U33\nCd(1) 0.1 0.2 0.3\nO(1S) 0.2 0.3 0.4"
    tables = r.atomic_table_windows(r.split_blocks(continued), DIGEST)
    check("dangling_caption_links_only_adjacent_coordinate_rows", len(tables) == 1 and tables[0]["locator"]["page"] == 2 and tables[0]["table_header_locator"]["page"] == 1)
    check("new_ADP_caption_stops_inherited_atomic_header", all(t["locator"]["page"] != 3 for t in tables))
    cif = "_refine_ls_R_factor_gt 0.04\nloop_\n_atom_site_label\n_atom_site_type_symbol\n_atom_site_fract_x\n_atom_site_fract_y\n_atom_site_fract_z\n_atom_site_occupancy\n_atom_site_U_iso_or_equiv\nPb1 Pb 0.1 0.2 0.3 1 0.01\nSe1 Se 0.2 0.3 0.4 1 0.02\nloop_\n_geom_bond_atom_site_label_1\n_geom_bond_atom_site_label_2\nPb1 Se1"
    tables = r.atomic_table_windows([(None, cif)], DIGEST)
    check("CIF_atom_site_loop_recognized_without_sliding_header_overlap", len(tables) == 1 and tables[0]["numeric_atom_row_count"] == 2)
    report = {"status": "author_bounded_regression_checks_not_independent_audit", "script_sha256": r.sha((HERE / "rank_pairs.py").read_bytes()), "checks": checks}
    (HERE / "author-regression-checks.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"passed": len(checks), "script_sha256": report["script_sha256"]}))

if __name__ == "__main__":
    main()
