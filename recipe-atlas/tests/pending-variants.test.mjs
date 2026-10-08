import test from 'node:test';
import assert from 'node:assert/strict';
import {pendingVariants,renderPendingVariants,PENDING_BADGE} from '../static/pending-variants.mjs';

test('pending notices require explicit locators, preserve input and do not infer from gaps',()=>{
 const input=[{id:'variant-b',label:'Synthetic variant B',source_locators:['Main PDF p.2, Table 1']}];
 const before=structuredClone(input);assert.deepEqual(pendingVariants(input),before);assert.deepEqual(input,before);
 assert.deepEqual(pendingVariants(undefined),[]);
 for(const bad of [[{...input[0],source_locators:[]}],[{...input[0],training_ready:true}],[input[0],input[0]],
   [{...input[0],source_locators:['C:/private/source.pdf']}],[{...input[0],source_locators:['Main p.2','Main p.2']}]])assert.throws(()=>pendingVariants(bad));
});

test('coverage notice is text-only, displays locators and retains audit/training qualifications',()=>{
 class Node {constructor(tag,doc){this.tagName=tag;this.ownerDocument=doc;this.children=[];this._text='';}
  append(...nodes){this.children.push(...nodes);}set textContent(v){this._text=String(v);this.children=[];}
  get textContent(){return this._text+this.children.map(n=>n.textContent).join(' ');}set innerHTML(_){throw Error('HTML sink forbidden');}}
 const doc={createElement:tag=>new Node(tag,doc)},host=new Node('section',doc);
 const notice=renderPendingVariants(host,[{id:'b',label:'<script>variant</script>',source_locators:['Main PDF p.2, Table 1']}]);
 assert.match(notice.textContent,new RegExp(PENDING_BADGE));assert.match(notice.textContent,/Main PDF p.2, Table 1/);
 assert.match(notice.textContent,/not been independently audited or included in training/);
 assert.equal(renderPendingVariants(host,[]),null);
});
