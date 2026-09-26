export const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined&&text!==null)n.textContent=text;if(cls)n.className=cls;return n;};
export const siteURL=path=>new URL(path,import.meta.url).href;
export function link(label,path,cls){const a=el('a',label,cls);a.href=/^(https?:|#)/.test(path)?path:siteURL(path);return a;}
export function button(label,fn,cls){const b=el('button',label,cls);b.type='button';b.onclick=fn;return b;}
export function disclosure(label,...children){const d=el('details');d.append(el('summary',label),...children.filter(Boolean));return d;}
export function human(s){return String(s||'').replaceAll('_',' ');}
export function componentScopeLabel(material){
 if(!material?.component_only)return '';
 const labels={phase_mixture:'a source-reported phase mixture',core_shell:'a core/shell heterostructure',heterostructure:'a heterostructure',composite:'a composite product',alloy:'an alloy',unresolved:'a product with unresolved architecture'};
 const architectures=[...new Set(material.component_architectures||[])];
 const phrases=architectures.map(value=>labels[value]).filter(Boolean);
 if(!phrases.length)return 'Component within a source-defined product';
 return 'Component within '+phrases.join(' and ');
}
export function section(id,n,title,subtitle){const s=el('section',undefined,'reader-section');s.id=id;const h=el('div',undefined,'reader-section-heading');h.append(el('span',n,'reader-number'),el('h2',title));s.append(h);if(subtitle)s.append(el('p',subtitle,'reader-subtitle'));return s;}
export function recordURL(rid,view='data'){return siteURL('records/'+encodeURIComponent(rid)+'.html')+(view?'?view='+view:'');}
export function sourceURL(source){return source?.url||('https://doi.org/'+source?.doi);}
export const isEquipment=m=>m.role==='apparatus'||/\b(burette|erlenmeyer|filter paper|filter membrane|glassware|pipette|syringe|crucible|centrifuge tube)\b/i.test(m.name||'');
export function shortMethod(s){return human(s).replace(/ with source-paired.*$/i,'').replace(/ with source-linked.*$/i,'');}
export function sentence(text){const t=String(text||'').trim();const match=t.match(/^.*?[.!?](?=\s+[A-Z]|$)/s);return match?match[0]:t;}
export function badge(text,cls=''){return el('span',text,'reader-badge '+cls);}
// Older reviewed records used optical for measured absorption/emission figures.
export function figureMatchesCategory(figure,category){
 const normalize=value=>({optical:'property',properties:'property'})[value]||value;
 const wanted=normalize(category);
 const categories=[figure.category,...(Array.isArray(figure.categories)?figure.categories:[])].map(normalize);
 return categories.includes(wanted)||(wanted==='structure'&&categories.includes('composition'));
}
