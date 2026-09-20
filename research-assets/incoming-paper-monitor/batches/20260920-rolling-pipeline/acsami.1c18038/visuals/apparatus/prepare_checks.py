from pathlib import Path
A=Path(__file__).resolve().parent
old=A.parents[2]/'acs.inorgchem.7b01711/visuals/apparatus'
# Reuse only the generic execution/render harness; scientific checks below are new.
s=(old/'render_and_check.mjs').read_text(encoding='utf-8')
s=s.replace('Morrison2017','Lian2021').replace('morrison2017','lian2021').replace('Morrison 2017','Lian 2021').replace('Morrison et al. 2017','Lian et al. 2021').replace('reported_observation_or_acquisition','source_context')
start=s.index("check(scenes.length===24")
end=s.index("save('rendered-scenes.json',scenes)")
s=s[:start]+'''check(scenes.length===21,'Exactly 21 operations');
check(scenes.reduce((n,s)=>n+s.rows.filter(x=>x.kind==='operation_parameter').length,0)===34,'34 operation parameters');
check(scenes.reduce((n,s)=>n+s.rows.filter(x=>x.kind==='source_context').length,0)===7,'Five mass ratios plus two k-meshes');
const scene=id=>scenes.find(s=>s.operation_id===id),row=(id,label)=>scene(id).rows.find(r=>r.label===label);
check(row('nc-dissolve-filter','DMF solvent charge').value==='2000 µL','Whole-stock solvent charge');
check(row('nc-inject','Precursor-solution aliquot').value==='500 µL','Only aliquot injected');
check(row('spin-feed','DMF solvent charge').value==='1000 µL','Separate spin-feed stock');
check(row('spin-deposit','Precursor-solution aliquot').value==='200 µL','Separate coating aliquot');
check(row('dft-relax','Force stopping criterion').value==='<0.01 eV/Å','Strict convergence bound');
check(row('dft-relax','Compound A k-point mesh').value==='4x4x4','Compound A mesh');
check(row('dft-relax','Compound B k-point mesh').value==='2x4x4','Compound B mesh');
check(scene('film-cast').description.includes('film is retained'),'Peeled film is product');
check(bindings.find(x=>x.operation_id==='film-cast').retained_fraction==='composite-film','Canonical retained film');
check(scene('bulk-xps-tga').description.includes('Nitrogen is assigned only to TGA'),'N2 scoped to TGA only');
check(scene('nc-plqe').description.includes('dried nanocrystal powder'),'Powder PLQE scope');
check(scene('nc-inject').description.includes('no nanocrystal growth temperature'),'No inherited room temperature');
''' +s[end:]
s=s.replace('All 24 canonical operations','All 21 canonical operations').replace('canonical_parameters:62','canonical_parameters:34').replace('additional_observation_acquisition_rows:8','additional_source_context_rows:7').replace('Explicit TEM branch, 2 h observation and 100(2) K acquisition checks','Stock/aliquot, film retention, TGA-only nitrogen, powder PLQE and strict DFT force checks')
(A/'render_and_check.mjs').write_text(s,encoding='utf-8')
(A/'render_previews.py').write_text((old/'render_previews.py').read_text(encoding='utf-8'),encoding='utf-8')
print('Prepared local generic render harness and Lian-specific checks.')
