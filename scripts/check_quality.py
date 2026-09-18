"""Read-only scientific publication/asset checks; Python standard library only.

Run after the complete build:
  python -B scripts/check_quality.py --root .
Or run this private copy with --root /path/to/recipe-atlas.
No Site imports, network access, build steps, or writes occur. Exit 1 means a
broken publication/evidence contract; warnings identify metadata improvements.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import sys

CRYSTALS = {
    "zno-wurtzite": (186, "dbc92c19b101d4fabb5594cc89f2a31629a0e8adab6539edd248c40c585649a1", {"Zn": 2, "O": 2}),
    "ir-fcc": (225, "ecc80c2b26b98c67712b6418ab7175e6e4a86a6f277a58d7556459c8f0ff3566", {"Ir": 4}),
    "inp-zinc-blende": (216, "dae92a9da8c000121f86e0f5c0f133d39f65cb94ccfb005410f2c213532afb42", {"In": 4, "P": 4}),
    "cspbbr3-orthorhombic": (62, "3abeb5af8ba1fb302248380fac29c51611d3d516bf981b5f4d4652ef06c4434a", {"Cs": 4, "Pb": 4, "Br": 12}),
    "coo-rocksalt": (225, "35661cbc816a7728cd6b7ef101483aa091b1b08f1f30fbde52343d5d6f9da07a", {"Co": 4, "O": 4}),
    "cofe2o4-spinel": (227, "cac0e1674371e05b06b58c22e6b518d0a38a218b2430207b54e5da7f87e58431", {"Co": 8, "Fe": 16, "O": 32}),
}
FIGURES = {
    "tessier2015": {"doi": "10.1021/acs.chemmater.5b02138", "figures": {"figure-1": ("main", 2), "figure-s3": ("si", 8), "figure-s4": ("si", 9)}, "sources": {"main": "964dfbf6fc6714dceef89fdb0d6c7cc425ab49903fa688cab9ca0796c36f45d5", "si": "20b8647e367caad427366d8b2b4e50a07738f44b326ffba749997bedd9fdd31a"}},
    "zhang2019": {"doi": "10.1021/acs.chemmater.9b03529", "figures": {"table-1": ("main", 3), "figure-1": ("main", 3), "figure-s2": ("si", 3), "figure-s3": ("si", 4), "table-s1": ("si", 4), "figure-s9": ("si", 9)}, "sources": {"main": "63f1ce8f9c67c93ff838c7bd1863456ed1a7eaa59d090866ea7f15b47a555e8e", "si": "171b0d4ca916dff8a3febe101a25ca836f17af8bdcdac79ecb50a47e525a4477"}},
}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def primary_doi(record):
    source = next((s for s in record["sources"] if s["id"] == record["lineage"]["source_group"]), None)
    return (source or {}).get("doi", "").lower()


class Audit:
    def __init__(self, root):
        self.root = root.resolve()
        self.dist = self.root / "dist"
        self.errors, self.warnings, self.counts = [], [], Counter()

    def check(self, condition, message):
        self.counts["checks"] += 1
        if not condition:
            self.errors.append(message)
        return bool(condition)

    def warn(self, condition, message):
        if not condition:
            self.warnings.append(message)

    def asset(self, base, relative, digest, label):
        if not self.check(isinstance(relative, str) and relative and not Path(relative).is_absolute(), f"{label}: absent/nonrelative asset path"):
            return None
        path = (base / relative).resolve()
        if not self.check(path.is_relative_to(base.resolve()), f"{label}: path leaves asset directory"):
            return None
        if not self.check(path.is_file(), f"{label}: missing file {relative}"):
            return None
        self.check(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest) is not None, f"{label}: missing SHA-256")
        self.check(sha(path) == digest, f"{label}: asset hash mismatch")
        self.counts["hashed_assets"] += 1
        return path

    def records(self, minimum):
        rows = [json.loads(line) for line in (self.dist / "data/records.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
        self.byid = {r["record_id"]: r for r in rows}
        self.check(len(rows) == len(self.byid), "Duplicate canonical record IDs")
        self.check(len(rows) >= minimum, f"Expected at least {minimum} canonical records; found {len(rows)}")
        self.counts["canonical_records"] = len(rows)
        for record in rows:
            rid = record["record_id"]
            public = self.dist / "data/records" / (rid + ".json")
            self.check(public.is_file() and load(public) == record, f"{rid}: canonical JSONL disagrees with public record")
            for asset in record.get("structure_assets", []):
                if asset["role"] != "measured_sample":
                    self.check(asset["eligible_as_measured_label"] is False, f"{rid}: reference/illustrative structure promoted to measured label")

    def materials(self):
        index = load(self.dist / "data/materials-index.json")["materials"]
        mids = {m["id"] for m in index}
        self.check(len(mids) == len(index), "Duplicate material hub IDs")
        self.check({f.stem for f in (self.dist / "data/materials").glob("*.json")} == mids, "Stale/unindexed material JSON can still expose an obsolete empty hub")
        self.hubs = {}
        for summary in index:
            hub = load(self.dist / "data/materials" / (summary["id"] + ".json"))
            formula = hub["formula"]
            self.hubs[formula] = hub
            route_ids = set(hub["record_ids"])
            self.check(bool(route_ids), f"{formula}: public material hub has no reviewed route")
            self.check(hub.get("publication_status") == "verified_synthesis_contribution", f"{formula}: hub lacks verified publication status")
            self.check(not hub.get("mentioned_paper_dois"), f"{formula}: title mentions leaked into material contributions")
            self.check(route_ids == {r["record_id"] for r in hub["records"]}, f"{formula}: route summary IDs disagree")
            direct = set()
            route_dois = set()
            for stub in hub["records"]:
                rid = stub["record_id"]
                r = self.byid.get(rid)
                if not self.check(r is not None, f"{formula}: unknown route {rid}"):
                    continue
                # Independently enforce scientific publication boundaries, rather
                # than calling or copying the builder's synthesis_route gate.
                self.check(r["collection"] == "reviewed_literature" and r["quality"]["review_status"] == "source_reviewed", f"{formula}/{rid}: unreviewed/benchmark record published as synthesis")
                self.check(r["record_type"] != "procedure" and any(o["stage"] == "synthesis" for o in r["operations"]), f"{formula}/{rid}: procedure/assay published as material route")
                self.check(stub.get("is_synthesis_route") is True, f"{formula}/{rid}: displayed route is not marked synthesis")
                self.check(not ("control" in rid and not r["quality"].get("requested_tasks")), f"{formula}/{rid}: contextual control promoted to a synthesis contribution")
                self.check(stub["formula"] == r["material"]["formula"], f"{formula}/{rid}: original product identity erased on component card")
                if formula == r["material"]["formula"]:
                    direct.add(rid)
                    self.check(stub["contribution_role"] == "direct_material", f"{formula}/{rid}: incorrect direct-material role")
                else:
                    self.check(formula in r["material"].get("components", []), f"{formula}/{rid}: association unsupported by canonical components")
                    self.check(stub["contribution_role"] == "component_of_heterostructure", f"{formula}/{rid}: component masquerades as pure-material synthesis")
                    self.check(r["material"].get("architecture") not in (None, "single_material"), f"{formula}/{rid}: component link lacks composite architecture")
                route_dois.add(primary_doi(r))
            self.check(set(hub["direct_record_ids"]) == direct, f"{formula}: direct-route identity mismatch")
            self.check(hub["component_only"] == (not direct), f"{formula}: wrong component-only label")
            if not direct:
                self.check("not standalone" in hub.get("scope_note", "").lower(), f"{formula}: component-only page lacks explicit scope")
            self.check(set(d.lower() for d in hub["paper_dois"]) == route_dois, f"{formula}: source list not tied to canonical routes")
            for paper in hub["papers"]:
                linked = set(paper.get("reviewedRecordIds", []))
                expected = {rid for rid in route_ids if primary_doi(self.byid[rid]) == paper["doi"].lower()}
                self.check(bool(linked) and linked == expected, f"{formula}/{paper['id']}: paper list includes unrelated or missing route links")
                self.check(not paper.get("benchmarkRecordIds"), f"{formula}: benchmark paper row presented as curated synthesis")
            self.check(hub["reviewed_records"] == len(route_ids) == summary["reviewed_records"], f"{formula}: reviewed-route count mismatch")
            self.check(len(hub["papers"]) == len(route_dois) == hub["paper_count"], f"{formula}: paper contribution count mismatch")
        # Concrete regressions established by the independently reviewed sources.
        ferrite = self.hubs.get("CoFe2O4", {})
        self.check(ferrite.get("component_only") is True, "CoFe2O4: Saha shell contribution incorrectly promoted to pure-ferrite synthesis")
        self.check("saha-2019-coo-cofe2o4-seeded-growth" in ferrite.get("record_ids", []), "Missing reviewed Saha ferrite-shell contribution")
        for formula in ("Ag", "CO", "NO", "Si", "PbS", "Fe–C–H–O"):
            self.check(formula not in self.hubs, f"{formula}: former title-only/benchmark/procedure hub reappeared; independent route review required")
        for paper in load(self.dist / "data/library-index.json")["papers"]:
            if paper["reviewStatus"] == "indexed_awaiting_review":
                self.check(not paper.get("reviewedRecordIds") and not paper.get("materials"), f"{paper['id']}: indexed-only candidate exposed as curated contribution")
        self.counts["material_hubs"] = len(index)

    def chemicals(self):
        base = self.dist / "assets/chemical-registry"
        registry, bindings = load(base / "registry.json"), load(base / "bindings.json")
        entries = {e["id"]: e for e in registry["entries"]}
        self.check(len(entries) == len(registry["entries"]), "Duplicate chemical registry IDs")
        self.check(set(bindings["recordBindings"]) == set(self.byid), "Chemical bindings do not cover exactly the current canonical records")
        self.check(not bindings.get("unresolved"), "Unresolved chemical bindings remain")
        for rid, r in self.byid.items():
            bound = bindings["recordBindings"].get(rid, {})
            self.check(set(bound) == {m["id"] for m in r["materials"]}, f"{rid}: missing/stale material bindings")
            self.check(bindings["sourceRecordSha256"].get(rid) == sha(self.dist / "data/records" / (rid + ".json")), f"{rid}: chemical bindings built from stale canonical record")
            for mid, eid in bound.items():
                self.check(eid in entries, f"{rid}/{mid}: chemical binding target absent")
                self.counts["material_instances"] += 1
        for eid, entry in entries.items():
            self.check(bool(entry.get("sourceUrls")) and bool(entry.get("caption")), f"{eid}: depiction lacks public attribution/scope")
            self.check(bool(entry.get("svgPath")), f"{eid}: no visible chemical representation")
            if entry["depictionKind"] in {"mixture", "specimen", "support", "formula"}:
                self.check(not entry.get("model3dPath"), f"{eid}: uncertain mixture/formula/specimen has invented molecular geometry")
            for key in ("svgPath", "model2dPath", "model3dPath"):
                if not entry.get(key):
                    continue
                path = self.asset(base, entry[key], entry.get("assetHashes", {}).get(key), f"{eid}/{key}")
                if path and key != "svgPath":
                    model = load(path)
                    atoms = model.get("atoms", [])
                    self.check(bool(atoms), f"{eid}/{key}: empty model")
                    for atom in atoms:
                        self.check(all(isinstance(atom.get(k), (int, float)) and math.isfinite(atom[k]) for k in ("x", "y", "z")), f"{eid}/{key}: nonfinite/missing atom coordinate")
                    for bond in model.get("bonds", []):
                        self.check(all(isinstance(bond.get(k), int) and 0 <= bond[k] < len(atoms) for k in ("a", "b")), f"{eid}/{key}: bond endpoint outside atom list")
                    for group in entry.get("functionalGroups", []):
                        self.check(all(0 <= i < len(atoms) for i in group.get("atomIndices", [])), f"{eid}/{key}: functional-group atom outside model")
        self.counts["chemical_identities"] = len(entries)

    def crystals(self):
        base = self.dist / "assets/crystal-references"
        entries = {e["id"]: e for e in load(base / "registry.json")["entries"]}
        self.check(set(entries) == set(CRYSTALS), "Six independently reviewed crystal references changed; review additions explicitly")
        for cid, (sg, expected_hash, composition) in CRYSTALS.items():
            if not self.check(cid in entries, f"Missing crystal {cid}"):
                continue
            e = entries[cid]
            self.check(e.get("referenceOnly") is True and e.get("trainingEligible") is False, f"{cid}: reference promoted to experimental training label")
            self.check(e.get("spaceGroupNumber") == sg and e.get("cifSha256") == expected_hash, f"{cid}: independently verified CIF identity changed")
            self.check(bool(e.get("scope")) and e.get("sourceUrl", "").startswith("https://www.crystallography.net/cod/"), f"{cid}: source/scope absent")
            self.check(set(e["record_ids"]) <= set(self.byid), f"{cid}: bound to nonexistent canonical recipe")
            self.asset(base, e.get("cifPath"), e.get("cifSha256"), cid + "/CIF")
            path = self.asset(base, e.get("modelPath"), e.get("modelSha256"), cid + "/model")
            if not path:
                continue
            m = load(path)
            self.check(m.get("training_eligible") is False and m.get("measured_sample_structure") is False, f"{cid}: model fails reference-only flags")
            self.check(m["source"]["sha256"] == expected_hash, f"{cid}: model derives from wrong CIF")
            counts, positions = Counter(), set()
            for a in m["atoms"]:
                xyz = tuple(a[k] for k in ("x", "y", "z"))
                self.check(all(isinstance(v, (int, float)) and math.isfinite(v) for v in xyz), f"{cid}: invalid atom coordinate")
                self.check(xyz not in positions, f"{cid}: overlapping sites rendered as separate fully occupied atoms")
                positions.add(xyz)
                components = a.get("components", [{"element": a["element"], "occupancy": a.get("occupancy", 1)}])
                self.check(abs(sum(c["occupancy"] for c in components) - 1) < 1e-6, f"{cid}: site occupancy does not sum to one")
                for c in components:
                    counts[c["element"]] += c["occupancy"]
                if len(components) > 1:
                    self.check(a.get("mixed_site") is True and a["element"] == "X" and "/" in a.get("label", ""), f"{cid}: mixed Co/Fe site presented as a known discrete atom")
            self.check(set(counts) == set(composition) and all(abs(counts[k] - v) < 1e-5 for k, v in composition.items()), f"{cid}: occupancy-weighted stoichiometry changed")
            if cid == "cofe2o4-spinel":
                self.check(e["mixedOccupancy"] is True and len(positions) == 56 and sum(a["mixed_site"] for a in m["atoms"]) == 24, "Ferrite: mixed-site representation/count changed")
                self.check(e["record_ids"] == ["saha-2019-coo-cofe2o4-seeded-growth"], "Ferrite reference attached to standalone CoO or unrelated protocol")
            if cid == "ir-fcc":
                self.check(e["record_ids"] == ["stowell-2005-ir-oa-oleylamine-290c"], "FCC Ir reference assigned to unverified TOAB/TOPB/TOP sample phase")
            if cid == "inp-zinc-blende":
                self.check(e.get("sample_context_ids") == ["inp-reference-characterization-20min"] and "30 min" in e["scope"], "InP: 20-minute characterization confused with 30-minute recipe product")
        self.counts["crystal_references"] = len(entries)

    def figures(self):
        for pid, expected in FIGURES.items():
            meta = load(self.dist / "data/recipe-figures" / (pid + ".json"))
            self.check(meta["doi"] == expected["doi"], f"{pid}: wrong selected-figure paper")
            self.check(meta.get("coverage_status") == "selected_figures_only" and bool(meta.get("scope")), f"{pid}: selected extraction misrepresented as full-paper review")
            rows = {f["id"]: f for f in meta["figures"]}
            self.check(set(rows) == set(expected["figures"]), f"{pid}: missing/unreviewed selected figures")
            for fid, (role, page) in expected["figures"].items():
                if fid not in rows:
                    continue
                f = rows[fid]
                self.asset(self.dist, f.get("public_asset"), f.get("public_asset_sha256"), pid + "/" + fid)
                self.check(f.get("document_role") == role and f.get("page") == page and f.get("source_sha256") == expected["sources"][role], f"{pid}/{fid}: source document/page mismatch")
                self.check(Path(f.get("source_file", "")).name == f.get("source_file") and f.get("source_file", "").endswith(".pdf"), f"{pid}/{fid}: source basename missing or private path exposed")
                box = f.get("crop_normalized", [])
                self.check(len(box) == 4 and all(0 <= v <= 1 for v in box) and box[0] < box[2] and box[1] < box[3], f"{pid}/{fid}: invalid crop locator")
                self.check(len(f.get("sample_assignments", "")) > 40 and f.get("raw_data_digitized") is False, f"{pid}/{fid}: lost sample scope or invented raw data")
                self.check(f.get("eligible_training", False) is False, f"{pid}/{fid}: contextual figure promoted to training label")
                self.warn("eligible_training" in f, f"{pid}/{fid}: add explicit eligible_training=false for machine-readable exclusion")
                self.counts["selected_figures"] += 1
            if pid == "tessier2015":
                text = rows["figure-1"]["sample_assignments"]
                self.check("20-minute" in text and "30 minutes" in text and "not assigned" in text, "InP Fig1 lost core/shell and 20/30-minute boundary")
            if pid == "zhang2019":
                self.check("not the TDPA-only" in rows["figure-1"]["sample_assignments"], "CsPbBr3 representative mixed-ligand panels assigned to TDPA-only")
                self.check("discrepancy" in rows["figure-s3"]["sample_assignments"], "CsPbBr3 SI panel/caption discrepancy lost")
        for export in (self.dist / "data/exports").glob("*.jsonl"):
            text = export.read_text(encoding="utf-8")
            self.check("assets/selected-evidence/" not in text and "assets/crystal-references/" not in text, f"{export.name}: contextual figure or reference crystal leaked into training export")

    def privacy(self):
        for directory in (self.dist / "data", self.dist / "assets/chemical-registry", self.dist / "assets/crystal-references"):
            for path in directory.rglob("*.json"):
                text = path.read_text(encoding="utf-8")
                self.check(not re.search(r"[A-Z]:[/\\]+Users[/\\]", text, re.I), f"{path.relative_to(self.dist)}: private absolute path in public metadata")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help="Site checkout containing dist; read only")
    parser.add_argument("--minimum-records", type=int, default=155)
    args = parser.parse_args()
    audit = Audit(args.root)
    for method, values in ((audit.records, (args.minimum_records,)), (audit.materials, ()), (audit.chemicals, ()), (audit.crystals, ()), (audit.figures, ()), (audit.privacy, ())):
        try:
            method(*values)
        except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
            audit.errors.append(f"{method.__name__}: incomplete/malformed build: {type(error).__name__}: {error}")
    report = {"passed": not audit.errors, "counts": dict(audit.counts), "errors": audit.errors, "warnings": audit.warnings, "scope": "Publication relevance, all canonical reagent bindings and assets, six independently pinned CIF identities, mixed occupancy, nine selected original figures and exclusion from training labels. No network, source-PDF access, or Site writes."}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if audit.errors else 0


if __name__ == "__main__":
    sys.exit(main())
