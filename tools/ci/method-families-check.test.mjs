import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {TARGET_SCHEMA, FAMILY_SCHEMA, MATERIALS, VIEWPORTS, validateTargets, targetURL, stableJSON, checkFamilyMetadata, checkMethodListMetrics, argumentsFor, beforeTargetsFromProtocolSnapshot, methodListMetrics} from './method-families-check.mjs';

const sha = value => createHash('sha256').update(value).digest('hex');
function groups() {return {schema: FAMILY_SCHEMA, default_record_id: 'r1', families: [{id: 'f', kind: 'synthesis', label: 'Own route - own source', paper_count: 1, papers: [{citation: 'Alpha et al. (2000)', record_ids: ['r1','r2']}]}]};}
function targets(phase = 'after') {return {schema: TARGET_SCHEMA, phase, targets: Object.entries(MATERIALS).map(([formula, material_id]) => ({id: 'method-list-' + formula.toLowerCase(), formula, material_id, route: formula === 'CdSe' ? 'cdse.html' : 'material.html?id=' + material_id, default_record_id: 'r1', record_json_bytes: 100, record_json_sha256: 'a'.repeat(64), ...(phase === 'after' ? {family_metadata_sha256: sha(stableJSON(groups())), family_count: 1, paper_card_count: 1, first_family_id: 'f', first_family_papers: 1} : {})}))};}
const rows = ['r1','r2'].map(record_id => ({record_id, is_synthesis_route: true, collection: 'reviewed_literature'}));
const rect = (left, top, width, height) => ({left, top, right: left + width, bottom: top + height, width, height});
function metrics() {return {selected:'r1',initial_card_limit:6,visible_card_count:1,toggle_count:0,toggle_expanded:null,page_overflow: false, bounds: rect(0,0,390,400), text: 'Own route Alpha et al. 1 paper Variant', labels: [{font_px: 13, bounds: rect(10,10,80,20), parent_bounds: rect(5,5,200,30)}], families: [{id:'f',visible:true,paper_cards:[{record_ids:['r1','r2'],hidden:false}]}]};}

