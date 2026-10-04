import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'session_coordination.py'
spec = importlib.util.spec_from_file_location('coord', SCRIPT)
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)

class CoordinationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'shared'; self.root.mkdir()
        c.write_new(self.root/'config.json', {'enabled': True, 'worker_sessions': ['a','b'], 'active_claims_per_worker': 2, 'ready_backlog_limit': 12})
        c.write_new(self.root/'candidates.json', [{'doi': f'10.1234/paper{i}'} for i in range(8)])
    def test_simultaneous_processes_claim_once_and_respect_cap(self):
        procs = [subprocess.Popen([sys.executable,str(SCRIPT),'--root',str(self.root),'claim-next','--session',s],stdout=subprocess.PIPE,stderr=subprocess.PIPE) for s in ['a','b']*4]
        results = [p.communicate() for p in procs]
        successes = [json.loads(o) for p,(o,e) in zip(procs,results) if p.returncode==0]
        self.assertEqual(len(successes),4)
        self.assertEqual(len({r['doi'] for r in successes}),4)
        self.assertEqual(sum(r['owner_session']=='a' for r in successes),2)
    def test_wrong_owner_and_actor_rejected(self):
        x=c.claim_next(self.root,'a')
        with self.assertRaises(ValueError):c.emit(self.root,'b',x['doi'],'extraction','b:extractor')
        with self.assertRaises(ValueError):c.emit(self.root,'a',x['doi'],'extraction','b:extractor')
    def test_ready_requires_independent_receipt(self):
        x=c.claim_next(self.root,'a'); p=self.root/'audit.json'
        c.write_new(p,{'doi':x['doi'],'accepted':True,'author_id':'a:x','reviewer_id':'a:x'})
        with self.assertRaises(ValueError):c.emit(self.root,'a',x['doi'],'ready','a:x',p)
        p.unlink();c.write_new(p,{'doi':x['doi'],'accepted':True,'author_id':'a:x','reviewer_id':'a:y'})
        e=c.emit(self.root,'a',x['doi'],'ready','a:y',p)
        self.assertFalse(e['publication_authorized'])
        self.assertFalse(e['scientific_acceptance_validated_by_coordinator'])
        with self.assertRaises(ValueError):c.emit(self.root,'a',x['doi'],'extraction','a:x')
        self.assertFalse((self.root/'ledger.jsonl').exists())
    def test_stop_and_occupied_lock_fail_closed(self):
        (self.root/'STOP').write_text('owner pause')
        with self.assertRaises(RuntimeError):c.claim_next(self.root,'a')
        (self.root/'.coordination.lock').write_text('other writer')
        with self.assertRaises(RuntimeError):
            with c.lock(self.root,timeout=0.01):pass
        self.assertTrue((self.root/'.coordination.lock').exists())
    def test_normalized_doi_deduplication(self):
        p=self.root/'candidates.json';p.unlink()
        c.write_new(p,[{'doi':'https://doi.org/10.1234/PAPER'},{'doi':'10.1234/paper'}])
        c.claim_next(self.root,'a')
        with self.assertRaises(RuntimeError):c.claim_next(self.root,'b')
    def test_receipt_required_and_external_path_rejected(self):
        x=c.claim_next(self.root,'a')
        with self.assertRaises(ValueError):c.emit(self.root,'a',x['doi'],'audit','a:y')
        with self.assertRaises(ValueError):c.emit(self.root,'a',x['doi'],'audit','a:y',SCRIPT)
    def test_sequence_not_wall_clock_drives_projection(self):
        x=c.claim_next(self.root,'a');e=c.emit(self.root,'a',x['doi'],'extraction','a:x')
        p=self.root/'accepted.json';c.write_new(p,{'doi':x['doi'],'accepted':True,'author_id':'a:x','reviewer_id':'a:y'})
        e2=c.emit(self.root,'a',x['doi'],'ready','a:y',p)
        self.assertGreater(e2['sequence'],e['sequence'])
        ep=self.root/'inbox'/(e2['event_id']+'.json');d=c.load(ep);d['at']='2000-01-01T00:00:00Z';ep.write_text(json.dumps(d))
        self.assertEqual(c.status(self.root)[0]['status'],'ready')
    def test_integrator_acknowledgment_drains_without_reclaim(self):
        x=c.claim_next(self.root,'a');p=self.root/'accepted.json'
        c.write_new(p,{'doi':x['doi'],'accepted':True,'author_id':'a:x','reviewer_id':'a:y'})
        c.emit(self.root,'a',x['doi'],'ready','a:y',p)
        c.write_new(self.root/'integrator-acknowledged'/(x['claim_key']+'.json'),{'claim_key':x['claim_key'],'integrator_id':'primary-integrator'})
        self.assertEqual(c.status(self.root)[0]['status'],'integrator_owned')
        with self.assertRaises(ValueError):c.emit(self.root,'a',x['doi'],'extraction','a:x')
    def test_incomplete_write_never_creates_visible_claim(self):
        original=c.json.dump
        def fail(obj,f,**kwargs):
            f.write('{');raise OSError('simulated disk full')
        with patch.object(c.json,'dump',side_effect=fail):
            with self.assertRaises(OSError):c.claim_next(self.root,'a')
        self.assertEqual(c.status(self.root),[])
        self.assertFalse(list((self.root/'claims').glob('*.partial')))
        self.assertEqual(c.claim_next(self.root,'b')['doi'],'10.1234/paper0')
    def test_create_never_overwrites_existing_evidence(self):
        p=self.root/'receipt.json';c.write_new(p,{'old':True})
        with self.assertRaises(FileExistsError):c.write_new(p,{'old':False})
        self.assertEqual(c.load(p),{'old':True})

if __name__=='__main__':unittest.main()
