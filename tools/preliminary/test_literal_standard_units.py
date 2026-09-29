"""Synthetic literal-unit regression fixtures; no scientific acceptance."""
import unittest
import preliminary as p
from test_preliminary import entry, evidence


class LiteralStandardUnits(unittest.TestCase):
    def check(self, reported, quote):
        e = entry()
        e['operations'][1]['conditions'][0] = {
            'parameter': 'Synthetic measured quantity', 'reported': reported}
        ev, texts = evidence(e)
        claim = next(c for c in ev['claims']
                     if c['pointer'] == '/operations/1/conditions/0/reported')
        claim['quote'] = quote
        texts[1] += ' ' + p.norm(quote)
        p.validate_claims(e, ev, texts)

    def rejects(self, pairs):
        for reported, quote in pairs:
            with self.subTest(reported=reported, quote=quote), self.assertRaises(ValueError):
                self.check(reported, quote)

    def test_exact_new_unit_spellings(self):
        for unit in ['GPa', 'torr', 'Å']:
            with self.subTest(unit=unit):
                self.assertIsNotNone(p.UNITS.fullmatch(unit))
                self.assertEqual({('', '2.5', unit)}, p.quantity_spans('2.5 ' + unit))
                self.check('2.5 ' + unit, 'The measured quantity was 2.5 ' + unit + '.')

    def test_literal_attached_units(self):
        for value in ['2.5GPa', '3torr', '2.87Å']:
            with self.subTest(value=value):
                self.check(value, 'The measured quantity was ' + value + '.')

    def test_literal_degree_mixed_source_notation(self):
        self.assertIsNotNone(p.UNITS.fullmatch('°'))
        self.assertEqual(['°C'], p.UNITS.findall('80°C'))
        self.assertEqual(['°', '°C'], p.UNITS.findall('80°–150°C'))
        self.assertEqual([], p.UNITS.findall('80 ° C'))
        self.assertEqual(['°'], p.UNITS.findall('80 ° Case'))
        self.check('80°–150°C', 'The reported range was 80°–150°C.')
        self.check('80°', 'The literal reported value was 80°.')
        self.check('< 80°', 'The literal reported value was < 80°.')

    def test_degree_does_not_imply_celsius_or_other_unit(self):
        self.rejects([('80°', 'Value 80°C.'),
                      ('80°C', 'Value 80°.'),
                      ('80°–150°C', 'Range 80°C–150°C.'),
                      ('80°C–150°C', 'Range 80°–150°C.'),
                      ('80°–150°C', 'Range 80°–150°.'),
                      ('80°–150°', 'Range 80°–150°C.')])

    def test_degree_does_not_drop_spaced_scale_letter(self):
        for letter in ['F', 'K', 'R', 'C', 'f', 'X']:
            with self.subTest(letter=letter), self.assertRaises(ValueError):
                self.check('80°', 'The source reports 80° ' + letter + '.')
        self.assertEqual(['°'], p.UNITS.findall('80° Case'))

    def test_degree_mixed_range_wrong_endpoints_and_disconnected_units(self):
        self.rejects([('80°–150°C', 'Range 90°–150°C.'),
                      ('80°–150°C', 'Range 80°–160°C.'),
                      ('80°–150°C', 'Values 80 Pa and 90°; 150 K and 160°C.'),
                      ('80°–150°C', 'Values 80°C and 150°.'),
                      ('80°', 'Value .80°.'),
                      ('80°', 'Value −80°.'),
                      ('80°', 'Value < 80°.')])

    def test_same_spelling_sign_qualifier_and_range(self):
        for value in ['< 2 GPa', '≥ 3 torr', '~ 2.87 Å', '−1 GPa', '+2 torr',
                      '.5 Å', '2–3 GPa', '2 to 3 torr', '2 ± 1 Å', '3e-6 torr']:
            with self.subTest(value=value):
                self.check(value, 'The measured quantity was ' + value + '.')

    def test_different_units_are_not_equivalent(self):
        self.rejects([
            ('2 GPa', 'Pressure 2 MPa.'), ('2 MPa', 'Pressure 2 GPa.'),
            ('2 torr', 'Pressure 2 Pa.'), ('2 Pa', 'Pressure 2 torr.'),
            ('2 Å', 'Current 2 A.'), ('2 A', 'Length 2 Å.'),
            ('1 GPa', 'Pressure 1000 MPa.'),
            ('1 torr', 'Pressure 133.322 Pa.'),
            ('1 Å', 'Length 0.1 nm.')])

    def test_no_unit_case_alias_or_name_expansion(self):
        for wrong in ['gpa', 'GPA', 'Torr', 'TORR', 'å', 'angstrom', 'Angstrom']:
            with self.subTest(unit=wrong):
                self.assertIsNone(p.UNITS.fullmatch(wrong))
                with self.assertRaises(ValueError):
                    self.check('2 ' + wrong, 'The quantity was 2 ' + wrong + '.')
        self.rejects([('2 GPa', 'Pressure 2 gpa.'),
                      ('2 torr', 'Pressure 2 Torr.'),
                      ('2 Å', 'Length 2 angstrom.')])

    def test_wrong_magnitude_and_decimal_suffix_rejected(self):
        for unit in ['GPa', 'torr', 'Å']:
            self.rejects([('2 ' + unit, 'Quantity 20 ' + unit + '.'),
                          ('2 ' + unit, 'Quantity .2 ' + unit + '.'),
                          ('2 ' + unit, 'Quantity 3 ' + unit + '.')])

    def test_disconnected_number_unit_tokens_do_not_support_quantity(self):
        self.rejects([
            ('2 GPa', 'The first pressure is 2 MPa and the second is 10 GPa.'),
            ('2 torr', 'The first pressure is 2 Pa and the second is 10 torr.'),
            ('2 Å', 'The current is 2 A and the length is 10 Å.'),
            ('2 GPa', 'A value of 2 was recorded. Another value was 10 GPa.'),
            ('2 torr', 'A value of 2 was recorded. Another value was 10 torr.'),
            ('2 Å', 'A value of 2 was recorded. Another value was 10 Å.')])

    def test_qualifiers_and_signs_cannot_be_changed(self):
        for unit in ['GPa', 'torr', 'Å']:
            self.rejects([('2 ' + unit, 'Quantity < 2 ' + unit + '.'),
                          ('< 2 ' + unit, 'Quantity 2 ' + unit + '.'),
                          ('> 2 ' + unit, 'Quantity < 2 ' + unit + '.'),
                          ('~ 2 ' + unit, 'Quantity 2 ' + unit + '.'),
                          ('2 ' + unit, 'Quantity −2 ' + unit + '.'),
                          ('−2 ' + unit, 'Quantity +2 ' + unit + '.')])

    def test_known_unit_token_cannot_be_dropped(self):
        for value in ['2 GPa', '2 torr', '2 Å']:
            e = entry()
            e['operations'][1]['conditions'][0]['reported'] = value
            ev, texts = evidence(e)
            claim = next(c for c in ev['claims']
                         if c['pointer'] == '/operations/1/conditions/0/reported')
            claim['value_tokens'] = ['2']
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'coverage'):
                p.validate_claims(e, ev, texts)

    def test_unrelated_typography_and_unknown_units_remain_held(self):
        self.rejects([('0.7 µm', 'A 0.7- µm-thick film.'),
                      ('20 kg/cm²', 'Pressure 20 kg/cm 2.'),
                      ('2 sccm', 'Flow 2 sccm.'),
                      ('2 mTorr', 'Pressure 2 mTorr.')])

    def test_raw_source_quote_anchor_remains_exact(self):
        e = entry()
        e['operations'][1]['conditions'][0]['reported'] = '2 GPa'
        ev, texts = evidence(e)
        texts[1] = texts[1].replace('2 GPa', '2 MPa')
        with self.assertRaisesRegex(ValueError, 'unmatched exact'):
            p.validate_claims(e, ev, texts)


if __name__ == '__main__':
    unittest.main()
