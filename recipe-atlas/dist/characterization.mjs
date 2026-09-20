const paperPdf='https://bpb-us-e1.wpmucdn.com/sites.mit.edu/dist/9/2055/files/2023/10/ja00072a025.pdf';
export const figureRecords={
 tem:{figure:6,page:8710,pdfPage:5,group:'structure',file:'figure-06-tem.png',type:'TEM · experimental',title:'TEM morphology and size distribution',alt:'Original Figure 6: lattice-contrast TEM of dispersed CdSe nanocrystals, with the original 20 nm scale bar.',caption:'Dispersed, slightly elongated CdSe nanocrystals. The original 20 nm scale bar is retained.',question:'What shape and size did they actually make?',explanation:'Transmission electron microscopy (TEM) images individual particles. Here the particles are slightly prolate: longer along one axis than across it.',metrics:[['Long axis','3.5 nm ±5%'],['Short axis','3.0 nm ±6%'],['Elongation direction','Along (002)']],reading:'Use the scale bar to read length. Dark particle outlines reveal shape; lattice contrast provides structural detail. The ±5% and ±6% describe population size spreads. The authors note that these widths are limited by uncertainty in locating particle edges.',limit:'The atomic model below uses these dimensions as its envelope. Its individual atom positions come from a separate bulk reference, not from this micrograph.'},
 xrd:{figure:11,page:8712,pdfPage:7,group:'structure',file:'figure-11-xrd-size-series.png',type:'Powder XRD · experimental',title:'Size-dependent powder XRD',alt:'Original Figure 11: stacked powder XRD patterns for CdSe sizes 1.2 to 11.5 nm, with bulk wurtzite peak positions.',caption:'Seven CdSe size populations, with bulk wurtzite peak positions at the bottom (h).',question:'How does the atomic order change with particle size?',explanation:'X-ray diffraction (XRD) combines scattering from many particles. The peak pattern supports predominantly wurtzite-like order, while the peaks broaden as the particles become smaller.',metrics:[['a → g · major-axis sizes','1.2, 1.8, 2.0, 3.7, 4.2, 8.3, 11.5 nm'],['Horizontal axis','Scattering angle, 2θ'],['Vertical axis','Intensity · arbitrary units']],reading:'Compare each experimental trace with the reference positions (h). Broad peaks reflect finite crystal size; the unusually weak (103) feature also points to stacking faults.',limit:'At about 1.2 nm the authors caution that a bulk wurtzite-versus-zinc-blende label loses meaning. These XRD samples are a separate reported series; they are not all the Figure 6 TEM sample.'},
 model:{figure:15,page:8714,pdfPage:9,group:'structure',file:'figure-15-experimental-model-xrd.png',type:'XRD · experiment + authors’ model',title:'Experimental and simulated XRD',alt:'Original Figure 15: experimental dotted XRD curve compared with the authors’ solid simulated curve for approximately 3.7 nm CdSe.',caption:'The original authors compare measured XRD with a structural simulation for approximately 3.7 nm CdSe.',question:'Why is an ideal lattice only part of the story?',explanation:'A slightly elongated shape, stacking faults and surface disorder help the authors reproduce the measured diffraction profile. Agreement with a pattern constrains a model; it does not uniquely locate every atom.',metrics:[['Dotted curve','Experimental XRD'],['Solid curve','Paper authors’ simulation'],['Model aspect ratio','1.3']],reading:'Follow where the two curves agree and where they differ. The simulated structure includes features omitted from this website’s simpler rotatable reference model.',limit:'The caption states one stacking fault per crystallite; the adjacent text describes an average of 1.3. That source discrepancy remains unresolved. This panel contains the paper’s original simulation, not a new fit.'},
 absorption:{figure:3,page:8709,pdfPage:4,group:'properties',file:'figure-03-absorption-size-series.png',type:'Absorption · experimental',title:'Size-dependent optical absorption',alt:'Original Figure 3: room-temperature absorption spectra of CdSe in hexane with individual size labels in angstroms, spanning approximately 1.2 to 11.5 nm.',caption:'Room-temperature absorption spectra for CdSe nanocrystals dispersed in hexane. The original size labels are in ångströms (10 Å = 1 nm).',question:'How does a smaller crystal change its optical response?',explanation:'Smaller CdSe nanocrystals have their lowest-energy absorption feature at shorter wavelengths. This size-dependent optical response is a signature of quantum confinement.',metrics:[['Reported size span','≈1.2–11.5 nm'],['Measurement medium','Hexane'],['Temperature','Room temperature']],reading:'Read each size label next to its spectrum, then compare the long-wavelength absorption feature. Smaller size corresponds to a higher transition energy. The plotted amplitudes are in arbitrary units.',limit:'These are the original published curves. They are not digitized data or a predictive size-to-color slider, and the article does not supply a unique synthesis time for every curve.'},
 pl:{figure:5,page:8710,pdfPage:5,group:'properties',file:'figure-05-absorption-photoluminescence.png',type:'Absorption + photoluminescence · experimental',title:'Band-edge photoluminescence',alt:'Original Figure 5: absorption and fluorescence spectra of a 3.5 nm CdSe optical sample at room temperature.',caption:'Absorption and photoluminescence of a 3.5 nm CdSe sample at room temperature; numerical optical results are discussed on page 8709.',question:'How efficiently does this sample emit light?',explanation:'Photoluminescence (PL) measures light emitted after excitation. This sample emits close to its lowest-energy absorption peak, with no deep-trap luminescence detected in the reported spectrum.',metrics:[['PL quantum yield','≈9.6%'],['Reference standard','Rhodamine 640'],['Emission peak shift','4 nm to the red']],reading:'The absorption and fluorescence arrows identify the two spectra. The emission maximum lies 4 nm beyond the absorption maximum; their linewidths are reported as equal. A quantum yield of 9.6% means about 9.6 emitted photons per 100 absorbed photons under the measurement conditions.',limit:'The Figure 5 optical sample is 3.5 nm in nominal diameter. The paper does not establish that it is the Figure 6 TEM specimen. No numerical linewidth or exact emission peak wavelength is inferred here from the printed plot.'}
};

