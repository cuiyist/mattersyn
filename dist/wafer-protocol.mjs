/** Heath et al. 1996, DOI 10.1021/jp951903v: source-scoped technical diagrams.
 * Pure SVG builder + DOM adapter compatible with aerosol-protocol.mjs.
 * Experimental values are supplied by the canonical operation/adjacent UI.
 * Geometry, layer heights and dot symbols are explanatory, never scale models.
 */
export const WAFER_ACTIONS=Object.freeze(['wafer_cleaning','thermal_oxidation','resist_coating','resist_bake','electron_beam_lithography','resist_development','reactive_ion_etching','resist_removal','native_oxide_removal','vacuum_loading','selective_cvd','wafer_dicing','raman_spectroscopy','near_ir_absorption','plan_view_tem','contact_mode_afm']);
const C={ink:'#284b5b',muted:'#637e8c',line:'#7899ad',si:'#aec5d1',oxide:'#e2b971',resist:'#8baccb',ge:'#497b94',accent:'#397d90',pale:'#edf5fa',hot:'#c8754e',white:'#fff',paper:'#fbfdff'};
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const text=(x,y,s,size=18,extra='')=>`<text x="${x}" y="${y}" font-size="${size}" ${extra}>${esc(s)}</text>`;
const center=(x,y,s,size=18)=>text(x,y,s,size,'text-anchor="middle"');
const line=(d,color=C.line,width=2,extra='')=>`<path d="${d}" fill="none" stroke="${color}" stroke-width="${width}" stroke-linecap="round" stroke-linejoin="round" ${extra}/>`;
const box=(x,y,w,h,fill=C.pale,rx=6)=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${rx}" fill="${fill}" stroke="${C.line}" stroke-width="1.8"/>`;
const arrow=(x,y,angle=0,color=C.accent)=>`<g transform="translate(${x} ${y}) rotate(${angle})">${line('M-20 0H16',color,2.5)}<path d="M9 -6L19 0L9 6Z" fill="${color}"/></g>`;
const leader=(d)=>line(d,C.muted,1.3);
const note=(s)=>center(300,346,s,14);
const title=s=>text(30,55,s,23,'font-weight="650"');
const dots=(x,y,count=3)=>Array.from({length:count},(_,i)=>`<path d="M${x+i*18} ${y}q5 -10 10 0Z" fill="${C.ge}"/>`).join('');
const heat=(x,y)=>[0,1,2].map(i=>line(`M${x+i*35} ${y}q-8 -12 0 -24t0 -24`,C.hot,2.5)+arrow(x+i*35,y-59,-90,C.hot)).join('');
function wellWidth(r){return r?.measurements?.find(m=>m.property==='well_diameter')?.value?.value??null;}
export function supportsWaferOperation(o,r){return WAFER_ACTIONS.includes(o?.action)&&r?.sources?.some(s=>String(s.doi||'').toLowerCase()==='10.1021/jp951903v')===true;}

/** Cross-section through circular openings. All graphic dimensions are arbitrary.
 * A residual oxide line is retained for 100 nm wells before the HF step, following
 * the authors' interpretation, rather than prematurely exposing bare Si.
 */
