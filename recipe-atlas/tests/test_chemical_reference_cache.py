"""H viewer exports must be reachable through fresh entry/dependency URLs."""
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
H_VERSION='0.43.0'
READER_VERSION='0.44.0'
READER_MODULES={'reader-app.mjs','illustrated-record.mjs','material-guide.mjs','material-hub.mjs','method-families.mjs'}


class ChemicalReferenceCacheTests(unittest.TestCase):
    def read(self,name):return(ROOT/name).read_text(encoding='utf-8')
    def viewer_url(self,code):
        urls=re.findall(r'''['"](\./chemical-viewer\.mjs(?:\?[^'"\r\n]*)?)['"]''',code)
        self.assertTrue(urls)
        for url in urls:self.assertEqual(url,'./chemical-viewer.mjs?v='+H_VERSION)
        return urls[0]
    def test_every_actual_direct_viewer_caller_uses_fresh_H_URL(self):
        for name in('reader-app.mjs','reader-structures.mjs','crystal-viewer.mjs','evans2010-products.mjs','illustrated-record.mjs','material-guide.mjs','protocol-references.mjs'):
            with self.subTest(name=name):self.viewer_url(self.read('static/'+name))
    def test_existing_cached_viewer_without_new_exports_cannot_satisfy_new_import(self):
        old_cache={'./chemical-viewer.mjs?v=0.34.1':{'openChemical'},'./chemical-viewer.mjs?v=0.41.0':{'openChemical'},'./chemical-viewer.mjs?v=0.42.0':{'openChemical'}}
        app=self.read('static/reader-app.mjs');url=self.viewer_url(app);self.assertNotIn(url,old_cache)
        self.assertIn('chemicalButtonLabel',app);self.assertIn('chemicalDisplayCaption',app)
        viewer=self.read('static/chemical-viewer.mjs');self.assertIn('chemicalButtonLabel',viewer);self.assertIn('chemicalDisplayCaption',viewer)
    def test_actual_record_material_and_handmade_entry_URLs_are_fresh(self):
        self.assertIn('reader-app.mjs?v='+READER_VERSION,self.read('templates/material-reader.html'))
        self.assertIn('../illustrated-record.mjs?v='+READER_VERSION,self.read('scripts/build_dataset.py'))
        for name in('murray-1993-method-1-evidence.html','murray-1993-method-2-evidence.html'):
            with self.subTest(name=name):self.assertIn('material-app.mjs?v='+H_VERSION,self.read('static/'+name))
    def test_changed_reverse_dependency_chain_is_consistently_refreshed(self):
        for parent,child in [('illustrated-record.mjs','reader-app.mjs'),('illustrated-record.mjs','material-guide.mjs'),('material-hub.mjs','material-guide.mjs'),('material-guide.mjs','crystal-viewer.mjs'),('protocol-visuals.mjs','protocol-references.mjs'),('crystal-viewer.mjs','evans2010-products.mjs'),('reader-app.mjs','reader-structures.mjs'),('chemical-viewer.mjs','reader-structures.mjs')]:
            with self.subTest(parent=parent,child=child):self.assertIn(child+'?v='+(READER_VERSION if child in READER_MODULES else H_VERSION),self.read('static/'+parent))


if __name__=='__main__':unittest.main()
