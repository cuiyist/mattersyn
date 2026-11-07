// Private Part I proposal. Build-time grouping; no record fetching or grouping here.
export const METHOD_FAMILIES_SCHEMA = 'mattersyn-method-families-compact/1';

export function validateMethodFamilies(groups, records) {
  if (groups?.schema !== METHOD_FAMILIES_SCHEMA || !Array.isArray(groups.families)) throw Error('Invalid method-family metadata');
  const known = new Map(records.map(row => [row.record_id, row]));
  if (known.size !== records.length) throw Error('Duplicate material record metadata');
  const seen = new Set(), familyIDs = new Set();
  for (const family of groups.families) {
    if (!family.id || familyIDs.has(family.id) || !family.label || !Array.isArray(family.papers) || family.paper_count !== family.papers.length) throw Error('Invalid method family');
    familyIDs.add(family.id);
    for (const paper of family.papers) {
      if (!paper.citation || !Array.isArray(paper.record_ids) || !paper.record_ids.length) throw Error('Invalid paper card');
      for (const rid of paper.record_ids) {
        if (!known.has(rid) || seen.has(rid)) throw Error('Unknown or repeated grouped record');
        seen.add(rid);
      }
    }
  }
  if (seen.size !== known.size || records.some(row => !seen.has(row.record_id))) throw Error('Incomplete method-family membership');
  if (groups.default_record_id !== (groups.families[0]?.papers[0]?.record_ids[0] ?? null)) throw Error('Inconsistent family default');
  return groups;
}

export function chooseMethodRecord(groups, records, explicit = null) {
  const ids = new Set(records.map(row => row.record_id));
  if (explicit && ids.has(explicit)) return explicit;
  if (groups?.default_record_id && ids.has(groups.default_record_id)) return groups.default_record_id;
  return records[0]?.record_id ?? null;
}

export function mountMethodFamilyList(host, {
  groups, records, onSelect, document: doc = globalThis.document, initialPaperLimit = 6,
}) {
  validateMethodFamilies(groups, records);
  if (!Number.isSafeInteger(initialPaperLimit) || initialPaperLimit < 1 || typeof onSelect !== 'function') throw Error('Invalid method-list options');
  const metadata = new Map(records.map(row => [row.record_id, row]));
  const create = (tag, text, className) => {
    const node = doc.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  };
  const root = create('div', undefined, 'reader-method-families');
  root.dataset.initialCardLimit = String(initialPaperLimit);
  const families = [], byRecord = new Map();
  let active = null, expanded = false, total = 0, toggle = null;
  for (const family of groups.families) {
    const section = create('section', undefined, 'reader-method-family');
    section.dataset.familyId = family.id;
    section.append(create('h3', family.label), create('p', `${family.paper_count} ${family.paper_count === 1 ? 'paper' : 'papers'}`, 'reader-family-adoption'));
    const list = create('div', undefined, 'reader-methods'), state = {section, list, cards: []};
    for (const paper of family.papers) {
      const card = create('article', undefined, 'reader-method-card reader-paper-card');
      card.dataset.paperCard = 'true'; card.dataset.recordIds = JSON.stringify(paper.record_ids);
      const choose = create('button', paper.citation, 'reader-paper-choice');
      choose.type = 'button'; choose.dataset.recordId = paper.record_ids[0]; choose.setAttribute('aria-pressed', 'false');
      const info = {card, choose, state, recordIDs: paper.record_ids, current: paper.record_ids[0], variants: null, index: total++};
      choose.onclick = () => onSelect(info.current); card.append(choose);
      if (paper.record_ids.length > 1) {
        const label = create('label', 'Variant', 'reader-variant-label'), variants = create('select');
        variants.setAttribute('aria-label', `Variant from ${paper.citation}`);
        for (const [index, rid] of paper.record_ids.entries()) {
          const row = metadata.get(rid), option = create('option', `Variant ${index + 1}` + (row.title ? ` - ${row.title}` : ''));
          option.value = rid; variants.append(option);
        }
        variants.value = info.current; variants.onchange = () => onSelect(variants.value);
        label.append(variants); card.append(label); info.variants = variants;
      }
      for (const rid of paper.record_ids) byRecord.set(rid, info);
      state.cards.push(info); list.append(card);
    }
    section.append(list); families.push(state); root.append(section);
  }
  if (total > initialPaperLimit) {
    toggle = create('button', undefined, 'reader-family-toggle'); toggle.type = 'button';
    toggle.onclick = () => {expanded = !expanded; refresh();}; root.append(toggle);
  }
  function refresh() {
    for (const state of families) {
      for (const info of state.cards) info.card.hidden = !expanded && info.index >= initialPaperLimit && !info.recordIDs.includes(active);
      state.section.hidden = state.cards.every(info => info.card.hidden);
    }
    if (toggle) {toggle.textContent = expanded ? 'Show fewer' : 'Show all'; toggle.setAttribute('aria-expanded', String(expanded));}
  }
  function select(rid) {
    const info = byRecord.get(rid);
    if (!info) throw Error('Selected record is outside method families');
    active = rid; info.current = rid; info.choose.dataset.recordId = rid;
    if (info.variants) info.variants.value = rid;
    if (info.index >= initialPaperLimit) expanded = true;
    for (const state of families) for (const card of state.cards) {
      const selected = card === info; card.choose.setAttribute('aria-pressed', String(selected)); card.card.dataset.activeRecord = selected ? rid : '';
    }
    refresh();
  }
  refresh(); host.append(root);
  return {select, root, familyCount: families.length, cardCount: total};
}
