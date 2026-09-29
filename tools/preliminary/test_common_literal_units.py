"""Synthetic exact-unit regression fixtures; no scientific acceptance."""
import unittest
import preliminary as p
from test_preliminary import entry, evidence


class CommonLiteralUnits(unittest.TestCase):
    units = ('mTorr', 'slm', 'sccm', 'GHz', 'MHz', 'W', 'mW', 'mA')

    def check(self, reported, quote):
        e = entry()
        e['operations'][1]['conditions'][0] = {
            'parameter': 'Synthetic reported quantity', 'reported': reported}
        ev, texts = evidence(e)
        claim = next(c for c in ev['claims']
                     if c['pointer'] == '/operations/1/conditions/0/reported')
        claim['quote'] = quote
        texts[1] += ' ' + p.norm(quote)
        p.validate_claims(e, ev, texts)

    def rejects(self, reported, quote):
        with self.subTest(reported=reported, quote=quote), self.assertRaises(ValueError):
            self.check(reported, quote)

    def test_exact_spaced_and_attached_units(self):
        for unit in self.units:
            self.assertIsNotNone(p.UNITS.fullmatch(unit))
            for gap in ('', ' '):
                value = '2.5' + gap + unit
                with self.subTest(value=value):
                    self.assertEqual({('', '2.5', unit)}, p.quantity_spans(value))
                    self.check(value, 'The reported quantity was ' + value + '.')

    def test_realistic_compound_current_density(self):
        for value in ('13 mA/cm2', '13mA/cm2', '13 mA/cm²'):
            with self.subTest(value=value):
                self.check(value, 'The current density was ' + value + '.')
        self.assertEqual({('', '13', 'mA/cm2')}, p.quantity_spans('13 mA/cm2'))
        for quote in ('Current density 13 A/cm2.', 'Current density 13 mA/cm3.',
                      'Current 13 mA and area 2 cm2.',
                      'Current density 3 mA/cm2 and current 13 mA.',
                      'Current density 13 mA/cm 2.'):
            self.rejects('13 mA/cm2', quote)

    def test_wrong_units_and_conversions_are_rejected(self):
        for left, right in [('mTorr', 'torr'), ('slm', 'sccm'), ('GHz', 'MHz'),
                            ('W', 'mW'), ('mA', 'A')]:
            self.rejects('2 ' + left, 'Quantity 2 ' + right + '.')
            self.rejects('2 ' + right, 'Quantity 2 ' + left + '.')
        for public, quote in [('1 mTorr', 'Pressure 0.001 torr.'),
                              ('1 slm', 'Flow 1000 sccm.'),
                              ('1 GHz', 'Frequency 1000 MHz.'),
                              ('1 W', 'Power 1000 mW.'),
                              ('1 mA', 'Current 0.001 A.')]:
            self.rejects(public, quote)

    def test_wrong_magnitude_and_decimal_suffix_are_rejected(self):
        for unit in self.units:
            for wrong in ('20', '.2', '3'):
                self.rejects('2 ' + unit, 'Quantity ' + wrong + ' ' + unit + '.')

    def test_disconnected_number_and_unit_are_rejected(self):
        for unit in self.units:
            self.rejects('2 ' + unit, 'A value of 2 was reported. Another is 10 ' + unit + '.')
            self.rejects('2 ' + unit, 'The duration is 2 h and the quantity is 10 ' + unit + '.')

    def test_literal_qualifiers_signs_and_ranges(self):
        for unit in self.units:
            for number in ('< 2', '≥ 2', '~ 2', '−2', '+2', '.2', '2–3', '2 to 3'):
                value = number + ' ' + unit
                with self.subTest(value=value):
                    self.check(value, 'Quantity ' + value + '.')
            for public, quoted in [('2', '< 2'), ('< 2', '2'),
                                   ('~ 2', '2'), ('2', '−2'), ('−2', '+2')]:
                self.rejects(public + ' ' + unit, 'Quantity ' + quoted + ' ' + unit + '.')

    def test_no_case_alias_or_unknown_unit_admission(self):
        for unit in ('mtorr', 'MTorr', 'SLM', 'SCCM', 'ghz', 'mhz', 'w', 'mw',
                     'ma', 'kHz', 'kW', 'uA', 'litres'):
            with self.subTest(unit=unit):
                self.assertIsNone(p.UNITS.fullmatch(unit))
                self.rejects('2 ' + unit, 'Quantity 2 ' + unit + '.')

    def test_unit_token_and_raw_quote_remain_required(self):
        for unit in self.units:
            e = entry()
            e['operations'][1]['conditions'][0]['reported'] = '2 ' + unit
            ev, texts = evidence(e)
            claim = next(c for c in ev['claims']
                         if c['pointer'] == '/operations/1/conditions/0/reported')
            claim['value_tokens'] = ['2']
            with self.subTest(unit=unit), self.assertRaisesRegex(ValueError, 'coverage'):
                p.validate_claims(e, ev, texts)
            ev, texts = evidence(e)
            texts[1] = texts[1].replace('2 ' + unit, '3 ' + unit)
            with self.subTest(unit=unit), self.assertRaisesRegex(ValueError, 'unmatched exact'):
                p.validate_claims(e, ev, texts)


if __name__ == '__main__':
    unittest.main()
