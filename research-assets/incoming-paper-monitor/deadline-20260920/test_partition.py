import copy,unittest
from partition_deadline_scope import partition
class PartitionTests(unittest.TestCase):
    def setUp(self):
        self.l={'source_paths':{'incoming':'C:/cutoff-test'},'groups':{'g':{'queue_order':1,'generation':1,'review':{'status':'complete'},'needs_recheck':False}},'files':{'g.pdf':{'source_id':'incoming','relative_filename':'g.pdf','group_id':'g','role':'main','size':10,'mtime_ns':1,'birthtime_ns':1,'exists':True}},'group_aliases':{}}
        self.i={'cutoff_at':'2026-09-20T00:00:00+00:00','entries':[{'source_id':'incoming','absolute_path':'C:/cutoff-test/g.pdf','relative_path':'g.pdf','monitor_eligible':True,'size_bytes':10,'mtime_ns':1,'birthtime_ns':1,'last_known_canonical_group_id':'g'}],'nested_document_candidates':[]}
        self.m={'groups':[{'group_id':'g','source_generation':1,'cutoff_present_file_keys':['g.pdf']}]}
    def test_terminal_seed_is_included_without_becoming_pending(self):
        p=partition(self.l,self.i,self.m);self.assertEqual(p['included_canonical_group_ids'],['g']);self.assertEqual(p['included_pending_group_ids'],[])
    def test_new_paper_stays_separate(self):
        self.l['groups']['later']={'generation':1,'review':{'status':'queued'}};self.l['files']['later.pdf']=dict(self.l['files']['g.pdf'],relative_filename='later.pdf',group_id='later')
        p=partition(self.l,self.i,self.m);self.assertEqual(p['later_arrival_group_ids'],['later']);self.assertEqual(p['included_canonical_group_ids'],['g'])
    def test_late_si_reopens_included_scope_check(self):
        self.l['files']['g_si_1.pdf']=dict(self.l['files']['g.pdf'],relative_filename='g_si_1.pdf',role='si');self.l['groups']['g']['generation']=2
        p=partition(self.l,self.i,self.m);self.assertEqual(p['later_arrival_group_ids'],[]);self.assertEqual(len(p['post_cutoff_included_paper_evidence_candidates']),1);self.assertTrue(p['included_groups'][0]['requires_generation_reopen_consistency_check']);self.assertEqual(self.l['groups']['g']['review']['status'],'complete')
    def test_newly_mapped_cutoff_file_is_included(self):
        self.i['entries'].append(dict(self.i['entries'][0],absolute_path='C:/cutoff-test/u.pdf',relative_path='u.pdf',last_known_canonical_group_id=None))
        p=partition(self.l,self.i,self.m);self.assertEqual(len(p['unmapped_cutoff_files']),1)
        self.l['groups']['u']={'generation':1,'review':{'status':'queued'}};self.l['files']['u.pdf']=dict(self.l['files']['g.pdf'],relative_filename='u.pdf',group_id='u')
        p=partition(self.l,self.i,self.m);self.assertEqual(p['unmapped_cutoff_files'],[]);self.assertIn('u',p['included_pending_group_ids']);self.assertEqual(len(p['cutoff_files_newly_mapped_since_capture']),1)
    def test_alias_merge_retains_membership_and_missing_path(self):
        self.l['groups']['merged']=self.l['groups'].pop('g');self.l['groups']['g']={'alias_of':'merged'};self.l['group_aliases']['g']='merged';self.l['files']={}
        p=partition(self.l,self.i,self.m);self.assertEqual(p['included_canonical_group_ids'],['merged']);self.assertEqual(len(p['unmapped_cutoff_files']),1)
    def test_changed_stat_does_not_silently_finish(self):
        self.l['files']['g.pdf']['size']=20;p=partition(self.l,self.i,self.m)
        self.assertTrue(p['included_groups'][0]['requires_generation_reopen_consistency_check']);self.assertEqual(len(p['changed_cutoff_membership_signatures']),1)
    def test_same_doi_candidate_is_not_merged(self):
        self.l['groups']['g']['doi_candidates']=['10.1/a'];self.l['groups']['other']={'generation':1,'review':{'status':'queued'},'doi_candidates':['10.1/a']};self.l['files']['other_si_1.pdf']=dict(self.l['files']['g.pdf'],relative_filename='other_si_1.pdf',group_id='other',role='si')
        before=copy.deepcopy(self.l);p=partition(self.l,self.i,self.m);self.assertEqual(p['later_arrival_group_ids'],['other']);self.assertEqual(before,self.l)
if __name__=='__main__':unittest.main()
