"""Pure synthetic M selection/preservation tests; no paper or network requests."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import reader_background as m
from build_reader_shards import shards


class ReaderBackgroundTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library = m.load_library(ROOT)

    def record(self, method='', roles=()):
        return {'record_id': 'r', 'method': method, 'lineage': {'source_group': 'source'},
                'quality': {'review_status': 'reviewed'},
                'materials': [{'id': 'm'+str(i), 'name': name, 'role': role}
                              for i, (name, role) in enumerate(roles)],
                'operations': []}

    def selected(self, record, presentation=None):
        return m.select_background(record, presentation or {}, self.library)

    def test_library_is_short_verified_authored_text_with_exact_label(self):
        for item in self.library['statements']:
            self.assertFalse(any(c.isdigit() for c in item['summary']))
            self.assertLessEqual(len(item['summary']), 520)
        self.assertEqual(m.LABEL, "General background, not the authors' interpretation")
        self.assertEqual(m.LIMIT, 3)

    def test_every_fixed_J_class_and_named_method_has_an_explicit_mapping(self):
        self.assertEqual(set(self.library['routes']), {name for name, _ in m.ROUTE_CLASSES+m.NAMED_METHODS})
        # The pure J classifier owns ambiguity/route detection. Exercise each
        # exact accepted class without replacing it with ad-hoc substring rules.
        from unittest.mock import patch
        for label, statement in self.library['routes'].items():
            with self.subTest(label=label), patch.object(m, 'route', return_value=label):
                self.assertEqual(self.selected(self.record())[0]['id'], statement)

    def test_actual_J_route_not_material_family_route_drives_selection(self):
        self.assertEqual(self.selected(self.record('Hot injection'))[0]['id'], 'hot-injection')
        self.assertEqual(self.selected(self.record('MBE'))[0]['id'], 'mbe')
        self.assertEqual(self.selected(self.record('Sol-gel'))[0]['id'], 'solgel')
        self.assertEqual(self.selected(self.record('Cation exchange'))[0]['id'], 'cation-exchange')

    def test_negated_or_conflicting_route_does_not_get_route_background(self):
        for value in ('without hot injection', 'hot injection or hydrothermal', 'unknown route'):
            with self.subTest(value=value):
                self.assertEqual([x['id'] for x in self.selected(self.record(value))], ['general-context'])

    def test_role_aliases_and_explicit_ligand_identity_subtypes(self):
        roles = [('oleic acid', 'surface_ligand'), ('oleylamine', 'amine-ligand'),
                 ('TOP', 'phosphine solvent'), ('TOPO', 'phosphine oxide ligand')]
        self.assertEqual(m.reported_roles(self.record(roles=roles)),
                         ['carboxylic-acid-ligand', 'amine-ligand', 'phosphine', 'phosphine-oxide'])

    def test_generic_reagent_name_formula_and_inventory_do_not_assign_roles(self):
        record = self.record(roles=[('oleic acid', 'reagent'), ('TOP', 'solvent inventory only'),
                                    ('cadmium', 'source-listed metal source; inventory only'),
                                    ('unknown', 'unknown ligand'), ('borohydride', 'not used reducing agent')])
        record['materials'][0]['formula'] = 'C18H34O2'
        self.assertEqual(m.reported_roles(record), [])
        self.assertEqual(self.selected(record)[0]['id'], 'general-context')

    def test_source_roles_accept_typed_feed_but_not_substrate_or_generic_reagent(self):
        record = self.record(roles=[('Cd precursor', 'cadmium precursor feed'),
                                    ('Se feed', 'selenium precursor solute'),
                                    ('GaAs wafer', 'substrate'), ('Pd', 'reagent')])
        self.assertEqual(m.reported_roles(record), ['metal-source', 'chalcogen-pnictogen-source'])

    def test_route_then_fixed_roles_deduplicates_and_caps_at_three(self):
        record = self.record('Hot injection', [('OA', 'carboxylic acid ligand'),
                             ('second OA', 'carboxylic acid ligand'), ('amine', 'amine ligand'),
                             ('NaBH4', 'reducing agent'), ('ethanol', 'antisolvent')])
        self.assertEqual([x['id'] for x in self.selected(record)],
                         ['hot-injection', 'carboxylate-ligand', 'amine-ligand'])

    def test_unknown_route_with_reported_role_uses_role_without_fallback(self):
        self.assertEqual([x['id'] for x in self.selected(self.record('unknown', [('x', 'reducing agent')]))], ['reducing-agent'])

    def test_generic_solvent_and_ligand_do_not_claim_specific_coordination(self):
        self.assertEqual(m.reported_roles(self.record(roles=[('unknown material', 'ligand'), ('TOP', 'solvent')])), ['ligand', 'solvent'])
        self.assertEqual(m.reported_roles(self.record(roles=[('ODE', 'non-coordinating solvent'), ('x', 'solvent')])), ['noncoordinating-solvent'])

    def test_status_does_not_affect_selection_and_inputs_stay_exact(self):
        record = self.record('Hot injection', [('oleic acid', 'ligand')])
        entry = {'method_label': 'Hot injection', 'intuition': [{'summary': 'Original source claim'}]}
        before = copy.deepcopy((record, entry, self.library))
        first = self.selected(record, entry)
        second = copy.deepcopy(record)
        second['quality']['review_status'] = 'source_extracted'
        self.assertEqual(first, self.selected(second, entry))
        self.assertEqual((record, entry, self.library), before)
        first[0]['reference']['title'] = 'mutated result'
        self.assertNotEqual(first, self.selected(record, entry))

    def test_attach_preserves_source_claims_and_shard_scope_exactly(self):
        entries = {'r': {'source_id': 'source', 'intuition': [{'summary': 'kept', 'claim_type': 'Source interpretation'}],
                          'figures': [{'id': 'figure'}]},
                   'q': {'source_id': 'source', 'figures': []}}
        view = {'records': entries, 'materials': {'material': {'record_ids': ['r', 'q']}}, 'figures_by_source': {}}
        records = {'r': self.record('Hot injection'), 'q': self.record('')}
        before = copy.deepcopy((view, records))
        projected, counts = m.attach_background(view, records, self.library)
        self.assertEqual((view, records), before)
        for rid in entries:
            self.assertEqual({k: v for k, v in projected['records'][rid].items() if k != 'general_background'}, entries[rid])
        self.assertEqual(counts['before_sections_visible'], 1)
        self.assertEqual(counts['after_sections_visible'], 2)
        self.assertEqual(counts['both'], 1)
        self.assertEqual(counts['background_only'], 1)
        self.assertEqual(counts['background_card_distribution'], {'0': 0, '1': 2, '2': 0, '3': 0})
        output = shards(projected)
        self.assertEqual(json.loads(output['records/r.json']), projected['records']['r'])
        self.assertNotIn('general_background', json.loads(output['materials/material.json'])['material'])

    def test_empty_projection_preserves_view_identity_and_zero_coverage(self):
        view = {'records': {}, 'materials': {}, 'figures_by_source': {}}
        before = copy.deepcopy(view)
        projected, coverage = m.attach_background(view, {}, self.library)
        self.assertIs(projected, view)
        self.assertEqual(view, before)
        self.assertEqual(coverage['canonical_records'], 0)
        self.assertEqual(coverage['reader_records'], 0)
        self.assertEqual(coverage['after_sections_visible'], 0)
        self.assertEqual(coverage['background_card_distribution'], {'0': 0, '1': 0, '2': 0, '3': 0})

    def test_canonical_non_Reader_records_keep_separate_default_visibility_counts(self):
        view = {'records': {'r': {'source_id': 'source', 'figures': []}},
                'materials': {'material': {'record_ids': ['r']}}, 'figures_by_source': {}}
        records = {'r': self.record('Hot injection'), 'context': self.record('')}
        before = copy.deepcopy((view, records))
        projected, counts = m.attach_background(view, records, self.library)
        self.assertEqual(set(projected['records']), {'r'})
        self.assertEqual((counts['canonical_records'], counts['reader_records']), (2, 1))
        self.assertEqual(counts['after_sections_visible'], 1)
        self.assertEqual(sum(counts['background_card_distribution'].values()), 1)
        canonical = counts['all_canonical']
        self.assertEqual(canonical['Data_only_default_pages'], 1)
        self.assertEqual(canonical['static_Data_sections_before'], 2)
        self.assertEqual(canonical['pages_with_authored_background_after'], 2)
        self.assertEqual(canonical['default_visible_union_before'], 1)
        self.assertEqual(canonical['default_visible_union_after'], 2)
        self.assertEqual(sum(canonical['background_card_distribution'].values()), 2)
        self.assertNotIn('records/context.json', shards(projected))
        self.assertEqual((view, records), before)

    def test_required_Reader_record_without_canonical_input_is_not_silently_skipped(self):
        view = {'records': {'required': {}}, 'materials': {}, 'figures_by_source': {}}
        with self.assertRaises(KeyError):
            m.attach_background(view, {}, self.library)

    def test_empty_source_array_keeps_browser_precedence_and_Wu_placeholder_count(self):
        self.assertEqual(m.source_interpretations({'intuition': [], 'chemical_intuition': [{'summary': 'alias'}]}), [])
        self.assertEqual(m.source_interpretations({'intuition': None, 'chemical_intuition': [{'summary': 'alias'}]}), [{'summary': 'alias'}])
        record = self.record()
        record['lineage']['source_group'] = 'wu2008'
        view = {'records': {'r': {}}, 'materials': {}, 'figures_by_source': {}}
        _, counts = m.attach_background(view, {'r': record}, self.library)
        self.assertEqual(counts['before_sections_visible'], 1)
        self.assertEqual(counts['before_sections_with_source_content'], 0)

    def test_missing_library_is_an_explicit_error_not_a_silent_empty_projection(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(FileNotFoundError):
                m.load_library(root)

    def test_invalid_reference_and_numeric_or_oversized_statement_fail(self):
        pins = json.loads((ROOT/'scripts/reader_background_reference_pins.json').read_bytes())
        for mutate in ('number', 'unverified', 'long', 'unmapped'):
            library, proof = copy.deepcopy(self.library), copy.deepcopy(pins)
            if mutate == 'number': library['statements'][0]['summary'] += ' At 250 degrees.'
            if mutate == 'unverified': next(iter(proof['references'].values()))['resolver_redirect_verified'] = False
            if mutate == 'long': library['statements'][0]['summary'] = 'x'*600+'.'
            if mutate == 'unmapped': library['routes']['Hot injection'] = 'missing'
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                m.validate_library(library, proof)


if __name__ == '__main__':
    unittest.main()
