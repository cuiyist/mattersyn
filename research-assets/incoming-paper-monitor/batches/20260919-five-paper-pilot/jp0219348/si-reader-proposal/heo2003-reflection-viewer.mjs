const el=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e;};
const cell=(r,k)=>r.cells.find(c=>c.evidence.column_key===k);
export function selectReflections(data,{query='',page=0,kind='all'}={}){
 const q=query.trim().toLowerCase(),hkl=q.match(/^\(?\s*(-?\d+)\s*[, ]+\s*(-?\d+)\s*[, ]+\s*(-?\d+)\s*\)?$/);
 return data.rows.filter(r=>{
  if(Number(page)&&r.cells[0].evidence.pdf_page!==Number(page))return false;
  if(q&&(hkl?!r.hkl.every((v,i)=>v===Number(hkl[i+1])):!r.row_id.toLowerCase().includes(q)&&!Object.values(r.raw_cells).some(v=>String(v).toLowerCase().includes(q))))return false;
  const obs=cell(r,'Fobs2').numeric_value;
  if(kind==='negative'&&!(obs!==null&&obs<0))return false;
  if(kind==='zero'&&obs!==0)return false;
  if(kind==='unresolved'&&!r.cells.some(c=>c.sign_status==='unresolved_from_retained_scan'))return false;
  return true;
 });
}
export async function mountHeoReflections(host,options={}){
 const dataUrl=options.dataUrl??new URL('assets/heo2003/heo2003-reflections.json',import.meta.url),tsvUrl=options.tsvUrl??new URL('assets/heo2003/heo2003-reflections.tsv',import.meta.url);
 const data=options.data??await fetch(dataUrl).then(r=>{if(!r.ok)throw Error('Reflection table unavailable');return r.json();});
 const section=el('section');section.className='heo-reflections';section.append(el('h3','Supporting reflection table'),el('p','Observed and calculated structure factors squared with ESDs · source In66-X · 1,209 rows. The two unresolved signs remain null; 137 negative observed values and one zero are preserved.'));
 const warnings=el('details'),summary=el('summary','Table provenance and uncertainty');warnings.append(summary);for(const s of data.scientific_limits)warnings.append(el('p',s));
 section.append(el('p','Raw source tokens are shown below. [sign_unresolved] is an editorial label for an ambiguous sign, not a printed value. The o-like marker is retained without assigning an acceptance or rejection meaning.'),warnings);
 const controls=el('div');controls.className='protocol-controls';const search=el('input');search.type='search';search.placeholder='Search h k l, row ID or raw token';search.setAttribute('aria-label','Search reflection table');
 const page=el('select');page.setAttribute('aria-label','Source SI page');page.append(new Option('All source pages','0'));for(let i=1;i<=14;i++)page.append(new Option('SI page '+i,String(i)));
 const kind=el('select');kind.setAttribute('aria-label','Reflection value filter');for(const [t,v] of [['All reflections','all'],['Negative observed values','negative'],['Zero observed value','zero'],['Unresolved signs','unresolved']])kind.append(new Option(t,v));controls.append(search,page,kind);
 const count=el('p');count.setAttribute('aria-live','polite');const wrap=el('div');wrap.style.overflowX='auto';const table=el('table');table.style.width='100%';const th=el('thead'),tr=el('tr');for(const title of ['Source row','h','k','l','Fcal²','Fobs²','σ(Fobs²)','Marker','Details'])tr.append(el('th',title));th.append(tr);const body=el('tbody');table.append(th,body);wrap.append(table);
 const pagination=el('div');pagination.className='protocol-controls';const prev=el('button','Previous'),next=el('button','Next');prev.type=next.type='button';pagination.append(prev,next);
 const detail=el('div');detail.setAttribute('aria-live','polite');const links=el('div');links.className='protocol-controls';for(const [label,url] of [['Download typed JSON',dataUrl],['Download raw/numeric TSV',tsvUrl],['Source paper','https://doi.org/10.1021/jp0219348']]){const a=el('a',label);a.href=url;if(!String(url).startsWith('https:'))a.download='';links.append(a);}
 section.append(controls,count,wrap,pagination,detail,links);host.append(section);let offset=0;const limit=50;
 function render(){const rows=selectReflections(data,{query:search.value,page:page.value,kind:kind.value});offset=Math.min(offset,Math.max(0,Math.floor((rows.length-1)/limit)*limit));body.replaceChildren();detail.replaceChildren();
  for(const r of rows.slice(offset,offset+limit)){const row=el('tr');row.dataset.rowId=r.row_id;for(const v of [r.row_id,...['h','k','l','Fcal2','Fobs2','sigma_Fobs2','marker'].map(k=>r.raw_cells[k])])row.append(el('td',String(v)));const td=el('td'),button=el('button','Inspect row');button.type='button';button.onclick=()=>{detail.replaceChildren(el('h4',r.row_id+' · source details'));for(const c of r.cells){const isMarker=c.evidence.column_key==='marker';const text=c.evidence.printed_column_label+': '+c.raw_text+(isMarker?'; literal marker retained; meaning not assigned':'; parsed value: '+(c.numeric_value===null?'null (not assigned)':c.numeric_value));detail.append(el('p',text),el('small',c.evidence.locator));if(c.uncertainty_note)detail.append(el('p',c.uncertainty_note));if(c.signed_value_candidates)detail.append(el('p','Possible signed values: '+c.signed_value_candidates.join(' or ')));if(c.editorial_annotation)detail.append(el('p',c.editorial_annotation));}};td.append(button);row.append(td);if(r.cells.some(c=>c.sign_status==='unresolved_from_retained_scan'))row.className='unresolved';body.append(row);}
  count.textContent=`${rows.length.toLocaleString()} matched rows · showing ${rows.length?offset+1:0}–${Math.min(offset+limit,rows.length)}. Source order is preserved.`;prev.disabled=offset===0;next.disabled=offset+limit>=rows.length;
 }
 search.oninput=page.onchange=kind.onchange=()=>{offset=0;render();};prev.onclick=()=>{offset-=limit;render();};next.onclick=()=>{offset+=limit;render();};render();return section;
}
