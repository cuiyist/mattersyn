// Private Part I proposal. No-argument execution/import performs no browser I/O.
// Capture only after Root integrates the matching build metadata/DOM contract.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';

export const TARGET_SCHEMA = 'mattersyn-method-family-targets/2';
export const LEGACY_TARGET_SCHEMA = 'mattersyn-method-family-targets/1';
export const J_PREVIEW_POLICY = 'three-families-two-papers/1';
export const LEGACY_PREVIEW_POLICY = 'global-six/1';
export const FAMILY_SCHEMA = 'mattersyn-method-families-compact/1';
export const MATERIALS = Object.freeze({CdSe: 'cdse-d923c5', CdS: 'cds-fad408', ZnS: 'zns-b01883', InAs: 'inas-a2e691', PbS: 'pbs-7e1774', Au: 'au-3325c2'});
export const VIEWPORTS = Object.freeze([{width: 1440, height: 900}, {width: 390, height: 844}]);
const hex = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
const safeID = value => typeof value === 'string' && /^[a-z0-9._-]+$/.test(value);
const sha = raw => createHash('sha256').update(raw).digest('hex');
export function stableJSON(value) {
  if (Array.isArray(value)) return '[' + value.map(stableJSON).join(',') + ']';
  if (value && typeof value === 'object') return '{' + Object.keys(value).sort().map(key => JSON.stringify(key) + ':' + stableJSON(value[key])).join(',') + '}';
  return JSON.stringify(value);
}
export function targetURL(base, target, recordID = null) {
  const root = new URL(base);
  assert(['https:', 'http:'].includes(root.protocol) && !root.username && !root.password && !root.search && !root.hash);
  if (!root.pathname.endsWith('/')) root.pathname += '/';
  const url = new URL(target.route, root);
  assert.equal(url.origin, root.origin);
  assert(url.pathname.startsWith(root.pathname) && !url.hash);
  if (recordID !== null) {assert(safeID(recordID)); url.searchParams.set('method', recordID);}
  return url.href;
}
export function validateTargets(value, phase) {
  assert(value && value.schema === TARGET_SCHEMA && value.phase === phase);
  assert.deepEqual(Object.keys(value).sort(), ['phase', 'preview_policy', 'schema', 'targets']);
  assert([J_PREVIEW_POLICY, LEGACY_PREVIEW_POLICY].includes(value.preview_policy), 'Explicit known preview policy required');
  if (phase === 'after') assert.equal(value.preview_policy, J_PREVIEW_POLICY, 'AFTER must use J three-family/two-paper preview');
  assert(Array.isArray(value.targets) && value.targets.length === 6);
  assert.deepEqual(value.targets.map(t => t.formula), Object.keys(MATERIALS));
  const common = ['id', 'formula', 'material_id', 'route', 'default_record_id', 'record_json_bytes', 'record_json_sha256'];
  const after = ['family_metadata_sha256', 'family_count', 'paper_card_count', 'first_family_id', 'first_family_papers'];
  for (const t of value.targets) {
    assert.deepEqual(Object.keys(t).sort(), [...common, ...after].sort());
    assert.equal(t.id, 'method-list-' + t.formula.toLowerCase());
    assert.equal(t.material_id, MATERIALS[t.formula]);
    assert(safeID(t.default_record_id) && Number.isSafeInteger(t.record_json_bytes) && t.record_json_bytes > 0 && hex(t.record_json_sha256));
    const expected = t.formula === 'CdSe' ? 'cdse.html' : 'material.html?id=' + t.material_id;
    assert.equal(t.route, expected, 'A method-list target must visit its actual default without method=');
    {
      assert(hex(t.family_metadata_sha256) && safeID(t.first_family_id));
      for (const key of ['family_count', 'paper_card_count', 'first_family_papers']) assert(Number.isSafeInteger(t[key]) && t[key] > 0);
    }
  }
  return value.targets;
}
export function beforeTargetsFromProtocolSnapshot(protocol, methodSnapshot) {
  const protocolCount = protocol?.schema === 'mattersyn-protocol-scenes-targets/1' ? 18
    : protocol?.schema === 'mattersyn-protocol-scenes-targets/2' ? 20 : null;
  assert(protocolCount !== null, 'Exact legacy or K comparison-base protocol schema required');
  assert(Array.isArray(protocol.targets) && protocol.targets.length === protocolCount);
  assert(methodSnapshot && methodSnapshot.phase === 'after', 'Exact comparison-base method snapshot required');
  const legacy = methodSnapshot.schema === LEGACY_TARGET_SCHEMA;
  if (legacy) assert.deepEqual(Object.keys(methodSnapshot).sort(), ['phase', 'schema', 'targets']);
  else validateTargets(methodSnapshot, 'after');
  const value = {...structuredClone(methodSnapshot), schema: TARGET_SCHEMA, phase: 'before',
    preview_policy: legacy ? LEGACY_PREVIEW_POLICY : methodSnapshot.preview_policy};
  validateTargets(value, 'before');
  const defaults = protocol.targets.filter(t => t.group === 'benchmark-default' && Object.hasOwn(MATERIALS, t.formula));
  for (const target of value.targets) {
    const matching = defaults.filter(t => t.formula === target.formula); assert.equal(matching.length, 1);
    const prior = matching[0];
    assert.equal(target.route, prior.route); assert.equal(target.default_record_id, prior.record_id);
    assert.equal(target.record_json_bytes, prior.record_json_bytes); assert.equal(target.record_json_sha256, prior.record_json_sha256);
  }
  return value;
}
export function previewCardMask(groups, policy) {
  assert([J_PREVIEW_POLICY, LEGACY_PREVIEW_POLICY].includes(policy), 'Explicit known preview policy required');
  let index = 0;
  return groups.families.map((family, familyIndex) => family.papers.map((paper, paperIndex) =>
    policy === LEGACY_PREVIEW_POLICY ? index++ < 6 : familyIndex < 3 && paperIndex < 2));
}
export function checkFamilyMetadata(groups, rows, target) {
  assert.equal(groups?.schema, FAMILY_SCHEMA);
  assert.equal(groups.default_record_id, target.default_record_id);
  assert.equal(sha(stableJSON(groups)), target.family_metadata_sha256, 'Built family metadata differs from fixed target snapshot');
  assert.equal(groups.families.length, target.family_count);
  assert.equal(groups.families[0].id, target.first_family_id);
  assert.equal(groups.families[0].paper_count, target.first_family_papers);
  const members = [], familyIDs = new Set();
  for (const f of groups.families) {
    assert(!familyIDs.has(f.id)); familyIDs.add(f.id); assert.equal(f.paper_count, f.papers.length);
    for (const p of f.papers) {assert(typeof p.citation === 'string' && p.citation.trim()); assert(p.record_ids.length > 0); members.push(...p.record_ids);}
  }
  assert.equal(groups.families.reduce((n, f) => n + f.paper_count, 0), target.paper_card_count);
  assert.equal(new Set(members).size, members.length);
  assert.deepEqual([...members].sort(), rows.filter(r => r.is_synthesis_route && r.collection === 'reviewed_literature').map(r => r.record_id).sort());
  return groups;
}

