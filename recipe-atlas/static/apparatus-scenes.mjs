const condition=(label,value)=>({label,value});
const unset='Not reported';
export const sceneRecords={
 synthesis:[
 {art:'materials',title:'PREPARE THE STARTING MATERIALS',caption:'Reagents and precursor stock',conditions:[condition('Stock','1.0 M TOPSe'),condition('Handling','Airless procedures'),condition('Stock temperature',unset),condition('Preparation time',unset)],path:['Se + TOP','TOPSe stock','Prepare reagents']},
 {art:'hot',title:'DRY & DEGAS THE TOPO',caption:'50 g TOPO · heated vessel',conditions:[condition('Reaction temperature','≈200 °C'),condition('Duration','≈20 min'),condition('Pressure','≈1 Torr'),condition('Gas treatment','Periodic Ar flushing')],path:['50 g TOPO','Dry & degas','Stabilize under Ar']},
 {art:'combine',title:'COMBINE SOLUTIONS A + B',caption:'Prepare and combine in the drybox',conditions:[condition('Solution A','Me₂Cd + TOP'),condition('Solution B','TOPSe + TOP'),condition('Temperature / time',unset),condition('Environment','Drybox; gas unspecified')],path:['Solution A + B','Combine','Load syringe']},
 {art:'inject',title:'MAKE A SINGLE RAPID INJECTION',caption:'Heat removed · vigorous stirring',conditions:[condition('Reaction temperature','≈300 → ≈180 °C'),condition('Injection duration',unset),condition('Heating','Removed for injection'),condition('Setup before injection','≈1 atm Ar')],path:['Combined precursor','Rapid injection','Nucleation']},
 {art:'grow',title:'REHEAT, GROW & SAMPLE',caption:'Heating restored · absorption checks',conditions:[condition('Initial growth range','230–260 °C'),condition('Growth duration','A few hours'),condition('Sample interval','5–10 min'),condition('Adjustment','Guided by absorption')],path:['Restore heating','Check aliquots','Adjust temperature']},
 {art:'withdraw',title:'TRANSFER BY CANNULA',caption:'Collect a portion in a vial',conditions:[condition('Endpoint','Desired absorption'),condition('Withdrawal temperature',unset),condition('Withdrawal duration',unset),condition('Next workup','10-mL reaction aliquot')],path:['Growth solution','Cannula transfer','Collection vial']}
 ],
 purification:[
 {art:'cool',title:'COOL THE REACTION ALIQUOT',caption:'Cool to just above TOPO’s melting point',conditions:[condition('Aliquot volume','10 mL'),condition('Target temperature','≈60 °C'),condition('Cooling duration',unset),condition('Cooling method',unset)],path:['10-mL aliquot','Cool','Ready to flocculate']},
 {art:'flocculate',title:'FLOCCULATE & CENTRIFUGE',caption:'Keep the nanocrystal flocculate',conditions:[condition('Add methanol','20 mL · anhydrous'),condition('Separation','Centrifugation'),condition('Retain','Flocculate'),condition('Speed / duration',unset)],path:['Add methanol','Centrifuge','Keep flocculate']},
 {art:'clarify',title:'REMOVE THE GRAY BYPRODUCT',caption:'Keep the clear liquid; discard the gray solid',conditions:[condition('Add 1-butanol','25 mL · anhydrous'),condition('Retain','Clear supernatant'),condition('Discard','Gray Cd/Se byproduct'),condition('Speed / duration',unset)],path:['Redisperse','Centrifuge','Keep supernatant']},
 {art:'reprecipitate',title:'REFLOCCULATE THE NANOCRYSTALS',caption:'Remove excess TOP and TOPO',conditions:[condition('Add methanol','25 mL · anhydrous'),condition('Product fraction','Flocculate'),condition('Temperature',unset),condition('Addition rate',unset)],path:['Clear supernatant','Add methanol','Collect flocculate']},
 {art:'dry',title:'RINSE & VACUUM-DRY',caption:'Product recovered from the 10-mL aliquot',conditions:[condition('Methanol rinse','50 mL'),condition('Drying environment','Vacuum'),condition('Pressure / time',unset),condition('Capped product','≈300 mg')],path:['Rinse flocculate','Vacuum dry','Capped CdSe powder']}
 ],
 fractionation:[
 {art:'disperse',title:'MAKE A CLEAR DISPERSION',caption:'Purified nanocrystals in 1-butanol',conditions:[condition('Dispersing solvent','Anhydrous 1-butanol'),condition('Appearance','Optically clear'),condition('Volume',unset),condition('Temperature',unset)],path:['Purified nanocrystals','1-butanol','Clear dispersion']},
 {art:'select',title:'ADD METHANOL DROPWISE',caption:'Retain the large-particle-enriched precipitate',conditions:[condition('Nonsolvent','Anhydrous methanol'),condition('Addition','Dropwise'),condition('Endpoint','Persistent opalescence'),condition('Volume / duration',unset)],path:['Add dropwise','Centrifuge','Select precipitate']},
 {art:'repeat',title:'REPEAT THE SIZE SELECTION',caption:'Redisperse, precipitate and check absorption',conditions:[condition('Disperse in','1-butanol'),condition('Precipitate with','Methanol'),condition('Stop when','No further sharpening'),condition('Fixed cycle count',unset)],path:['Redisperse','Reprecipitate','Check absorption']}
 ]
};
export const hotBathStabilized={art:'hot',title:'STABILIZE UNDER ARGON',caption:'50 g TOPO · ready for precursor injection',conditions:[condition('Reaction temperature','≈300 °C'),condition('Stabilization duration',unset),condition('Pressure','≈1 atm'),condition('Atmosphere','Argon')],path:['Degassed TOPO','Stabilize under Ar','Ready to inject']};

