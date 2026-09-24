import copy,re,unittest
from source_link_artifacts import project_display_json

class DisplayProjectionTests(unittest.TestCase):
    def setUp(self):
        self.row={'original_path':'assets/figure.png','original_sha256':'a'*64,'display_path':'assets/source-links/card.svg','display_sha256':'b'*64,'source_url':'https://doi.org/10.1000/example','display_note':'Source link; not measured data.'}
        self.lookup={self.row['original_path']:self.row};self.pattern=re.compile(re.escape(self.row['original_path']));self.replacements={self.row['original_path']:self.row['display_path']}
    def apply(self,d):
        private=[];out=project_display_json(copy.deepcopy(d),self.lookup,private,'data/example.json',self.pattern,self.replacements);return out,private
    def test_original_crop_identity_and_facts_are_not_display_identity(self):
        original={'file':'assets/figure.png','sha256':'a'*64,'source_pdf_sha256':'c'*64,'pdf_page':4,'pixel_size':[150,200],'original_published_figure':True}
        d={'original_figure_asset':original,'sample':'sample-2','size_nm':4.2};out,private=self.apply(d)
        self.assertEqual(out['original_figure_asset']['sha256'],'a'*64)
        self.assertEqual(out['original_figure_asset']['source_pdf_sha256'],'c'*64)
        self.assertEqual(out['original_figure_asset']['source_asset_locator'],'assets/figure.png')
        self.assertNotIn('file',out['original_figure_asset'])
        self.assertEqual(out['display_asset']['sha256'],'b'*64)
        self.assertEqual(out['sample'],d['sample']);self.assertEqual(out['size_nm'],d['size_nm'])
        self.assertEqual(private[0]['original'],original)
    def test_public_display_hash_is_distinct_from_source_pdf_and_crop(self):
        d={'public_asset':'assets/figure.png','public_asset_sha256':'a'*64,'source_sha256':'c'*64,'page':2,'summary':'Authored factual summary.'};out,private=self.apply(d)
        self.assertEqual(out['public_asset_sha256'],'b'*64);self.assertEqual(out['source_crop_sha256'],'a'*64);self.assertEqual(out['source_sha256'],'c'*64);self.assertEqual(private[0]['original'],d)
    def test_wrong_original_hash_is_rejected(self):
        for d in [{'original_figure_asset':{'file':'assets/figure.png','sha256':'d'*64}},{'public_asset':'assets/figure.png','public_asset_sha256':'d'*64}]:
            with self.assertRaises(RuntimeError):self.apply(d)
    def test_unrelated_data_remains_unchanged(self):
        d={'temperature':{'value':280,'unit':'C'},'sample':'sample-1','source_sha256':'c'*64};out,private=self.apply(d);self.assertEqual(out,d);self.assertEqual(private,[])
    def test_idempotent_display_projection(self):
        d={'public_asset':'assets/figure.png','public_asset_sha256':'a'*64};once,_=self.apply(d);twice,private=self.apply(once);self.assertEqual(once,twice);self.assertEqual(private,[])

if __name__=='__main__':unittest.main()
