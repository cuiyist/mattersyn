import {test} from 'node:test';import assert from 'node:assert/strict';
import {extendedReportedScene as choose} from '../static/reported-scene-extensions.mjs';
import {reportedProtocolSceneDescriptor} from '../static/reported-protocol-scenes.mjs';
const o=(action,label=action,extra={})=>({action,label,description:label,parameters:{},environment:{status:'not_reported',value:null},inputs:[],...extra});
const r={materials:[],products:[],operations:[]};
for(const action of ['disperse','dilute','formulate','sonicate','transfer','incubate','age'])test(action+' requires own liquid context',()=>{assert.equal(choose(o(action),r).kind,undefined);assert.equal(choose(o(action,action+' the aqueous solution'),r).kind,'solution');});
test('generic grow remains unsupported without its own liquid/system',()=>{assert.equal(choose(o('grow','Grow CdS shell'),r).kind,undefined);assert.equal(choose(o('grow','Grow dots in solution'),r).kind,'solution');});
test('generic store/purify do not invent apparatus',()=>{assert.equal(choose(o('store'),r).kind,undefined);assert.equal(choose(o('purify'),r).kind,undefined);});
test('reported current workup techniques select their own class',()=>{assert.equal(choose(o('purify','Purify by centrifugation'),r).kind,'centrifuge');assert.equal(choose(o('collect','Collect by filtration'),r).kind,'filter');assert.equal(choose(o('recover','Recover by precipitation'),r).kind,'workup-tube');});
test('negation and later techniques never choose apparatus',()=>{for(const label of ['Purify without centrifugation','Purify before centrifugation','Purify for later centrifugation'])assert.equal(choose(o('purify',label),r).kind,undefined);assert.equal(choose(o('do_not_transfer','Do not transfer solution'),r).kind,undefined);});
test('a direct solvent must be a current operation input',()=>{const rr={materials:[{id:'s',role:'solvent'}]};assert.equal(choose(o('transfer'),rr).kind,undefined);assert.equal(choose(o('transfer','Transfer',{inputs:['s']}),rr).kind,'solution');});
test('neighboring reactor and temperature cannot qualify transfer',()=>{assert.equal(choose(o('transfer'),{...r,method:'Hydrothermal',products:[{notes:['Reactor: autoclave (Main PDF p.2).']}],operations:[o('heat','Heat aqueous solution')]}).kind,undefined);});
test('preheating a furnace or unspecified material is not a liquid scene',()=>{assert.equal(choose(o('preheat','Preheat furnace'),r).kind,undefined);assert.equal(choose(o('preheat','Preheat solution'),r).kind,'solution');});
test('dry solids and water vapor do not become a solution',()=>{assert.equal(choose(o('disperse','Disperse dry powder'),r).kind,undefined);assert.equal(choose(o('mix','Mix powder under water vapor'),r).kind,undefined);});
test('storage can use only a validated own reported container',()=>{const own={descriptor:()=>({vessel:{value:'glass vial',scope:'step'}})};assert.equal(choose(o('store','Store solution'),r,own).kind,'workup-tube');assert.equal(choose(o('store'),r,{descriptor:()=>({vessel:{value:'glass vial',scope:'recipe'}})}).kind,undefined);});
test('explicit own deposition system qualifies; method alone does not',()=>{assert.equal(choose(o('cap','Cap using MBE'),r).kind,'chamber');assert.equal(choose(o('grow'),{...r,method:'MBE'}).kind,undefined);});
test('measurement mention of a vessel never becomes a process',()=>assert.equal(choose(o('measure','Measure solution in flask'),r).kind,undefined));
test('explicit own mortar and pestle select only that solid-handling apparatus',()=>{const x=choose(o('grind','Grind powder using mortar and pestle'),r);assert.equal(x.kind,'mortar-pestle');});
test('proposal does not mutate public operation/record',()=>{const x=o('transfer','Transfer solution'),y={materials:[]};const before=JSON.stringify([x,y]);choose(x,y);assert.equal(JSON.stringify([x,y]),before);});

test('anchored current label can classify a bookkeeping action key with its own liquid',()=>{const result=choose(o('sulfur-solution','Prepare sulfur solution'),r,{descriptor:(shown)=>shown.action==='prepare'?{kind:'solution'}:null});assert.equal(result.kind,'solution');assert.equal(result.rule,'anchored_current_own_label_supported_action');assert.equal(result.selector_action,'prepare');});
test('own-label matching refuses mentions, negation, later instructions and dry preparation',()=>{for(const label of ['Mixture for preparing solution','Do not prepare solution','Prepare solution for later reflux','Mix dry powder'])assert.equal(choose(o('bookkeeping-key',label),r,{descriptor:()=>({kind:'solution'})}).kind,undefined);});
test('own-label alias cannot borrow recipe method or recipe vessel',()=>{let seen;choose(o('bookkeeping-key','Heat solution'),{...r,method:'Hydrothermal',products:[{notes:['Reactor: autoclave (Main PDF p.2).']}]},{descriptor:(shown,context)=>{if(shown.action==='wash')return null;seen=context;return {kind:'solution'};}});assert.equal(seen.method,'Other');assert.deepEqual(seen.products[0].notes,[]);});

test('storage liquid alone never implies a tube',()=>assert.equal(choose(o('store','Store aqueous solution'),r).kind,undefined));
test('surface inputs cannot become generic liquid actions just because solvent is present',()=>{const rr={materials:[{id:'wafer',role:'substrate',name:'Silicon wafer'},{id:'s',role:'solvent',name:'Water'}]};for(const action of ['clean','transfer','incubate','age','grow','purify'])assert.equal(choose(o(action,action+' in solution',{inputs:['wafer','s']}),rr).kind,undefined);});
test('explicit dissolution or dispersion stays allowed with surface-named starting material',()=>{const rr={materials:[{id:'film',name:'Starting film'},{id:'s',role:'solvent'}]};assert.equal(choose(o('disperse','Disperse film into aqueous suspension',{inputs:['film','s']}),rr).kind,'solution');});


test('actual extended descriptor preserves original own values, not recipe apparatus or heat',()=>{
 const operation=o('transfer','Transfer aqueous solution');
 const record={...r,method:'Hydrothermal',products:[{notes:['Reactor: autoclave (Main PDF p.2).']}],operations:[operation]};
 const before=JSON.stringify([operation,record]);
 const chosen=reportedProtocolSceneDescriptor(operation,record);
 assert.equal(chosen.kind,'solution'); assert.equal(chosen.vessel,null);assert.equal(chosen.heating,false);
 assert.equal(JSON.stringify([operation,record]),before);
});
test('actual own-label injection preserves own reported temperature and added material',()=>{
 const operation=o('bookkeeping','Inject aqueous precursor',{inputs:['m'],parameters:{temperature:{status:'reported',value:150,unit:'degC'}}});
 const record={...r,materials:[{id:'m',name:'Precursor',role:'metal_precursor'}],operations:[operation]};
 const chosen=reportedProtocolSceneDescriptor(operation,record);
 assert.equal(chosen.kind,'inject');assert.equal(chosen.heating,true);assert.deepEqual(chosen.added,['Precursor']);
});
test('conditional or negative own instructions cannot be overridden by a short positive label',()=>{
 for(const description of ['Do not transfer solution.','Optionally transfer the solution.','Transfer the solution if necessary.'])
 assert.equal(choose(o('transfer','Transfer solution',{description}),r).kind,undefined);
});
