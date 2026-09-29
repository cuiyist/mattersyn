"""Synthetic syntax tests; no scientific or publication acceptance."""
import unittest
import preliminary as p
from shared_unit_lists import coordinated_quantity_spans, MAX_ITEMS


class SharedUnitLists(unittest.TestCase):
    def spans(self, text):
        return coordinated_quantity_spans(p.norm(text), p._LITERAL_UNIT)

    def test_two_decimal_values(self):
        self.assertEqual({('', '13.6', 'nm'), ('', '22.5', 'nm')}, self.spans('13.6 and 22.5 nm'))

    def test_comma_and_oxford_lists(self):
        expected={('', str(n), 'nm') for n in [1,2,3]}
        for text in ['1, 2 and 3 nm', '1, 2, and 3 nm', '1,2,3 nm']:
            with self.subTest(text=text):self.assertEqual(expected,self.spans(text))

    def test_each_qualifier_retained(self):
        self.assertEqual({('~','1','nm'),('>','2','nm'),('≤','3','nm')},self.spans('~1, >2 and ≤3 nm'))

    def test_no_qualifier_inheritance(self):
        self.assertEqual({('~','1','nm'),('','2','nm')},self.spans('~1 and 2 nm'))

    def test_literal_signs_and_exponents(self):
        self.assertEqual({('','−1.2e-3','V'),('','+2.0E3','V')},self.spans('−1.2e-3 and +2.0E3 V'))

    def test_compound_unit_literal_only(self):
        self.assertEqual({('','1','nm/s'),('','2','nm/s')},self.spans('1 and 2 nm / s'))

    def test_maximum_and_oversized_lists(self):
        make=lambda n:', '.join(str(i) for i in range(1,n+1))+' nm'
        self.assertEqual(MAX_ITEMS,len(self.spans(make(MAX_ITEMS))))
        self.assertEqual(set(),self.spans(make(MAX_ITEMS+1)))

    def test_sentence_crossing_and_intervening_words(self):
        for text in ['1. and 2 nm','1; and 2 nm','1 and roughly 2 nm','1, sample 2 and 3 nm','1 and 2. Next 3 nm']:
            with self.subTest(text=text):self.assertEqual(set(),self.spans(text))

    def test_mixed_units_and_partial_tails(self):
        for text in ['1 um and 2 nm','1 nm, 2 and 3 nm','1 and 2 nm and 3 um','1 and 2 nm, 3 nm','1 K, 2 and 3 nm']:
            with self.subTest(text=text):self.assertEqual(set(),self.spans(text))

    def test_digit_joining_and_thousands(self):
        for text in ['1 000 and 2 nm','1,000 and 2 nm','1, 000 and 2 nm','v1 and 2 nm','1.2.3 and 4 nm']:
            with self.subTest(text=text):self.assertEqual(set(),self.spans(text))

    def test_ranges_not_expanded(self):
        for text in ['1–2 and 3 nm','1-2 and 3 nm','1 to 2 and 3 nm','1 ± 2 and 3 nm']:
            with self.subTest(text=text):self.assertEqual(set(),self.spans(text))

    def test_unknown_units_and_other_conjunctions(self):
        for text in ['1 and 2 furlongs','1 or 2 nm','1 versus 2 nm','1 plus 2 nm']:
            with self.subTest(text=text):self.assertEqual(set(),self.spans(text))

    def test_glyph_digit_prefix_remains_uninterpreted(self):
        self.assertEqual(set(),self.spans('/H1101113.6 and 22.5 nm'))

    def test_units_and_qualifiers_cannot_be_changed(self):
        spans=p.quantity_spans('~13.6 and >22.5 nm')
        self.assertIn(('~','13.6','nm'),spans)
        self.assertNotIn(('','13.6','nm'),spans)
        self.assertNotIn(('<','22.5','nm'),spans)
        self.assertNotIn(('~','0.0136','µm'),spans)

    def test_degree_spacing_not_silently_added(self):
        self.assertEqual(set(),self.spans('1 and 2 ° C'))
        self.assertEqual({('','1','°C'),('','2','°C')},self.spans('1 and 2 °C'))

    def test_no_conversion_or_rounding(self):
        spans=self.spans('13.6 and 22.5 nm')
        for unsupported in [('', '0.0136','µm'),('', '14','nm'),('', '13.6','µm')]:
            self.assertNotIn(unsupported,spans)

    def test_existing_standalone_results_preserved(self):
        for text in ['5 nm','~10 nm and 20 nm','5–10 nm','2 h; 3 g; 8 K','1 nm/s','1.0e3 nm']:
            old={(m['qualifier'] or '',p.re.sub(r'\s+','',m['number']),p.re.sub(r'\s+','',m['unit'])) for m in p._QUANTITY.finditer(p.norm(text))}
            self.assertTrue(old.issubset(p.quantity_spans(text)))
        self.assertIn(('', '13.6','nm'),p.quantity_spans('13.6 and 22.5 nm'))

    def test_input_unchanged_and_independent_lists(self):
        text='1 and 2 nm; 3 and 4 K';before=text
        self.assertEqual({('','1','nm'),('','2','nm'),('','3','K'),('','4','K')},self.spans(text))
        self.assertEqual(before,text)


if __name__=='__main__':unittest.main()
