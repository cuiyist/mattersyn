// Norberg 2004: source-specific explanatory apparatus. No measured geometry.
const C={ink:'#173c4b',muted:'#557381',line:'#7b9baa',pale:'#f1f7fa',blue:'#dcecf3',gold:'#d5a34a',particle:'#607e9a',green:'#217862'};
const esc=s=>String(s??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const text=(x,y,s,size=16,anchor='middle',fill=C.ink,weight=400)=>`<text x="${x}" y="${y}" text-anchor="${anchor}" font-family="Arial,sans-serif" font-size="${size}" font-weight="${weight}" fill="${fill}">${esc(s)}</text>`;
const path=(d,color=C.line,w=2.4,extra='')=>`<path d="${d}" fill="none" stroke="${color}" stroke-width="${w}" stroke-linecap="round" stroke-linejoin="round" ${extra}/>`;
const rect=(x,y,w,h,fill=C.pale,rx=10)=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${rx}" fill="${fill}" stroke="${C.line}" stroke-width="1.5"/>`;
const arrow=(x,y,a=0,color=C.line)=>`<g transform="translate(${x} ${y}) rotate(${a})">${path('M-20 0H20M12 -7L20 0L12 7',color,2.8)}</g>`;
function wrap(s,max=58){const lines=[];let row='';for(const word of String(s).split(/\s+/)){if(row&&(`${row} ${word}`).length>max){lines.push(row);row=word;}else row+=(row?' ':'')+word;}if(row)lines.push(row);return lines;}
const para=(x,y,s,{max=45,size=14,line=19,anchor='start',fill=C.muted}={})=>wrap(s,max).map((t,i)=>text(x,y+i*line,t,size,anchor,fill)).join('');
function quantity(q){if(q.value!=null)return `${q.approximate?'≈ ':''}${q.value} ${q.unit==='degC'?'°C':q.unit??''}`.trim();if(q.minimum!=null&&q.maximum!=null)return `${q.minimum}–${q.maximum} ${q.unit}`;if(q.maximum!=null)return `${q.maximum_exclusive?'<':'≤'} ${q.maximum} ${q.unit}`;if(q.minimum!=null)return `${q.minimum_exclusive?'>':'≥'} ${q.minimum} ${q.unit}`;return 'Not reported';}
function particles(x,y,pellet=false){return [[-27,7],[16,-7],[31,27],[-6,31],[-33,32]].map(([a,b],i)=>`<circle cx="${x+a}" cy="${pellet?y+38+(i%2)*4:y+b}" r="6" fill="${C.particle}"/>`).join('');}
function vessel(x,y,{dots=false,pellet=false,heat=false,label='',cap=false}={}){
 let s=`<path d="M${x-53} ${y-62}V${y+55}Q${x-53} ${y+72} ${x-37} ${y+72}H${x+37}Q${x+53} ${y+72} ${x+53} ${y+55}V${y-62}" fill="#fff" stroke="${C.line}" stroke-width="2.5"/><path d="M${x-49} ${y-5}H${x+49}V${y+53}Q${x+49} ${y+67} ${x+35} ${y+67}H${x-35}Q${x-49} ${y+67} ${x-49} ${y+53}Z" fill="${C.blue}"/>`;
 if(dots||pellet)s+=particles(x,y+3,pellet);
 if(cap)s+=rect(x-54,y-74,108,14,'#adbec6',3);
 if(heat)s+=rect(x-70,y+89,140,17,'#efe0c5',3)+[-36,0,36].map(a=>path(`M${x+a} ${y+86}q-5 -7 0 -14q5 -7 0 -14`,C.gold,2)).join('');
 return s+para(x,y+(heat?132:101),label,{max:35,size:13,line:17,anchor:'middle'});
}
function bottle(x,y,label){return rect(x-26,y-33,52,65,'#edf4f7',6)+rect(x-19,y-45,38,14,'#a9bfc9',3)+para(x,y+54,label,{max:19,size:13,line:16,anchor:'middle',fill:C.ink});}
function charge(c,dots=false,drop=false){let s=vessel(190,300,{dots,label:c.specimen});
 const names=c.names.length?c.names:['Source-defined input'];
 s+=names.map((n,i)=>bottle(names.length===1?116:85+i*155,158,n)).join('');
 if(drop){s+=path('M119 207v35',C.line,3)+[254,264,274].map(y=>`<circle cx="119" cy="${y}" r="2" fill="${C.line}"/>`).join('');if(c.art==='drop')s+=path('M164 335q24 -18 48 0',C.line,2)+arrow(209,331,20);}
 else s+=arrow(137,235,43);
 return s;
}
function precipitation(c){return vessel(97,252,{dots:true,label:c.specimen})+arrow(190,263)+vessel(289,252,{pellet:true,label:'Retain particle fraction'})+para(192,141,c.names.length?c.names.join(' + '):'Rapid precipitation; antisolvent unspecified',{max:36,size:16,line:21,anchor:'middle',fill:C.ink})+text(193,409,'Separation equipment is not specified',13,'middle',C.muted);}
function redisperse(c){return vessel(96,256,{pellet:true,label:'Recovered particles'})+arrow(190,258)+vessel(290,256,{dots:true,label:c.names.join(' / ')})+text(190,156,'Redispersion',20,'middle',C.ink,600);}
function wash(c){return vessel(98,260,{pellet:true,label:'Retain particle fraction'})+arrow(188,229)+arrow(188,302,180)+vessel(286,260,{dots:true,label:'Resuspended colloids'})+para(190,141,c.names.join(' / '),{max:38,size:17,line:22,anchor:'middle',fill:C.ink})+text(190,411,'Wash / recovery settings remain unspecified',13,'middle',C.muted);}
function thermal(c,cool=false){return vessel(190,258,{dots:true,heat:!cool,label:c.specimen})+(cool?arrow(93,196,90,'#4b8fba')+arrow(285,196,90,'#4b8fba')+text(190,145,'Cooling',20,'middle',C.ink,600):para(190,145,c.names.length?c.names.join(' + '):'Thermal growth / treatment',{max:36,size:17,line:22,anchor:'middle',fill:C.ink}))+text(190,439,cool?'Cooling method not reported':'Heating support is generic',13,'middle',C.muted);}
function aliquot(c){return vessel(111,267,{dots:true,label:c.specimen})+path('M231 170l-59 92',C.line,7)+arrow(252,248,28)+rect(291,264,36,80,C.blue,3)+text(308,377,'Aliquot',14)+text(191,150,'Sample the reaction bulk',19,'middle',C.ink,600)+text(191,423,'Remaining bulk and sampled aliquot are distinct',13,'middle',C.muted);}
function substrate(x,y,label){return `<path d="M${x-66} ${y}l80 -22l53 24l-80 23Z" fill="#d9e9f1" stroke="${C.line}" stroke-width="2"/>`+text(x,y+62,label,14);}
function film(c,kind){
 if(kind==='cycles')return [90,197,304].map((x,i)=>`<g transform="translate(${x} 240) scale(.7)">${substrate(0,0,'')}</g>`+text(x,305,['Film A','Film B','Film C'][i],14)+text(x,343,i===0?'40 coats':'20 coats',17,'middle',C.green,600)).join('')+text(193,153,'Coat → anneal → repeat',20,'middle',C.ink,600)+text(193,414,'Preparation scope: A–C only',15,'middle',C.muted);
 if(kind==='anneal')return rect(64,151,257,223,'#efe8dd',12)+rect(88,179,209,160,'#fff',6)+substrate(187,261,'Deposited layer')+[-35,0,35].map(a=>path(`M${189+a} 229q-7 -10 0 -20q7 -10 0 -20`,C.gold,2)).join('')+text(192,416,'Generic thermal chamber · air',14,'middle',C.muted);
 let s=kind==='spin'?substrate(190,283,'')+text(190,377,'Fused-silica substrate',14):`<ellipse cx="190" cy="296" rx="76" ry="26" fill="#d9e9f1" stroke="${C.line}" stroke-width="2"/>`+text(190,358,'Quartz disk',14);
 s+=path('M209 172l-24 77',C.line,6)+`<circle cx="184" cy="259" r="4" fill="${C.particle}"/>`+para(193,137,c.names.join(' / '),{max:34,size:16,line:21,anchor:'middle',fill:C.ink});
 if(kind==='spin')s+=`<ellipse cx="190" cy="331" rx="99" ry="16" fill="none" stroke="${C.line}" stroke-width="2"/>`+arrow(267,321,-10)+text(191,414,'Spin coating · speed not reported',14,'middle',C.muted);
 else s+=text(192,421,'Frozen solution for MCD',16,'middle',C.muted);
 return s;
}
function alternatives(){const open=(x,y,label)=>path(`M${x-25} ${y-33}v65h50v-65`,C.line,2)+rect(x-23,y,46,29,C.blue,1)+text(x,y+55,label,13);return [85,195,305].map((x,i)=>i===2?bottle(x,235,'Anaerobic'):open(x,235,['Air baseline','Zn acetate'][i])).join('')+[125,270].map((x,i)=>open(x,359,['NaOAc control','Mn nitrate control'][i])).join('')+text(191,146,'Independent solution variants',19,'middle',C.ink,600);}
function optical(c,lum=false){let s=rect(48,240,65,57,'#d4e3eb')+arrow(136,269)+rect(178,210,46,119,C.blue,4)+arrow(250,269)+rect(290,240,58,57,'#d4e3eb');if(lum)s+=arrow(201,179,-90,'#9180bc')+rect(174,131,57,24,'#e2dcec',5);return s+para(197,378,c.specimen,{max:41,size:16,line:21,anchor:'middle',fill:C.ink})+text(197,431,'Generic acquisition geometry; source curves separate',13,'middle',C.muted);}
function magnet(c,epr=false){return path('M97 193v131q0 31 34 31h121q31 0 31 -31V193','#9ab2bf',30)+rect(174,224,37,76,'#d4e3eb',4)+arrow(150,256)+arrow(242,256)+text(192,159,epr?'Microwave field / specimen':'Magnetic field / specimen',18,'middle',C.ink,600)+para(192,403,c.specimen,{max:39,size:15,line:21,anchor:'middle'});}
function comparison(c,kind){const labels=kind==='optical-compare'?['Undoped','0.13% Mn','1.3% Mn']:kind==='magnetic-compare'?['Powder','Film A','Film B','Film C']:['Film A','Precursor colloid'];const w=labels.length===4?76:labels.length===3?103:139;return labels.map((label,i)=>{const x=192+(i-(labels.length-1)/2)*(w+10);return rect(x-w/2,228,w,104,i%2?'#dce5eb':'#e5edf4',6)+para(x,276,label,{max:17,size:14,line:20,anchor:'middle',fill:C.ink});}).join('')+para(192,158,c.specimen,{max:34,size:18,line:23,anchor:'middle',fill:C.ink})+text(192,380,'Separate source specimens',16,'middle',C.ink,600)+text(192,420,kind==='epr-compare'?'Film A compared with precursor colloid':'No physical mixing or shared batch inferred',13,'middle',C.muted);}
function diffraction(c,filmMode=false){return rect(56,178,63,45,'#d5e5ed',6)+path('M115 224L194 289L290 199','#b09257',3)+substrate(191,302,filmMode?'Thin-film specimen':'Powder specimen')+(filmMode?'':`<g transform="translate(191 275) scale(.65)">${particles(0,0,true)}</g>`)+rect(284,175,41,75,'#d5e5ed',4)+text(192,148,'X-ray diffraction',20,'middle',C.ink,600)+text(192,422,'No artificial diffraction peaks or pattern',13,'middle',C.muted);}
function electron(c){return rect(75,144,86,212,'#deebf1',10)+arrow(118,204,90)+rect(89,292,57,11,'#aabfc8',3)+arrow(209,271)+rect(271,223,60,72,'#edf4f8',4)+text(118,395,'Electron probe',15)+text(299,333,'Source image',14)+text(191,445,'No invented lattice image or diffraction pattern',13,'middle',C.muted);}
function model(){return rect(50,178,291,177,'#e6eef4',10)+rect(70,199,251,114,'#fff',4)+text(194,240,'Spin Hamiltonian · Equation 1',17)+text(194,280,'Full-matrix diagonalization',16)+path('M172 357v27h-40m40 0h58',C.line,3)+text(193,431,'Calculated EPR traces; not measured atom positions',13,'middle',C.muted);}
function sceneArt(c){switch(c.art){
 case 'charge':case 'solution':return charge(c,false);
 case 'drop':case 'titrate':return charge(c,false,true);
 case 'particle-drop':return charge(c,true,true);
 case 'particle-add':case 'cap':return charge(c,true);
 case 'precipitate':return precipitation(c);case 'redisperse':return redisperse(c);case 'wash':return wash(c);
 case 'heat':return thermal(c);case 'cool':return thermal(c,true);
 case 'ripen':return vessel(190,279,{dots:true,label:c.specimen})+text(190,151,'Initial growth → further ripening',18,'middle',C.ink,600)+text(190,426,'Room-temperature / near-60 °C alternatives',13,'middle',C.muted);
 case 'control-particles':return vessel(191,271,{dots:true,label:'Pure ZnO in ethanol'})+text(191,155,'No manganese in upstream feed',18,'middle',C.ink,600);
 case 'spin':case 'anneal':case 'cycles':case 'dropcoat':return film(c,c.art);
 case 'aliquot':return aliquot(c);case 'alternatives':return alternatives();
 case 'stability':return alternatives()+text(191,468,'Store, then compare absorption',15,'middle',C.muted);
 case 'dilute':return rect(71,224,43,113,C.blue,4)+arrow(157,279)+rect(196,224,43,113,'#ecf4f8',4)+arrow(282,279)+rect(321,240,35,70,C.pale,4)+text(94,371,'Aliquot',15)+text(219,371,'Diluted',15)+text(337,371,'Read',15)+text(195,165,'Measure → dilute → remeasure',18,'middle',C.ink,600);
 case 'optical':case 'lum':return optical(c,c.art==='lum');
 case 'magnetic':case 'epr':case 'mcd':return magnet(c,c.art==='epr');
 case 'optical-compare':case 'magnetic-compare':case 'epr-compare':return comparison(c,c.art);
 case 'xrd-powder':case 'xrd-film':return diffraction(c,c.art==='xrd-film');case 'tem':return electron(c);
 case 'model':return model();
 case 'structure':return rect(65,166,255,67,C.pale,9)+text(192,206,'TEM / HRTEM',20)+rect(65,261,255,67,C.pale,9)+text(192,301,'Powder / thin-film XRD',19)+text(192,398,'Keep panel and specimen assignments',14,'middle',C.muted);
 case 'icp':return bottle(84,273,'Analytical aliquot')+arrow(146,273)+path('M190 332q-29 -73 0 -109q27 33 0 109',C.gold,9)+arrow(239,273)+rect(281,230,60,87,C.pale,5)+text(190,155,'ICP-AES analysis',20,'middle',C.ink,600)+text(193,407,'Elemental concentration; no atom map',14,'middle',C.muted);
 default:throw Error('Unknown scene art '+c.art);
}}
export function buildNorberg2004Scene(o,r){
 if(r?.lineage?.source_group!=='norberg2004'||!DATA.records[r.record_id]?.includes(o?.id))return null;
 const c=DATA.configs[o.id];if(!c)return null;
 const rows=Object.entries(o.parameters??{}).map(([k,q])=>({label:DATA.parameter_labels[k],value:quantity(q)})).concat(c.extra_rows);
 if(o.environment?.value)rows.push({label:'Atmosphere',value:o.environment.value});
 if(o.stage!=='characterization'&&!rows.some(x=>/pressure/i.test(x.label)))rows.push({label:'Numerical pressure',value:'Not reported'});
 let y=130,panel='';for(const row of rows){const lines=wrap(row.value,49);panel+=text(422,y,row.label,12,'start',C.muted,600)+lines.map((line,i)=>text(422,y+23+i*20,line,16,'start',C.ink,500)).join('');y+=Math.max(1,lines.length)*20+35;}
 const divider=Math.max(510,y+5),notes=wrap(c.note,115),height=divider+78+notes.length*19;
 const svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 ${height}" role="img" aria-label="${esc(c.title)}" style="width:100%;height:auto"><title>${esc(c.title)}</title><desc>Norberg et al. 2004. Source-specific inputs and conditions; geometry, colors and particles are illustrative, not measured apparatus or atomic coordinates.</desc><rect width="900" height="${height}" rx="18" fill="#fff"/>${text(28,38,c.title,24,'start',C.ink,600)}${text(28,72,o.stage==='characterization'?'ACQUISITION / MODEL CONTEXT':'SOURCE PREPARATION / MATERIAL FLOW',12,'start',C.muted,600)}${sceneArt(c)}${rect(398,96,476,divider-114,'#f3f8fb',14)}${panel}${path(`M28 ${divider}H872`,'#d9e6ec',1)}${notes.map((line,i)=>text(29,divider+30+i*19,line,14,'start',C.muted)).join('')}${text(28,height-19,'Illustrative geometry and particle symbols · no measured atomic coordinates or surface coverage',11,'start',C.muted)}</svg>`;
 return {kind:`${r.record_id}--${o.id}`,svg,caption:'Source-specific explanatory schematic. Labels retain the reported inputs, conditions, sample scopes and missingness. Geometry, colors and particle symbols are illustrative.'};
}
export function createNorberg2004Art(o,r){const s=buildNorberg2004Scene(o,r);if(!s)return null;const d=document.createElement('div');d.className='protocol-art protocol-art-norberg2004';d.dataset.scene='norberg2004-'+s.kind;d.style.height='auto';d.innerHTML=s.svg;return d;}
export const norberg2004SceneSelection={source_group:'norberg2004',records:DATA.records};
