import {mountProtocol} from './protocol-visuals.mjs?v=0.25.0-r1';
import {enhanceRecordChemicals} from './chemical-viewer.mjs?v=0.25.0-r1';
import {mountEvidence, mountCrystalReferences} from './material-guide.mjs?v=0.25.0-r1';
const id=document.body.dataset.recordId;
try{const response=await fetch(new URL('data/records/'+id+'.json',import.meta.url),{cache:'no-store'});if(!response.ok)throw Error('Record unavailable');const r=await response.json();mountProtocol(document.getElementById('record-protocol-visual'),r,'../');await enhanceRecordChemicals(r);await mountEvidence(document.getElementById('record-original-evidence'),r);await mountCrystalReferences(document.getElementById('record-crystal-references'),r);}catch(e){console.error(e);}

if(id==='heo-2003-refinement-comparison'){const host=document.getElementById('record-crystal-references');const {mountHeoReflections}=await import('./heo2003-reflection-viewer.mjs');await mountHeoReflections(host);}
