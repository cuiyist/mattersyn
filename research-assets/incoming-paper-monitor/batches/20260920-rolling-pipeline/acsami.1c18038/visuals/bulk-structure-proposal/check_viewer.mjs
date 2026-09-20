import fs from 'node:fs';
import {eligibleBulkContexts,displayGeometry,mountLianBulk,BULK_BINDINGS} from './lian2021-bulk-viewer.mjs';
const read=f=>JSON.parse(fs.readFileSync(new URL(f,import.meta.url),'utf8'));
const records=read('canonical-record-snapshots.json'),models={A:read('lian2021-bulk-a-non-h.json'),B:read('lian2021-bulk-b-non-h.json')};
const checks=[];function ok(name,result){checks.push({check:name,passed:!!result});if(!result)throw Error(name);}
for(const [id,r]of Object.entries(records)){
 const expected=BULK_BINDINGS.filter(b=>b.record_id===id);ok(id+' exact context count',eligibleBulkContexts(r).length===expected.length);
 for(const b of expected){for(const [field,change]of [['sample',p=>p.sample_id+='-wrong'],['formula',p=>p.composition.value='wrong'],['phase',p=>p.phase.value='wrong']]){const copy=structuredClone(r);change(copy.products.find(p=>p.sample_id===b.sample_id));ok(id+' '+b.sample_id+' rejects '+field,!eligibleBulkContexts(copy).some(x=>x.sample_id===b.sample_id));}}
 const wrong=structuredClone(r);wrong.lineage.source_group='other';ok(id+' rejects other source',eligibleBulkContexts(wrong).length===0);
}
for(const [phase,m]of Object.entries(models)){
 const before=JSON.stringify(m);for(const expanded of [false,true]){const g=displayGeometry(m,expanded);ok(phase+' markers '+expanded,g.sites.length===(expanded?(phase==='A'?64:144):(phase==='A'?32:36)));ok(phase+' bond mode '+expanded,g.bonds.length===(expanded?0:(phase==='A'?29:32)));for(const s of g.sites){ok(s.id+' unknown occupancy '+expanded,s.occupancy===null);ok(s.id+' finite Cartesian '+expanded,s.cartesian.every(Number.isFinite));}}
 ok(phase+' geometry immutable',JSON.stringify(m)===before);
 const bad=structuredClone(m);bad.asymmetric_unit_sites[0].occupancy=1;let rejected=false;try{displayGeometry(bad);}catch{rejected=true;}ok(phase+' occupancy inference rejected',rejected);
}
// Actual adapter execution with a minimal DOM and renderer spy. This is not a browser test.
class Element{constructor(tag){this.tag=tag;this.children=[];this.dataset={};this.style={};this.isConnected=true;}append(...nodes){this.children.push(...nodes);}setAttribute(k,v){this[k]=v;}}
globalThis.document={createElement:tag=>new Element(tag)};globalThis.ResizeObserver=class{observe(){}disconnect(){}};
const spies=[];globalThis.$3Dmol={createViewer(){const spy={atoms:[],lines:[],styles:[],resets:0,getView(){return [0,0,0,0,0,0,0,1];},setView(){this.resets++;},clear(){this.atoms=[];this.lines=[];},addModel(){return {addAtoms:a=>spy.atoms=a};},setStyle(...a){this.styles.push(a);},addLine(a){this.lines.push(a);},zoomTo(){},zoom(){},rotate(){},render(){},resize(){},removeAllLabels(){},addLabel(){}};spies.push(spy);return spy;}};
const walk=(node)=>[node,...node.children.flatMap(x=>x instanceof Element?walk(x):[])];
for(const [id,r]of Object.entries(records)){
 const host=new Element('host'),n=eligibleBulkContexts(r).length,start=spies.length;
 ok(id+' mount return',(await mountLianBulk(host,r,{models}))===!!n);ok(id+' mounted card count',host.children.length===n);
 for(let i=0;i<n;i++){const b=eligibleBulkContexts(r)[i],spy=spies[start+i],nodes=walk(host.children[i]);ok(id+' '+b.phase+' source bond total',spy.atoms.reduce((s,a)=>s+a.bonds.length,0)===(b.phase==='A'?58:64));ok(id+' '+b.phase+' cell edges',spy.lines.length===12);
 const select=nodes.find(x=>x.tag==='select');select.value='cell';select.onchange();ok(id+' '+b.phase+' expanded marker count',spy.atoms.length===(b.phase==='A'?64:144));ok(id+' '+b.phase+' no guessed expanded bonds',spy.atoms.every(x=>x.bonds.length===0));const reset=nodes.find(x=>x.tag==='button'&&x.textContent==='Reset');reset.onclick();ok(id+' '+b.phase+' reset orientation',spy.resets===3);
 ok(id+' '+b.phase+' scope caveat',nodes.some(x=>x.textContent?.includes('same physical aliquot')));ok(id+' '+b.phase+' unknown occupancy warning',nodes.some(x=>x.textContent?.includes('All occupancies remain unknown')));
 }
}
const out={status:'passed',scope:'actual module functions and DOM/renderer-spy integration; browser evidence is separate',check_count:checks.length,checks};fs.writeFileSync(new URL('viewer-validation.json',import.meta.url),JSON.stringify(out,null,2)+'\n');console.log(JSON.stringify({status:out.status,checks:out.check_count}));
