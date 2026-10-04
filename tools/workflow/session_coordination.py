"""Local cross-session claims and immutable event inbox, never audit acceptance.

Only the integrator writes the authoritative scientific/publication ledgers.
The coordination lock uses exclusive file creation; stale locks require explicit
operator recovery, never automatic timeout stealing. All state stays private.
"""
from __future__ import annotations
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import time
import uuid

ACTIVE = {'claimed', 'extraction', 'frozen', 'audit', 'correction'}
TERMINAL = {'ready', 'held', 'skipped'}
KINDS = ACTIVE | TERMINAL | {'activity_started', 'activity_finished', 'handoff'}

def now():
    return datetime.now(timezone.utc).isoformat()

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def normalize_doi(value):
    value = value.strip().lower()
    for prefix in ('https://doi.org/', 'http://doi.org/', 'doi:'):
        if value.startswith(prefix):
            value = value[len(prefix):].strip()
    if not re.fullmatch(r'10\.\d{4,9}/\S+', value):
        raise ValueError('a primary DOI is required; ambiguous identity is a hold')
    return value

def key(doi):
    return hashlib.sha256(normalize_doi(doi).encode()).hexdigest()[:24]

def write_new(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.partial')
    try:
        with temporary.open('x', encoding='utf-8', newline='\n') as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)
            f.write('\n'); f.flush(); os.fsync(f.fileno())
        # Atomic create without replacement on NTFS and POSIX. A failed write
        # never exposes an incomplete claim/event to another process.
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)

@contextmanager
def lock(root, timeout=15):
    root.mkdir(parents=True, exist_ok=True)
    p = root / '.coordination.lock'
    deadline = time.monotonic() + timeout
    while True:
        try:
            fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise RuntimeError('coordination lock busy; report to integrator, do not delete it')
            time.sleep(0.05)
    try:
        os.write(fd, json.dumps({'pid': os.getpid(), 'at': now()}).encode())
        os.fsync(fd); os.close(fd)
        yield
    finally:
        p.unlink()

def status(root):
    claims = [load(p) for p in sorted((root / 'claims').glob('*.json'))]
    # Files are written under the same short lock. Read with that lock in CLI.
    states = {c['claim_key']: {'claim': c, 'status': c['initial_status']} for c in claims}
    events = [load(p) for p in (root / 'inbox').glob('*.json')]
    for e in sorted(events, key=lambda e: e['sequence']):
        if e['claim_key'] in states and e['stage'] in ACTIVE | TERMINAL:
            states[e['claim_key']]['status'] = e['stage']
    for p in (root / 'integrator-acknowledged').glob('*.json'):
        a = load(p)
        if a.get('claim_key') in states and a.get('integrator_id') == 'primary-integrator':
            states[a['claim_key']]['status'] = 'integrator_owned'
    return list(states.values())

def claim_next(root, session):
    with lock(root):
        config = load(root / 'config.json')
        if not config.get('enabled') or (root / 'STOP').exists():
            raise RuntimeError('new claims disabled by integrator')
        if session not in config['worker_sessions']:
            raise ValueError('session is not assigned')
        rows = status(root)
        mine = [r for r in rows if r['claim']['owner_session'] == session]
        if sum(r['status'] in ACTIVE for r in mine) >= config['active_claims_per_worker']:
            raise RuntimeError('session active-claim limit reached')
        if sum(r['status'] == 'ready' for r in rows) >= config['ready_backlog_limit']:
            raise RuntimeError('integrator backlog limit reached')
        claimed = {r['claim']['doi'] for r in rows}
        for c in load(root / 'candidates.json'):
            doi = normalize_doi(c['doi'])
            if doi in claimed:
                continue
            obj = {'schema': 'mattersyn-session-claim/1', 'claim_key': key(doi),
                   'doi': doi, 'owner_session': session, 'claimed_at': now(),
                   'initial_status': 'claimed', 'candidate': c}
            write_new(root / 'claims' / (obj['claim_key'] + '.json'), obj)
            return obj
        raise RuntimeError('no unclaimed candidates in assigned snapshot')

def emit(root, session, doi, stage, actor, receipt=None, note=''):
    if stage not in KINDS:
        raise ValueError('unsupported event stage')
    if not actor.startswith(session + ':'):
        raise ValueError('actor must be namespaced by assigned session')
    doi = normalize_doi(doi)
    with lock(root):
        c = load(root / 'claims' / (key(doi) + '.json'))
        if c['owner_session'] != session:
            raise ValueError('claim belongs to another session')
        current = next(r['status'] for r in status(root) if r['claim']['doi'] == doi)
        if current in TERMINAL | {'integrator_owned'} and stage in ACTIVE | TERMINAL:
            raise ValueError('terminal claim requires integrator handoff; never silently reclaim')
        evidence = None
        if receipt:
            p = Path(receipt).resolve()
            if not p.is_relative_to(root.parent.resolve()) or not p.is_file():
                raise ValueError('receipt must exist within the private research-assets area')
            raw = p.read_bytes()
            evidence = {'path': str(p), 'sha256': hashlib.sha256(raw).hexdigest()}
        if stage in {'frozen', 'audit', 'ready', 'held', 'skipped'} and not evidence:
            raise ValueError('this stage requires a real immutable receipt')
        if stage == 'ready':
            r = json.loads(raw)
            if r.get('accepted') is not True:
                raise ValueError('ready handoff needs explicit scientific acceptance')
            a, b = r.get('author_id'), r.get('reviewer_id') or r.get('auditor_id')
            if not a or not b or a == b:
                raise ValueError('ready handoff needs distinct extractor and auditor identities')
            if normalize_doi(r.get('doi', '')) != doi:
                raise ValueError('audit receipt DOI does not match claim')
        sequence = 1 + max((load(p)['sequence'] for p in (root / 'inbox').glob('*.json')), default=0)
        eid = f'{sequence:012d}-' + uuid.uuid4().hex
        obj = {'schema': 'mattersyn-session-event/1', 'event_id': eid, 'sequence': sequence,
               'claim_key': c['claim_key'], 'doi': doi, 'session': session,
               'actor_id': actor, 'stage': stage, 'at': now(),
               'receipt': evidence, 'note': note,
               'scientific_acceptance_validated_by_coordinator': False,
               'publication_authorized': False}
        write_new(root / 'inbox' / (eid + '.json'), obj)
        return obj

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', required=True, type=Path)
    sub = ap.add_subparsers(dest='command', required=True)
    c = sub.add_parser('claim-next'); c.add_argument('--session', required=True)
    sub.add_parser('status')
    e = sub.add_parser('event')
    for name in ('session', 'doi', 'stage', 'actor'):
        e.add_argument('--' + name, required=True)
    e.add_argument('--receipt'); e.add_argument('--note', default='')
    a = ap.parse_args()
    if a.command == 'claim-next':
        result = claim_next(a.root, a.session)
    elif a.command == 'status':
        with lock(a.root): result = status(a.root)
    else:
        result = emit(a.root, a.session, a.doi, a.stage, a.actor, a.receipt, a.note)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
