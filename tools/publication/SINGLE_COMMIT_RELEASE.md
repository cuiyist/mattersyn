# Single-commit source release preparation

This kit removes the separate source-manifest closure commit. It does not remove
scientific audits, exact file approvals, the public boundary gate, source-figure
provenance checks, clean-build requirements, or anonymous deployment verification.
It never commits, pushes, changes GitHub permissions, or starts cloud processing.

## Integration

Install these modules together in `tools/publication`:

- `prepare_source_release.py`
- `bind_source_allowlist.py`
- `scientific_binding.py`
- the updated `check_project_manifest.py` (replaces the existing checker)
- `test_prepare_source_release.py` and `test_scientific_binding.py`

The updated checker remains backward compatible with the current closure-commit
manifests; all 12 existing manifest regression tests passed. The kit has 24 new
tests using the repository's real publication guard. They cover one-commit
preparation, final-commit runtime rebinding and actual guarded export, exact
changed-file approval, secrets and PDF rejection, staged/index races, rollback,
content-binding tampering, scientific changes, and restricted stale-digest repair.

The tests locate the guard beside `tools/publication`; an external test runner
can instead supply `MATTERSYN_GUARD_MODULE`. No scientific records were changed by
this implementation or its temporary fixture repositories.

## One commit instead of payload plus closure

1. Finish the scientific audit or code review, then stage only the reviewed
   source changes. Keep drafts and original source evidence outside the checkout.
2. Supply an external exact review receipt for every new/changed/deleted payload
   file. The receipt is a declaration by the actual reviewer, not something the
   preparer invents. Unchanged rows reuse their prior approval. Generated control
   files cannot be manually approved through this input.
3. Run the preparer once with `--apply`. It boundary-scans the staged payload,
   regenerates the blueprint, generates an exact content-bound source allowlist,
   and stages both control files in the same index transaction.
4. Make one ordinary Git commit containing payload and controls. Run the updated
   manifest checker, create the normal clean runtime snapshot, and run the usual
   scientific/build/browser/boundary checks. Push only after those checks pass.

```sh
python tools/publication/prepare_source_release.py \
  --root . --reviews "$REVIEW_RECEIPT" --release-id "$RELEASE_ID" \
  --report-out "$PREPARATION_REPORT" --apply
git commit -m "Integrate reviewed contributions"
python tools/publication/check_project_manifest.py --pre-push
```

The default without `--apply` is read-only. `--apply` writes only the two control
files and their staged index entries. It locks the index, verifies the captured
tree and HEAD, and rolls back ordinary exceptions. As with Git itself, a process
or operating-system crash may require restoring generated controls and rerunning;
never bypass a failed clean-tree or hash check after an interruption.

Example review receipt structure (replace every placeholder with actual review):

```json
{
  "schema": "mattersyn-reviewed-source-changes/1",
  "base_commit": "<current full HEAD>",
  "files": [{
    "path": "README.md",
    "before_sha256": "<previous approved bytes; null for a new path>",
    "sha256": "<current staged SHA-256>",
    "bytes": 1234,
    "git_mode": "100644",
    "decision": "allow",
    "review_status": "approved",
    "reviewer": "<actual reviewer>",
    "reviewed_at": "<UTC review timestamp>",
    "source_refs": []
  }]
}
```

A deletion requires its own row with `decision: "delete"` and exact previous
`before_sha256`. Structure/provenance fields remain subject to the current guard;
a reviewer receipt cannot authorize a PDF, secret, or an unmatched source image.

The blueprint's `input_files`, `release_id`, `updated_at`, and `record_count` are
generated in the same transaction as the dataset baseline and source allowlist.
The baseline retains prior record digests and task eligibility so the final
builder can independently reject unapproved changes. A prior record correction
still requires an exact changed-file review and an explicitly approved digest;
task eligibility changes remain rejected. Do not stage a manual baseline edit.
All other blueprint fields, especially approved record digests, baseline commit
and withheld-input count, must stay identical to committed HEAD or carry a
separate `blueprint_metadata_review` in the review receipt. That block binds the
old and new canonical-JSON metadata SHA-256 values, an actual reviewer/timestamp,
`decision: allow`, and `review_status: approved`. Hash metadata after removing
only the four generated fields. This prevents a manual change to scientific
snapshot authorization from being silently approved as a generated control.

## Content binding and runtime source commit

The committed source allowlist records `source_commit_role: preparation_base`.
Its `source_payload_binding` hashes sorted path, byte count, SHA-256 and Git mode
identities for every staged payload member except the manifest itself. The
blueprint is included in that payload binding but excludes itself and the
manifest from its input list. This avoids circular commit IDs without omitting
scientific inputs. The updated checker validates exact membership, content,
mode, blueprint coverage, preparation-base ancestry and a clean final checkout.

