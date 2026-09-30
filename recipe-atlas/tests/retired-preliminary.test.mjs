import test from 'node:test';
import assert from 'node:assert/strict';
import {existsSync, readFileSync} from 'node:fs';

const staticFile = (path) => new URL(`../static/${path}`, import.meta.url);

test('retired preliminary synthesis display is absent from public site inputs', () => {
  for (const path of [
    'experimental-silver.html',
    'experimental-silver.mjs',
    'data/experimental-silver.json',
    'preliminary-synthesis.html',
    'preliminary-synthesis.css',
    'preliminary-synthesis.mjs',
    'data/preliminary-synthesis.json',
  ]) {
    assert.equal(existsSync(staticFile(path)), false, `${path} must stay private`);
  }

  const catalog = readFileSync(new URL('../scripts/catalog_view.py', import.meta.url), 'utf8');
  assert.doesNotMatch(catalog, /experimental-silver\.html|Experimental silver: partial/);

  const metadata = readFileSync(new URL('../scripts/generate_release_metadata.py', import.meta.url), 'utf8');
  assert.doesNotMatch(metadata, /preliminary-synthesis\.json|Preliminary synthesis sources/);
  const homepage = readFileSync(new URL('../static/index.html', import.meta.url), 'utf8');
  assert.doesNotMatch(homepage, /preliminary-synthesis|review-progress|progress\.mjs/);
  const coverage = readFileSync(new URL('../scripts/source_coverage.py', import.meta.url), 'utf8');
  assert.doesNotMatch(coverage, /preliminary|all tiers/i);
});
