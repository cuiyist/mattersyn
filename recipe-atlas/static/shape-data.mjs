export const sourceUrl='https://doi.org/10.1038/35003535';
export const sampleRecords={
 dot4a:{name:'A quantum dot.',long:3.7,short:3.3,source:'FIGURE 4a · P. 60',method:'Dimension label in optical figure',shape:'dot'},
 rod4b:{name:'A quantum rod.',long:6.6,short:3.6,source:'FIGURE 4b · P. 60',method:'Dimension label in optical figure',shape:'rod'},
 rod2a:{name:'A shorter quantum rod.',long:5.6,short:4.2,source:'FIGURE 2a · P. 59',method:'XRD pattern simulation',shape:'rod'},
 rod2b:{name:'An elongated quantum rod.',long:9.1,short:4.5,source:'FIGURE 2b · P. 59',method:'XRD pattern simulation',shape:'rod'}
};
export const protocols={
 typical:{
 note:'The typical paragraph reports a family of conditions. It does not identify a complete recipe for every particle shown in the figures.',
 steps:[
 {tab:'Stock',title:'Begin with a shared precursor stock.',description:'The typical stock contains selenium, dimethylcadmium and tributylphosphine in the stated mass ratio. The detailed preparation sequence is not given.',fields:[['Se : Cd(CH₃)₂ : TBP','1 : 2 : 38 by weight'],['Stock aliquot','2 mL'],['Absolute component masses','Not reported'],['Preparation conditions','Not reported']]},
 {tab:'Hot medium',title:'Prepare the coordinating medium.',description:'The reported medium is 4 g of TOPO or TOPO plus HPA. HPA is varied in the shape-control experiments. The paper does not specify the separate component masses or a heating ramp.',fields:[['Medium charge','4 g TOPO or TOPO + HPA'],['HPA comparison','1.5%, 3%, 5%, 10%, 20% by weight'],['Injection temperatures','360, 310 or 280 °C'],['Ramp / preheating time','Not reported']]},
 {tab:'Inject',title:'Make a rapid injection.',description:'Inject 2 mL of stock into the hot reaction medium. The paper describes the addition as much less than one second. Keep the three reported thermal alternatives separate.',fields:[['Stock addition','2 mL'],['Addition time','≪ 1 s'],['Temperature before → after','360→300; 310→280; 280→250 °C'],['Thermal recovery trace','Not reported']]},
 {tab:'Grow & sample',title:'Follow growth with small aliquots.',description:'Withdraw aliquots to monitor UV–visible absorption and photoluminescence after injection. No numerical growth duration or sampling schedule is supplied.',fields:[['Monitoring','UV–visible + photoluminescence'],['Growth duration','Not reported'],['Aliquot volume / timing','Not reported'],['Shape history','Discussed qualitatively on pp. 60–61']]},
 {tab:'Reinject',title:'Replenish monomer when needed.',description:'The paper allows additional injections of the same stock to maintain or recover rod morphology. This is an optional branch, with no complete schedule for an individual sample.',fields:[['Operation','Optional secondary injection'],['Volume constraint','Less than 40% of volume injected previously'],['Injection count / schedule','Not reported'],['Purpose','Replenish monomer without new nuclei']]},
 {tab:'Stop',title:'Remove the heating mantle.',description:'Stop the reaction by removing the heating mantle. The article does not provide a purification or isolation procedure, so the recorded sequence ends here.',fields:[['Stopping operation','Remove heating mantle'],['Stop time / cooling rate','Not reported'],['Workup / purification','Not reported'],['Final storage','Not reported']]}
 ]},
 optimized:{
 note:'This is the separate condition set reported to give the best high-aspect-ratio results. Parameters absent from this sentence are not silently copied from the typical protocol.',
 steps:[
 {tab:'Stock',title:'Use the revised stock composition.',description:'The high-aspect-ratio variant changes both the cadmium and tributylphosphine proportions. It is not simply the typical recipe with a different HPA concentration.',fields:[['Se : Cd(CH₃)₂ : TBP','1 : 2.6 : 48 by weight'],['Stock aliquot','2 mL'],['Absolute component masses','Not reported'],['Preparation procedure','Not restated for this variant']]},
 {tab:'Surfactant',title:'Use the reported 8% HPA mixture.',description:'The best-results sentence specifies 8% HPA in TOPO. A weight basis is inferred from the immediately preceding HPA discussion; that sentence does not repeat the basis or total bath mass.',fields:[['Reaction medium','8% HPA in TOPO'],['Percent basis','Weight basis inferred from context'],['Total bath mass','Not restated for this variant'],['Separate HPA / TOPO masses','Not reported']]},
 {tab:'Inject',title:'Inject at 360 °C.',description:'The authors specify a 2 mL injection at 360 °C. The duration and post-injection temperature are not repeated in this high-aspect-ratio condition set.',fields:[['Stock addition','2 mL'],['Injection temperature','360 °C'],['Addition duration','Not restated for this variant'],['Post-injection temperature','Not restated for this variant']]},
 {tab:'Outcome',title:'A high-aspect-ratio result, without a full run record.',description:'The paper calls these the best conditions for high aspect ratios. It does not assign a numerical size, aspect ratio, reaction duration or figure panel to this specific sentence.',fields:[['Reported outcome','Best high-aspect-ratio results'],['Exact aspect ratio / size','Not assigned to this variant'],['Growth duration / injection count','Not reported'],['Figure-to-recipe mapping','Not provided']]}
 ]}
};
export const moleculeNotes={
 hpa:{head:'Phosphonic acid head group',text:'HPA was added deliberately to pure TOPO. The authors attribute control of growth to stronger coordination to cadmium. The highlighted neutral free-acid head is not a resolved surface-bound ligand.'},
 topo:{head:'Phosphine oxide head group',text:'TOPO is the coordinating reaction medium. The phosphorus–oxygen group is highlighted. This source record supplies a 2D connectivity depiction, not a 3D conformer.'},
 tbp:{head:'Phosphine coordination center',text:'Tributylphosphine is the stock-solution medium. The phosphorus and adjacent carbon atoms are highlighted. It is TBP, not trioctylphosphine (TOP).'},
 dimethylcadmium:{head:'Dimethylcadmium precursor',text:'The cadmium source is Cd(CH₃)₂. This schematic shows molecular connectivity only. No atomic geometry is inferred from PubChem’s disconnected standardized ionic record.'},
 selenium:{head:'An elemental reference, not the stock species',text:'Selenium powder enters the precursor stock. Its initial allotrope and the dissolved selenium species are not resolved in this paper. The display is a separate trigonal solid-selenium reference.'}
};
export function buildCrystal(reference,sample){
 const vectors=reference.latticeVectors, radius=sample.short*5,halfLength=sample.long*5,atoms=[];
 const nxy=Math.ceil(radius/(reference.a*.7))+2,nz=Math.ceil(halfLength/reference.c)+1;
 for(let i=-nxy;i<=nxy;i++)for(let j=-nxy;j<=nxy;j++)for(let k=-nz;k<=nz;k++)for(const b of reference.fractionalAtoms){
  const f=[i+b.x,j+b.y,k+b.z];
  const p=[0,1,2].map(d=>f.reduce((v,u,n)=>v+u*vectors[n][d],0));
  const [x,y,z]=p;
  const inside=sample.shape==='dot'?(x*x+y*y)/(radius*radius)+(z*z)/(halfLength*halfLength)<=1:
   Math.abs(z)<=halfLength&&Math.abs(x)<=radius&&Math.abs(y)<=Math.sqrt(3)*radius/2&&Math.sqrt(3)*Math.abs(x)+Math.abs(y)<=Math.sqrt(3)*radius;
  if(inside)atoms.push({elem:b.element,x,y,z,index:atoms.length,serial:atoms.length,bonds:[],bondOrder:[]});
 }
 // Spatial buckets keep the larger rod models responsive.
 const bins=new Map(),width=3;
 for(const a of atoms){
  const cell=[a.x,a.y,a.z].map(v=>Math.floor(v/width));
  for(let dx=-1;dx<=1;dx++)for(let dy=-1;dy<=1;dy++)for(let dz=-1;dz<=1;dz++){
   const key=[cell[0]+dx,cell[1]+dy,cell[2]+dz].join(',');
   for(const j of bins.get(key)||[]){const b=atoms[j];const distance=Math.hypot(a.x-b.x,a.y-b.y,a.z-b.z);if(a.elem!==b.elem&&distance>2.45&&distance<2.75){a.bonds.push(j);a.bondOrder.push(1);b.bonds.push(a.index);b.bondOrder.push(1);}}
  }
  const key=cell.join(',');if(!bins.has(key))bins.set(key,[]);bins.get(key).push(a.index);
 }
 return atoms;
}

