"""Synthetic-only experimental display checks; no real source quotation is included."""
import copy,json,unittest
import experimental as E

def fixture():
    page='Method A was heated at 120 °C for 3 h.'
    claims=[{'recipe_id':'Method A','sample_id':None,'slot_id':'growth-temperature','field':'reaction_temperature','value':120,'unit':'°C','value_text':'120','unit_text':'°C','document_id':'main','page':1,'quote':'heated at 120 °C','link_quote':'Method A was heated','link_page':1,'modality':'explicit_text','technique':None,'chemical_id':None}]
    pages={'documents':{'main':{'source_id':'synthetic-a','document_sha256':'1'*64,'pages':{'1':page}}}}
    draft={'schema':E.silver.VERSION+'/draft','source_id':'synthetic-a','runner':'local','saw_other_draft':False,'pipeline_sha256':'2'*64,'model_sha256':'3'*64,'prompt_sha256':'4'*64,'claims':claims}
    raw=lambda x:json.dumps(x,sort_keys=True).encode()
    psha=E.sha(raw(pages));dsha=E.sha(raw(draft))
    identity={'source_id':'synthetic-a','document_role':'main','page_count':1,'source_sha256':'1'*64,'doi':'10.9999/synthetic-a','url':'https://doi.org/10.9999/synthetic-a','title':'Synthetic material preparation','citation':'Synthetic test fixture; not a real paper.','page_map_sha256':psha}
    receipt={'schema':'mattersyn-local-draft-run/1','external_document_transfer':False,'published':False,'draft_sha256':dsha,'page_map_sha256':psha,'pipeline_sha256':'2'*64,'model_sha256':'3'*64,'claims':1,'model':'synthetic-local'}
    scope={'status':'complete_model_draft_not_reviewed','external_transfer':False,'input_pages':[1],'source_total_pages':1}
    response={'done':True,'done_reason':'stop','model':'synthetic-local','message':{'content':json.dumps({'claims':claims})}}
    return dict(draft=draft,pages=pages,identity=identity,receipt=receipt,scope=scope,response=response,draft_sha256=dsha,pages_sha256=psha)

class ExperimentalTests(unittest.TestCase):
    def test_validator_dependency_pin_is_never_bypassed(self):
        from unittest import mock
        with mock.patch.object(E,'VALIDATOR_SHA','0'*64):
            with self.assertRaisesRegex(ValueError,'Validator dependency changed'):E.project(**fixture())
    def updated(self,args):
        args['receipt']['claims']=len(args['draft']['claims'])
        args['response']['message']['content']=json.dumps({'claims':args['draft']['claims']})
        args['draft_sha256']=E.sha(json.dumps(args['draft'],sort_keys=True).encode());args['receipt']['draft_sha256']=args['draft_sha256']
        return args
    def test_valid_unreviewed_never_training_or_accuracy(self):
        a=fixture();before=copy.deepcopy(a);e,d=E.project(**a);self.assertEqual(a,before)
        self.assertEqual(e['fields'][0]['value'],120);self.assertFalse(e['training_ready']);self.assertIsNone(e['precision']);self.assertIsNone(e['recall']);self.assertEqual(e['training_weight'],0)
        catalog=E.catalog([e]);self.assertEqual(catalog['structure_pair_count_contribution'],0);self.assertEqual(catalog['completed_paper_count_contribution'],0)
        raw=json.dumps(catalog);self.assertNotIn('link_quote',raw);self.assertNotIn('heated at 120',raw)
    def test_quote_and_numeric_unit_mismatch_withheld_not_repaired(self):
        for key,value in [('quote','heated at 125 °C'),('value',125),('unit','K'),('page',2),('recipe_id','invented method')]:
            a=fixture();a['draft']['claims'][0][key]=value;self.updated(a);e,d=E.project(**a)
            self.assertIsNone(e);self.assertEqual(d['withheld'],1)
    def test_duplicate_slot_is_not_cherry_picked(self):
        a=fixture();a['draft']['claims']*=2;self.updated(a);e,d=E.project(**a)
        self.assertIsNone(e);self.assertEqual(d['withheld'],2)
    def test_incomplete_or_edited_model_response_rejected(self):
        for mutation in ['truncated','edit']:
            a=fixture()
            if mutation=='truncated':a['response']['done_reason']='length'
            else:a['response']['message']['content']='{"claims":[]}'
            with self.assertRaises(ValueError):E.project(**a)
    def test_receipt_source_and_pipeline_tamper_rejected(self):
        for target,key in [('receipt','draft_sha256'),('receipt','page_map_sha256'),('receipt','pipeline_sha256'),('identity','source_sha256')]:
            a=fixture();a[target][key]='f'*64
            with self.assertRaises(ValueError):E.project(**a)
    def test_private_paths_bad_doi_url_and_model_claim_extras(self):
        for key,value in [('title','C:/private/source.pdf'),('url','javascript:alert(1)'),('citation','file:' '///secret')]:
            a=fixture();a['identity'][key]=value
            with self.assertRaises(ValueError):E.project(**a)
        a=fixture();a['draft']['claims'][0]['training_ready']=True;self.updated(a);e,d=E.project(**a);self.assertIsNone(e)
    def test_no_substantive_values_and_source_duplicates_rejected(self):
        with self.assertRaises(ValueError):E.catalog([])
        e,_=E.project(**fixture())
        with self.assertRaises(ValueError):E.catalog([e,e])
        e['quote']='private evidence'
        with self.assertRaises(ValueError):E.catalog([e])
    def test_single_source_chunk_origins_and_overlap_validation(self):
        a=fixture();chunk={k:v for k,v in a.items() if k!='identity'}
        e,d=E.project_chunks([chunk],a['pages'],a['identity'],pages_sha256=a['pages_sha256']);self.assertEqual(d['displayed'],1);self.assertEqual(e['extraction']['chunks'],1)
        with self.assertRaises(ValueError):E.project_chunks([chunk,chunk],a['pages'],a['identity'],pages_sha256=a['pages_sha256'])
        chunk=copy.deepcopy(chunk);chunk['pages']['documents']['main']['pages']['1']='Different text'
        with self.assertRaises(ValueError):E.project_chunks([chunk],a['pages'],a['identity'],pages_sha256=a['pages_sha256'])
    def test_extracted_numeric_string_is_not_silently_converted(self):
        a=fixture();a['draft']['claims'][0]['value']='120';self.updated(a);e,d=E.project(**a);self.assertIsNone(e)
    def test_excluded_page_cannot_supply_evidence(self):
        a=fixture();a['identity']['page_count']=2;a['scope']['source_total_pages']=2
        a['pages']['documents']['main']['pages']['2']=a['pages']['documents']['main']['pages']['1'];a['draft']['claims'][0]['page']=2;self.updated(a)
        e,d=E.project(**a);self.assertIsNone(e)

if __name__=='__main__':unittest.main()
