const byId=id=>document.getElementById(id);
let records=[],page=0;const pageSize=12;const materialScope=new URLSearchParams(location.search).get('material');
function link(text,href){const a=document.createElement('a');a.textContent=text;a.href=href;return a;}
function render(){
 const query=byId('record-search').value.trim().toLowerCase(),family=byId('family-filter').value,type=byId('type-filter').value;
 const matched=records.filter(r=>(!materialScope||r.formula===materialScope||r.components?.includes(materialScope))&&(!query||[r.title,r.formula,r.method,r.source_doi].join(' ').toLowerCase().includes(query))&&(!family||r.formula===family)&&(type==='all'||(type==='recipes'&&!['procedure','observation'].includes(r.record_type))||(type==='pairs'&&r.pair_ids?.length)||(type==='observation'&&r.record_type==='observation')||(type==='procedure'&&r.record_type==='procedure')));
 const pages=Math.max(1,Math.ceil(matched.length/pageSize));page=Math.min(page,pages-1);const host=byId('catalog-results');host.replaceChildren();
 for(const r of matched.slice(page*pageSize,(page+1)*pageSize)){
  const card=document.createElement('article');card.className='dataset-card';
  const meta=document.createElement('div');meta.className='record-meta';const material=document.createElement('span');material.textContent=r.formula+' · '+r.method;
  const badge=document.createElement('span');badge.className='record-badge';badge.textContent=r.collection==='published_benchmark'?'Published experimental row':r.record_type.replaceAll('_',' ');meta.append(material,badge);
  const heading=document.createElement('h2');heading.append(link(r.title,r.page_url));
  const summary=document.createElement('p');summary.textContent=r.pair_ids?.length?r.pair_ids.length+' documented recipe–structure pair'+(r.pair_ids.length===1?'':'s')+'.':r.collection==='published_benchmark'?'Published recipe parameters and optical measurements; particle structure is not supplied in this experimental row.':'Source-linked recipe or supporting evidence; see the record for available structural information.';
  const bottom=document.createElement('div');bottom.className='record-bottom';const citation=document.createElement('span');citation.textContent=r.source_year+' · '+r.source_doi;bottom.append(citation,link('Inspect record →',r.page_url));card.append(meta,heading,summary,bottom);host.append(card);
 }
 if(!matched.length){const note=document.createElement('p');note.className='record-notice';note.textContent='No records match these filters.';host.append(note);}
 byId('record-count').textContent=matched.length+' matching records'+(materialScope?' · '+materialScope+' and component systems':'');byId('page-label').textContent='Page '+(page+1)+' of '+pages;byId('page-prev').disabled=page===0;byId('page-next').disabled=page+1>=pages;
}
try{
 const response=await fetch('data/dataset-manifest.json');if(!response.ok)throw Error('Could not load dataset manifest');const data=await response.json();records=data.records.sort((a,b)=>a.formula.localeCompare(b.formula)||a.title.localeCompare(b.title));render();
 for(const id of ['record-search','family-filter','type-filter'])byId(id).addEventListener(id==='record-search'?'input':'change',()=>{page=0;render();});
 byId('page-prev').addEventListener('click',()=>{page--;render();});byId('page-next').addEventListener('click',()=>{page++;render();});
}catch(error){byId('record-count').textContent=error.message;console.error(error);}