test('exact six phases validate independently, preserving changed defaults', () => {
  assert.equal(validateTargets(targets('before'),'before').length,6); assert.equal(validateTargets(targets(),'after').length,6);
  const after = targets(); after.targets[0].default_record_id = 'different-default'; assert.equal(validateTargets(after,'after')[0].default_record_id,'different-default');
  assert.deepEqual(VIEWPORTS.map(x=>x.width),[1440,390]);
});
test('before targets come from the exact prior protocol snapshot, not new defaults', () => {
  const before=targets('before'), protocol={schema:'mattersyn-protocol-scenes-targets/1',targets:[...before.targets.map(t=>({group:'benchmark-default',formula:t.formula,route:t.route,record_id:'old-'+t.formula.toLowerCase(),record_json_bytes:t.record_json_bytes,record_json_sha256:t.record_json_sha256})),...Array.from({length:12},()=>({group:'route-example'}))]};
  const converted=beforeTargetsFromProtocolSnapshot(protocol);assert.equal(converted.targets[0].default_record_id,'old-cdse');assert.equal(converted.phase,'before');
  protocol.targets[0].route+='&method=changed';assert.throws(()=>beforeTargetsFromProtocolSnapshot(protocol));
});
test('missing/extra targets, changed formula/order/material and unknown fields fail', () => {
  for (const mutate of [v=>v.targets.pop(),v=>v.targets.push(v.targets[0]),v=>v.targets.reverse(),v=>v.targets[0].material_id='other',v=>v.targets[0].extra=true]) {const v=targets(); mutate(v); assert.throws(()=>validateTargets(v,'after'));}
});
test('a default target may not include method, protocol, fragments or an external route', () => {
  for (const route of ['material.html?id=cdse-d923c5&method=r1','https://example.com/cdse.html','../cdse.html','cdse.html#protocol','javascript:alert(1)']) {const v=targets();v.targets[0].route=route;assert.throws(()=>validateTargets(v,'after'));}
});
test('raw hash/bytes and grouped expected counters are fixed target data', () => {
  for (const mutate of [t=>t.record_json_sha256='bad',t=>t.record_json_bytes=0,t=>t.family_count=0,t=>t.family_metadata_sha256='z'.repeat(64),t=>t.default_record_id='../x']) {const v=targets();mutate(v.targets[0]);assert.throws(()=>validateTargets(v,'after'));}
  assert.throws(()=>validateTargets(targets('before'),'after'));
});
test('site-relative URLs preserve site prefix and explicit method links', () => {
  const t=targets().targets[0];assert.equal(targetURL('https://host.invalid/site/',t),'https://host.invalid/site/cdse.html');
  assert.equal(new URL(targetURL('https://host.invalid/site',t,'r2')).searchParams.get('method'),'r2');
  assert.throws(()=>targetURL('https://host.invalid/site/',{route:'../escape'}));assert.throws(()=>targetURL('https://user:pass@host.invalid/',t));
});
test('family metadata hash and exact complete membership are checked', () => {
  assert.equal(checkFamilyMetadata(groups(),rows,targets().targets[0]).families.length,1);
  for (const mutate of [g=>g.default_record_id='r2',g=>g.families[0].papers[0].record_ids.pop(),g=>g.families[0].papers[0].citation='Wrong',g=>g.families[0].paper_count=2]) {const g=groups();mutate(g);assert.throws(()=>checkFamilyMetadata(g,rows,targets().targets[0]));}
  assert.throws(()=>checkFamilyMetadata(groups(),[...rows,{record_id:'r3',is_synthesis_route:true,collection:'reviewed_literature'}],targets().targets[0]));
});
test('paper count counts folded cards, not variants', () => {
  const t=targets().targets[0];assert.equal(checkFamilyMetadata(groups(),rows,t).families[0].paper_count,1);t.paper_card_count=2;assert.throws(()=>checkFamilyMetadata(groups(),rows,t));
});
test('font, overflow, container clipping and dropped variant regressions fail', () => {
  checkMethodListMetrics(metrics(),targets().targets[0],groups());
  for (const mutate of [m=>m.labels[0].font_px=11.99,m=>m.page_overflow=true,m=>m.labels[0].bounds.right=500,m=>m.families[0].paper_cards[0].record_ids.pop(),m=>m.selected='r2',m=>m.text+=' reviewed recipes']) {const m=metrics();mutate(m);assert.throws(()=>checkMethodListMetrics(m,targets().targets[0],groups()));}
});
test('browser metric collector includes direct label text/select and excludes hidden text', () => {
  const prior={document:globalThis.document,Node:globalThis.Node,innerWidth:globalThis.innerWidth,getComputedStyle:globalThis.getComputedStyle};
  const node=(tag,hidden=false)=>({tagName:tag,_hidden:hidden,offsetHeight:20,dataset:{},childNodes:[],getBoundingClientRect:()=>rect(10,10,120,20),closest:()=>hidden?{}:null});
  const title=node('H3'),hidden=node('BUTTON',true),select=node('SELECT');
  const text={nodeType:3,textContent:'Own route',owner:title};title.childNodes=[text];hidden.childNodes=[{nodeType:3,textContent:'Hidden',owner:hidden}];select.parentElement={getBoundingClientRect:()=>rect(5,5,200,30)};
  const card=node('ARTICLE');card.dataset.recordIds='["r1","r2"]';const family={tagName:'SECTION',offsetHeight:20,dataset:{familyId:'f'},getBoundingClientRect:()=>rect(5,5,200,30),querySelectorAll:()=>[card]};
  const root={dataset:{initialCardLimit:'6'},textContent:'Own route',getBoundingClientRect:()=>rect(0,0,390,400),querySelectorAll:term=>term==='.reader-method-family'?[family]:term==='.reader-paper-card'?[card]:term==='.reader-family-toggle'?[]:[title,hidden,select],querySelector:term=>term==='.reader-family-toggle'?null:({dataset:{recordId:'r1'}})};
  try {
    globalThis.Node={TEXT_NODE:3};globalThis.innerWidth=390;globalThis.getComputedStyle=n=>({fontSize:'13px',display:n._hidden?'none':'block',visibility:'visible'});
    globalThis.document={documentElement:{scrollWidth:390},createRange:()=>{let own;return{selectNodeContents:n=>{own=n;},getClientRects:()=>[rect(10,10,70,18)]};}};
    const measured=methodListMetrics(root);assert.equal(measured.labels.length,2);assert.equal(measured.labels[0].font_px,13);assert.equal(measured.labels[1].tag,'select');assert.equal(measured.selected,'r1');assert.deepEqual(measured.families[0].paper_cards[0].record_ids,['r1','r2']);
  } finally {for(const [key,value] of Object.entries(prior)){if(value===undefined)delete globalThis[key];else globalThis[key]=value;}}
});
test('stable JSON projection is independent of object-key insertion order', () => {assert.equal(stableJSON({b:[2,{x:1}],a:'é'}),stableJSON({a:'é',b:[2,{x:1}]}));});
test('CLI requires exact paired options and phase; duplicate/unknown options fail', () => {
  assert.equal(argumentsFor(['--base','https://host.invalid/','--out','out','--phase','after','--targets','target.json']).phase,'after');
  for (const args of [[],['--phase','after'],['--base','url','--base','url'],['--force','yes'],['--out']]) assert.throws(()=>argumentsFor(args));
});
test('direct no-argument helper remains inert without Playwright, outputs or network', () => {
  const file=fileURLToPath(new URL('./method-families-check.mjs',import.meta.url));const r=spawnSync(process.execPath,[file],{encoding:'utf8'});assert.equal(r.status,0,r.stderr);assert.deepEqual(JSON.parse(r.stdout),{status:'DEFAULT_INERT',browser_started:false,network_calls:0,screenshots_created:0});
});

test('global initial limit and hidden family headings are enforced on actual rendered metrics',()=>{
 const g=groups();g.families[0].papers=Array.from({length:8},(_,i)=>({citation:'Own author',record_ids:['r'+i]}));g.families[0].paper_count=8;
 const target={...targets().targets[0],paper_card_count:8},m=metrics();m.visible_card_count=6;m.toggle_count=1;m.toggle_expanded='false';m.families[0].paper_cards=g.families[0].papers.map((p,i)=>({record_ids:p.record_ids,hidden:i>=6}));checkMethodListMetrics(m,target,g);
 const all=structuredClone(m);all.visible_card_count=8;all.toggle_expanded='true';all.families[0].paper_cards.forEach(c=>c.hidden=false);checkMethodListMetrics(all,target,g,{expanded:true});
 for(const mutate of [x=>x.visible_card_count=8,x=>x.toggle_count=2,x=>x.families[0].visible=false]){const bad=structuredClone(m);mutate(bad);assert.throws(()=>checkMethodListMetrics(bad,target,g));}
});
