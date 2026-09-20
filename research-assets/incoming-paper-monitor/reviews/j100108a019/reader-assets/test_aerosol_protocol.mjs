import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {test} from 'node:test';
import {AEROSOL_ACTIONS,buildAerosolScene,sourceQuantity,supportsAerosolOperation,createAerosolArt,createAerosolConditionGrid} from './aerosol-protocol.mjs';
const here=path.dirname(fileURLToPath(import.meta.url)),root=path.dirname(here);
const load=name=>JSON.parse(fs.readFileSync(path.join(root,'canonical-drafts',name),'utf8'));
const variants=['1p0','2p0','6p0'].map(v=>load(`littau-1993-si-aerosol-${v}.json`));
const sample=variants[2],op=action=>sample.operations.find(o=>o.action===action),scene=action=>buildAerosolScene(op(action),sample);

test('five distinct apparatus scenes for each real formulation',()=>{
  for(const record of variants){
    const scenes=record.operations.map(o=>buildAerosolScene(o,record));
    assert.equal(scenes.length,5);assert.equal(new Set(scenes.map(s=>s.svg)).size,5);
    for(const s of scenes){
      assert.match(s.svg,/viewBox="0 0 760 525"/);
      assert.equal((s.svg.match(/data-active="true"/g)||[]).length,1);
      assert.match(s.svg,new RegExp(`data-stage="${s.scene}" data-active="true"`));
      assert.match(s.svg,/overview-furnace-1/);assert.match(s.svg,/overview-furnace-2/);assert.match(s.svg,/overview-serial-bubblers/);
      assert.doesNotMatch(s.svg,/scene-vial|neutral-reaction-vessel|flask|batch duration/i);
    }
  }
});
test('stock flow remains mixture flow and variant differences are rendered',()=>{
  const flows=variants.map(r=>buildAerosolScene(r.operations[0],r).conditions.find(x=>x.label==='Stock-mixture flow'));
  assert.deepEqual(flows.map(x=>x.value),['1.0 sccm','2.0 sccm','6.0 sccm']);
  assert.ok(flows.every(x=>/not pure disilane/.test(x.note)));
  const s=scene('gas_feed');assert.match(s.svg,/0.1 % in He/);assert.match(s.svg,/Oxisorb/);assert.match(s.svg,/helium-through-purifier/);
  assert.equal(s.conditions.find(x=>x.label==='Combined pyrolysis feed').value,'300 sccm');
  assert.equal(s.conditions.find(x=>x.label==='Disilane partial pressure').value,'20 mTorr');
});
test('pyrolysis preserves conflicting temperatures and residence meaning',()=>{
  const s=scene('aerosol_pyrolysis');
  assert.match(s.svg,/860 °C/);assert.match(s.svg,/865 °C/);assert.match(s.svg,/conflict/);
  assert.match(s.svg,/external-tube-furnace-1/);assert.match(s.svg,/data-role="wall-deposit"/);
  assert.equal(s.conditions.find(x=>x.label==='Heated-zone residence time').value,'≈60 ms');
  assert.equal(s.conditions.find(x=>x.label==='Run duration').value,'Not reported');
  assert.match(s.notes.join(' '),/Thermocouples were removed/);
});
test('quench shows both gas streams, raw ratios and first aperture',()=>{
  const s=scene('gas_dilution_quench');
  for(const expected of ['1000 sccm','6000 sccm','1:23','1:6','200–300 °C','0.6 mm','first-aperture'])assert.ok(s.svg.includes(expected),expected);
  assert.equal(s.conditions.find(x=>x.label==='Exact local pressure').value,'Not reported');
  assert.equal(s.conditions.find(x=>x.label==='Cooling time').value,'Not reported');
  assert.doesNotMatch(s.svg,/1:24|cooling bath|ice|1\.4 atm/);
});
test('oxidation uses its own furnace, aperture, speed and residence',()=>{
  const s=scene('aerosol_oxidation');
  for(const expected of ['external-tube-furnace-2','second-aperture','1–2 mm','700 °C','≈430 cm/s','≈20 ms'])assert.ok(s.svg.includes(expected),expected);
  assert.doesNotMatch(s.svg,/860 °C|865 °C|60 ms/);
  assert.match(s.notes.join(' '),/not a universal measured shell/);
});
test('collection has two serial EG fractions and never inherits furnace conditions',()=>{
  const s=scene('sequential_bubbler_collection');
  assert.match(s.svg,/data-role="prebubbler" data-serial-position="1"/);
  assert.match(s.svg,/data-role="frit-collector" data-serial-position="2"/);
  assert.match(s.svg,/data-flow="prebubbler-to-frit-collector"/);
  assert.match(s.svg,/silanized-coarse-glass-frit/);
  assert.equal((s.svg.match(/9 cm³ ethylene glycol/g)||[]).length,2);
  assert.doesNotMatch(s.svg,/700|860|865|20 ms|60 ms|1\.4 atm/);
  for(const label of ['Collection temperature','Collection duration','Collection pressure'])assert.equal(s.conditions.find(x=>x.label===label).value,'Not reported');
  assert.match(s.notes.join(' '),/SiH₂Cl₂ in toluene/);
  assert.match(s.notes.join(' '),/two-thirds.*not.*one-third/);
});
test('source quantities are data-driven and absent values remain unknown',()=>{
  const changed=structuredClone(op('gas_feed'));changed.parameters.stock_gas_flow.value=4;
  assert.match(buildAerosolScene(changed,sample).svg,/4.0 sccm/);
  delete changed.parameters.stock_gas_flow;
  assert.equal(buildAerosolScene(changed,sample).conditions.find(x=>x.label==='Stock-mixture flow').value,'Not reported');
  assert.equal(sourceQuantity({value:700,unit:'degC',status:'not_reported'}),'Not reported');
});
test('all non-synthesis drafts and unrelated papers fall back safely',()=>{
  let drafts=0;
  for(const folder of ['canonical-drafts','procedure-drafts','context-drafts'])for(const file of fs.readdirSync(path.join(root,folder)).filter(x=>x.endsWith('.json'))){
    const r=JSON.parse(fs.readFileSync(path.join(root,folder,file),'utf8'));drafts++;
    for(const o of r.operations)assert.equal(supportsAerosolOperation(o,r),AEROSOL_ACTIONS.includes(o.action));
  }
  assert.equal(drafts,13);
  assert.equal(buildAerosolScene(op('gas_feed'),{...sample,sources:[{doi:'10.1000/other'}]}),null);
});
test('source labels are escaped inside generated SVG',()=>{
  const hostile={...op('gas_feed'),label:'<script>alert(1)</script>'};
  const s=buildAerosolScene(hostile,sample);assert.doesNotMatch(s.svg,/<script>/);assert.match(s.svg,/&lt;script&gt;/);
});
test('DOM adapters preserve existing protocol contracts and explicit collection conditions',()=>{
  const saved=globalThis.document;
  globalThis.document={createElement:tag=>({tag,style:{},dataset:{},children:[],append(...nodes){this.children.push(...nodes);}})};
  try{
    const host=createAerosolArt(op('aerosol_pyrolysis'),sample,'unused-compatibility-prefix');
    assert.equal(host.dataset.scene,'aerosol_pyrolysis');assert.equal(host.style.height,'auto');assert.match(host.innerHTML,/quartz-tube/);
    const grid=createAerosolConditionGrid(op('sequential_bubbler_collection'),sample);
    assert.equal(grid.tag,'dl');assert.equal(grid.children.length,6);
    assert.equal(grid.children.find(x=>x.children[0].textContent==='Collection duration').children[1].textContent,'Not reported');
  }finally{globalThis.document=saved;}
});

