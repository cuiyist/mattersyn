/** Reader-only view of release-admitted silver projections. Never modifies gold or training exports. */
export const BADGE = 'Machine-extracted, not reviewed';
const CATALOG_SCHEMA = 'mattersyn-silver/0.1/reader-catalog';
const CANDIDATE_SCHEMA = 'mattersyn-silver/0.1/public-candidate';
const THRESHOLDS = {high: .98, medium: .95, low: .90};
const FIELDS = new Set(['reaction_temperature', 'duration', 'precursor_amount', 'solvent_volume',
  'concentration', 'particle_diameter', 'core_diameter', 'shell_thickness', 'hydrodynamic_diameter',
  'crystallite_size', 'phase', 'morphology', 'precursor_identity', 'composition', 'product_statement']);
const TEXT_FIELDS = new Set(['phase', 'morphology', 'precursor_identity', 'composition', 'product_statement']);
const HASH = /^[a-f0-9]{64}$/;
const PRIVATE_PATH = /(?:(?<![A-Za-z])[A-Za-z]:[\\/]|\\\\|file:\/\/|\/Users\/|\/home\/|\/tmp\/)/i;
const DEPENDENCE = 'Field-instance bounds assume independent instances. Variants and supporting information from one paper can be correlated. The source-cluster bound is a sensitivity check, not a dependence-adjusted accuracy guarantee.';
const clean = (value, max = 500) => typeof value === 'string' && value.length > 0 && value.length <= max && !PRIVATE_PATH.test(value) ? value : null;
const human = value => value.replaceAll('_', ' ');
const probability = value => Number.isFinite(value) && value >= 0 && value <= 1;
const count = value => Number.isSafeInteger(value) && value >= 0;

