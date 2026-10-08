"""Private first-pass findings monitor. Reads receipts; never edits audit history or publishes."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re

SCHEMA = 'mattersyn-record-window-monitor/1'
HASH = re.compile(r'^[a-f0-9]{64}$')
WINDOW_SIZE = 500
MIN_RECORDS = 100
THRESHOLD_PER_100 = 1


def require(condition, message):
    if not condition:
        raise ValueError(message)


def identity(value):
    require(isinstance(value, str) and value.strip() == value and value, 'nonempty identity required')
    return value


def timestamp(value):
    require(isinstance(value, str), 'sampled_at timestamp required')
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(result.tzinfo is not None, 'sampled_at requires a timezone')
    return result.astimezone(timezone.utc)


def monitor(events, window_id):
    """Order by completion time, event ID and the frozen explicit record order.

    Each original finding counts once when any explicitly affected record remains
    inside the exact last-500-record slice. A grouped finding is not multiplied by
    its affected-record count. Corrections cannot replace or append a sample.
    Other resume windows are retained by the caller, never included implicitly.
    """
    identity(window_id)
    require(isinstance(events, list), 'events must be a list')
    selected_events, event_ids, sources, records = [], set(), set(), set()
    for event in events:
        require(isinstance(event, dict), 'invalid sample event')
        identity(event.get('window_id'))
        if event['window_id'] != window_id:
            continue
        eid, source = identity(event.get('event_id')), identity(event.get('primary_source_id'))
        require(eid not in event_ids, 'duplicate event in window')
        require(source not in sources, 'duplicate source or correction sample in window')
        event_ids.add(eid); sources.add(source)
        at = timestamp(event.get('sampled_at'))
        for key in ('frozen_package_sha256', 'receipt_sha256'):
            require(isinstance(event.get(key), str) and HASH.fullmatch(event[key]), key + ' required')
        agents = [identity(event.get(key)) for key in ('author_id', 'full_auditor_id', 'deep_auditor_id')]
        require(len(set(agents)) == 3, 'author, full auditor and deep auditor must be distinct')
        rids = event.get('record_ids')
        require(isinstance(rids, list) and rids, 'frozen ordered record_ids required')
        require(all(isinstance(r, str) and r and r.strip() == r for r in rids), 'invalid record identity')
        require(len(set(rids)) == len(rids) and not records.intersection(rids), 'duplicate record in window')
        records.update(rids)
        findings = event.get('original_findings')
        require(isinstance(findings, list), 'original first-pass findings required')
        seen = set()
        for finding in findings:
            require(isinstance(finding, dict), 'invalid original finding')
            fid = identity(finding.get('finding_id'))
            require(fid not in seen, 'duplicate adjudicated finding')
            seen.add(fid)
            require(finding.get('severity') in ('S1', 'S2', 'S3', 'S4'), 'invalid finding severity')
            affected = finding.get('affected_record_ids')
            require(isinstance(affected, list) and affected and all(isinstance(r, str) and r in rids for r in affected)
                    and len(set(affected)) == len(affected),
                    'explicit affected_record_ids must name sampled records')
        selected_events.append((at, eid, event))
    selected_events.sort(key=lambda item: (item[0], item[1]))
    ordered = [(event, rid) for _, _, event in selected_events for rid in event['record_ids']]
    selected = ordered[-WINDOW_SIZE:]
    selected_ids = {rid for _, rid in selected}
    counted, partial = [], []
    for _, _, event in selected_events:
        in_window = [rid for rid in event['record_ids'] if rid in selected_ids]
        if not in_window:
            continue
        if len(in_window) != len(event['record_ids']):
            partial.append({'primary_source_id': event['primary_source_id'],
                            'included_record_ids': in_window,
                            'excluded_record_ids': [r for r in event['record_ids'] if r not in selected_ids]})
        for finding in event['original_findings']:
            if finding['severity'] in ('S1', 'S2') and selected_ids.intersection(finding['affected_record_ids']):
                counted.append({'event_id': event['event_id'], 'finding_id': finding['finding_id'],
                                'severity': finding['severity']})
    n, errors = len(selected), len(counted)
    evaluated = n >= MIN_RECORDS
    # Integer comparison preserves the strict boundary without float rounding.
    stop = evaluated and errors * 100 > THRESHOLD_PER_100 * n
    return {'schema': SCHEMA, 'window_id': window_id, 'sampled_records': n,
            'all_sampled_records': len(ordered), 's1_s2_findings': errors,
            'findings_per_100_sampled_records': errors * 100 / n if n else None,
            'evaluated': evaluated, 'stop_required': stop,
            'threshold_per_100': THRESHOLD_PER_100, 'minimum_records': MIN_RECORDS,
            'window_size': WINDOW_SIZE, 'counted_findings': counted,
            'ordered_record_ids': [rid for _, rid in selected], 'partial_boundary_papers': partial,
            'boundary_rule': 'A first-pass S1/S2 finding counts once if any explicit affected record is in the exact record window; grouped findings are not multiplied. Corrections retain the original event.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ledger', required=True)
    parser.add_argument('--window-id', required=True)
    parser.add_argument('--output')
    args = parser.parse_args()
    events = [json.loads(line) for line in Path(args.ledger).read_text(encoding='utf-8').splitlines() if line.strip()]
    result = monitor(events, args.window_id)
    raw = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    if args.output:
        require(Path(args.output).resolve() != Path(args.ledger).resolve(), 'cannot overwrite original ledger')
        Path(args.output).write_text(raw, encoding='utf-8', newline='\n')
    else:
        print(raw, end='')
    return 2 if result['stop_required'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
