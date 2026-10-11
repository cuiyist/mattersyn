import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
class Element {
 constructor(tag){this.tagName=tag;this.children=[];this.dataset={};this._text='';this.className='';this.open=false;}
 set textContent(value){this._text=String(value);this.children=[];}
 get textContent(){return this._text+this.children.map(x=>x.textContent??String(x)).join('');}
 set innerHTML(value){throw new Error('Unsafe HTML interpretation is forbidden');}
 append(...children){this.children.push(...children);}
 replaceChildren(...children){this._text='';this.children=[...children];}
 insertBefore(child){this.children.push(child);}
 closest(selector){return selector==='[data-figure]'&&this.dataset.figure?this:null;}
 showModal(){this.open=true;}
 close(){this.open=false;}
}
function fixture(){
 const created=[],ids=new Map(),listeners=new Map();
 const create=tag=>{const x=new Element(tag);created.push(x);return x;};
 const document={title:'',createElement:create,getElementById:id=>{if(!ids.has(id))ids.set(id,create(id==='figure-dialog'?'dialog':'div'));return ids.get(id);},addEventListener:(name,fn)=>listeners.set(name,fn)};
 const long='Registered public paraphrase. '+('Complete public detail. '.repeat(80));
 const data={title:'Synthetic legacy review',doi:'10.1000/synthetic',documents:[],recipe_inventory:[],characterization_inventory:[],figures:[
  {id:'figure-1',label:'Figure 1',public_asset:'synthetic-one.png',caption_paraphrase:long,document_role:'main',page:2,raw_quote:'PRIVATE-SYNTHETIC'},
  {id:'figure-2',label:'Figure 2',public_asset:'synthetic-two.png',description:'Existing short public description',document_role:'main',page:3},
  {id:'figure-3',label:'Figure 3',public_asset:'synthetic-three.png',document_role:'main',page:4}
 ],evidence_conflicts:[],remaining_gaps:[]};
 return {created,ids,listeners,document,data,long};
}
test('legacy cards and native enlargement use complete safe public captions, preserve locators, and clear stale text',{concurrency:false},async()=>{
 const f=fixture(),keys=['document','location','fetch'],old=new Map(keys.map(k=>[k,Object.getOwnPropertyDescriptor(globalThis,k)]));
 let requests=0;
 try{
  globalThis.document=f.document;globalThis.location={search:'?id=synthetic-caption-review',hash:''};
  globalThis.fetch=async url=>{requests++;assert.equal(url,'data/paper-reviews/synthetic-caption-review.json');return {ok:true,json:async()=>f.data};};
  await import('../static/paper-review.mjs?synthetic-caption-regression=1');
  assert.equal(requests,1);
  const cards=f.created.filter(x=>x.className==='review-figure');assert.equal(cards.length,3);
  const triggers=cards.map(x=>x.children.find(n=>n.dataset?.figure));
  assert.equal(cards[0].children.filter(x=>x.className==='reader-caption-text')[0].textContent,f.long.trim());
  assert.equal(cards[0].children.find(x=>x.tagName==='small').textContent,'main · PDF page 2');
  const click=f.listeners.get('click');assert.equal(typeof click,'function');
  click({target:triggers[0],preventDefault(){}});
  const dialog=f.ids.get('figure-dialog'),host=dialog.children.find(x=>x.className==='review-figure-caption');
  assert.equal(dialog.open,true);assert.equal(host.textContent,f.long.trim());assert.equal(host.textContent.includes('PRIVATE-SYNTHETIC'),false);
  assert.equal(f.ids.get('figure-large').alt,f.long.trim());
  click({target:triggers[1],preventDefault(){}});
  assert.equal(host.textContent,'Existing short public description');assert.equal(host.children.length,1);
  click({target:triggers[2],preventDefault(){}});
  assert.equal(host.textContent,'');assert.equal(host.children.length,0);assert.equal(f.ids.get('figure-title').textContent,'Figure 3');
 }finally{for(const k of keys){const descriptor=old.get(k);if(descriptor)Object.defineProperty(globalThis,k,descriptor);else delete globalThis[k];}}
});
test('legacy modal captions wrap fully without truncation styles',()=>{
 const css=fs.readFileSync(new URL('../static/paper-review.css',import.meta.url),'utf8');
 const rule=css.match(/\.review-figure-caption \.reader-caption-text\{([^}]+)\}/);assert.ok(rule);
 assert.match(rule[1],/white-space:pre-wrap/);assert.match(rule[1],/overflow-wrap:anywhere/);
 assert.doesNotMatch(rule[1],/line-clamp|text-overflow|max-height|overflow:hidden/);
});
