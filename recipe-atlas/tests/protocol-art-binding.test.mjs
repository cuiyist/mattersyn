import test from 'node:test';
import assert from 'node:assert/strict';
import {selectProtocolArt} from '../static/protocol-art-binding.mjs';
const record={record_id:'example-route'},operation={id:'sealed-hold'};
const item={operation_id:'sealed-hold',asset_path:'assets/protocol/example.svg',asset_sha256:'a'.repeat(64),caption:'Illustrative equipment only.',source_locator:'Main p. 1'};
const binding={record_id:'example-route',bindings:[item]};
test('matches the exact record and operation without adding conditions',()=>{
 assert.equal(selectProtocolArt(binding,record,operation),item);
 assert.equal(selectProtocolArt(binding,{record_id:'other'},operation),null);
 assert.equal(selectProtocolArt(binding,record,{id:'other'}),null);
 assert.equal(selectProtocolArt(null,record,operation),null);
});
test('rejects ambiguous, unsupported or unattributed artwork',()=>{
 assert.equal(selectProtocolArt({...binding,bindings:[item,item]},record,operation),null);
 for(const invalid of [{asset_path:'https://example.com/image.svg'},{asset_path:'assets/protocol/../image.svg'},{asset_sha256:'x'},{source_locator:''},{caption:''}])
  assert.equal(selectProtocolArt({...binding,bindings:[{...item,...invalid}]},record,operation),null);
});


// Exercise the actual cached Reader accessor and Data mount with invented inputs.
import {readFile} from 'node:fs/promises';
const readerCode=await readFile(new URL('../static/reader-app.mjs',import.meta.url),'utf8');
const dataCode=await readFile(new URL('../static/illustrated-record.mjs',import.meta.url),'utf8');
function cacheAccessor(payload){
 let fetches=0;
 const cache=readerCode.match(/^const cache=new Map\(\);$/m)[0];
 const json=readerCode.match(/^function json\(path\)\{[^\n]+\}$/m)[0];
 const accessor=readerCode.match(/^export async function reviewedProtocolArt\(r\)\{[\s\S]*?^\}/m)[0].replace('export ','');
 const fetch=async()=>{fetches++;return {ok:true,json:async()=>payload};};
 const get=new Function('fetch','siteURL',cache+'\n'+json+'\n'+accessor+'\nreturn reviewedProtocolArt;')(fetch,p=>'https://fixture.invalid/'+p);
 return {get,fetches:()=>fetches};
}
test('Data uses the exact cached reviewed operation art without mutating inputs',async()=>{
 const payload={records:{[record.record_id]:{protocol_art:binding}}},before=JSON.stringify({record,payload}),c=cacheAccessor(payload);
 const first=await c.get(record),second=await c.get(record);
 assert.equal(first,binding);assert.equal(second,binding);assert.equal(c.fetches(),1);
 assert.equal(selectProtocolArt(first,record,operation),item);
 assert.equal(selectProtocolArt(first,record,{id:'other'}),null);
 assert.equal(JSON.stringify({record,payload}),before);
});
test('missing, wrong-record and malformed cached bindings keep the existing fallback',async()=>{
 for(const candidate of [undefined,null,{}, {...binding,record_id:'other'}, {...binding,bindings:null}, {...binding,bindings:[null]}, {...binding,bindings:[undefined]}, {...binding,bindings:['invalid']}]){
  const c=cacheAccessor({records:{[record.record_id]:{protocol_art:candidate}}});
  assert.equal(await c.get(record),null);
 }
 assert.equal(await cacheAccessor({}).get(record),null);
 assert.equal(await cacheAccessor({records:{}}).get(record),null);
 assert.equal(await cacheAccessor({}).get(null),null);
 for(const candidate of [{...binding,bindings:[]},{...binding,bindings:[item,item]},{...binding,bindings:[{...item,asset_path:'assets/protocol/../invalid.svg'}]}]){
  const result=await cacheAccessor({records:{[record.record_id]:{protocol_art:candidate}}}).get(record);
  assert.equal(selectProtocolArt(result,record,operation),null);
 }
});
const AsyncFunction=Object.getPrototypeOf(async function(){}).constructor;
async function actualDataMount(payload,readerSelected=false){
 const c=cacheAccessor(payload),calls=[],doc={body:{dataset:{recordId:record.record_id}},getElementById:id=>({id})};
 const code=dataCode.replace(/^import .+;\r?\n/gm,'').replaceAll('import.meta.url',JSON.stringify('https://fixture.invalid/illustrated-record.mjs'));
 await new AsyncFunction('document','fetch','bootstrapRecord','mountProtocol','enhanceRecordChemicals','mountEvidence','mountCrystalReferences','reviewedProtocolArt','console',code)(doc,async()=>({ok:true,json:async()=>record}),async()=>readerSelected,(...args)=>calls.push(args),async()=>{},async()=>{},async()=>{},c.get,{error:e=>{throw e;}});
 return {calls,fetches:c.fetches()};
}
test('actual Data bootstrap passes the reviewed binding as the fourth mount argument',async()=>{
 const result=await actualDataMount({records:{[record.record_id]:{protocol_art:binding}}});
 assert.equal(result.calls.length,1);assert.equal(result.calls[0][0].id,'record-protocol-visual');
 assert.equal(result.calls[0][1],record);assert.equal(result.calls[0][2],'../');assert.equal(result.calls[0][3],binding);
 assert.equal(selectProtocolArt(result.calls[0][3],record,operation),item);
 const absent=await actualDataMount({records:{}});assert.equal(absent.calls[0][3],null);
 assert.equal(selectProtocolArt(absent.calls[0][3],record,operation),null);
 const reader=await actualDataMount({records:{[record.record_id]:{protocol_art:binding}}},true);assert.equal(reader.calls.length,0);assert.equal(reader.fetches,0);
});
