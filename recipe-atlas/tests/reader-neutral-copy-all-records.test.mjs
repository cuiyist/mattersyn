// Full canonical-record display check: invoke on GitHub, not as a local quick check.
// No papers, model calls, record writes, Source edits or source-text requests.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {conditionFieldText,conditionDisclosureText,productFactLabel,formulaFieldText,READER_COPY} from '../static/source-field-copy.mjs';
import {protocolPresentationPolicy} from '../static/protocol-record-fit.mjs';
import {defaultCrystalReferences} from '../static/crystal-defaults.mjs';

const frozen = value => {
  if (value && typeof value === 'object') {for (const child of Object.values(value)) frozen(child); Object.freeze(value);}
  return value;
};
const records = new URL('../data/records/', import.meta.url);
const libraryPath = new URL('../static/assets/crystal-references/registry.json', import.meta.url);
const libraryRaw = fs.readFileSync(libraryPath);
const referenceLibrary = JSON.parse(libraryRaw);
const entries = frozen(referenceLibrary.entries);
const libraryBefore = JSON.stringify(referenceLibrary);
const missing = ['Not reported','Not recorded in this field','Not specified','Unspecified'];
const statuses = ['source_reviewed','source_extracted'];

test('every canonical record uses neutral Reader copy without changing facts or provenance', () => {
  const files = fs.readdirSync(records).filter(name => name.endsWith('.json')).sort();
  assert(files.length > 0); let operations = 0, missingQuantities = 0, referenceRecords = 0;
  for (const file of files) {
    const path = new URL(file, records), raw = fs.readFileSync(path);
    const original = frozen(JSON.parse(raw)), before = JSON.stringify(original);
    const pairs = statuses.map(review_status => frozen({...original,quality:{...original.quality,review_status}}));
    for (const record of pairs) {
      const unchanged = JSON.stringify(record);
      for (const value of missing) assert.equal(conditionFieldText(value,record),'Not reported');
      assert.equal(conditionDisclosureText(record),'Conditions and source');
      assert.equal(productFactLabel('Crystal phase',record),'Phase or crystallinity');
      for (const value of [undefined,null,'','Unspecified','Source empirical formula not reported'])
        assert.equal(formulaFieldText(value),'Not reported');
      for (const operation of record.operations || []) for (const quantity of Object.values(operation.parameters || {})) {
        if (quantity && quantity.status === 'not_reported') assert.equal(conditionFieldText('Not reported',record),'Not reported');
      }
      assert.equal(JSON.stringify(record),unchanged);
    }
    const [reviewed,extracted] = pairs;
    const hasDrawing = Boolean(original.operations?.length);
    assert.deepEqual(protocolPresentationPolicy(reviewed,{hasDrawing}),protocolPresentationPolicy(extracted,{hasDrawing}));
    const shared = protocolPresentationPolicy(reviewed,{hasDrawing:true});
    assert.equal(shared.caption,'Schematic: vessel shapes and colors are illustrative.');
    assert.equal(shared.enlarge,true);
    assert.equal(protocolPresentationPolicy(reviewed,{hasDrawing:false}).enlarge,false);
    const protectedCaption = 'Source-specific fixture caption; specimen and source qualifications retained.';
    const options = {protectedPerPaper:true,protectedCaption,hasDrawing:true};
    assert.deepEqual(protocolPresentationPolicy(reviewed,options),protocolPresentationPolicy(extracted,options));
    assert.equal(protocolPresentationPolicy(reviewed,options).caption,protectedCaption);
    assert.deepEqual(defaultCrystalReferences(entries,reviewed),defaultCrystalReferences(entries,extracted));
    if (defaultCrystalReferences(entries,reviewed).length) referenceRecords++;
    assert.equal(JSON.stringify(original),before);
    assert(fs.readFileSync(path).equals(raw),'Canonical record bytes changed');
    operations += original.operations?.length || 0;
    missingQuantities += (original.operations || []).flatMap(op => Object.values(op.parameters || {})).filter(q => q?.status === 'not_reported').length;
  }
  assert.equal(READER_COPY.sourceLink,'Source details →');
  assert.equal(READER_COPY.toolbar,'Synthesis and evidence');
  assert.equal(READER_COPY.sourceFigureScope,'record');
  assert.equal(JSON.stringify(referenceLibrary),libraryBefore);
  assert(fs.readFileSync(libraryPath).equals(libraryRaw),'Reference library bytes changed');
  console.log(JSON.stringify({records:files.length,operations,missingQuantities,referenceRecords,status_pair:'source_reviewed/source_extracted',canonical_changes:0,library_changes:0,model_or_paper_calls:0}));
});
