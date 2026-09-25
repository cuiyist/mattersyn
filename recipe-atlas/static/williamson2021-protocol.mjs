const routeId='williamson-2021-coni2s4-hot-injection';
const stages={
 'step-1':['Main PDF p9 / printed p9430 · Materials and synthesis, step 1','The shared vacuum/degas vessel scene remains schematic.'],
 'step-2':['Main PDF p9 / printed p9430 · Materials and synthesis, step 2','Precursor amount and Co:Ni orientation statements remain side by side in the audited source-conflict ledger; no charge or ratio is selected here.'],
 'step-3':['Main PDF p9 / printed p9430 · Materials and synthesis, step 3','The shared heated-vessel scene remains schematic.'],
 'step-4':['Main PDF p9 / printed p9430 · Materials and synthesis, step 4','The source heating-rate comparison and approximate rate remain separately disclosed; this scene does not choose between them.'],
 'step-5':['Main PDF p9 / printed p9430 · Materials and synthesis, step 5','The shared injection vessel and syringe scene is illustrative.'],
 'step-6':['Main PDF p9 / printed p9430 · Materials and synthesis, step 6','The shared cooling scene does not imply a measured cooling rate.'],
 'step-7':['Main PDF p9 / printed p9430 · Materials and synthesis, step 7','The shared separation scene does not supply an unreported centrifuge speed.'],
 'step-8':['Main PDF p9 / printed p9430 · Materials and synthesis, step 8','The shared wash/separation scene is illustrative.'],
 'step-9':['Main PDF p9 / printed p9430 · Materials and synthesis, step 9','The shared wash/separation scene is illustrative.'],
 'step-10':['Main PDF p9 / printed p9430 · Materials and synthesis, step 10','The shared redispersion scene is illustrative.'],
};
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
function context(o,r){return r?.record_id===routeId?stages[o?.id]||null:null;}
export function buildWilliamson2021Scene(o,r){const x=context(o,r);return x?{caption:`${x[0]}. Shared MatterSyn operation illustration; equipment geometry is generic and reported parameters appear alongside.`}:null;}
export function decorateWilliamson2021Art(host,o,r){
 const x=context(o,r);if(!host||!x)return host;
 host.classList.add('protocol-art-williamson-source-linked');
 host.setAttribute('aria-label',`${host.getAttribute('aria-label')||o.label}. Source locator: ${x[0]}. ${x[1]}`);
 // The source locator is displayed in the caption below the art.
 return host;
}
export function createWilliamson2021ConditionGrid(o,r){
 const x=context(o,r);if(!x)return null;
 const note=el('div',undefined,'record-note williamson-stage-source-note');
 note.append(el('p',x[1]),el('p','The temperature, duration, atmosphere, and other reported parameters remain in the standard condition grid and full route details.'));
 return note;
}
