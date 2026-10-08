/** Coverage notice only. Never promotes source scope or supplies training values. */
export const PENDING_BADGE = 'Core synthesis scope · other variants pending';
export function pendingVariants(rows) {
  if (rows === undefined) return [];
  if (!Array.isArray(rows)) throw Error('Invalid pending variant inventory');
  const seen = new Set(), privatePath = /[A-Za-z]:[\\/]|file:|\\\\|\/(?:Users|home|tmp|research-assets)\//i;
  const text = (value, max) => typeof value === 'string' && value.trim().length > 0 && value.length <= max && !privatePath.test(value) && !/[\u0000-\u001f]/.test(value);
  return rows.map(row => {
    if (!row || Object.keys(row).sort().join(',') !== 'id,label,source_locators' || !text(row.id, 120)
      || !text(row.label, 600) || seen.has(row.id) || !Array.isArray(row.source_locators)
      || !row.source_locators.length || row.source_locators.length > 32
      || !row.source_locators.every(locator => text(locator, 600))
      || new Set(row.source_locators).size !== row.source_locators.length) throw Error('Pending variant requires explicit public locators');
    seen.add(row.id);
    return {id:row.id, label:row.label, source_locators:[...row.source_locators]};
  });
}
export function renderPendingVariants(host, rows) {
  const pending = pendingVariants(rows);
  if (!pending.length) return null;
  const doc = host.ownerDocument, node = (tag, text) => { const n=doc.createElement(tag); n.textContent=text; return n; };
  const notice=doc.createElement('aside'); notice.className='record-notice pending-variants';
  notice.append(node('strong', PENDING_BADGE), node('p', 'Only the published core scope is covered by the linked audit. Pending variants have not been independently audited or included in training.'));
  const list=doc.createElement('ul');
  for (const row of pending) { const item=node('li',row.label); item.append(node('small','Source: '+row.source_locators.join('; '))); list.append(item); }
  notice.append(list); host.append(notice); return notice;
}
