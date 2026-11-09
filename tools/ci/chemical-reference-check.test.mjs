import assert from 'node:assert/strict';
import {test} from 'node:test';
import {selectTargets,selectLTargets,assertFieldQualification,L_FIELD_DEFAULT_QUALIFICATION} from './chemical-reference-check.mjs';
const KIM='kim2013-pbs-ionic-liquid-am3029766-pbs-qd';
function fixture(){
 const entries=[['oa','Oleic acid'],['ode','1-Octadecene'],['ethanol','Ethanol'],['acetone','Acetone'],['computed','Computed name'],['ion','Salt'],['ambient','InAs'],['flat','TiO2'],['hmds','Hexamethyldisilathiane'],['octane','Octane'],['hx-wash','Hexane'],['hx-tem','Hexane'],['pbo','Lead oxide'],['name-card-indium-palmitate','indium palmitate']].map(([id,name])=>({id,name}));
 const references={oa:{route:'molecule_reference',reason:'identical_CID'},ode:{route:'molecule_reference',reason:'unique_exact_compound_name'},ethanol:{route:'molecule_reference',reason:'validated_connectivity_computed_conformer'},acetone:{route:'molecule_reference',reason:'validated_connectivity_computed_conformer'},computed:{route:'molecule_reference',reason:'validated_connectivity_computed_conformer'},ion:{route:'independent_component_references'},ambient:{route:'ambient_crystal_reference'},flat:{route:'flat',whyNo3d:'The form is unreported.'},hmds:{route:'molecule_reference',reason:'unique_exact_compound_name'},octane:{route:'molecule_reference',reason:'owner_fixed_named_identity'},'hx-wash':{route:'molecule_reference',reason:'owner_fixed_named_identity'},'hx-tem':{route:'molecule_reference',reason:'owner_fixed_named_identity'},pbo:{route:'flat',whyNo3d:'The form is unreported.'},'name-card-indium-palmitate':{route:'independent_component_references',namedLigandReference:{entry_id:'name-card-indium-palmitate'}}};
 const bindings={recordBindings:{[KIM]:{m1:'oa',m2:'ode',m3:'ethanol',m4:'acetone',m9:'hmds',m10:'octane','chemical--hexane-wash':'hx-wash','chemical--hexane-tem':'hx-tem',m11:'pbo'},other:{m5:'computed',m6:'ion',m7:'ambient',m8:'flat',m12:'name-card-indium-palmitate'}}};
 return [{entries},bindings,{entries:references}];
}
test('actual Kim2013 routes, independent ions, ambient and named ligands give twelve targets',()=>{
 const targets=selectTargets(...fixture());assert.equal(targets.length,12);assert.deepEqual(targets.filter(t=>['kim2013-oa','kim2013-ode','kim2013-ethanol','kim2013-acetone'].includes(t.id)).map(t=>t.name),['Oleic acid','1-Octadecene','Ethanol','Acetone']);
 const covered=new Set(targets.flatMap(t=>[t.id,...t.covers||[]]));for(const id of ['reused-molecule','computed-molecule','independent-ions','ambient-cell','flat-reason'])assert(covered.has(id));
});
test('missing route or actual precursor binding fails instead of silently skipping',()=>{
 let args=fixture();args[2].entries.ethanol.reason='identical_CID';args[2].entries.acetone.reason='identical_CID';delete args[2].entries.computed;assert.throws(()=>selectTargets(...args),/computed-molecule/);
 args=fixture();args[2].entries.ethanol.reason='identical_CID';args[2].entries.acetone.reason='identical_CID';assert.throws(()=>selectTargets(...args,(rid,mid)=>mid!=='m5'),/computed-molecule/);
});
test('Kim ambiguity or missing exact named identity fails',()=>{
 const [registry,bindings,overlay]=fixture();registry.entries.push({id:'oa-ambiguous',name:'Oleic acid'});bindings.recordBindings[KIM].m9='oa-ambiguous';assert.throws(()=>selectTargets(registry,bindings,overlay),/exactly one/);
});

test('named ligand target retains its own binding and fails on missing scope identity',()=>{
 const args=fixture(),targets=selectTargets(...args),named=targets.find(t=>t.id==='named-ligand-reference');assert.equal(targets.length*2,24);assert.equal(named.registry_id,'name-card-indium-palmitate');assert.equal(named.material_id,'m12');delete args[2].entries['name-card-indium-palmitate'].namedLigandReference;assert.throws(()=>selectTargets(...args),/named-ligand/);
});

