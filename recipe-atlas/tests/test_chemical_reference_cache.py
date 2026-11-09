"""H viewer exports must be reachable through fresh entry/dependency URLs."""
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
H_VERSION='0.43.0'
READER_VERSION='0.45.0'
K_PATCH_VERSION='0.45.2'
L_MODULES=('chemical-reference-route.mjs', 'chemical-viewer.mjs', 'crystal-viewer.mjs', 'evans2010-products.mjs', 'illustrated-record.mjs', 'material-guide.mjs', 'material-hub.mjs', 'protocol-references.mjs', 'protocol-visuals.mjs', 'reader-app.mjs', 'reader-structures.mjs')
ENTRY_VERSION='0.48.0'
L_VERSION='0.46.0'
M_MODULES=('illustrated-record.mjs', 'material-guide.mjs', 'material-hub.mjs', 'reader-app.mjs', 'reader.css')
PATCH_MODULES=('illustrated-record.mjs', 'material-guide.mjs', 'material-hub.mjs', 'protocol-visuals.mjs', 'reader-app.mjs', 'reported-protocol-scenes.mjs')
READER_MODULES={'illustrated-record.mjs', 'crystal-defaults.mjs', 'chemical-viewer.mjs', 'crystal-viewer.mjs', 'material-guide.mjs', 'source-field-copy.mjs', 'protocol-record-fit.mjs', 'material-hub.mjs', 'reader-structures.mjs', 'reader-particle.mjs', 'reported-protocol-scenes.mjs', 'protocol-visuals.mjs', 'reader-app.mjs', 'protocol-references.mjs', 'evans2010-products.mjs', 'reported-scene-drawing.mjs'}

N_VERSION='0.48.0'
N_MODULES=('chemical-viewer.mjs', 'crystal-viewer.mjs', 'evans2010-products.mjs', 'illustrated-record.mjs', 'material-guide.mjs', 'material-hub.mjs', 'paper-app.mjs', 'paper-review.mjs', 'particle-shapes.mjs', 'protocol-modules.mjs', 'protocol-references.mjs', 'protocol-visuals.mjs', 'reader-app.mjs', 'reader-figure-morphology.mjs', 'reader-particle.mjs', 'reader-scoped-product-art.mjs', 'reader-structures.mjs', 'williamson2021-protocol.mjs')
def version_for(name):return N_VERSION if name in N_MODULES else '0.47.1' if name == 'reader.css' else ENTRY_VERSION if name in M_MODULES else L_VERSION if name in L_MODULES else K_PATCH_VERSION if name in PATCH_MODULES else READER_VERSION if name in READER_MODULES else H_VERSION


class ChemicalReferenceCacheTests(unittest.TestCase):
    def read(self,name):return(ROOT/name).read_text(encoding='utf-8')
    def viewer_url(self,code):
        urls=re.findall(r'''['"](\./chemical-viewer\.mjs(?:\?[^'"\r\n]*)?)['"]''',code)
        self.assertTrue(urls)
        for url in urls:self.assertEqual(url,'./chemical-viewer.mjs?v='+version_for('chemical-viewer.mjs'))
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
        self.assertIn('reader-app.mjs?v='+ENTRY_VERSION,self.read('templates/material-reader.html'))
        self.assertIn('../illustrated-record.mjs?v='+ENTRY_VERSION,self.read('scripts/build_dataset.py'))
        for name in('murray-1993-method-1-evidence.html','murray-1993-method-2-evidence.html'):
            with self.subTest(name=name):self.assertIn('material-app.mjs?v='+H_VERSION,self.read('static/'+name))
    def test_changed_reverse_dependency_chain_is_consistently_refreshed(self):
        for parent,child in [('illustrated-record.mjs','reader-app.mjs'),('illustrated-record.mjs','material-guide.mjs'),('material-hub.mjs','material-guide.mjs'),('material-guide.mjs','crystal-viewer.mjs'),('protocol-visuals.mjs','protocol-references.mjs'),('crystal-viewer.mjs','evans2010-products.mjs'),('reader-app.mjs','reader-structures.mjs'),('chemical-viewer.mjs','reader-structures.mjs')]:
            with self.subTest(parent=parent,child=child):self.assertIn(child+'?v='+version_for(child),self.read('static/'+parent))


    def test_L_own_identity_route_is_reachable_beyond_stale_cached_route(self):
        code=self.read('static/chemical-viewer.mjs')
        urls=re.findall(r"['\"](\./chemical-reference-route\.mjs(?:\?[^'\"\r\n]*)?)['\"]",code)
        self.assertEqual(urls,['./chemical-reference-route.mjs?v='+version_for('chemical-reference-route.mjs')])
        self.assertNotIn(urls[0],{'./chemical-reference-route.mjs','./chemical-reference-route.mjs?v=0.43.0'})


if __name__=='__main__':unittest.main()
