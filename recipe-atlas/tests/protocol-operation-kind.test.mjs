import assert from 'node:assert/strict';
import {test} from 'node:test';
import {operationKind} from '../static/protocol-operation-kind.mjs';

test('source-scoped acquisition, context and fraction actions avoid preparation vials', () => {
  for(const [action,kind] of Object.entries({purge_by_bubbling:'degas',acquire_tem:'characterize',acquire_hrtem:'characterize',acquire_xrd:'characterize',record_tilt_imaging_context:'context',record_ed_hrtem_context:'context',annotate_condition:'context',vary_molar_ratio:'context',liquid_liquid_extraction:'separate',decant:'separate',redispersion_and_fractionation:'separate',withdraw_and_collect:'sample'}))
    assert.equal(operationKind({action}),kind,action);
  for(const [action,kind] of Object.entries({heat_in_air:'heat',cool:'cool',inject:'inject',drop_cast:'sample',precipitation:'separate',centrifugation:'separate',mix_components:'prepare'}))
    assert.equal(operationKind({action}),kind,action);
});

test('a reported reflux action selects a heated vessel', () => {
  assert.equal(operationKind({action:'reflux'}),'heat');
  assert.equal(operationKind({action:'reflux_under_nitrogen'}),'heat');
});
test('a later reflux mentioned during preparation does not activate heating', () => {
  assert.equal(operationKind({action:'dissolve',description:'Prepare feed for later reflux.'}),'prepare');
});
test('workup and sampling take precedence over a heating reference', () => {
  for (const [action, expected] of [['cool_reflux_mixture','cool'],['remove_heat','cool'],['sample_hot_reaction','sample'],['centrifuge_reaction','separate'],['heat_under_vacuum','degas']]) {
    assert.equal(operationKind({action}),expected);
  }
});
