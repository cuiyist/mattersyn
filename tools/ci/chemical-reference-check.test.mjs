import assert from 'node:assert/strict';
import {test} from 'node:test';
import {selectTargets} from './chemical-reference-check.mjs';
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
