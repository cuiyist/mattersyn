"""End-to-end test of source preservation, filtering and merge ancestry."""
from pathlib import Path
import json, os, subprocess, sys, tempfile, unittest

ROOT=Path(__file__).resolve().parent

def cmd(repo,*args):
    r=subprocess.run(['git','-c','safe.directory='+repo.as_posix(),'-C',str(repo),*args],capture_output=True)
    if r.returncode:raise RuntimeError('Synthetic git fixture failure: '+args[0])
    return r.stdout

class HistoryRepairTest(unittest.TestCase):
    def test_isolated_projection_preserves_graph_and_source(self):
        base=Path(tempfile.mkdtemp(prefix='history-engine-test-'));src=base/'original';src.mkdir();dst=base/'public';reports=base/'reports'
        cmd(src,'init','--initial-branch=main');cmd(src,'config','user.name','Synthetic Test');cmd(src,'config','user.email','test@example.invalid');cmd(src,'config','core.autocrlf','false')
        (src/'README.md').write_text('Authored record\n',encoding='utf-8');(src/'private').mkdir();(src/'private'/'source.json').write_text('{"text":"private fixture"}',encoding='utf-8')
        cmd(src,'add','.');cmd(src,'commit','-m','First scientific checkpoint')
        cmd(src,'checkout','-b','side');(src/'side.md').write_text('Authored supplementary checkpoint\n',encoding='utf-8');cmd(src,'add','.');cmd(src,'commit','-m','Parallel review')
        cmd(src,'checkout','main');(src/'README.md').write_text('Authored record with LOCAL_PRIVATE_PATH\n',encoding='utf-8');cmd(src,'add','.');cmd(src,'commit','-m','Update public record');cmd(src,'merge','side','--no-ff','-m','Merge independent review')
        head=cmd(src,'rev-parse','HEAD').decode().strip();refs=cmd(src,'show-ref');before=cmd(src,'status','--porcelain=v1','-z')
        (base/'config.json').write_text('{}',encoding='utf-8')
        (base/'policy.py').write_text("def history_exclude_path(kind,path,config):\n    return 'private_fixture' if path.startswith('private/') else None\ndef history_project(kind,path,raw,config):\n    if path.startswith('private/'):return {'action':'omit','reason':'private_fixture'}\n    return {'action':'allow','reason':'authored','content':raw.replace(b'LOCAL_PRIVATE_PATH',b'[local evidence]'),'content_class':'authored'}\n",encoding='utf-8')
        result=subprocess.run([sys.executable,str(ROOT/'project_history.py'),'--source',str(src),'--destination',str(dst),'--reports',str(reports),'--policy',str(base/'policy.py'),'--config',str(base/'config.json'),'--kind','project','--expected-head',head],capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout.decode()+result.stderr.decode())
        self.assertEqual(cmd(src,'rev-parse','HEAD').decode().strip(),head);self.assertEqual(cmd(src,'show-ref'),refs);self.assertEqual(cmd(src,'status','--porcelain=v1','-z'),before)
        mapping=json.loads((reports/'commit-map.json').read_text());self.assertEqual(len(mapping),4)
        for old,new in mapping.items():
            oldparents=cmd(src,'show','-s','--format=%P',old).decode().strip().split();newparents=cmd(dst,'show','-s','--format=%P',new).decode().strip().split()
            self.assertEqual(newparents,[mapping[x] for x in oldparents]);self.assertEqual(cmd(src,'show','-s','--format=%an%n%ae%n%at%n%B',old),cmd(dst,'show','-s','--format=%an%n%ae%n%at%n%B',new));self.assertNotIn(b'private/source.json',cmd(dst,'ls-tree','-r','--name-only',new))
        self.assertNotIn('LOCAL_PRIVATE_PATH',(dst/'README.md').read_text());self.assertIn('LOCAL_PRIVATE_PATH',(src/'README.md').read_text())
        self.assertEqual(cmd(dst,'remote').strip(),b'');self.assertFalse((dst/'.git/objects/info/alternates').exists());self.assertTrue((src/'private/source.json').exists())
        print('Synthetic fixture retained outside the source checkout.')

if __name__=='__main__':unittest.main()
