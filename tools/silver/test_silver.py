import copy
import math
import unittest
import silver as s


def policy(band="high"):
    return {"schema": s.VERSION+"/policy", "pipeline_id": "test-v1", "pipeline_sha256": "b"*64,
            "thresholds_confirmed": True, "thresholds": s.BANDS.copy(), "confidence": .95,
            "family_bands": {"demo": band}, "family_count_snapshot_sha256": "f"*64}


def claim(field="reaction_temperature", value=270, unit="°C", sample=None):
    text = "Method A was heated at 270 °C for 30 min to make sample A. Sample A has 4 nm diameter by TEM."
    return {"recipe_id": "Method A", "sample_id": sample, "slot_id": field, "field": field, "value": value,
            "unit": unit, "value_text": str(value), "unit_text": unit, "document_id": "main", "page": 1,
            "quote": text, "link_quote": text, "link_page": 1, "modality": "explicit_text", "technique": None, "chemical_id": None}


def inputs(band="high", source="paper1"):
    c = claim()
    pages = {"documents": {"main": {"source_id": source, "pages": {"1": c["quote"]}}}}
    a = {"schema": s.VERSION+"/draft", "pipeline_id": "test-v1", "pipeline_sha256": "b"*64, "runner": "local", "saw_other_draft": False,
         "pass_id": "a", "prompt_sha256": "a"*64, "model_sha256": "c"*64, "source_id": source, "family_id": "demo", "claims": [c]}
    b = copy.deepcopy(a)
    b["pass_id"] = "b"
    b["prompt_sha256"] = "d"*64
    return a, b, pages, policy(band)


def reconcile(band="high", source="paper1"):
    return s.reconcile(*inputs(band, source))


def calibration_data(n=1, band="high", wrong=0, repeated=1):
    predictions, gold = [], []
    for i in range(n):
        p = reconcile(band, "paper"+str(i))
        for j in range(repeated):
            if j:
                p["claims"].append(copy.deepcopy(p["claims"][0]))
            row = p["claims"][j]
            row["key"][2] = "growth"+str(j)
            for alt in row["alternatives"]:
                alt["slot_id"] = "growth"+str(j)
            g = copy.deepcopy(row["alternatives"][0])
            g.update(source_id=p["source_id"], band=band)
            if i < wrong:
                g["value"] = 280
            gold.append(g)
        predictions.append(p)
    truth = {"schema": s.VERSION+"/gold-holdout", "pipeline_id": "test-v1", "gold_snapshot_sha256": "e"*64,
             "split": "heldout", "frozen_before_extraction": True, "independent_scientific_audit": True,
             "auditor_id": "reviewer", "extractor_id": "author", "heldout_source_ids": [p["source_id"] for p in predictions],
             "training_source_ids": [], "selection_source_ids": [], "records": gold}
    return truth, predictions, policy(band)


