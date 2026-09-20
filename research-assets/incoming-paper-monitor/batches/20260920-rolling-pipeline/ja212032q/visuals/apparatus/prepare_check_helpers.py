from pathlib import Path
A=Path(__file__).resolve().parent;old=A.parents[2]/'acsami.1c18038/visuals/apparatus'
text=(old/'render_and_check.mjs').read_text(encoding='utf-8').replace('Lian2021','Ghosh2012').replace('lian2021','ghosh2012').replace('Lian et al. 2021','Ghosh et al. 2012').replace('Lian 2021','Ghosh 2012')
start=text.index("check(scenes.length===21")
end=text.index("save('rendered-scenes.json'")
text=text[:start]+'''check(scenes.length===33,'Exactly 33 operations');
check(scenes.reduce((n,s)=>n+s.rows.filter(x=>x.kind==='operation_parameter').length,0)===70,'70 exact operation parameters');
check(scenes.reduce((n,s)=>n+s.rows.filter(x=>x.kind==='alternative_schedule_parameter').length,0)===10,'10 exact alternative schedule parameters');
const scene=id=>scenes.find(s=>s.operation_id===id),row=(id,p)=>scene(id).rows.find(r=>r.pointer?.endsWith('/'+p));
check(row('large-feed','initial_growth_time').value.startsWith('≈'),'Initial 10-minute growth remains approximate');
check(row('shell-charge','washed_core_amount').value.startsWith('≈'),'Core amount remains approximate');
check(row('shell-cycles','post_cadmium_anneal').quantity.value===2.5,'Preferred post-Cd 2.5 h');
check(scene('compare-anneals').rows.filter(r=>r.kind==='alternative_schedule_parameter').length===10,'Five independent paired schedules');
check(row('single-analyze','prose_on_time_threshold').value.startsWith('>'),'Strict >99% prose threshold');
check(row('single-acquire','total_measurement_time').value.startsWith('>'),'Greater than one hour');
check(Object.keys(records.find(r=>r.record_id.endsWith('ftir-procedure')).operations[0].parameters).join()==='washing_cycles','Preparation has only wash control');
check(Object.keys(records.find(r=>r.record_id.endsWith('xrd-procedure')).operations[0].parameters).length===0,'No scan controls on deposition');
check(bindings.find(b=>b.operation_id==='shell-withdraw').retained_fraction==='remaining-shell-growth','Remaining growth mixture retained');
check(scene('single-acquire').rows.some(r=>r.value.includes('CCD detector')&&r.value.includes('not a specimen')),'Nitrogen is detector cooling only');
check(scene('core-control-wash').description.includes('Upstream synthesis')&&scene('core-control-wash').rows.some(r=>r.value.includes('does not inherit')),'Seven-nanometer control does not inherit core synthesis');
for(const s of scenes)for(const rr of s.rows.filter(x=>x.kind==='alternative_schedule_parameter')){
 const r=records.find(x=>x.record_id===s.record_id),parts=rr.pointer.split('/'),q=r.condition_options[+parts[2]].parameters[parts[4]];
 check(JSON.stringify(rr.quantity)===JSON.stringify(q),'Exact alternative canonical quantity');
}
''' +text[end:]
text=text.replace('All 21 canonical operations','All 33 canonical operations').replace('canonical_parameters:34,additional_source_context_rows:7','canonical_parameters:70,alternative_schedule_parameters:10').replace("'Stock/aliquot, film retention, TGA-only nitrogen, powder PLQE and strict DFT force checks'","'Stock/aliquot, retained fractions, separate alternatives, strict threshold and CCD-only nitrogen checks'")
(A/'render_and_check.mjs').write_text(text,encoding='utf-8')
(A/'render_previews.py').write_text((old/'render_previews.py').read_text(encoding='utf-8'),encoding='utf-8')
print('Private Ghosh check/preview helpers created; old source files unchanged.')
