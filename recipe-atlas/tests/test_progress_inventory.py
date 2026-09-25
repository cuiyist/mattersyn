"""A new contribution must update inventory totals without inventing audit events."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from generate_release_metadata import synchronize_progress_counts

class ProgressInventoryTests(unittest.TestCase):
    def test_added_route_replaces_stale_totals_without_counting_components_twice(self):
        route={'collection':'reviewed_literature','record_type':'protocol_variant',
               'quality':{'review_status':'source_reviewed','requested_tasks':[]},
               'reader_role':'synthesis_route','operations':[{'stage':'synthesis'}]}
        observation=copy.deepcopy(route);observation.update(record_type='observation',reader_role='contextual_observation')
        benchmark=copy.deepcopy(route);benchmark['collection']='published_benchmark'
        progress={'published':{'record_count':99,'public_source_group_count':99},
                  'daily_throughput':{'completed_papers_today':0},'recent_milestones':[{'text':'Prior immutable event'}]}
        events=copy.deepcopy(progress['recent_milestones'])
        manifest={'dataset_version':'test','records':[{'eligibility':{'exact_structure_recipe':{'eligible':False}}} for _ in range(3)]}
        synchronize_progress_counts(progress,manifest,[route,observation,benchmark],{'paper':{}},
                                    [{'component_only':False},{'component_only':True}],2)
        self.assertEqual(progress['published']['record_count'],3)
        self.assertEqual(progress['published']['synthesis_route_count'],1)
        self.assertEqual(progress['published']['material_hub_count'],2)
        self.assertEqual(progress['published']['direct_material_hub_count'],1)
        self.assertEqual(progress['published']['component_material_hub_count'],1)
        self.assertEqual(progress['published']['public_source_group_count'],2)
        self.assertEqual(progress['published']['formal_source_reader_count'],1)
        self.assertEqual(progress['published']['exact_structure_recipe_count'],0)
        self.assertEqual(progress['daily_throughput']['completed_papers_today'],0)
        self.assertEqual(progress['recent_milestones'],events)

if __name__=='__main__':unittest.main()
