"""DOI extraction regressions; metadata strings only, no papers or model payloads."""
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parent / 'mattersyn_simple.py'
SPEC = importlib.util.spec_from_file_location('simple_tidy_doi_test', MODULE)
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)

TITANIA = '10.1002/1521-3862(200010)6:5<239::aid-cvde239>3.0.co;2-q'
NITRIDE = '10.1002/1521-396x(200202)189:3<691::aid-pssa691>3.0.co;2-3'


class TidyDoiTests(unittest.TestCase):
    def test_registered_sici_dois_keep_angle_section_and_checksum(self):
        for doi in (TITANIA, NITRIDE):
            with self.subTest(doi=doi):
                self.assertEqual(m.tidy_doi(doi), doi)

    def test_sici_url_and_double_quoted_markup(self):
        for value in ('https://doi.org/' + TITANIA,
                      '<a href="https://doi.org/' + NITRIDE + '">DOI</a>'):
            with self.subTest(value=value):
                self.assertEqual(m.tidy_doi(value), TITANIA if TITANIA in value else NITRIDE)

    def test_sici_case_and_surrounding_punctuation_are_preserved(self):
        doi = NITRIDE.upper()
        self.assertEqual(m.tidy_doi('DOI: ' + doi + ').'), doi)
        self.assertEqual(m.tidy_doi('[' + TITANIA + ']'), TITANIA)

    def test_existing_parenthesized_sici_prefix(self):
        doi = '10.1002/(SICI)1234-5678(200001)1:2<3::AID-EXAMPLE>3.0.CO;2-X'
        self.assertEqual(m.tidy_doi(doi), doi)

    def test_ordinary_dois_and_punctuation_are_unchanged(self):
        for value, expected in (
            ('doi:10.1021/acs.langmuir.0c02477.', '10.1021/acs.langmuir.0c02477'),
            ('[10.1016/j.example.2020.123456)]', '10.1016/j.example.2020.123456'),
            ('10.1234/example; prose', '10.1234/example'),
            ('10.1234/first, 10.1234/second', '10.1234/first'),
        ):
            with self.subTest(value=value):
                self.assertEqual(m.tidy_doi(value), expected)

    def test_ordinary_markup_is_not_part_of_the_doi(self):
        for value in ('<a href="https://doi.org/10.1234/example">link</a>',
                      '10.1234/example<em>caption</em>',
                      '10.1234/example<em>text;2-q'):
            with self.subTest(value=value):
                self.assertEqual(m.tidy_doi(value), '10.1234/example')

    def test_incomplete_sici_is_not_extended_through_markup(self):
        for value in ('10.1234/example<239::AID-X>broken;2-q',
                      '10.1234/example<239::AID-X>3.0.CO;2-'):
            with self.subTest(value=value):
                self.assertEqual(m.tidy_doi(value), '10.1234/example')

    def test_first_doi_and_no_doi_behavior_are_unchanged(self):
        self.assertEqual(m.tidy_doi('10.1234/first ' + TITANIA), '10.1234/first')
        for value in (None, '', 'No identifier here'):
            with self.subTest(value=value):
                self.assertEqual(m.tidy_doi(value), '')

    def test_old_processing_labels_are_not_relabelled_as_canonical(self):
        label = '10.1002/1521-3862(200010)6_5_239__aid-cvde239_3.3.co;2-h'
        self.assertNotEqual(m.tidy_doi(label), TITANIA)

    def test_page_guess_retains_complete_sici_doi(self):
        self.assertEqual(m.doi_guess(['Generated metadata DOI: ' + TITANIA], 'unused'), TITANIA)


if __name__ == '__main__':
    unittest.main()
