import test from 'node:test';
import assert from 'node:assert/strict';
import {BADGE, prepareCatalog, renderCatalog, safeHttpsUrl, mountSilverReader, qualifiedMachinePaperDois} from '../static/silver-reader.mjs';

// Entirely synthetic software fixtures. None are source evidence or measured calibration results.
const HASH = 'a'.repeat(64);
// Construct an inert file-scheme fixture without embedding a local file URL.
const FILE_URL_FIXTURE = new URL('https://example.org/synthetic-test.pdf');
FILE_URL_FIXTURE.protocol = 'file:';
function metric(field = 'reaction_temperature', band = 'high') {
  return {band, field, gold_instances: 160, predicted_instances: 150, true_positive: 150,
    false_positive: 0, false_negative: 10, precision: 1, recall: 150 / 160,
    instance_precision_lower95: .98022, distinct_source_clusters: 10, all_correct_source_clusters: 10,
    source_cluster_lower95: .74113, required_precision: {high:.98, medium:.95, low:.90}[band],
    precision_basis: 'field_instance', status: 'eligible_for_independent_calibration_review'};
}
function field(overrides = {}) {
  return {recipe_id:'Synthetic method A', sample_id:null, slot_id:'growth-temperature',
    field:'reaction_temperature', state:'accepted_auto_checked', value:270, unit:'°C',
    training_masked:false, training_weight:.74113, locators:[{document_id:'main', page:2}], ...overrides};
}
function entry(overrides = {}) {
  return {source:{title:'Synthetic fixture only', citation:'Software test fixture; no research paper', url:'https://example.org/paper'},
    candidate:{schema:'mattersyn-silver/0.1/public-candidate', tier:'silver', source_id:'fixture-paper',
      family_id:'synthetic-family', band:'high', publication_enabled:false, has_publishable_values:true,
      calibration_sha256:HASH, fields:[field()], ...overrides}};
}
function catalog(entries = [entry()]) {
  return {schema:'mattersyn-silver/0.1/reader-catalog', entries,
    report_url:'https://example.org/report', calibrations:[{calibration_sha256:HASH,
      independently_reviewed:true, metrics:[metric()]}]};
}

function coreCatalog() {
  const fields = [['composition','composition','ZnO',null],['reaction_temperature','temperature',270,'°C'],
    ['duration','duration',30,'min'],['product_statement','product','ZnO nanocrystals',null],
    ['precursor_identity','precursor','Zinc acetate',null],['precursor_amount','precursor',1,'mmol']]
    .map(([name,slot_id,value,unit])=>field({field:name,slot_id,value,unit}));
  const data=catalog([entry({fields})]);data.entries[0].source.url='https://doi.org/10.9999/SYNTHETIC-A';
  data.calibrations[0].metrics=fields.map(row=>metric(row.field));return data;
}

test('machine paper counter requires every core field, bound precursor amount and unique unmasked primary DOI',()=>{
  const data=coreCatalog();const view=prepareCatalog(data);
  assert.deepEqual(qualifiedMachinePaperDois(view),['10.9999/synthetic-a']);
  assert.deepEqual(qualifiedMachinePaperDois(view,{excludedPrimaryDois:['10.9999/SYNTHETIC-A']}),[]);
  const duplicate=structuredClone(data.entries[0]);duplicate.candidate.source_id='another-identity-same-paper';
  data.entries.push(duplicate);assert.equal(qualifiedMachinePaperDois(prepareCatalog(data)).length,1);
  for(const name of ['composition','reaction_temperature','duration','product_statement','precursor_identity','precursor_amount']) {
    const masked=coreCatalog();masked.entries[0].candidate.fields.find(row=>row.field===name).training_masked=true;
    assert.deepEqual(qualifiedMachinePaperDois(prepareCatalog(masked)),[],name+' must be unmasked');
  }
  const unbound=coreCatalog();unbound.entries[0].candidate.fields.find(row=>row.field==='precursor_amount').slot_id='unrelated';
  assert.deepEqual(qualifiedMachinePaperDois(prepareCatalog(unbound)),[]);
  const invalid=coreCatalog();invalid.entries[0].source.url='https://doi.org/10.9999/%INVALID';
  assert.deepEqual(qualifiedMachinePaperDois(prepareCatalog(invalid)),[]);
  const noDoi=coreCatalog();noDoi.entries[0].source.url='https://example.org/paper';
  assert.deepEqual(qualifiedMachinePaperDois(prepareCatalog(noDoi)),[]);
  const mixedSamples=coreCatalog();mixedSamples.entries[0].candidate.fields[0].sample_id='different-sample';
  assert.deepEqual(qualifiedMachinePaperDois(prepareCatalog(mixedSamples)),[]);
});

