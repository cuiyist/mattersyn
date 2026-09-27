"""Content-scoped audit reuse and narrowly deterministic stale-digest repair.

This module never declares an audit passed. A caller must supply an already
accepted independent audit of the exact previous record and of this digest
policy. All unknown/new fields are scientific by default. Raw record hashes and
the public delivery gate remain required even when a scientific audit is reused.
"""
from __future__ import annotations

import copy
import hashlib
import json

POLICY = {
    'schema': 'mattersyn-scientific-digest-policy/1',
    'policy_id': 'record-science-v1',
    # Intentionally no recursive name matching, wildcards, or blanket quality,
    # sources, notes, evidence, sample, eligibility or lineage exclusions.
    'reviewed_metadata_pointers': ['/revision', '/updated_at', '/quality/reviewed_at', '/quality/reviewer'],
    'list_order': 'preserved',
    'numbers': 'JSON-exact; no unit normalization or tolerance',
}


class AuditBindingError(ValueError):
    pass


def raw_sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    except (ValueError, TypeError) as exc:
        raise AuditBindingError('Record is not finite canonical JSON') from exc


POLICY_SHA256 = raw_sha(canonical(POLICY))


def scientific_value(record):
    if not isinstance(record, dict):
        raise AuditBindingError('Record must be an object')
    result = copy.deepcopy(record)
    for pointer in POLICY['reviewed_metadata_pointers']:
        parts = pointer[1:].split('/')
        parent = result
        for part in parts[:-1]:
            if not isinstance(parent, dict) or part not in parent:
                parent = None
                break
            parent = parent[part]
        if isinstance(parent, dict):
            parent.pop(parts[-1], None)
    return result


def scientific_digest(record):
    return raw_sha(canonical({'policy_sha256': POLICY_SHA256, 'record': scientific_value(record)}))


def verify_reuse(before_raw, after_raw, audit):
    before, after = json.loads(before_raw), json.loads(after_raw)
    required = {'schema': 'mattersyn-independent-scientific-audit/1', 'status': 'passed',
                'digest_policy_sha256': POLICY_SHA256, 'record_id': before.get('record_id'),
                'reviewed_record_sha256': raw_sha(before_raw), 'scientific_digest': scientific_digest(before)}
    if any(audit.get(k) != v for k, v in required.items()):
        raise AuditBindingError('Independent audit does not bind exact previous record and digest policy')
    author, reviewer = audit.get('author_id'), audit.get('reviewer')
    if not all(isinstance(v, str) and v.strip() for v in (author, reviewer, audit.get('audit_id'))):
        raise AuditBindingError('Independent audit identity is missing')
    if author.strip() == reviewer.strip():
        raise AuditBindingError('Scientific audit author and reviewer must be distinct')
    if not before.get('record_id') or before['record_id'] != after.get('record_id'):
        raise AuditBindingError('Record identity changed')
    if scientific_digest(after) != required['scientific_digest']:
        raise AuditBindingError('Scientific content changed; independent re-audit is required')
    return {'record_id': after['record_id'], 'before_sha256': raw_sha(before_raw),
            'after_sha256': raw_sha(after_raw), 'scientific_digest': required['scientific_digest'],
            'digest_policy_sha256': POLICY_SHA256, 'reused_audit_id': audit['audit_id']}


def refresh_chemical_digest(bindings, before_raw, after_raw, audit):
    """Refresh only an existing sourceRecordSha256[record_id] after audit reuse.

    Never regenerate chemistry identities, sample mappings, product facts, figure
    assignments, or scientific claims. Those require their own reviewed inputs.
    """
    receipt = verify_reuse(before_raw, after_raw, audit)
    rid = receipt['record_id']
    if bindings.get('sourceRecordSha256', {}).get(rid) != receipt['before_sha256']:
        raise AuditBindingError('Existing chemical binding does not bind audited previous bytes')
    if rid not in bindings.get('recordBindings', {}):
        raise AuditBindingError('No pre-existing chemical assignment for this record')
    result = copy.deepcopy(bindings)
    result['sourceRecordSha256'][rid] = receipt['after_sha256']
    return result, {**receipt, 'operation': 'refresh_existing_chemical_record_digest_only',
                    'scientific_audit_reused': True, 'public_delivery_approved': False}
