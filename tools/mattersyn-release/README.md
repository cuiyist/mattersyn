# Public release boundary tools

These tools validate or project exact reviewed files for the MatterSyn source
repository and website. The project-wide workflow is in `PUBLICATION.md` at the
repository root. Scientific review, source-image rights and public delivery are
separate gates: passing this boundary does not approve a scientific claim,
sample-coordinate pair or training example.

## Inputs and commands

The project policy and factual image-rights register live in
`publication/public-release-policy.json` and
`publication/asset-rights-registry.json`. A website release carries its exact
controls under `.release-control/`. Supply the paths and hashes belonging to the
release being checked; do not substitute another release's allowlist or registry.
Allowlist preparation must follow review of the complete candidate file set.

`gate.py` checks an isolated prepared stage without copying or deploying it:

```text
python gate.py --root STAGE --allowlist ALLOWLIST --registry REGISTRY --policy POLICY --repo mattersyn-site --manifest-out EXTERNAL_MANIFEST --report-out EXTERNAL_REPORT
```

Use `--repo mattersyn` when checking a source projection. The stage contains only
deliverable files, without Git metadata. Receipts must use distinct new paths
outside the stage.

`export_release.py` projects a reviewed input tree into a new, disjoint destination:

```text
python export_release.py --source-root SOURCE --destination NEW_STAGE --allowlist ALLOWLIST --registry REGISTRY --policy POLICY --repo mattersyn-site --manifest-out EXTERNAL_MANIFEST --report-out EXTERNAL_REPORT
```

Consult each command's `--help` for its exact interface. Neither command commits,
pushes, changes repository visibility, or deploys a website. A failed check must
be resolved before publication; its diagnostic receipt is not an approval.

## Checks and provenance

`public_release_guard.py` is the shared implementation. The policy, allowlist,
asset register and every delivered file are bound by exact hashes. Missing or
changed files, private source payloads, local machine paths and unmatched image
identities fail delivery. Structured quantities and approved coordinate payloads
retain their evidence and values; nested JSON strings receive the same private
content checks as ordinary JSON. An authored diagram or source-link card must
retain that classification and must not be represented as a measured image.
Pending source-image clearance is represented by citations and qualified source
links while the original evidence remains private.

Run the included bounded regression suite from this directory:

```text
python -B -m unittest discover -s tests -p "test_*.py"
```

These tests exercise boundary behavior. They do not replace per-paper source
audits, record validation, reader checks, or release-specific review.
