"""Synthetic static Data-page background tests; no real record or paper reads."""
import copy
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import build_dataset as builder
import reader_background as m
from record_helpers import record, source


class BackgroundNesting(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.parents = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'data-record-background' in attrs:
            self.parents.append(list(self.stack))
        if tag not in {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
                       'link', 'meta', 'param', 'source', 'track', 'wbr'}:
            self.stack.append((tag, attrs.get('id')))

    def handle_endtag(self, tag):
        for index in range(len(self.stack)-1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break


class DataPageBackgroundTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library = m.load_library(ROOT)

    def record(self):
        src = source('synthetic-background-source', '10.0000/synthetic-background',
                     'Synthetic context', 'Test author', 2000)
        result = record('synthetic-background-context', 'Synthetic context', 'ZnO',
                        'test', 'unclassified context', src, 'Synthetic context')
        result['collection'] = 'reviewed_literature'
        result['record_type'] = 'observation'
        result['quality']['review_status'] = 'source_reviewed'
        result['context_links'] = [{'label': 'Existing source context',
                                   'url': 'paper-review.html?id=synthetic-background-source',
                                   'relation': 'source_intuition'}]
        return result

    def meta(self):
        return {'eligibility': {}, 'group_id': 'synthetic', 'split': 'development',
                'record_sha256': 'synthetic-not-a-record-pin'}

    def test_Data_only_context_gets_cards_after_source_and_links_outside_cleared_hosts(self):
        record = self.record()
        before = copy.deepcopy(record)
        page = builder.render_record(record, self.meta(), self.library)
        section = page.split('<section id="intuition"', 1)[1].split('<section id="evidence"', 1)[0]
        block = m.render_record_background(record, self.library)
        self.assertIn(block, section)
        self.assertEqual(page.count('data-record-background'), 1)
        self.assertLess(section.index('id="record-intuition-content"'), section.index(block))
        self.assertLess(section.index('Existing source context'), section.index(block))
        nesting = BackgroundNesting()
        nesting.feed(page)
        self.assertEqual(len(nesting.parents), 1)
        self.assertIn(('section', 'intuition'), nesting.parents[0])
        self.assertNotIn(('div', 'record-intuition-content'), nesting.parents[0])
        self.assertNotIn(('div', 'record-original-evidence'), nesting.parents[0])
        self.assertEqual(record, before)

    def test_exact_label_reference_links_and_no_status_based_background(self):
        record = self.record()
        cards = m.select_background(record, {}, self.library)
        block = m.render_record_background(record, self.library)
        self.assertGreaterEqual(len(cards), 1)
        self.assertLessEqual(len(cards), 3)
        self.assertEqual(unescape(block).count(m.LABEL), len(cards))
        for card in cards:
            self.assertIn('href="'+card['reference']['url']+'"', block)
            self.assertIn('DOI '+card['reference']['doi'], block)
        extracted = copy.deepcopy(record)
        extracted['quality']['review_status'] = 'source_extracted'
        self.assertEqual(block, m.render_record_background(extracted, self.library))

    def test_existing_two_argument_renderer_uses_validated_library(self):
        with patch.object(builder, 'load_library', return_value=self.library) as load:
            page = builder.render_record(self.record(), self.meta())
        load.assert_called_once_with(builder.ROOT)
        self.assertIn('data-record-background', page)

    def test_authored_text_is_escaped_and_Data_classes_are_readable_without_Reader_css(self):
        library = copy.deepcopy(self.library)
        item = next(item for item in library['statements'] if item['id'] == library['fallback'])
        item['title'] = '<img onerror="not-executed"> & title'
        block = m.render_record_background(self.record(), library)
        self.assertNotIn('<img', block)
        self.assertIn('&lt;img', block)
        self.assertIn('intuition-grid', block)
        self.assertIn('class="intuition-card"', block)
        self.assertIn('min-width:0;overflow-wrap:anywhere', block)
        self.assertIn('font-size:13px', block)


if __name__ == '__main__':
    unittest.main()
