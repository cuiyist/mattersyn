// Classify the recorded action only; descriptions may mention other stages.
const exactKinds=Object.freeze({
  purge_by_bubbling:'degas',
  acquire_tem:'characterize',acquire_hrtem:'characterize',acquire_xrd:'characterize',
  record_tilt_imaging_context:'context',record_ed_hrtem_context:'context',
  annotate_condition:'context',vary_molar_ratio:'context',
  liquid_liquid_extraction:'separate',decant:'separate',redispersion_and_fractionation:'separate',
  withdraw_and_collect:'sample',
});
export function operationKind(operation) {
  const action = String(operation.action || '').toLowerCase();
  if(Object.hasOwn(exactKinds,action))return exactKinds[action];
  if (/store/.test(action)) return 'store';
  if (/filter/.test(action)) return 'filter';
  if (/centrifug|purif|wash|rinse|precipitat|floccul|nonsolvent/.test(action)) return 'separate';
  if (/dry|evaporat|distill/.test(action)) return 'dry';
  if (/cool|quench|remove_heat/.test(action)) return 'cool';
  if (/inject|hot_add/.test(action)) return 'inject';
  if (/sample|measur|aliquot|drop_cast/.test(action)) return 'sample';
  if (/degas|vacuum|evacuat|freeze|gas_saturate/.test(action)) return 'degas';
  if (/heat|grow|react|stabilize|reflux/.test(action)) return 'heat';
  return 'prepare';
}
