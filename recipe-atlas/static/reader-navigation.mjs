// Resolve fragments only after the asynchronous Reader has created its sections.
// Data pages retain native browser navigation; no scientific content is changed.
let installed = false;
export function fragmentId(hash) {
  try { return decodeURIComponent(String(hash || '').replace(/^#/, '')); }
  catch { return null; }
}
export async function applyReaderFragment(root) {
  const id = fragmentId(location.hash);
  if (!id || !root?.isConnected || !root.dataset.readerReady) return false;
  const hash = location.hash;
  const generation = root.dataset.readerReady;
  await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
  if (!root.isConnected || location.hash !== hash || root.dataset.readerReady !== generation) return false;
  const target = document.getElementById(id);
  if (!target || !root.contains(target)) return false;
  target.scrollIntoView({block: 'start', behavior: 'instant'});
  return true;
}
export function installReaderHashNavigation() {
  if (installed) return;
  installed = true;
  addEventListener('hashchange', () => {
    const root = document.querySelector('main[data-reader-ready]');
    if (root) void applyReaderFragment(root);
  });
}
