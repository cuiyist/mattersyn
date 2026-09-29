# Declarative additive overlay merger

R1 stages a frozen package as a private overlay. It reads a checkout and payload but never writes either. It does not approve scientific content, release rights, or publication.

The contract (`schema_version: mattersyn-declarative-additive-merge/1`) pins every changed JSON base file by SHA-256 and may pin a full Git object ID. It supports:

- `create_files`: create-only payload copies with exact source path, target path, SHA-256 and byte count; every payload file must be listed.
- `add_keys`: add keys at an existing JSON Pointer; key collisions fail.
- `append_unique`: append list objects using declared `identity_keys`; an existing identity with identical JSON content is a no-op, conflicting content fails.

Unsafe/noncanonical paths, symlinks, stale hashes, unlisted files, duplicate targets, malformed pointers, unknown fields, and rights/release-policy targets fail closed. Rights registries and public-release policies require a separate explicit review and are never auto-merged.

```powershell
python -B -X utf8 merger.py `
  --checkout ../private-checkout `
  --payload ../frozen-package `
  --contract ../frozen-package/merge-contract.json `
  --importer ../private-checkout/tools/package-importer/importer.py `
  --output ../private-stage/new-overlay
```

The stage contains `overlay/` candidates and a hash manifest. It is not applied data. An integrator must compare-and-swap the exact base in a private checkout, apply the overlay, then run the repository `preflight.py`, builders, source/review checks, rights gate, and release tests. The merger does not resolve semantic conflicts or promote review status.

Focused synthetic tests:

```powershell
$env:MATTERSYN_IMPORTER_PATH = '../private-checkout/tools/package-importer/importer.py'
python -B -X utf8 -m unittest discover -s tests -v
```

New paper reviews may declare a table's `source_data_path` as
`data/paper-evidence/<paper_id>/<basename>.csv`, with its exact
`source_data_sha256`. If the accepted payload supplies only the corresponding
`recipe-atlas/static/data/paper-evidence/...` CSV, the merger also stages the
same pinned bytes at `recipe-atlas/data/paper-evidence/...`. The static copy is
retained. Both paths appear explicitly as create-only entries in the output
file manifest; `evidence_csv_placements` records the source, destination, hash
and size. An already declared source-side CSV is validated without duplication.

Only the exact paper ID and a single CSV basename are supported by this
placement step. Missing/unpinned data, differing copies, missing/wrong hashes,
foreign paper paths and target collisions stop preparation before output is
created. Existing path, symlink, payload, additive merge and create-only checks
remain in force. This step preserves accepted table bytes; it does not create
new table content, certify science, amend rights, or grant publication credit.
