import unittest,sys,tempfile,json,hashlib,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from make_runtime_snapshot import make
class RuntimeSnapshot(unittest.TestCase):
    def test_clean_commit_binding_and_outside_output(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp)/'source';root.mkdir();subprocess.run(['git','init','-q',str(root)],check=True)
            p=root/'recipe-atlas/input.txt';p.parent.mkdir();p.write_text('synthetic fixture')
            bp=root/'publication/build-inputs.json';bp.parent.mkdir();bp.write_text(json.dumps({'schema':'mattersyn-build-input-blueprint/1','updated_at':'2000-01-01T00:00:00Z','input_files':[{'path':'recipe-atlas/input.txt','sha256':hashlib.sha256(p.read_bytes()).hexdigest()}]}))
            subprocess.run(['git','add','.'],cwd=root,check=True);subprocess.run(['git','-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','Synthetic fixture'],cwd=root,check=True)
            out=Path(tmp)/'snapshot.json';result=make(root,bp,out)
            self.assertEqual(result['source_commit'],subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip())
            with self.assertRaises(ValueError):make(root,bp,root/'snapshot.json')
            p.write_text('changed')
            with self.assertRaises(ValueError):make(root,bp,Path(tmp)/'dirty.json')
