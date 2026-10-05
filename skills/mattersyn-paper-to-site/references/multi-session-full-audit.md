# Additional extraction and audit tasks

The owner approved this arrangement on October 3, 2026 (Chicago time). It supplements
workflow-v5; it does not change scientific acceptance, sampling or release rules.

## Ownership

Two additional tasks, worker-a and worker-b, each use a separate detached source
checkout and private output directory. Each may run two extractor-auditor pairs:
the task primary and another agent extract; two different agents audit. Obey each
task's actual runtime allowance. Do not infer active work from a created task,
queued role, command wait or elapsed wall time.

The original task alone writes canonical data, assigns first-40 ordinals, dispatches
third-agent deep audits, writes authoritative ledgers and releases the website.
Its dedicated historical worker fully audits the reconciled 20 published v5 papers
without prior deep audits. Historical findings and corrections stay outside the
first-40 sampling denominator and earn no new-paper publication credit.

## Shared coordination

Use `tools/workflow/session_coordination.py` with the integrator-provided private
root and session name. That root contains the candidate snapshot, reservations,
config, immutable claims, event inbox and integrator acknowledgments. Never commit
that state, source files, quotes, detailed audits or candidate packages.

`claim-next` exclusively reserves a normalized DOI. Two active claims per worker
task are allowed. Existing published and historical claims are reserved in advance.
Filename identity is provisional: if the source DOI differs, stop that claim and
ask the integrator to reserve the alias. Do not silently create another claim.

All coordinator mutations use an exclusive short lock and atomic create-only
writes. An old lock is never stolen automatically. Check `STOP` and `enabled`
before new work; after a pause preserve current bytes and report the checkpoint.
Workers must not delete claims, change configuration or write integrator acks.

Use globally unique actor IDs containing session, actual task ID and role. Submit
stage/activity events with actual timestamps and exact receipt hashes. The inbox
is a handoff log, not a scientific or publication ledger. The `ready` shape check
does not establish acceptance: the integrator verifies the full independent audit,
distinct real agents, exact accepted hashes and any required third-agent sample.

Freeze packages before audit, run `check_records.py` before every audit, and keep
corrections in new revisions. Author and auditor must be different agents. Audit
both source-to-record completeness and every record's source support. Preserve
original S1/S2 findings after correction. Do not use the retired quick audit.

For future full comparisons, an available central ordinal/admission receipt is not a start
prerequisite. Within an existing exclusive claim, verify source identity, current `enabled`/`STOP`
and quality-stop state, the exact immutable package bytes, a successful fresh checker after freeze,
and an auditor distinct from every scientific author with their own source-first inventory frozen
before opening claims. Immediately submit the immutable first valid freeze, then emit the actual
comparison-start receipt to the coordinator/root; retain the real timestamps and exact hashes.
Do not wait for transport polish or further parent permission. Identity ambiguity, a missing or
stale checker, or any failed prerequisite keeps the comparison on hold.

Root alone sorts and adopts genuine first-freeze receipts, records later insertion separately from
actual occurrence, and assigns the unchanged deterministic sampling ordinals. Workers never assign
a slot or dispatch a third audit. Third audits still require root qualification and full-audit
acceptance, with their own fresh checker. This replaces earlier wait-for-admission instructions
for future full comparisons only; acceptance, READY and publication requirements remain unchanged.

## Collision prevention and throughput

Workers never edit shared canonical checkouts, policies, allowlists, Git settings,
source/site branches or scientific ledgers, and never commit, push or deploy.
Use base-hash-pinned additive handoffs. Only the integrator rebases transport onto
a new canonical base; accepted unchanged scientific bytes retain their receipts.
Use separate private artifact paths and avoid full-project copies per paper.

At twelve unacknowledged ready handoffs, new claims stop until the integrator drains
the backlog. Acknowledgment transfers ownership permanently; it does not free the
paper for another extractor. Scaling to 8, 12 or 16 pairs is not authorized merely
by adding tasks: retain the owner's ten-deep-audit quality, zero-collision,
two-batch backlog and measured spare machine/agent-capacity conditions. The existing
single-session `ramp_gate` remains conservative and is not evidence of cross-session
capacity or permission for further scaling.

Release at six ready papers or three hours, using the normal batch gates. Do not
wait for a blocked paper. Only deployed, anonymously verified contributions increase
the homepage count. No new paid processing, source transfer, downloads, installations,
automations or scheduled progress reports are authorized by this arrangement.
