import fs from 'node:fs';
import assert from 'node:assert/strict';
import {dirname, isAbsolute, join, relative, resolve} from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {parseArgs} from 'node:util';

const revision = '';
const {values} = parseArgs({options: {'fixture-root': {type: 'string'}, help: {type: 'boolean', short: 'h'}}});
if (values.help) {
  console.log('Usage: node runtime-contract-check.mjs [--fixture-root PATH_TO_JP0219348_PACKAGE]');
  console.log('Reads private review fixtures and the tracked chemicalEntry module. Does not write or approve source data.');
  process.exit(0);
}
const scriptDir = dirname(fileURLToPath(import.meta.url));
function repositoryRoot(start) {
  for (let current = start; ; current = dirname(current)) {
    if (fs.existsSync(join(current, 'recipe-atlas', 'static', 'chemical-viewer.mjs'))) return current;
    if (dirname(current) === current) throw new Error('Cannot locate the tracked recipe-atlas/static/chemical-viewer.mjs module.');
  }
}
const project = repositoryRoot(scriptDir);
const packageRoot = resolve(values['fixture-root'] ?? resolve(scriptDir, revision ? '../..' : '..'));
const proposalRoot = join(packageRoot, 'canonical-binding-proposal', revision);
if (!['bindings-proposal.json', 'material-slot-map.json'].every(name => fs.existsSync(join(proposalRoot, name)))) {
  throw new Error('Private audit fixtures are not included in the public source. Supply --fixture-root PATH_TO_JP0219348_PACKAGE containing this proposal revision.');
}
function readJson(base, name) {
  const file = resolve(base, name), child = relative(base, file);
  if (isAbsolute(child) || child === '..' || child.startsWith('..' + (process.platform === 'win32' ? String.fromCharCode(92) : '/'))) {
    throw new Error('Fixture reference must remain inside its source package.');
  }
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}
const read = name => readJson(proposalRoot, name);
const {chemicalEntry} = await import(pathToFileURL(join(project, 'recipe-atlas', 'static', 'chemical-viewer.mjs')).href);
const bindings = read('bindings-proposal.json');
const maps = read('material-slot-map.json').bindings;
const entries = new Map();
for (const x of maps) {
  const all = readJson(packageRoot, x.reference.file);
  entries.set(x.registry_id, all.entries[Number(x.reference.json_pointer.split('/').at(-1))]);
}
let checks=0;
for(const x of maps){const base=entries.get(x.registry_id);assert.equal(chemicalEntry({entries,bindings},x.record_id,x.material_id),base);checks++;}
// Approval below exists only in a transient test fixture. The authored files stay false.
const fixture=structuredClone(bindings);
for(const x of maps){const note=fixture.bindingNotes[x.record_id][x.material_id];note.binding_approved=true;note.viewOverrides.formula='PROHIBITED_TEST_OVERRIDE';const scoped=chemicalEntry({entries,bindings:fixture},x.record_id,x.material_id);assert.equal(scoped.name,x.viewOverrides.name);assert.equal(scoped.caption,x.viewOverrides.caption);assert.equal(scoped.sourceBindingCaption,x.viewOverrides.caption);assert.deepEqual(scoped.limitations,x.viewOverrides.limitations);assert.equal(scoped.formula,entries.get(x.registry_id).formula);assert.equal(scoped.model3dPath,entries.get(x.registry_id).model3dPath);checks+=6;}
const feed=chemicalEntry({entries,bindings:fixture},'heo-2003-in66-route','feed-water');const wash=chemicalEntry({entries,bindings:fixture},'heo-2003-in66-route','wash-water');assert.notEqual(feed.caption,wash.caption);assert.ok(feed.caption.includes('grade is unreported'));assert.ok(wash.caption.includes('deionized'));checks+=3;
console.log(JSON.stringify({status:'passed',checks,scope:'Actual chemicalEntry function; pending and hypothetical approved in-memory fixtures only. No DOM, browser, asset science or public integration audit.'}));
