import assert from 'node:assert/strict';import fs from 'node:fs';
import {averagePositions,HEO_RECORDS} from './heo2003-average-viewer.mjs';
import {selectReflections} from '../../si-reader-proposal/heo2003-reflection-viewer.mjs';
const model=JSON.parse(fs.readFileSync(new URL('./heo2003-average-view.json',import.meta.url),'utf8'));
const si=JSON.parse(fs.readFileSync(new URL('../../si-reader-proposal/heo2003-reflections.json',import.meta.url),'utf8'));let checks=0;
const check=f=>{f();checks++;};
check(()=>assert.equal(averagePositions(model).length,680));check(()=>assert.equal(averagePositions(model,2).length,5440));
for(const [i,p]of averagePositions(model).entries()){check(()=>assert.deepEqual([p.x,p.y,p.z],model.fractionalSites[i].cartesian));check(()=>assert.deepEqual(p.components,model.fractionalSites[i].components));}
check(()=>assert.equal(averagePositions(model,1,['In(IIa)']).length,648));check(()=>assert.equal(averagePositions(model,1,['In(II)','In(IIa)']).length,616));
check(()=>assert.throws(()=>averagePositions(model,3)));check(()=>assert.deepEqual(HEO_RECORDS,['heo-2003-in66-route','heo-2003-single-crystal-acquisition','heo-2003-average-structure']));
check(()=>assert.equal(selectReflections(si).length,1209));check(()=>assert.equal(selectReflections(si,{page:'0'}).length,1209));
check(()=>assert.equal(selectReflections(si,{kind:'negative'}).length,137));check(()=>assert.equal(selectReflections(si,{kind:'zero'}).length,1));check(()=>assert.equal(selectReflections(si,{kind:'unresolved'}).length,2));
for(let page=1;page<=14;page++)check(()=>assert.equal(selectReflections(si,{page:String(page)}).length,si.counts.rows_by_page[String(page)]));
check(()=>assert.equal(selectReflections(si,{query:'9 11 27'}).length,1));check(()=>assert.equal(selectReflections(si,{query:'(9,11,27)'})[0].row_id,'si-p11-R-r035'));
check(()=>assert.equal(selectReflections(si,{query:'si-p12-L-r012',kind:'unresolved'}).length,1));
check(()=>assert.equal(selectReflections(si,{query:'nonsense'}).length,0));
check(()=>assert.equal(model.dft_input_eligible,false));check(()=>assert.equal(model.exact_structure_recipe_eligible,false));
console.log(JSON.stringify({status:'passed',checks,scope:'Actual exported data-selection and average-periodic-repetition functions; DOM/browser checked separately.'}));
