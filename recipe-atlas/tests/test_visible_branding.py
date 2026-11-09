"""Focused current-display branding checks; no build or record/paper reads."""
import ast
import copy
import html
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import unittest
import urllib.parse
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
BRAND='NanoXtalSyn'
TAGLINE='Nanocrystal synthesis atlas'
HTML_FILES=['static/index.html','static/library.html','static/paper.html',
            'static/progress.html','static/alivisatos-2000-evidence.html',
            'static/nakonechnyi-2017-evidence.html','static/murray-1993-method-1-evidence.html',
            'static/murray-1993-method-2-evidence.html','templates/material-reader.html']


class Head(HTMLParser):
    def __init__(self):super().__init__();self.icons=[];self.in_head=False;self.in_title=False;self.title=''
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='head':self.in_head=True
        if tag=='title'and self.in_head:self.in_title=True
        if tag=='link'and a.get('rel')=='icon':self.icons.append(a.get('href'))
    def handle_endtag(self,tag):
        if tag=='title':self.in_title=False
        if tag=='head':self.in_head=False
    def handle_data(self,data):
        if self.in_title:self.title+=data


def functions(path,names):
    tree=ast.parse(path.read_text(encoding='utf-8'))
    module=ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name in names],type_ignores=[])
    values={'html':html};exec(compile(module,str(path),'exec'),values)
    return values


class VisibleBrandingTests(unittest.TestCase):
    def assertNIcon(self,markup):
        h=Head();h.feed(markup);self.assertEqual(len(h.icons),1)
        self.assertTrue(h.icons[0].startswith('data:image/svg+xml,'))
        svg=ET.fromstring(urllib.parse.unquote(h.icons[0].split(',',1)[1]))
        self.assertEqual(svg.find('{http://www.w3.org/2000/svg}text').text,'N')
        return h

    def test_current_page_titles_and_lettermark_are_consistent(self):
        for relative in HTML_FILES:
            with self.subTest(path=relative):
                raw=(ROOT/relative).read_text(encoding='utf-8');h=self.assertNIcon(raw)
                self.assertIn(BRAND,h.title)
                self.assertNotIn('MatterSyn',raw)
                self.assertIn('<span class="brand-mark">N</span>',raw)

    def test_tagline_and_current_social_addresses(self):
        home=(ROOT/'static/index.html').read_text(encoding='utf-8')
        self.assertIn(TAGLINE,home);self.assertIn(TAGLINE.upper(),home)
        for relative in ['static/alivisatos-2000-evidence.html','static/nakonechnyi-2017-evidence.html']:
            self.assertIn(TAGLINE,(ROOT/relative).read_text(encoding='utf-8'))
        for relative in HTML_FILES:
            text=(ROOT/relative).read_text(encoding='utf-8')
            self.assertNotIn('https://cuiyist.github.io/mattersyn-site/',text)
        evidence=(ROOT/'static/murray-1993-method-1-evidence.html').read_text(encoding='utf-8')
        self.assertIn('https://cuiyist.github.io/nanoxtalsyn-site/og.png',evidence)

    def test_data_generator_head_header_and_escaping(self):
        f=functions(ROOT/'scripts/build_dataset.py',{'esc','head','header'})
        head=f['head']('<sample>','../');h=self.assertNIcon(head)
        self.assertEqual(h.title,'<sample> · '+BRAND)
        self.assertIn('&lt;sample&gt;',head)
        self.assertIn('<span class="brand-mark">N</span>'+BRAND,f['header']('../'))

    def test_reader_shell_uses_new_display_and_retains_script_contract(self):
        f=functions(ROOT/'scripts/build_reader_views.py',{'shell'})
        value=f['shell']('Material','<p>Unchanged body</p>','material-hub.mjs')
        h=self.assertNIcon(value);self.assertEqual(h.title,'Material · '+BRAND)
        self.assertIn('<p>Unchanged body</p>',value)
        self.assertIn('material-hub.mjs?v=0.48.0',value)

    def test_review_scope_display_changes_no_record_value(self):
        path=ROOT/'scripts/build_dataset.py';tree=ast.parse(path.read_text(encoding='utf-8'))
        render=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='render_record')
        expr=next(x for x in ast.walk(render)if isinstance(x,ast.Call)and isinstance(x.func,ast.Attribute)
                  and x.func.attr=='replace'and ast.unparse(x.func.value)=="r['quality']['review_scope']")
        record={'quality':{'review_scope':'MatterSyn source-linked scope; missing fields retained.'}}
        before=copy.deepcopy(record);serialized=json.dumps(record,sort_keys=True)
        result=eval(compile(ast.Expression(expr),str(path),'eval'),{'r':record})
        self.assertEqual(result,'NanoXtalSyn source-linked scope; missing fields retained.')
        self.assertEqual(record,before);self.assertEqual(json.dumps(record,sort_keys=True),serialized)

    def test_schema_title_changes_but_identity_does_not(self):
        path=ROOT/'scripts/schema_definition.py';spec=importlib.util.spec_from_file_location('branding_schema',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        self.assertEqual(module.SCHEMA['title'],'NanoXtalSyn source-linked synthesis record')
        self.assertEqual(module.SCHEMA['$id'],'https://mattersyn-recipe-atlas.cuiy781513.chatgpt.site/data/record.schema.json')
        self.assertEqual(module.SCHEMA['$schema'],'https://json-schema.org/draft/2020-12/schema')

    def test_current_dynamic_titles_and_authored_caption_brand(self):
        for name in ['reader-app.mjs','material-hub.mjs','paper-app.mjs','paper-review.mjs']:
            text=(ROOT/'static'/name).read_text(encoding='utf-8')
            self.assertIn('NanoXtalSyn',text);self.assertNotIn('MatterSyn',text)
        text=(ROOT/'static/williamson2021-protocol.mjs').read_text(encoding='utf-8')
        self.assertIn('Shared NanoXtalSyn operation illustration',text)


if __name__=='__main__':unittest.main()
