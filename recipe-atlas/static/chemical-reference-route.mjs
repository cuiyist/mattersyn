// Proposed pure Reader adapter. No fetching or mutation of registry entries.
const hash = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
const path = value => typeof value === 'string' && /^models\/[A-Za-z0-9][A-Za-z0-9._/-]*\.json$/.test(value)
  && !value.split('/').some(part => part === '..' || part === '.');
const model = value => path(value?.model3dPath) && hash(value?.model3dSha256);
const fallback = 'No unique molecular or eligible bulk-reference model is assigned.';

export function referenceRoute(entry) {
  if (entry?._readerReferenceResolved && entry.readerAmbientReference) {
    const ref = entry.readerAmbientReference;
    if (path(ref.modelPath) && hash(ref.modelSha256) && ref.referenceOnly === true && ref.trainingEligible === false)
      return {route: 'ambient_crystal_reference', crystalReference: ref};
    return {route: 'flat', whyNo3d: fallback};
  }
  const ref = entry?.readerReference3d;
  if (!ref) return {route: entry?.model3dPath ? 'existing_molecule' : entry?.component3dModels?.length ? 'existing_components' : 'flat', whyNo3d: fallback};
  if (ref.route === 'flat') return {route: 'flat', whyNo3d: typeof ref.whyNo3d === 'string' && ref.whyNo3d.trim() ? ref.whyNo3d : fallback};
  if (ref.referenceOnly !== true || ref.trainingEligible !== false) return {route: 'flat', whyNo3d: fallback};
  if (ref.route === 'molecule_reference' && model(ref)) return ref;
  if (ref.route === 'independent_component_references' && ref.component3dModels?.length
      && ref.component3dModels.every(model)) return ref;
  if (ref.route === 'ambient_crystal_reference' && ref.crystalReference
      && path(ref.crystalReference.modelPath) && hash(ref.crystalReference.modelSha256)
      && ref.crystalReference.referenceOnly === true && ref.crystalReference.trainingEligible === false) return ref;
  return {route: 'flat', whyNo3d: fallback};
}

export const hasReference3d = entry => referenceRoute(entry).route !== 'flat';
export const chemicalButtonLabel = entry => hasReference3d(entry) ? 'Rotate 3D ↗' : 'View formula ↗';
export const flatReferenceReason = entry => referenceRoute(entry).route === 'flat' ? entry?.whyNo3d || referenceRoute(entry).whyNo3d : '';

// These exact historical formula-card statements describe the old depiction,
// not a scientific restriction on using a separately qualified reference.
// Keep their still-applicable identity/surface/measurement qualifications.
const obsoleteFlatStatements = [
  ['Source-qualified identity/formula only.', 'Source-qualified chemical identity.'],
  ['No atoms, bonds, bound surface geometry, molecular conformer or measured coordinates are assigned.',
    'Bound surface geometry and measured sample coordinates are not assigned.'],
];
function referencePresentationText(text, fixedOctane = false) {
  if (typeof text !== 'string') return text;
  let result = text;
  for (const [before, after] of obsoleteFlatStatements) result = result.split(before).join(after);
  if (fixedOctane) {
    result = result.split('No unique isomer or molecular connectivity is assigned.').join('The systematic name octane denotes the straight-chain reference; solution speciation and measured geometry are not assigned.');
    result = result.split('A source that names octane without specifying an isomer does not establish this exact connectivity; ').join('');
  }
  return result;
}
const newReference = ref => ['molecule_reference', 'independent_component_references', 'ambient_crystal_reference'].includes(ref.route);
const referenceCaption = ref => ref.caption || ref.component3dScope || ref.crystalReference?.description || ref.crystalReference?.scope;
const distinctText = values => [...new Set(values.filter(value => typeof value === 'string' && value.trim()))].join(' ');
function fixedOctaneReference(entry, ref = referenceRoute(entry)) {
  return ['octane', 'n-octane'].includes(String(entry?.name || '').trim().toLowerCase())
    && (entry?.readerFixedOctaneReference === true || ref.reason === 'owner_fixed_named_identity' && ref.referenceRegistryId === 'octane'
      || ref.route === 'existing_molecule' && entry.id === 'octane');
}

export const chemicalModelCaption = (entry, caption) => fixedOctaneReference(entry) ? referencePresentationText(caption, true) : caption;

export function chemicalDisplayCaption(entry, suppliedCaption) {
  const ref = referenceRoute(entry);
  const fixedOctane = fixedOctaneReference(entry, ref);
  if (!newReference(ref) && fixedOctane) return referencePresentationText(suppliedCaption ?? entry?.caption ?? '', true);
  if (!newReference(ref)) return suppliedCaption ?? entry?.caption ?? entry?.depictionKind ?? '';
  if (suppliedCaption !== undefined) {
    const cleaned = referencePresentationText(suppliedCaption, fixedOctane);
    return cleaned === suppliedCaption ? cleaned : distinctText([referencePresentationText(referenceCaption(ref), fixedOctane), cleaned]);
  }
  return distinctText([referencePresentationText(referenceCaption(ref), fixedOctane), referencePresentationText(entry?.caption, fixedOctane)]);
}

export function viewerEntry(entry) {
  if (entry?._readerReferenceResolved) return entry;
  const ref = referenceRoute(entry);
  const fixedOctane = fixedOctaneReference(entry, ref);
  if (ref.route.startsWith('existing_')) return fixedOctane ? {...entry, _readerReferenceResolved: true, readerFixedOctaneReference: true,
    caption: referencePresentationText(entry.caption, true), sourceBindingCaption: referencePresentationText(entry.sourceBindingCaption, true),
    limitations: (entry.limitations || []).map(text => referencePresentationText(text, true))} : entry;
  // These are temporary viewer values, never replacements for the original
  // entry's classification, name, formula, caption, SVG or source bindings.
  const common = {...entry, model3dPath: null, component3dModels: [], readerAmbientReference: undefined,
    readerReference3d: undefined, _readerReferenceResolved: true};
  if (ref.route === 'flat') return {...common, whyNo3d: ref.whyNo3d};
  const scoped = {...common, readerFixedOctaneReference: fixedOctane, caption: referencePresentationText(referenceCaption(ref) || entry.caption, fixedOctane),
    sourceBindingCaption: referencePresentationText(entry.sourceBindingCaption || entry.caption, fixedOctane),
    limitations: [...new Set([...(entry.limitations || []), ...(ref.limitations || [])].map(text => referencePresentationText(text, fixedOctane)))],
    sourceUrls: [...new Set([...(entry.sourceUrls || []), ...(ref.sourceUrls || []), ...(ref.sourceUrl ? [ref.sourceUrl] : [])])]};
  if (ref.route === 'ambient_crystal_reference') return {...scoped, readerAmbientReference: ref.crystalReference};
  if (ref.route === 'molecule_reference') return {...scoped, model3dPath: ref.model3dPath,
    assetHashes: {...entry.assetHashes, model3dPath: ref.model3dSha256}};
  return {...scoped, component3dModels: ref.component3dModels, component3dScope: ref.component3dScope};
}