class TestQuoteAndSchema(unittest.TestCase):
    def test_valid_recipe_scope_no_sample(self):
        row = reconcile()["claims"][0]
        self.assertEqual(row["state"], "agreed")
        self.assertFalse(row["training_masked"])

    def test_no_cross_page_match(self):
        a, b, pages, p = inputs()
        b["claims"][0]["page"] = 2
        self.assertEqual(s.reconcile(a,b,pages,p)["claims"][0]["state"], "withheld")

    def test_line_wrap_not_paraphrase(self):
        self.assertEqual(s.normalize("nano-\ncrystals"), "nanocrystals")
        a,b,pages,p = inputs()
        b["claims"][0]["quote"] = b["claims"][0]["quote"].replace("heated", "reacted")
        self.assertIn("quote_page_mismatch", s.reconcile(a,b,pages,p)["claims"][0]["validation_errors"][1])

    def test_unit_case_sensitive(self):
        self.assertNotEqual(s.normalize("mM"), s.normalize("mm"))

    def test_kelvin_not_celsius(self):
        a,b,pages,p=inputs()
        b["claims"][0].update(unit="K",unit_text="K")
        self.assertIn("unit_anchor_mismatch", s.reconcile(a,b,pages,p)["claims"][0]["validation_errors"][1])

    def test_value_and_unit_must_be_adjacent(self):
        a,b,pages,p=inputs()
        b["claims"][0].update(value=30,value_text="30")
        self.assertIn("numeric_unit_pair_not_in_quote", s.reconcile(a,b,pages,p)["claims"][0]["validation_errors"][1])

    def test_bad_source_and_figure_forbidden(self):
        a,b,pages,p=inputs()
        b["claims"][0].update(modality="figure_read",document_id="wrong")
        errors=s.reconcile(a,b,pages,p)["claims"][0]["validation_errors"][1]
        self.assertIn("not_explicit_text",errors)
        self.assertIn("wrong_source_document",errors)

    def test_duplicate_claim_retained_withheld(self):
        a,b,pages,p=inputs();a["claims"].append(copy.deepcopy(a["claims"][0]))
        row=s.reconcile(a,b,pages,p)["claims"][0]
        self.assertEqual(row["state"],"withheld")
        self.assertEqual(row["pass_alternative_counts"],[2,1])
        self.assertEqual(len(row["alternatives"]),3)

    def test_same_pass_and_shared_draft_error(self):
        a,b,pages,p=inputs();b["pass_id"]=a["pass_id"]
        with self.assertRaisesRegex(ValueError,"Same extraction"):
            s.reconcile(a,b,pages,p)
        b["pass_id"]="b";b["saw_other_draft"]=True
        with self.assertRaisesRegex(ValueError,"Separate local"):
            s.reconcile(a,b,pages,p)

    def test_pipeline_configuration_bound(self):
        a,b,pages,p=inputs();b["pipeline_sha256"]="a"*64
        with self.assertRaisesRegex(ValueError,"configuration"):
            s.reconcile(a,b,pages,p)

    def test_unknown_extra_and_nan_rejected(self):
        a,b,pages,p=inputs();b["claims"][0]["inferred"]=True
        self.assertEqual(s.reconcile(a,b,pages,p)["claims"][0]["state"],"withheld")
        c=claim(value=float("nan"))
        self.assertIn("invalid_numeric_value",s.validate_claim(c,pages,"paper1",{}))

    def test_unsupported_fields_and_ranges(self):
        c=claim("absorption_inferred_size")
        self.assertIn("unsupported_field",s.validate_claim(c,{},"paper1",{}))
        c=claim(value=[2,4])
        self.assertIn("invalid_numeric_value",s.validate_claim(c,{},"paper1",{}))

    def test_range_endpoint_and_approximation_withheld(self):
        for text,value in (("Method A used 230–300 °C.",300),("Method A used approximately 270 °C.",270),("Method A used 270 °C to 300 °C.",270)):
            a,b,pages,p=inputs()
            pages["documents"]["main"]["pages"]["1"]=text
            for d in (a,b):d["claims"][0].update(value=value,value_text=str(value),quote=text,link_quote=text)
            self.assertIn("range_or_approximation_not_scalar",s.reconcile(a,b,pages,p)["claims"][0]["validation_errors"][0])

    def test_slot_formatting_only_normalization(self):
        a,b,pages,p=inputs()
        a["claims"][0]["slot_id"]="iron(III) acetylacetonate-amount"
        b["claims"][0]["slot_id"]="iron-iii-acetylacetonate-amount"
        self.assertEqual(s.reconcile(a,b,pages,p)["claims"][0]["state"],"agreed")
        b["claims"][0]["slot_id"]="iron-ii-acetylacetonate-amount"
        self.assertEqual(len(s.reconcile(a,b,pages,p)["claims"]),2)

    def test_exact_numeric_unit_lexical_anchor(self):
        a,b,pages,p=inputs()
        a["claims"][0]["value_text"]="270 °C"
        self.assertEqual(s.reconcile(a,b,pages,p)["claims"][0]["state"],"agreed")
        a["claims"][0]["value_text"]="270 K"
        self.assertEqual(s.reconcile(a,b,pages,p)["claims"][0]["state"],"withheld")


