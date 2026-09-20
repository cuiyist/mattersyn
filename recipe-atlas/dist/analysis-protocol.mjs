/** Source-scoped explanatory diagrams; no invented spectra or instrument geometry. */
const actions={acid_reflux_activation:'reflux',acid_reflux_reactivation:'reflux',size_exclusion_calibration:'chromatography',size_exclusion_hplc:'chromatography',grind_and_press:'pellet',infrared_spectroscopy:'spectroscopy',uv_vis_spectroscopy:'spectroscopy',steady_state_PL:'spectroscopy',time_resolved_PL:'spectroscopy',grid_deposition:'grid',grid_evaporation:'grid',grid_washing:'grid',electron_microscopy:'microscopy',powder_mount_preparation:'mount',mechanical_mounting:'mount',powder_diffraction:'diffraction'};
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const text=(x,y,s,size=15)=>`<text x="${x}" y="${y}" font-size="${size}" text-anchor="middle">${esc(s)}</text>`;
const box=(x,y,w,h)=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="8" fill="#edf5f9" stroke="#7899ad" stroke-width="2"/>`;
const path=(d,color='#7899ad',width=3)=>`<path d="${d}" stroke="${color}" stroke-width="${width}" fill="none" stroke-linecap="round"/>`;
const arrow=(x,y)=>path(`M${x-18} ${y}h36m-9 -7l9 7-9 7`,'#48879a',2);
function grid(){let s='<circle cx="235" cy="165" r="74" fill="#e8f2f8" stroke="#7899ad" stroke-width="3"/>';for(let i=-2;i<=2;i++){s+=path(`M${235+i*22} 115v100M185 ${165+i*22}h100`,'#9db7c5',1);}return s;}
export function createAnalysisArt(o,r){
 if(!r.sources?.some(s=>s.doi?.toLowerCase()==='10.1021/j100108a019'))return null;
 const kind=actions[o.action];if(!kind)return null;let body='';
 if(kind==='reflux'){
  body=box(211,32,48,115)+path('M235 28v122M201 47h-24M269 129h25')+path('M222 150v28c-63 22-78 100 13 105 91-5 76-83 13-105v-28');
  body+='<path d="M179 239q55 24 112 0q-5 42-56 43t-56-43" fill="#d9be81" opacity=".55"/>'+box(173,290,125,24)+text(235,334,'Heated reflux')+text(112,70,'Condenser',14)+path('M154 75h48','#9db7c5',1)+text(235,367,'Source conditions are listed alongside',12);
 }else if(kind==='chromatography'){
  body=box(15,141,64,80)+text(47,184,'Sample',13)+arrow(105,181)+box(130,99,65,161)+text(163,153,'ZORBAX',11)+text(163,176,'60-S',13)+arrow(220,181)+box(246,99,65,161)+text(279,153,'ZORBAX',11)+text(279,176,'300-S',13)+arrow(337,181)+box(362,140,98,90)+text(411,173,'Detection',13)+text(411,194,'/ fractions',12)+text(235,302,'Two sequential size-exclusion columns',15)+text(235,335,'Retention time and equivalent size are distinct',12);
 }else if(kind==='pellet'){
  body=path('M115 174q120 155 240 0M138 178h194', '#7899ad',4)+path('M289 78l-93 111','#627f90',16)+text(235,283,'Sample + KBr → pressed pellet',17)+text(235,320,'Preparation geometry is schematic',12);
 }else if(kind==='grid'){
  body=grid()+text(235,278,'TEM support / specimen preparation',17)+text(235,317,o.action==='grid_washing'?'Wash the deposited fraction':o.action==='grid_deposition'?'Direct aerosol deposition':'Evaporate the selected colloid or fraction',13);
 }else if(kind==='mount'){
  body='<ellipse cx="235" cy="175" rx="55" ry="25" fill="#d9be81" stroke="#9d875d"/>'+text(235,116,'Powder specimen',17);
  if(o.action==='mechanical_mounting')body+=path('M235 302V201','#7899ad',8)+text(235,334,'Optical-fiber-tip mount',15);
  else if(/mylar|encas/i.test(o.label+' '+o.description))body+=box(158,139,154,83)+text(235,272,'Mylar enclosure',15);
  else body+=text(235,272,'A little AOT binds the powder',15);
  body+=text(235,365,'Alternative preparations remain separate steps',12);
 }else if(kind==='microscopy'){
  body=box(205,55,60,79)+path('M235 135v50','#48879a',3)+'<ellipse cx="235" cy="204" rx="50" ry="14" fill="#d9be81"/>'+path('M235 219v51')+box(159,274,152,43)+text(235,85,'Electron',12)+text(235,104,'beam',12)+text(235,300,'Image acquisition',13)+text(235,356,'Measured TEM images appear in the evidence gallery',12);
 }else if(kind==='diffraction'){
  body=box(35,86,104,48)+text(87,116,'X-ray source',13)+path('M139 120L239 239L360 111','#48879a',3)+'<ellipse cx="235" cy="249" rx="53" ry="16" fill="#d9be81"/>'+box(317,64,112,44)+text(373,92,'Detector',14)+text(235,307,'Powder diffraction',18)+text(235,348,'No simulated pattern is substituted for source data',12);
 }else{
  body=box(22,130,104,60)+text(74,155,'Source /',14)+text(74,177,'excitation',14)+arrow(151,160)+box(181,109,105,103)+text(233,167,'Specimen')+arrow(312,160)+box(339,130,105,60)+text(391,167,'Detector',14)+text(235,274,'Optical / infrared acquisition',18)+text(235,314,'Wavelength, sample state and detector depend on the step',11)+text(235,350,'No spectrum is invented by this diagram',12);
 }
 const host=document.createElement('div');host.className='protocol-art protocol-art-analysis';host.dataset.scene=kind;host.style.height='auto';host.innerHTML=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 470 400" role="img" aria-label="${esc(o.label)}. Explanatory schematic; dimensions do not specify actual equipment." style="width:100%;height:auto;font-family:Segoe UI,Arial,sans-serif;fill:#35596e"><title>${esc(o.label)}</title>${body}</svg>`;return host;
}
