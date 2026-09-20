// Display-only source-table reconstruction. No canonical or training fields are changed.
export const BULK_BINDINGS = Object.freeze([
 {record_id:'lian-2021-bulk-a-route',sample_id:'bulk-a',phase:'A',formula:'(C12H28N)2SbCl5',crystal_phase:'triclinic P-1'},
 {record_id:'lian-2021-bulk-b-route',sample_id:'bulk-b',phase:'B',formula:'(C12H28N)SbCl4',crystal_phase:'monoclinic P21/c'},
 {record_id:'lian-2021-bulk-characterization',sample_id:'bulk-a-crystal',phase:'A',formula:'(C12H28N)2SbCl5',crystal_phase:'triclinic P-1'},
 {record_id:'lian-2021-bulk-characterization',sample_id:'bulk-b-crystal',phase:'B',formula:'(C12H28N)SbCl4',crystal_phase:'monoclinic P21/c'}
]);
export function eligibleBulkContexts(record){
 if(record?.lineage?.source_group!=='lian2021')return [];
 return BULK_BINDINGS.filter(b=>record.record_id===b.record_id && record.products?.some(p=>p.sample_id===b.sample_id && p.composition?.value===b.formula && p.phase?.value===b.crystal_phase));
}
export function displayGeometry(model,expanded=false){
 if(model?.schema!=='mattersyn.source_non_h_bulk_view.v1'||!['A','B'].includes(model.phase)||model.source_id!=='lian2021')throw Error('Unqualified bulk model');
 const sites=expanded?model.geometric_cell_positions:model.asymmetric_unit_sites;
 if(sites.some(s=>s.occupancy!==null))throw Error('Unexpected occupancy assignment');
 // No inferred connectivity. Expanded positions are shown unbonded to avoid artificial cross-cell bonds.
 return {sites,bonds:expanded?[]:model.source_bonds.map(b=>({a:b.sites[0],b:b.sites[1]}))};
}
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
const COLORS={Sb:'#ad539b',Cl:'#379765',N:'#356ac7',C:'#526475'};
const RADII={Sb:.36,Cl:.26,N:.20,C:.18};
export async function mountLianBulk(host,record,options={}){
 const bindings=eligibleBulkContexts(record);if(!bindings.length)return false;
 for(const b of bindings){
  const stem='lian2021-bulk-'+b.phase.toLowerCase()+'-non-h';
  const modelUrl=options.modelUrls?.[b.phase]??new URL('assets/crystal-references/'+stem+'.json',import.meta.url);
  const cifUrl=options.cifUrls?.[b.phase]??new URL('assets/crystal-references/'+stem+'-partial.cif',import.meta.url);
  const model=options.models?.[b.phase]??await fetch(modelUrl).then(r=>{if(!r.ok)throw Error('Bulk table model unavailable');return r.json();});
  if(model.phase!==b.phase||model.id!=='lian2021-bulk-'+b.phase.toLowerCase())throw Error('Bulk phase/model mismatch');
  displayGeometry(model);
  const card=el('article',undefined,'lian-bulk-card');card.dataset.sampleId=b.sample_id;
  card.append(el('p','BULK '+b.phase+' · SOURCE TABLE RECONSTRUCTION','lian-bulk-eyebrow'),el('h3','Non-hydrogen crystal coordinates'),el('p',`${b.formula} · ${model.space_group.hm} · source context ${b.sample_id}`,'lian-bulk-subtitle'));
  card.append(el('p','The structure was refined for the corresponding bulk compound. This link does not establish that the diffraction crystal was the same physical aliquot as this synthesis or any other characterization specimen.','lian-bulk-note'));
  const cell=model.cell;card.append(el('p',`a ${cell.a} Å · b ${cell.b} Å · c ${cell.c} Å · α ${cell.alpha}° · β ${cell.beta}° · γ ${cell.gamma}°`,'lian-bulk-cell'));
  const controls=el('div',undefined,'lian-bulk-controls'),mode=el('select');mode.setAttribute('aria-label','Bulk '+b.phase+' coordinate scope');
  for(const [value,label] of [['asu','Listed asymmetric unit'],['cell','Geometric symmetry expansion']]){const opt=el('option',label);opt.value=value;mode.append(opt);}
  controls.append(mode);
  const view=el('div',undefined,'lian-bulk-view');view.tabIndex=0;view.setAttribute('aria-label','Bulk '+b.phase+' non-hydrogen coordinates; drag to rotate, scroll to zoom, arrow keys to rotate');
  const status=el('p',undefined,'lian-bulk-status');
  const legend=el('p','Sb  antimony · Cl  chlorine · N  nitrogen · C  carbon. Constant-size markers; no hydrogen sites or thermal ellipsoids.','lian-bulk-legend');
  card.append(controls,view,status,legend,el('p','Occupancies were not supplied. All occupancies remain unknown; marker counts describe geometric positions, not a complete occupied crystal.','lian-bulk-warning'));
  const detail=el('details'),summary=el('summary','Source values, reconstruction and limits');detail.append(summary);
  for(const p of model.limitations)detail.append(el('p',p));
  detail.append(el('p',`Source: Tables S1, S${b.phase==='A'?'6 and S8':'7 and S9'}; bonds/angles from Tables S${b.phase==='A'?'2 and S4':'3 and S5'}. Space-group operations: ${model.space_group.operations.join('; ')}. Original values and uncertainties are retained in the JSON and partial CIF.`));
  const links=el('div',undefined,'lian-bulk-controls');
  for(const [label,url] of [['Download qualified non-H JSON',modelUrl],['Download partial-table CIF',cifUrl],['Source article','https://doi.org/10.1021/acsami.1c18038']]){const a=el('a',label);a.href=url;if(!String(url).startsWith('https:'))a.download='';links.append(a);}
  card.append(detail,links);host.append(card);
  if(!globalThis.$3Dmol){view.append(el('p','The 3D renderer is unavailable. Source values, limitations and downloads remain available.'));status.textContent='No interactive geometry was rendered.';detail.open=true;continue;}
  const viewer=globalThis.$3Dmol.createViewer(view,{backgroundColor:'#f4f7fa'}),initialView=viewer.getView();let expanded=false;
  const xyz=v=>({x:v[0],y:v[1],z:v[2]});
  const draw=()=>{
   viewer.clear();const g=displayGeometry(model,expanded),map=new Map(g.sites.map((s,i)=>[s.id,i]));
   const atoms=g.sites.map((s,i)=>({serial:i,elem:s.element,...xyz(s.cartesian),bonds:[],bondOrder:[],clickable:true,callback:()=>{viewer.removeAllLabels();viewer.addLabel(`${s.id} · occupancy unknown`,{position:xyz(s.cartesian),fontSize:13,backgroundColor:'#ffffff',fontColor:'#1a3040'});viewer.render();}}));
   // Explicit source-table bonds only; disable all distance-based bond guessing.
   for(const bond of g.bonds){const i=map.get(bond.a),j=map.get(bond.b);atoms[i].bonds.push(j);atoms[i].bondOrder.push(1);atoms[j].bonds.push(i);atoms[j].bondOrder.push(1);}
   viewer.addModel().addAtoms(atoms);
   for(const elem of Object.keys(COLORS))viewer.setStyle({elem},{sphere:{radius:RADII[elem],color:COLORS[elem]},...(expanded?{}:{stick:{radius:.045,color:COLORS[elem]}})});
   const matrix=model.cell_cartesian_matrix,cart=f=>matrix.map(row=>row.reduce((s,v,i)=>s+v*f[i],0));
   for(let axis=0;axis<3;axis++)for(const p of [0,1])for(const q of [0,1]){const a=[p,q];a.splice(axis,0,0);const z=[...a];z[axis]=1;viewer.addLine({start:xyz(cart(a)),end:xyz(cart(z)),color:'#8897a5',linewidth:1});}
   viewer.setView(initialView);viewer.zoomTo();viewer.zoom(expanded?.95:(view.clientWidth<400?1.0:1.45));viewer.rotate(-12,'x');viewer.rotate(20,'y');viewer.render();
   status.textContent=expanded?`${g.sites.length} geometric positions generated by ${model.space_group.operations.length} space-group operations and wrapped into one cell. No inferred bonds are drawn. Occupancies remain unknown.`:`${g.sites.length} listed non-H sites in their original fractional positions; some extend beyond the outlined cell. ${g.bonds.length} source-reported links are shown; line style does not assign bond order. Drag to rotate, scroll to zoom.`;
  };
  mode.onchange=()=>{expanded=mode.value==='cell';draw();};
  for(const [text,action] of [['−',()=>viewer.zoom(1/1.2)],['Reset',draw],['+',()=>viewer.zoom(1.2)]]){const button=el('button',text);button.type='button';button.setAttribute('aria-label',text==='−'?'Zoom out bulk '+b.phase:text==='+'?'Zoom in bulk '+b.phase:'Reset bulk '+b.phase);button.onclick=()=>{action();viewer.render();};controls.append(button);}
  view.onkeydown=e=>{const t={ArrowLeft:[-12,'y'],ArrowRight:[12,'y'],ArrowUp:[-12,'x'],ArrowDown:[12,'x']}[e.key];if(t)viewer.rotate(...t);else if(e.key==='Home')draw();else if(['+','='].includes(e.key))viewer.zoom(1.15);else if(e.key==='-')viewer.zoom(1/1.15);else return;e.preventDefault();viewer.render();};
  const resize=new ResizeObserver(()=>{if(view.isConnected){viewer.resize();viewer.render();}else{viewer.clear();resize.disconnect();}});resize.observe(view);draw();
 }
 return true;
}
