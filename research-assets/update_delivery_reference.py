from pathlib import Path
R=Path(__file__).resolve().parent.parent
p=R/'skills/mattersyn-paper-to-site/references/delivery-and-memory.md'
text=p.read_text(encoding='utf8')
entry='''

## Verified public GitHub delivery (September 20, 2026)

Both `cuiyist/mattersyn` and `cuiyist/mattersyn-site` are public. The preserved unfiltered repositories are private under `mattersyn-source-archive-20260920` and `mattersyn-site-source-archive-20260920`; their old local checkouts point to these preservation names. The original authoring directory stays `[local path redacted] Current isolated publication copies are `[local path redacted] and `[local path redacted] Consult latest MEMORY.md if paths change.

Use `research-assets/sync_github_public.py project` or `site`, which applies `public_projection_policy.py` before committing. The history builder preserved all32 earlier commits while filtering source-equivalent content; do not recreate repositories on routine future releases. `github_public_delivery.py preserve-and-create` was a one-time migration action, not part of normal synchronization. The obsolete `sync_github_private.py` is disabled. Never push the unfiltered authoring tree or preserved original checkout to the public destination.

Run the citation/progress generators when their underlying milestones change; inspect the resulting public projection, commit/push the affected repository and verify the exact published commit anonymously. `verify_public_delivery.py` checks both public repositories, README DOI links, actual deployed bytes and the omitted complete-page asset. If the reference count grows beyond the initial31sources, update that explicit expected count from the current published manifest rather than treating31as a permanent scientific requirement. Preserve scientific dataset publication time separately from a progress-only website redeployment. Synchronize memory, skills, proposal/audit artifacts and final verification after delivery, while keeping unfinished science labeled.

The user requested a two-month fixed-collection target and authorized preparing an API pilot cost/capacity proposal. No paid pilot or production infrastructure is authorized yet. Preserve the current proposal and correction history under `research-assets/incoming-paper-monitor/deadline-20260920/`. A deliberately diverse QA sample does not establish corpus prevalence. Expanded capacity must preserve per-paper independent audits and be validated with an appropriately designed throughput test.

Measure public asset growth and publication time during the pilot. GitHub Pages currently limits a published site to1GB and has a soft10builds/hour limit for the branch-based path; coalesce completed contributions/progress updates and reassess asset hosting before measured growth reaches that limit. Do not lower figure legibility or omit data to fit a deadline. Reference: https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits . No alternative paid host has been chosen or purchased.
'''
if '## Verified public GitHub delivery' not in text:p.write_text(text+entry,encoding='utf8')
print('Saved verified public delivery workflow and pilot boundary in project skill.')
