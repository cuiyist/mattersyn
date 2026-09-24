import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from generate_release_metadata import readme_with_references
class ReadmeProjection(unittest.TestCase):
    def test_authored_instructions_survive_repeated_generation(self):
        original='# MatterSyn\n\n## Build\nRun the reviewed builder.\n'
        one=readme_with_references(original,'unused','old bibliography')
        two=readme_with_references(one,'unused','new bibliography')
        self.assertTrue(two.startswith(original))
        self.assertNotIn('old bibliography',two)
        self.assertEqual(two.count('<!-- mattersyn-generated-references:start -->'),1)
        self.assertEqual(two,readme_with_references(two,'unused','new bibliography'))
