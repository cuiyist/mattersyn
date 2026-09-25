const stages={
  'solvothermal-reaction':{asset:'assets/reader-schematics/li2000cu2sns3/autoclave.svg',caption:'Source-bound conditions: sealed 100 mL Teflon-lined autoclave; ethylenediamine fill up to 90%; 140–180 °C for 15 h. Pressure and dimensions are unreported. Vessel drawing is conceptual.'},
  'vacuum-dry':{asset:'assets/reader-schematics/vacuum-drying-chamber.svg',caption:'Source reports vacuum drying at 60 °C for 4 h. Chamber construction, vacuum pressure and sample-bed geometry are not reported; illustration is conceptual.'}
};
export function buildLi2000cu2sns3Scene(o,r){if(r.lineage?.source_group!=='li2000cu2sns3')return null;const s=stages[o.id];return s?{asset:s.asset,caption:s.caption}:null;}
export function createLi2000cu2sns3Art(o,r,prefix=''){const s=buildLi2000cu2sns3Scene(o,r);if(!s)return null;const d=document.createElement('div'),img=document.createElement('img');d.className='protocol-art protocol-art-li2000cu2sns3';img.src=prefix+s.asset;img.alt=o.label+' · conceptual source-stage illustration';img.loading='lazy';img.style.width='100%';img.style.height='100%';img.style.objectFit='contain';d.append(img);return d;}