function lFixture(){
 const args=fixture(),[registry,bindings,overlay]=args,IS='MatterSyn-L-reference-identity-pins/1',SS='MatterSyn-L4-S8-reference-proof/1';
 overlay.lIdentityProofs={schema:IS,entries:{}};overlay.lSulfurProofs={schema:SS,entries:{}};overlay.lFieldQualifications={};overlay.lAmbientProofs={schema:'MatterSyn-L4-admitted-fixed-ambient-proof/1',formulas:{CdO:{reference_id:'cdo-reference'}}};
 const add=(eid,name,ref,proof)=>{registry.entries.push({id:eid,name});bindings.recordBindings.other['material-'+eid]=eid;overlay.entries[eid]=ref;if(proof)overlay.lIdentityProofs.entries[eid]={schema:IS,entry_id:eid,...proof};};
 add('l-ambient','Cadmium oxide (99%)',{route:'ambient_crystal_reference',reason:'L_owner_fixed_ambient_default',referenceId:'cdo-reference',crystalReference:{formula:'CdO'},l4OwnNameProof:{schema:'MatterSyn-L4-own-name-normalization/1',entry_id:'l-ambient',reference_id:'cdo-reference'}});
 add('l-s8','Sulfur',{route:'molecule_reference',reason:'L_owner_elemental_sulfur_S8_reference'});overlay.lSulfurProofs.entries['l-s8']={schema:SS,entry_id:'l-s8',plan:{kind:'s8_reference',ownerpart:'L4'}};
 for(const [eid,ownerpart,route]of [['l-normalized','L1','molecule_reference'],['l-acetate','L2','independent_component_references'],['l-stock','L5','independent_component_references'],['l-single','L6','molecule_reference'],['l-default','L3','molecule_reference']])add(eid,eid,{route,reason:'L_owner_named_reference'},{plan:{kind:ownerpart==='L2'||ownerpart==='L5'?'independent_components':'single_compound',ownerpart,transformations:['synthetic own-name cleanup']}});
 overlay.lFieldQualifications['l-default']={source_entry_sha256:'a'.repeat(64),reference_sha256:'b'.repeat(64),qualification:L_FIELD_DEFAULT_QUALIFICATION};return args;
}
test('H selection stays twelve and absent L maps require no fabricated success',()=>{
 const args=fixture(),before=structuredClone(args),extra=selectLTargets(...args);assert.equal(selectTargets(...args).length,12);assert.equal(extra.targets.length,0);assert.equal(extra.coverage.length,7);assert(extra.coverage.every(x=>x.status==='NO_RESOLVED_ENTRIES'));assert.deepEqual(args,before);
});
test('all seven present L groups select actual bound entries from their own proof maps',()=>{
 const args=lFixture(),before=structuredClone(args),extra=selectLTargets(...args);assert.equal(selectTargets(...args).length,12);assert.equal(extra.targets.length,7);assert.deepEqual(extra.targets.map(t=>t.id),['l4-ambient','l4-s8','l1-normalized-molecule','l2-acetate','l5-stock-components','l6-single-compound','l3-field-default']);
 for(const t of extra.targets)assert.equal(args[1].recordBindings[t.record_id][t.material_id],t.registry_id);assert.equal(extra.targets.at(-1).field_default_qualification,L_FIELD_DEFAULT_QUALIFICATION);assert.deepEqual(args,before);
});
test('L selection is deterministic after input ordering changes and skips ineligible material bindings',()=>{
 const args=lFixture(),a=selectLTargets(...args);args[0].entries.reverse();args[1].recordBindings=Object.fromEntries(Object.entries(args[1].recordBindings).reverse().map(([rid,row])=>[rid,Object.fromEntries(Object.entries(row).reverse())]));args[2].lIdentityProofs.entries=Object.fromEntries(Object.entries(args[2].lIdentityProofs.entries).reverse());assert.deepEqual(selectLTargets(...args),a);
 assert.throws(()=>selectLTargets(...args,(rid,mid)=>mid!=='material-l-stock'),/L l5-stock-components.*actual Reader precursor binding/);
});
test('L targets cannot be inferred from names without successful maps or from malformed proofs',()=>{
 let args=fixture();args[0].entries.push({id:'sulfur-name-only',name:'Sulfur'});assert.equal(selectLTargets(...args).targets.length,0);
 args=lFixture();delete args[2].entries['l-s8'];assert.throws(()=>selectLTargets(...args),/successful proof.*resolved reference/);
 args=lFixture();delete args[2].entries['l-ambient'].l4OwnNameProof;assert.throws(()=>selectLTargets(...args),/ambient target.*actual admitted/);
 args=lFixture();args[2].lFieldQualifications['l-default'].qualification='A guessed default';assert.throws(()=>selectLTargets(...args),/exact validated mapping/);
});
test('L3 prefers newly resolved default over original already-rotatable qualified entry',()=>{
 const args=lFixture();args[0].entries.push({id:'a-old-default',name:'ODE',model3dPath:'models/original.json'});args[1].recordBindings.other.old='a-old-default';args[2].lFieldQualifications['a-old-default']={source_entry_sha256:'c'.repeat(64),reference_sha256:'d'.repeat(64),qualification:L_FIELD_DEFAULT_QUALIFICATION};assert.equal(selectLTargets(...args).targets.find(t=>t.l_group==='l3-field-default').registry_id,'l-default');
});
test('exact L3 line appears once in each modal phase; missing, duplicate or changed wording fails',()=>{
 for(const phase of ['initial_modal','after_model_open'])assert.equal(assertFieldQualification('Reference structure. '+L_FIELD_DEFAULT_QUALIFICATION).occurrences,1,phase);
 for(const text of ['Reference only.',L_FIELD_DEFAULT_QUALIFICATION+' '+L_FIELD_DEFAULT_QUALIFICATION])assert.throws(()=>assertFieldQualification(text),/exactly once/);assert.throws(()=>assertFieldQualification('Different','Different'),/Unexpected L3/);
});
