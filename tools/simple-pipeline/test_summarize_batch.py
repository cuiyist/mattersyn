import copy
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).parent))
import summarize_batch as helper


class SyntheticChecks:
    is_route = staticmethod(lambda r: any(o.get('stage') == 'synthesis' for o in r.get('operations', [])))
    material_id = staticmethod(lambda formula: 'material-' + formula.casefold())

    def errors(self, record):
        if not self.is_route(record):
            return ['no_synthesis_operation']
        if not record['material']['elements']:
            return ['material_elements_invalid']
        return []


class BatchSummaryTest(unittest.TestCase):
    def doc(self):
        return {'id': 'sample', 'doi': '10.1234/sample', 'authors': 'Example Researcher', 'year': '2026',
                'check': helper.CHECK, 'figures': [], 'private_path': 'C:/private/full-paper.pdf',
                'pairs': [{'product': 'CdSe dots', 'structure': {'composition': {'value': 'CdSe', 'page': 2, 'quote': 'PRIVATE-SOURCE-QUOTE'}},
                           'recipe': {'chemicals': [{'name': 'cadmium oxide', 'role': 'metal source', 'amount': 0.4, 'unit': 'mmol',
                                                    'page': 2, 'quote': 'PRIVATE-CHEMICAL-QUOTE'}],
                                      'reaction_temperature': {'value': 240, 'unit': '°C', 'page': 2, 'quote': 'PRIVATE-TEMP-QUOTE'},
                                      'reaction_time': {'value': 5, 'unit': 'min', 'page': 2, 'quote': 'PRIVATE-TIME-QUOTE'},
                                      'steps': [{'action': 'heat', 'page': 2, 'quote': 'PRIVATE-STEP-QUOTE'}]}}]}

    def run_summary(self, doc=None, **kwargs):
        return helper.summary([(Path('sample.pairs.json'), doc or self.doc())], SyntheticChecks(), **kwargs)

    def test_ready_and_rare_and_five_fields(self):
        result = self.run_summary(existing_routes={'CdSe': 2})
        self.assertEqual(result['totals']['eligible_records'], 1)
        self.assertEqual(result['totals']['eligible_papers'], 1)
        self.assertEqual(result['totals']['five_field_complete_records'], 1)
        record = result['papers'][0]['records'][0]
        self.assertTrue(record['rare_material'])
        self.assertEqual(record['existing_routes'], 2)
        self.assertFalse(result['five_field_completeness_is_admission_gate'])

    def test_optional_fields_and_missing_counter_fields_do_not_change_route(self):
        doc = self.doc()
        del doc['pairs'][0]['recipe']['reaction_time']
        doc['pairs'][0]['recipe']['chemicals'][0]['role'] = 'ligand'
        result = self.run_summary(doc, existing_routes={'CdSe': 3})
        self.assertEqual(result['totals']['eligible_records'], 1)
        self.assertEqual(result['totals']['five_field_complete_records'], 0)
        self.assertFalse(result['papers'][0]['records'][0]['rare_material'])
        self.assertFalse(result['papers'][0]['records'][0]['five_fields_present']['precursor_with_amount'])

    def test_no_private_values_paths_or_captions_and_input_unchanged(self):
        doc = self.doc()
        doc['figures'] = [{'file': 'C:/private/figure-1.png', 'caption': 'PRIVATE-FIGURE-CAPTION', 'figure': 'Figure 1'}]
        before = copy.deepcopy(doc)
        report = json.dumps(self.run_summary(doc))
        for private in ('PRIVATE-', 'private/', 'cadmium oxide', '240', 'Example Researcher', 'quote', 'caption'):
            self.assertNotIn(private, report)
        self.assertEqual(doc, before)

    def test_missing_or_stale_check_leaves_out_records(self):
        for value in (None, 'quote found', 'single pass'):
            doc = self.doc(); doc['check'] = value
            result = self.run_summary(doc)
            self.assertEqual(result['totals']['eligible_records'], 0)
            self.assertEqual(result['papers'][0]['status'], 'not_two_pass_checked')

    def test_primary_doi_duplicates_count_once(self):
        a, b = self.doc(), self.doc(); b['doi'] = 'https://doi.org/10.1234/SAMPLE'
        result = helper.summary([(Path('one.pairs.json'), a), (Path('two.pairs.json'), b)], SyntheticChecks())
        self.assertEqual(result['totals']['eligible_papers'], 1)
        self.assertEqual(result['papers'][1]['status'], 'duplicate_doi_in_batch')
        self.assertEqual(result['papers'][1]['duplicate_of_paper_id'], 'one')

    def test_published_doi_and_protected_source_left_out(self):
        result = self.run_summary(known_dois={'10.1234/SAMPLE'})
        self.assertEqual(result['papers'][0]['status'], 'doi_already_in_site_baseline')
        self.assertEqual(result['totals']['eligible_records'], 0)
        builder = helper.to_site.Builder(self.doc())
        result = self.run_summary(known_sources={builder.source_id: {'doi': '10.1234/sample', 'status': 'source_reviewed'}})
        self.assertEqual(result['papers'][0]['status'], 'protected_source_identity')

    def test_chemical_only_or_workup_only_is_not_a_route(self):
        for steps in ([], [{'action': 'wash', 'page': 2}]):
            doc = self.doc(); doc['pairs'][0]['recipe']['steps'] = steps
            result = self.run_summary(doc)
            self.assertEqual(result['totals']['generated_records'], 1)
            self.assertEqual(result['totals']['eligible_records'], 0)
            self.assertEqual(result['papers'][0]['records'][0]['hold_reasons'], ['no_synthesis_operation'])

    def test_numeric_zero_is_present_and_bool_is_not(self):
        pair = self.doc()['pairs'][0]
        pair['recipe']['reaction_temperature']['value'] = 0
        self.assertTrue(helper.five_fields(pair)['reaction_temperature'])
        pair['recipe']['reaction_time']['value'] = True
        self.assertFalse(helper.five_fields(pair)['reaction_time'])

    def test_bad_json_and_conversion_error_reveal_no_error_payload(self):
        doc = self.doc(); doc['pairs'][0]['recipe']['chemicals'] = [{'quote': 'PRIVATE'}]
        result = helper.summary([(Path('bad.pairs.json'), None), (Path('broken.pairs.json'), doc)], SyntheticChecks())
        self.assertEqual([r['status'] for r in result['papers']], ['invalid_pair_json', 'conversion_or_metadata_error'])
        self.assertNotIn('PRIVATE', json.dumps(result))

    def test_baseline_uses_primary_sources_and_site_route_counts(self):
        with TemporaryDirectory(dir=Path(__file__).parent) as work:
            site = Path(work); (site / 'data').mkdir()
            record = helper.to_site.records_of(self.doc())[1][0]
            record['sources'].append({'id': 'reference', 'doi': '10.1234/reference'})
            (site / 'data/records.jsonl').write_text(json.dumps(record) + '\n', encoding='utf-8')
            (site / 'data/materials-index.json').write_text(json.dumps({'materials': [{'formula': 'CdSe', 'route_records': 4, 'reviewed_records': 2}]}), encoding='utf-8')
            dois, sources, routes = helper.baseline(site, SyntheticChecks())
            self.assertEqual(dois, {'10.1234/sample'})
            self.assertEqual(routes['CdSe'], 4)
            self.assertEqual(sources[record['lineage']['source_group']]['status'], 'source_extracted')

    def test_crop_basename_is_found_in_converter_figures_folder(self):
        with TemporaryDirectory(dir=Path(__file__).parent) as work:
            pairs = Path(work); (pairs / 'figures').mkdir()
            (pairs / 'figures/figure-1.png').write_bytes(b'synthetic-crop')
            doc = self.doc(); doc['figures'] = [{'file': 'figure-1.png', 'caption': 'PRIVATE-CAPTION'}]
            result = helper.summary([(pairs / 'sample.pairs.json', doc)], SyntheticChecks())
            row = result['papers'][0]
            self.assertEqual((row['figures_listed'], row['figure_files_found'], row['missing_figure_files']), (1, 1, 0))
            self.assertNotIn('PRIVATE', json.dumps(result))


if __name__ == '__main__':
    unittest.main()
