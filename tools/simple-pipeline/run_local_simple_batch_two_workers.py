"""Two-paper local orchestration; extraction and checks stay in the existing script.

This file never starts/stops a model server and never integrates or releases records.
Each child runs the unchanged script, whose A/B calls remain sequential. Two child
workers therefore allow at most two local model requests at a time.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import threading
import time
import traceback


_DIRECTORY_CREATION_LOCK = threading.Lock()


def make_directory(path):
    # Serialize first-use nested mkdir on Windows; paper payload writes stay disjoint.
    with _DIRECTORY_CREATION_LOCK:
        Path(path).mkdir(parents=True, exist_ok=True)


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def invalid_passes(work, stem):
    """The exact predicate used by the existing production controller/check."""
    bad = []
    for letter in ('A', 'B'):
        path = Path(work) / f'{stem}.pass{letter}.json'
        try:
            data = json.loads(path.read_text(encoding='utf8'))
            good = (isinstance(data, dict) and 'error' not in data and isinstance(data.get('pairs'), list)
                    and all(isinstance(pair, dict) for pair in data['pairs']))
        except (OSError, UnicodeError, json.JSONDecodeError):
            good = False
        if not good:
            bad.append(letter)
    return bad


def same_bytes(a, b):
    return a.stat().st_size == b.stat().st_size and hashlib.sha256(a.read_bytes()).digest() == hashlib.sha256(b.read_bytes()).digest()


def preserve_files(files, destination):
    """Preserve every prior byte; never overwrite a different earlier snapshot."""
    if os.name == 'nt':
        absolute = os.path.abspath(destination)
        if not absolute.startswith('\\\\?\\'):
            absolute = ('\\\\?\\UNC\\' + absolute[2:] if absolute.startswith('\\\\')
                        else '\\\\?\\' + absolute)
        destination = Path(absolute)
    files = [p for p in files if p.is_file()]
    if not files:
        return
    make_directory(destination)
    for source in files:
        target = destination / source.name
        ordinal = 2
        while target.exists() and not same_bytes(source, target):
            target = destination / f'{source.name}.preserved-{ordinal}'
            ordinal += 1
        if not target.exists():
            shutil.copy2(source, target)


class BatchLock:
    """An OS file lock prevents two instances from owning this batch at once.

    The tiny lock file is retained; the OS releases ownership even on a crash.
    Existing serial controllers do not participate, so root must still finish
    the old controller before selecting this replacement.
    """
    def __init__(self, batch):
        self.path = Path(batch) / '.controller-two-workers.lock'
        self.stream = None

    def __enter__(self):
        self.stream = self.path.open('a+b')
        if self.path.stat().st_size == 0:
            self.stream.write(b'0'); self.stream.flush()
        self.stream.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(self.stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            self.stream.close(); self.stream = None
            raise RuntimeError('Another two-worker coordinator owns this batch') from error
        return self

    def __exit__(self, *exc):
        if self.stream:
            self.stream.seek(0)
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(self.stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.stream.fileno(), fcntl.LOCK_UN)
            self.stream.close(); self.stream = None


class StateWriter:
    """All shared progress writes are confined to the coordinator's thread."""
    def __init__(self, batch, summary, server_pid, work):
        self.batch, self.summary = batch, summary
        self.server_pid, self.work = server_pid, work
        self.owner_thread = threading.get_ident()
        self.write_threads = set()
        self.active = {}
        self.last_written = 0.0

    def write(self, phase, **extra):
        if threading.get_ident() != self.owner_thread:
            raise RuntimeError('Only the coordinator may write progress files')
        self.write_threads.add(threading.get_ident())
        state = {'phase': phase, 'updated_at_utc': utc(), 'controller_pid': os.getpid(),
                 'server_pid': self.server_pid, 'workdir': str(self.work),
                 'successful_two_pass_papers': self.summary['successful_two_pass_papers'],
                 'next_action': 'continue current batch, then root handoff',
                 'active_children': list(self.active.values()), 'maximum_paper_workers': 2, **extra}
        for target, content in ((self.batch / 'processing-summary.json', self.summary),
                                (self.batch / 'run-state.json', state)):
            temporary = target.with_name(target.name + '.tmp')
            temporary.write_text(json.dumps(content, indent=2), encoding='utf8')
            os.replace(temporary, target)
        self.last_written = time.monotonic()


