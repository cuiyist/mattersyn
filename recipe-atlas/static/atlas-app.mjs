import {elements} from './periodic-data.mjs';
import {componentScopeLabel} from './reader-utils.mjs?v=0.40.1';
const $=id=>document.getElementById(id),selected=new Set(),tiles=new Map();let materials=[];
const params=new URLSearchParams(location.search);
for(const symbol of (params.get('elements')||'').split(','))if(elements.some(e=>e.symbol===symbol))selected.add(symbol);
const table=$('periodic-table');
for(const e of elements){
 const b=document.createElement('button');b.type='button';b.className='element-tile';b.style.gridRow=e.row;b.style.gridColumn=e.column;b.setAttribute('aria-label',`${e.name} (${e.symbol}), atomic number ${e.number}`);b.title=`${e.name} · ${e.number}`;
 const z=document.createElement('span');z.className='element-number';z.textContent=e.number;const s=document.createElement('span');s.className='element-symbol';s.textContent=e.symbol;b.append(z,s);b.addEventListener('click',()=>{selected.has(e.symbol)?selected.delete(e.symbol):selected.add(e.symbol);render();});table.append(b);tiles.set(e.symbol,b);
}
for(const [row,text] of [[6,'57–71'],[7,'89–103']]){const d=document.createElement('div');d.className='periodic-spacer';d.style.gridRow=row;d.style.gridColumn=3;d.textContent=text;table.append(d);}
function render(){
 const selection=$('selected-elements');selection.replaceChildren();const label=document.createElement('span');label.className='selection-label';label.textContent=selected.size?'Selected elements':'Select elements to find a material';selection.append(label);
 for(const symbol of selected){const b=document.createElement('button');b.className='element-chip';b.textContent=symbol+' ×';b.setAttribute('aria-label','Remove '+symbol);b.addEventListener('click',()=>{selected.delete(symbol);render();});selection.append(b);}
 for(const [symbol,b] of tiles)b.setAttribute('aria-pressed',String(selected.has(symbol)));
 const query=$('material-search').value.trim().toLowerCase(),scope=$('material-scope').value,exact=$('exact-elements').checked;
 const matches=materials.filter(m=>[...selected].every(s=>m.elements.includes(s))&&(!exact||!selected.size||m.elements.length===selected.size)&&(!query||`${m.formula} ${m.name}`.toLowerCase().includes(query))&&(scope==='all'||m.reviewed_records>0));
 matches.sort((a,b)=>(b.reviewed_records>0)-(a.reviewed_records>0)||(b.benchmark_records>0)-(a.benchmark_records>0)||b.reviewed_records-a.reviewed_records||a.formula.localeCompare(b.formula));
 const host=$('material-results');host.replaceChildren();$('material-count').textContent=matches.length+' material / component pages'+(selected.size?' containing '+[...selected].join(' + '):' in the collection');
 for(const m of matches.slice(0,60)){
  const card=document.createElement('article');card.className='material-entry';const status=document.createElement('span');status.className='atlas-status';status.textContent=m.reviewed_records?'Reviewed synthesis records':m.benchmark_records?'Published benchmark':'Indexed literature · awaiting review';
  const h=document.createElement('h3');h.textContent=m.formula;const p=document.createElement('p');p.textContent=m.component_only?componentScopeLabel(m):m.name;const meta=document.createElement('div');meta.className='entry-meta';meta.textContent=`${m.paper_count} verified source contributions · ${m.reviewed_records} methods / variants`;
  const a=document.createElement('a');a.href=m.url;a.textContent='Open material →';card.append(status,h,p,meta,a);host.append(card);
 }
 if(!matches.length){const p=document.createElement('p');p.className='atlas-empty';p.textContent='No reviewed synthesis page matches this selection yet. Papers awaiting review remain in the Source library. This does not establish that synthesis methods do not exist.';host.append(p);}
 if(matches.length>60){const p=document.createElement('p');p.className='atlas-footnote';p.textContent='Showing the first 60 systems. Select additional elements or search a formula to narrow the collection.';host.append(p);}
 const url=new URL(location.href);selected.size?url.searchParams.set('elements',[...selected].join(',')):url.searchParams.delete('elements');history.replaceState(null,'',url.pathname+url.search);
}
$('clear-elements').addEventListener('click',()=>{selected.clear();$('material-search').value='';render();});for(const id of ['material-search','material-scope','exact-elements'])$(id).addEventListener(id==='material-search'?'input':'change',render);
try{const response=await fetch('data/materials-index.json',{cache:'no-store'});if(!response.ok)throw Error('Material index could not be loaded');const data=await response.json();materials=data.materials;
 for(const [symbol,b] of tiles){const found=materials.filter(m=>m.elements.includes(symbol));b.classList.toggle('covered',found.some(m=>m.reviewed_records>0||m.benchmark_records>0));b.classList.toggle('indexed',found.length>0&&!found.some(m=>m.reviewed_records>0||m.benchmark_records>0));}
 if(data.coverage)$('corpus-coverage').textContent=data.coverage;
 render();
}catch(e){$('material-count').textContent=e.message;console.error(e);}
// Preserve old bookmarks to the former root CdSe material page.
if(['#product','#properties','#intuition','#methods','#literature'].includes(location.hash))location.replace('cdse.html'+location.hash);
