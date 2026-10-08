"""Synthetic exact-text regression checks; no real calibration or admission."""
import copy
import unittest
import silver as s
from test_silver import claim, inputs, policy, calibration_data


def text_inputs(field, value):
    a,b,pages,p = inputs()
    span = 'Method A produced sample A: CdSe nanocrystals.'
    c = claim(field,value,None,'sample A')
    c.update(value_text=value,quote=span,link_quote=span)
    pages['documents']['main']['pages']['1'] = span
    a['claims']=[c]; b['claims']=[copy.deepcopy(c)]
    return a,b,pages,p


class CoreTextTests(unittest.TestCase):
    def test_exact_source_text_composition_and_product_statement_agree(self):
        for field,value in [('composition','CdSe'),('product_statement','CdSe nanocrystals')]:
            a,b,pages,p = text_inputs(field,value)
            self.assertEqual(s.validate_claim(a['claims'][0],pages,'paper1',{}),[])
            self.assertEqual(s.reconcile(a,b,pages,p)['claims'][0]['state'],'agreed')

    def test_no_synthesized_text_fuzzy_matching_or_cross_page_quote(self):
        for field in ('composition','product_statement'):
            for change,error in [({'value':'cadmium selenide','value_text':'cadmium selenide'},'value_not_in_quote'),
                                 ({'sample_id':'sample B'},'explicit_sample_link_missing'),
                                 ({'page':2},'quote_page_mismatch'),
                                 ({'value':'x'*121,'value_text':'x'*121},'invalid_text_value'),
                                 ({'unit':'nm'},'invalid_text_value')]:
                a,b,pages,p=text_inputs(field,'CdSe'); a['claims'][0].update(change)
                self.assertIn(error,s.validate_claim(a['claims'][0],pages,'paper1',{}))
                self.assertTrue(s.reconcile(a,b,pages,p)['claims'][0]['training_masked'])
        self.assertFalse(s.equivalent({'value':'CdSe','unit':None},{'value':'cadmium selenide','unit':None}))

    def test_new_field_disagreement_keeps_existing_band_rule(self):
        for band,state in [('high','withheld'),('medium','uncertain'),('low','uncertain')]:
            a,b,pages,p=text_inputs('composition','CdSe'); p=policy(band)
            span='Method A produced sample A: CdSe and ZnS.'
            pages['documents']['main']['pages']['1']=span
            for draft in (a,b): draft['claims'][0].update(quote=span,link_quote=span)
            b['claims'][0].update(value='ZnS',value_text='ZnS')
            row=s.reconcile(a,b,pages,p)['claims'][0]
            self.assertEqual(row['state'],state);self.assertTrue(row['training_masked'])

    def test_each_new_field_is_scored_with_existing_denominators_and_stop(self):
        for field in ('composition','product_statement'):
            truth,pred,p=calibration_data(1)
            for row in truth['records']:
                row.update(field=field,value='CdSe',unit=None,value_text='CdSe',unit_text=None)
            for package in pred:
                row=package['claims'][0]; row['key'][-1]=field
                for alternative in row['alternatives']:
                    alternative.update(field=field,value='CdSe',unit=None,value_text='CdSe',unit_text=None)
            result=s.calibrate(truth,pred,p); metric=result['metrics'][0]
            self.assertEqual(metric['true_positive'],1);self.assertEqual(metric['gold_instances'],1)
            self.assertEqual(metric['status'],'STOP');self.assertFalse(result['publication_enabled'])
            truth['records'][0]['value']='ZnS'
            metric=s.calibrate(truth,pred,p)['metrics'][0]
            self.assertEqual(metric['false_positive'],1);self.assertEqual(metric['false_negative'],1)


if __name__ == '__main__': unittest.main()
