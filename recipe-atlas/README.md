# MatterSyn build and validation

MatterSyn presents reviewed synthesis records through shared Reader and Data views.
Source facts, sample identities, conflicting claims and task-specific training
eligibility remain in reviewed data; a successful build is not a scientific audit.

## Source of truth

- `data/records/` and `data/paper-reviews/`: approved release records and source reviews.
- `data/reader-presentation-reviewed.json`: the reviewed record/figure/interpretation
  sidecar. Preserve source and sample scopes when adding a contribution.
- `data/`: audited inventory, display classifications, structure-task policy,
  release-progress snapshot and corpus metadata required by the builders.
- `templates/` and `scripts/`: page templates, builders and validators.
- `static/`: authored JavaScript, CSS, historical evidence pages, approved assets
  and source inputs that previously lived only inside `dist`.
- `dist/`: generated release artifact; never edit it directly after migration.

The migration must first preserve all required inputs in a new isolated source
tree. Do not delete the existing `dist` or use an incomplete committed checkout
as the source for a release. The migration plan records both committed and dirty
input hashes, excludes unpublished records, holds unselected or unclassified source
assets and private working materials, and preserves selected original source
figures as exact cited website inputs under the user's current display preference.

## Build a release

Use Python 3 with `requirements-data.txt` installed in an existing environment.
Scientific tests use the standard-library unittest runner; browser checks use Playwright with an installed
browser. The build never installs packages, downloads papers, publishes or changes
repository visibility/history.

For a final source checkout, first create an external runtime snapshot from the
committed portable blueprint (run these commands inside `recipe-atlas`):

```shell
python scripts/make_runtime_snapshot.py --root .. --blueprint ../publication/build-inputs.json --output ../../mattersyn-runtime-snapshot.json
python scripts/build_release.py --output ../../new-release-workspace --snapshot ../../mattersyn-runtime-snapshot.json --gate ../tools/mattersyn-release/gate.py --allowlist ../../release-allowlist.json --registry ../publication/asset-rights-registry.json --policy ../publication/public-release-policy.json --artifact-transform ../tools/publication/source_link_artifacts.py
```

For a review-only build, pass `--candidate` and omit gate/allowlist/policy. It emits only `candidate-manifest.json` marked **UNAPPROVED**, never a release manifest. Inspect that artifact and approve its exact output hashes before a separate clean final build. No dummy or bypass gate is used.

The output directory must not exist. The command stages `static`, runs dataset,
Reader views, evidence views, paper reviews, atlas and inventory builders, then
copies the independently reviewed Reader sidecar. It generates references and the
HTML progress fallback from one snapshot, validates links/data, and runs the
separate release boundary gate. Failure leaves a diagnostic workspace, never a
publishable manifest. The boundary gate is authoritative for public content.

The committed blueprint records fixed release input hashes and a timestamp,
without embedding its own future commit ID. The helper requires a clean checkout,
verifies the listed inputs and binds the external runtime snapshot to the actual
Git HEAD. Final builds recheck that commit; candidate builds cannot grant approval.
The source and artifact gates must reject unlisted files as well as hash changes.
The immutable runtime snapshot records the approved source commit, release ID, exact
record/review/static input hashes and progress timestamp. A new paper must be
present in the approved records, inventory and reviewed Reader sidecar before it
can enter a release. Bibliographies derive from that exact approved record set.

## Checks before publication

Run `python -m unittest discover -s tests -v` and `check_site.py`, `check_atlas.py`,
`check_quality.py`. Browser checks must cover cold fragment links and `hashchange`
after asynchronous Reader rendering, not just static ID presence. Verify the
progress fallback with JavaScript disabled and with a failed progress fetch.

Deploy only the artifact whose file hashes match the final release manifest.
Use the same snapshot for the project bibliography and website bibliography.
Repository `.nojekyll` is a deliberate deployment adapter. Do not compare a dirty
working tree to a public commit and call that a reproducible build.

Publication remains a separate authorized action after content and source/Reader
QA. The user's current instruction keeps selected original source figures available
on the public reader with citation, page/figure locator and supported sample
provenance. This project display choice does not mean publisher permission was
verified; keep each asset's permission status accurate. A successful build does not
make original papers or SI, extracted full text/OCR, page renders, private working
crops or unselected source assets public.

Historical counts, former Sites instructions and old one-off build descriptions
are retained in [CHANGELOG.md](CHANGELOG.md).
