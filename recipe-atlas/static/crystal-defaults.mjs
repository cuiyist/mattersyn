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
 [/zinc.?blende?|sphalerite|coloradoite|tiemannite/i,either(symbol(/F\s*-4\s*3\s*m/),named(/zinc.?blende|sphalerite/i))],
 [/wurtzite/i,either(symbol(/P\s*63\s*m\s*c/),named(/wurtzite/i))],
 [/rock.?salt|halite|galena|periclase|bunsenite|alabandite|sylvite/i,either(named(/rock.?salt/i),entry=>group(entry)===225&&!/face.cent|\bfcc\b/i.test(entry.name||''))],
 [/face.cent(?:e?red)|\bfcc\b/i,inRange(225,225)],[/\bhcp\b|hexagonal close/i,inRange(194,194)],[/\bbcc\b|body.cent(?:e?red)/i,inRange(229,229)],
 [/anatase/i,named(/anatase/i)],[/rutile/i,named(/rutile/i)],[/brookite/i,named(/brookite/i)],[/chalcopyrite/i,named(/chalcopyrite/i)],
 [/spinel/i,named(/spinel/i)],[/calcite/i,named(/calcite/i)],[/aragonite/i,named(/aragonite/i)],[/baddeleyite/i,named(/baddeleyite/i)],
 [/bixbyite/i,named(/bixbyite/i)],[/perovskite/i,named(/perovskite/i)],[/cuprite/i,named(/cuprite/i)],[/hydroxy?l?apatite|\bapatite/i,named(/apatite/i)],
 [/herzenbergite/i,named(/herzenbergite/i)],[/\b2H\b/i,named(/\b2H\b/i)],[/\b3C\b/i,named(/\b3C\b/i)],[/\b6H\b/i,named(/\b6H\b/i)],
 [/kesterite/i,named(/kesterite/i)],[/scheelite|wulfenite/i,named(/scheelite|wulfenite/i)],[/pyrite|cattierite|vaesite/i,named(/pyrite|cattierite|vaesite/i)],[/aurivillius/i,named(/aurivillius/i)],
 [/russellite|\bP\s*21\s*ab\b/i,either(named(/russellite/i),inRange(29,29))],[/\bYAG\b|garnet/i,named(/garnet/i)],[/hausmannite|hetaerolite/i,named(/hausmannite|hetaerolite/i)],[/tenorite/i,named(/tenorite/i)],
 // Rhombohedral R-Se (Se6 rings) is not the trigonal chain allotrope; no library cell matches it.
 [/\bR-Se\b|\bSe6\b/i,named(/\bR-Se\b|\bSe6\b/i)],
 [/\bcubic\b/i,inRange(195,230)],[/tetragonal/i,inRange(75,142)],[/orthorhombic/i,inRange(16,74)],[/\bhexagonal\b/i,inRange(168,194)],
 [/trigonal|rhombohedral/i,inRange(143,167)],[/monoclinic/i,inRange(3,15)],[/triclinic/i,inRange(1,2)]
];
const tidy=value=>String(value||'').replace(/\s+/g,'');
// Alloy, solid-solution and core/shell names stand for their end members, which are
// shown as component references, as for composites. A name expands only when the
// library has a bulk reference for every end member; otherwise nothing is shown for it.
export const END_MEMBERS=Object.freeze({InGaAs:['InAs','GaAs'],InGaN:['InN','GaN'],AlGaAs:['AlAs','GaAs'],ZnSeS:['ZnSe','ZnS'],CdSeS:['CdSe','CdS'],CdZnS:['CdS','ZnS'],'CdSe-ZnS':['CdSe','ZnS'],InGaP:['InP','GaP'],ZnCdS:['ZnS','CdS'],CdTeSe:['CdTe','CdSe'],SiGe:['Si','Ge'],'CuInSexS2−x':['CuInSe2','CuInS2'],'CuInSexS2-x':['CuInSe2','CuInS2']});
// Composition-specific alloy names (In0.41Ga0.59As) stand for the same end members.
const ALLOY_PATTERNS=[[/^In\d*\.?\d+Ga\d*\.?\d+As$/,['InAs','GaAs']],[/^Al\d*\.?\d+Ga\d*\.?\d+As$/,['AlAs','GaAs']],[/^In\d*\.?\d+Ga\d*\.?\d+N$/,['InN','GaN']]];
const endMembers=part=>END_MEMBERS[part]||ALLOY_PATTERNS.find(([pattern])=>pattern.test(part))?.[1];
// A doped formula names a host and a dopant in either order ("InP:Zn", "Mn:ZnO",
// "Co2+:CdS"); the host cell is the useful comparison. When exactly one side is a bare
// element or ion it is the dopant; otherwise the first side is the host.
const BARE_ELEMENT=/^[A-Z][a-z]?(?:\d*[+-])?$/;
export function dopedHost(part){
 const sides=String(part).split(':').map(tidy).filter(Boolean);
 if(sides.length<2)return sides[0]||'';
 const compounds=sides.filter(side=>!BARE_ELEMENT.test(side));
 return compounds.length===1?compounds[0]:sides[0].replace(/\d*[+-]$/,'');
}
function listedParts(r){
 const material=r?.material||{},listed=Array.isArray(material.components)&&material.components.length?material.components:String(material.formula||'').split(/[\/@]/);
 return [...new Set(listed.map(dopedHost).filter(Boolean))];
}
export function compositionParts(r,entries=null){
 const bulkFormulas=entries&&new Set(entries.filter(bulkReference).map(entry=>tidy(entry.formula)));
 return [...new Set(listedParts(r).flatMap(part=>{const members=endMembers(part);if(!members)return [part];return !bulkFormulas||members.every(m=>bulkFormulas.has(m))?members:[];}))];
}
// Any periodic reference cell in the library qualifies; partial, computed and measured-sample models do not.
function bulkReference(entry){return Boolean(entry.modelPath)&&entry.referenceOnly!==false&&entry.measuredSampleStructure!==true&&!/partial|comput|dft/i.test([entry.sourceType,entry.referenceType].join(' '));}
export function reportedPhases(r){
 // Crystallinity alone does not name a phase or constrain a bulk comparison.
 const specific=value=>typeof value==='string'&&value.trim()&&!/^(?:crystal|crystalline)$/i.test(value.trim());
 const productFacts=(r?.products||[]).map(p=>p?.phase?.value).filter(specific);
 // The reported product phase, if present, takes precedence over an intended target.
 return productFacts.length?productFacts:[r?.intended_target?.phase?.value].filter(specific);
}
export function defaultCrystalReferences(entries,r,excluded=[]){
 if(!r||CUSTOM_VIEWER_SOURCES.has(r.lineage?.source_group))return [];
 if(excluded.some(x=>tidy(x.formula)===tidy(r.material?.formula)))return [];
 const parts=compositionParts(r,entries),phases=reportedPhases(r),chosen=[];
 // A nonempty phase that is not understood must not be described as unreported.
 // Separate phase fractions only when every clause explicitly starts with a percentage.
 // Other separators may join compatible qualifiers; those remain conjunctive.
 const phaseTests=phases.flatMap(phase=>{
  const components=phase.split(/\s*;\s*/).filter(Boolean);
  return components.length>1&&components.every(component=>/^\s*\d+(?:\.\d+)?\s*%/.test(component))?components:[phase];
 })
  .map(phase=>PHASE_TESTS.filter(([words])=>words.test(phase)).map(([,test])=>test));
 for(const part of parts){
  const seen=new Set(),bulk=[];
  for(const entry of entries){
   if(tidy(entry.formula)!==part||!bulkReference(entry))continue;
   const key=entry.cifSha256||entry.cifPath;if(seen.has(key))continue;seen.add(key);bulk.push(entry);
  }
  const shown=phases.length?bulk.filter(entry=>phaseTests.some(tests=>tests.length&&tests.every(test=>test(entry)))):bulk;
  for(const entry of shown){
   const scope=(phases.length?'Bulk reference shown because the composition matches and the paper reports this phase.':'The record does not assign a crystal phase; available bulk references are shown for comparison.')+' It is not a structure of the synthesized sample: size, surface, defects and interfaces are not represented.';
   // A reused library title may mention another record's core/shell role.
   // Every composite default has a neutral component role, even when the
   // product architecture is named; a library title cannot assign that role.
   const name=r.quality?.review_status==='source_extracted'&&parts.length>1
    ?String(entry.name||'').replace(/\s*(?:[·:—–-]\s*)?\b(?:core|shell)\s+comparison\s*$/i,'').trim():entry.name;
   chosen.push({...entry,name,displayPolicy:'independent_reference',sample_context_ids:undefined,sampleContextIdsByRecord:undefined,bindingScopes:undefined,finiteModelPath:undefined,
    roleByRecord:{[r.record_id]:parts.length>1?'Component reference':'Reference by composition'},scope,phaseScope:scope,description:scope,sample_context_note:null,defaultByComposition:true});
  }
 }
 return chosen;
}
