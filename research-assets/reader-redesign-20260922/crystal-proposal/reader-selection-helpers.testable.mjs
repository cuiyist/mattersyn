export function scopeKind(ref){
 const kind=[ref.sourceType,ref.referenceType,ref.name,ref.description].filter(Boolean).join(' ');
 if(/comput|DFT|PBE/i.test(kind))return 'Computed reference';
 if(/construct|ideal_reference|ideal reference/i.test(kind))return 'Constructed reference';
 return 'Bulk reference';
}
export function referenceCellVectors(model){
 const supplied=model.cellVectors??model.latticeVectors;
 let v=supplied;
 if(!v){
  const c=model.cell??model,{a,b,c:cc,alpha,beta,gamma}=c;
  if(![a,b,cc,alpha,beta,gamma].every(Number.isFinite))throw Error('Reference cell metadata is incomplete');
  const rad=Math.PI/180,ca=Math.cos(alpha*rad),cb=Math.cos(beta*rad),cg=Math.cos(gamma*rad),sg=Math.sin(gamma*rad);
  if(Math.abs(sg)<1e-8)throw Error('Reference cell has a singular angle');
  const cy=(ca-cb*cg)/sg,cz2=1-cb*cb-cy*cy;
  if(cz2<=0)throw Error('Reference cell angles are invalid');
  v=[[a,0,0],[b*cg,b*sg,0],[cc*cb,cc*cy,cc*Math.sqrt(cz2)]];
 }
 if(!Array.isArray(v)||v.length!==3||v.some(row=>!Array.isArray(row)||row.length!==3||!row.every(Number.isFinite)))throw Error('Reference cell vectors are invalid');
 const det=v[0][0]*(v[1][1]*v[2][2]-v[1][2]*v[2][1])-v[0][1]*(v[1][0]*v[2][2]-v[1][2]*v[2][0])+v[0][2]*(v[1][0]*v[2][1]-v[1][1]*v[2][0]);
 if(det<=1e-8)throw Error('Reference cell has non-positive volume');
 return v;
}
// Existing sample_context_ids sometimes describe evidence context rather than
// eligibility. Only an explicit sample_context_choice policy imposes this gate.
export function referencesForSample(entries,sampleId){
 return entries.filter(ref=>ref.displayPolicy!=='sample_context_choice'||(ref.sample_context_ids||[]).includes(sampleId));
}
export function referenceSampleChoices(entries,r){
 if(!entries.some(ref=>ref.displayPolicy==='sample_context_choice'))return [];
 const scopedIds=new Set(entries.filter(ref=>ref.displayPolicy==='sample_context_choice').flatMap(ref=>ref.sample_context_ids||[]));
 const seen=new Set();
 return (r.products||[]).filter(p=>p.sample_id&&(p.phase?.value||scopedIds.has(p.sample_id))).filter(p=>{if(seen.has(p.sample_id))return false;seen.add(p.sample_id);return true;});
}
