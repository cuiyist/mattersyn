import unittest

from validate_quote_spans import normalize_for_quote_match, split_pdf_pages, validate_quotes


class QuoteSpanValidationTests(unittest.TestCase):
    def test_page_markers_and_exact_quote(self):
        pages = split_pdf_pages("===== PDF PAGE 1 =====\nAlpha route.\n===== PDF PAGE 2 =====\nBeta route.")
        result = validate_quotes(pages, {"pdf_page": 2, "procedure_claims": [{"exact_verbatim_quote": "Beta route."}]})
        self.assertEqual((result["matched_count"], result["unmatched_count"]), (1, 0))

    def test_line_end_hyphenation_is_joined(self):
        pages = split_pdf_pages("===== PDF PAGE 2 =====\nThe precipi-\ntate was washed.")
        result = validate_quotes(pages, {"pdf_page": 2, "procedure_claims": [{"exact_verbatim_quote": "The precipitate was washed."}]})
        self.assertEqual(result["matched_count"], 1)

    def test_citation_omission_is_not_accepted(self):
        pages = split_pdf_pages("===== PDF PAGE 2 =====\nAqueous coprecipitation of Co2+ and Fe3+ ions29 (method B).")
        result = validate_quotes(pages, {"pdf_page": 2, "procedure_claims": [{"exact_verbatim_quote": "Aqueous coprecipitation of Co2+ and Fe3+ ions (method B)."}]})
        self.assertEqual(result["unmatched_count"], 1)

    def test_quote_must_be_on_cited_page(self):
        pages = split_pdf_pages("===== PDF PAGE 1 =====\nExact source.\n===== PDF PAGE 2 =====\nOther source.")
        result = validate_quotes(pages, {"pdf_page": 2, "procedure_claims": [{"exact_verbatim_quote": "Exact source."}]})
        self.assertEqual(result["unmatched_count"], 1)

    def test_nfkc_only_normalizes_compatibility_forms(self):
        self.assertEqual(normalize_for_quote_match("The ﬁnal product"), normalize_for_quote_match("The final product"))
        self.assertNotEqual(normalize_for_quote_match("Cu Kα"), normalize_for_quote_match("Cu KR"))


if __name__ == "__main__":
    unittest.main()