// Serializable browser-only function. Text is public UI; no source evidence/body IO.
export function methodListMetrics(root) {
  const box = node => {const r = node.getBoundingClientRect(); return {left: r.left, right: r.right, top: r.top, bottom: r.bottom, width: r.width, height: r.height};};
  const visible = node => {for(let ancestor=node;ancestor;ancestor=ancestor.parentElement){const style=getComputedStyle(ancestor);if(style.display==='none'||style.visibility==='hidden')return false;}const r=box(node);return r.width>0&&r.height>0;};
  const labels = [];
  for (const node of root.querySelectorAll('h3,p,button,label,select')) {
    if (!visible(node)) continue;
    const style = getComputedStyle(node), r = box(node);
    const text = [...node.childNodes].filter(n => n.nodeType === Node.TEXT_NODE && n.textContent.trim());
    if (node.tagName === 'SELECT') labels.push({tag: 'select', font_px: parseFloat(style.fontSize) * (node.offsetHeight ? r.height / node.offsetHeight : 1), bounds: r, parent_bounds: box(node.parentElement)});
    for (const n of text) {
      const range = document.createRange(); range.selectNodeContents(n);
      for (const part of range.getClientRects()) labels.push({tag: node.tagName.toLowerCase(), font_px: parseFloat(style.fontSize) * (node.offsetHeight ? r.height / node.offsetHeight : 1), bounds: {left: part.left, right: part.right, top: part.top, bottom: part.bottom, width: part.width, height: part.height}, parent_bounds: r});
    }
  }
  return {bounds: box(root), initial_card_limit:Object.hasOwn(root.dataset,'initialCardLimit')?Number(root.dataset.initialCardLimit):null,initial_family_limit:Object.hasOwn(root.dataset,'initialFamilyLimit')?Number(root.dataset.initialFamilyLimit):null,initial_papers_per_family:Object.hasOwn(root.dataset,'initialPapersPerFamily')?Number(root.dataset.initialPapersPerFamily):null, visible_card_count:[...root.querySelectorAll('.reader-paper-card')].filter(visible).length,toggle_count:root.querySelectorAll('.reader-family-toggle').length,toggle_expanded:root.querySelector('.reader-family-toggle')?.getAttribute('aria-expanded')||null,page_overflow: document.documentElement.scrollWidth > innerWidth + 2, labels,
    families: [...root.querySelectorAll('.reader-method-family')].map(f => ({id: f.dataset.familyId, label:f.querySelector('h3')?.textContent || '',adoption:f.querySelector('.reader-family-adoption')?.textContent || '',visible:visible(f),paper_cards: [...f.querySelectorAll('.reader-paper-card')].map(c => ({record_ids: JSON.parse(c.dataset.recordIds || 'null'), hidden: !visible(c)}))})),
    selected: root.querySelector('.reader-paper-choice[aria-pressed="true"]')?.dataset.recordId || null,
    text: root.textContent};
}
export function checkMethodListMetrics(metrics, target, groups, {expanded=false, phase='after', previewPolicy=J_PREVIEW_POLICY}={}) {
  assert(['before','after'].includes(phase));
  assert([J_PREVIEW_POLICY,LEGACY_PREVIEW_POLICY].includes(previewPolicy));
  if (phase === 'after') assert.equal(previewPolicy,J_PREVIEW_POLICY,'AFTER cannot accept the legacy preview');
  assert.equal(metrics.page_overflow, false, 'Horizontal page overflow');
  assert.equal(metrics.selected, target.default_record_id);
  if (previewPolicy === LEGACY_PREVIEW_POLICY) {
    assert.equal(metrics.initial_card_limit,6);assert.equal(metrics.initial_family_limit,null);assert.equal(metrics.initial_papers_per_family,null);
  } else {
    assert.equal(metrics.initial_card_limit,null);assert.equal(metrics.initial_family_limit,3);assert.equal(metrics.initial_papers_per_family,2);
  }
  const mask=previewCardMask(groups,previewPolicy),initial=mask.flat().filter(Boolean).length;
  assert.equal(metrics.visible_card_count,expanded?target.paper_card_count:initial,'Actual visible cards violate the exact phase preview');
  assert.equal(metrics.toggle_count,target.paper_card_count>initial?1:0,'Expected one Show all control exactly when cards are hidden');
  if(metrics.toggle_count)assert.equal(metrics.toggle_expanded,String(expanded));
  assert.deepEqual(metrics.families.map(f => f.id), groups.families.map(f => f.id));
  assert.deepEqual(metrics.families.map(f => f.paper_cards.map(p => p.record_ids)), groups.families.map(f => f.papers.map(p => p.record_ids)));
  for (const [i,family] of metrics.families.entries()) {
    const expected=groups.families[i];assert.equal(family.label,expected.label);assert.equal(family.adoption,`${expected.paper_count} ${expected.paper_count===1?'paper':'papers'}`);
    assert.deepEqual(family.paper_cards.map(card=>!card.hidden),mask[i].map(shown=>expanded||shown),'Cards must be the first two of each first three families, or the exact legacy BEFORE policy');
    assert.equal(family.visible,family.paper_cards.some(card=>!card.hidden),'A family heading must be hidden when all its cards are hidden');
  }
  assert(metrics.labels.length > 0);
  for (const label of metrics.labels) {
    assert(Number.isFinite(label.font_px) && label.font_px >= 12, 'Method-list text is below 12 displayed px');
    assert(label.bounds.width > 0 && label.bounds.height > 0);
    assert(label.bounds.left >= label.parent_bounds.left - 2 && label.bounds.right <= label.parent_bounds.right + 2, 'Method-list label clips its container');
    assert(label.bounds.left >= metrics.bounds.left - 2 && label.bounds.right <= metrics.bounds.right + 2, 'Method-list label clips its section');
  }
  assert(!/source_extracted|machine.extracted|reviewed\s+(?:recipe|record|method)/i.test(metrics.text), 'Method list introduces status wording');
}
function picture(out, file) {const raw = fs.readFileSync(path.join(out, file)); return {file, bytes: raw.length, sha256: sha(raw)};}
async function downloadPin(context, page, recordID) {
  const href = await page.locator('.reader-switch a').filter({hasText: 'Download JSON'}).getAttribute('href');
  assert(href); const url = new URL(href, page.url());
  assert(url.pathname.endsWith('/data/records/' + recordID + '.json'), 'Download JSON changed destination');
  const response = await context.request.get(url.href); assert.equal(response.status(), 200); const raw = await response.body();
  return {bytes: raw.length, sha256: sha(raw)};
}
async function waitRecord(page, recordID) {
  await page.waitForFunction(rid => document.querySelector('main')?.dataset.readerReady === rid, recordID, {timeout: 60000});
  assert.equal(new URL(page.url()).searchParams.get('method'), recordID);
}
async function visit(browser, args, target, viewport) {
  const context = await browser.newContext({viewport, deviceScaleFactor: 1, serviceWorkers: 'block', reducedMotion: 'reduce'}), page = await context.newPage(), errors = [];
  page.on('pageerror', e => errors.push(String(e.message || e)));
  const row = {id: target.id, formula: target.formula, viewport, record_id: target.default_record_id};
  try {
    const response = await page.goto(targetURL(args.base, target), {waitUntil: 'domcontentloaded', timeout: 90000}); assert.equal(response?.status(), 200);
    await waitRecord(page, target.default_record_id);
    const root = page.locator('.reader-method-families').first();
    await root.waitFor({state: 'visible'}); await root.scrollIntoViewIfNeeded();
    row.download_json = await downloadPin(context, page, target.default_record_id);
    assert.equal(row.download_json.bytes, target.record_json_bytes); assert.equal(row.download_json.sha256, target.record_json_sha256);
    const materialResponse = await context.request.get(new URL('data/materials/' + target.material_id + '.json', args.base.endsWith('/') ? args.base : args.base + '/').href);
    assert.equal(materialResponse.status(), 200); const material = await materialResponse.json(), groups = checkFamilyMetadata(material.method_families, material.records, target);
    row.preview_policy=args.previewPolicy;
    row.metrics = await root.evaluate(methodListMetrics); checkMethodListMetrics(row.metrics, target, groups,{phase:args.phase,previewPolicy:args.previewPolicy});
    const initialMask=previewCardMask(groups,args.previewPolicy),initialCount=initialMask.flat().filter(Boolean).length;
    if (args.phase === 'after') {
      if (target.paper_card_count>initialCount) {
        const toggle=root.locator('.reader-family-toggle');assert.equal(await toggle.getAttribute('aria-expanded'),'false');await toggle.click();
        assert.equal(await toggle.getAttribute('aria-expanded'),'true');assert.equal(await root.locator('.reader-paper-card:visible').count(),target.paper_card_count);
        assert.equal(await page.locator('main[data-reader-ready]').getAttribute('data-reader-ready'),target.default_record_id);
        row.expanded_metrics=await root.evaluate(methodListMetrics);checkMethodListMetrics(row.expanded_metrics,target,groups,{expanded:true,phase:args.phase,previewPolicy:args.previewPolicy});
        row.show_all_probe={papers:target.paper_card_count,default_unchanged:true,passed:true};
      } else row.show_all_probe={status:'all_cards_initially_visible'};
      const variantPaper = groups.families.flatMap(f => f.papers).find(p => p.record_ids.length > 1);
      if (variantPaper) {
        await page.goto(targetURL(args.base, target, variantPaper.record_ids[0]), {waitUntil: 'domcontentloaded'});
        await waitRecord(page, variantPaper.record_ids[0]);
        const rid = variantPaper.record_ids[1], select = root.locator('select').filter({has: page.locator('option[value="' + rid + '"]')});
        await select.selectOption(rid); await waitRecord(page, rid);
        assert.equal(await page.locator('.reader-paper-choice[aria-pressed="true"]').getAttribute('data-record-id'), rid);
        row.variant_probe = {record_id: rid, passed: true};
      } else row.variant_probe = {status: 'no_same_paper_variants_in_material'};
      const hiddenPaper = groups.families.flatMap((f,i) => f.papers.filter((p,j) => !initialMask[i][j]))[0];
      if (hiddenPaper) {
        const rid = hiddenPaper.record_ids[0]; await page.goto(targetURL(args.base, target, rid), {waitUntil: 'domcontentloaded'}); await waitRecord(page, rid);
        const selected = page.locator('.reader-paper-choice[aria-pressed="true"]'); assert.equal(await selected.getAttribute('data-record-id'), rid); assert(await selected.isVisible());
        row.deep_link_probe = {record_id: rid, passed: true};
      } else row.deep_link_probe = {status: 'no_hidden_paper_cards_in_material'};
      // Capture the actual default list after probes; no changed scientific record.
      await page.goto(targetURL(args.base, target), {waitUntil: 'domcontentloaded'}); await waitRecord(page, target.default_record_id);
    }
    await root.scrollIntoViewIfNeeded(); await page.waitForTimeout(300);
    row.page_overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2); assert.equal(row.page_overflow, false);
    assert.deepEqual(errors, []); const stem = target.id + '-' + viewport.width;
    await page.screenshot({path: path.join(args.out, stem + '-viewport.png')}); await root.screenshot({path: path.join(args.out, stem + '-methods.png')});
    row.screenshots = [picture(args.out, stem + '-viewport.png'), picture(args.out, stem + '-methods.png')]; row.automated_pass = true; row.human_visual_review = 'pending';
  } catch (error) {row.automated_pass = false; row.error = String(error.message || error);}
  finally {row.page_errors = errors; await context.close();}
  return row;
}
export function argumentsFor(argv) {
  const a = {};
  for (let i = 0; i < argv.length; i += 2) {assert(['--base', '--out', '--phase', '--targets'].includes(argv[i]) && typeof argv[i + 1] === 'string'); const key = argv[i].slice(2); assert(!Object.hasOwn(a, key)); a[key] = argv[i + 1];}
  assert(a.base && a.out && a.targets && ['before', 'after'].includes(a.phase)); return a;
}
export async function main(argv = process.argv.slice(2)) {
  if (!argv.length) {console.log(JSON.stringify({status: 'DEFAULT_INERT', browser_started: false, network_calls: 0, screenshots_created: 0})); return;}
  const args = argumentsFor(argv), raw = fs.readFileSync(args.targets), targets = validateTargets(JSON.parse(raw), args.phase);
  args.previewPolicy=JSON.parse(raw).preview_policy;
  for (const target of targets) targetURL(args.base, target);
  args.out = path.resolve(args.out); assert(!fs.existsSync(args.out), 'Preserve previous captures; choose fresh output');
  const require = createRequire(path.join(process.env.PLAYWRIGHT_DIR || process.cwd(), 'package.json')), {chromium} = require('playwright'); fs.mkdirSync(args.out);
  const receipt = {schema: 'mattersyn-method-family-capture/1', at_utc: new Date().toISOString(), phase: args.phase, base: args.base, preview_policy:args.previewPolicy, target_set_sha256: sha(raw), workflow_commit: process.env.GITHUB_SHA || null, anonymous: true, browser_started: false, uploads: 0, records_changed: 0, publication_checks_replaced: false, pages: []};
  const save = () => fs.writeFileSync(path.join(args.out, 'receipt.json'), JSON.stringify(receipt, null, 2) + '\n'); save(); let browser;
  try {browser = await chromium.launch({args: ['--disable-gpu']}); receipt.browser_started = true; for (const t of targets) for (const v of VIEWPORTS) {receipt.pages.push(await visit(browser, args, t, v)); save();}}
  finally {if (browser) await browser.close(); save();}
  receipt.summary = {views: receipt.pages.length, failures: receipt.pages.filter(p => !p.automated_pass).length}; save(); assert.equal(receipt.summary.views, 12); assert.equal(receipt.summary.failures, 0);
}
if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) main().catch(e => {console.error(e.message || e); process.exitCode = 1;});
