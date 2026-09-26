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
