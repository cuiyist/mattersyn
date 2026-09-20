export function finiteReferenceAtoms(model) {
  if (model.periodic !== false || model.representation !== 'finite_illustrative_particle') {
    throw new Error('Expected an explicitly nonperiodic illustrative particle model.');
  }
  if (model.measured_sample_structure !== false || model.training_eligible !== false) {
    throw new Error('This renderer is restricted to reference/illustrative models.');
  }
  return model.atoms.map(a => ({
    serial:a.serial, elem:a.element, x:a.x, y:a.y, z:a.z,
    bonds:[...a.bonds], bondOrder:[...a.bondOrder],
    properties:{...a.properties, reference_only:true, measured_sample:false}
  }));
}
export function drawFiniteReference(viewer, model) {
  viewer.clear();
  viewer.addModel().addAtoms(finiteReferenceAtoms(model));
  for (const element of new Set(model.atoms.map(a=>a.element))) {
    const color=({Pb:'#8b9bae',Se:'#bc8957'})[element]||'#6b95b3';
    viewer.setStyle({elem:element}, {sphere:{radius:.37,color},stick:{radius:.07,color:'#a0b7c6'}});
  }
  // No periodic tiling and no enclosing crystal-cell box for a finite crop.
  viewer.zoomTo();viewer.rotate(17,'y');viewer.rotate(-12,'x');viewer.render();
  return model.caption; // Show this beside the viewer, not only in metadata.
}
