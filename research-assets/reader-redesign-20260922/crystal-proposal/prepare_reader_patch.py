"""Read the site's current reader; write only an isolated proposed file + diff."""
from pathlib import Path
import difflib,hashlib
ROOT=Path(__file__).parent
SITE=Path(r'[local path redacted]')
source=(SITE/'reader-structures.mjs').read_text(encoding='utf-8-sig')
out=source
old="function scopeKind(ref){return /comput|DFT|PBE/i.test([ref.sourceType,ref.referenceType,ref.name,ref.description].join(' '))?'Computed reference':'Bulk reference';}"
helpers=r'''export function scopeKind(ref){
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
async function mountReferenceChoices(panel,entries,r,finite){
 const contexts=referenceSampleChoices(entries,r),scopeNote=el('p',undefined,'reader-note reader-sample-scope'),choose=el('select',undefined,'reader-method-select'),display=el('div');
 let sampleSelect,activeEntries=[],generation=0;
 if(contexts.length){
  sampleSelect=el('select',undefined,'reader-method-select');sampleSelect.setAttribute('aria-label','Source specimen context for unit-cell comparison');
  for(const p of contexts){const opt=el('option',p.sample_id+(p.phase?.value?' · source reports '+p.phase.value:''));opt.value=p.sample_id;sampleSelect.append(opt);}
  panel.append(sampleSelect);
 }
 choose.setAttribute('aria-label',finite?'Choose a finite particle reference':'Choose a component and reference phase');
 panel.append(scopeNote,choose,display);
 const render=async()=>{
  const token=++generation,ref=activeEntries.find(x=>x.id===choose.value);display.replaceChildren();
  if(!ref){display.append(el('p',activeEntries.length?'Choose an independently sourced reference for comparison. This choice does not assign a phase to the synthesis specimen.':'No suitable unit-cell reference is supplied for this selected source context. Its reported phase remains source evidence, not a verified atomic reconstruction.','reader-note'));return;}
  try{await drawReference(display,ref,finite);}catch(error){if(token===generation)display.replaceChildren(el('p','Structure unavailable: '+error.message,'reader-note'));}
 };
 const refresh=async()=>{
  const sample=contexts.find(p=>p.sample_id===sampleSelect?.value);
  activeEntries=referencesForSample(entries,sample?.sample_id);
  scopeNote.textContent=sample?'Selected source context: '+sample.sample_id+(sample.phase?.value?' · source reports '+sample.phase.value:'')+'. The reference does not independently verify that phase assignment.':'Independent reference comparison. Component unit cells do not reconstruct an interface or complete particle.';
  choose.replaceChildren();
  const requiresChoice=activeEntries.length>1;
  if(requiresChoice){const prompt=el('option',finite?'Choose a finite reference':'Choose a component and reference phase');prompt.value='';prompt.disabled=true;prompt.selected=true;choose.append(prompt);}
  const groups=new Map();
  for(const ref of activeEntries){const formula=ref.formula||'Reference';if(!groups.has(formula)){const group=el('optgroup');group.label=formula+' · independent reference';groups.set(formula,group);choose.append(group);}const option=el('option',ref.name+' · '+scopeKind(ref));option.value=ref.id;groups.get(formula).append(option);}
  choose.hidden=activeEntries.length===0;
  if(!requiresChoice&&activeEntries.length)choose.value=activeEntries[0].id;
  await render();
 };
 choose.onchange=render;if(sampleSelect)sampleSelect.onchange=refresh;await refresh();
}'''
assert old in out
out=out.replace(old,helpers)
old=" const details=disclosure('Reference scope and provenance',el('p',ref.scope||ref.description));if(ref.phaseScope)details.append(el('p',ref.phaseScope));host.append(details);"
new=""" const phaseScope=ref.phaseScope||ref.scope||ref.description;
 if(phaseScope)host.append(el('p',phaseScope,'reader-note reader-phase-scope'));
 if(ref.sample_context_note)host.append(el('p',ref.sample_context_note,'reader-note reader-sample-scope'));
 const details=disclosure('Reference provenance',el('p','Reference type: '+scopeKind(ref)+'. This asset is not a measured synthesis-sample reconstruction.'));
 if(ref.scope&&ref.scope!==phaseScope)details.append(el('p',ref.scope));host.append(details);"""
assert old in out
out=out.replace(old,new)
old="  const v=model.cellVectors,point="
assert old in out
out=out.replace(old,"  const v=referenceCellVectors(model),point=")
old="  const entries=key==='finite'?finite:refs;if(entries.length){const select=el('select',undefined,'reader-method-select'),view=el('div');select.setAttribute('aria-label',key==='finite'?'Finite particle reference':'Unit cell reference');for(const ref of entries){const option=el('option',ref.name);option.value=ref.id;select.append(option);}panel.append(select,view);const show=()=>drawReference(view,entries.find(x=>x.id===select.value),key==='finite').catch(e=>{view.textContent='Structure unavailable: '+e.message;});select.onchange=show;await show();return;}"
assert old in out
out=out.replace(old,"  const entries=key==='finite'?finite:refs;if(entries.length){await mountReferenceChoices(panel,entries,r,key==='finite');return;}")
old="Mo:'#738c9c',X:'#9975b3'"
assert old in out
out=out.replace(old,"Mo:'#738c9c',In:'#7e88b5',Co:'#4c83b5',Ni:'#5caa87',Ir:'#9d8fb5',Mn:'#be7eaf',Pt:'#a2afb9',Sn:'#718695',Al:'#b7bfc9',As:'#a48cc4',X:'#9975b3'")
(ROOT/'reader-structures.proposed.mjs').write_text(out,encoding='utf-8')
diff=''.join(difflib.unified_diff(source.splitlines(True),out.splitlines(True),fromfile='a/dist/reader-structures.mjs',tofile='b/dist/reader-structures.mjs'))
(ROOT/'reader-structures.patch').write_text(diff,encoding='utf-8')
(ROOT/'reader-structures-base.sha256').write_text(hashlib.sha256(source.encode()).hexdigest()+'\n',encoding='utf-8')
(ROOT/'reader-selection-helpers.testable.mjs').write_text(helpers.split('async function mountReferenceChoices')[0],encoding='utf-8')
print('Wrote proposal module, unified patch, base-content hash and testable pure helpers.')
