"""A compact reader catalogue, backed by the unchanged scientific records."""


def _outcome_text(value):
    if not isinstance(value, dict):
        return str(value)
    shown = value.get('value')
    if shown is None:
        shown = str(value.get('minimum') if value.get('minimum') is not None else '—') + '–' + str(value.get('maximum') if value.get('maximum') is not None else '—')
    return str(shown) + ((' ' + str(value['unit'])) if value.get('unit') else '')


def structure_coverage_html(report, esc, pair_rows=()):
    if 'reader_collection' not in report:
        return '<section class="record-section"><h2>Synthesis recipe–structure pairs</h2><p>Pair coverage has not been generated for this build. Unavailable counts are not zero.</p></section>'
    collection = report['reader_collection']
    result = '<section class="record-section" id="pairs"><h2>Synthesis recipe–structure pairs</h2>'
    result += '<p>One pair links a documented synthesis recipe or condition variant to an identified product and its structural outcome. Changing a precursor amount or another condition counts as a separate pair when the source reports a separately characterized product. Several measurements of the same record and sample enrich one pair.</p>'
    result += '<p class="pair-footnote"><strong>Information coverage.</strong> (a) ' + str(collection['more_comprehensive_pairs']) + ' pairs have a more comprehensive description: source-backed quantified synthesis inputs, ordered operations with temperature and duration, sample-linked phase, morphology and dimensions, and a reference unit cell. (b) ' + str(collection['partial_pairs']) + ' pairs have one or more of those categories not documented in the linked record. Each row lists its documentation gaps; this is not a claim that the original paper lacks the information. A reference cell is independently sourced and does not establish the measured atomic structure of the product. These categories do not imply a complete laboratory SOP.</p>'
    result += '<p class="pair-footnote">The exact count is of documented recipe/sample pairs. Cross-paper physical-sample deduplication is not complete; these are not necessarily independent batches. Missing source details and conflicting statements remain visible in each record.</p>'
    result += '<a class="data-download" href="data/synthesis-structure-pairs.json">Download all counted pairs and source locators ↓</a> · <a class="data-download" href="data/reader-collection.json">Download documentation coverage ↓</a>'
    result += '<details class="pair-row-browser"><summary>Browse all ' + str(collection['synthesis_structure_pairs']) + ' pairs</summary><div class="table-scroll"><table class="reagent-table"><thead><tr><th>Source and recipe</th><th>Product</th><th>Structural outcome</th><th>Documentation</th></tr></thead><tbody>'
    for row in pair_rows:
        facts = [f['kind'].replace('_', ' ') + ': ' + _outcome_text(f['value']) for f in row.get('product_structure_fields', [])]
        facts += [m['property'].replace('_', ' ') + ': ' + _outcome_text(m['value']) for m in row.get('structural_measurements', [])]
        documentation = row['documentation']
        gaps = ', '.join(k.replace('_', ' ') for k in documentation['missing_categories'])
        result += '<tr><td><a href="' + esc(row['record_page_path']) + '">' + esc(row['title']) + '</a><small>' + esc(str(row.get('year') or '')) + ' · ' + esc(row['source_group']) + '</small></td><td>' + esc(row.get('source_sample_label') or row['sample_id']) + '<small>' + esc(row.get('composition', {}).get('value') or 'Composition unspecified') + '</small></td><td>' + esc('; '.join(facts)) + '</td><td>' + ('More comprehensive' if documentation['category'] == 'more_comprehensive' else 'Partial') + ('<small>Missing coverage: ' + esc(gaps) + '</small>' if gaps else '') + '</td></tr>'
    return result + '</tbody></table></div></details></section>'


def render(report, manifest, head, header, esc, human, pair_rows=()):
    collection = report['reader_collection']
    s = head('Synthesis records') + '<body>' + header() + '<main class="dataset-main"><div class="dataset-heading"><span class="eyebrow">MATERIALS SYNTHESIS DATASET</span><h1>Synthesis records</h1><p>Source-linked recipes, product structures and measured properties.</p></div><div class="dataset-summary reader-collection-summary">'
    for key, label in [('material_families', 'Material families'), ('contributing_papers', 'Contributing papers'), ('synthesis_structure_pairs', 'Synthesis recipe–structure pairs')]:
        s += '<div><strong>' + str(collection[key]) + '</strong><span>' + label + '</span></div>'
    s += '</div><p class="coverage-note">Material families are distinct directly synthesized material systems. Component-only pages point to the same underlying records and do not add families or pairs. Papers are counted once by their primary source identifier.</p>'
    s += structure_coverage_html(report, esc, pair_rows)
    s += '<section class="record-section"><h2>Explore synthesis and evidence records</h2><p>Recipes, experimental series, supporting procedures and observations share one catalogue. A record with only optical properties is available here but does not count as a recipe–structure pair.</p><div class="dataset-filters"><label>Search<input id="record-search" type="search" placeholder="Material, paper or method"></label><label>Material system<select id="family-filter"><option value="">All materials</option>'
    formulas = sorted({r['formula'] for r in manifest['records'] if r['record_type'] != 'procedure'})
    s += ''.join('<option>' + esc(f) + '</option>' for f in formulas)
    s += '</select></label><label>Record type<select id="type-filter"><option value="recipes">Recipes and experimental series</option><option value="pairs">Records with structure pairs</option><option value="procedure">Supporting procedures</option><option value="observation">Contextual observations</option><option value="all">All records</option></select></label></div><p id="record-count" class="record-count" aria-live="polite"></p><div id="catalog-results" class="record-list"></div><div class="catalog-pagination"><button id="page-prev" type="button">← Previous</button><span id="page-label"></span><button id="page-next" type="button">Next →</button></div></section>'
    s += '<section id="exports" class="record-section"><h2>Dataset downloads</h2><div class="export-grid"><a href="data/synthesis-structure-pairs.json" download><strong>Recipe–structure pairs ↓</strong><span>Product descriptors, recipe links and evidence</span></a><a href="data/records.jsonl" download><strong>All synthesis and evidence records ↓</strong><span>Canonical JSONL, including experimental series</span></a><a href="data/record.schema.json" download><strong>Record schema ↓</strong><span>Quantities, sample identities and missing information</span></a><a href="data/dataset-manifest.json" download><strong>Dataset manifest ↓</strong><span>Versions, sources and record identifiers</span></a></div>'
    s += '<details><summary>Provenance and reuse</summary><p>Literature records are not independent laboratory reproductions. Supporting procedures and contextual observations remain linked to their sources. An illustrative morphology or a bulk reference cell does not become a measured product label. Machine-readable task eligibility is retained in the downloads.</p><p>The 100 selected PbS experimental rows are incorporated in this catalogue: 95 optical outcomes and five flagged failures. They come from Voznyy et al. (2019), <a href="https://doi.org/10.1021/acsnano.9b03864.s002">official dataset</a>, under <a href="https://creativecommons.org/licenses/by-nc/4.0/">CC BY-NC 4.0</a>. Changes comprise named columns and units, row IDs, selected subset, derived cohort labels and null continuous targets for failure placeholders. Attribution and noncommercial restrictions accompany the exports. These rows do not supply particle structures. Article and figure rights remain separate.</p></details></section></main><script type="module" src="dataset-app.mjs?v=0.41.0"></script></body></html>'
    return s
