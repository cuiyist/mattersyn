import test from 'node:test';
import assert from 'node:assert/strict';
import {componentScopeLabel} from '../static/reader-utils.mjs';
import {classifyMorphology} from '../static/reader-particle.mjs';

test('phase-mixture component badge does not claim a heterostructure',()=>{
 const label=componentScopeLabel({component_only:true,component_architectures:['phase_mixture']});
 assert.equal(label,'Component within a source-reported phase mixture');
 assert.doesNotMatch(label,/heterostructure/i);
});
test('core-shell component keeps its heterostructure label',()=>{
 assert.equal(componentScopeLabel({component_only:true,component_architectures:['core_shell']}),'Component within a core/shell heterostructure');
});
test('composite component receives a composite label',()=>{
 assert.equal(componentScopeLabel({component_only:true,component_architectures:['composite']}),'Component within a composite product');
});
test('non-component material has no component badge',()=>{
 assert.equal(componentScopeLabel({component_only:false,component_architectures:['phase_mixture']}),'');
});

test('unspecified architecture never gains a heterostructure badge',()=>{
 assert.doesNotMatch(componentScopeLabel({component_only:true}),/heterostructure/i);
 assert.doesNotMatch(componentScopeLabel({component_only:true,component_architectures:['unresolved']}),/heterostructure/i);
});

test('source-described disks get an illustrative planar shape but negated or conflicting morphology does not',()=>{
 assert.equal(classifyMorphology('Disklike; equilateral hexagon shape is predominant'),'platelet');
 assert.equal(classifyMorphology('CuS nanodisks'),'platelet');
 for(const value of ['No nanodisks observed','Nanodisks were not observed','Nanodisks and spheres','Unknown disklike morphology'])assert.equal(classifyMorphology(value),'neutral',value);
});
