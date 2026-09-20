"""Adverse-case tests for the private proposal, without mutating inputs or Site."""
import copy
import unittest
import prepare_proposal as p


class ProposalBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.originals = {
            r['record_id']: r
            for folder in p.AUDITS
            for path in (p.REVIEW / folder).glob('*.json')
            for r in [p.read(path)]
        }
        cls.proposals = {
            r['record_id']: r for path in (p.OUT / 'records').glob('*.json')
            for r in [p.read(path)]
        }
        cls.context = p.read(p.OUT / 'source-context.json')

    def assertRejected(self, mutate, expected_error):
        candidate = copy.deepcopy(self.proposals)
        mutate(candidate)
        result, _ = p.validate_proposals(self.originals, candidate, self.context)
        self.assertEqual(result['status'], 'failed')
        self.assertTrue(any(expected_error in error for error in result['errors']), result['errors'])

    def test_valid_proposal(self):
        result, views = p.validate_proposals(self.originals, self.proposals, self.context)
        self.assertEqual(result['errors'], [])
        self.assertEqual(len(views), 6)

    def test_reintroduced_study_range_quantity_is_rejected(self):
        def mutate(records):
            rid = p.VARIANTS[0]
            original = self.originals[rid]['operations'][0]['parameters'][p.RANGE_KEY]
            records[rid]['operations'][0]['parameters'][p.RANGE_KEY] = copy.deepcopy(original)
        self.assertRejected(mutate, 'no study-wide concentration leakage')

    def test_reintroduced_study_range_material_note_is_rejected(self):
        def mutate(records):
            records[p.VARIANTS[0]]['materials'][0]['notes'][0] += ' Further diluted to 3–30 ppm.'
        self.assertRejected(mutate, 'no study-wide concentration leakage')

    def test_supporting_procedure_training_promotion_is_rejected(self):
        def mutate(records):
            records[p.PREFIX + 'acid-activation']['quality']['requested_tasks'] = ['partial_protocol']
        self.assertRejected(mutate, 'actual eligible tasks exactly scoped')

    def test_invented_physical_batch_is_rejected(self):
        def mutate(records):
            records[p.VARIANTS[0]]['lineage']['batch_id'] = 'invented-same-batch'
        self.assertRejected(mutate, 'preserve lineage')

    def test_invented_matched_si_claim_is_rejected(self):
        def mutate(records):
            records[p.VARIANTS[0]]['sources'][0]['si_status'] = 'matched and read'
        self.assertRejected(mutate, 'preserve source identity and SI status')

    def test_collapsed_temperature_conflict_is_rejected(self):
        def mutate(records):
            op = next(o for o in records[p.VARIANTS[0]]['operations'] if o['id'] == 'pyrolysis')
            op['parameters']['text_temperature']['value'] = 865
        self.assertRejected(mutate, 'operations unchanged except removed study-wide range')

    def test_measurement_sample_reassignment_is_rejected(self):
        def mutate(records):
            records['littau-1993-aks41-context']['measurements'][0]['sample_id'] = records['littau-1993-aks41-context']['products'][-1]['sample_id']
        self.assertRejected(mutate, 'preserve measurements')


if __name__ == '__main__':
    unittest.main(verbosity=2)
