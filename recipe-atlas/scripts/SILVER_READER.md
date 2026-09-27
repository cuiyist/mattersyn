# Silver Reader integration

The catalogue has a separate, disabled-by-default silver section. It makes no
silver request and shows no silver cards until the release builder supplies the
fixed path `data/silver-reader-catalog.json` to `catalog_view.render` through its
`silver_catalog_url` argument. Existing records, headline counts and training
exports remain unchanged.

The public manifest has schema `mattersyn-silver/0.1/reader-catalog`, `entries`,
`calibrations` and a verified public HTTPS `report_url`. Each entry combines an
unchanged release-admitted candidate from `tools/silver/silver.py project` with
reviewed source metadata (`title`, full `citation`, publisher/DOI `url`). Do not
change the candidate's `publication_enabled:false`: an export is not release
approval. The controlled builder must bind the exact public bytes separately.

Each calibration summary contains its `calibration_sha256`, genuinely verified
`independently_reviewed:true` and public `metrics`: field/band, gold/predicted
instances, true/false positives, false negatives, precision/recall, field-instance
and source-cluster lower bounds, distinct/all-correct source clusters, required
precision, precision basis and status. Copy measured summaries only; full truth,
quotes, audit identities, model replies and private paths remain local. The UI
checks consistency and masks malformed data; it cannot authenticate approval or
substitute for calibration and release gates.

Cards say **Machine-extracted, not reviewed**, preserve explicit recipe/sample
contexts and page locators, and count primary sources separately from records.
Main/SI copies do not add paper credit. Uncertain and unsupported values remain
masked. Missing information does not establish absence from the paper. These
cards neither grant gold status nor infer structure-pair or training eligibility.
The accuracy disclosure preserves denominators, the IID assumption and the
limitations of correlated observations. No forecast is an accuracy result.

The correction link must be real and anonymously accessible before activation.
The renderer uses textContent and HTTPS-only links, but hiding private payload
keys on screen is not enough: the complete served JSON must pass the public
boundary check. Never place raw evidence in that file.

Run `node --test recipe-atlas/tests/silver-reader.test.mjs`. Before activating a
real manifest, check desktop/mobile layouts, badges, field masks, source and
correction links, accuracy disclosures, unavailable-manifest behavior and the
existing catalogue. No scientific silver data or live activation is supplied by
this code increment; do not create a status-only deployment for hidden assets.
