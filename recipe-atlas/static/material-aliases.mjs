export function resolveMaterialEntry(materials, id) {
  return materials.find(material => material.id === id || material.alias_ids?.includes(id));
}
