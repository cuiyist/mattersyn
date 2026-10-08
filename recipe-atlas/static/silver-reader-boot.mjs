import {mountSilverReader,renderCatalog,qualifiedMachinePaperDois} from './silver-reader.mjs';
const host = document.getElementById('silver-catalog');
if (host) {
  const view=await mountSilverReader(host, {url: host.dataset.catalogUrl || null, hideEmpty: host.dataset.hideEmpty === 'true'});
  if (view?.available) for (const count of document.querySelectorAll('[data-machine-papers]')) {
    // Audited DOI bindings are emitted from the same regular collection as this counter.
    // A missing/malformed binding never permits a possibly duplicate paper count.
    try {const excludedPrimaryDois=JSON.parse(count.parentElement.dataset.auditedPrimaryDois);
      if(Array.isArray(excludedPrimaryDois))count.textContent=String(qualifiedMachinePaperDois(view,{excludedPrimaryDois}).length);
    } catch {count.textContent='0';}
  }
  const filter=document.getElementById('review-filter');
  if (filter && view) filter.addEventListener('change',()=>renderCatalog(host,view,{hideEmpty:true,hiddenByFilter:filter.value==='audited'}));
}
