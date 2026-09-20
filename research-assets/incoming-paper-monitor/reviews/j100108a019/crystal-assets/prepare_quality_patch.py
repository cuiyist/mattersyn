"""Prepare a narrowly scoped checker patch outside the Site; do not apply it."""
from pathlib import Path
import difflib,hashlib,json
BASE=Path(__file__).resolve().parent
SOURCE=Path('[local path redacted]')
original=SOURCE.read_text(encoding='utf-8')
changed=original
def replace(old,new):
 global changed
 assert changed.count(old)==1,old[:100]
 changed=changed.replace(old,new)
replace('FIGURES = {', '''LITTAU_SI_ROUTES = {"littau-1993-si-aerosol-1p0", "littau-1993-si-aerosol-2p0", "littau-1993-si-aerosol-6p0"}
IDEAL_SI_ID = "littau-1993-si-diamond-ideal-reference"
IDEAL_SI_UNIT_HASH = "f37cb123ed21eed6bd1c681d78373ffa9c179810a8d3f52ea80fb954617cff6f"
IDEAL_SI_FINITE_HASH = "eab44501bd84a248f8343694869c0aae37dcc71d29f0641da954e8a34af7fe59"
FIGURES = {''')
replace('    "cofe2o4-spinel": (227, "cac0e1674371e05b06b58c22e6b518d0a38a218b2430207b54e5da7f87e58431", {"Co": 8, "Fe": 16, "O": 32}),',
'''    "cofe2o4-spinel": (227, "cac0e1674371e05b06b58c22e6b518d0a38a218b2430207b54e5da7f87e58431", {"Co": 8, "Fe": 16, "O": 32}),
    "littau-1993-si-diamond-ideal-reference": (227, "1252db5c1bedea5e671a9995282b976002f67cb6418d296796c392eef8e8476f", {"Si": 8}),''')
replace('        for formula in ("Ag", "CO", "NO", "Si", "PbS", "Fe–C–H–O"):',
'''        silicon = self.hubs.get("Si", {})
        self.check(silicon.get("component_only") is True and silicon.get("direct_record_ids") == [], "Si: Littau component contribution promoted to pure-material synthesis")
        self.check(set(silicon.get("record_ids", [])) == LITTAU_SI_ROUTES, "Si: missing or unaudited synthesis contribution; exactly the three reviewed Littau formulations are allowed")
        self.check(set(silicon.get("paper_dois", [])) == {"10.1021/j100108a019"}, "Si: unreviewed title match added to the reviewed Littau contribution")
        self.check(all(self.byid.get(rid, {}).get("material", {}).get("formula") == "Si/SiOx" for rid in LITTAU_SI_ROUTES), "Si: source surface-oxidized product identity was erased")
        for formula in ("Ag", "CO", "NO", "PbS", "Fe–C–H–O"):''')
replace('"Six independently reviewed crystal references changed; review additions explicitly"',
 '"Seven independently reviewed crystal references changed; review additions explicitly"')
replace('            self.check(bool(e.get("scope")) and e.get("sourceUrl", "").startswith("https://www.crystallography.net/cod/"), f"{cid}: source/scope absent")',
'''            if cid == IDEAL_SI_ID:
                self.check(bool(e.get("scope")) and e.get("sourceUrl") == "https://doi.org/10.1021/j100108a019", f"{cid}: quoted bulk-parameter source/scope absent")
                self.check(e.get("referenceType") == "locally_constructed_ideal_reference" and e.get("structureAssetRole") == "illustrative" and e.get("measuredSampleStructure") is False, f"{cid}: generated reference misrepresented as experimental CIF")
                self.check(set(e.get("record_ids", [])) == LITTAU_SI_ROUTES - {"littau-1993-si-aerosol-1p0"}, f"{cid}: reference attached outside phase-supported 6.0/2.0 formulations")
                self.check(e.get("modelSha256") == IDEAL_SI_UNIT_HASH, f"{cid}: independently validated ideal cell changed")
            else:
                self.check(bool(e.get("scope")) and e.get("sourceUrl", "").startswith("https://www.crystallography.net/cod/"), f"{cid}: source/scope absent")''')
replace('            self.check(m["source"]["sha256"] == expected_hash, f"{cid}: model derives from wrong CIF")',
'''            if cid == IDEAL_SI_ID:
                self.check(m.get("source", {}).get("source_sha256") == "dd498b93be57a3701beedb3302c5111e85b58f4e73db40be8e8c58b1622a592e", f"{cid}: wrong bulk-parameter paper")
                parameter = m.get("source", {}).get("reported_parameter", {})
                self.check(parameter.get("value") == 5.43 and parameter.get("status") == "reported_bulk_reference" and m.get("evidence_type") == "illustrative", f"{cid}: bulk comparison value relabeled as a measured sample parameter")
                self.check(e.get("finiteModelSha256") == IDEAL_SI_FINITE_HASH and e.get("finiteModelPeriodic") is False, f"{cid}: validated finite illustration changed or became periodic")
                finite_path = self.asset(base, e.get("finiteModelPath"), e.get("finiteModelSha256"), cid + "/finite-model")
                if finite_path:
                    finite = load(finite_path)
                    self.check(finite.get("periodic") is False and finite.get("training_eligible") is False and finite.get("measured_sample_structure") is False and finite.get("evidence_type") == "illustrative", f"{cid}: finite illustration promoted to measured/training structure")
                    self.check(len(finite.get("atoms", [])) == 705 and {a.get("element") for a in finite.get("atoms", [])} == {"Si"}, f"{cid}: finite Si illustration gained an unverified shell or changed atom count")
            else:
                self.check(m["source"]["sha256"] == expected_hash, f"{cid}: model derives from wrong CIF")''')
replace('six independently pinned CIF identities, mixed occupancy',
 'six pinned database CIFs plus one pinned ideal silicon reference, mixed occupancy')
compile(changed,str(SOURCE),'exec')
(BASE/'check_quality.proposed.py').write_text(changed,encoding='utf-8')
patch=''.join(difflib.unified_diff(original.splitlines(True),changed.splitlines(True),fromfile='a/scripts/check_quality.py',tofile='b/scripts/check_quality.py'))
(BASE/'check_quality-littau.patch').write_text(patch,encoding='utf-8')
report={'status':'proposed_only_not_applied','source_checker_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
 'proposed_checker_sha256':hashlib.sha256(changed.encode()).hexdigest(),'syntax_compilation':'passed',
 'scope':'Only the stale Si-hub exclusion and six-reference pin set, with the attribution and reference-only guards required by the newly allowed ideal reference.',
 'tests_not_run':'No full checker run and no asset geometric validation suite rerun.',
 'site_changed':False}
(BASE/'check_quality-patch-provenance.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
