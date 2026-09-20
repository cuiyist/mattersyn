import {initializeCharacterization} from './characterization.mjs';
import {renderApparatus,sceneRecords} from './apparatus-scenes.mjs';
import {protocols,stocks,inventory,auxiliaryInventory,feedback} from './material-data.mjs';
import {buildCrystal} from './shape-data.mjs';
const $=id=>document.getElementById(id);
const method=document.body.dataset.method;
const colors={C:'#728399',H:'#d9e1ea',O:'#df6279',P:'#e6a541',Cd:'#159eab',Se:'#e3ad51',Si:'#9290ad',Cl:'#68ad75',N:'#4c7ed7',B:'#d6a081',Li:'#a67cca',Ar:'#8ba6b0'};
const panels=new Set();
let molecules=[],selectedStock=0,highlight=true;
function activeButtons(selector,attribute,value){document.querySelectorAll(selector).forEach(b=>{const active=b.dataset[attribute]===String(value);b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active));});}
function registerViewer(host,viewer,reset){
 host.tabIndex=0;host.addEventListener('keydown',event=>{const rotate={ArrowLeft:[-12,'y'],ArrowRight:[12,'y'],ArrowUp:[-12,'x'],ArrowDown:[12,'x']}[event.key];if(rotate)viewer.rotate(...rotate);else if(['+','='].includes(event.key))viewer.zoom(1.15);else if(event.key==='-')viewer.zoom(1/1.15);else if(event.key==='Home')reset();else return;event.preventDefault();viewer.render();});
 const observer=new ResizeObserver(()=>{if(host.clientWidth&&host.clientHeight){viewer.resize();viewer.render();}});observer.observe(host);return observer;
}
function atomData(record){
 const atoms=record.atoms.map((a,i)=>({index:i,serial:i,elem:a.element??a.elem,x:a.x,y:a.y,z:a.z,bonds:[],bondOrder:[]}));
 for(const b of record.bonds||[]){atoms[b.a].bonds.push(b.b);atoms[b.a].bondOrder.push(b.order);atoms[b.b].bonds.push(b.a);atoms[b.b].bondOrder.push(b.order);}return atoms;
}
function clearPanels(host){for(const panel of [...panels])if(host.contains(panel.host)){panel.observer?.disconnect();panel.viewer?.clear();panel.viewer?.stopAnimate();panels.delete(panel);}}
function molecularPanel(id,role){
 const record=molecules.find(m=>m.id===id),panel=document.createElement('article');panel.className='component-panel';
 const title=document.createElement('div');title.className='component-title';
 const eyebrow=document.createElement('span'),name=document.createElement('h4'),formula=document.createElement('p');eyebrow.textContent=role;name.textContent=record?.name??id;formula.textContent=(record?.formula??'').replace(/\d/g,d=>'₀₁₂₃₄₅₆₇₈₉'[Number(d)]);title.append(eyebrow,name,formula);panel.append(title);
 const host=document.createElement('div');host.className='component-viewer';host.setAttribute('aria-label',(record?.name??id)+' molecular structure');panel.append(host);
 const foot=document.createElement('div');foot.className='component-foot';panel.append(foot);
 const badge=document.createElement('span');badge.textContent=!record?'Structure not available':record.representation==='formula-only'?'Connectivity schematic':record.representation==='2d'?'2D connectivity':record.id==='argon'?'Atomic reference':record.computedBy?'Computed illustrative 3D':'Reference 3D';foot.append(badge);
 const info={host,record,panel,viewer:null,observer:null};panels.add(info);
 if(!record){host.textContent='Chemical identity and amounts remain available in the table.';return panel;}
 if(record.representation==='formula-only'){
  host.classList.add('formula-connectivity');host.textContent=record.id==='dimethylcadmium'?'CH₃—Cd—CH₃':record.connectivityLabel??record.formula;
 }else if(record.representation==='2d'){
  const canvas=document.createElement('canvas');host.append(canvas);canvas.setAttribute('aria-label',record.name+' 2D molecular connectivity');
  info.draw=()=>draw2D(canvas,record);info.observer=new ResizeObserver(info.draw);info.observer.observe(host);requestAnimationFrame(info.draw);
 }else{
  try{
   if(!window.$3Dmol)throw Error('Viewer unavailable');
   info.viewer=$3Dmol.createViewer(host,{backgroundColor:'#f7faff',antialias:true});info.viewer.addModel().addAtoms(atomData(record));
   const reset=()=>{info.viewer.zoomTo();info.viewer.rotate(12,'y');info.viewer.rotate(-8,'z');info.viewer.zoom(.84);info.viewer.render();};
   info.reset=reset;styleMolecule(info);info.observer=registerViewer(host,info.viewer,reset);requestAnimationFrame(()=>{if(host.isConnected&&host.clientWidth){info.viewer.resize();reset();}});
   const button=document.createElement('button');button.type='button';button.textContent='Reset';button.addEventListener('click',reset);foot.append(button);
  }catch(error){host.classList.add('formula-connectivity');host.textContent=record.formula+' · 3D display unavailable';console.error(error);}
 }
 if(record.source){const source=document.createElement('a');source.href=record.source;source.target='_blank';source.rel='noopener noreferrer';source.textContent='Structure source ↗';foot.append(source);}
 return panel;
}
function styleMolecule(info){
 if(!info.viewer)return;
 const marked=new Set(info.record.functionalGroups?.flatMap(g=>g.atomIndices)??[]);
 const colorfunc=a=>highlight&&marked.has(a.index)?'#d46d98':colors[a.elem]??'#8090a3';
 info.viewer.setStyle({},{stick:{radius:.11,colorfunc},sphere:{scale:.28,colorfunc}});info.viewer.render();
}
function draw2D(canvas,record){
 const rect=canvas.parentElement.getBoundingClientRect();if(!rect.width||!rect.height)return;const dpr=devicePixelRatio||1;
 canvas.width=rect.width*dpr;canvas.height=rect.height*dpr;canvas.style.width=rect.width+'px';canvas.style.height=rect.height+'px';const ctx=canvas.getContext('2d');ctx.scale(dpr,dpr);
 const atoms=record.atoms,marked=new Set(record.functionalGroups?.flatMap(g=>g.atomIndices)??[]);
 const visible=new Set(atoms.map((a,i)=>a.element!=='H'?i:-1).filter(i=>i>=0));
 for(const b of record.bonds??[])if((atoms[b.a].element==='H'&&atoms[b.b].element!=='C')||(atoms[b.b].element==='H'&&atoms[b.a].element!=='C')){visible.add(b.a);visible.add(b.b);}
 const points=[...visible].map(i=>atoms[i]),xs=points.map(a=>a.x),ys=points.map(a=>a.y),dx=Math.max(...xs)-Math.min(...xs),dy=Math.max(...ys)-Math.min(...ys),cx=(Math.min(...xs)+Math.max(...xs))/2,cy=(Math.min(...ys)+Math.max(...ys))/2;
 const scale=Math.min((rect.width-65)/Math.max(dx,1),(rect.height-65)/Math.max(dy,1));const xy=a=>[(a.x-cx)*scale+rect.width/2,-(a.y-cy)*scale+rect.height/2];
 for(const b of record.bonds??[]){if(!visible.has(b.a)||!visible.has(b.b))continue;const a=xy(atoms[b.a]),z=xy(atoms[b.b]);ctx.strokeStyle=highlight&&marked.has(b.a)&&marked.has(b.b)?'#d46d98':'#708296';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(...a);ctx.lineTo(...z);ctx.stroke();}
 for(const i of visible){const a=atoms[i];if(a.element==='C')continue;const [x,y]=xy(a);ctx.fillStyle='#f7faff';ctx.fillRect(x-12,y-12,27,25);ctx.fillStyle=highlight&&marked.has(i)?'#b85682':colors[a.element]??'#304c67';ctx.font='600 17px Arial';ctx.textAlign='center';ctx.textBaseline='middle';const charge=a.formalCharge??a.charge??0;ctx.fillText(a.element+(charge>0?'+':charge<0?'−':''),x,y);}
}
function showStock(index){
 selectedStock=index;const stock=stocks[method][index];activeButtons('[data-stock]','stock',index);
 $('stock-title').textContent=stock.name;$('stock-amount').textContent=stock.amount;$('stock-concentration').textContent=stock.concentration;$('stock-note').textContent=stock.description;$('stock-source').textContent=stock.source;
 const host=$('stock-models');clearPanels(host);host.replaceChildren(molecularPanel(stock.solute,'Solute / precursor'),...(stock.secondSolute?[molecularPanel(stock.secondSolute,'Second precursor')]:[]),molecularPanel(stock.solvent,'Solvent / coordinating component'));
}
async function initializeMolecules(){
 if(!method)return;
 try{
  const response=await fetch('assets/cdse-molecular-structures.json');if(!response.ok)throw Error('Molecular data unavailable');molecules=await response.json();showStock(0);
  document.querySelectorAll('[data-stock]').forEach(b=>b.addEventListener('click',()=>showStock(Number(b.dataset.stock))));
  const dialog=$('compound-dialog'),content=$('compound-dialog-content');let trigger;
  document.querySelectorAll('[data-compound]').forEach(b=>b.addEventListener('click',()=>{trigger=b;clearPanels(content);content.replaceChildren(molecularPanel(b.dataset.compound,'Molecular structure'));$('compound-dialog-title').textContent=b.dataset.compound==='selenium'?'Selenium starting material':molecules.find(x=>x.id===b.dataset.compound)?.name??b.textContent;dialog.showModal();for(const p of panels)if(content.contains(p.host)){p.viewer?.resize();p.reset?.();p.draw?.();}}));
  $('compound-dialog-close').addEventListener('click',()=>dialog.close());dialog.addEventListener('close',()=>trigger?.focus());
  $('molecular-highlight').addEventListener('change',event=>{highlight=event.target.checked;for(const p of panels){styleMolecule(p);p.draw?.();}});
 }catch(error){$('stock-models').textContent=error.message+'. Formulae, quantities and references remain in the tables.';console.error(error);}
}
function initializeProtocols(){
 if(!method)return;
 const c=(label,value)=>({label,value});
 sceneRecords.method2=[
 {art:'silyl',title:'SILYL-SELENIUM PRECURSOR STORAGE',caption:'Storage is distinct from reaction conditions',conditions:[c('Precursor','(TMS)₂Se'),c('Storage temperature','−35 °C'),c('Environment','Drybox'),c('Duration / gas','Not reported')],path:['Cited preparation','Store precursor','Method 2']},
 {art:'route2',title:'CDSE METHOD 2 · ROUTE DEFINITION',caption:'Silyl precursor substitutes for the phosphine selenide',conditions:[c('Selenium precursor','(TMS)₂Se'),c('Cadmium source','Me₂Cd, by reference'),c('Numerical charges','Not separately reported'),c('General temperatures','Not separately reported')],path:['Me₂Cd + (TMS)₂Se','Coordinating medium','CdSe']},
 {art:'grow',title:'SMALLEST-SPECIES VARIANT',caption:'Reported low-temperature injection and growth',conditions:[c('Injection','≈100 °C'),c('Growth','≈100 °C'),c('Reported size','≈1.2 nm'),c('Time / pressure','Not reported')],path:['Inject','Grow at ≈100 °C','Small CdSe species'],hide:['.sample-monitor']}
 ];
 sceneRecords.exchange=[
 {art:'disperse',title:'PYRIDINE SURFACE EXCHANGE',caption:'Optional post-synthesis branch',conditions:[c('Capped crystallites','≈50 mg'),c('Pyridine','5–10 mL'),c('Temperature','≈60 °C'),c('Duration','Not reported')],path:['Capped CdSe','Disperse in pyridine','Ligand exchange'],labels:{'.solvent-tag':'Pyridine','.scene-vial>span':'Pyridine dispersion'}},
 {art:'flocculate',title:'HEXANE FLOCCULATION',caption:'Retain the crystallite flocculate',conditions:[c('Nonsolvent','Excess hexane'),c('Volume','Not reported'),c('Retain','Crystallite flocculate'),c('Speed / duration','Not reported')],path:['Add hexane','Centrifuge','Retain flocculate']},
 {art:'repeat',title:'REPEATED SURFACE EXCHANGE',caption:'Source reports a change in solvent dispersibility',conditions:[c('Disperse','Pyridine'),c('Flocculate','Hexane'),c('Cycle count','Not specified'),c('Endpoint','Changed dispersibility')],path:['Pyridine','Hexane','Repeat exchange'],labels:{'.stock-note':'Repeat dispersion and flocculation; observe dispersibility'}}
 ];
 let key=method==='method2'?'method2':'synthesis',index=0;
 function showStep(i){index=i;const step=protocols[key].steps[i];activeButtons('[data-step]','step',i);renderApparatus(key,i);$('step-kicker').textContent='STAGE '+(i+1)+' / '+protocols[key].steps.length;$('step-title').textContent=step.title;$('step-description').textContent=step.description;$('step-source').textContent=step.source+' ↗';$('step-fields').replaceChildren(...step.fields.map(([label,value])=>{const row=document.createElement('div');row.className='field';const dt=document.createElement('label'),dd=document.createElement('span');dt.textContent=label;dd.textContent=value;row.append(dt,dd);return row;}));$('next-step').textContent=i===protocols[key].steps.length-1?'Return to first stage ↺':'Next stage →';}
 function selectProtocol(value){key=value;activeButtons('[data-protocol]','protocol',key);$('protocol-note').textContent=protocols[key].note+(method==='method2'&&key==='purification'?' This is the common procedure, not an independently documented Method 2 yield.':'');const list=document.querySelector('.process-tabs');list.style.gridTemplateColumns='repeat('+protocols[key].steps.length+',1fr)';list.replaceChildren(...protocols[key].steps.map((step,i)=>{const b=document.createElement('button');b.type='button';b.dataset.step=i;b.textContent=(i+1)+' · '+step.tab;b.setAttribute('aria-pressed',String(i===0));b.addEventListener('click',()=>showStep(i));return b;}));showStep(0);}
 document.querySelectorAll('[data-protocol]').forEach(b=>b.addEventListener('click',()=>selectProtocol(b.dataset.protocol)));$('next-step').addEventListener('click',()=>showStep((index+1)%protocols[key].steps.length));selectProtocol(key);
 document.querySelectorAll('[data-feedback]').forEach(b=>b.addEventListener('click',()=>{const item=feedback[b.dataset.feedback];activeButtons('[data-feedback]','feedback',b.dataset.feedback);$('feedback-title').textContent=item.title;$('feedback-text').textContent=item.text;}));
}
async function initializeCrystals(){
 if(!$('crystal-viewer'))return;
 try{
  const results=await Promise.all(['assets/peng2000-crystal-reference.json','assets/cdse-structures/cdse-unit-cell-viewer.json'].map(async file=>{const r=await fetch(file);if(!r.ok)throw Error('Crystal data unavailable');return r.json();}));
  const [reference,cell]=results;if(!window.$3Dmol)throw Error('3D viewer unavailable');
  const cluster=$3Dmol.createViewer($('crystal-viewer'),{backgroundColor:'#f5f9fb',antialias:true}),unit=$3Dmol.createViewer($('unit-cell-viewer'),{backgroundColor:'#f5f9fb',antialias:true});
  cluster.addModel().addAtoms(buildCrystal(reference,{long:3.5,short:3.0,shape:'dot'}));
  const colorfunc=a=>colors[a.elem];let style='ball';
  const setStyle=()=>cluster.setStyle({},style==='space'?{sphere:{scale:.8,colorfunc}}:{sphere:{scale:.23,colorfunc},stick:{radius:.075,color:'#a8c1c7'}});
  const resetCluster=()=>{cluster.zoomTo();cluster.rotate(75,'y');cluster.rotate(-24,'z');cluster.zoom(.88);cluster.render();};setStyle();resetCluster();$('crystal-status').hidden=true;
  document.querySelectorAll('[data-style]').forEach(b=>b.addEventListener('click',()=>{style=b.dataset.style;activeButtons('[data-style]','style',style);setStyle();cluster.render();}));$('reset-crystal').addEventListener('click',resetCluster);registerViewer($('crystal-viewer'),cluster,resetCluster);
  const resetUnit=()=>{unit.zoomTo();unit.rotate(20,'x');unit.rotate(-25,'y');unit.zoom(.78);unit.render();};
  const drawCell=()=>{unit.removeAllModels();unit.removeAllShapes();const neighbors=$('unit-neighbors').checked;unit.addModel().addAtoms(structuredClone(neighbors?cell.atomsWithPeriodicNeighborContext:cell.atoms));unit.setStyle({},{sphere:{scale:.29,colorfunc},stick:{radius:.07,color:'#abc2ca'}});if(neighbors)unit.addStyle({index:cell.atomsWithPeriodicNeighborContext.filter(a=>a.isPeriodicImage).map(a=>a.index)},{sphere:{scale:.22,opacity:.38,colorfunc}});for(const edge of cell.unitCellEdges)unit.addLine({start:edge.start,end:edge.end,color:'#657b93',linewidth:2});resetUnit();};
  drawCell();$('unit-cell-status').hidden=true;$('unit-neighbors').addEventListener('change',drawCell);$('reset-unit-cell').addEventListener('click',resetUnit);registerViewer($('unit-cell-viewer'),unit,resetUnit);
 }catch(error){for(const id of ['crystal-status','unit-cell-status']){$(id).textContent=error.message+'. Structure files and source information remain available.';$(id).hidden=false;}console.error(error);}
}
initializeProtocols();initializeMolecules();initializeCrystals();if(document.querySelector('[data-gallery]'))initializeCharacterization();