export function initializeCharacterization(){
 const dialog=document.getElementById('figure-dialog');
 const largeImage=document.getElementById('figure-dialog-image');
 const viewport=document.getElementById('figure-viewport');
 const zoomLabel=document.getElementById('figure-zoom-label');
 let activeFigure,zoom=1,returnFocus;
 function applyZoom(){
  if(!largeImage.naturalWidth)return;
  const width=Math.min(largeImage.naturalWidth,Math.max(120,viewport.clientWidth-40),Math.max(160,viewport.clientHeight-40)*largeImage.naturalWidth/largeImage.naturalHeight);
  largeImage.style.width=Math.round(width*zoom)+'px';
  zoomLabel.textContent=Math.round(zoom*100)+'%';
  document.getElementById('figure-zoom-out').disabled=zoom<=.5;
  document.getElementById('figure-zoom-in').disabled=zoom>=3;
 }
 function openFigure(record,trigger){
  activeFigure=record;returnFocus=trigger;zoom=1;
  document.getElementById('figure-dialog-title').textContent='Figure '+record.figure+' · '+record.type;
  document.getElementById('figure-dialog-caption').textContent=record.caption+' Murray, Norris & Bawendi, JACS 1993, p. '+record.page+'.';
  largeImage.alt=record.alt;largeImage.style.width='';largeImage.src='assets/murray1993-figures/'+record.file;
  dialog.showModal();if(largeImage.complete)applyZoom();
  viewport.scrollTop=0;viewport.scrollLeft=0;
 }
 largeImage.addEventListener('load',applyZoom);
 document.getElementById('figure-zoom-in').addEventListener('click',()=>{zoom=Math.min(3,zoom+.25);applyZoom();});
 document.getElementById('figure-zoom-out').addEventListener('click',()=>{zoom=Math.max(.5,zoom-.25);applyZoom();});
 document.getElementById('figure-zoom-reset').addEventListener('click',()=>{zoom=1;applyZoom();viewport.scrollTop=viewport.scrollLeft=0;});
 document.getElementById('figure-dialog-close').addEventListener('click',()=>dialog.close());
 dialog.addEventListener('click',event=>{if(event.target===dialog){const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close();}});
 dialog.addEventListener('close',()=>returnFocus?.focus());
 new ResizeObserver(()=>{if(dialog.open&&activeFigure)applyZoom();}).observe(viewport);
 document.querySelectorAll('[data-gallery]').forEach(gallery=>{
  const select=(key)=>{
   const record=figureRecords[key];if(!record||record.group!==gallery.dataset.gallery)return;
   gallery.dataset.selectedFigure=key;
   gallery.querySelectorAll('[data-figure]').forEach(button=>{const active=button.dataset.figure===key;button.classList.toggle('active',active);button.setAttribute('aria-pressed',String(active));});
   for(const field of ['type','title','caption','question','explanation','reading','limit'])gallery.querySelector('[data-field="'+field+'"]').textContent=record[field];
   const image=gallery.querySelector('[data-field="image"]');image.src='assets/murray1993-figures/'+record.file;image.alt=record.alt;
   const source=gallery.querySelector('[data-field="source"]');source.textContent='Figure '+record.figure+' · p. '+record.page+' ↗';source.href=paperPdf+'#page='+record.pdfPage;
   gallery.querySelector('[data-field="metrics"]').replaceChildren(...record.metrics.map(([name,value])=>{const row=document.createElement('div'),dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=name;dd.textContent=value;row.append(dt,dd);return row;}));
   gallery.querySelector('[data-enlarge]').setAttribute('aria-label','Enlarge original Figure '+record.figure);
  };
  gallery.querySelectorAll('[data-figure]').forEach(button=>button.addEventListener('click',()=>select(button.dataset.figure)));
  gallery.querySelector('[data-enlarge]').addEventListener('click',event=>openFigure(figureRecords[gallery.dataset.selectedFigure],event.currentTarget));
  select(gallery.dataset.gallery==='structure'?'tem':'absorption');
 });
}
