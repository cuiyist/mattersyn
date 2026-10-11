"""Synthetic chemical-name matching regressions; no paper, Git, network or source checkout mutations."""
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

spec = importlib.util.spec_from_file_location('to_site_matching', Path(__file__).with_name('to_site.py'))
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class ChemicalMatchingTest(unittest.TestCase):
    def entry(self, eid, name, **extra):
        return dict(id=eid, name=name, depictionKind='ionic_components', **dict({'aliases': []}, **extra))

    def index(self, entries):
        index = {}
        for entry in entries:
            for name in [entry['name']] + entry.get('aliases', []):
                for key in c.name_keys(name):
                    index.setdefault(key, []).append(entry)
        return index

    def test_internal_formula_groups_never_collapse(self):
        names = ['Cd(acac)2', 'Cd(ClO4)2', 'Cd(NO3)2', 'Cd(oleate)2', 'Zn(NO3)2·6H2O']
        self.assertEqual(len({c.name_keys(n)[0] for n in names}), len(names))
        self.assertTrue(all(len(c.name_keys(n)) == 1 for n in names))
        index = self.index([self.entry('cadmium-acac', names[0])])
        for name in names[1:]:
            self.assertIsNone(c.chemical_match(index, name, lambda e: e['id']))

    def test_internal_text_groups_and_oxidation_are_preserved(self):
        for name in ['tris(dimethylamino)arsine', 'tris(trimethylsilyl)arsine',
                     'poly(allylamine hydrochloride) (PAH)', 'poly(propylene glycol)',
                     'Iron (III)', 'Zinc(II) chloride', 'copper iodide (anhydrous)',
                     'cadmium chloride (hydrate)', 'chemical (SO2)', 'chemical (CdCl2)']:
            with self.subTest(name=name):
                self.assertIn('(', c.name_keys(name)[0])
                self.assertEqual(len(c.name_keys(name)), 1)

    def test_terminal_token_needs_both_explicit_aliases(self):
        self.assertEqual(c.name_keys('N,N-dimethylformamide (DMF)'),
                         ['n,n-dimethylformamide(dmf)'])
        target = self.entry('hda', 'Hexadecylamine', aliases=['HDA'])
        self.assertEqual(c.chemical_match(self.index([target]), 'Hexadecylamine (HDA)', lambda e: e['id']), target)
        self.assertEqual(c.chemical_match(self.index([target]), 'hexadecylamine', lambda e: e['id']), target)
        incomplete = self.entry('hda', 'Hexadecylamine')
        self.assertIsNone(c.chemical_match(self.index([incomplete]), 'Hexadecylamine (HDA)', lambda e: e['id']))
        other_token = self.entry('other', 'Different reagent', aliases=['HDA'])
        self.assertIsNone(c.chemical_match(self.index([incomplete, other_token]), 'Hexadecylamine (HDA)', lambda e: e['id']))

    def test_terminal_chemical_qualifications_never_map_to_element_or_generic_reagent(self):
        index = self.index([self.entry('zinc-metal', 'Zinc', aliases=['Zn']),
                            self.entry('generic', 'reagent'), self.entry('hydroxyl', 'OH'),
                            self.entry('carbon-monoxide', 'CO'), self.entry('cyanide', 'CN')])
        for name in ['zinc (OH)', 'reagent (CO)', 'reagent (CN)', 'zinc (II)',
                     'zinc (hydrate)', 'zinc (anhydrous)']:
            with self.subTest(name=name):
                self.assertIsNone(c.chemical_match(index, name, lambda e: e['id']))
        self.assertNotIn('zinc', self.index([self.entry('qualified', 'zinc (OH)')]))

    def test_exact_name_beats_terminal_abbreviation_fallback(self):
        exact = self.entry('z-exact', 'Alpha reagent (AR)')
        fallback = self.entry('a-fallback', 'Alpha reagent', aliases=['AR'])
        self.assertEqual(c.chemical_match(self.index([exact, fallback]), 'Alpha reagent (AR)', lambda e: e['id']), exact)

    def test_no_cross_match_tris_or_poly(self):
        index = self.index([self.entry('tms3as', 'Tris(trimethylsilyl)arsine'),
                            self.entry('polypropylene', 'Poly(propylene glycol)')])
        for name in ['tris(dimethylamino)arsine', 'poly(allylamine hydrochloride) (PAH)']:
            with self.subTest(name=name):
                self.assertIsNone(c.chemical_match(index, name, lambda e: e['id']))

    def test_equivalent_parenthesis_spacing_preserves_group_content(self):
        target = self.entry('bis-trimethylsilyl-sulfide', 'Bis(trimethylsilyl)sulfide')
        self.assertEqual(c.chemical_match(self.index([target]), 'bis(trimethylsilyl) sulfide', lambda e: e['id']), target)
        self.assertNotEqual(c.name_keys('bis(trimethylsilyl) sulfide'), c.name_keys('bis(dimethylamino) sulfide'))

    def test_safe_existing_binding_is_kept_without_reranking(self):
        exact = self.entry('a-exact', 'Alpha reagent (AR)')
        existing = self.entry('z-existing', 'Alpha reagent', aliases=['AR'])
        index = self.index([exact, existing])
        self.assertEqual(c.chemical_match(index, 'Alpha reagent (AR)', lambda e: e['id'], 'z-existing'), existing)
        self.assertEqual(c.chemical_match(index, 'Alpha reagent (AR)', lambda e: e['id'], 'not-compatible'), exact)

    def test_name_card_fallback_preserves_existing_bindings_assets_and_record_bytes(self):
        with TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            atlas = Path(tmp)
            base = atlas / 'static/assets/chemical-registry'
            (base / 'svg').mkdir(parents=True)
            registry = {'entries': [self.entry('gu2004-cadmium-acac-reference', 'Cd(acac)2', formula='C10H14CdO4')]}
            binding = {'recordBindings': {'audited': {'material': 'audited-asset'}},
                       'recordStateBindings': {'audited': {'state': 'audited-state'}},
                       'sourceRecordSha256': {'audited': 'pinned-old-record'}}
            for name, doc in [('registry.json', registry), ('bindings.json', binding)]:
                (base / name).write_text(json.dumps(doc), encoding='utf-8')
            asset = base / 'svg/gu2004-cadmium-acac-reference.svg'
            asset.write_bytes(b'prior reference asset')
            record = {'record_id': 'synthetic-new', 'materials': [{'id': 'cd-clo4-2', 'name': 'Cd(ClO4)2'}]}
            record_path = atlas / 'data/records/synthetic-new.json'
            record_path.parent.mkdir(parents=True)
            record_path.write_bytes(json.dumps(record).encode())
            old_record = record_path.read_bytes()
            created = []
            self.assertEqual(c.bind_chemicals(atlas, [record], 'https://doi.org/10.1234/synthetic', created), (0, 1))
            result = json.loads((base / 'bindings.json').read_text())
            self.assertEqual(result['recordBindings']['audited'], binding['recordBindings']['audited'])
            self.assertEqual(result['recordStateBindings'], binding['recordStateBindings'])
            self.assertEqual(result['recordBindings']['synthetic-new']['cd-clo4-2'], 'name-card-cd-clo4-2')
            card = json.loads((base / 'registry.json').read_text())['entries'][-1]
            self.assertEqual((card['formula'], card['model2dPath'], card['model3dPath']), ('', None, None))
            self.assertIn('no structure asserted', created[0].read_text())
            self.assertEqual(asset.read_bytes(), b'prior reference asset')
            self.assertEqual(record_path.read_bytes(), old_record)

    def test_selective_rebind_preserves_every_unselected_binding(self):
        with TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            atlas = Path(tmp)
            base = atlas / 'static/assets/chemical-registry'
            (base / 'svg').mkdir(parents=True)
            registry = {'entries': [self.entry('gu2004-cadmium-acac-reference', 'Cd(acac)2')]}
            binding = {'recordBindings': {'simple': {'bad': 'gu2004-cadmium-acac-reference', 'keep': 'qualified-current'},
                                         'audited': {'old': 'audited-asset'}},
                       'recordStateBindings': {'audited': {'state': 'audited-state'}}, 'sourceRecordSha256': {}}
            for name, doc in [('registry.json', registry), ('bindings.json', binding)]:
                (base / name).write_text(json.dumps(doc), encoding='utf-8')
            record = {'record_id': 'simple', 'materials': [{'id': 'bad', 'name': 'Cd(ClO4)2'},
                                                        {'id': 'keep', 'name': 'Unresolved qualification'}]}
            path = atlas / 'data/records/simple.json'
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(record), encoding='utf-8')
            original = path.read_bytes()
            self.assertEqual(c.bind_chemicals(atlas, [record], 'https://doi.org/10.1234/test', [], {'bad'}), (0, 1))
            result = json.loads((base / 'bindings.json').read_text())
            self.assertEqual(result['recordBindings']['simple']['keep'], 'qualified-current')
            self.assertEqual(result['recordBindings']['audited'], binding['recordBindings']['audited'])
            self.assertEqual(result['recordStateBindings'], binding['recordStateBindings'])
            self.assertEqual(path.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
