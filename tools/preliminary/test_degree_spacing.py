"""Comparison-only degree-C typography; no source text or numeric repair."""
import unittest
import preliminary as p
from test_preliminary import entry, evidence


class DegreeSpacingTests(unittest.TestCase):
    def check(self, reported, quote):
        e = entry()
        e['operations'][1]['conditions'][0] = {'parameter':'Temperature','reported':reported}
        ev, texts = evidence(e)
        c = next(c for c in ev['claims'] if c['pointer'] == '/operations/1/conditions/0/reported')
        c['quote'] = quote
        texts[1] += ' ' + p.norm(quote)
        p.validate_claims(e, ev, texts)

    def test_degree_c_whitespace_only(self):
        for quote in ['Heat at ~150 ° C.', 'Heat at ~150 °   C.', 'Heat at ~150 °\tC.']:
            self.check('~150 °C', quote)
        self.check('150 °C', 'Heat at 150 ° C.')
        self.assertTrue(p._token_in_quote('°C', '150 ° C'))
        self.assertEqual('4 8 nm; 20 kg/cm 2; 150 °C', p.matching_text('4 8 nm; 20 kg/cm 2; 150 ° C'))

    def test_no_conversion_or_kelvin_typography(self):
        for value, quote in [('150 °C','Heat at 423 K.'), ('150 °C','Heat at 150 ° K.'), ('150 K','Heat at 150 ° K.'), ('150 °C','Heat at 302 ° F.'), ('150 °C','Heat at 150 ° Celsius.')]:
            with self.subTest(value=value,quote=quote), self.assertRaises(ValueError):
                self.check(value,quote)

    def test_magnitude_and_association_boundaries_unchanged(self):
        for value, quote in [('48 °C','Heat at 4 8 ° C.'), ('150 °C','Use 150 mL at 30 ° C.'), ('150 °C','Heat at 150 and later at 30 ° C.'), ('15 °C','Heat at 150 ° C.'), ('150 °C','Heat at .150 ° C.')]:
            with self.subTest(value=value,quote=quote), self.assertRaises(ValueError):
                self.check(value,quote)

    def test_qualifier_not_erased_or_word_aliased(self):
        for value, quote in [('150 °C','Heat at ~150 ° C.'), ('~150 °C','Heat at 150 ° C.'), ('approximately 150 °C','Heat at ~150 ° C.')]:
            with self.subTest(value=value,quote=quote), self.assertRaises(ValueError):
                self.check(value,quote)

    def test_raw_quote_anchor_stays_exact(self):
        e=entry();e['operations'][1]['conditions'][0]={'parameter':'Temperature','reported':'150 °C'}
        ev,texts=evidence(e);c=next(c for c in ev['claims'] if c['pointer']=='/operations/1/conditions/0/reported')
        texts[1]=texts[1].replace('150 °C','150 ° C')
        with self.assertRaisesRegex(ValueError,'unmatched exact'):p.validate_claims(e,ev,texts)

    def test_unit_exponent_spacing_remains_held(self):
        self.assertNotEqual(p.quantity_spans('20 kg/cm²'),p.quantity_spans('20 kg/cm 2'))
        with self.assertRaises(ValueError):self.check('20 kg/cm²','Press at 20 kg/cm 2.')


if __name__ == '__main__':unittest.main()