function wafer(x,y,w,{oxide=true,resist=false,opening='none',width=null,grown=false}={}){
 let out=`<g data-role="wafer-cross-section">${box(x,y+28,w,49,C.si,1)}`;
 if(oxide)out+=`<rect x="${x}" y="${y+14}" width="${w}" height="14" fill="${C.oxide}"/>`;
 if(resist)out+=`<rect x="${x}" y="${y+3}" width="${w}" height="11" fill="${C.resist}"/>`;
 const centers=[x+w*.23,x+w*.5,x+w*.77],hw=w*.075;
 if(opening!=='none')for(const cx of centers){
  if(resist)out+=`<rect x="${cx-hw}" y="${y+2}" width="${hw*2}" height="12" fill="${C.paper}"/>`;
  if(opening!=='resist'){
   const depth=width===150?39:28;
   out+=`<path d="M${cx-hw} ${y+13}V${y+depth}H${cx+hw}V${y+13}Z" fill="${C.paper}"/>`;
   if(width===100&&opening==='etched')out+=`<path d="M${cx-hw} ${y+27}H${cx+hw}" stroke="${C.oxide}" stroke-width="3" data-role="possible-residual-oxide"/>`;
   if(grown){const dy=y+depth;out+=width===150?dots(cx-hw+2,dy,1)+dots(cx+hw-12,dy,1):dots(cx-5,dy,1);}
  }
 }
 return out+center(x+w/2,y+61,'Si(100)',17)+'</g>';
}
function legend(entries){let x=48;return entries.map(([name,color])=>{const s=`<rect x="${x}" y="${315}" width="14" height="14" rx="2" fill="${color}"/>`+text(x+21,327,name,15);x+=name.length*8+60;return s;}).join('');}
function cleaning(){return title('Silicon substrate preparation')+wafer(105,160,390,{oxide:false})+box(157,95,286,38,'#fff')+center(300,120,'Cleaning is reported',17)+arrow(300,148,90)+note('Cleaning chemistry and equipment are not specified.');}
function oxidation(){return title('Thermal oxide formation')+wafer(105,157,390)+heat(270,294)+text(390,133,'SiO₂ film',17)+leader('M423 139L423 172')+legend([['Si substrate',C.si],['Thermal oxide',C.oxide]])+note('Heating and film growth are schematic; oxidant is unreported.');}
function coating(){return title('PMMA resist layer')+wafer(105,158,390,{resist:true})+text(387,109,'PMMA film',18)+leader('M422 117V159')+arrow(300,124,90)+legend([['Si substrate',C.si],['SiO₂',C.oxide],['PMMA',C.resist]])+note('The paper does not specify a coating technique or formulation.');}
function baking(){return title('Resist bake')+wafer(105,139,390,{resist:true})+heat(265,288)+center(300,110,'PMMA-coated wafer',18)+note('Thermal treatment; heater geometry and atmosphere are unreported.');}
function exposure(){let out=title('Electron-beam pattern definition')+box(226,83,148,46)+center(300,112,'Electron beam',17)+wafer(105,200,390,{resist:true});for(const x of [195,300,405])out+=line(`M300 134L${x} 198`,C.accent,1.6,'stroke-dasharray="5 5"')+`<circle cx="${x}" cy="205" r="4" fill="${C.accent}"/>`;return out+center(300,175,'Point exposures',16)+note('Pitch and dose are reported; their variant assignments are unresolved.');}
function development(){return title('Resist development')+wafer(105,165,390,{resist:true,opening:'resist'})+box(116,90,368,45,'#fff')+center(300,119,'Isopropyl alcohol : MIBK developer',17)+arrow(300,148,90)+legend([['SiO₂ remains',C.oxide],['Patterned PMMA',C.resist]])+note('Openings form in PMMA; the oxide has not yet been etched.');}
function etch(o,r){const w=wellWidth(r);let out=title('Reactive-ion transfer into the oxide')+box(187,82,226,45)+center(300,111,'CF₄ / CHF₃ plasma',18)+wafer(105,189,390,{resist:true,opening:'etched',width:w});for(const x of [195,300,405])out+=arrow(x,153,90);out+=legend([['SiO₂ mask',C.oxide],['PMMA resist',C.resist]]);return out+note(w===100?'100 nm wells: possible residual oxide before the HF treatment.':'150 nm wells: over-etch extends into Si; no endpoint detection.');}
function stripping(o,r){return title('PMMA removal')+wafer(105,168,390,{opening:'etched',width:wellWidth(r)})+box(181,87,238,44,'#fff')+center(300,115,'Acetone rinse',18)+arrow(300,147,90)+legend([['Si substrate',C.si],['SiO₂ mask retained',C.oxide]])+note('PMMA is removed; rinse volume, time and equipment are unreported.');}
function hf(o,r){return title('Native-oxide removal at the well bases')+wafer(105,180,390,{opening:'clean',width:wellWidth(r)})+box(174,85,252,48,'#fff')+center(300,115,'Brief HF dip',18)+arrow(300,157,90)+center(300,285,'Exposed Si sites for selective growth',17)+note('Concentration basis, solvent and exact dip duration are unspecified.');}
function loading(o,r){return title('Transfer to the UHV/CVD system')+wafer(35,182,174,{opening:'clean',width:wellWidth(r)})+arrow(233,225)+box(266,125,119,151,'#fff')+center(326,155,'Load lock',18)+box(405,102,159,174)+center(484,134,'Growth',18)+center(484,159,'chamber',18)+arrow(394,210)+line('M415 249H551',C.line,4)+note('Chamber base pressure is distinct from the deposition pressure.');}
function growth(o,r){const w=wellWidth(r);return title('Selective Ge island growth')+box(66,103,469,191,'#f5f9fc')+wafer(121,177,358,{opening:'clean',width:w,grown:true})+box(23,108,165,43,'#fff')+center(105,136,'GeH₄ / He',18)+arrow(214,130)+text(336,136,'CVD chamber',18)+line('M223 281q12 -16 24 0t24 0t24 0t24 0t24 0',C.hot,3)+legend([['SiO₂ mask',C.oxide],['Ge island symbols',C.ge]])+note(w===100?'A single-dot well is illustrated; occupancy is not guaranteed.':'Perimeter-island symbols reflect reported morphology, not exact counts.');}
function dicing(){let out=title('Wafer division for characterization')+box(72,121,187,139,C.si)+center(165,104,'Shared patterned wafer',17)+arrow(300,189);for(const [x,y]of [[359,119],[455,119],[359,202],[455,202]])out+=box(x,y,73,57,C.si);out+=line('M165 126V255M78 190H253',C.paper,3,'stroke-dasharray="6 5"')+center(446,104,'Analysis pieces',17)+note('The number, dimensions and measurement assignments are unreported.');return out;}
function raman(){return title('Micro-Raman characterization')+box(45,86,143,59,'#fff')+center(117,111,'Excitation',17)+center(117,132,'source',16)+line('M163 145L291 213',C.accent,3)+wafer(208,200,220,{opening:'clean',grown:true})+line('M313 203L438 133',C.accent,2,'stroke-dasharray="5 5"')+box(413,80,148,69,'#fff')+center(487,109,'Raman',17)+center(487,132,'collection',17)+note('Measurement concept only; no experimental spectrum is generated.');}
function nearIR(){return title('Near-infrared absorption')+box(26,155,156,70,'#fff')+center(104,182,'Near-IR',18)+center(104,205,'illumination',17)+arrow(205,190)+box(233,142,145,96,C.si)+center(305,180,'Patterned',18)+center(305,206,'wafer region',17)+arrow(402,190)+box(431,155,141,70,'#fff')+center(501,182,'Absorption',17)+center(501,205,'measurement',16)+note('Conceptual acquisition flow; transmission/reflection geometry is unstated.');}
function tem(){return title('Plan-view transmission electron microscopy')+box(258,82,84,58,'#fff')+center(300,106,'Electron',16)+center(300,128,'column',16)+arrow(300,163,90)+box(205,195,190,10,C.si,1)+arrow(300,244,90)+box(216,268,169,40,'#fff')+center(300,294,'Image acquisition',16)+text(46,193,'Thin specimen',16)+leader('M167 192L203 199')+note('150 nm wells were usable; 100 nm regions lacked suitable TEM preparation.');}
function afm(){return title('Supertip atomic force microscopy')+wafer(107,200,386,{opening:'clean',width:100,grown:true})+box(177,100,151,16,C.resist,1)+`<path d="M292 116L310 149L327 116Z" fill="${C.resist}" stroke="${C.line}" stroke-width="1.6"/>`+line('M310 149L305 219',C.ink,3)+arrow(370,106)+arrow(410,106,180)+text(371,82,'Contact scan',17)+text(62,145,'Si nitride tip',16)+leader('M163 144L290 128')+text(338,178,'Carbon whisker',16)+leader('M335 183L310 176')+note('Tip convolution broadens width and reduces apparent in-well height.');}
const RENDER={wafer_cleaning:cleaning,thermal_oxidation:oxidation,resist_coating:coating,resist_bake:baking,electron_beam_lithography:exposure,resist_development:development,reactive_ion_etching:etch,resist_removal:stripping,native_oxide_removal:hf,vacuum_loading:loading,selective_cvd:growth,wafer_dicing:dicing,raman_spectroscopy:raman,near_ir_absorption:nearIR,plan_view_tem:tem,contact_mode_afm:afm};
const NOTES={
 reactive_ion_etching:['Cross-sections pass through circular wells; graphical layer heights, opening widths and defect positions are not quantitative.','For 100 nm wells, the residual-oxide illustration follows the authors’ interpretation that the subsequent HF dip exposes Si.'],
 selective_cvd:['The 100 and 150 nm regions share the same wafer exposure. Particle symbols illustrate the reported positions without specifying atomic structure, exact dimensions or fabrication yield.','Gas-mixture flow is distinct from pure-germane flow; base pressure is distinct from deposition pressure.'],
 wafer_dicing:['The drawn number of pieces is illustrative. No specimen-to-technique assignment is inferred from this geometry.'],
 plan_view_tem:['The schematic is not a TEM image or diffraction pattern. Original experimental imagery belongs in the source evidence gallery.'],
 contact_mode_afm:['A dot and probe illustrate the convolution problem; their apparent geometry is not a recreation or fit of Figure 6.'],
 raman_spectroscopy:['The source reports a Raman peak in prose but provides no Raman trace. The light paths are a generic measurement concept, not reported optical geometry.'],
 near_ir_absorption:['The source reports a surface-state absorption peak, not a bandgap. The acquisition-flow diagram does not specify optical transmission or reflection geometry.']
};
export function buildWaferScene(o,r){
 if(!supportsWaferOperation(o,r))return null;
 const name=o.label||o.action.replaceAll('_',' '),width=wellWidth(r);
 const scope=width?`${width} nm template variant; common-wafer exposure`:'Source-specific preparation or measurement concept';
 const description=`${name}. ${scope}. Geometry, film thicknesses and particle symbols are schematic, not to scale. Source conditions are displayed alongside.`;
 const body=RENDER[o.action](o,r);
 const svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 382" class="wafer-apparatus-svg" role="img" aria-label="${esc(description)}" data-scene="${esc(o.action)}" style="display:block;width:100%;height:auto;max-width:100%;font-family:Segoe UI,Arial,sans-serif;fill:${C.ink}"><title>${esc(name)}</title><desc>${esc(description)}</desc><rect width="600" height="382" rx="18" fill="${C.paper}"/>${body}${center(300,370,'Explanatory diagram · geometry not to scale',12)}</svg>`;
 return {scene:o.action,title:name,svg,evidence:(o.evidence||[]).map(x=>({...x})),notes:NOTES[o.action]||[],caption:'Source-linked technical schematic. Apparatus geometry, film thicknesses and dot symbols are illustrative; measured dimensions and conditions remain in the record. No micrograph or spectrum is simulated.'};
}
export function createWaferArt(o,r,prefix=''){
 const scene=buildWaferScene(o,r);if(!scene)return null;
 const host=document.createElement('div');host.className='protocol-art protocol-art-wafer';host.dataset.scene=scene.scene;
 Object.assign(host.style,{display:'block',width:'100%',height:'auto',minHeight:'0',padding:'0'});
 host.innerHTML=scene.svg;return host;
}
