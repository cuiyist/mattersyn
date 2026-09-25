"""Prevent a source-level gallery from masking missing browser-facing figures."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_reader_metadata import validate_reader_view


class ReaderRenderContractTests(unittest.TestCase):
    def test_source_gallery_does_not_replace_record_figures(self):
        with self.assertRaisesRegex(ValueError,'per-record figure list'):
            validate_reader_view('example',{'scopeLabel':'Main article only',
                'figures_by_source':{'source':[{'id':'figure-1'}]}})

    def test_id_references_do_not_render_as_figure_objects(self):
        with self.assertRaisesRegex(ValueError,'complete objects'):
            validate_reader_view('example',{'scopeLabel':'Reported source context',
                'figures':['figure-1']})

    def test_explicit_no_assigned_figure_is_valid(self):
        validate_reader_view('example',{'scopeLabel':'No figure assigned to this procedure',
            'figures':[]})

    def test_visible_scope_is_required(self):
        with self.assertRaisesRegex(ValueError,'visible source/sample scope'):
            validate_reader_view('example',{'figures':[]})


if __name__=='__main__':unittest.main()