class Node {
  constructor(tag, doc) { this.tagName = tag; this.ownerDocument = doc; this.children = []; this._text = ''; }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; this._text = ''; }
  set textContent(value) { this._text = String(value); this.children = []; }
  get textContent() { return this._text + this.children.map(c => c.textContent).join(' '); }
  set innerHTML(_) { throw Error('HTML injection sink must never be used'); }
}
function host() {
  const doc = {createElement: tag => new Node(tag, doc)};
  return new Node('section', doc);
}
function walk(node) { return [node, ...node.children.flatMap(walk)]; }

test('separates silver from reviewed/benchmark manifests and never emits structure-pair eligibility', () => {
  assert.equal(prepareCatalog({records:[{tier:'gold'}]}).available, false);
  const input = catalog([entry(), entry({tier:'gold', source_id:'gold'}), entry({tier:'benchmark', source_id:'benchmark'})]);
  const before = structuredClone(input), view = prepareCatalog(input);
  assert.equal(view.records.length, 1);
  assert.equal(view.source_count, 1);
  assert.equal(view.pair_count, null);
  assert.equal('eligibility' in view.records[0], false);
  assert.deepEqual(input, before, 'the input records must remain immutable');
  const root = host(); renderCatalog(root, view);
  assert.match(root.textContent, /Machine-extracted, not reviewed/);
  assert.match(root.textContent, /Silver structure pairs Not assessed/);
});

test('requires a bound independently reviewed passing calibration, not model agreement', () => {
  for (const mutate of [c=>c.calibrations=[], c=>c.calibrations[0].independently_reviewed=false,
    c=>c.entries[0].candidate.calibration_sha256='b'.repeat(64),
    c=>c.calibrations[0].metrics[0].status='STOP', c=>c.calibrations[0].metrics[0].instance_precision_lower95=.97,
    c=>c.calibrations[0].metrics[0].predicted_instances=0]) {
    const data = catalog(); mutate(data);
    assert.equal(prepareCatalog(data).records.length, 0);
  }
});

test('masks uncertain, not-extracted, tampered and nonfinite values even if payload contains secrets', () => {
  for (const change of [{state:'uncertain',training_masked:true}, {state:'not_extracted'},
    {training_masked:true}, {training_weight:NaN}, {training_weight:0}, {value:Infinity},
    {locators:[{document_id:'main',page:-1}]}]) {
    const bad = field({slot_id:'masked-slot', value:123456789, unit:'PRIVATE_SECRET', ...change});
    const data = catalog([entry({fields:[field(),bad]})]);
    const view = prepareCatalog(data), masked = view.records[0].fields[1];
    assert.equal(masked.value, null); assert.equal(masked.unit, null);
    assert.equal(masked.training_masked, true); assert.deepEqual(masked.locators, []);
    const root = host(); renderCatalog(root, view);
    assert.doesNotMatch(root.textContent, /123456789|PRIVATE_SECRET|Infinity|NaN/);
  }
});

test('medium/low uncertainty stays explicit and masked while high disagreements are withheld', () => {
  for (const band of ['high','medium','low']) {
    const data = catalog([entry({band, fields:[field(),field({slot_id:'uncertain-context', state:'uncertain', training_masked:true, value:777})]})]);
    data.calibrations[0].metrics = [metric('reaction_temperature',band)];
    const view = prepareCatalog(data);
    assert.equal(view.records[0].fields[1].state, band==='high'?'not_extracted':'uncertain');
    assert.equal(view.records[0].fields[1].value, null);
  }
});

test('counts distinct primary sources separately from recipes/samples, deduplicating main/SI and identical entries', () => {
  const main = entry(), si = entry({fields:[field({recipe_id:'Synthetic method B',sample_id:'S1',locators:[{document_id:'si',page:3}]})]});
  const secondSample = entry({fields:[field({recipe_id:'Synthetic method B',sample_id:'S2'})]});
  const otherPaper = entry({source_id:'fixture-paper-2'});
  const view = prepareCatalog(catalog([main,si,secondSample,otherPaper,structuredClone(main)]));
  assert.equal(view.record_count, 4);
  assert.equal(view.source_count, 2);
  assert.equal(view.metrics.length, 1, 'do not aggregate/double-count the same calibration across records');
});

test('duplicate conflicting slots cannot reveal arbitrarily selected values or inflate counts', () => {
  const view = prepareCatalog(catalog([entry(), entry({fields:[field({value:999})]})]));
  assert.equal(view.source_count, 0);
  assert.equal(view.record_count, 0);
  const differentBinding = entry(); differentBinding.source.title='Different source identity';
  assert.equal(prepareCatalog(catalog([entry(),differentBinding])).records.length,0);
});

