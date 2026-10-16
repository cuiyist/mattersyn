import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("identity_preflight", Path(__file__).with_name("bibliographic_identity_preflight.py"))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def row(doi="10.1002/ange.200700197", title="A specific nanocrystal paper", year=2007,
        authors=None):
    return {"doi": doi, "title": title, "year": year,
            "authors": ["Jianping Ge", "Yadong Yin"] if authors is None else authors}


class IdentityTests(unittest.TestCase):
    def test_existing_representation_wins_over_english(self):
        old = row()
        incoming = row("10.1002/anie.200700197")
        result = M.screen([incoming], [old])
        self.assertEqual(result["strong_alias_proposals"][0]["represented_doi"], old["doi"])

    def test_incoming_pair_prefers_english_in_both_orders(self):
        for incoming in ([row(), row("10.1002/anie.200700197")],
                         [row("10.1002/anie.200700197"), row()]):
            result = M.screen(incoming, [])
            self.assertEqual(len(result["strong_alias_proposals"]), 1)
            self.assertEqual(result["strong_alias_proposals"][0]["incoming_doi"], "10.1002/ange.200700197")

    def test_first_already_represented_doi_is_preserved(self):
        old = [row(), row("10.1002/anie.200700197")]
        result = M.screen([row("10.1002/anie.200700197")], old)
        self.assertEqual(result["strong_alias_proposals"][0]["represented_doi"], old[0]["doi"])

    def test_same_title_without_wiley_suffix_is_ambiguous(self):
        result = M.screen([row("10.1063/1.2335400")], [row("10.1002/pssa.200565129")])
        self.assertEqual(result["strong_alias_proposals"], [])
        self.assertEqual(len(result["ambiguous_technical_holds"]), 1)

    def test_ordered_author_mismatch_or_initial_only_is_not_alias(self):
        for authors in (["Yadong Yin", "Jianping Ge"], ["J. Ge", "Y. Yin"]):
            result = M.screen([row(authors=authors)], [row("10.1002/anie.200700197")])
            self.assertEqual(result["strong_alias_proposals"], [])
            self.assertEqual(len(result["ambiguous_technical_holds"]), 1)

    def test_missing_mononym_or_comma_authors_hold(self):
        for authors in ([], ["Motlan"], "Ge, Jianping"):
            result = M.screen([row(authors=authors)], [row("10.1002/anie.200700197")])
            self.assertEqual(result["strong_alias_proposals"], [])
            self.assertEqual(result["missing_or_unsupported_identity_fields"][0]["fields"], ["authors"])

    def test_missing_title_year_and_bool_year_are_not_alias(self):
        for key, value in (("title", None), ("year", None), ("year", True)):
            incoming = row(); incoming[key] = value
            result = M.screen([incoming], [row("10.1002/anie.200700197")])
            self.assertEqual(result["strong_alias_proposals"], [])
            self.assertIn(key, result["missing_or_unsupported_identity_fields"][0]["fields"])

    def test_unicode_spacing_and_markup_normalization(self):
        result = M.screen([row(title="<i>Nanocrystal–mediated</i> growth", authors=["Ward\u2005P. Beyermann", "Yadong Yin"])],
                          [row("10.1002/anie.200700197", title="Nanocrystal-mediated growth", authors=["Ward P. Beyermann", "Yadong Yin"])])
        self.assertEqual(len(result["strong_alias_proposals"]), 1)

    def test_same_doi_uses_existing_collision_path_not_alias(self):
        result = M.screen([row()], [row()])
        self.assertEqual(result["strong_alias_proposals"], [])
        self.assertEqual(result["already_represented_same_DOI"], [row()["doi"]])

    def test_inputs_unchanged_and_no_status_or_doi_rewrite(self):
        incoming, old = [row()], [row("10.1002/anie.200700197")]
        before = copy.deepcopy([incoming, old])
        result = M.screen(incoming, old)
        self.assertEqual([incoming, old], before)
        self.assertFalse(result["DOIs_or_existing_records_rewritten"])
        self.assertFalse(result["scientific_statuses_changed"])

    def test_trusted_records_shape_flags_exact_doi(self):
        r = {"doi": "10.1002/ange.200700197", "metadata_only": True, "doi_exact_match": True,
             "citation": {"DOI": "10.1002/ange.200700197", "title": ["Test"], "authors": ["A. Author"],
                          "published": {"date-parts": [[2007]]}}}
        self.assertEqual(M.trusted_authority({"records": [r]}), [r])
        for field in ("metadata_only", "doi_exact_match"):
            altered = copy.deepcopy(r); altered[field] = 1
            with self.assertRaises(ValueError): M.trusted_authority({"records": [altered]})
        altered = copy.deepcopy(r); altered["citation"]["DOI"] = "10.1002/anie.200700197"
        with self.assertRaises(ValueError): M.trusted_authority({"records": [altered]})

    def test_default_inert_and_exclusive_output(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(M.main(["--authority", "does-not-exist.json"]), 0)
        self.assertTrue(json.loads(out.getvalue())["inert"])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "existing.json"; output.write_text("protected", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                M.main(["--execute", "--authority", "does-not-exist.json", "--existing-metadata", "also-absent.json", "--out", str(output)])
            self.assertEqual(output.read_text(), "protected")


if __name__ == "__main__":
    unittest.main()
