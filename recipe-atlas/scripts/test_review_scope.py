"""Regression checks against silently promoting main-only reading to main + SI."""
import unittest
from review_scope import MAIN_ONLY, MAIN_SI, SI_ONLY, source_review_scope, pending_variants, pending_variants_html


class ReviewScopeTests(unittest.TestCase):
    def test_pending_variants_are_explicit_located_scope_metadata(self):
        import copy
        row={'id':'variant-b','label':'Synthetic <variant> B','source_locators':['Main PDF p.2, Table 1']}
        scope={'pending_variants':[row]};before=copy.deepcopy(scope)
        self.assertEqual(pending_variants(scope),[row]);self.assertEqual(scope,before)
        self.assertIn('other variants pending',pending_variants_html(scope))
        self.assertIn('&lt;variant&gt;',pending_variants_html(scope))
        self.assertEqual(pending_variants({'remaining_gaps':['Variants not extracted']}),[])
        for bad in [dict(row,source_locators=[]),dict(row,training_ready=True),dict(row,source_locators=['C:/private/source.pdf'])]:
            with self.assertRaises(ValueError):pending_variants({'pending_variants':[bad]})

    def test_main_only_stays_si_unverified(self):
        result = source_review_scope({'review_scope':MAIN_ONLY,'documents':[{'role':'main'}]})
        self.assertEqual(result['review_status'],'main_only_reviewed')
        self.assertEqual(result['si_status'],'not_located_or_verified')
        self.assertIn('SI unverified',result['label'])

    def test_missing_si_cannot_claim_matched_review(self):
        with self.assertRaisesRegex(ValueError,'requires a reviewed SI'):
            source_review_scope({'review_scope':MAIN_SI,'documents':[{'role':'main'}]})

    def test_explicit_scope_required(self):
        with self.assertRaisesRegex(ValueError,'Explicit recognized'):
            source_review_scope({'documents':[{'role':'main'},{'role':'si'}]})

    def test_document_scope_contradictions_rejected(self):
        for roles in [['main','si'],['si'],[]]:
            with self.subTest(roles=roles),self.assertRaises(ValueError):
                source_review_scope({'review_scope':MAIN_ONLY,'documents':[{'role':r} for r in roles]})

    def test_standalone_si_never_claims_main_reading(self):
        result=source_review_scope({'review_scope':SI_ONLY,'documents':[{'role':'si'}]})
        self.assertEqual(result['review_status'],'si_only_reviewed')
        self.assertEqual(result['main_status'],'not_located_or_verified')
        self.assertEqual(result['si_status'],'reviewed_standalone_main_unverified')
        self.assertIn('main unverified',result['label'])

    def test_si_only_rejects_missing_si_main_and_unknown_document(self):
        for roles in [[],['main'],['main','si'],['unknown'],['si','unknown']]:
            with self.subTest(roles=roles),self.assertRaisesRegex(ValueError,'SI-only scope'):
                source_review_scope({'review_scope':SI_ONLY,'documents':[{'role':r} for r in roles]})

    def test_main_scopes_reject_unknown_roles(self):
        for scope,roles in [(MAIN_ONLY,['main','unknown']),(MAIN_SI,['main','si','unknown']),(MAIN_ONLY,['main','supporting_information']),(MAIN_SI,['main','supporting_information'])]:
            with self.subTest(scope=scope,roles=roles),self.assertRaises(ValueError):
                source_review_scope({'review_scope':scope,'documents':[{'role':r} for r in roles]})

    def test_matched_scope_preserved(self):
        result=source_review_scope({'review_scope':MAIN_SI,'documents':[{'role':'main'},{'role':'si'}]})
        self.assertEqual(result['review_status'],'full_documents_reviewed')
        self.assertEqual(result['si_status'],'matched_and_reviewed')


if __name__=='__main__':unittest.main()
