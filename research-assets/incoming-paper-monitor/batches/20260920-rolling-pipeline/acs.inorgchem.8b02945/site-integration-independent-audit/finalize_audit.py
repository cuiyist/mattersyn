"""Freeze independent audit outputs only; never modify proposed or Site content."""
import datetime
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
M = Path('[local path redacted]')
O = Path(__file__).parent
F = O.parent
V = F / 'site-integration-proposal/v1'
sys.path.insert(0, str(M / 'research-assets'))
from sync_github_public import io_path

def read(p):
    return json.loads(io_path(p).read_text(encoding='utf-8-sig'))

def sha(p):
    return hashlib.sha256(io_path(p).read_bytes()).hexdigest()

def write(p, value):
    io_path(p).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

checks = read(O/'projection-checks.json')
schema = read(O/'current-schema-checks.json')
assert checks['summary']['passed'] == checks['summary']['executed'] == 3788
assert not checks['summary']['failed']
assert schema['passed'] and schema['record_count'] == 30
expected = '1714710fcab2068a7b9dc13e0392ccb8dd708cc661961c324ef969c6fee34612'
assert checks['proposal_freeze_sha256'] == schema['proposal_freeze_sha256'] == sha(V/'package-freeze.json') == expected
bound = {**checks['bound_files'], **schema['bound_files']}
for name in ['projection-checks.json', 'current-schema-checks.json', 'check_projection.py',
             'check_current_schema.py', 'projection-checks-initial-diagnostics.json', 'finalize_audit.py']:
    p = O/name
    bound[str(p)] = sha(p)
