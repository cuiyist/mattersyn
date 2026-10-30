import contextlib
import copy
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

import summarize_batch
import to_site


class MicroscopyGridStageTest(unittest.TestCase):
    def doc(self, description='Deposit preformed metal clusters onto a copper TEM grid.'):
        return {'id': 'synthetic-grid-preparation', 'doi': '10.1234/synthetic-grid-preparation',
                'authors': 'Fixture', 'year': 2026, 'check': summarize_batch.CHECK, 'figures': [],
                'pairs': [{'product': 'preformed Au nanoclusters',
                           'structure': {'composition': {'value': 'Au', 'page': 1}},
                           'recipe': {'steps': [{'action': 'deposit', 'description': description,
                                                 'uses': [], 'page': 1}]}}]}

    def checks(self):
        return summarize_batch.ProjectChecks(Path(__file__).parents[2])

    def test_specimen_preparation_has_no_route_in_summary_or_written_record(self):
        for description in ('Deposit preformed metal clusters onto a copper TEM grid.',
                            'Passivated clusters on copper grid'):
            with self.subTest(description=description):
                doc = self.doc(description)
                doc['pairs'][0]['product'] = 'passivated Au nanoclusters'
                before = copy.deepcopy(doc)
                record = to_site.records_of(doc)[1][0]
                self.assertEqual(record['operations'][0]['stage'], 'workup')
                self.assertEqual(record['operations'][0]['action'], 'deposit')
                self.assertEqual(self.checks().errors(record), ['no_synthesis_operation'])
                report = summarize_batch.summary([(Path('synthetic.pairs.json'), doc)], self.checks())
                self.assertEqual(report['totals']['eligible_records'], 0)
                self.assertEqual(report['papers'][0]['records'][0]['hold_reasons'], ['no_synthesis_operation'])
                with TemporaryDirectory(dir=Path(__file__).parent) as tmp:
                    repo = Path(tmp)
                    records = repo / 'recipe-atlas/data/records'
                    records.mkdir(parents=True)
                    inventory = repo / 'recipe-atlas/data/inventory-evidence.json'
                    inventory.write_text(json.dumps({'per_paper': []}), encoding='utf-8')
                    pairs = repo / 'pairs'
                    pairs.mkdir()
                    pairfile = pairs / 'synthetic.pairs.json'
                    pairfile.write_text(json.dumps(doc), encoding='utf-8')
                    pair_before = pairfile.read_bytes()
                    with contextlib.redirect_stdout(io.StringIO()):
                        to_site.cmd_records(SimpleNamespace(repo=repo, pairs=pairs, replace=True, include_optical=False))
                    written = [json.loads(p.read_bytes()) for p in records.glob('*.json')]
                    self.assertEqual(len(written), 1)
                    self.assertEqual(written[0]['operations'], record['operations'])
                    self.assertEqual(self.checks().errors(written[0]), ['no_synthesis_operation'])
                    self.assertEqual(pairfile.read_bytes(), pair_before)
                self.assertEqual(doc, before)

    def test_formation_before_grid_preparation_keeps_route_and_original_ordinal(self):
        doc = self.doc()
        doc['pairs'][0]['recipe']['steps'].insert(0, {'action': 'reduce', 'description': 'Reduce the metal precursor', 'page': 1})
        doc['pairs'].insert(0, {'product': 'unselected fixture'})
        before = copy.deepcopy(doc)
        record = to_site.records_of(doc, original_ordinals=[2])[1][0]
        self.assertTrue(record['record_id'].endswith('-2'))
        self.assertEqual([op['stage'] for op in record['operations']], ['synthesis', 'workup'])
        self.assertEqual(record['operations'][1]['depends_on'], [record['operations'][0]['id']])
        self.assertEqual(self.checks().errors(record), [])
        self.assertEqual(record['quality']['review_status'], 'source_extracted')
        self.assertEqual(doc, before)

    def test_growth_precursor_or_device_deposition_stays_synthesis(self):
        descriptions = ('Deposit metal precursor onto a copper TEM grid.',
                        'Deposit preformed metal clusters onto a copper TEM grid and grow shells.',
                        'Grow passivated clusters on copper grid',
                        'Deposit preformed metal clusters onto a device substrate.',
                        'Deposit metal from solution onto copper.')
        for description in descriptions:
            with self.subTest(description=description):
                doc = self.doc(description)
                before = copy.deepcopy(doc)
                record = to_site.records_of(doc)[1][0]
                self.assertEqual(record['operations'][0]['stage'], 'synthesis')
                self.assertEqual(self.checks().errors(record), [])
                self.assertEqual(doc, before)
        doc = self.doc()
        doc['pairs'][0]['product'] = 'new Au deposit'
        self.assertEqual(to_site.records_of(doc)[1][0]['operations'][0]['stage'], 'synthesis')


if __name__ == '__main__':
    unittest.main()
