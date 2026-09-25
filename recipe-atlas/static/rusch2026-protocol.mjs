/* Author candidate. Drawn geometry is illustrative, never atomic coordinates. */
const esc=x=>String(x??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;');
export function buildRusch2026Scene(o,r){
 if(r.lineage?.source_group!=='rusch2026')return null;
 let kind=o.action;
 if(o.id==='bi-stock-vacuum')kind='vacuum-heat';
 if(o.id==='bi-stock-nitrogen')kind='nitrogen-heat';
 if(o.id==='bi-stock-cool')kind='stock';
 if(o.id==='hi-dissolve')kind='hi-heat';
 return {kind,caption:'Source-specific operation schematic. Vessel geometry and colors are illustrative. Conditions, fractions and unresolved quantities come from the selected operation. The illustration does not establish atomic structure, particle-size statistics or an unreported apparatus design.'};
}
export function rusch2026SVG(o,r){
 const s=buildRusch2026Scene(o,r);if(!s)return null;
 const stroke='#7193a5',glass='#e9f3f7',liquid=o.stage==='precursor_preparation'?'#e4eff5':'#efd5ae',red=r.material.formula.includes('bromide')?'#d8b946':r.material.formula.includes('chloride')?'#e9edf3':'#b5583f';
 const text=(x,y,t)=>`<text x="${x}" y="${y}" text-anchor="middle" font-family="system-ui,sans-serif" font-size="15" fill="#153746">${esc(t)}</text>`;
 const vial=`<path d="M153 84H247V256Q200 281 153 256Z" fill="${glass}" stroke="${stroke}" stroke-width="3"/><path d="M157 184H243V253Q200 274 157 253Z" fill="${liquid}"/>`;
 const syringe=`<g transform="translate(250 20) rotate(28)"><path d="M0 0V30M-13 0H13M-10 30H10V85H-10ZM0 85V124" fill="${glass}" stroke="${stroke}" stroke-width="3"/></g>`;
 const heater=`<rect x="133" y="274" width="134" height="30" rx="6" fill="#c5dce7" stroke="${stroke}" stroke-width="3"/><path d="M162 285H238" stroke="#d4a553" stroke-width="5"/>`;
 const plates=`<path d="M177 220L212 211L229 232L191 242Z M164 247L195 241L209 259L178 265Z" fill="${red}" opacity=".85"/>`;
 let body=vial;
 if(['vacuum-heat','nitrogen-heat','hi-heat'].includes(s.kind))body+=heater+text(200,52,s.kind==='vacuum-heat'?'Vacuum':s.kind==='nitrogen-heat'?'Nitrogen':'Boiling aqueous HI');
 else if(['inject','add_slowly'].includes(s.kind))body+=syringe+plates+text(200,323,s.kind==='inject'?'Rapid precursor addition':'Controlled precursor addition');
 else if(s.kind==='wash')body=`<ellipse cx="111" cy="179" rx="76" ry="58" fill="${glass}" stroke="${stroke}" stroke-width="3"/><circle cx="111" cy="179" r="27" fill="#c5dce7"/><path d="M76 143L146 215M146 143L76 215" stroke="${stroke}" stroke-width="9"/><g transform="translate(95 0)">${vial}${plates}</g>${text(105,275,'Centrifuge')}${text(292,304,'Retained solid')}`;
 else if(o.id==='hi-cool')body=vial+plates+text(200,52,'Slow cooling')+text(200,323,'Temperature and rate: not reported');
 else if(s.kind==='evaporate')body=vial+plates+`<path d="M146 80H254" stroke="${stroke}" stroke-width="8" stroke-dasharray="9 5"/><path d="M182 72Q172 56 182 43M217 72Q207 56 217 43" fill="none" stroke="${stroke}" stroke-width="2"/>`+text(200,323,o.id==='hi-cool'?'Slow cooling':'Slow solvent evaporation');
 else if(s.kind==='spin_coat')body=`<ellipse cx="200" cy="197" rx="122" ry="60" fill="${glass}" stroke="${stroke}" stroke-width="4"/><ellipse cx="200" cy="187" rx="62" ry="25" fill="#cadbe4"/><path d="M150 181L232 162L251 192L169 212Z" fill="${red}" opacity=".8"/><path d="M100 164Q174 110 286 168M274 157L287 168L271 172" fill="none" stroke="${stroke}" stroke-width="4"/>${text(200,300,'Spin coating')}`;
 else if(s.kind==='sonicate')body=`<rect x="92" y="138" width="216" height="137" rx="12" fill="${glass}" stroke="${stroke}" stroke-width="3"/><path d="M117 165H283M171 177L233 158L250 219L188 238" fill="none" stroke="${stroke}" stroke-width="3"/><path d="M122 258Q147 231 172 258T222 258T272 258" fill="none" stroke="#74b2cb" stroke-width="3"/>${text(200,321,'Sequential cleaning baths')}`;
 else if(s.kind==='dissolve')body+=syringe+text(200,323,'Dissolution endpoint: see conditions');
 else if(s.kind==='store'||s.kind==='stock')body+=`<rect x="147" y="73" width="106" height="15" rx="4" fill="#abc1cc"/>`+text(200,323,s.kind==='stock'?'Bismuth precursor solution':'Product stored under hexane');
 else if(s.kind==='dry')body=`<rect x="105" y="179" width="190" height="12" rx="4" fill="#bacfd9"/><path d="M130 173L255 173" stroke="${red}" stroke-width="5"/><path d="M159 155Q144 128 159 102M198 155Q183 128 198 102M237 155Q222 128 237 102" fill="none" stroke="${stroke}" stroke-width="3"/>${text(200,270,'Drying conditions: source notes')}`;
 else body+=text(200,323,'Precursor mixing');
 return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 360" role="img" aria-label="${esc(o.label)}"><rect width="400" height="360" rx="20" fill="#f7fbfe"/>${body}</svg>`;
}
export function createRusch2026Art(o,r){const svg=rusch2026SVG(o,r);if(!svg)return null;const host=document.createElement('div');host.className='protocol-art rusch2026-art';host.innerHTML=svg;const image=host.querySelector('svg');image.style.width='100%';image.style.height='100%';image.style.maxHeight='330px';return host;}

// Preserve every reported condition, qualifier and whole-charge/aliquot distinction.
export function createRusch2026ConditionGrid(o,r){
 const dl=document.createElement('dl');dl.className='protocol-condition-grid';
 const human=x=>x.replaceAll('_',' '), value=q=>q?.value??(q?.minimum!==null&&q?.maximum!==null&&q?.minimum!==undefined?`${q.minimum}–${q.maximum}`:null);
 const fmt=q=>[(value(q)===null?'Not reported':(q.approximate?'≈':'')+value(q)),q?.unit||'',q?.qualifier||'',q?.basis||''].filter(Boolean).join(' · ');
 const row=(k,v)=>{const d=document.createElement('div'),dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=k;dd.textContent=v;d.append(dt,dd);dl.append(d);};
 for(const [k,q]of Object.entries(o.parameters||{}))row(human(k),fmt(q));
 row('Environment',o.environment?.value||o.environment?.note||'Not reported');
 row('Endpoint',o.endpoint?.value||o.endpoint?.note||'Not reported');
 for(const id of o.inputs||[]){const m=r.materials.find(x=>x.id===id);if(m)for(const[k,q]of Object.entries(m.quantities||{}))row(m.name+' · '+human(k),fmt(q));}
 if(o.retained_fraction)row('Retained fraction',human(o.retained_fraction));
 return dl;
}
