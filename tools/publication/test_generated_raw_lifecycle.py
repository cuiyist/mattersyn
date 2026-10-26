"""Portable fake-filesystem tests for the normal release tool's fresh raw lifecycle.

No test creates, reads, or deletes a real generated build tree. The module under
test is the normal sibling release_batch, not a copy of its implementation.
"""
from pathlib import PurePosixPath
import stat
from types import SimpleNamespace
import unittest
from unittest import mock

import release_batch as rb


class FakePath:
    def __init__(self, fs, path):
        self.fs, self.path = fs, PurePosixPath(path)

    def __str__(self): return str(self.path)
    def __truediv__(self, other): return FakePath(self.fs, self.path / other)
    def __eq__(self, other): return isinstance(other, FakePath) and self.path == other.path
    def __hash__(self): return hash(self.path)
    @property
    def parent(self): return FakePath(self.fs, self.path.parent)
    def is_absolute(self): return self.path.is_absolute()
    def is_relative_to(self, other): return self.path.is_relative_to(other.path)

    def resolve(self, strict=False):
        value = str(self)
        for original, target in self.fs.aliases.items():
            if value == original or value.startswith(original + '/'):
                value = target + value[len(original):]
                break
        result = FakePath(self.fs, value)
        if strict: result.lstat()
        return result

    def lstat(self):
        try: return self.fs.nodes[str(self)]
        except KeyError: raise FileNotFoundError(str(self)) from None

    def exists(self): return str(self) in self.fs.nodes
    def mkdir(self, parents=False, exist_ok=False):
        if self.exists() and not exist_ok: raise FileExistsError(str(self))
        if not self.parent.exists(): raise FileNotFoundError(str(self.parent))
        self.fs.add(str(self))


class FakeFS:
    def __init__(self):
        self.nodes, self.aliases, self.events, self.scanned = {}, {}, [], []
        self.next_inode = 100
        self.fail_removal_number = None
        for path in ('/workspace', '/workspace/fresh', '/source', '/site'):
            self.add(path)
        self.add('/source/original', directory=False)

    def path(self, path): return FakePath(self, path)

    def add(self, path, directory=True):
        self.next_inode += 1
        value = SimpleNamespace(st_mode=stat.S_IFDIR if directory else stat.S_IFREG,
                                st_dev=1, st_ino=self.next_inode, st_nlink=1,
                                st_file_attributes=0)
        self.nodes[path] = value
        return value

    def build(self, phase):
        prefix = '/workspace/fresh/' + phase
        for suffix in ('', '/project', '/project/tools', '/project/recipe-atlas',
                       '/project/recipe-atlas/dist'):
            self.add(prefix + suffix)
        for name in ('scripts', 'templates', 'data', 'static', 'tests'):
            self.add(prefix + '/project/recipe-atlas/' + name)
            self.add(prefix + '/project/recipe-atlas/' + name + '/input', directory=False)
        for name in ('candidate-manifest.json', 'snapshot.json', 'child.log',
                     'project/README.md', 'project/recipe-atlas/dist/index.html'):
            self.add(prefix + '/' + name, directory=False)

    def explicit_stat(self, path, *, follow_symlinks):
        if follow_symlinks is not False: raise AssertionError('stat must not follow links')
        self.events.append(('explicit_stat', str(path)))
        return path.lstat()

    def scandir(self, path):
        self.scanned.append(str(path))
        fs = self
        class Entries:
            def __enter__(self):
                entries = []
                for name in fs.nodes:
                    if PurePosixPath(name).parent == path.path:
                        # Reproduce the Windows cached nlink=0. Correct code must
                        # use explicit_stat rather than trust this cached result.
                        cached = SimpleNamespace(**{**vars(fs.nodes[name]), 'st_nlink': 0})
                        def cached_stat(*, follow_symlinks, value=cached, name=name):
                            fs.events.append(('cached_stat', name))
                            return value
                        entries.append(SimpleNamespace(name=PurePosixPath(name).name, stat=cached_stat))
                return iter(entries)
            def __exit__(self, *args): pass
        return Entries()

    def rmtree(self, root):
        removed = [event for event in self.events if event[0] == 'remove']
        if self.fail_removal_number == len(removed): raise OSError('injected removal failure')
        self.events.append(('remove', str(root)))
        prefix = str(root)
        self.nodes = {name: value for name, value in self.nodes.items()
                      if name != prefix and not name.startswith(prefix + '/')}


class FreshRawLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.fs = FakeFS()
        # Replace only this module's references; never patch process-global OS
        # functions or let fake paths reach the real filesystem.
        self.os = SimpleNamespace(scandir=self.fs.scandir, stat=self.fs.explicit_stat)
        self.shutil = SimpleNamespace(rmtree=self.fs.rmtree)
        for name, value in (('os', self.os), ('shutil', self.shutil)):
            patcher = mock.patch.object(rb, name, value)
            patcher.start(); self.addCleanup(patcher.stop)

    def reset_fs(self):
        self.fs = FakeFS()
        self.os.scandir, self.os.stat = self.fs.scandir, self.fs.explicit_stat
        self.shutil.rmtree = self.fs.rmtree

    def engine(self):
        return rb._FreshRawCopies(self.fs.path('/workspace/fresh'), self.fs.path('/workspace'))

    def prepared(self):
        engine = self.engine(); engine.arm('candidate'); self.fs.build('candidate')
        return engine

    def removals(self): return [path for event, path in self.fs.events if event == 'remove']

    def test_both_completed_children_retire_only_their_five_raw_inputs(self):
        engine = self.engine()
        for phase in ('candidate', 'final'):
            engine.arm(phase); self.fs.build(phase); engine.retire(phase)
            self.assertEqual(engine.states[phase], 'retired')
            for name in ('candidate-manifest.json', 'snapshot.json', 'child.log',
                         'project/README.md', 'project/recipe-atlas/dist/index.html'):
                self.assertIn('/workspace/fresh/' + phase + '/' + name, self.fs.nodes)
        self.assertEqual(self.removals(), ['/workspace/fresh/' + phase + '/project/recipe-atlas/' + name
                                          for phase in ('candidate', 'final')
                                          for name in ('scripts', 'templates', 'data', 'static', 'tests')])
        self.assertIn('/source/original', self.fs.nodes)

    def test_explicit_stat_supersedes_windows_cached_link_zero(self):
        engine = self.prepared()
        with self.fs.scandir(self.fs.path('/workspace/fresh/candidate/project/recipe-atlas/data')) as entries:
            self.assertEqual(next(entries).stat(follow_symlinks=False).st_nlink, 0)
        self.fs.events.clear()
        engine.retire('candidate')
        self.assertEqual(len([e for e in self.fs.events if e[0] == 'explicit_stat']), 5)
        self.assertFalse(any(e[0] == 'cached_stat' for e in self.fs.events))

    def test_invalid_leaf_in_last_tree_prevents_every_removal(self):
        for field, value in (('st_nlink', 0), ('st_nlink', 2), ('st_mode', stat.S_IFLNK),
                             ('st_mode', stat.S_IFIFO), ('st_file_attributes', 1024)):
            with self.subTest(field=field, value=value):
                self.reset_fs()
                engine = self.prepared()
                setattr(self.fs.nodes['/workspace/fresh/candidate/project/recipe-atlas/tests/input'], field, value)
                with self.assertRaises(SystemExit): engine.retire('candidate')
                self.assertEqual(self.removals(), [])

    def test_reparse_directory_is_not_traversed(self):
        engine = self.prepared()
        self.fs.add('/workspace/fresh/candidate/project/recipe-atlas/data/junction').st_file_attributes = 1024
        with self.assertRaises(SystemExit): engine.retire('candidate')
        self.assertNotIn('/workspace/fresh/candidate/project/recipe-atlas/data/junction', self.fs.scanned)
        self.assertEqual(self.removals(), [])

    def test_missing_raw_tree_or_retained_dist_blocks(self):
        for name in ('data', 'dist'):
            with self.subTest(name=name):
                self.reset_fs(); engine = self.prepared()
                del self.fs.nodes['/workspace/fresh/candidate/project/recipe-atlas/' + name]
                with self.assertRaises(FileNotFoundError): engine.retire('candidate')
                self.assertEqual(self.removals(), [])

    def test_existing_unarmed_unknown_and_repeated_phases_block(self):
        engine = self.engine(); self.fs.build('candidate')
        with self.assertRaises(SystemExit): engine.arm('candidate')
        with self.assertRaises(SystemExit): engine.retire('final')
        with self.assertRaises(SystemExit): engine.arm('../source')
        engine.arm('final')
        with self.assertRaises(SystemExit): engine.arm('final')
        self.assertEqual(self.removals(), [])

    def test_workspace_is_explicit_absolute_and_work_is_strictly_inside(self):
        for work, workspace in (('/workspace/fresh', None), ('/workspace/fresh', 'relative'),
                                ('/other/fresh', '/workspace'), ('/workspace', '/workspace')):
            with self.subTest(work=work, workspace=workspace):
                with self.assertRaises(SystemExit):
                    rb._raw_work_scope(self.fs.path(work), None if workspace is None else self.fs.path(workspace))
        self.assertEqual(self.removals(), [])

    def test_aliased_workspace_work_and_fixed_target_block(self):
        for original, replacement in (('/workspace', '/other'), ('/workspace/fresh', '/other/fresh'),
                                      ('/workspace/fresh/candidate/project/recipe-atlas/data', '/other/data')):
            with self.subTest(original=original):
                self.reset_fs(); engine = self.prepared()
                for path in ('/other', '/other/fresh', '/other/data'): self.fs.add(path)
                self.fs.aliases[original] = replacement
                with self.assertRaises(SystemExit): engine.retire('candidate')
                self.assertEqual(self.removals(), [])

    def test_reparse_ancestor_and_changed_work_or_workspace_identity_block(self):
        self.fs.add('/workspace/nested').st_file_attributes = 1024
        with self.assertRaises(SystemExit):
            rb._raw_work_scope(self.fs.path('/workspace/nested/fresh'), self.fs.path('/workspace'))
        for path in ('/workspace', '/workspace/fresh'):
            with self.subTest(path=path):
                self.reset_fs(); engine = self.prepared(); self.fs.nodes[path].st_ino += 1
                with self.assertRaises(SystemExit): engine.retire('candidate')
                self.assertEqual(self.removals(), [])

    def test_partial_removal_failure_cannot_be_replayed(self):
        engine = self.prepared(); self.fs.fail_removal_number = 1
        with self.assertRaises(OSError): engine.retire('candidate')
        self.assertEqual(len(self.removals()), 1)
        self.assertEqual(engine.states['candidate'], 'retiring')
        with self.assertRaises(SystemExit): engine.retire('candidate')
        self.assertEqual(len(self.removals()), 1)

    def test_normal_main_orders_retirement_after_success_before_next_child(self):
        self.check_main_build_boundary(fail_child=False)

    def test_failed_child_keeps_partial_output_and_never_retires_it(self):
        self.check_main_build_boundary(fail_child=True)

    def test_feature_off_keeps_existing_raw_copy_lifetime(self):
        self.check_main_build_boundary(fail_child=False, enabled=False)

    def test_workspace_argument_without_opt_in_blocks_before_build(self):
        args = SimpleNamespace(source=self.fs.path('/source'), site=self.fs.path('/site'),
                               work=self.fs.path('/workspace/fresh'), raw_workspace=self.fs.path('/workspace'),
                               retire_generated_raw=False, phase_budget=None)
        with mock.patch.object(rb.argparse.ArgumentParser, 'parse_args', return_value=args), \
                mock.patch.object(rb, 'run', side_effect=AssertionError('no child may start')):
            with self.assertRaisesRegex(SystemExit, 'requires raw retirement or phase budgets'): rb.main()
        self.assertEqual(self.removals(), [])

    def check_main_build_boundary(self, fail_child, enabled=True):
        del self.fs.nodes['/workspace/fresh']
        args = SimpleNamespace(source=self.fs.path('/source'), site=self.fs.path('/site'),
                               work=self.fs.path('/workspace/fresh'),
                               raw_workspace=self.fs.path('/workspace') if enabled else None,
                               retire_generated_raw=enabled, push=False, verify=False, skip_ci_check=False,
                               source_repo='example/source', wait_ci=0, sync_gate_tools=False,
                               release_id='unit-fixture', reviewer='unit-reviewer', phase_budget=None)
        class StopAfterBothBuilds(Exception): pass
        def git(repo, *options):
            return '' if options[0] == 'status' else 'a' * 40
        def run(argv, cwd=None):
            strings = [str(value) for value in argv]
            name = next((value for value in strings if value.endswith('.py')), '')
            if name.endswith('/build_release.py'):
                phase = 'candidate' if '--candidate' in strings else 'final'
                self.fs.events.append(('build_start', phase)); self.fs.build(phase)
                if fail_child: raise SystemExit('injected child failure')
                self.fs.events.append(('build_zero', phase))
            elif name.endswith('/prepare_allowlist.py'):
                self.fs.events.append(('allowlist', 'candidate dist'))
            return ''
        with mock.patch.object(rb.argparse.ArgumentParser, 'parse_args', return_value=args), \
                mock.patch.object(rb, 'git', side_effect=git), \
                mock.patch.object(rb, 'wait_for_ci', return_value=(True, [])), \
                mock.patch.object(rb, 'run', side_effect=run), \
                mock.patch.object(rb, 'tree_digest', side_effect=StopAfterBothBuilds):
            with self.assertRaises(SystemExit if fail_child else StopAfterBothBuilds): rb.main()
        events = [event for event in self.fs.events if event[0] != 'explicit_stat']
        if fail_child:
            self.assertEqual(events, [('build_start', 'candidate')])
            self.assertIn('/workspace/fresh/candidate/project/recipe-atlas/data/input', self.fs.nodes)
        elif not enabled:
            self.assertEqual(events, [('build_start', 'candidate'), ('build_zero', 'candidate'),
                                      ('allowlist', 'candidate dist'), ('build_start', 'final'), ('build_zero', 'final')])
            for phase in ('candidate', 'final'):
                self.assertIn('/workspace/fresh/' + phase + '/project/recipe-atlas/data/input', self.fs.nodes)
        else:
            self.assertEqual(events[:2], [('build_start', 'candidate'), ('build_zero', 'candidate')])
            self.assertTrue(all(event[0] == 'remove' for event in events[2:7]))
            self.assertEqual(events[7:10], [('allowlist', 'candidate dist'), ('build_start', 'final'), ('build_zero', 'final')])
            self.assertTrue(all(event[0] == 'remove' for event in events[10:15]))
            self.assertEqual(len(events), 15)


if __name__ == '__main__':
    unittest.main()
