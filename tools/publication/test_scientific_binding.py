import copy
import json
import unittest

from scientific_binding import AuditBindingError, POLICY_SHA256, raw_sha, scientific_digest, verify_reuse, refresh_chemical_digest


class AuditReuseTests(unittest.TestCase):
    def setUp(self):
        self.record = {'record_id': 'sample-a', 'revision': 1, 'material': {'formula': 'CdSe'},
                       'recipe': {'temperature': {'value': 300, 'unit': 'degC'}, 'amount': 1},
                       'outcome': {'diameter_nm': 3, 'sample_id': 'A'},
                       'quality': {'review_status': 'source_reviewed', 'reviewer': 'first'},
                       'evidence': [{'figure': '2a', 'page': 3}], 'training_eligible': False}
        self.before = self.dump(self.record)
        self.audit = {'schema': 'mattersyn-independent-scientific-audit/1', 'status': 'passed',
                      'digest_policy_sha256': POLICY_SHA256, 'record_id': 'sample-a',
                      'reviewed_record_sha256': raw_sha(self.before), 'scientific_digest': scientific_digest(self.record),
                      'author_id': 'fixture-author', 'reviewer': 'independent-fixture', 'audit_id': 'audit-1'}

    @staticmethod
    def dump(value):
        return json.dumps(value).encode()

    def test_reviewed_metadata_and_format_only_reuse(self):
        after = copy.deepcopy(self.record)
        after['revision'] = 2
        after['quality']['reviewer'] = 'second'
        after['updated_at'] = '2026-09-26'
        self.assertEqual(verify_reuse(self.before, self.dump(after), self.audit)['reused_audit_id'], 'audit-1')

    def test_unknown_or_scientific_fields_reaudit(self):
        mutations = [lambda r: r['recipe']['temperature'].update(value=301),
                     lambda r: r['recipe']['temperature'].update(unit='K'),
                     lambda r: r['outcome'].update(sample_id='B'),
                     lambda r: r['evidence'][0].update(figure='2b'),
                     lambda r: r.update(training_eligible=True),
                     lambda r: r['quality'].update(review_status='unreviewed'),
                     lambda r: r.update(new_claim='rods'),
                     lambda r: r['recipe'].update(revision='not metadata here')]
        for change in mutations:
            after = copy.deepcopy(self.record)
            change(after)
            with self.subTest(after=after), self.assertRaisesRegex(AuditBindingError, 'Scientific content changed'):
                verify_reuse(self.before, self.dump(after), self.audit)

    def test_array_order_and_source_locators_bound(self):
        after = copy.deepcopy(self.record)
        after['evidence'].append({'page': 4, 'figure': '3'})
        with self.assertRaises(AuditBindingError):
            verify_reuse(self.before, self.dump(after), self.audit)

    def test_audit_tampering_or_mismatched_base_rejected(self):
        for key, value in [('status', 'draft'), ('digest_policy_sha256', '0' * 64),
                           ('reviewed_record_sha256', '0' * 64), ('scientific_digest', '0' * 64)]:
            audit = {**self.audit, key: value}
            with self.subTest(key=key), self.assertRaises(AuditBindingError):
                verify_reuse(self.before, self.before, audit)

    def test_refresh_changes_only_machine_digest(self):
        after = {**self.record, 'revision': 2}
        bindings = {'sourceRecordSha256': {'sample-a': raw_sha(self.before), 'sample-b': 'other'},
                    'recordBindings': {'sample-a': {'precursor': 'cadmium-acetate'}}, 'notes': ['unchanged']}
        result, receipt = refresh_chemical_digest(bindings, self.before, self.dump(after), self.audit)
        self.assertEqual(result['sourceRecordSha256']['sample-a'], raw_sha(self.dump(after)))
        result['sourceRecordSha256']['sample-a'] = raw_sha(self.before)
        self.assertEqual(result, bindings)
        self.assertFalse(receipt['public_delivery_approved'])

    def test_refresh_rejects_existing_stale_or_unbound_mapping(self):
        with self.assertRaises(AuditBindingError):
            refresh_chemical_digest({'sourceRecordSha256': {'sample-a': 'wrong'}}, self.before, self.before, self.audit)

    def test_nonfinite_json_rejected(self):
        with self.assertRaises(AuditBindingError):
            scientific_digest({'record_id': 'sample-a', 'amount': float('nan')})

    def test_audit_author_and_reviewer_must_be_named_and_distinct(self):
        for author in (None, '', 'independent-fixture'):
            with self.subTest(author=author), self.assertRaises(AuditBindingError):
                verify_reuse(self.before, self.before, {**self.audit, 'author_id': author})


if __name__ == '__main__':
    unittest.main()