stale = [p for p, h in bound.items() if sha(Path(p)) != h]
assert not stale, stale
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
report = {
    'audit_id': 'friedfeld2019-publication-projection-v1-independent-audit',
    'status': 'passed', 'author': '/root', 'auditor': '/root/backlog_eta',
    'reviewer': '/root/backlog_eta', 'created_at': now,
    'proposal_freeze_path': str(V/'package-freeze.json'),
    'proposal_freeze_sha256': expected,
    'scope': 'Independent metadata/publication-path and byte transport audit of the frozen private Site proposal; not a new full-paper scientific review or approval of actual Site import/browser/publication.',
    'findings': [], 'open_findings': [],
    'counts': {**checks['counts'], 'reader_items': 417, 'reader_field_links': 2131,
               'solution_contexts': 8, 'public_assets': 162, 'independent_upstream_audits': 6},
    'validation': {
        'projection_hash_transport_checks': checks['summary'],
        'current_schema_semantic_records_passed': 30,
        'current_eligibility_records_checked': 30,
        'eligible_training_tasks': 0,
        'actual_reader_consumer_validation': 'passed with no errors against the isolated proposal fixture',
        'final_bound_file_rehash_count': len(bound), 'stale_bound_files': [],
        'full_details': ['projection-checks.json', 'current-schema-checks.json']
    },
    'manual_review_scope': [
        'Read the root projection builder, frozen manifests, disclosed pre-freeze failed-attempt receipt and metadata delta categories.',
        'Reviewed promotion wording, audit identities/hashes and retained distinctions among four route/variant, fifteen procedure and eleven observation records.',
        'Reviewed reader publication/audit/training wording and false Site/browser/publication/exact-structure gates.',
        'Reviewed source-specific stock mapping, particularly the varied MSC concentration context, without substituting its representative 20 mg charge.',
        'Reviewed the public asset inventory and exclusion patterns. Existing approved visual and source audits supply scientific/visual provenance; no unchanged source pages or all visual previews were reread in this transport audit.'
    ],
    'preservation_results': {
        'canonical_records': 'All 30 records equal frozen draft-v3 after restoring only collection, reader_role, quality review/status/historical-workflow metadata and source review-status metadata. All 58 operations, 750 measurements, sample/condition/conflict fields and empty task/structure arrays are unchanged.',
        'reader': 'All 417 reader items, their 2,131 typed links, scientific arrays, source locators, original crop links and conflicts are unchanged. Only review/presentation metadata, audited flags and the resolved historical pending-workflow sentence changed.',
        'molecules': '39 effective correction-v2 entries, 77 exact canonical material-slot assignments and all model/hash references are preserved. Approval flags and promoted-record digests alone change.',
        'solutions': 'All eight source-bound solution contexts and sixteen components are identical apart from approval flags. All stock figure record/stock assignments, hashes and scopes are preserved.',
        'products': '88 exact contextual mappings and fourteen symbolic entries are unchanged apart from approval/audit flags and approved public SVG paths; no product atomic coordinates are added.',
        'assets': 'All 162 public assets, including 51 selected original crops, are byte-identical to independently approved upstream assets. Exact direct or audited-freeze transitive hash chains were verified. The staged dist inventory equals the allowlist.',
        'publication_exclusions': 'No source PDFs, full-page source scans, complete-source text payloads or extra assets occur in the public allowlist/dist tree. Scans of intended public JSON/MJS/SVG content found no local absolute paths, file URLs or source-render/complete-source payload references.',
        'training': 'Every requested_tasks list is empty; actual current dataset_lib eligibility returns false for every task on all 30 records.'
    },
    'allowed_delta_categories': [
        'Source-reviewed collection and review/status/scope metadata, four route navigation roles plus procedure/observation roles, and removal of one resolved historical pending-workflow sentence.',
        'Reader audit references and presentation approval flags supported by six distinct upstream passed audits; downstream import/browser/publication remain false.',
        'Molecular/product approval metadata, exact promoted canonical byte digests, empty binding maps for records with no materials, and approved public SVG paths.',
        'Public asset copying with byte equality; no scientific or geometric transformation.'
    ],
    'history': {
        'author_failed_attempt': 'V1/FAILED_ATTEMPT.json discloses pre-freeze Windows path and allowlist I/O corrections. The final frozen proposal is complete and all its hashes/inventory were independently verified.',
        'auditor_initial_diagnostics': 'projection-checks-initial-diagnostics.json is preserved. Fifteen initial asset-coverage checks assumed direct audit-bound file enumeration; the corrected checker follows exact audit-bound apparatus/product freeze manifests. No author asset correction was required.'
    },
    'not_approved_here': ['Actual shared Site import or generated Site outputs', 'Browser rendering/interaction', 'Live publication and anonymous delivery', 'Any new training task or measured exact structure–recipe pair'],
    'next_action': 'Root may use this passed exact-hash proposal audit as the pre-import transport gate. Revalidate bound bytes immediately before import, then run the separate build, integrated browser and publication verification gates.',
    'bound_files': dict(sorted(bound.items()))
}
write(O/'promotion-delta-audit.json', report)
md = f'''# Friedfeld publication projection audit

**Passed.** Author: `/root`; independent auditor: `/root/backlog_eta`.

The frozen proposal SHA256 is `{expected}`. All 3,788 transport/hash checks and current schema/semantic checks for all 30 records pass. The actual current reader validator reports no errors. All {len(bound):,} final input bindings were rehashed before this report.

The 30 records retain all scientific content from approved canonical draft-v3: four route/variant records, fifteen procedures, eleven observations, 58 operation instances and 750 measurements. The 417-item reader and its 2,131 field links remain scientifically unchanged. Source conflicts, missingness and sample boundaries are retained.

The proposal preserves 39 molecular identities, 77 material slots, eight solution contexts with sixteen components, and 88 product contexts with fourteen symbolic depictions. All 162 public assets—including 51 selected original crops—match approved source bytes. The varied MSC stock does not acquire the representative stock charge. No product atomic model is introduced.

Allowed changes are review/collection/navigation metadata, audit and binding flags, promoted record hashes, approved public paths, and removal of resolved historical workflow wording. All training requests remain empty; actual eligibility is false for every task on all 30 records.

No source PDFs, full-page scans, complete-source payloads or extra files appear in the staged public asset set. The intended public text files contain no local absolute paths or source-render payload references. Private manifests remain private.

There are no required corrections. The author's disclosed pre-freeze I/O attempts and the auditor's initial direct-binding assumption are preserved; neither changes the frozen scientific package. This review inspected the projection and its exact deltas and reused the six passed scientific/visual audits. It did not repeat unchanged full-paper or full-preview reading.

Actual Site import, integrated rendering/browser QA and live publication remain separate gates. Root can proceed to its prepared import only while the audit-bound files still match. Detailed checks and exact file hashes are in `promotion-delta-audit.json`, `projection-checks.json` and `current-schema-checks.json`.
'''
io_path(O/'promotion-delta-audit.md').write_text(md, encoding='utf-8')
receipt = {'status': 'passed', 'created_at': now, 'author': '/root', 'auditor': '/root/backlog_eta',
           'proposal_freeze_sha256': expected, 'audit_path': str(O/'promotion-delta-audit.json'),
           'audit_sha256': sha(O/'promotion-delta-audit.json'),
           'report_path': str(O/'promotion-delta-audit.md'), 'report_sha256': sha(O/'promotion-delta-audit.md'),
           'next_action': report['next_action'], 'additional_audits_started': False}
write(O/'next-action-receipt.json', receipt)
print(json.dumps(receipt, indent=2))
