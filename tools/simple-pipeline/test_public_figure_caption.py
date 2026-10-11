"""Public caption plumbing never falls back to private raw caption/quote fields."""
import importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('caption_converter_fixture',Path(__file__).with_name('to_site.py'))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class PublicFigureCaption(unittest.TestCase):
    def test_only_explicit_public_caption_is_projected(self):
        source={'public_caption':' Public paraphrase ', 'caption':'PRIVATE SOURCE CAPTION','quote':'PRIVATE QUOTE','other':'PRIVATE'}
        self.assertEqual({'public_caption':'Public paraphrase'},module.public_figure_caption(source))
        self.assertEqual('PRIVATE SOURCE CAPTION',source['caption'])
    def test_missing_malformed_or_blank_caption_never_uses_private_fallback(self):
        for candidate in [None,{'quote':'PRIVATE'},[],42,'  ']:
            self.assertEqual({},module.public_figure_caption({'public_caption':candidate,'caption':'PRIVATE','quote':'PRIVATE'}))

if __name__=='__main__':unittest.main()
