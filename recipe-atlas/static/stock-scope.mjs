const el=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
export function stockScope(stock,record){
 const host=el('div'),raw=stock.scope;
 if(record.lineage?.source_group!=='evans2010'){host.append(el('p',raw));return host;}
 let fields,end=-1;
 for(let i=0;i<raw.length;i++){if(raw[i]!=='}')continue;try{fields=JSON.parse(raw.slice(0,i+1));end=i+1;break;}catch{}}
 if(!fields||typeof fields!=='object'||Array.isArray(fields)){host.append(el('p',raw));return host;}
 const list=el('dl');list.className='fact-list';const identifiers=[];
 for(const [key,v] of Object.entries(fields)){
  if(['id','source_unit_id'].includes(key)){identifiers.push(key+': '+v);continue;}
  const row=el('div'),value=v===null?'Not explicitly reported':typeof v==='object'?JSON.stringify(v):String(v).replaceAll('_',' ');
  row.append(el('dt',key.replaceAll('_',' ')),el('dd',value));list.append(row);
 }
 host.append(list,el('p',raw.slice(end).trim()));const provenance=el('details');provenance.append(el('summary','Stock provenance identifiers'),el('p',identifiers.join('; ')));host.append(provenance);return host;
}
