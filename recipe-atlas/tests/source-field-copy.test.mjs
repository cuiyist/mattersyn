import assert from 'node:assert/strict';
import {conditionFieldText,conditionDisclosureText,productFactLabel} from '../static/source-field-copy.mjs';
const extracted={quality:{review_status:'source_extracted'}};
let passed=0;
const check=(ok)=>{assert.ok(ok);passed++;};
check(conditionFieldText('Not reported',extracted)==='Not recorded in this field');
check(conditionDisclosureText(extracted)==='Conditions and source');
check(productFactLabel('Crystal phase',extracted)==='Phase or crystallinity');
check(productFactLabel('Phase',extracted)==='Phase or crystallinity');
for(const status of ['source_reviewed','reviewed','draft',null]){
 const record={quality:{review_status:status}};
 check(conditionFieldText('Not reported',record)==='Not reported');
 check(conditionDisclosureText(record)==='All reported conditions and source');
 check(productFactLabel('Crystal phase',record)==='Crystal phase');
}
for(const value of ['200 °C','650 °C','Ar','30 MPa','450 °C','Not recorded in this field'])check(conditionFieldText(value,extracted)===value);
check(productFactLabel('Composition',extracted)==='Composition');
const fact={label:'Crystal phase',value:'single-crystal'},before=JSON.stringify(fact);
check(productFactLabel(fact.label,extracted)==='Phase or crystallinity'&&JSON.stringify(fact)===before);
console.log(JSON.stringify({passed,failed:0,canonical_changes:0,source_claims:0,model_calls:0}));
