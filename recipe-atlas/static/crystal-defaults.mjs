// Unit cells for routes that have no hand-bound reference: use the library's bulk
// reference for the same composition (or for each component of a composite).
// A default is a comparison aid only; it is never a statement about the paper's sample.
// If the paper names a phase and the library has no cell of that phase, nothing is shown.
const CUSTOM_VIEWER_SOURCES=new Set(['heo2003','lian2021','heath1996','evans2010']);
const group=entry=>entry.prototypeSpaceGroupNumber||entry.spaceGroupNumber||0;
const inRange=(lo,hi)=>entry=>group(entry)>=lo&&group(entry)<=hi;
const symbol=pattern=>entry=>pattern.test(entry.spaceGroup||'');
const named=pattern=>entry=>pattern.test([entry.name,entry.phaseName].filter(Boolean).join(' '));
const either=(...tests)=>entry=>tests.some(test=>test(entry));
// [words a paper may use for a phase, test a library entry must pass]
const PHASE_TESTS=[
 [/zinc.?blende|sphalerite/i,either(symbol(/F\s*-4\s*3\s*m/),named(/zinc.?blende|sphalerite/i))],
 [/wurtzite/i,either(symbol(/P\s*63\s*m\s*c/),named(/wurtzite/i))],
 [/rock.?salt|halite|galena/i,either(named(/rock.?salt/i),entry=>group(entry)===225&&!/face.cent|\bfcc\b/i.test(entry.name||''))],
 [/face.cent(?:e?red)|\bfcc\b/i,inRange(225,225)],[/\bhcp\b|hexagonal close/i,inRange(194,194)],[/\bbcc\b|body.cent(?:e?red)/i,inRange(229,229)],
 [/anatase/i,named(/anatase/i)],[/rutile/i,named(/rutile/i)],[/brookite/i,named(/brookite/i)],[/chalcopyrite/i,named(/chalcopyrite/i)],
 [/spinel/i,named(/spinel/i)],[/calcite/i,named(/calcite/i)],[/aragonite/i,named(/aragonite/i)],[/baddeleyite/i,named(/baddeleyite/i)],
 [/bixbyite/i,named(/bixbyite/i)],[/perovskite/i,named(/perovskite/i)],
 [/\bcubic\b/i,inRange(195,230)],[/tetragonal/i,inRange(75,142)],[/orthorhombic/i,inRange(16,74)],[/\bhexagonal\b/i,inRange(168,194)],
 [/trigonal|rhombohedral/i,inRange(143,167)],[/monoclinic/i,inRange(3,15)],[/triclinic/i,inRange(1,2)]
];
const tidy=value=>String(value||'').replace(/\s+/g,'');
export function compositionParts(r){
 const material=r?.material||{},listed=Array.isArray(material.components)&&material.components.length?material.components:String(material.formula||'').split(/[\/@]/);
 // "InP:Zn" is a doped host; the host cell is the useful comparison.
 return [...new Set(listed.map(part=>tidy(String(part).split(':')[0])).filter(Boolean))];
}
export function reportedPhases(r){
 const productFacts=(r?.products||[]).map(p=>p?.phase?.value).filter(value=>typeof value==='string'&&value.trim());
 // The reported product phase, if present, takes precedence over an intended target.
 return productFacts.length?productFacts:[r?.intended_target?.phase?.value].filter(value=>typeof value==='string'&&value.trim());
}
export function defaultCrystalReferences(entries,r,excluded=[]){
 if(!r||CUSTOM_VIEWER_SOURCES.has(r.lineage?.source_group))return [];
 if(excluded.some(x=>tidy(x.formula)===tidy(r.material?.formula)))return [];
 const parts=compositionParts(r),phases=reportedPhases(r),chosen=[];
 // A nonempty phase that is not understood must not be described as unreported.
 // Recognized qualifiers in the same phase statement all constrain the reference.
 const phaseTests=phases.map(phase=>PHASE_TESTS.filter(([words])=>words.test(phase)).map(([,test])=>test));
 for(const part of parts){
  const seen=new Set(),bulk=[];
  for(const entry of entries){
   // Any periodic reference cell in the library qualifies; partial, computed and measured-sample models do not.
   if(tidy(entry.formula)!==part||!entry.modelPath||entry.referenceOnly===false||entry.measuredSampleStructure===true)continue;
   if(/partial|comput|dft/i.test([entry.sourceType,entry.referenceType].join(' ')))continue;
   const key=entry.cifSha256||entry.cifPath;if(seen.has(key))continue;seen.add(key);bulk.push(entry);
  }
  const shown=phases.length?bulk.filter(entry=>phaseTests.some(tests=>tests.length&&tests.every(test=>test(entry)))):bulk;
  for(const entry of shown){
   const scope='Bulk reference shown because the composition matches'+(phases.length?' and the paper reports this phase':'; the paper does not state the phase, so every bulk form in the library is shown')+'. It is not a structure of the synthesized sample: size, surface, defects and interfaces are not represented.';
   chosen.push({...entry,displayPolicy:'independent_reference',sample_context_ids:undefined,sampleContextIdsByRecord:undefined,bindingScopes:undefined,finiteModelPath:undefined,
    roleByRecord:{[r.record_id]:parts.length>1?'Component reference':'Reference by composition'},scope,phaseScope:scope,description:scope,sample_context_note:null,defaultByComposition:true});
  }
 }
 return chosen;
}
