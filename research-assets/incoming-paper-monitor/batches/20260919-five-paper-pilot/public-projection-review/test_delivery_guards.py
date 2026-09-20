"""Offline simulations only: replace credential() and api() before running main body."""
from pathlib import Path
from contextlib import redirect_stdout,redirect_stderr
from unittest.mock import patch
import ast,copy,io,sys,unittest
SOURCE=Path(__file__).resolve().parents[5]/'research-assets/github_public_delivery.py'
class Guards(unittest.TestCase):
    def simulate(self,args,responses):
        code=SOURCE.read_text(encoding='utf-8');tree=ast.parse(code);guard=tree.body[-1];self.assertIsInstance(guard,ast.If)
        ctx={'__name__':'offline_guard_test','__file__':str(SOURCE)}
        exec(compile(ast.Module(body=tree.body[:-1],type_ignores=[]),str(SOURCE),'exec'),ctx)
        events=[];remaining=copy.deepcopy(responses);credentials=[]
        def credential():credentials.append('called fake');return 'offline-audit-placeholder'
        def api(path,method='GET',payload=None):
            events.append((method,path,payload))
            if not remaining:raise AssertionError('Unexpected simulated API operation: '+method+' '+path)
            expected_method,expected_path,status,data=remaining.pop(0)
            self.assertEqual((method,path),(expected_method,expected_path));return status,data
        ctx['credential']=credential;ctx['api']=api
        out=io.StringIO();err=io.StringIO();stopped=False
        with patch.object(sys,'argv',[str(SOURCE),*args]),redirect_stdout(out),redirect_stderr(err):
            try:exec(compile(ast.Module(body=guard.body,type_ignores=[]),str(SOURCE),'exec'),ctx)
            except SystemExit:stopped=True
        self.assertNotIn('offline-audit-placeholder',out.getvalue()+err.getvalue())
        return {'stopped':stopped,'events':events,'remaining':remaining,'credentials':credentials,'output':out.getvalue()}
    def user(self):return ('GET','/user',200,{'login':'cuiyist','id':147659097})
    def start(self,old_id=10,archive_exists=False):return [self.user(),('GET','/repos/cuiyist/mattersyn-site',200,{'id':old_id,'name':'mattersyn-site','private':False}),('GET','/repos/cuiyist/mattersyn-site-source-archive-20260920',200 if archive_exists else 404,{'id':99} if archive_exists else {})]
    def args(self):return ['preserve-and-create','--repo','mattersyn-site','--expected-old-id','10']
    def test_wrong_account_blocks_all_repository_actions(self):
        r=self.simulate(self.args(),[('GET','/user',200,{'login':'other','id':999})]);self.assertTrue(r['stopped']);self.assertEqual(len(r['events']),1)
    def test_wrong_original_id_blocks_rename(self):
        r=self.simulate(self.args(),self.start(old_id=11));self.assertTrue(r['stopped']);self.assertTrue(all(e[0]=='GET' for e in r['events']))
    def test_existing_preservation_name_blocks_mutation(self):
        r=self.simulate(self.args(),self.start(archive_exists=True));self.assertTrue(r['stopped']);self.assertTrue(all(e[0]=='GET' for e in r['events']))
    def test_wrong_private_preservation_state_blocks_create(self):
        r=self.simulate(self.args(),self.start()+[('PATCH','/repos/cuiyist/mattersyn-site',200,{'id':10,'name':'mattersyn-site-source-archive-20260920','private':False})]);self.assertTrue(r['stopped']);self.assertFalse(any(e[0]=='POST' for e in r['events']))
    def test_success_is_preserve_before_create_with_fixed_payloads(self):
        r=self.simulate(self.args(),self.start()+[('PATCH','/repos/cuiyist/mattersyn-site',200,{'id':10,'name':'mattersyn-site-source-archive-20260920','private':True}),('POST','/user/repos',201,{'id':20,'name':'mattersyn-site','private':False})]);self.assertFalse(r['stopped']);self.assertEqual(r['events'][-2],('PATCH','/repos/cuiyist/mattersyn-site',{'name':'mattersyn-site-source-archive-20260920','private':True}));self.assertFalse(r['events'][-1][2]['private']);self.assertFalse(r['events'][-1][2]['auto_init'])
    def test_missing_created_visibility_is_not_verified(self):
        r=self.simulate(self.args(),self.start()+[('PATCH','/repos/cuiyist/mattersyn-site',200,{'id':10,'name':'mattersyn-site-source-archive-20260920','private':True}),('POST','/user/repos',201,{'id':20,'name':'mattersyn-site'})]);self.assertTrue(r['stopped'])
    def test_unapproved_repository_name_never_gets_credentials(self):
        r=self.simulate(['preserve-and-create','--repo','unrelated','--expected-old-id','10'],[]);self.assertTrue(r['stopped']);self.assertEqual(r['credentials'],[]);self.assertEqual(r['events'],[])
    def test_enable_pages_requires_public_website_repository(self):
        r=self.simulate(['enable-pages'],[self.user(),('GET','/repos/cuiyist/mattersyn-site',200,{'private':True})]);self.assertTrue(r['stopped']);self.assertTrue(all(e[0]=='GET' for e in r['events']))
if __name__=='__main__':unittest.main()