class TestScienceGuards(unittest.TestCase):
    def test_explicit_structure_sample_required(self):
        a,b,pages,p=inputs()
        c=claim("particle_diameter",4,"nm");c["technique"]="TEM"
        a["claims"]=[c];b["claims"]=[copy.deepcopy(c)]
        self.assertIn("invalid_sample_id",s.reconcile(a,b,pages,p)["claims"][0]["validation_errors"][0])
        for d in (a,b):d["claims"][0]["sample_id"]="sample A"
        self.assertEqual(s.reconcile(a,b,pages,p)["claims"][0]["state"],"agreed")

    def test_dls_not_core_and_absorption_not_size(self):
        a,b,pages,p=inputs()
        for technique in ("DLS","UVVis"):
            c=claim("particle_diameter",4,"nm","sample A");c["technique"]=technique
            self.assertIn("descriptor_technique_mismatch",s.validate_claim(c,pages,"paper1",{}))

    def test_phase_not_invented(self):
        c=claim("phase","wurtzite",None,"sample A");c["technique"]="XRD"
        self.assertIn("value_not_in_quote",s.validate_claim(c,inputs()[2],"paper1",{}))

    def test_technique_requires_source_text_anchor(self):
        a,b,pages,p=inputs()
        text="Method A produces sample A with 4 nm particle diameter."
        pages["documents"]["main"]["pages"]["1"]=text
        c=claim("particle_diameter",4,"nm","sample A");c.update(quote=text,link_quote=text,technique="TEM")
        self.assertIn("technique_source_anchor_missing",s.validate_claim(c,pages,"paper1",{}))
        pages["documents"]["main"]["pages"]["2"]="TEM was used for particle sizing."
        c.update(technique_page=2,technique_quote="TEM was used for particle sizing.")
        self.assertEqual(s.validate_claim(c,pages,"paper1",{}),[])

    def test_sample_link_does_not_match_unrelated_name(self):
        c=claim("particle_diameter",4,"nm","sample B");c["technique"]="TEM"
        self.assertIn("explicit_sample_link_missing",s.validate_claim(c,inputs()[2],"paper1",{}))

    def test_chemical_identity_registry_required(self):
        c=claim("precursor_identity","cobalt acetate",None)
        self.assertIn("unresolved_chemical_identity",s.validate_claim(c,inputs()[2],"paper1",{}))

    def test_disagreement_retained_masked(self):
        for band,state in (("high","withheld"),("medium","uncertain"),("low","uncertain")):
            a,b,pages,p=inputs(band)
            text="Method A used 270 °C or 280 °C."
            pages["documents"]["main"]["pages"]["1"]=text
            for d in (a,b):d["claims"][0].update(quote=text,link_quote=text)
            b["claims"][0].update(value=280,value_text="280")
            row=s.reconcile(a,b,pages,p)["claims"][0]
            self.assertEqual(row["state"],state);self.assertTrue(row["training_masked"])
            self.assertEqual(len(row["alternatives"]),2)

    def test_core_shell_inconsistency_withheld(self):
        a,b,pages,p=inputs()
        text="Method A produces sample A with 4 nm core diameter, 2 nm shell thickness, and 5 nm particle diameter by TEM."
        pages["documents"]["main"]["pages"]["1"]=text
        claims=[]
        for f,v in (("core_diameter",4),("shell_thickness",2),("particle_diameter",5)):
            c=claim(f,v,"nm","sample A");c.update(quote=text,link_quote=text,technique="TEM");claims.append(c)
        a["claims"]=claims;b["claims"]=copy.deepcopy(claims)
        result=s.reconcile(a,b,pages,p)
        self.assertTrue(all(r["state"]=="withheld" for r in result["claims"]))
        s.reconciled_contract(result,p)

    def test_duplicate_dimension_slots_never_overwrite(self):
        a,b,pages,p=inputs()
        text="Method A produces sample A with 4 nm particle diameter by TEM."
        pages["documents"]["main"]["pages"]["1"]=text
        c=claim("particle_diameter",4,"nm","sample A");c.update(quote=text,link_quote=text,technique="TEM")
        d=copy.deepcopy(c);d["slot_id"]="alternate-diameter"
        a["claims"]=[c,d];b["claims"]=copy.deepcopy(a["claims"])
        result=s.reconcile(a,b,pages,p)
        self.assertTrue(all(r["state"]=="withheld" for r in result["claims"]))
        self.assertTrue(all("ambiguous_dimension_slots" in r["validation_errors"][0] for r in result["claims"]))
        s.reconciled_contract(result,p)