**The committed preparation-base manifest is not the final export receipt.**
Resolve it to the actual clean committed HEAD before every source export:

```sh
python tools/publication/bind_source_allowlist.py \
  --root . --output "$RUNNER_TEMP/source-allowlist.json"
python tools/mattersyn-release/export_release.py \
  --source-root . --destination "$RUNNER_TEMP/public-source" \
  --allowlist "$RUNNER_TEMP/source-allowlist.json" \
  --registry publication/asset-rights-registry.json \
  --policy publication/public-release-policy.json --repo mattersyn \
  --manifest-out "$RUNNER_TEMP/source-manifest.json" \
  --report-out "$RUNNER_TEMP/source-boundary.json"
```

Replace the existing CI source-export step's allowlist argument with this runtime
file and add the binding command immediately before it. Runtime files remain
outside the repository. The binding records the original preparation base and
committed-manifest hash, while the unchanged export gate receives the actual
release commit. Candidate/site release stages keep their existing source and
snapshot checks. Do not push a prepared manifest until that CI change and the
updated checker have been reviewed together.

## Scientific audit reuse

`scientific_binding.py` provides `scientific_digest`, `verify_reuse`, and
`refresh_chemical_digest`. Its explicit policy excludes only `revision`,
`updated_at`, `quality.reviewed_at`, and `quality.reviewer`. All other fields,
including unknown new fields, array order, units, source locators, sample links,
review status and training eligibility, remain bound. The audit must already
bind the exact previous record bytes and digest-policy hash, and name a distinct
`author_id` and `reviewer`. Computing a digest
does not create a passed audit.

The narrowly supported regeneration updates only the existing chemical
`sourceRecordSha256[record_id]`. Existing chemical identities and assignments are
unchanged. Any scientific difference, wrong previous hash, or absent independent
audit blocks regeneration. Additional aggregate generators should be adopted
with separate contracts and tests; do not globally rewrite scientific bindings
merely to satisfy a stale-hash assertion. The generated output still needs its
public-delivery review and normal preflight, build, and browser checks.

## Publishing without new broad credentials

The source workflow currently has `contents: read`; the site repository has its
own guarded Pages deployment. The source repository's built-in token is scoped
to that repository, and cannot simply push the separate site repository.
[GitHub token scope](https://docs.github.com/en/enterprise-cloud%40latest/actions/concepts/security/github_token).
Pages deployment also requires the site's Pages and identity permissions.
[GitHub Pages custom workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

Adopt the one-commit preparation and runtime binding now. Keep the existing
reviewed local site handoff and existing site Pages workflow while a CI-only
handoff is designed. No new credential or repository permission is required for
this increment. A later option is a site-owned pull-and-build workflow: it reads
a pinned public source commit and approved release intent, re-runs source and
artifact gates, then deploys with its existing site-scoped permissions. That
option needs an authenticated/validated release-intent contract and trusted event
trigger; a schedule alone must not turn every unreviewed source commit into a
publication. It is not installed or claimed working by this kit.

Do not add an unrestricted PAT, remove the allowlist to make CI green, run
untrusted PR code with deployment credentials, or upload the repository root.
No cross-repository credentials or remote GitHub settings were changed here.

## Current pitfalls removed or deliberately retained

- The old checker requires `source_commit` followed by a second manifest-only
  commit. Content binding removes that dependency while retaining exact bytes.
- The old preparer can mark an entire provided tree approved based on a reviewer
  string. The new preparer requires exact changed-file review declarations;
  boundary acceptance alone is never treated as scientific approval.
- The current importer/preflight bind raw canonical record hashes. They should
  consume narrowly regenerated bindings only when the scientific digest is
  unchanged, not drop their checks.
- Existing source policy detects workstation paths even inside comments and
  string literals. Keep new docs portable; never include private evidence paths
  or raw source text in a public receipt. Existing exact COD exporter-comment
  exceptions remain exact hash/path exceptions, not a general local-path bypass.
- `requirements-publication.txt` pins the top-level schema package, but its
  transitive dependencies and runner images are not a full locked environment.
  A separate tested lock/container revision is still needed before claiming a
  pinned environment. Existing Windows/Linux artifact comparison stays enabled.
- This kit does not implement weekly presentation publication, silver-tier
  extraction, PR claims, merge queues, or measured throughput. Those are separate
  work packages and cannot be inferred from these tests.
