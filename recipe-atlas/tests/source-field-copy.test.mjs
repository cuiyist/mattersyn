import assert from 'node:assert/strict';
import {conditionFieldText,conditionDisclosureText,productFactLabel,formulaFieldText,READER_COPY} from '../static/source-field-copy.mjs';
const extracted={quality:{review_status:'source_extracted'}};
let passed=0;
const check=(ok)=>{assert.ok(ok);passed++;};
check(conditionFieldText('Not reported',extracted)==='Not reported');
check(conditionDisclosureText(extracted)==='Conditions and source');
check(productFactLabel('Crystal phase',extracted)==='Phase or crystallinity');
check(productFactLabel('Phase',extracted)==='Phase or crystallinity');
for(const status of ['source_reviewed','reviewed','draft',null]){
 const record={quality:{review_status:status}};
 check(conditionFieldText('Not reported',record)==='Not reported');
 check(conditionDisclosureText(record)==='Conditions and source');
 check(productFactLabel('Crystal phase',record)==='Phase or crystallinity');
}
for(const value of ['200 °C','650 °C','Ar','30 MPa','450 °C','Not recorded in this field'])check(conditionFieldText(value,extracted)===(value==='Not recorded in this field'?'Not reported':value));
check(productFactLabel('Composition',extracted)==='Composition');
const fact={label:'Crystal phase',value:'single-crystal'},before=JSON.stringify(fact);
check(productFactLabel(fact.label,extracted)==='Phase or crystallinity'&&JSON.stringify(fact)===before);


for(const status of ['source_extracted','source_reviewed','audited',undefined]){const r={quality:{review_status:status}},before=JSON.stringify(r);for(const text of ['Not reported','Not recorded in this field','Not specified','Unspecified'])check(conditionFieldText(text,r)==='Not reported');for(const text of [undefined,null,'','Unspecified','Source empirical formula not reported'])check(formulaFieldText(text)==='Not reported');check(READER_COPY.sourceLink==='Source details →'&&READER_COPY.toolbar==='Synthesis and evidence');check(JSON.stringify(r)===before);}
for(const text of ['CdSe','Source-defined mixture','Room temperature (numeric value not reported)','Not reported · explicit source note','Reactor quantity unavailable: source binding or value invalid']){check(conditionFieldText(text,extracted)===text);check(formulaFieldText(text)===text);}
console.log(JSON.stringify({passed,failed:0,canonical_changes:0,source_claims:0,model_calls:0}));
