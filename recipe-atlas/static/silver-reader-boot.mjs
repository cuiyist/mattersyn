import {mountSilverReader,renderCatalog,qualifiedMachinePaperDois} from './silver-reader.mjs';
const host = document.getElementById('silver-catalog');
if (host) {
  const view=await mountSilverReader(host, {url: host.dataset.catalogUrl || null, hideEmpty: host.dataset.hideEmpty === 'true'});
  if (view?.available) for (const count of document.querySelectorAll('[data-paper-total]')) {
    // Audited DOI bindings are emitted from the same regular collection as this counter.
    // A missing/malformed binding never permits a possibly duplicate paper count.
    try {const extractedBase=Number(count.dataset.sourceExtractedPapers||0);
      const audited=JSON.parse(count.dataset.auditedPrimaryDois),extracted=JSON.parse(count.dataset.sourceExtractedDois||'[]');
      if(Array.isArray(audited)&&Array.isArray(extracted))count.textContent=String(Number(count.dataset.auditedPapers||0)+extractedBase+qualifiedMachinePaperDois(view,{excludedPrimaryDois:[...audited,...extracted]}).length);
    } catch {count.textContent=String(Number(count.dataset.auditedPapers||0)+Number(count.dataset.sourceExtractedPapers||0));}
  }
}