const flask='<img class="scene-flask" src="assets/chemical-registry/svg/wu2008-three-neck-flask.svg" alt="Illustrative three-neck flask; geometry and fittings are not measured">';
const bath='<div class="heating-bath" aria-hidden="true"><div class="bath-rim"></div><div class="bath-front"></div><div class="heater-base"><i></i><span>HEATING</span><b></b></div><div class="heat-lines"><i></i><i></i><i></i></div></div>';
const syringe='<div class="scene-syringe" aria-hidden="true"><div class="plunger-top"></div><div class="plunger-stem"></div><div class="syringe-barrel"><i></i></div><div class="syringe-needle"></div></div>';
function vial(label,kind='clear',extra=''){return '<div class="scene-vial '+kind+' '+extra+'"><div class="sv-cap"></div><div class="sv-glass"><div class="sv-liquid"></div><div class="sv-solid"></div></div><span>'+label+'</span></div>';}
const centrifuge='<div class="mini-centrifuge" aria-hidden="true"><div class="rotor"><i></i><i></i><i></i><i></i></div><span>CENTRIFUGE</span></div>';
const dropper='<div class="scene-dropper" aria-hidden="true"><i></i><b></b><span></span></div>';
const sceneArt={
 materials:'<div class="stock-prep-diagram"><span class="mini-label">SEPARATE STOCK PREPARATION</span><h3>Se shot + TOP</h3><span class="preparation-arrow" aria-hidden="true">↓</span><h3>1.0 M TOPSe in TOP</h3><p>Elemental selenium is dissolved to prepare the stock. The injected selenium precursor is TOPSe.</p><a href="#stocks">Precursor and solvent structures ↑</a></div>',
 silyl:'<div class="stock-prep-diagram"><span class="mini-label">SELENIUM PRECURSOR · METHOD 2</span><h3>Me₃Si—Se—SiMe₃</h3><p>Bis(trimethylsilyl)selenium</p><div class="storage-note"><strong>Storage: −35 °C</strong><span>Drybox · gas and duration not specified</span></div><a href="#precursor-preparation">Cited precursor preparation ↑</a></div>',
 route2:'<div class="stock-prep-diagram"><span class="mini-label">PRECURSOR SUBSTITUTION</span><h3>Me₂Cd + (TMS)₂Se</h3><p>Coordinating-medium / injection framework referenced to Method 1.</p><div class="storage-note"><strong>CdSe formulation incompletely specified</strong><span>Charge, injection-stock concentration and general growth schedule are not restated.</span></div></div>',
 hot:flask+bath+'<div class="gas-line"><span id="scene-gas">Vacuum / Ar</span><i></i></div>',
 combine:'<div class="drybox-frame"><span class="drybox-label">DRYBOX</span><div class="solution-pair">'+vial('A · Me₂Cd + TOP','clear')+'<b>+</b>'+vial('B · TOPSe + TOP','clear')+'</div><div class="combine-arrow">↓</div><div class="mixture-label">Combined precursor mixture</div></div>',
 inject:flask+syringe+'<div class="stir-indicator" aria-hidden="true">↻</div><div class="heat-off">HEAT REMOVED</div>',
 grow:flask+bath+'<div class="sample-monitor"><div class="cuvette"><i></i></div><span>ABSORPTION<br>CHECK</span></div>',
 withdraw:flask+'<div class="cannula-line" aria-hidden="true"></div>'+vial('Collection vial','clear','collection-vial'),
 cool:vial('10-mL aliquot','clear','central-vial')+'<div class="cooling-note"><span>↓</span> COOL TO<br><strong>≈60 °C</strong></div>',
 flocculate:dropper+vial('Keep flocculate','pellet','central-vial')+centrifuge,
 clarify:'<div class="fraction-pair">'+vial('Clear liquid · KEEP','clear','keep-fraction')+vial('Gray solid · DISCARD','gray','discard-fraction')+'</div>'+centrifuge,
 reprecipitate:dropper+vial('CdSe flocculate','pellet','central-vial')+'<div class="solvent-tag">+ Methanol</div>',
 dry:'<div class="vacuum-dome"><span>VACUUM</span><div class="powder-dish"><i></i></div></div><div class="powder-caption">TOP/TOPO-capped CdSe</div>',
 disperse:vial('Clear dispersion','clear','central-vial')+'<div class="solvent-tag">1-Butanol</div>',
 select:dropper+vial('Persistent opalescence','cloudy','central-vial')+'<div class="solvent-tag">Dropwise methanol</div>',
 repeat:'<div class="selection-cycle"><span>↻</span>'+vial('Redisperse','clear')+vial('Reprecipitate','pellet')+'</div><div class="stock-note">Check absorption after each cycle</div>'
};