// Human-inspection assets: no source data, Site checkout or ledger is modified.
if(process.argv.includes('--write-preview')){
  const generated=[];
  for(const o of sample.operations){const s=buildAerosolScene(o,sample);fs.writeFileSync(path.join(here,`${s.scene}.svg`),s.svg);generated.push(s);}
  const esc=s=>String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
  fs.writeFileSync(path.join(here,'apparatus-preview.html'),`<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Littau apparatus · private candidate</title><style>body{font:16px/1.5 Segoe UI,sans-serif;color:#284b5b;background:#f3f7fa;margin:0;padding:28px}main{max-width:1250px;margin:auto}section{background:white;border:1px solid #d6e4eb;border-radius:15px;margin:25px 0;padding:25px;display:grid;grid-template-columns:1.4fr 1fr;gap:30px}svg{width:100%;height:auto}h1{font-size:28px}h2{font-size:21px}dl{display:grid;grid-template-columns:1fr 1fr;gap:13px}dl>div{border-bottom:1px solid #d6e4eb;padding-bottom:8px}dt{font-size:12px;color:#637e8c}dd{margin:3px 0;font-weight:650}small{display:block;font-size:12px;color:#637e8c}li{margin:7px 0;font-size:13px}@media(max-width:900px){section{display:block}body{padding:14px}}</style><main><h1>Littau 1993 · continuous-flow apparatus candidate</h1><p>Private review asset. Formulation 6.0 shown. Source quantities and source conflicts are retained; diagrams are not to scale. No Site integration or publication has occurred.</p>${generated.map(s=>`<section><div>${s.svg}<small>${esc(s.caption)}</small></div><div><h2>${esc(s.title)}</h2><dl>${s.conditions.map(c=>`<div><dt>${esc(c.label)}</dt><dd>${esc(c.value)}</dd>${c.note?`<small>${esc(c.note)}</small>`:''}</div>`).join('')}</dl><ul>${s.notes.map(n=>`<li>${esc(n)}</li>`).join('')}</ul></div></section>`).join('')}</main></html>`);
}
