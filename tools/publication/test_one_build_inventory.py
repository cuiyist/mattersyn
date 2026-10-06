"""Tiny inventory conformance/fault tests; no production trees or build."""
import concurrent.futures
import hashlib
import os
from pathlib import Path
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest import mock

import one_build as NEW


# The serial scheduling oracle retains the prior algorithm, using the same
# stable-byte primitive. Explicit output/error assertions test the primitive.
OLD = SimpleNamespace(stable_bytes=NEW.stable_bytes, listing=NEW.listing)


def serial_inventory(root):
    paths = OLD.listing(root)
    rows = []
    for name in paths:
        raw = OLD.stable_bytes(Path(root) / name)
        rows.append({'path': name, 'sha256': NEW.digest(raw), 'bytes': len(raw)})
    NEW.require(OLD.listing(root) == paths, 'directory_membership_race')
    return rows


OLD.inventory = serial_inventory


def outcome(fn, root):
    try:
        return ('rows', fn(root))
    except Exception as error:
        return ('error', type(error).__name__, str(error))


class InventoryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='inventory-unit-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()

    def fresh(self, suffix=''):
        path = self.root / ('case' + suffix)
        path.mkdir()
        return path

    def test_exact_binary_unicode_nested_output(self):
        p=self.fresh();(p/'sub dir').mkdir()
        data={'z.bin':bytes(range(256))*16,'empty':b'','sub dir/alpha.txt':b'one\r\ntwo\n','sub dir/caf\u00e9.txt':'angstrom\u00c5'.encode()}
        for n,v in data.items():(p/n).write_bytes(v)
        expected=[{'path':n,'sha256':hashlib.sha256(v).hexdigest(),'bytes':len(v)} for n,v in sorted(data.items())]
        self.assertEqual(OLD.inventory(p),expected)
        self.assertEqual(NEW.inventory(p),expected)

    def test_empty_and_missing_root(self):
        p=self.fresh();self.assertEqual(OLD.inventory(p),NEW.inventory(p))
        self.assertEqual(outcome(OLD.inventory,p/'absent'),outcome(NEW.inventory,p/'absent'))

    def test_four_readers_overlap_but_never_exceed_four(self):
        p=self.fresh()
        for n in range(13):(p/f'{n:02d}').write_bytes(bytes([n])*32)
        reference=OLD.inventory(p);original=NEW.stable_bytes
        barrier=threading.Barrier(4);lock=threading.Lock();state={'entered':0,'active':0,'peak':0,'seen':[]}
        def wrapped(path,*args,**kwargs):
            with lock:
                state['entered']+=1;number=state['entered'];state['active']+=1
                state['peak']=max(state['peak'],state['active']);state['seen'].append(Path(path).name)
            try:
                if number<=4:barrier.wait(timeout=5)
                return original(path,*args,**kwargs)
            finally:
                with lock:state['active']-=1
        with mock.patch.object(NEW,'stable_bytes',wrapped):result=NEW.inventory(p)
        self.assertEqual(result,reference);self.assertEqual(state['peak'],4)
        self.assertEqual(state['active'],0);self.assertEqual(sorted(state['seen']),[f'{n:02d}' for n in range(13)])

    def test_static_failures_report_first_sorted_path(self):
        p=self.fresh()
        for n in ['a','b','c','d']:(p/n).write_bytes(b'x')
        done=threading.Event();original=NEW.stable_bytes
        def parallel(path):
            n=Path(path).name
            if n=='a':
                if not done.wait(5):raise RuntimeError('fixture synchronization failed')
                raise ValueError('fault:a')
            if n=='b':done.set();raise ValueError('fault:b')
            return original(path)
        old_stable = OLD.stable_bytes
        def serial(path):
            if Path(path).name in ['a','b']:raise ValueError('fault:'+Path(path).name)
            return old_stable(path)
        with mock.patch.object(OLD,'stable_bytes',serial):a=outcome(OLD.inventory,p)
        with mock.patch.object(NEW,'stable_bytes',parallel):b=outcome(NEW.inventory,p)
        self.assertEqual(a,b);self.assertEqual(b,('error','ValueError','fault:a'))

    def test_failure_joins_other_readers_before_return(self):
        p=self.fresh();(p/'a').write_bytes(b'a');(p/'b').write_bytes(b'b')
        entered=threading.Event();failed=threading.Event();release=threading.Event();finished=threading.Event()
        original=NEW.stable_bytes
        def wrapped(path):
            if Path(path).name=='a':
                if not entered.wait(5):raise RuntimeError('fixture synchronization failed')
                failed.set();raise ValueError('fault:a')
            entered.set()
            try:
                if not release.wait(5):raise RuntimeError('fixture release timed out')
                return original(path)
            finally:finished.set()
        with mock.patch.object(NEW,'stable_bytes',wrapped),concurrent.futures.ThreadPoolExecutor(max_workers=1) as outer:
            future=outer.submit(outcome,NEW.inventory,p)
            try:
                self.assertTrue(failed.wait(5));self.assertFalse(future.done())
            finally:release.set()
            self.assertEqual(future.result(timeout=5),('error','ValueError','fault:a'))
            self.assertTrue(finished.is_set())

    def test_real_private_hardlink_rejected(self):
        p=self.fresh();(p/'a').write_bytes(b'private fixture only')
        try:os.link(p/'a',p/'b')
        except OSError as e:self.skipTest('Host cannot create private hardlink: '+str(e))
        self.assertEqual(outcome(OLD.inventory,p),outcome(NEW.inventory,p))
        self.assertEqual(outcome(NEW.inventory,p),('error','Rejected','not_unique_regular_file'))

    def test_real_private_symlink_rejected_if_supported(self):
        p=self.fresh();(p/'target').write_bytes(b'private fixture only')
        try:os.symlink(p/'target',p/'link')
        except OSError as e:self.skipTest('Host symlink privilege unavailable: '+str(e))
        self.assertEqual(outcome(OLD.inventory,p),outcome(NEW.inventory,p))
        self.assertEqual(outcome(NEW.inventory,p),('error','Rejected','symlink_or_reparse'))

    def test_real_case_alias_if_supported(self):
        p=self.fresh();(p/'a').write_bytes(b'lower');(p/'A').write_bytes(b'upper')
        if len(list(p.iterdir()))!=2:self.skipTest('Actual test directory is case-insensitive; synthetic enumeration tested separately')
        self.assertEqual(outcome(OLD.inventory,p),outcome(NEW.inventory,p))
        self.assertEqual(outcome(NEW.inventory,p),('error','Rejected','case_colliding_path'))

    def test_synthetic_case_alias_enumeration(self):
        p=self.fresh();(p/'a').write_bytes(b'x');(p/'A').write_bytes(b'x')
        with mock.patch('os.walk',return_value=[(str(p),[],['a','A'])]):
            a=outcome(OLD.inventory,p);b=outcome(NEW.inventory,p)
        self.assertEqual(a,b);self.assertEqual(b,('error','Rejected','case_colliding_path'))

    def test_synthetic_reparse_attribute_branch(self):
        p=self.fresh();f=p/'file';f.write_bytes(b'x');original=Path.lstat
        def injected(path,*a,**kw):
            s=original(path,*a,**kw)
            if path==f:return SimpleNamespace(st_mode=s.st_mode,st_file_attributes=getattr(s,'st_file_attributes',0)|0x400)
            return s
        with mock.patch.object(Path,'lstat',injected):
            a=outcome(OLD.inventory,p);b=outcome(NEW.inventory,p)
        self.assertEqual(a,b);self.assertEqual(b,('error','Rejected','symlink_or_reparse'))

    def test_real_special_file_if_supported(self):
        p=self.fresh()
        if not hasattr(os,'mkfifo'):self.skipTest('Host has no mkfifo; special-file branch tested with synthetic type observation')
        os.mkfifo(p/'fifo')
        self.assertEqual(outcome(OLD.inventory,p),outcome(NEW.inventory,p))
        self.assertEqual(outcome(NEW.inventory,p),('error','Rejected','special_file'))

    def test_synthetic_special_file_type(self):
        p=self.fresh();f=p/'special';f.write_bytes(b'x');old_file=Path.is_file;old_dir=Path.is_dir
        with mock.patch.object(Path,'is_file',lambda x:False if x==f else old_file(x)),mock.patch.object(Path,'is_dir',lambda x:False if x==f else old_dir(x)):
            a=outcome(OLD.inventory,p);b=outcome(NEW.inventory,p)
        self.assertEqual(a,b);self.assertEqual(b,('error','Rejected','special_file'))

    def test_noncanonical_unicode_rejected(self):
        p=self.fresh();(p/'e\u0301.txt').write_bytes(b'x')
        self.assertEqual(outcome(OLD.inventory,p),outcome(NEW.inventory,p))
        self.assertEqual(outcome(NEW.inventory,p),('error','Rejected','noncanonical_unicode_path'))

    def test_add_and_remove_membership_between_censuses(self):
        for mutation in ['add','remove']:
            results=[]
            for k,m in enumerate([OLD,NEW]):
                p=self.fresh(mutation+str(k));(p/'a').write_bytes(b'a');(p/'b').write_bytes(b'b')
                original=m.listing;calls=0
                def injected(root):
                    nonlocal calls
                    calls+=1
                    if calls==2:
                        if mutation=='add':(p/'extra').write_bytes(b'new')
                        else:(p/'b').unlink()
                    return original(root)
                with mock.patch.object(m,'listing',injected):results.append(outcome(m.inventory,p))
            self.assertEqual(results[0],results[1]);self.assertEqual(results[1],('error','Rejected','directory_membership_race'))

    def test_actual_inplace_mutation_between_stable_reads(self):
        results=[]
        for k,m in enumerate([OLD,NEW]):
            p=self.fresh(str(k));target=p/'a';target.write_bytes(b'abcd');original_open=Path.open
            class Proxy:
                def __init__(self,f):self.f=f;self.n=0
                def __enter__(self):self.f.__enter__();return self
                def __exit__(self,*args):return self.f.__exit__(*args)
                def fileno(self):return self.f.fileno()
                def seek(self,*args):return self.f.seek(*args)
                def read(self,*args):
                    raw=self.f.read(*args);self.n+=1
                    if self.n==1:
                        with original_open(target,'r+b') as writer:writer.write(b'Xbcd');writer.flush();os.fsync(writer.fileno())
                    return raw
            def injected(path,*args,**kwargs):
                f=original_open(path,*args,**kwargs)
                return Proxy(f) if path==target and args and args[0]=='rb' else f
            with mock.patch.object(Path,'open',injected):results.append(outcome(m.inventory,p))
        self.assertEqual(results[0],results[1]);self.assertEqual(results[1],('error','Rejected','file_changed_during_read'))

    def test_permission_error_object_and_errno_preserved(self):
        failure = PermissionError(13, 'fixture denied')
        with mock.patch.object(NEW, 'listing', return_value=['a']), \
                mock.patch.object(NEW, 'stable_bytes', side_effect=failure):
            with self.assertRaises(PermissionError) as caught:
                NEW.inventory(self.root)
        self.assertIs(caught.exception, failure)
        self.assertEqual(caught.exception.errno, 13)

    def test_partial_submission_failure_joins_and_preserves_error(self):
        release = threading.Event()
        done = []
        lock = threading.Lock()
        failure = OSError(11, 'fixture submission failure')
        test = self

        class FailingPool:
            def __init__(self, max_workers):
                test.assertEqual(max_workers, 4)
                self.inner = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
                self.count = 0

            def __enter__(self):
                return self

            def submit(self, fn, value):
                self.count += 1
                if self.count == 3:
                    release.set()
                    raise failure
                return self.inner.submit(fn, value)

            def __exit__(self, *args):
                self.inner.shutdown(wait=True)

        def read(path):
            if not release.wait(5):
                raise AssertionError('fixture release timed out')
            time.sleep(0.015)
            with lock:
                done.append(path.name)
            return b'fixture'

        with mock.patch.object(NEW, 'listing', return_value=list('abcd')), \
                mock.patch.object(NEW, 'stable_bytes', side_effect=read), \
                mock.patch.object(NEW, 'ThreadPoolExecutor', FailingPool):
            with self.assertRaises(OSError) as caught:
                NEW.inventory(self.root)
        self.assertIs(caught.exception, failure)
        self.assertEqual(sorted(done), ['a', 'b'])

    def test_closing_census_after_all_readers_and_exactly_two_censuses(self):
        calls = []
        completed = []
        lock = threading.Lock()

        def read(path):
            with lock:
                completed.append(path.name)
            return path.name.encode('ascii')

        def listing(root):
            calls.append(True)
            if len(calls) == 2:
                self.assertEqual(sorted(completed), list('abcde'))
            return list('abcde')

        with mock.patch.object(NEW, 'listing', side_effect=listing), \
                mock.patch.object(NEW, 'stable_bytes', side_effect=read):
            rows = NEW.inventory(self.root)
        self.assertEqual(len(calls), 2)
        self.assertEqual(rows, [
            {'path': name, 'sha256': hashlib.sha256(name.encode()).hexdigest(), 'bytes': 1}
            for name in 'abcde'])


if __name__ == '__main__':
    unittest.main()