let currentProtocol='synthesis',currentStep=0,hotPhase='degas';
export function getApparatusScene(protocol,index,phase='degas'){
 return protocol==='synthesis'&&index===1&&phase==='stabilize'?hotBathStabilized:sceneRecords[protocol][index];
}
export function renderApparatus(protocol,index){
 if(protocol!==currentProtocol||index!==currentStep)hotPhase='degas';
 currentProtocol=protocol;currentStep=index;
 const scene=getApparatusScene(protocol,index,hotPhase),host=document.getElementById('stage-apparatus');
 host.dataset.scene=scene.art;host.dataset.phase=hotPhase;
 document.getElementById('apparatus-heading').textContent=scene.title;
 const picture=document.getElementById('apparatus-picture');picture.innerHTML=sceneArt[scene.art];picture.setAttribute('aria-label',scene.caption);
 for(const [selector,text] of Object.entries(scene.labels||{})){const element=picture.querySelector(selector);if(element)element.textContent=text;}
 for(const selector of scene.hide||[])picture.querySelectorAll(selector).forEach(element=>element.hidden=true);
 const gas=document.getElementById('scene-gas');if(gas)gas.textContent=hotPhase==='degas'?'Vacuum / Ar':'Argon';
 document.getElementById('apparatus-caption').textContent=scene.caption;
 document.getElementById('apparatus-conditions').replaceChildren(...scene.conditions.map(({label,value})=>{
  const div=document.createElement('div');const dt=document.createElement('dt');const dd=document.createElement('dd');dt.textContent=label;dd.textContent=value;if(value===unset)div.className='condition-missing';div.append(dt,dd);return div;
 }));
 const phases=document.getElementById('bath-phases');phases.hidden=protocol!=='synthesis'||index!==1;
 phases.querySelectorAll('button').forEach(button=>{const selected=button.dataset.bathPhase===hotPhase;button.classList.toggle('active',selected);button.setAttribute('aria-pressed',String(selected));});
 ['path-start','path-middle','path-end'].forEach((id,i)=>document.getElementById(id).textContent=scene.path[i]);
}
document.querySelectorAll('[data-bath-phase]').forEach(button=>button.addEventListener('click',()=>{hotPhase=button.dataset.bathPhase;renderApparatus(currentProtocol,currentStep);}));