test('renders untrusted source/scientific text as text and rejects executable or credentialled URLs', () => {
  const data = catalog();
  data.entries[0].source.title = '<img src=x onerror=alert(1)>';
  data.entries[0].source.citation = '</p><script>alert(1)</script>';
  data.entries[0].candidate.fields.push(field({field:'phase', slot_id:'phase', value:'<svg onload=alert(1)>',unit:null}));
  data.calibrations[0].metrics.push(metric('phase'));
  const root = host(); renderCatalog(root,prepareCatalog(data));
  assert.match(root.textContent, /<img src=x onerror=alert\(1\)>/);
  assert.match(root.textContent, /<svg onload=alert\(1\)>/);
  assert.equal(walk(root).some(n=>['script','img','svg'].includes(n.tagName)),false);
  for (const bad of ['javascript:alert(1)','data:text/html,<script>',FILE_URL_FIXTURE.href,'//example.org','https://user:secret@example.org','https:\n//example.org']) {
    assert.equal(safeHttpsUrl(bad),null);
    const input = catalog(); input.entries[0].source.url=bad;
    assert.equal(prepareCatalog(input).record_count,0);
  }
  data.report_url='javascript:alert(1)';
  const blocked = host(); renderCatalog(blocked,prepareCatalog(data));
  assert.equal(walk(blocked).some(n=>n.href?.startsWith('javascript:')),false);
});

test('whitelists output and preserves source document/PDF page without copying private quotations', () => {
  const data = catalog(); data.entries[0].candidate.quote='PRIVATE_RAW_QUOTE';
  data.entries[0].candidate.fields[0].quote='PRIVATE_FIELD_QUOTE';
  data.entries[0].candidate.fields[0].locators[0].local_path='C:/private/paper.pdf';
  const view = prepareCatalog(data), encoded=JSON.stringify(view);
  assert.doesNotMatch(encoded,/PRIVATE_RAW_QUOTE|PRIVATE_FIELD_QUOTE|C:\/private/);
  assert.deepEqual(view.records[0].fields[0].locators,[{document_id:'main',page:2}]);
  const root=host();renderCatalog(root,view);
  assert.match(root.textContent,/main · PDF page 2/);
  assert.ok(walk(root).some(n=>n.tagName==='a'&&n.textContent==='Report a possible error'&&n.href==='https://example.org/report'));
});

test('accepts a public DOI URL in citation text while rejecting actual local paths', () => {
  const data=catalog();data.entries[0].source.citation='Synthetic fixture, https://doi.org/10.example/test';
  assert.equal(prepareCatalog(data).record_count,1);
  for (const path of ['C:/private/paper.pdf','C:\\private\\paper.pdf',FILE_URL_FIXTURE.href]) {
    data.entries[0].source.citation='Private path: '+path;
    assert.equal(prepareCatalog(data).record_count,0);
  }
});

test('calibration summary reports actual fixture denominators, recall and dependence separately', () => {
  const root=host();renderCatalog(root,prepareCatalog(catalog()));
  assert.match(root.textContent,/150\/150 predicted field instances/);
  assert.match(root.textContent,/150\/160 audited expected instances/);
  assert.match(root.textContent,/Distinct source clusters: 10/);
  assert.match(root.textContent,/source-cluster bound is below/);
  assert.match(root.textContent,/assume independent instances/);
  assert.match(root.textContent,/not a probability that an individual field is correct/);
});

test('invalid statistics or duplicate calibration digests fail closed', () => {
  for (const change of [{true_positive:149},{precision:NaN},{recall:1},{required_precision:.90},
    {distinct_source_clusters:151},{source_cluster_lower95:1.1},{precision_basis:'source_cluster'}]) {
    const data=catalog();Object.assign(data.calibrations[0].metrics[0],change);
    assert.equal(prepareCatalog(data).record_count,0);
  }
  const duplicate=catalog();duplicate.calibrations.push(structuredClone(duplicate.calibrations[0]));
  assert.equal(prepareCatalog(duplicate).record_count,0);
});

test('empty/unavailable data has no invented accuracy or zero reviewed count; hidden mode is supported', async () => {
  for (const data of [null,catalog([])]) {
    const root=host();renderCatalog(root,prepareCatalog(data));
    assert.match(root.textContent,/Calibration accuracy is unavailable/);
    assert.doesNotMatch(root.textContent,/100%|98%|Gold|0 reviewed/);
    renderCatalog(root,prepareCatalog(data),{hideEmpty:true});assert.equal(root.hidden,true);
  }
  const root=host();let fetchCalls=0;
  await mountSilverReader(root,{fetcher:()=>{fetchCalls++;throw Error('must not fetch');}});
  assert.equal(fetchCalls,0);
  await mountSilverReader(root,{url:'data/silver-reader-catalog.json',fetcher:async()=>({ok:false})});
  assert.match(root.textContent,/unavailable/);
  await mountSilverReader(root,{url:'data/silver-reader-catalog.json',fetcher:async()=>({ok:true,json:async()=>{throw Error('bad JSON');}}),hideEmpty:true});
  assert.equal(root.hidden,true);
});
