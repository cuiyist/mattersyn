"""Save the current integration and GitHub handoff without changing publication claims."""
from pathlib import Path
from datetime import datetime, timezone
import json

root = Path('[local path redacted]')
now = datetime.now(timezone.utc).isoformat()
state = {
    'saved_at': now,
    'github': {
        'account': 'cuiyist',
        'project_repository': {'name': 'mattersyn', 'visibility': 'private'},
        'website_repository': {'name': 'mattersyn-site', 'visibility': 'public'},
        'papers_and_si': 'keep_local',
        'authorization': 'first_request_denied; replacement_request_pending',
        'repositories_created': False,
        'uploaded': False,
        'pages_published': False,
    },
    'local_candidate': {
        'dataset_version': '0.23.0', 'records': 470, 'material_collections': 42,
        'direct_material_collections': 32, 'component_material_collections': 10,
        'formal_source_readers': 26, 'source_groups': 31,
        'new_contributions': ['nagasaki2004', 'ribeiro2004', 'norberg2004'],
        'new_records': 46, 'old_424_records_unchanged': True,
        'build_checks': 'passed', 'browser_checks': 'partially_completed',
        'independent_reader_integration_audit': 'passed: 4485 checks, zero findings',
        'independent_reader_integration_audit_sha256': 'bbe9e8761041cef75ad351713ff2fff22d8035554fee2496e59542b0fa4c6e27',
        'published': False,
    },
    'live_site': {'version': 29, 'dataset_version': '0.22.0',
        'url': 'https://mattersyn-recipe-atlas.cuiy781513.chatgpt.site/'},
    'latest_intake': {'scan_at': '2026-09-20T01:16:19.340381+00:00',
        'document_copies': 13714, 'incoming': 6341, 'legacy': 7373,
        'waiting_provisional_review_scopes': 9397, 'active': 4,
        'verified_unique_paper_count': None},
    'heo_si': {'reviewed_pages': '1-12', 'remaining_pages': '13-14',
        'rows': 1070, 'numeric_positions': 6420, 'resolved_numeric_values': 6418,
        'uncertain_signs': 2, 'markers': 1070, 'definite_negative_fobs_squared': 115,
        'uncertain_cells': ['11R35 Fobs2: magnitude 1965.46', '12L12 Fcal2: magnitude 3757.09'],
        'complete_si_review': False, 'exact_structure_recipe_approved': False},
}
(root/'research-assets/github-preparation-checkpoint.json').write_text(json.dumps(state, indent=2)+'\n', encoding='utf8')
heading = '## 2026-09-20 — Private GitHub backup and separate public website; integration candidate ready'
memory = root/'MEMORY.md'
old = memory.read_text(encoding='utf8')
entry = f'''{heading}

Saved {now}. The user's LATEST choice overrides the earlier public-project answer: create PRIVATE cuiyist/mattersyn for project code, memory, skills, structured data and audit/review history, plus PUBLIC cuiyist/mattersyn-site containing only the published website. Keep downloaded papers and SI local. GitHub authorization is pending after the first device request was denied; no repository has been created, no project uploaded and no GitHub Pages deployment completed. Do not store device codes, credentials or cookies. Exact current state: research-assets/github-preparation-checkpoint.json.

The integrated local candidate is dataset0.23.0:470 canonical/public records,42 material collections (32direct+10component),31sourcegroups,26formalreaders/245pages. It adds46records from Nagasaki CdS, Ribeiro SnO2 and Norberg Mn:ZnO,586readeritems,147materialbindings,63originalassets and96operation-specific scenes. All424oldcanonicalrecords are unchanged. Root scientific promotion audits and independent asset/reader transport audits passed. Final reader integration audit:4485checks,zero findings,SHA256 bbe9e8761041cef75ad351713ff2fff22d8035554fee2496e59542b0fa4c6e27. Final build and data/quality checks passed; see incoming-paper-monitor/batches/20260919-five-paper-pilot/build-check-output.json. Browser verification is partially complete. These contributions are NOT YET PUBLISHED; do not close their claims. The live Site remains version29/dataset0.22.0.

Heo SI pages1-12 have independently audited chunks:1070rows,6420numeric positions,6418resolved values,2unresolved signs,1070markers and115definite negative Fobs2 values. Unresolved signs:11R35 Fobs2 magnitude1965.46 and12L12 Fcal2 magnitude3757.09; retain signed null and both candidates. Pages13-14 remain unreviewed. No complete-SI/CIF/exact-pair approval. The newer chunk audit files under jp0219348 supersede earlier progress summaries; immutable earlier freezes and correction histories remain.

Latest intake scan2026-09-20T01:16:19.340381+00:00:13714documentcopies(6341incoming+7373legacy),9397waiting provisional scopes,4active. These are not verified unique-paper/material/recipe totals. Preserve evidence-rich priority, current retained batch, local-only sources and CdSe standards. Do not rerun old save_visual_stage_checkpoint.py or save_reader_stage_checkpoint.py: they hardcode outdated Heo/intake state. Publish only after browser/deployment verification and then update the authoritative publication checkpoint.

'''
if heading not in old:
    memory.write_text(entry+old, encoding='utf8')
print('Saved current private/public preference, local integration scope and unfinished work; publication ledger unchanged.')