class TestCalibration(unittest.TestCase):
    def test_exact_binomial_endpoints(self):
        self.assertEqual(s.lower_bound(0,0),0)
        self.assertAlmostEqual(s.lower_bound(1,1),.05)
        self.assertAlmostEqual(s.lower_bound(2,3),.1353503621715838,places=10)
        self.assertLess(s.lower_bound(148,148),.98)
        self.assertGreaterEqual(s.lower_bound(149,149),.98)

    def test_repeated_instances_report_source_dependence(self):
        result=s.calibrate(*calibration_data(1,repeated=200))
        m=result["metrics"][0]
        self.assertEqual(m["predicted_instances"],200)
        self.assertEqual(m["distinct_source_clusters"],1)
        self.assertEqual(m["status"],"eligible_for_independent_calibration_review")
        self.assertTrue(m["source_dependence_warning"])
        self.assertEqual(result["status"],"INDEPENDENT_REVIEW_REQUIRED")

    def test_sixty_sources_insufficient_high_band(self):
        result=s.calibrate(*calibration_data(60))
        self.assertEqual(result["status"],"STOP")
        self.assertEqual(result["metrics"][0]["minimum_zero_error_instances"],149)

    def test_all_fields_not_automatically_approved_by_other_field(self):
        truth,pred,p=calibration_data(60,"medium")
        result=s.calibrate(truth,pred,p)
        self.assertEqual(result["status"],"INDEPENDENT_REVIEW_REQUIRED")
        self.assertFalse(result["publication_enabled"])

    def test_error_and_omission_count(self):
        truth,pred,p=calibration_data(2,wrong=1)
        pred.pop()
        m=s.calibrate(truth,pred,p)["metrics"][0]
        self.assertEqual((m["true_positive"],m["false_positive"],m["false_negative"]),(0,1,2))
        self.assertEqual(m["recall"],0)

    def test_holdout_leakage_and_self_audit(self):
        truth,pred,p=calibration_data()
        truth["selection_source_ids"]=["paper0"]
        with self.assertRaisesRegex(ValueError,"leakage"):s.calibrate(truth,pred,p)
        truth["selection_source_ids"]=[];truth["auditor_id"]="author"
        with self.assertRaisesRegex(ValueError,"Separate gold auditor"):s.calibrate(truth,pred,p)

    def test_calibration_requires_complete_provenance(self):
        for name in ("extractor_id","training_source_ids","selection_source_ids"):
            truth,pred,p=calibration_data();truth.pop(name)
            with self.assertRaises(ValueError):s.calibrate(truth,pred,p)
        for bad in ("paper1",[""],["C:/private/source.pdf"]):
            truth,pred,p=calibration_data();truth["training_source_ids"]=bad
            with self.assertRaises(ValueError):s.calibrate(truth,pred,p)

    def test_duplicate_source_rejected(self):
        truth,pred,p=calibration_data()
        pred.append(pred[0])
        with self.assertRaisesRegex(ValueError,"duplicate source"):s.calibrate(truth,pred,p)

    def test_input_gold_unchanged(self):
        truth,pred,p=calibration_data()
        before=s.digest(truth);s.calibrate(truth,pred,p)
        self.assertEqual(before,s.digest(truth))

    def test_calibration_sample_source_counts(self):
        truth,pred,p=calibration_data(149)
        m=s.calibrate(truth,pred,p)["metrics"][0]
        self.assertEqual(m["status"],"eligible_for_independent_calibration_review")


