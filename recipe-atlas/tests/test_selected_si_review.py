"""Partial SI coverage stays explicit and cannot inherit complete-document credit."""
import copy,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from review_scope import MAIN_SI,MAIN_SELECTED_SI,source_review_scope,reviewed_page_count

def fixture():
 def doc(role,count,chosen):
  x={'role':role,'page_count':count,'sha256':'a'*64,'pages':[{'page':n,'text_read':n in chosen,'visual_review':n in chosen} for n in range(1,count+1)]}
  if role=='si':x['pages_read']=chosen
  return x
 return {'review_scope':MAIN_SELECTED_SI,'documents':[doc('main',2,[1,2]),doc('si',5,[1,3])],'figures':[],'recipe_inventory':[]}

class SelectedSIReview(unittest.TestCase):
 def test_selected_counts_only_reviewed_pages(self):
  c=fixture();before=copy.deepcopy(c);self.assertEqual(reviewed_page_count(c),4);self.assertEqual(c,before)
  result=source_review_scope(c);self.assertEqual(result['si_status'],'partially_reviewed');self.assertIn('remaining SI unreviewed',result['label'])
 def test_unread_main_rejected(self):
  c=fixture();c['documents'][0]['pages'][0].update(text_read=False,visual_review=False)
  with self.assertRaisesRegex(ValueError,'Unread'):reviewed_page_count(c)
 def test_duplicate_or_missing_si_inventory_rejected(self):
  for change in ('missing','duplicate','outside','boolean'):
   c=fixture();p=c['documents'][1]['pages']
   if change=='missing':p.pop()
   elif change=='duplicate':p[-1]=copy.deepcopy(p[0])
   elif change=='outside':p[-1]['page']=6
   else:p[0]['page']=True
   with self.subTest(change=change),self.assertRaisesRegex(ValueError,'inventory'):reviewed_page_count(c)
 def test_selected_numbers_reject_empty_duplicate_outside_or_full(self):
  for chosen in ([],[1,1],[1,6],[True,3],[3,1],[1,2,3,4,5]):
   c=fixture();c['documents'][1]['pages_read']=chosen
   with self.subTest(chosen=chosen),self.assertRaisesRegex(ValueError,'proper subset'):reviewed_page_count(c)
 def test_flags_must_match_selected_exactly(self):
  for flags in ({'text_read':True,'visual_review':False},{'text_read':False,'visual_review':False},{'text_read':1,'visual_review':True}):
   c=fixture();c['documents'][1]['pages'][0].update(flags)
   with self.subTest(flags=flags),self.assertRaises(ValueError):reviewed_page_count(c)
 def test_unselected_page_cannot_claim_reading(self):
  c=fixture();c['documents'][1]['pages'][1].update(text_read=True,visual_review=True)
  with self.assertRaisesRegex(ValueError,'declared'):reviewed_page_count(c)
 def test_partial_cannot_claim_full_scope(self):
  c=fixture();c['review_scope']=MAIN_SI
  with self.assertRaisesRegex(ValueError,'Unread'):reviewed_page_count(c)
 def test_selected_requires_one_main_one_si(self):
  for roles in (['si'],['main'],['main','si','si'],['main','unknown']):
   c=fixture();c['documents']=[{'role':r} for r in roles]
   with self.subTest(roles=roles),self.assertRaises(ValueError):source_review_scope(c)
 def test_full_existing_scope_retains_all_pages(self):
  c=fixture();c['review_scope']=MAIN_SI
  for p in c['documents'][1]['pages']:p.update(text_read=True,visual_review=True)
  del c['documents'][1]['pages_read'];self.assertEqual(reviewed_page_count(c),7)
 def test_inventory_requires_full_main_and_partial_si_flags(self):
  c={'review_scope':MAIN_SELECTED_SI,'documents':[{'role':'main','page_count':2,'all_text_read':True,'all_visually_reviewed':True},{'role':'si','page_count':5,'pages_read':[1,3],'all_text_read':False,'all_visually_reviewed':False}]}
  self.assertEqual(reviewed_page_count(c,inventory=True),4)
  for doc,key in ((0,'all_text_read'),(0,'all_visually_reviewed'),(1,'all_text_read'),(1,'all_visually_reviewed')):
   x=copy.deepcopy(c);x['documents'][doc][key]=not x['documents'][doc][key]
   with self.subTest(doc=doc,key=key),self.assertRaises(ValueError):reviewed_page_count(x,inventory=True)
 def test_paper_validator_keeps_unread_main_and_asset_guards(self):
  import build_paper_reviews as b
  c=fixture();self.assertEqual(b.validate(c),[])
  c['documents'][0]['pages'][0]['text_read']=False;self.assertTrue(b.validate(c))
  c=fixture();c['figures']=[{'id':'missing','public_asset':'missing.png','public_asset_sha256':'a'*64}];self.assertTrue(any('hash mismatch' in e for e in b.validate(c)))
 def test_derive_inventory_uses_separate_scope_and_exact_selected_pages(self):
  from test_derive_inventory import fixture as inventory_fixture
  from derive_inventory import derive
  data=inventory_fixture();p=data['seed']['per_paper'][0];p['review_status']='full_main_and_selected_si_independently_reviewed'
  p['documents']=[{'role':'main','page_count':4,'all_text_read':True,'all_visually_reviewed':True},{'role':'si','page_count':5,'pages_read':[1,3],'all_text_read':False,'all_visually_reviewed':False}]
  data['reviews'][0].update(review_scope=MAIN_SELECTED_SI,pages_read=6,selected_si_pages=[1,3]);r=derive(**data)
  self.assertEqual(r['summary']['formal_full_main_and_matched_si_reviews'],0);self.assertEqual(r['summary']['formal_main_and_selected_si_reviews'],1);self.assertEqual(r['summary']['formal_main_and_selected_si_review_pages'],6)
  for field,value in (('pages_read',9),('selected_si_pages',[1,2]),('selected_si_pages',[1,1]),('review_scope',MAIN_SI)):
   x=copy.deepcopy(data);x['reviews'][0][field]=value
   with self.subTest(field=field,value=value),self.assertRaises(ValueError):derive(**x)
if __name__=='__main__':unittest.main()