function primaryDoi(source) {
  let doi = source?.doi;
  if (doi === undefined) {
    const url = safeHttpsUrl(source?.url);
    if (url) {
      const parsed = new URL(url);
      if (['doi.org', 'dx.doi.org'].includes(parsed.hostname)) {
        try {doi = decodeURIComponent(parsed.pathname.slice(1));} catch {return null;}
      }
    }
  }
  return typeof doi === 'string' && /^10\.\d{4,9}\/[^\s?#]+$/i.test(doi) ? doi.toLowerCase() : null;
}

export function qualifiedMachinePaperDois(view, {excludedPrimaryDois = []} = {}) {
  const excluded = new Set(excludedPrimaryDois.map(doi => primaryDoi({doi})).filter(Boolean));
  const qualified = new Set();
  for (const record of view?.records || []) {
    if (!record.primary_doi || excluded.has(record.primary_doi)) continue;
    const fields = record.fields.filter(field => field.training_masked === false && field.state === 'accepted_auto_checked');
    const core = ['composition', 'reaction_temperature', 'duration', 'product_statement'];
    const boundPrecursor = fields.some(identity => identity.field === 'precursor_identity'
      && fields.some(amount => amount.field === 'precursor_amount' && amount.slot_id === identity.slot_id));
    if (boundPrecursor && core.every(name => fields.some(field => field.field === name))) qualified.add(record.primary_doi);
  }
  return [...qualified].sort();
}

export function safeHttpsUrl(value) {
  if (typeof value !== 'string' || /[\u0000-\u0020\u007f]/.test(value)) return null;
  try {
    const url = new URL(value);
    return url.protocol === 'https:' && !url.username && !url.password ? url.href : null;
  } catch { return null; }
}

function metricValid(metric) {
  if (!metric || !FIELDS.has(metric.field) || !(metric.band in THRESHOLDS)) return false;
  const counts = ['gold_instances', 'predicted_instances', 'true_positive', 'false_positive',
    'false_negative', 'distinct_source_clusters', 'all_correct_source_clusters'];
  if (!counts.every(key => count(metric[key])) || !metric.predicted_instances || !metric.gold_instances || !metric.distinct_source_clusters) return false;
  if (metric.true_positive + metric.false_positive !== metric.predicted_instances || metric.true_positive + metric.false_negative !== metric.gold_instances) return false;
  if (metric.all_correct_source_clusters > metric.distinct_source_clusters || metric.distinct_source_clusters > metric.predicted_instances) return false;
  if (!['precision', 'recall', 'instance_precision_lower95', 'source_cluster_lower95'].every(key => probability(metric[key]))) return false;
  if (Math.abs(metric.precision - metric.true_positive / metric.predicted_instances) > 1e-10 || Math.abs(metric.recall - metric.true_positive / metric.gold_instances) > 1e-10) return false;
  return metric.instance_precision_lower95 <= metric.precision && metric.source_cluster_lower95 <= metric.all_correct_source_clusters / metric.distinct_source_clusters
    && metric.required_precision === THRESHOLDS[metric.band] && metric.precision_basis === 'field_instance';
}

function calibrationMap(summaries) {
  const map = new Map();
  for (const summary of Array.isArray(summaries) ? summaries : []) {
    if (!summary || !HASH.test(summary.calibration_sha256 || '') || summary.independently_reviewed !== true || !Array.isArray(summary.metrics)) continue;
    const metrics = new Map();
    let valid = true;
    for (const metric of summary.metrics) {
      const key = JSON.stringify([metric?.band, metric?.field]);
      if (!metricValid(metric) || metrics.has(key)) { valid = false; break; }
      // Keep only the public statistical summary; ignore any private audit payload.
      metrics.set(key, Object.fromEntries(['band', 'field', 'gold_instances', 'predicted_instances', 'true_positive',
        'false_positive', 'false_negative', 'precision', 'recall', 'instance_precision_lower95', 'distinct_source_clusters',
        'all_correct_source_clusters', 'source_cluster_lower95', 'required_precision', 'precision_basis', 'status'].map(k => [k, metric[k]])));
    }
    // Duplicate digests are ambiguous, even when one of the supplied summaries is valid.
    if (map.has(summary.calibration_sha256)) map.set(summary.calibration_sha256, null);
    else map.set(summary.calibration_sha256, valid && metrics.size ? metrics : null);
  }
  return map;
}

function fieldView(field, band, metrics) {
  if (!field || !FIELDS.has(field.field) || !clean(field.recipe_id, 120) || !clean(field.slot_id, 120)
    || !(field.sample_id === null || clean(field.sample_id, 120))) return null;
  const metric = metrics?.get(JSON.stringify([band, field.field]));
  const calibrated = metric?.status === 'eligible_for_independent_calibration_review'
    && metric.instance_precision_lower95 >= THRESHOLDS[band];
  const locators = Array.isArray(field.locators) ? field.locators.filter(x => clean(x?.document_id, 120) && Number.isSafeInteger(x.page) && x.page > 0)
    .map(x => ({document_id: x.document_id, page: x.page})) : [];
  const typed = TEXT_FIELDS.has(field.field) ? !!clean(field.value, 120) && field.unit === null
    : Number.isFinite(field.value) && !!clean(field.unit, 25);
  const accepted = calibrated && field.state === 'accepted_auto_checked' && field.training_masked === false
    && probability(field.training_weight) && field.training_weight > 0 && typed && locators.length > 0
    && locators.length === field.locators.length;
  // Never reveal values, units, alternatives or locators carried on masked/invalid rows.
  const state = accepted ? 'accepted_auto_checked' : calibrated && band !== 'high' && field.state === 'uncertain'
    && field.training_masked === true ? 'uncertain' : 'not_extracted';
  return {recipe_id: field.recipe_id, sample_id: field.sample_id, slot_id: field.slot_id, field: field.field,
    state, value: accepted ? field.value : null, unit: accepted ? field.unit : null,
    training_masked: !accepted, locators: accepted ? locators : [], metric: calibrated ? metric : null};
}

export function prepareCatalog(catalog) {
  const unavailable = {available: false, records: [], metrics: [], record_count: null, source_count: null,
    pair_count: null, report_url: null};
  if (!catalog || catalog.schema !== CATALOG_SCHEMA || !Array.isArray(catalog.entries)) return unavailable;
  const calibrations = calibrationMap(catalog.calibrations);
  const grouped = new Map(), sourceBindings = new Map(), rejectedSources = new Set(), metrics = new Map();
  for (const entry of catalog.entries) {
    const candidate = entry?.candidate, source = entry?.source;
    if (!candidate || candidate.schema !== CANDIDATE_SCHEMA || candidate.tier !== 'silver'
      || candidate.publication_enabled !== false || candidate.has_publishable_values !== true
      || !clean(candidate.source_id, 120) || !clean(candidate.family_id, 120) || !(candidate.band in THRESHOLDS)
      || !HASH.test(candidate.calibration_sha256 || '') || !Array.isArray(candidate.fields) || !source
      || !clean(source.title, 1000) || !clean(source.citation, 2000) || !safeHttpsUrl(source.url)) continue;
    const doi = primaryDoi(source);
    const binding = JSON.stringify([candidate.family_id, candidate.band, candidate.calibration_sha256, source.title, source.citation, source.url, doi]);
    if (sourceBindings.has(candidate.source_id) && sourceBindings.get(candidate.source_id) !== binding) rejectedSources.add(candidate.source_id);
    sourceBindings.set(candidate.source_id, binding);
    for (const raw of candidate.fields) {
      const field = fieldView(raw, candidate.band, calibrations.get(candidate.calibration_sha256));
      if (!field) continue;
      const key = JSON.stringify([candidate.source_id, field.recipe_id, field.sample_id]);
      if (!grouped.has(key)) grouped.set(key, {key, source_id: candidate.source_id, family_id: candidate.family_id,
        band: candidate.band, calibration_sha256: candidate.calibration_sha256, title: source.title,
        citation: source.citation, source_url: safeHttpsUrl(source.url), primary_doi: doi, recipe_id: field.recipe_id,
        sample_id: field.sample_id, fields: new Map(), duplicate_fields: new Set()});
      const record = grouped.get(key), fieldKey = JSON.stringify([field.slot_id, field.field]);
      if (record.fields.has(fieldKey) && JSON.stringify(record.fields.get(fieldKey)) !== JSON.stringify(field)) record.duplicate_fields.add(fieldKey);
      else record.fields.set(fieldKey, field);
    }
  }
  const records = [];
  for (const record of grouped.values()) {
    if (rejectedSources.has(record.source_id)) continue;
    const fields = [...record.fields.entries()].map(([key, field]) => record.duplicate_fields.has(key)
      ? {...field, state: 'not_extracted', value: null, unit: null, locators: [], training_masked: true} : field);
    if (!fields.some(field => !field.training_masked)) continue;
    for (const field of fields) if (field.metric) metrics.set(JSON.stringify([record.calibration_sha256, record.band, field.field]),
      {calibration_sha256: record.calibration_sha256, ...field.metric});
    const {duplicate_fields, ...publicRecord} = record;
    records.push({...publicRecord, fields});
  }
  return {available: true, records, metrics: [...metrics.values()], record_count: records.length,
    source_count: new Set(records.map(r => r.source_id)).size, pair_count: null,
    report_url: safeHttpsUrl(catalog.report_url)};
}

function element(doc, tag, text, className) {
  const node = doc.createElement(tag);
  if (text !== undefined) node.textContent = String(text);
  if (className) node.className = className;
  return node;
}

function sourceLink(doc, text, href) {
  const node = element(doc, 'a', text);
  node.href = href;
  node.rel = 'noopener noreferrer';
  return node;
}

const percent = value => (value * 100).toFixed(2) + '%';

export function renderCatalog(host, view, {hideEmpty = false, hiddenByFilter = false} = {}) {
  const doc = host.ownerDocument;
  host.replaceChildren();
  host.hidden = hiddenByFilter || hideEmpty && !view.records.length;
  if (host.hidden) return;
  host.className = 'record-section silver-reader';
  host.append(element(doc, 'h2', 'Machine-extracted records'));
  host.append(element(doc, 'p', BADGE, 'silver-badge'));
  if (!view.records.length) {
    host.append(element(doc, 'p', 'No release-admitted silver records are available in this view. Calibration accuracy is unavailable.', 'record-notice'));
    return;
  }
  host.append(element(doc, 'p', 'These silver records have field-level automatic checks and calibration. Each paper has not received an independent scientific review. They remain separate from the existing reviewed collection and its training/evaluation exports.'));
  const counts = element(doc, 'dl', undefined, 'silver-counts');
  for (const [label, value] of [['Silver source papers', view.source_count], ['Silver recipe/sample records', view.record_count], ['Silver structure pairs', 'Not assessed']]) {
    const block = element(doc, 'div'); block.append(element(doc, 'dt', label), element(doc, 'dd', value)); counts.append(block);
  }
  host.append(counts, element(doc, 'p', 'Paper counts deduplicate the primary source identifier, including linked main text and supporting information. Record counts distinguish explicit recipe/sample contexts. These counts do not establish daily publication throughput.', 'record-note'));
  const list = element(doc, 'div', undefined, 'silver-records');
  for (const record of view.records) {
    const card = element(doc, 'article', undefined, 'dataset-card silver-card');
    card.append(element(doc, 'p', BADGE, 'silver-badge'));
    const heading = element(doc, 'h3'); heading.append(sourceLink(doc, record.title, record.source_url)); card.append(heading);
    card.append(element(doc, 'p', record.citation, 'record-citation'));
    card.append(element(doc, 'p', 'Recipe: ' + record.recipe_id + ' · Sample: ' + (record.sample_id ?? 'No explicit sample assignment')));
    if (record.band === 'low') card.append(element(doc, 'p', 'Sparse material family: coverage may be limited.', 'record-note'));
    const table = element(doc, 'table', undefined, 'silver-field-table');
    const caption = element(doc, 'caption', 'Extracted field states and source locators');
    const thead = element(doc, 'thead'), headings = element(doc, 'tr');
    for (const name of ['Field and context', 'Value', 'State and evidence']) { const th = element(doc, 'th', name); th.scope = 'col'; headings.append(th); }
    thead.append(headings); const tbody = element(doc, 'tbody');
    for (const field of record.fields) {
      const row = element(doc, 'tr'), name = element(doc, 'th', human(field.field) + ' · ' + field.slot_id); name.scope = 'row';
      const value = element(doc, 'td', field.training_masked ? 'Value withheld' : String(field.value) + (field.unit ? ' ' + field.unit : ''));
      const state = element(doc, 'td');
      state.append(element(doc, 'strong', field.state === 'accepted_auto_checked' ? 'Accepted by automatic checks' : field.state === 'uncertain' ? 'Uncertain · training masked' : 'Not extracted · training masked'));
      if (field.locators.length) for (const locator of field.locators) state.append(element(doc, 'span', locator.document_id + ' · PDF page ' + locator.page, 'silver-locator'));
      else state.append(element(doc, 'span', 'No admitted evidence locator.', 'silver-locator'));
      row.append(name, value, state); tbody.append(row);
    }
    table.append(caption, thead, tbody); const scroll = element(doc, 'div', undefined, 'silver-table-scroll'); scroll.append(table); card.append(scroll);
    card.append(element(doc, 'p', 'Only supplied extraction fields are listed. Missing or withheld information does not establish absence in the paper. This is not a complete laboratory protocol.', 'record-note'));
    card.append(element(doc, 'p', 'Source identifier: ' + record.source_id + ' · Calibration: ' + record.calibration_sha256, 'silver-provenance'));
    if (view.report_url) card.append(sourceLink(doc, 'Report a possible error', view.report_url));
    else card.append(element(doc, 'p', 'Error reporting link is unavailable.', 'record-note'));
    list.append(card);
  }
  host.append(list);
  const accuracy = element(doc, 'details', undefined, 'silver-accuracy');
  accuracy.append(element(doc, 'summary', 'Calibration summary'));
  accuracy.append(element(doc, 'p', 'Observed held-out results by field and material-family frequency band. These are calibration-set statistics, not a probability that an individual field is correct.'));
  accuracy.append(element(doc, 'p', DEPENDENCE, 'record-notice'));
  for (const metric of view.metrics) {
    const block = element(doc, 'section');
    block.append(element(doc, 'h3', human(metric.field) + ' · ' + metric.band + ' frequency band'));
    block.append(element(doc, 'p', 'Observed precision: ' + percent(metric.precision) + ' (' + metric.true_positive + '/' + metric.predicted_instances + ' predicted field instances). Recall: ' + percent(metric.recall) + ' (' + metric.true_positive + '/' + metric.gold_instances + ' audited expected instances).'));
    block.append(element(doc, 'p', 'One-sided 95% lower precision bound: ' + percent(metric.instance_precision_lower95) + '; required threshold: ' + percent(metric.required_precision) + '.'));
    block.append(element(doc, 'p', 'Distinct source clusters: ' + metric.distinct_source_clusters + '; all-correct clusters: ' + metric.all_correct_source_clusters + '; source-cluster lower 95% bound: ' + percent(metric.source_cluster_lower95) + '.'));
    if (metric.source_cluster_lower95 < metric.required_precision) block.append(element(doc, 'p', 'Dependence sensitivity: the source-cluster bound is below the field admission threshold.', 'record-notice'));
    block.append(element(doc, 'p', 'Calibration version: ' + metric.calibration_sha256, 'silver-provenance'));
    accuracy.append(block);
  }
  host.append(accuracy);
}

export async function mountSilverReader(host, {url, fetcher = globalThis.fetch, hideEmpty = false} = {}) {
  if (!host) return;
  if (!url) { renderCatalog(host, prepareCatalog(null), {hideEmpty}); return; }
  try {
    const response = await fetcher(url);
    if (!response.ok) throw new Error('Silver catalogue unavailable');
    const view=prepareCatalog(await response.json());
    renderCatalog(host, view, {hideEmpty});
    return view;
  } catch { renderCatalog(host, prepareCatalog(null), {hideEmpty}); }
}