class TestProjection(unittest.TestCase):
    def setup_pass(self):
        truth,pred,p=calibration_data(60,"medium")
        cal=s.calibrate(truth,pred,p)
        approval={"approved":True,"calibration_sha256":s.digest(cal),"reviewer_id":"second-reviewer","independent":True,"extractor_ids":["author"],"field_instance_iid_assumption_reviewed":True}
        return pred[0],cal,p,approval

    def test_requires_separate_calibration_review(self):
        pred,cal,p,approval=self.setup_pass()
        result=s.project(pred,cal,p)
        self.assertFalse(result["has_publishable_values"])
        self.assertTrue(result["fields"][0]["training_masked"])

    def test_projection_never_quotes_paths_or_gold_label(self):
        pred,cal,p,approval=self.setup_pass()
        result=s.project(pred,cal,p,approval,inputs("medium","paper0")[2])
        self.assertTrue(result["has_publishable_values"])
        self.assertFalse(result["publication_enabled"])
        text=str(result)
        self.assertNotIn("Method A was heated",text)
        self.assertNotIn("link_quote",text)
        self.assertEqual(result["tier"],"silver")
        self.assertLess(result["fields"][0]["training_weight"],1)

    def test_stale_review_or_self_approval_withheld(self):
        pred,cal,p,approval=self.setup_pass()
        approval["calibration_sha256"]="0"*64
        self.assertFalse(s.project(pred,cal,p,approval)["has_publishable_values"])
        approval["calibration_sha256"]=s.digest(cal);approval["reviewer_id"]="author"
        self.assertFalse(s.project(pred,cal,p,approval)["has_publishable_values"])

    def test_uncertain_values_never_training(self):
        pred,cal,p,approval=self.setup_pass()
        pred["claims"][0]["state"]="uncertain"
        pred["claims"][0]["training_masked"]=True
        result=s.project(pred,cal,p,approval,inputs("medium","paper0")[2])
        self.assertEqual(result["fields"][0]["state"],"uncertain")
        self.assertIsNone(result["fields"][0]["value"])
        self.assertEqual(result["fields"][0]["training_weight"],0)

    def test_distinct_source_not_record_count(self):
        pred,cal,p,approval=self.setup_pass()
        result=s.project(pred,cal,p,approval,inputs("medium","paper0")[2])
        self.assertEqual(s.count_sources([result,result]),1)

    def test_unseen_field_stops(self):
        pred,cal,p,approval=self.setup_pass()
        pred["claims"][0]["key"][3]="duration"
        with self.assertRaisesRegex(ValueError,"key differs"):
            s.project(pred,cal,p,approval)

    def test_missing_page_map_cannot_publish(self):
        pred,cal,p,approval=self.setup_pass()
        self.assertFalse(s.project(pred,cal,p,approval)["has_publishable_values"])

    def test_projection_revalidates_impossible_value(self):
        pred,cal,p,approval=self.setup_pass()
        for alt in pred["claims"][0]["alternatives"]:alt.update(value=-300,value_text="-300")
        self.assertFalse(s.project(pred,cal,p,approval,inputs("medium","paper0")[2])["has_publishable_values"])

    def test_projection_rejects_mismatch_or_single_pass(self):
        pred,cal,p,approval=self.setup_pass()
        pred["claims"][0]["alternatives"][1]["value"]=280
        with self.assertRaisesRegex(ValueError,"agreement"):
            s.project(pred,cal,p,approval)
        pred,cal,p,approval=self.setup_pass()
        pred["claims"][0]["alternatives"].pop()
        with self.assertRaises(ValueError):s.project(pred,cal,p,approval)

    def test_projection_rejects_unknown_family_and_long_source_text_id(self):
        pred,cal,p,approval=self.setup_pass();pred["family_id"]="not-registered"
        with self.assertRaisesRegex(ValueError,"family/band"):
            s.project(pred,cal,p,approval)
        pred,cal,p,approval=self.setup_pass();pred["claims"][0]["key"][0]="Raw source paragraph "*15
        with self.assertRaisesRegex(ValueError,"public claim IDs"):
            s.project(pred,cal,p,approval)

    def test_independent_review_must_address_dependence(self):
        pred,cal,p,approval=self.setup_pass();approval.pop("field_instance_iid_assumption_reviewed")
        self.assertFalse(s.project(pred,cal,p,approval,inputs("medium","paper0")[2])["has_publishable_values"])


if __name__ == "__main__":
    unittest.main()
