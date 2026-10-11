import copy
import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

spec = importlib.util.spec_from_file_location('simple_recipe_vessel_scope', Path(__file__).with_name('to_site.py'))
converter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(converter)


class RecipeVesselScopeTest(unittest.TestCase):
    def operation(self, action='wash'):
        return {'action': action, 'label': action.capitalize(), 'parameters': {'temperature': {'value': 25, 'unit': 'degC'},
                                                                          'duration': {'value': 10, 'unit': 'min'}}}

    def test_recipe_vessel_does_not_become_workup_vessel(self):
        operation = self.operation(); before = copy.deepcopy(operation)
        svg, caption = converter.step_svg(operation, '50 mL three-neck flask')
        self.assertIn('Recipe-level reported vessel:', svg)
        self.assertIn('Recipe-level reported vessel: 50 mL three-neck flask.', caption)
        self.assertIn('No vessel assignment is made for this step.', svg)
        self.assertIn('Conceptual action diagram', caption)
        self.assertEqual(operation, before)

    def test_missing_recipe_vessel_remains_not_reported(self):
        svg, caption = converter.step_svg(self.operation('heat'), None)
        self.assertIn('Recipe-level vessel: not reported', svg)
        self.assertIn('No vessel assignment is made for this step.', caption)
        self.assertNotIn('three-neck', svg)

    def test_long_vessel_is_wrapped_inside_canvas_without_truncating_caption(self):
        vessel = 'A reported reactor label with additional fittings and source-stated capacity details ' * 4
        svg, caption = converter.step_svg(self.operation(), vessel)
        root = ET.fromstring(svg)
        _, _, width, height = map(float, root.attrib['viewBox'].split())
        self.assertEqual(width, 600)
        rows = root.findall('{http://www.w3.org/2000/svg}text')
        self.assertTrue(all(float(row.get('y')) + 20 < height for row in rows))
        self.assertTrue(all(len(row.text or '') <= 66 for row in rows if row.get('font-size') == '14'))
        self.assertIn(vessel, caption)


if __name__ == '__main__':
    unittest.main()
