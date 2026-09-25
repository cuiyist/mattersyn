import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from generate_release_metadata import citation

class ReviewCitationIdentity(unittest.TestCase):
    def test_source_and_reader_ids_may_differ(self):
        source={'id':'source-main','title':'A source','year':2014,'doi':'10.0000/example'}
        review={'paper_id':'source','source_group':'source-main','paper':{'authors':['A. Author']}}
        text=citation(source,review)
        self.assertIn('paper-review.html?id=source)',text)
        self.assertNotIn('paper-review.html?id=source-main)',text)
        self.assertIn('A. Author',text)

    def test_legacy_id_and_unreviewed_context_remain_supported(self):
        source={'id':'legacy','title':'Legacy paper','year':2000}
        self.assertIn('paper-review.html?id=legacy)',citation(source,{'paper':{'authors':['Legacy author']}}))
        self.assertNotIn('paper-review.html',citation(source,{}))

if __name__=='__main__':unittest.main()
