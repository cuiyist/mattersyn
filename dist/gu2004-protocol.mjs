// Private Gu et al. 2004 apparatus proposal. No canonical record is mutated.
// Geometry, colors and particle symbols are explanatory, not measured apparatus.
const C={ink:'#173c4b',muted:'#587281',line:'#7998a5',pale:'#f1f7fa',blue:'#dcecf3',gold:'#d5a34a',pt:'#625379',brown:'#98734d',green:'#217862'};
const esc=s=>String(s??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const text=(x,y,s,size=16,anchor='middle',fill=C.ink,weight=400)=>`<text x="${x}" y="${y}" text-anchor="${anchor}" font-family="Arial,sans-serif" font-size="${size}" font-weight="${weight}" fill="${fill}">${esc(s)}</text>`;
const path=(d,color=C.line,w=2.4,extra='')=>`<path d="${d}" fill="none" stroke="${color}" stroke-width="${w}" stroke-linecap="round" stroke-linejoin="round" ${extra}/>`;
const rect=(x,y,w,h,fill=C.pale,rx=10)=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${rx}" fill="${fill}" stroke="${C.line}" stroke-width="1.5"/>`;
const arrow=(x,y,a=0,color=C.line)=>`<g transform="translate(${x} ${y}) rotate(${a})">${path('M-20 0H20M12 -7L20 0L12 7',color,2.8)}</g>`;
function wrap(s,max=58){const lines=[];let row='';for(const word of String(s).split(/\s+/)){if(row&&(`${row} ${word}`).length>max){lines.push(row);row=word;}else row+=(row?' ':'')+word;}if(row)lines.push(row);return lines;}
const para=(x,y,s,{max=62,size=15,line=20,anchor='start',fill=C.muted}={})=>wrap(s,max).map((t,i)=>text(x,y+i*line,t,size,anchor,fill)).join('');
function quantity(o,key){const q=o.parameters?.[key];if(!q)return 'not reported';let v=q.value;if(v==null){if(q.minimum!=null||q.maximum!=null)v=`${q.minimum??'…'}–${q.maximum??'…'}`;else return 'not reported';}return `${q.approximate?'≈ ':''}${v} ${({'degC':'°C'})[q.unit]??q.unit??''}`.trim();}
const Q=(label,key)=>({label,key});
const L=(label,value)=>({label,value});
const positions=[[-29,4],[15,-8],[34,23],[-9,31],[-37,34]];
function particles(x,y,mode){return positions.map(([dx,dy],i)=>{
 const a=x+dx,b=y+dy;
 if(mode==='white')return `<ellipse cx="${a}" cy="${b}" rx="7" ry="3" fill="#fff" stroke="#9babb2" stroke-width="1"/>`;
 if(mode==='pellet')return `<ellipse cx="${a}" cy="${y+31+((i%2)*3)}" rx="8" ry="4" fill="${C.brown}"/>`;
 if(mode==='heterodimer')return `<circle cx="${a-4}" cy="${b}" r="5.5" fill="${C.pt}"/><circle cx="${a+6}" cy="${b+1}" r="8" fill="${C.gold}"/>`;
 if(mode==='residue')return `<circle cx="${a}" cy="${b}" r="6" fill="${C.pt}"/>${path(`M${a+6} ${b-7}q8 2 7 8`,C.gold,3.5,'opacity="0.65"')}`;
 return `<circle cx="${a}" cy="${b}" r="6" fill="${C.pt}"/>`;
}).join('');}
function vessel(x,y,{fill=C.blue,mode=null,cap=false,heat=false,label='Generic reaction vessel',gas=null,openingDepth=85}={}){
 let s=`<path d="M${x-60} ${y-openingDepth}V${y+61}Q${x-60} ${y+76} ${x-44} ${y+76}H${x+44}Q${x+60} ${y+76} ${x+60} ${y+61}V${y-openingDepth}" fill="#fff" stroke="${C.line}" stroke-width="2.6"/><path d="M${x-56} ${y-14}H${x+56}V${y+59}Q${x+56} ${y+71} ${x+43} ${y+71}H${x-43}Q${x-56} ${y+71} ${x-56} ${y+59}Z" fill="${fill}"/>${path(`M${x-56} ${y-14}Q${x} ${y-5} ${x+56} ${y-14}`,C.line,1.1)}`;
 if(mode)s+=particles(x,y+13,mode);
 if(cap)s+=rect(x-62,y-93,124,17,'#d1e2e9',3);
 if(gas)s+=text(x,y-115,gas,14,'middle',C.muted)+arrow(x-87,y-79,20);
 if(heat)s+=rect(x-79,y+99,158,19,'#ecdcc2',4)+[-40,0,40].map(dx=>path(`M${x+dx} ${y+96}q-6 -7 0 -14q6 -7 0 -14`,C.gold,2)).join('');
 s+=text(x,y+(heat?148:104),label,14,'middle',C.muted);
 return s;
}
function bottle(x,y,label,fill='#eef3f5'){return rect(x-25,y-43,50,65,fill,6)+rect(x-19,y-55,38,14,'#9eb4bf',3)+text(x,y+47,label,13);}
function addition({kind='liquid',fill=C.blue,mode=null,names=[],heat=false}={}){
 let s=vessel(190,258,{fill,mode,heat,openingDepth:45,label:heat?'Illustrative heating support':'Generic reaction vessel'});
 if(names.length===1)s+=bottle(104,140,names[0],kind==='powder'?'#e6ddcb':C.pale)+arrow(146,216,37);
 else s+=names.map((n,i)=>bottle(62+i*100,140,n,kind==='powder'?'#e6ddcb':C.pale)+arrow(names.length===2?135+i*50:128+i*58,218,names.length===2?40+i*30:40+i*50)).join('');
 return s;
}
function stirring(mode=null,fill=C.blue){return vessel(185,250,{mode,fill})+path('M152 287q32 -20 63 0',C.line,2)+arrow(209,283,15)+text(185,391,'Stirring is reported; speed is unknown',13,'middle',C.muted);}
function filtered(){return bottle(81,140,'Crude slurry','#eef0e9')+arrow(107,203,45)+`<path d="M132 195H245L204 248V278H175V248Z" fill="#edf4f7" stroke="${C.line}" stroke-width="2.5"/>${path('M141 202H236',C.line,5)}${particles(190,172,'white')}<path d="M141 301v49h98v-49" fill="#e4eef4" stroke="${C.line}" stroke-width="2"/>`+text(190,164,'Retain the filter cake',16,'middle',C.green,600)+text(190,386,'Filter geometry is illustrative',13,'middle',C.muted);}
function drying(){return rect(53,142,271,223,'#edf3f7')+rect(77,168,222,156,'#fff')+path('M104 272H273',C.line,4)+particles(185,229,'white')+arrow(306,188)+text(184,121,'Vacuum drying',19,'middle',C.ink,600)+text(186,301,'Cd(acac)₂ precursor',16)+text(184,391,'Generic vacuum chamber',14,'middle',C.muted);}
function thermal(mode,kind='heat'){
 let s=vessel(185,244,{heat:kind==='heat',mode,fill:mode?'#e4dfd5':'#dac7af',label:kind==='heat'?'Illustrative heating support':'Generic reaction vessel'});
 if(kind==='cool')s+=arrow(78,189,90,'#45869e')+arrow(290,189,90,'#45869e')+text(184,132,'Cooling method not reported',15,'middle',C.muted);
 if(mode==='residue')s+=text(185,136,'Proposed coverage, not an intact shell',14,'middle',C.muted);
 return s;
}
function centrifuge({keep='pellet',ethanol=false}={}){
 let s=rect(34,139,160,150,'#edf3f7')+`<circle cx="114" cy="211" r="53" fill="#dae7ec" stroke="${C.line}" stroke-width="2"/>`+[-1,1].map(z=>`<g transform="translate(${114+z*28} 206) rotate(${z*35})">${rect(-9,-34,18,65,'#f9fcfd',6)}</g>`).join('')+text(112,317,'Centrifugation',16)+arrow(218,219);
 s+=`<path d="M252 161v118q0 34 29 43q29 -9 29 -43V161Z" fill="#e4eef1" stroke="${C.line}" stroke-width="2.5"/>`;
 if(keep==='pellet')s+=`<path d="M255 279q5 25 26 32q21 -7 26 -32Z" fill="${C.brown}"/>`+text(281,357,'Keep pellet',16,'middle',C.green,600);
 else s+=`<g transform="translate(280 218) scale(.5)">${particles(0,0,'heterodimer')}</g>`+`<path d="M255 279q5 25 26 32q21 -7 26 -32Z" fill="#8c999e"/>`+text(277,137,'Keep liquid',16,'middle',C.green,600)+text(185,370,'Discard insoluble sediment',15,'middle',C.muted);
 if(ethanol)s+=text(112,115,'Ethanol precipitation',16,'middle',C.ink,600);
 return s+text(185,404,'Rotor and tube geometry are illustrative',13,'middle',C.muted);
}
function redispersion(){return vessel(95,247,{mode:'pellet',fill:'#f2e9dc',label:'Retained pellet'})+arrow(187,235)+vessel(278,247,{mode:'heterodimer',label:'Hexane dispersion'});}
function analysis(kind){
 if(['tem','hrtem','saed','xrf'].includes(kind))return rect(59,139,90,190,'#dce8ef')+arrow(104,211,90)+rect(76,310,56,14,'#a2b5bc',3)+arrow(217,255)+rect(272,204,58,73,'#eff5f7',4)+text(106,365,kind==='xrf'?'X-ray probe':'Electron probe',15)+text(282,310,'Source data',14)+text(185,404,'Acquisition diagram; no simulated pattern',13,'middle',C.muted);
 if(kind==='magnetic')return path('M104 180v122q0 32 33 32h96q33 0 33 -32V180','#91a9b5',31)+rect(87,168,36,30,C.pale,3)+rect(247,168,36,30,C.pale,3)+rect(167,207,37,76,'#d7d0dc',5)+text(185,139,'Magnetic specimen',19,'middle',C.ink,600)+text(184,381,'Generic field / specimen diagram',14,'middle',C.muted);
 if(kind==='comparison')return bottle(102,222,'Product 4',C.blue)+bottle(280,222,'Reference',C.pale)+path('M140 211H240',C.line,2,'stroke-dasharray="5 5"')+text(185,148,'Separate comparison samples',18,'middle',C.ink,600)+text(185,351,'No reference is added to the product',14,'middle',C.muted);
 if(kind==='photo')return rect(66,139,83,39,'#bbc0dc',7)+arrow(132,202,55,'#8b79be')+vessel(234,262,{fill:'#c7eaf2',cap:true,mode:'heterodimer',label:'Illustrative blue emission'})+text(128,116,'Hand-held UV lamp',15);
 return rect(34,211,75,55,'#e3ecf1')+arrow(132,238)+rect(169,183,47,110,C.blue,4)+arrow(251,238)+rect(282,211,65,55,'#e3ecf1')+text(190,157,'Hexane optical sample',18,'middle',C.ink,600)+text(190,342,'Generic optical cell; path length unknown',14,'middle',C.muted);
}
const main={
 'hetero-charge':{art:()=>addition({names:['Pt(acac)₂','Diol']}),rows:[Q('Pt(acac)₂','platinum_precursor_mass'),Q('First diol charge','first_diol_mass'),Q('Dioctyl ether','dioctyl_ether_volume')],note:'Combine the named inputs. Nanoparticles are not depicted before the FePt formation step. The vessel and mixing apparatus are not specified.'},
 'hetero-preheat':{art:()=>thermal(null),rows:[Q('Solution temperature','temperature'),Q('Approximate thermal interval','duration'),L('Observed endpoint','Light-brown solution')],note:'The source says raised to 100°C for about 5 minutes until light brown. Ramp and hold times are not independently resolved; the heater shown is generic.'},
 'hetero-metal-addition':{art:()=>addition({names:['Oleylamine','Oleic acid','Fe(CO)₅'],fill:'#dac7af'}),rows:[Q('Oleylamine','oleylamine_volume'),Q('Oleic acid','oleic_acid_volume'),Q('Fe(CO)₅','iron_pentacarbonyl_volume')],note:'Add the three named reagents. Their individual addition order and rates are not reported. No FePt particle formation is assigned to this addition itself.'},
 'hetero-fept-growth':{art:()=>thermal('fept'),rows:[L('Thermal target','Boiling point of dioctyl ether'),Q('Duration','duration'),L('Numerical temperature','Not reported')],note:'FePt stage 1 forms in this heating step. The source does not supply a numerical boiling temperature or reflux apparatus; 280°C belongs to the later CdS conversion.'},
 'hetero-cool':{art:()=>thermal('fept','cool'),rows:[Q('Solution temperature','temperature'),L('Material retained','In-pot FePt dispersion'),L('Cooling rate / duration','Not reported')],note:'Cool the solution without separating or purifying FePt. No ice bath, oil bath, cooling fluid or imposed cooling rate is reported.'},
 'hetero-sulfur':{art:()=>addition({names:['Sulfur'],kind:'powder',mode:'fept'}),rows:[Q('Elemental sulfur powder','sulfur_mass'),Q('Stirring duration','duration'),Q('Temperature · preceding state','temperature')],note:'The authors assign sulfur deposition to stage 2. Isolating large quantities of intact shells was unsuccessful, so no isolated uniform shell is depicted.'},
 'hetero-cadmium-addition':{art:()=>addition({names:['TOPO','Diol','Cd(acac)₂'],mode:'residue'}),rows:[Q('TOPO','topo_mass'),Q('Second diol charge','second_diol_mass'),Q('Cd(acac)₂','cadmium_precursor_mass')],note:'Add these reagents to the stage-2 dispersion. The 105 mg diol is a separate charge from the initial 195 mg. Coverage symbols are explanatory, not resolved shell structure.'},
 'hetero-shell-hold':{art:()=>thermal('residue'),rows:[Q('Solution temperature','temperature'),Q('Duration','duration'),L('Source assignment','Proposed metastable stage 3')],note:'The authors propose FePt@CdS with amorphous CdS. Open patches represent uncertain coverage; intact isolated core–shell particles and shell thickness are not established.'},
 'hetero-crystallize':{art:()=>thermal('heterodimer'),rows:[Q('Solution temperature','temperature'),Q('Duration','duration'),L('Source product','FePt–CdS heterodimer 4')],note:'Heating yields crystalline CdS–FePt heterodimers. Dewetting is the authors’ mechanism. Paired symbols are not an atomic model, interface measurement or particle-size scale.'},
 'hetero-cool-workup':{art:()=>thermal('heterodimer','cool'),rows:[L('Endpoint','Room temperature'),L('Numerical temperature','Not reported'),L('Next operation','Ethanol precipitation')],note:'Stop heating and cool before adding ethanol. The cooling method is unknown; room temperature is not replaced with an assumed numerical value.'},
 'hetero-first-precipitation':{art:()=>centrifuge({ethanol:true}),rows:[Q('Ethanol addition','ethanol_volume'),L('Retain','Brown product pellet'),L('Centrifuge speed / duration','Not reported')],note:'Add ethanol and centrifuge. Keep the product precipitate for the following hexane redispersion. The drawn rotor and tube do not identify the experimental equipment.'},
 'hetero-hexane-redispersion':{art:redispersion,rows:[Q('Hexane','hexane_volume'),L('Starting fraction','First retained pellet'),L('Output','Crude hexane dispersion')],note:'Redisperse the first pellet. No sonication, heating, mixing duration or solution concentration is supplied.'},
 'hetero-insoluble-removal':{art:()=>centrifuge({keep:'liquid'}),rows:[L('Retain','Clarified hexane liquid'),L('Remove','Undissolved precipitate'),L('Centrifuge speed / duration','Not reported')],note:'This centrifugation keeps the liquid, unlike the precipitation steps. The discarded sediment is not chemically identified and is not labeled as product.'},
 'hetero-reprecipitation':{art:()=>centrifuge({ethanol:true}),rows:[Q('Second ethanol addition','ethanol_volume'),L('Retain','Final brown product pellet'),L('Product mass / yield','Not reported')],note:'Add ethanol to the clarified hexane dispersion and centrifuge to recover product 4. Keep the pellet for the final storage dispersion.'},
 'hetero-storage':{art:()=>vessel(185,253,{cap:true,mode:'heterodimer',gas:'N₂ storage',label:'Generic sealed storage vessel'}),rows:[Q('Hexane storage medium','hexane_volume'),L('Atmosphere','Nitrogen'),L('Storage temperature / duration','Not reported')],note:'Disperse the final product in 15 mL hexane and store under nitrogen. Nitrogen is specified for storage; its use as the reaction gas is not established.'}
};
const upstream={
 'cdacac-dissolve':{art:()=>addition({names:['CdCl₂'],kind:'powder'}),rows:[Q('CdCl₂ · reported mass','cadmium_chloride_mass'),Q('CdCl₂ · reported amount','cadmium_chloride_amount'),Q('DI water','water_volume')],note:'The source prints CdCl₂ at 80.5% grade. Hydration and assay basis remain unresolved. Both reported mass and amount are retained without a silent chemical correction.'},
 'cdacac-chelate':{art:()=>addition({names:['Acetylacetone']}),rows:[Q('2,4-Pentanedione','acetylacetone_volume'),Q('Reported amount','acetylacetone_amount'),Q('Magnetic stirring','duration')],note:'Add acetylacetone under magnetic stirring and continue for 15 minutes. Temperature, stirring speed and addition rate are not reported; particles are not shown at this stage.'},
 'cdacac-precipitate':{art:()=>addition({names:['Et₃N'],mode:'white'}),rows:[Q('Triethylamine','triethylamine_volume'),L('Observed endpoint','White precipitate'),L('Aging time / temperature','Not reported')],note:'White solid symbols represent the reported precipitate, not a measured crystal habit or nanoparticle-size distribution.'},
 'cdacac-filter':{art:filtered,rows:[L('Operation','Filtration'),L('Retain','Crude Cd(acac)₂ solid'),L('Washing / filter details','Not reported')],note:'Recover the crude product by filtration. The funnel and receiving vessel are generic. No washing solvent or pressure-assisted filtration is inferred.'},
 'cdacac-recrystallize':{art:()=>addition({names:['Ethanol','Water'],mode:'white'}),rows:[L('Recrystallization medium','Ethanol + water'),L('Isolated Cd(acac)₂ mass','2.8 g · source measurement'),L('Ratio / temperature / duration','Not reported')],note:'The reported 2.8 g belongs to the precursor preparation; the weighing state relative to drying is unresolved. It is not the amount used in the heterodimer reaction.'},
 'cdacac-dry':{art:drying,rows:[Q('Drying temperature','temperature'),L('Atmosphere','Vacuum'),L('Pressure / drying duration','Not reported')],note:'Dry the isolated precursor before use. The chamber is illustrative; vacuum pressure, drying duration and storage conditions are not provided.'}
};
const acquisition={
 'gu-2004-microscopy':{
  tem:{kind:'tem',rows:[L('Specimens','Stages 1, 2, 3 and product 4'),L('Method','TEM'),L('Instrument / voltage','Not reported')],note:'These are separate source-labeled specimens, not a mixed sample. Isolation of stages 2 and 3 may damage coverage; no new microscopy image is generated.'},
  hrtem:{kind:'hrtem',rows:[L('Specimen','Product 4'),L('Method','HRTEM'),L('Source evidence','Figure 1C')],note:'The source uses HRTEM to discuss crystalline CdS. Instrument voltage, measured lattice spacing and atomic interface coordinates are not supplied.'},
  saed:{kind:'saed',rows:[L('Specimen','Product 4'),L('Method','Selected-area electron diffraction'),L('Source evidence','Figure 1D')],note:'Link the actual source diffraction pattern. Do not fabricate diffraction rings or assign product-4 SAED to precursor 1.'}
 },
 'gu-2004-xrf':{xrf:{kind:'xrf',rows:[L('Specimen','Product 4'),L('Method','X-ray fluorescence'),L('Source evidence','Figure S-1')],note:'Preserve the main ratio and inconsistent SI software mol% separately. This is XRF, not XRD; Si and Rh are not assigned as product dopants.'}},
 'gu-2004-magnetometry':{
  'zfc-fc':{kind:'magnetic',rows:[L('Specimen','Product 4'),Q('Applied field','applied_field'),L('Acquisition','ZFC / FC')],note:'Product-4 magnetometry was performed immediately after synthesis. Specimen mass/state and detailed cooling protocol are unreported; no synthetic curve is displayed.'},
  hysteresis:{kind:'magnetic',rows:[L('Specimen','Product 4'),Q('Measurement temperature','temperature'),L('Acquisition','Field-dependent magnetometry')],note:'The source shows hysteresis at 5 K. The diagram illustrates measurement only and supplies neither a fabricated loop nor an unreported instrument model.'}
 },
 'gu-2004-optical':{
  absorption:{kind:'optical',rows:[L('Specimen','Product 4 in hexane'),L('Method','UV–visible absorption'),L('Source evidence','Figure 2C')],note:'293 nm FePt-assigned absorption and the 369 nm shoulder are source results. Cell geometry is generic; concentration and optical path length are unknown.'},
  fluorescence:{kind:'optical',rows:[L('Specimen','Product 4 in hexane'),Q('Excitation wavelength','excitation_wavelength'),L('Method','Photoluminescence')],note:'The 365 nm setting belongs to the spectrometer measurement. It is not automatically the wavelength of the hand-held lamp used for the photograph.'},
  'quantum-yield':{kind:'comparison',rows:[L('Product / reference','Separate samples'),L('Reference','9,10-Dibromoanthracene'),L('Reference quantum yield','11% · source standard')],note:'The reported product quantum yield is 3.2%. The reference is not physically added to product 4. Measurement corrections and standard matching details are not provided.'},
  'uv-photograph':{kind:'photo',rows:[L('Specimen','Product 4 in hexane'),L('Illumination','Hand-held UV lamp'),L('Lamp wavelength / power','Not reported')],note:'The source photograph shows blue emission. The explanatory color is not quantitative emission data, concentration or quantum yield.'}
 },
 'gu-2004-fept-control':{
  absorption:{kind:'optical',rows:[L('Specimen','As-prepared FePt 1 in hexane'),L('Source evidence','Figure S-2'),L('Numerical precursor peak','Not explicitly reported')],note:'This is the FePt precursor comparison. A visible broad UV maximum is not converted to an exact peak value from visual estimation.'},
  'zfc-fc':{kind:'magnetic',rows:[L('Specimen','As-prepared FePt 1'),L('Source evidence','Figure S-3'),L('Applied field','Not reported')],note:'Do not copy the final-product 100 Oe acquisition field, 11 K blocking value or an exact anisotropy fit to this precursor control.'}
 }
};
function choice(o,r){if(r.record_id==='gu-2004-heterodimer')return main[o.id];if(r.record_id==='gu-2004-cdacac-preparation')return upstream[o.id];const a=acquisition[r.record_id]?.[o.id];return a?{...a,art:()=>analysis(a.kind)}:null;}
function conditionPanel(o,c){let y=131;const rows=c.rows.map(d=>({label:d.label,value:d.key?quantity(o,d.key):d.value}));if((o.stage==='synthesis'||o.stage==='precursor_preparation')&&!rows.some(row=>row.label==='Atmosphere'))rows.push(L('Atmosphere',o.environment.value==='Vacuum'?'Vacuum; pressure not reported':'Inert; gas / pressure not reported'));
 else if(o.stage==='workup')rows.push(L('Atmosphere / pressure','Not reported'));
 let out=rect(366,94,368,326,'#f3f8fb',14)+text(388,118,'SOURCE CONDITIONS AND INPUTS',12,'start',C.muted,600);
 for(const row of rows){const labelLines=wrap(row.label,44),valueLines=wrap(row.value,40);out+=labelLines.map((s,i)=>text(389,y+18+i*15,s,12,'start',C.muted,600)).join('');y+=labelLines.length*15+5;out+=valueLines.map((s,i)=>text(389,y+18+i*19,s,16,'start',C.ink,500)).join('');y+=valueLines.length*19+9;}
 return out;
}
export function buildGu2004Scene(o,r){if(r?.lineage?.source_group!=='gu2004'||!r.record_id?.startsWith('gu-2004-'))return null;const c=choice(o,r);if(!c)return null;
 const titleLines=wrap(o.label,67),heading=titleLines.map((s,i)=>text(28,32+i*24,s,20,'start',C.ink,600)).join('');
 const svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 540" role="img" aria-label="${esc(o.label)} — explanatory apparatus" style="width:100%;height:auto"><title>${esc(o.label)}</title><desc>Gu et al. 2004, source-specific operation. Apparatus geometry, colors and particle symbols are explanatory. Original measurements remain separate.</desc><rect width="760" height="540" rx="18" fill="#ffffff"/>${heading}${text(28,81,o.stage==='characterization'?'CHARACTERIZATION · SEPARATE SOURCE SPECIMEN':'PREPARATION · SOURCE OPERATION',11,'start',C.muted,600)}${c.art()}${conditionPanel(o,c)}${path('M28 442H732','#d9e6ec',1)}${para(29,465,c.note,{max:105,size:14,line:18})}${text(28,529,'Generic geometry · illustrative colors and particle symbols · not an atomic structure',11,'start',C.muted)}</svg>`;
 return{kind:`${r.record_id}--${o.id}`,svg,caption:'Source-specific explanatory schematic. Apparatus geometry and particle symbols are illustrative; reported inputs, conditions and missingness remain traceable to the canonical operation.'};
}
export function createGu2004Art(o,r){const s=buildGu2004Scene(o,r);if(!s)return null;const d=document.createElement('div');d.className='protocol-art protocol-art-gu2004';d.dataset.scene='gu2004-'+s.kind;d.style.height='auto';d.innerHTML=s.svg;return d;}
export const gu2004SceneSelection={source_group:'gu2004',records:{'gu-2004-cdacac-preparation':Object.keys(upstream),'gu-2004-heterodimer':Object.keys(main),...Object.fromEntries(Object.entries(acquisition).map(([k,v])=>[k,Object.keys(v)]))}};
