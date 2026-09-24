// Source-average coordinates only. This adapter never chooses an ordered microstate.
export const HEO_RECORDS = ['heo-2003-in66-route','heo-2003-single-crystal-acquisition','heo-2003-average-structure'];
export function averagePositions(model,extent=1,hidden=[]){
 if(![1,2].includes(extent))throw Error('Only unit-cell or 2 × 2 × 2 average views are supported.');
 const omit=new Set(hidden),out=[],a=model.cell.a;
 for(let i=0;i<extent;i++)for(let j=0;j<extent;j++)for(let k=0;k<extent;k++)for(const s of model.fractionalSites){
  if(omit.has(s.source_label))continue;
  out.push({site_id:s.id,source_label:s.source_label,cell:[i,j,k],x:s.cartesian[0]+i*a,y:s.cartesian[1]+j*a,z:s.cartesian[2]+k*a,components:s.components,occupancy_sum:s.occupancy_sum,mixed:s.mixed});
 }
 return out;
}
const node=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
export async function mountHeoAverage(host,record,options={}){
 if(record.lineage?.source_group!=='heo2003'||!HEO_RECORDS.includes(record.record_id))return false;
 const modelUrl=options.modelUrl??new URL('assets/crystal-references/heo2003-average-view.json',import.meta.url);
 const cifUrl=options.cifUrl??new URL('assets/crystal-references/heo2003-average-position-occupancy.cif',import.meta.url);
 const model=options.model??await fetch(modelUrl).then(r=>{if(!r.ok)throw Error('Average model unavailable');return r.json();});
 const card=node('article',undefined,'crystal-reference-card heo-average-card');
 card.append(node('h3','Average crystal structure'),node('p','Source-derived positions and occupancies · In66-X','guide-notice'),node('p','Fd-3m (No. 227), origin choice 2 · a = 24.942(4) Å · 294 K diffraction.'));
 card.append(node('p','Purple T markers represent Si 0.5 / Al 0.5. In(II) and In(IIa) markers show partial split positions, not simultaneous fully occupied atoms. No ordered Si/Al arrangement or local occupation pattern is selected.','guide-notice'));
 const view=node('div',undefined,'crystal-reference-view');view.style.minHeight='440px';view.style.position='relative';view.tabIndex=0;view.setAttribute('aria-label','Average occupancy model; drag to rotate and scroll to zoom');
 const controls=node('div',undefined,'protocol-controls'),layers=node('fieldset'),legend=node('legend','Display source site groups'),summary=node('p',undefined,'guide-notice');layers.append(legend);
 const siteTable=node('table'),head=node('tr');for(const s of ['Source site','Positions / cell','Occupancy components'])head.append(node('th',s));siteTable.append(head);
 for(const g of model.groups){const tr=node('tr');tr.append(node('td',g.label),node('td',String(g.positions_per_cell)),node('td',g.components.map(c=>c.element+' '+c.occupancy).join(' / ')));siteTable.append(tr);}
 const info=node('details'),infoTitle=node('summary','Occupancies, limitations and source');info.append(infoTitle,siteTable);
 for(const s of model.limitations)info.append(node('p',s));
 const links=node('div',undefined,'protocol-controls');for(const [label,url] of [['Download average position/occupancy CIF',cifUrl],['Download average model JSON',modelUrl],['Source paper','https://doi.org/10.1021/jp0219348']]){const a=node('a',label);a.href=url;if(!String(url).startsWith('https:'))a.download='';links.append(a);}
 card.append(controls,view,summary,layers,node('p','The weighted average formula Si96Al96O384In66 differs from the nominal In66Si100Al92O384. ADPs are omitted. The 107.1602° coordinate-derived versus 111.7(20)° reported angle discrepancy remains unresolved.'),node('p','No finite particle, surface ligands, unique ordered structure, exact structure–recipe label or DFT input is provided.','guide-notice'),info,links);host.append(card);
 if(!globalThis.$3Dmol){view.append(node('p','The 3D renderer is unavailable. The exact average model, occupancy table, limitations and downloads remain accessible.'));info.open=true;return true;}
 const viewer=globalThis.$3Dmol.createViewer(view,{backgroundColor:'#f5f9fc'});let extent=1,hidden=new Set();
 const componentText=s=>s.components.map(c=>c.element+' '+c.occupancy).join(' / ');
 const draw=()=>{
  viewer.clear();const positions=averagePositions(model,extent,[...hidden]);
  const atoms=positions.map((p,i)=>({serial:i,elem:p.mixed?'X':p.components[0].element,x:p.x,y:p.y,z:p.z,properties:{site_id:p.site_id,source_label:p.source_label},clickable:true,callback:()=>{viewer.removeAllLabels();viewer.addLabel(p.source_label+' · '+componentText(p),{position:{x:p.x,y:p.y,z:p.z},backgroundColor:'#ffffff',fontColor:'#173b4d',fontSize:13});viewer.render();}}));
  viewer.addModel().addAtoms(atoms);
  for(const g of model.groups){const ids=positions.flatMap((p,i)=>p.source_label===g.label?[i]:[]);const radius=g.label.startsWith('O')?.16:g.label==='(Si,Al)'?.23:.31;viewer.setStyle({index:ids},{sphere:{radius,color:model.colors[g.label],opacity:g.occupancy_sum<1?.60:1}});}
  const n=extent*model.cell.a;for(let axis=0;axis<3;axis++)for(const b of [0,n])for(const c of [0,n]){const a=[b,c];a.splice(axis,0,0);const z=[...a];z[axis]=n;viewer.addLine({start:{x:a[0],y:a[1],z:a[2]},end:{x:z[0],y:z[1],z:z[2]},color:'#849caa',linewidth:1});}
  viewer.zoomTo();viewer.rotate(15,'y');viewer.rotate(-12,'x');viewer.render();summary.textContent=`${extent===1?'One conventional unit cell':'2 × 2 × 2 repetition of the same average model'} · ${positions.length.toLocaleString()} visible position markers. One full cell has 680 distinct positions, 872 species components and 642 occupancy-weighted atoms. Display-layer changes do not select a physical arrangement. Click a marker for its source site and occupancy.`;
 };
 for(const [label,n] of [['Unit cell',1],['2 × 2 × 2 average lattice',2]]){const b=node('button',label);b.type='button';b.onclick=()=>{extent=n;draw();};controls.append(b);}
 for(const [label,action] of [['−',()=>viewer.zoom(1/1.2)],['Reset view',()=>draw()],['+',()=>viewer.zoom(1.2)]]){const b=node('button',label);b.type='button';b.onclick=()=>{action();viewer.render();};controls.append(b);}
 for(const g of model.groups){const label=node('label'),box=node('input');box.type='checkbox';box.checked=true;box.setAttribute('aria-label','Display '+g.label+' average positions');label.append(box,document.createTextNode(g.label+' · '+g.components.map(c=>c.element+' '+c.occupancy).join(' / ')));label.style.borderLeft='4px solid '+model.colors[g.label];box.onchange=()=>{box.checked?hidden.delete(g.label):hidden.add(g.label);draw();};layers.append(label);}
 view.onkeydown=e=>{const turn={ArrowLeft:[-12,'y'],ArrowRight:[12,'y'],ArrowUp:[-12,'x'],ArrowDown:[12,'x']}[e.key];if(turn)viewer.rotate(...turn);else if(e.key==='Home')draw();else if(['+','='].includes(e.key))viewer.zoom(1.15);else if(e.key==='-')viewer.zoom(1/1.15);else return;e.preventDefault();viewer.render();};
 const resize=new ResizeObserver(()=>{if(view.isConnected){viewer.resize();viewer.render();}else{viewer.clear();resize.disconnect();}});resize.observe(view);draw();return true;
}
