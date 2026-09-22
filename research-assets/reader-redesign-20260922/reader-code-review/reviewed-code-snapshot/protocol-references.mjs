import {chemicalRegistry,chemicalEntry,openChemical} from './chemical-viewer.mjs';
import {el,button,isEquipment,recordURL,link} from './reader-utils.mjs';
let equipmentDialog;
export function showEquipment(material){
 if(!equipmentDialog){equipmentDialog=el('dialog',undefined,'reader-equipment-dialog');document.body.append(equipmentDialog);}
 const header=el('header');header.append(el('h2',material.name),button('Close ×',()=>equipmentDialog.close()));
 const art=el('div',undefined,'equipment-illustration');const name=material.name.toLowerCase();
 const drawing=/paper|membrane/.test(name)?'<ellipse cx="160" cy="135" rx="105" ry="60" fill="#faf2dc" stroke="#c0a56b" stroke-width="3"/><path d="M60 127Q160 172 260 127M92 100L220 165M78 115L197 178M129 82L247 150" stroke="#dac99f" fill="none"/>':/burette/.test(name)?'<path d="M144 20H176V175L164 195V240" fill="#e8f4fa" stroke="#67859b" stroke-width="3"/><path d="M149 75H171V170H149Z" fill="#8fbfd0"/><path d="M149 35H161M149 48H161M149 61H161M149 87H161M149 100H161M149 113H161M149 126H161M149 139H161" stroke="#67859b"/><path d="M137 196H185" stroke="#56778c" stroke-width="7"/>':'<path d="M138 35H182V104L250 224Q260 248 160 248Q60 248 70 224L138 104Z" fill="#edf6fa" stroke="#7696a9" stroke-width="3"/><path d="M110 160H210L244 222Q251 243 160 243Q69 243 76 222Z" fill="#8bbdc7" opacity=".6"/><path d="M145 42V108L84 223" stroke="white" stroke-width="5" fill="none"/>';
 art.innerHTML='<svg viewBox="0 0 320 280" role="img" aria-label="Schematic equipment illustration">'+drawing+'</svg>';
 equipmentDialog.replaceChildren(header,art,el('p','Equipment schematic · geometry and colors are illustrative.'));if(!equipmentDialog.open)equipmentDialog.showModal();
}
export async function mountProtocolReferences(host,r,o){
 const data=await chemicalRegistry();if(!host.isConnected)return;
 const inventory=new Map(r.materials.map(m=>[m.id,m]));
 const ids=new Set([...(o.inputs||[]),...(o.optional_inputs||[])]);
 for(const stock of r.stocks||[])if(ids.has(stock.id))for(const c of stock.components)ids.add(c.material_id);
 const matches=new Map();
 for(const m of r.materials){
  for(const text of [m.name,m.formula,...(/^[A-Za-z][A-Za-z0-9]{1,8}$/.test(m.id)?[m.id]:[])].filter(Boolean)){
   const key=text.toLowerCase();if(matches.has(key)&&matches.get(key)?.id!==m.id)matches.set(key,null);else if(!matches.has(key))matches.set(key,m);
  }
 }
 const names=[...matches.keys()].filter(k=>k.length>1&&matches.get(k)).sort((a,b)=>b.length-a.length);
 const escape=s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
 const pattern=names.length?new RegExp('(?<![A-Za-z0-9])('+names.map(escape).join('|')+')(?![A-Za-z0-9])','gi'):null;
 const onChemical=m=>{const entry=chemicalEntry(data,r.record_id,m.id);return isEquipment(m)?()=>showEquipment(m):entry?()=>openChemical(entry):null;};
 if(pattern){const walker=document.createTreeWalker(host,NodeFilter.SHOW_TEXT);const nodes=[];while(walker.nextNode())if(!walker.currentNode.parentElement.closest('button,a,summary,details,svg'))nodes.push(walker.currentNode);
  for(const node of nodes){const text=node.textContent;pattern.lastIndex=0;let match,last=0,found=false;const fragment=document.createDocumentFragment();while((match=pattern.exec(text))){const m=matches.get(match[0].toLowerCase());if(!m)continue;const elemental=/^[A-Z][a-z]?$/.test(m.formula||'');if(elemental&&match[0].toLowerCase()===m.formula.toLowerCase()&&match[0]!==m.formula)continue;const fn=onChemical(m);if(!fn)continue;found=true;fragment.append(document.createTextNode(text.slice(last,match.index)),button(match[0],fn,'inline-chemical'));last=match.index+match[0].length;}if(found){fragment.append(document.createTextNode(text.slice(last)));node.replaceWith(fragment);}}
 }
 const items=[...ids].map(id=>inventory.get(id)).filter(Boolean);if(!items.length)return;
 const panel=el('div',undefined,'protocol-chemical-links');panel.setAttribute('aria-label','Chemicals and equipment in this step');
 for(const m of items){const fn=onChemical(m);panel.append(fn?button(m.name,fn,'reader-chip'):link(m.name+' · identity',recordURL(r.record_id)+'#precursors','reader-chip'));}
 const controls=host.querySelector('.protocol-controls');controls?host.insertBefore(panel,controls):host.append(panel);
}