class Coordinator:
    def __init__(self, batch, script, server_pid, model='qwen3-32b', *, manifest=None, trusted_meta=None):
        self.batch, self.script = Path(batch), Path(script)
        self.server_pid, self.model = server_pid, model
        self.manifest_path = Path(manifest) if manifest is not None else self.batch / 'identity-supported-manifest.json'
        self.trusted_meta = Path(trusted_meta) if trusted_meta is not None else self.batch / 'trusted-meta'
        self.manifest = json.loads(self.manifest_path.read_text(encoding='utf8'))
        self.cohort = json.loads((self.batch / 'manifest.json').read_text(encoding='utf8'))
        self.papers = self.manifest['papers']
        keys = [p['doi'] for p in self.papers]
        stems = [Path(p['batch_pdf_path']).stem.casefold() for p in self.papers]
        if len(set(keys)) != len(keys) or len(set(stems)) != len(stems):
            raise ValueError('Duplicate DOI/PDF stem would collide in worker output ownership')
        self.work, self.pairs = self.batch / 'work', self.batch / 'pairs'
        defaults = {'cohort_papers': len(self.cohort['papers']), 'generation_papers': len(self.papers),
                    'identity_holds': [p['doi'] for p in self.cohort['papers'] if p['doi'] not in set(keys)],
                    'retry_papers': [], 'left_out': [], 'successful_two_pass_papers': 0,
                    'figures_failures': [], 'extract_started_utc': utc(),
                    'original_failed_pass_executions': 0, 'redo_failed_pass_executions': 0,
                    'extraction_results': {}, 'figure_completed_dois': []}
        summary_path = self.batch / 'processing-summary.json'
        old = json.loads(summary_path.read_text(encoding='utf8')) if summary_path.exists() else {}
        self.summary = {**defaults, **old}
        # Existing serial-controller progress is a manifest-order prefix.
        if not self.summary['extraction_results'] and old.get('completed_generation_papers'):
            left_out = {row['doi'] for row in self.summary['left_out']}
            for paper in self.papers[:old['completed_generation_papers']]:
                bad = invalid_passes(self.work, Path(paper['batch_pdf_path']).stem)
                if not bad or paper['doi'] in left_out:
                    self.summary['extraction_results'][paper['doi']] = {'doi': paper['doi'], 'valid': not bad,
                                                                        'reused_saved_result': True, 'failed_passes': bad}
        self.events = queue.Queue()
        self.writer = StateWriter(self.batch, self.summary, server_pid, self.work)
        self.env = dict(os.environ)
        for key in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy'):
            self.env.pop(key, None)
        self.env['NO_PROXY'] = '127.0.0.1,localhost,::1'; self.env['PYTHONUTF8'] = '1'
        self._refresh_counts()

    def _refresh_counts(self):
        results = self.summary['extraction_results']
        self.summary['successful_two_pass_papers'] = sum(bool(r['valid']) for r in results.values())
        self.summary['completed_generation_papers'] = len(results)

    def _command(self, phase, paper, arguments):
        stem = Path(paper['batch_pdf_path']).stem
        log = self.batch / 'logs' / phase / f'{stem}.console.log'
        make_directory(log.parent)
        command = [sys.executable, '-X', 'utf8', '-B', '-u', str(self.script), *arguments]
        with log.open('a', encoding='utf8') as output:
            child = subprocess.Popen(command, stdout=output, stderr=subprocess.STDOUT, env=self.env)
            self.events.put({'type': 'started', 'doi': paper['doi'], 'phase': phase,
                             'child_pid': child.pid, 'command_started_utc': utc(), 'log': str(log)})
            code = child.wait()
        self.events.put({'type': 'ended', 'doi': paper['doi'], 'phase': phase, 'child_pid': child.pid,
                         'exit_code': code, 'log': str(log)})
        return code

    def _extract(self, paper):
        doi, pdf = paper['doi'], Path(paper['batch_pdf_path'])
        stem = pdf.stem
        preserve_files([p for p in self.work.iterdir() if p.name.startswith(stem + '.')],
                       self.batch / 'reused-originals' / stem / 'before-command')
        code = self._command('extract', paper, ['extract', str(pdf), '--out', str(self.work), '--model', self.model])
        bad = invalid_passes(self.work, stem)
        redo_bad, redo_done = [], False
        if bad:
            answer = queue.Queue(maxsize=1)
            self.events.put({'type': 'retry_request', 'doi': doi, 'bad': bad, 'answer': answer})
            if answer.get():
                preserve_files([p for p in self.work.iterdir() if p.name.startswith(stem + '.')],
                               self.batch / 'retries' / stem / 'before-redo')
                code = self._command('extract', paper, ['extract', str(pdf), '--out', str(self.work),
                                                      '--model', self.model, '--redo'])
                bad = invalid_passes(self.work, stem)
                redo_bad, redo_done = list(bad), True
        return {'doi': doi, 'valid': not bad, 'failed_passes': bad, 'redo_performed': redo_done,
                'redo_failed_passes': redo_bad, 'last_exit_code': code}

    def _figures(self, paper):
        code = self._command('figures', paper, ['figures', paper['batch_pdf_path'], '--out', str(self.work),
                                               '--model', self.model])
        return {'doi': paper['doi'], 'exit_code': code}

    def _event(self, event, phase):
        doi, kind = event['doi'], event['type']
        if kind == 'started':
            self.writer.active[doi] = {k: v for k, v in event.items() if k != 'type'}
        elif kind == 'ended':
            self.writer.active.pop(doi, None)
            self.summary['last_child_exit_code'] = event['exit_code']
        elif kind == 'retry_request':
            allowed = doi not in self.summary['retry_papers']
            if allowed:
                self.summary['original_failed_pass_executions'] += len(event['bad'])
                self.summary['retry_papers'].append(doi)
            # Persist the one-redo reservation before the worker can act.
            self.writer.write(phase)
            event['answer'].put(allowed)
            return
        self.writer.write(phase)

    def _pool(self, phase, papers, worker):
        with ThreadPoolExecutor(max_workers=2, thread_name_prefix='paper-worker') as executor:
            futures = {executor.submit(worker, paper): paper for paper in papers}
            pending = set(futures)
            while pending:
                try:
                    self._event(self.events.get(timeout=0.1), phase)
                except queue.Empty:
                    pass
                for future in tuple(pending):
                    if not future.done():
                        continue
                    paper = futures[future]
                    try:
                        result = future.result()
                    except Exception as error:
                        error_log = self.batch / 'logs' / phase / f"{Path(paper['batch_pdf_path']).stem}.console.log"
                        make_directory(error_log.parent)
                        with error_log.open('a', encoding='utf8') as output:
                            output.write('\nOrchestration exception (private diagnostics):\n' + traceback.format_exc())
                        result = {'doi': paper['doi'], 'valid': False, 'failed_passes': [],
                                  'exit_code': -1, 'error_type': type(error).__name__}
                    if phase == 'extract':
                        self.summary['extraction_results'][paper['doi']] = result
                        self.summary['redo_failed_pass_executions'] += len(result.get('redo_failed_passes', []))
                        if not result['valid'] and not any(x['doi'] == paper['doi'] for x in self.summary['left_out']):
                            self.summary['left_out'].append({'doi': paper['doi'],
                                'reason': 'extract_orchestration_error' if result.get('error_type') else 'invalid_or_failed_pass_after_one_redo',
                                'failed_passes': result['failed_passes'], **({'error_type': result['error_type']} if result.get('error_type') else {})})
                        self._refresh_counts()
                    else:
                        self.summary['figure_completed_dois'].append(paper['doi'])
                        if result['exit_code']:
                            self.summary['figures_failures'].append({'doi': paper['doi'], 'exit_code': result['exit_code'],
                                **({'error_type': result['error_type']} if result.get('error_type') else {})})
                    with (self.batch / f'{phase}.console.log').open('a', encoding='utf8') as output:
                        output.write(json.dumps(result) + '\n')
                    pending.remove(future)
                    self.writer.write(phase)
                if time.monotonic() - self.writer.last_written > 60:
                    self.writer.write(phase)
            # A worker exit event can be queued just before its future completes.
            while not self.events.empty():
                self._event(self.events.get_nowait(), phase)

    def run(self):
        with BatchLock(self.batch):
            return self._run_owned()

    def _run_owned(self):
        self.work.mkdir(exist_ok=True); self.pairs.mkdir(exist_ok=True)
        for meta in self.trusted_meta.glob('*.meta.json'):
            if (self.work / meta.name).exists():
                preserve_files([self.work / meta.name], self.batch / 'reused-originals' / meta.stem / 'before-command')
            shutil.copy2(meta, self.work / meta.name)
        started = time.monotonic()
        self.writer.write('extract')
        remaining = [p for p in self.papers if p['doi'] not in self.summary['extraction_results']]
        self._pool('extract', remaining, self._extract)
        self.summary['extract_wall_minutes'] = round(self.summary.get('extract_wall_minutes', 0) +
                                                    (time.monotonic() - started) / 60, 4)
        self.summary['extract_finished_utc'] = utc()
        successful = [p for p in self.papers if self.summary['extraction_results'][p['doi']]['valid']]
        figures = [p for p in successful if p['doi'] not in self.summary['figure_completed_dois']]
        self._pool('figures', figures, self._figures)
        preserve_files(list(self.pairs.glob('*.pairs.json')), self.pairs / 'originals-before-check')
        check_command = [sys.executable, '-X', 'utf8', '-B', '-u', str(self.script),
                         'check', str(self.work), '--out', str(self.pairs)]
        self.writer.write('check')
        with (self.batch / 'check.console.log').open('a', encoding='utf8') as output:
            child = subprocess.Popen(check_command, stdout=output, stderr=subprocess.STDOUT, env=self.env)
            self.writer.active['check'] = {'phase': 'check', 'child_pid': child.pid, 'command_started_utc': utc()}
            self.writer.write('check')
            self.summary['check_exit_code'] = child.wait()
            self.writer.active.pop('check', None)
        self.summary['pair_files'] = len(list(self.pairs.glob('*.pairs.json')))
        self.summary['figures_found'] = sum(len(json.loads(p.read_text(encoding='utf8'))) for p in self.work.glob('*.figures.json'))
        self.summary['finished_at_utc'] = utc()
        self.summary['coordinator'] = {'paper_workers': 2, 'state_writers': len(self.writer.write_threads),
                                       'server_management': 'none; root owns server startup/capacity verification'}
        self.writer.write('batch processing complete', next_action='root identity verification and ordinary site integration')
        print(json.dumps(self.summary), flush=True)
        return self.summary['check_exit_code']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch', type=Path, required=True)
    parser.add_argument('--script', type=Path, required=True)
    parser.add_argument('--server-pid', type=int, required=True)
    parser.add_argument('--model', default='qwen3-32b')
    parser.add_argument('--manifest', type=Path, help='Supported identity manifest; default: <batch>/identity-supported-manifest.json')
    parser.add_argument('--trusted-meta', type=Path, help='DOI-only metadata directory; default: <batch>/trusted-meta')
    args = parser.parse_args()
    return Coordinator(args.batch, args.script, args.server_pid, args.model,
                       manifest=args.manifest, trusted_meta=args.trusted_meta).run()


if __name__ == '__main__':
    raise SystemExit(main())
