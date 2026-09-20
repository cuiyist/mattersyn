// Source-qualified molecular species 9 only. This adapter contains no coordinates.
export const EVANS_SPECIES9 = Object.freeze({
  registryId: 'evans2010-species9-reference',
  formula: 'C24H20P2PbSe4',
  svgPath: 'svg/evans2010-species9-reference.svg',
  model3dPath: 'models/evans2010-species9-reference-3d.json',
  svgSha256: 'd7dc6acf4deb555209a87fc391061356aad4b41fd134bb45bf77485a18bb6ebd',
  modelSha256: '60dcc117105d7a70edf803bf5dedc35617302c6de485447efd431cb05e99ca2c',
  sourceCifSha256: 'abd4ecdae2c4a445921b9fdde415fda76208d11fe0df40cc510c7fa94b510ef4'
});

const bindings = Object.freeze({
  'evans-2010-species9-crystallization': Object.freeze({
    sampleId: 'species9-crystallization',
    label: 'Isolated molecular species 9',
    context: 'The isolated Pb(Se₂PPh₂)₂ crystal described in the species 9 crystallization procedure.',
    locator: 'SI pp. S15–S16; supplied species 9 CIF.'
  }),
  'evans-2010-molecular9-structure': Object.freeze({
    sampleId: 'species9-cif',
    label: 'Molecular species 9 · single-crystal structure',
    context: 'The species 9 single-crystal refinement context, separate from the nanocrystal synthesis and characterization samples.',
    locator: 'SI p. S15, Figure S12 and refinement description; supplied species 9 CIF.'
  })
});

export function evansSpecies9Context(record, sampleId) {
  const binding = bindings[record?.record_id];
  if (!binding || record?.lineage?.source_group !== 'evans2010' || record?.material?.formula !== EVANS_SPECIES9.formula) return null;
  if (sampleId !== undefined && sampleId !== binding.sampleId) return null;
  const sample = record.products?.find(p => p.sample_id === binding.sampleId);
  if (!sample) return null;
  return { ...binding, recordId: record.record_id, sampleLabel: sample.source_sample_label || binding.label, registryId: EVANS_SPECIES9.registryId };
}

export function evansSpecies9Entry(data, context) {
  if (!context || bindings[context.recordId]?.sampleId !== context.sampleId) return null;
  const e = data?.entries?.get(EVANS_SPECIES9.registryId);
  if (!e || e.formula !== EVANS_SPECIES9.formula || e.depictionKind !== 'source_crystallographic_model' ||
      e.svgPath !== EVANS_SPECIES9.svgPath || e.model3dPath !== EVANS_SPECIES9.model3dPath ||
      e.assetHashes?.svgPath !== EVANS_SPECIES9.svgSha256 || e.assetHashes?.model3dPath !== EVANS_SPECIES9.modelSha256 ||
      e.provenance?.sourceCifSha256 !== EVANS_SPECIES9.sourceCifSha256) return null;
  const caption = context.context + ' Coordinates are the documented Cartesian transform of the supplied molecular crystal refinement. All 20 H sites use the reported calculated riding model.';
  return { ...e, name: context.label, caption, sourceBindingCaption: caption,
    limitations: [...new Set([...(e.limitations || []),
      'The asymmetric-unit molecule is shown; symmetry-related packing contacts and a periodic crystal lattice are not displayed.',
      'This model does not provide PbSe or CdSe quantum-dot or magic-size-cluster coordinates. No exact training pair or DFT-ready structure is approved.'
    ])]
  };
}

const element = (tag, text, className) => {
  const n = document.createElement(tag);
  if (text !== undefined) n.textContent = text;
  if (className) n.className = className;
  return n;
};

/** Mount once in a record's Final structures host, or pass the exact sampleId. */
export async function mountEvansSpecies9(host, record, options = {}) {
  const context = evansSpecies9Context(record, options.sampleId);
  if (!host || !context) return { mounted: false, reason: 'outside_species9_scope' };
  if (host.querySelector('[data-evans-species9]')) return { mounted: false, reason: 'already_mounted' };
  const api = options.chemicalApi || await import('./chemical-viewer.mjs');
  const data = options.data || await api.chemicalRegistry();
  const entry = evansSpecies9Entry(data, context);
  if (!entry) return { mounted: false, reason: 'qualified_registry_entry_unavailable' };
  // Registry requests may outlive a route change; avoid inserting stale content.
  if (host.isConnected === false) return { mounted: false, reason: 'host_detached' };
  const card = element('section', undefined, 'structure-record evans-species9-card');
  card.dataset.evansSpecies9 = context.sampleId;
  card.style.cssText = 'border:1px solid #cedbe4;border-radius:14px;padding:18px;margin:16px 0;background:#f8fbfd';
  card.append(element('h4', context.label), element('p', 'Pb(Se₂PPh₂)₂ · C₂₄H₂₀P₂PbSe₄', 'chemical-formula'));
  const preview = api.chemicalImage(entry);
  preview.style.cssText = 'display:block;width:100%;max-width:680px;height:300px;object-fit:contain;background:white;border-radius:10px';
  preview.alt = 'Species 9 molecular crystal reference; source-derived coordinates with calculated riding hydrogen sites.';
  card.append(preview, element('p', entry.caption, 'chemical-caption'));
  card.append(element('p', 'Only the asymmetric-unit molecule is shown. The 20 H sites follow the reported riding model; symmetry-related intermolecular packing contacts are omitted.', 'guide-notice'));
  const controls = element('div', undefined, 'protocol-controls');
  const rotate = element('button', 'Rotate / zoom species 9 ↗', 'molecule-link');
  rotate.type = 'button';
  const message = element('p', '', 'chemical-caption');
  message.setAttribute('aria-live', 'polite');
  rotate.onclick = async () => {
    message.textContent = '';
    try { await api.openChemical(entry); }
    catch { message.textContent = 'The molecular viewer could not open. The model JSON remains available below.'; }
  };
  const download = element('a', 'Download molecular model JSON');
  download.href = new URL('assets/chemical-registry/' + EVANS_SPECIES9.model3dPath + '?sha=' + EVANS_SPECIES9.modelSha256, import.meta.url).href;
  download.download = 'evans2010-species9-source-molecular-model.json';
  controls.append(rotate, download);
  card.append(controls, message, element('p', context.locator, 'chemical-caption'));
  card.append(element('p', 'This molecular complex is separate from PbSe/CdSe quantum dots and magic-size clusters. No nanocrystal coordinates, surface ligands, exact training pair or DFT eligibility are inferred.', 'guide-notice'));
  host.append(card);
  return { mounted: true, recordId: context.recordId, sampleId: context.sampleId, registryId: entry.id };
}
