"""Tiny offline fixtures for direct preview composition; no release actions."""
import copy
import os
from pathlib import Path
import shutil
import stat
import tempfile
import unittest
from unittest.mock import patch
import one_build as p
import release_batch as rb


class PreviewCompositionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.site, self.dist = self.root/'site', self.root/'dist'
        self.old = {'same.txt':b'same','changed.txt':b'old','gone.txt':b'gone',
                    '.github/workflows/site.yml':b'workflow','tools/check.py':b'check',
                    '.release-control/policy.json':b'policy','.gitattributes':b'attrs'}
        self.new = {'same.txt':b'same','changed.txt':b'new','added.txt':b'added'}
        self.put(self.site,self.old);self.put(self.dist,self.new)
        self.base,self.artifacts=p.inventory(self.site),p.inventory(self.dist)
        self.out=self.root/'preview'

    @staticmethod
    def put(root,files):
        for name,raw in files.items():
            q=root/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(raw)

    def compose(self,**kw):
        return p.compose_site_preview(kw.get('site',self.site),kw.get('dist',self.dist),
            kw.get('out',self.out),kw.get('base',self.base),kw.get('artifacts',self.artifacts),
            kw.get('controls',rb.SITE_CONTROL))

    def test_exact_legacy_output_and_delta(self):
        legacy=self.root/'legacy';p.copy_exact(self.site,legacy,self.base)
        expected=rb.stage_dist(self.dist,legacy)
        self.assertEqual(self.compose(),expected)
        self.assertEqual(p.inventory(self.out),p.inventory(legacy))
        self.assertEqual(expected,(['added.txt'],['changed.txt'],['gone.txt']))
        self.assertEqual(p.inventory(self.site),self.base)
        self.assertEqual(p.inventory(self.dist),self.artifacts)

    def test_reordered_rows_identical(self):
        self.compose(base=list(reversed(self.base)),artifacts=list(reversed(self.artifacts)))
        want={**{n:b for n,b in self.old.items() if n.split('/')[0] in rb.SITE_CONTROL},**self.new}
        self.assertEqual({r['path']:(self.out/r['path']).read_bytes() for r in p.inventory(self.out)},want)

    def test_manifest_size_and_digest_drift(self):
        for key,value in [('bytes',999),('sha256','a'*64)]:
            with self.subTest(key=key):
                rows=copy.deepcopy(self.artifacts);rows[0][key]=value
                with self.assertRaisesRegex(p.Rejected,'copy_input_drift'):self.compose(artifacts=rows,out=self.root/key)

    def test_same_size_restored_mtime_input_drift(self):
        q=self.dist/'changed.txt';old=q.stat();q.write_bytes(b'bad');os.utime(q,ns=(old.st_atime_ns,old.st_mtime_ns))
        with self.assertRaisesRegex(p.Rejected,'copy_input_drift'):self.compose()

    def test_control_content_drift(self):
        (self.site/'tools/check.py').write_bytes(b'wrong')
        with self.assertRaisesRegex(p.Rejected,'copy_input_drift'):self.compose()

    def test_input_membership_missing_or_extra(self):
        (self.dist/'added.txt').unlink()
        with self.assertRaisesRegex(p.Rejected,'artifact_membership_drift'):self.compose()
        (self.dist/'added.txt').write_bytes(b'added');(self.dist/'secret.txt').write_bytes(b'extra')
        with self.assertRaisesRegex(p.Rejected,'artifact_membership_drift'):self.compose()

    def test_membership_change_during_copy(self):
        original=p.stable_bytes;fired=False
        def read(q,**kw):
            nonlocal fired
            raw=original(q,**kw)
            if Path(q)==self.dist/'same.txt' and not fired:
                fired=True;(self.dist/'late.txt').write_bytes(b'late')
            return raw
        with patch.object(p,'stable_bytes',read),self.assertRaisesRegex(p.Rejected,'artifact_membership_race'):self.compose()

    def test_output_content_drift(self):
        original=p.inventory
        def inv(root):
            if Path(root)==self.out:(self.out/'same.txt').write_bytes(b'BAD!')
            return original(root)
        with patch.object(p,'inventory',inv),self.assertRaisesRegex(p.Rejected,'copy_output_drift'):self.compose()

    def test_output_extra_file(self):
        original=p.inventory
        def inv(root):
            if Path(root)==self.out:(self.out/'extra.txt').write_bytes(b'x')
            return original(root)
        with patch.object(p,'inventory',inv),self.assertRaisesRegex(p.Rejected,'copy_output_drift'):self.compose()

    def test_control_path_injection_and_case_alias(self):
        for name in ['tools/private.py','Tools/private.py','.git/config','.release-control/policy.json']:
            row={'path':name,'sha256':'a'*64,'bytes':1}
            with self.subTest(name=name),self.assertRaisesRegex(p.Rejected,'artifact_contains_site_control'):self.compose(artifacts=self.artifacts+[row])
        row={'path':'.git/config','sha256':'a'*64,'bytes':1}
        with self.assertRaisesRegex(p.Rejected,'git_administration'):self.compose(base=self.base+[row])

    def test_hostile_inventory_and_duplicate_rows(self):
        for name in ['../escape','/absolute','x\\y','CON.txt','same.txt','SAME.txt']:
            row={'path':name,'sha256':'a'*64,'bytes':1}
            with self.subTest(name=name),self.assertRaises(p.Rejected):self.compose(artifacts=self.artifacts+[row])

    def test_existing_or_nested_destination_rejected(self):
        self.out.mkdir();(self.out/'sentinel').write_bytes(b'preserve')
        with self.assertRaisesRegex(p.Rejected,'output_exists'):self.compose()
        self.assertEqual((self.out/'sentinel').read_bytes(),b'preserve')
        for root in [self.site,self.dist]:
            with self.assertRaisesRegex(p.Rejected,'output_not_disjoint'):self.compose(out=root/'nested')

    def test_reparse_ancestor_rejected(self):
        original=Path.lstat
        def fake(path):
            result=original(path)
            if Path(path)==self.dist:
                class Reparse:
                    st_mode=result.st_mode
                    st_file_attributes=0x400
                return Reparse()
            return result
        with patch.object(Path,'lstat',fake),self.assertRaisesRegex(p.Rejected,'reparse'):self.compose()

    def test_hardlink_source_rejected(self):
        q=self.dist/'same.txt';os.link(q,self.root/'hardlink')
        with self.assertRaisesRegex(p.Rejected,'not_unique_regular_file'):self.compose()

    def test_permission_error_preserved(self):
        original=Path.lstat
        def blocked(q):
            if Path(q)==self.dist:raise PermissionError('synthetic denied')
            return original(q)
        with patch.object(Path,'lstat',blocked),self.assertRaises(PermissionError):self.compose()

    def test_post_copy_source_drift_requires_unchanged_closing_gate(self):
        self.compose();(self.dist/'same.txt').write_bytes(b'late')
        self.assertNotEqual(p.inventory(self.dist),self.artifacts)
        # Caller verify_promoted still compares this full actual inventory to its
        # sealed rows. Composition is not a replacement for that closing gate.
        (self.site/'gone.txt').write_bytes(b'site changed')
        self.assertNotEqual(p.inventory(self.site),self.base)

    def test_no_old_public_file_is_copied_or_diff_hashed(self):
        seen=[];original=p.stable_bytes
        def read(q,**kw):seen.append(Path(q));return original(q,**kw)
        with patch.object(p,'stable_bytes',read):self.compose()
        old_public={self.site/n for n in self.old if n.split('/')[0] not in rb.SITE_CONTROL}
        self.assertTrue(old_public.isdisjoint(seen))
        for n in self.new:self.assertEqual(seen.count(self.dist/n),1)
        for n in self.old:
            if n.split('/')[0] in rb.SITE_CONTROL:self.assertEqual(seen.count(self.site/n),1)
        self.assertEqual(sum(q.is_relative_to(self.out) for q in seen),len(self.new)+4)

    def test_empty_control_subset_is_valid(self):
        site=self.root/'no-controls';self.put(site,{'old.txt':b'old'})
        self.assertEqual(self.compose(site=site,base=p.inventory(site)),(['added.txt','changed.txt','same.txt'],[],['old.txt']))


if __name__=='__main__':unittest.main()
