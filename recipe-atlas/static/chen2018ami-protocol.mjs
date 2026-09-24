/* Source-bound apparatus illustrations. Coordinates describe drawings, not atoms. */
import {quantityValue} from './quantity-value.mjs';
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
const esc=x=>String(x??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const human=x=>String(x).replaceAll('_',' ');
export function buildChen2018amiScene(o,r){
 if(r.lineage?.source_group!=='chen2018ami')return null;
 let kind='transfer';
 if(o.id==='precursor-mix')kind='glovebox';
 else if(o.id==='acid-add')kind='room-injection';
 else if(o.id==='maturation')kind='stir';
 else if(o.id==='isolate'||o.id==='purify-redisperse')kind='centrifuge';
 else if(o.id==='wash')kind='wash';
 else if(o.id==='dry')kind='vacuum-oven';
 else if(['stock-dry','lead-dry'].includes(o.id))kind='vacuum-flask';
 else if(o.id==='stock-clear'||o.id==='grow')kind='heated-flask';
 else if(['ligand-add','hot-inject'].includes(o.id))kind='heated-injection';
 else if(o.id==='quench')kind='ice-bath';
 else if(r.record_id.endsWith('-film'))kind=o.id==='step-1'?'dropcast':'film-dry';
 else if(r.record_id.endsWith('-wled'))kind=o.id==='step-1'?'blend':o.id==='step-2'?'device':'vacuum-oven';
 else if(r.record_id.endsWith('-surface-scrape'))kind='scrape';
 else if(r.record_id.endsWith('-homogenization'))kind='homogenize';
 return {kind,caption:'Operation illustration for the selected source formulation. Vessel geometry, colors and particle placements are illustrative. Numerical conditions and unknown values follow this operation only; the room-temperature composite route has no invented heating bath.'};
}
function svgScene(kind,o){
 const c={stroke:'#7394a5',glass:'#eaf5f8',solution:'#b6d8dc',solid:'#c9d573',ink:'#153746'};
 const txt=(x,y,t,size=15)=>`<text x="${x}" y="${y}" text-anchor="middle" fill="${c.ink}" font-size="${size}" font-family="system-ui,sans-serif">${esc(t)}</text>`;
 const vessel=`<path d="M185 77H215V148L239 137V100H261V155L239 179C279 207 280 251 253 272C228 293 173 293 147 272C122 252 124 207 164 179L140 155V100H162V137L185 148Z" fill="${c.glass}" stroke="${c.stroke}" stroke-width="3"/><path d="M137 229Q200 216 263 229V259Q244 282 200 281Q153 282 137 259Z" fill="${c.solution}"/><path d="M158 247H242" stroke="white" stroke-width="4" stroke-linecap="round"/>`;
 const vial=(x,color,caption)=>`<rect x="${x-35}" y="120" width="70" height="130" rx="12" fill="${c.glass}" stroke="${c.stroke}" stroke-width="3"/><rect x="${x-31}" y="192" width="62" height="52" rx="5" fill="${color}"/><rect x="${x-39}" y="106" width="78" height="17" rx="5" fill="#b7c9d1"/>${txt(x,278,caption,13)}`;
 const syringe=`<path d="M268 56L235 115" stroke="${c.stroke}" stroke-width="3"/><path d="M264 51L291 67L266 111L239 95Z" fill="#eef9ff" stroke="${c.stroke}" stroke-width="3"/><path d="M282 55L300 24M286 16L312 32" stroke="${c.stroke}" stroke-width="4"/>`;
 const heater=`<rect x="117" y="290" width="166" height="42" rx="9" fill="#d1e0e7" stroke="${c.stroke}" stroke-width="3"/><path d="M147 302H243" stroke="#d6a967" stroke-width="5"/>${txt(200,323,'Heated reaction',12)}`;
 let body='';
 if(kind==='glovebox'){body=`<rect x="45" y="56" width="310" height="239" rx="15" fill="#f0f7fa" stroke="${c.stroke}" stroke-width="3"/>${vial(200,'#dce5d1','Turbid precursor dispersion')}<circle cx="100" cy="219" r="30" fill="none" stroke="${c.stroke}" stroke-width="4"/><circle cx="300" cy="219" r="30" fill="none" stroke="${c.stroke}" stroke-width="4"/>${txt(200,86,'Nitrogen glovebox')}`;}
 else if(['room-injection','stir','wash'].includes(kind)){body=vial(200,kind==='room-injection'?'#dce5d1':c.solid,kind==='wash'?'Isolated precipitate':'Composite dispersion');if(kind==='room-injection')body+=syringe;if(kind==='stir')body+=`<path d="M174 220H226" stroke="#719097" stroke-width="5"/>${txt(200,318,'Stir · room temperature')}`;if(kind==='wash')body+=syringe+txt(95,74,'DMSO wash',13);}
 else if(kind==='centrifuge'){body=`<ellipse cx="120" cy="191" rx="84" ry="57" fill="#e4eef3" stroke="${c.stroke}" stroke-width="4"/><circle cx="120" cy="187" r="34" fill="#d7e4eb" stroke="${c.stroke}" stroke-width="2"/><path d="M87 156L152 218M150 156L88 218" stroke="${c.stroke}" stroke-width="8"/>${vial(292,c.solid,'Recovered material')}${txt(120,280,'Centrifugation')}${txt(200,322,'Fraction sequence: see source conditions',12)}`;}
 else if(kind==='vacuum-oven'){body=`<rect x="73" y="72" width="254" height="223" rx="12" fill="#dce8ee" stroke="${c.stroke}" stroke-width="4"/><rect x="99" y="111" width="202" height="139" rx="8" fill="#f8fcfd" stroke="${c.stroke}" stroke-width="2"/><path d="M126 217Q200 235 274 217" fill="none" stroke="${c.stroke}" stroke-width="6"/><path d="M139 211Q200 196 261 211" fill="none" stroke="${c.solid}" stroke-width="8"/><path d="M327 98H365V51" fill="none" stroke="${c.stroke}" stroke-width="3"/>${txt(200,279,'Vacuum drying',13)}`;}
 else if(['heated-flask','heated-injection','vacuum-flask','ice-bath'].includes(kind)){body=vessel;if(kind==='ice-bath')body+=`<path d="M105 231V308Q200 336 295 308V231" fill="#d2ecf7" fill-opacity=".55" stroke="${c.stroke}" stroke-width="3"/><path d="M124 274L142 254L159 273L141 288Z M248 275L268 256L284 276L268 292Z" fill="white" stroke="#a9ccdc"/>${txt(200,353,'Ice–water bath',13)}`;else body+=heater;if(kind==='heated-injection')body+=syringe;if(kind==='vacuum-flask')body+=`<path d="M171 84L141 45H70" fill="none" stroke="${c.stroke}" stroke-width="4"/>${txt(70,29,'Vacuum',13)}`;}
 else if(kind==='dropcast'||kind==='film-dry'){body=`<path d="M83 230L233 190L325 237L175 281Z" fill="#d9edf5" stroke="${c.stroke}" stroke-width="3"/><path d="M141 237Q195 210 244 231Q223 256 181 255Z" fill="${c.solid}"/>${txt(200,316,'Glass-supported NC film',14)}`;if(kind==='dropcast')body+=syringe;}
 else if(kind==='device'){body=`<rect x="108" y="152" width="184" height="96" rx="8" fill="#d2d9e2" stroke="${c.stroke}" stroke-width="3"/><rect x="152" y="171" width="96" height="54" fill="#639ad2"/><path d="M131 161Q200 101 269 161" fill="${c.solid}" stroke="#adbf69" stroke-width="2"/>${txt(200,287,'Phosphor + silicone on blue chip',13)}`;}
 else if(kind==='blend'){body=vial(126,c.solid,'Green composite')+vial(276,'#dbaa8c','Red phosphor + binder');}
 else if(kind==='scrape'){body=`<path d="M90 257Q170 180 260 260Z" fill="${c.solid}" stroke="${c.stroke}" stroke-width="2"/><path d="M231 216L304 136" stroke="#8699a6" stroke-width="8"/>${txt(200,312,'Surface fraction only',14)}`;}
 else if(kind==='homogenize'){body=vial(115,c.solid,'S1')+vial(200,c.solid,'S2.5')+vial(285,c.solid,'S4')+txt(200,328,'Mix within each sample; do not pool',13);}
 else body=vial(200,c.solution,'Source-defined specimen');
 return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 380" role="img" aria-label="${esc(o.label)}"><rect width="400" height="380" rx="20" fill="#f8fbfd"/>${body}</svg>`;
}
export function createChen2018amiArt(o,r){const s=buildChen2018amiScene(o,r);if(!s)return null;const host=el('div',undefined,'protocol-art chen2018ami-art');host.dataset.scene=s.kind;host.innerHTML=svgScene(s.kind,o);return host;}
function quantity(q){if(!q)return 'Not reported';const v=quantityValue(q);const unit=({degC:'°C',uL:'µL',mmol:'mmol'})[q.unit]||q.unit||'';if(v===null)return q.raw_text?`${q.raw_text} (numerical value not reported)`:q.qualifier||'Not reported';return `${q.approximate?'≈':''}${v} ${unit}`;}
export function createChen2018amiConditionGrid(o,r){if(!buildChen2018amiScene(o,r))return null;const dl=el('dl',undefined,'protocol-condition-grid');for(const [key,q] of Object.entries(o.parameters)){const row=el('div');row.append(el('dt',human(key)),el('dd',quantity(q)));dl.append(row);}const row=el('div');row.append(el('dt','Environment'),el('dd',o.environment?.value||'Not reported'));dl.append(row);return dl;}
