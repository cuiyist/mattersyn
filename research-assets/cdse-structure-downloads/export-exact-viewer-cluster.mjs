import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {buildCrystal} from '../../recipe-atlas/dist/shape-data.mjs';
import {sampleRecords} from '../../recipe-atlas/dist/murray-data.mjs';
const root=path.dirname(fileURLToPath(import.meta.url));
const site=path.resolve(root,'../../recipe-atlas/dist');
const refPath=path.join(site,'assets/peng2000-crystal-reference.json');
const reference=JSON.parse(fs.readFileSync(refPath,'utf8'));
const sample=sampleRecords.tem6;
if(sample.long!==3.5||sample.short!==3||sample.shape!=='dot')throw Error('Expected current TEM6 sample changed.');
const atoms=buildCrystal(reference,sample);
const sha=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const result={source:'Exact return value of current Site buildCrystal(reference, sampleRecords.tem6), imported read-only',
  sourceModule:path.join(site,'shape-data.mjs'),sourceModuleSha256:sha(path.join(site,'shape-data.mjs')),
  sampleSourceModuleSha256:sha(path.join(site,'murray-data.mjs')),referenceSha256:sha(refPath),
  reference,sample,atoms};
fs.writeFileSync(path.join(root,'exact-viewer-cluster.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({atomCount:atoms.length,counts:atoms.reduce((r,a)=>(r[a.elem]=(r[a.elem]||0)+1,r),{})}));
