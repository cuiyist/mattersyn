import {initializeCharacterization} from './characterization.mjs';
import {renderApparatus} from './apparatus-scenes.mjs';
import {protocols,sampleRecords,moleculeNotes,feedback} from './murray-data.mjs';
import {buildCrystal} from './shape-data.mjs';
const $=id=>document.getElementById(id);
let protocolKey='synthesis',stepIndex=0,selectedMolecule='topo',sampleKey='tem6',representation='ball';
let moleculeViewer,crystalViewer,molecules=[],reference,selenium;
let planar={zoom:1,x:0,y:0,data:null};
const colors={C:'#728399',H:'#d9e1ea',O:'#df6279',P:'#e6a541',Cd:'#159eab',Se:'#e3ad51'};
function markButtons(selector,attribute,value){document.querySelectorAll(selector).forEach(button=>{const active=button.dataset[attribute]===value;button.classList.toggle('active',active);button.setAttribute(button.getAttribute('role')==='tab'?'aria-selected':'aria-pressed',String(active));});}
function showStep(index){
 stepIndex=index;const steps=protocols[protocolKey].steps,step=steps[index];
 markButtons('[data-step]','step',String(index));
 $('step-kicker').textContent='STAGE '+String(index+1).padStart(2,'0')+' / '+String(steps.length).padStart(2,'0');
 $('step-source').textContent=step.source+' ↗';
 renderApparatus(protocolKey,index);
 $('step-title').textContent=step.title;$('step-description').textContent=step.description;
 $('step-fields').replaceChildren(...step.fields.map(([label,value])=>{const div=document.createElement('div');div.className='field'+(/Not |inferred/.test(value)?' missing':'');const dt=document.createElement('label'),dd=document.createElement('span');dt.textContent=label;dd.textContent=value;div.append(dt,dd);return div;}));
 $('next-step').textContent=index===steps.length-1?'Start again ↺':'Next stage →';
}
function showProtocol(key){
 protocolKey=key;markButtons('[data-protocol]','protocol',key);$('protocol-note').textContent=protocols[key].note;
 const tabs=document.querySelector('.process-tabs');tabs.style.gridTemplateColumns='repeat('+protocols[key].steps.length+',1fr)';
 tabs.replaceChildren(...protocols[key].steps.map((step,index)=>{const button=document.createElement('button');button.type='button';button.setAttribute('role','tab');button.dataset.step=String(index);button.innerHTML='<span>'+String(index+1).padStart(2,'0')+'</span>'+step.tab;button.addEventListener('click',()=>showStep(index));return button;}));showStep(0);
}
document.querySelectorAll('[data-protocol]').forEach(b=>b.addEventListener('click',()=>showProtocol(b.dataset.protocol)));
$('next-step').addEventListener('click',()=>showStep((stepIndex+1)%protocols[protocolKey].steps.length));showProtocol('synthesis');
document.querySelectorAll('[data-feedback]').forEach(b=>b.addEventListener('click',()=>{const item=feedback[b.dataset.feedback];markButtons('[data-feedback]','feedback',b.dataset.feedback);$('feedback-title').textContent=item.title;$('feedback-text').textContent=item.text;}));
function atomData(data){const atoms=data.atoms.map((a,i)=>({index:i,serial:i,elem:a.element,x:a.x,y:a.y,z:a.z,bonds:[],bondOrder:[]}));data.bonds.forEach(b=>{atoms[b.a].bonds.push(b.b);atoms[b.a].bondOrder.push(b.order);atoms[b.b].bonds.push(b.a);atoms[b.b].bondOrder.push(b.order)});return atoms;}
const planarCanvas=document.createElement('canvas');planarCanvas.id='planar-viewer';planarCanvas.className='viewer';planarCanvas.hidden=true;planarCanvas.setAttribute('aria-label','Molecular connectivity diagram');planarCanvas.tabIndex=0;$('molecule-viewer').after(planarCanvas);
function drawPlanar(){
 if(!planar.data||planarCanvas.hidden)return;
 const rect=planarCanvas.getBoundingClientRect();if(!rect.width||!rect.height)return;
 const dpr=window.devicePixelRatio||1;planarCanvas.width=Math.round(rect.width*dpr);planarCanvas.height=Math.round(rect.height*dpr);
 const ctx=planarCanvas.getContext('2d');ctx.scale(dpr,dpr);ctx.clearRect(0,0,rect.width,rect.height);
 const data=planar.data,heavy=data.atoms.filter(a=>a.element!=='H'),selected=new Set(data.functionalGroups[0].atomIndices);
 const xs=heavy.map(a=>a.x),ys=heavy.map(a=>a.y),cx=(Math.min(...xs)+Math.max(...xs))/2,cy=(Math.min(...ys)+Math.max(...ys))/2;
 const scale=Math.min((rect.width-55)/(Math.max(...xs)-Math.min(...xs)),(rect.height-45)/(Math.max(...ys)-Math.min(...ys)))*planar.zoom;
 const xy=a=>[(a.x-cx)*scale+rect.width/2+planar.x,-(a.y-cy)*scale+rect.height/2+planar.y];
 ctx.lineCap='round';
 for(const bond of data.bonds){const a=data.atoms[bond.a],b=data.atoms[bond.b];if(a.element==='H'||b.element==='H')continue;const [x1,y1]=xy(a),[x2,y2]=xy(b);const highlighted=$('highlight').checked&&selected.has(a.index)&&selected.has(b.index);ctx.strokeStyle=highlighted?'#e57191':'#697f95';ctx.lineWidth=2.2;const length=Math.hypot(x2-x1,y2-y1),nx=-(y2-y1)/length*2,ny=(x2-x1)/length*2;
  for(const sign of bond.order===2?[-1,1]:[0]){ctx.beginPath();ctx.moveTo(x1+nx*sign,y1+ny*sign);ctx.lineTo(x2+nx*sign,y2+ny*sign);ctx.stroke();}
 }
 for(const a of heavy){if(a.element==='C')continue;const [x,y]=xy(a);ctx.fillStyle='#f8faff';ctx.beginPath();ctx.arc(x,y,12,0,Math.PI*2);ctx.fill();ctx.fillStyle=$('highlight').checked&&selected.has(a.index)?'#d95f83':colors[a.element];ctx.font='600 18px Arial';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(a.element,x,y);}
}
planarCanvas.addEventListener('wheel',event=>{event.preventDefault();planar.zoom=Math.max(.45,Math.min(3,planar.zoom*Math.exp(-event.deltaY*.001)));drawPlanar();},{passive:false});
let pointer=null;
planarCanvas.addEventListener('pointerdown',event=>{pointer={id:event.pointerId,x:event.clientX,y:event.clientY};planarCanvas.setPointerCapture(event.pointerId);});
planarCanvas.addEventListener('pointermove',event=>{if(!pointer||pointer.id!==event.pointerId)return;planar.x+=event.clientX-pointer.x;planar.y+=event.clientY-pointer.y;pointer.x=event.clientX;pointer.y=event.clientY;drawPlanar();});
planarCanvas.addEventListener('pointerup',()=>{pointer=null});planarCanvas.addEventListener('pointercancel',()=>{pointer=null});
planarCanvas.addEventListener('keydown',event=>{if(event.key==='Home'){planar.zoom=1;planar.x=planar.y=0;}else if(event.key==='+'||event.key==='=')planar.zoom=Math.min(3,planar.zoom*1.1);else if(event.key==='-')planar.zoom=Math.max(.45,planar.zoom/1.1);else return;event.preventDefault();drawPlanar();});
function showMolecule(key){
 selectedMolecule=key;const meta=moleculeNotes[key],data=molecules.find(d=>d.id===key),solid=key==='selenium';if(!meta||(!solid&&!data))return;
 const formula=data?.representation==='formula-only',flat=data?.representation==='2d';
 markButtons('[data-molecule]','molecule',key);$('more-reagents').value=['top','topo','topse'].includes(key)?'':key;
 $('molecule-name').textContent=solid?'Selenium · Se':data.name;$('group-name').textContent=meta.head;$('group-description').textContent=meta.text;
 $('molecule-viewer').hidden=formula||flat;planarCanvas.hidden=!flat;$('formula-model').hidden=!formula;
 document.querySelector('.toggle-label').hidden=solid||formula;$('reset-molecule').hidden=formula;
 $('molecule-badge').textContent=formula?'CONNECTIVITY SCHEMATIC':flat?'PUBCHEM 2D':solid?'SOLID REFERENCE':data.computedBy?'COMPUTED 3D MODEL':'PUBCHEM 3D';
 $('molecule-hint').textContent=formula?'Molecular connectivity only':flat?'Drag to pan · Scroll to zoom':'Drag to rotate · Scroll to zoom';
 const names={C:'Carbon',H:'Hydrogen',P:'Phosphorus',O:'Oxygen',Se:'Selenium'};const legend=solid?[['Se','Selenium']]:formula?[]:[...new Set(data.atoms.map(a=>a.element))].map(e=>[e,names[e]||e]);
 $('molecule-legend').innerHTML=legend.map(([element,label])=>'<span><i style="background:'+colors[element]+'"></i>'+label+'</span>').join('')+(!solid&&!formula?'<span><i style="background:#e57191"></i>Highlighted group</span>':'');
 $('molecule-status').classList.add('hidden');
 if(formula)return;
 if(flat){planarCanvas.setAttribute('aria-label','2D connectivity diagram of '+data.name);planar={zoom:1,x:0,y:0,data};drawPlanar();return;}
 if(!moleculeViewer){$('molecule-status').textContent='3D display is unavailable in this browser. Chemical facts remain available.';$('molecule-status').classList.remove('hidden');return;}
 const modelData=solid?selenium.displayModel:data;
 moleculeViewer.resize();moleculeViewer.removeAllModels();moleculeViewer.addModel().addAtoms(atomData(modelData));
 const highlight=!solid&&$('highlight').checked,marked=new Set(solid?[]:data.functionalGroups[0].atomIndices);
 const colorfunc=a=>highlight&&marked.has(a.index)?'#e57191':colors[a.elem]||'#71849b';
 moleculeViewer.setStyle({}, {stick:{radius:.105,colorfunc},sphere:{scale:.28,colorfunc}});
 if(highlight)moleculeViewer.addStyle({index:[...marked]},{sphere:{scale:.34,color:'#e57191'}});
 moleculeViewer.zoomTo();moleculeViewer.rotate(15,'y');moleculeViewer.rotate(-12,'z');moleculeViewer.zoom(.88);moleculeViewer.render();
}
document.querySelectorAll('[data-molecule]').forEach(button=>button.addEventListener('click',()=>showMolecule(button.dataset.molecule)));
$('more-reagents').addEventListener('change',e=>{if(e.target.value)showMolecule(e.target.value)});
$('highlight').addEventListener('change',()=>{if(!planarCanvas.hidden)drawPlanar();else showMolecule(selectedMolecule)});
$('reset-molecule').addEventListener('click',()=>showMolecule(selectedMolecule));
function crystalStyle(style){representation=style;markButtons('[data-style]','style',style);if(!crystalViewer)return;const colorfunc=a=>colors[a.elem];crystalViewer.setStyle({},style==='space'?{sphere:{scale:.8,colorfunc}}:{sphere:{scale:.23,colorfunc},stick:{radius:.075,color:'#a8c1c7'}});crystalViewer.render();}
function resetCrystal(){if(!crystalViewer)return;crystalViewer.zoomTo();crystalViewer.rotate(75,'y');crystalViewer.rotate(-24,'z');crystalViewer.zoom(.88);crystalViewer.render();}
const crystalCache=new Map();
function showSample(key){
 sampleKey=key;const sample=sampleRecords[key];markButtons('[data-sample]','sample',key);
 $('sample-source').textContent=sample.source;$('sample-name').textContent=sample.name;$('sample-dimensions').textContent=sample.long+' × '+sample.short+' nm';
 $('sample-ratio').innerHTML=(sample.long/sample.short).toFixed(2)+'<small>calculated from reported dimensions</small>';$('sample-method').textContent=sample.method;
 if(!crystalViewer)return;
 if(!crystalCache.has(key))crystalCache.set(key,buildCrystal(reference,sample));
 crystalViewer.removeAllModels();crystalViewer.addModel().addAtoms(crystalCache.get(key));crystalStyle(representation);resetCrystal();$('crystal-status').classList.add('hidden');
}
document.querySelectorAll('[data-sample]').forEach(b=>b.addEventListener('click',()=>showSample(b.dataset.sample)));
document.querySelectorAll('[data-style]').forEach(b=>b.addEventListener('click',()=>crystalStyle(b.dataset.style)));
$('reset-crystal').addEventListener('click',resetCrystal);
document.querySelectorAll('[role="tablist"]').forEach(list=>list.addEventListener('keydown',event=>{
 if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
 const tabs=[...list.querySelectorAll('[role="tab"]')],index=tabs.indexOf(document.activeElement);if(index<0)return;
 event.preventDefault();const next=event.key==='Home'?0:event.key==='End'?tabs.length-1:(index+(event.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;tabs[next].focus();tabs[next].click();
}));
for(const [id,getViewer] of [['molecule-viewer',()=>moleculeViewer],['crystal-viewer',()=>crystalViewer]]){
 $(id).tabIndex=0;$(id).addEventListener('keydown',event=>{const viewer=getViewer();if(!viewer)return;
 const rotation={ArrowLeft:[-12,'y'],ArrowRight:[12,'y'],ArrowUp:[-12,'x'],ArrowDown:[12,'x']}[event.key];
 if(rotation)viewer.rotate(...rotation);else if(['+','='].includes(event.key))viewer.zoom(1.1);else if(event.key==='-')viewer.zoom(1/1.1);else if(event.key==='Home'){if(id==='crystal-viewer')resetCrystal();else showMolecule(selectedMolecule);}else return;
 event.preventDefault();viewer.render();
 });
}
async function initialize(){
 try{
  const results=await Promise.all(['murray1993-molecular-structures.json','peng2000-crystal-reference.json','selenium-reference.json'].map(async name=>{const r=await fetch('assets/'+name);if(!r.ok)throw Error('Structure data could not be loaded.');return r.json();}));
  [molecules,reference,selenium]=results;
  $('source-links').innerHTML=molecules.map(d=>'<a href="'+d.source+'" target="_blank" rel="noopener noreferrer">'+d.name+' ↗</a>').join('')+'<a href="'+reference.source.url+'" target="_blank" rel="noopener noreferrer">CdSe wurtzite reference ↗</a><a href="https://www.crystallography.net/cod/9012501.html" target="_blank" rel="noopener noreferrer">Selenium reference ↗</a>';
  try{if(!window.$3Dmol)throw Error('3D viewer library unavailable');moleculeViewer=$3Dmol.createViewer($('molecule-viewer'),{backgroundColor:'#f8faff',antialias:true});crystalViewer=$3Dmol.createViewer($('crystal-viewer'),{backgroundColor:'#f5f9fb',antialias:true});}catch(error){console.error(error);$('crystal-status').textContent='3D display is unavailable. Reported sample dimensions remain available.';}
  showMolecule('topo');showSample('tem6');
  const resize=new ResizeObserver(()=>{if(moleculeViewer&&!$('molecule-viewer').hidden){moleculeViewer.resize();moleculeViewer.render();}if(crystalViewer){crystalViewer.resize();crystalViewer.render();}drawPlanar();});
  resize.observe(document.querySelector('.molecule-stage'));resize.observe(document.querySelector('.crystal-stage'));
 }catch(error){document.querySelectorAll('.viewer-status').forEach(e=>{e.textContent=error.message+' Source details remain available.';e.classList.remove('hidden')});console.error(error);}
}
initialize();


initializeCharacterization();
