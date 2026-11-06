import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { validateTargets, targetURL, checkAfterLabels, VIEWPORTS } from './protocol-scenes-check.mjs';

const original = JSON.parse(fs.readFileSync(new URL('./protocol-scenes-targets.json', import.meta.url), 'utf8'));
const copy = () => structuredClone(original);

test('fixed public target set has ten actual defaults and five named examples', () => {
  const rows = validateTargets(copy());
  assert.equal(rows.length, 15);
  assert.equal(rows.filter((row) => row.group === 'benchmark-default').length, 10);
  assert.equal(rows.filter((row) => row.group === 'route-example').length, 5);
  assert.deepEqual(VIEWPORTS.map((row) => row.width), [1440, 390]);
  assert.equal(rows.length * VIEWPORTS.length * 2, 60);
});

test('private fields, record duplicates, absent target and invalid operation/hash are rejected', () => {
  const mutations = [
    (x) => { x.targets[0].private_path = 'private'; },
    (x) => { x.targets[0].review_status = 'private'; },
    (x) => { x.targets[1].record_id = x.targets[0].record_id; },
    (x) => { x.targets.pop(); },
    (x) => { x.targets[0].operation_index = -1; },
    (x) => { x.targets[0].record_json_sha256 = 'not-a-sha'; },
  ];
  for (const mutate of mutations) { const value = copy(); mutate(value); assert.throws(() => validateTargets(value)); }
});

test('defaults cannot acquire method parameters, examples must name their exact record', () => {
  const defaultWithMethod = copy(); defaultWithMethod.targets[0].route += '?method=' + defaultWithMethod.targets[0].record_id;
  assert.throws(() => validateTargets(defaultWithMethod));
  const wrongExample = copy(); wrongExample.targets[10].route = wrongExample.targets[10].route.replace(wrongExample.targets[10].record_id, 'other');
  assert.throws(() => validateTargets(wrongExample));
});

test('target URLs stay within live or local candidate site roots', () => {
  const row = original.targets[1];
  assert.equal(targetURL('https://cuiyist.github.io/mattersyn-site/', row), 'https://cuiyist.github.io/mattersyn-site/' + row.route);
  assert.equal(targetURL('http://127.0.0.1:8172/candidate', row), 'http://127.0.0.1:8172/candidate/' + row.route);
  for (const route of ['https://other.invalid/material.html', '//other.invalid/material.html', '../material.html']) {
    assert.throws(() => targetURL('http://127.0.0.1:8172/candidate/', { route }));
  }
  const outside = copy(); outside.targets[0].route = 'https://other.invalid/material.html';
  assert.throws(() => validateTargets(outside));
});

test('after examples require measured inline labels of at least12 actual screen pixels', () => {
  const example = original.targets[10];
  const measured = (px) => ({ inline_svg_count: 1, minimum_measured_screen_font_px: px });
  checkAfterLabels('after', example, measured(12));
  assert.throws(() => checkAfterLabels('after', example, measured(11.99)));
  assert.throws(() => checkAfterLabels('after', example, { inline_svg_count: 0, minimum_measured_screen_font_px: 16 }));
  assert.throws(() => checkAfterLabels('after', example, { inline_svg_count: 1, minimum_measured_screen_font_px: null }));
  checkAfterLabels('before', example, measured(8));
  checkAfterLabels('after', original.targets[0], measured(8));
});

test('direct no-argument invocation is inert and does not require Playwright or a browser', () => {
  const script = fileURLToPath(new URL('./protocol-scenes-check.mjs', import.meta.url));
  const result = spawnSync(process.execPath, [script], { encoding: 'utf8', env: { ...process.env, PLAYWRIGHT_DIR: 'Z:/definitely-not-installed' } });
  assert.equal(result.status, 0, result.stderr);
  assert.deepEqual(JSON.parse(result.stdout), { status: 'DEFAULT_INERT', browser_started: false, network_calls: 0, screenshots_created: 0 });
});
