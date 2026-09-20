from pathlib import Path
A=Path(__file__).resolve().parent
G=A.parents[2]/'ja212032q/visuals/apparatus'
t=(G/'protocol-template.mjs').read_text('utf-8')
t=t[:t.index('function draw(c)')]+(A/'draw-scenes.mjs').read_text('utf-8')+'\n'+t[t.index('function quantity(q)'):]
t=t.replace('Ghosh','Sommer').replace('ghosh','sommer').replace('2012','2020')
t=t.replace('const v=quantityValue(q),unit=',"const v=/^\\d+(?:\\.\\d+)?(?:\\(\\d+\\))?$|^\\d+\\/\\d+$/.test(q.raw_text||'')?q.raw_text:quantityValue(q),unit=")
t=t.replace("count:'count'","count:'count','angstrom^-1':'Å⁻¹','degC/min':'°C/min',ratio_parts:''")
# Summarize each independent option as one readable group without changing quantities.
old="for(const p of c.option_pointers){const option=r.condition_options?.[Number(p.split('/')[2])];if(!option)throw Error('Missing schedule '+p);for(const[k,q]of Object.entries(option.parameters))rows.push({label:option.label+' · '+(DATA.parameter_labels[k]||k),value:quantity(q),pointer:p+'/parameters/'+k,quantity:q,kind:'alternative_schedule_parameter'});}"
new="for(const p of c.option_pointers){const option=r.condition_options?.[Number(p.split('/')[2])];if(!option)throw Error('Missing schedule '+p);const quantities=Object.entries(option.parameters).map(([k,q])=>({label:DATA.parameter_labels[k]||k.replaceAll('_',' '),value:quantity(q),pointer:p+'/parameters/'+k,quantity:q}));rows.push({label:option.label,value:quantities.map(x=>x.label+': '+x.value).join('; '),pointer:p,quantities,kind:'alternative_schedule_group'});}"
assert old in t;t=t.replace(old,new)
(A/'protocol-template.mjs').write_text(t,'utf-8')
t=(G/'render_previews.py').read_text('utf-8').replace("'/root/norberg2004_extract'","'/root'")
(A/'render_previews.py').write_text(t,'utf-8')
t=(G/'render_and_check.mjs').read_text('utf-8').replace('Ghosh','Sommer').replace('ghosh','sommer').replace('2012','2020').replace('33','31').replace("'/root/norberg2004_extract'","'/root'")
start=t.index("check(scenes.reduce((n,s)=>n+s.rows.filter")
end=t.index("for(const s of scenes)for(const rr",start)
t=t[:start]+'''const expectedParameters=records.reduce((n,r)=>n+r.operations.reduce((a,o)=>a+Object.keys(o.parameters).length,0),0);
const expectedOptions=bindings.reduce((n,b)=>n+b.option_pointers.reduce((a,p)=>a+Object.keys(records.find(r=>r.record_id===b.record_id).condition_options[+p.split('/')[2]].parameters).length,0),0);
check(scenes.reduce((n,s)=>n+s.rows.filter(x=>x.kind==='operation_parameter').length,0)===expectedParameters,'All operation parameters');
check(scenes.reduce((n,s)=>n+s.rows.filter(x=>x.kind==='alternative_schedule_parameter').length,0)===expectedOptions,'All selected source option parameters');
const scene=id=>scenes.find(s=>s.operation_id===id),row=(id,p)=>scene(id).rows.find(r=>r.pointer?.endsWith('/'+p));
check(row('synchrotron-load-acquire','wavelength').value==='0.50054(6) Å','Parenthetic uncertainty retained');
check(row('acs-heat','assumed_time_to_set_point').value.startsWith('≈'),'Assumed ramp approximate');
check(row('lab-xrd-fit','maximum_spherical_harmonic_functions').value.startsWith('≤'),'Upper bound retained');
check(scene('insitu-mix').rows.some(x=>x.value.includes('not NaOH-stock')),'Mixed-reaction context distinct');
check(scene('lab-separate').rows.some(x=>x.value.includes('not pooled')),'No pooled workup');
check(scene('scf-react').rows.some(x=>x.value.includes('380 °C')),'SCF conflict retained');
check(scene('pdf-acquire').rows.some(x=>x.value.includes('no thermal dwell')),'PDF acquisition not heating');
''' + t[end:]
t=t.replace("s.rows.filter(x=>x.kind==='alternative_schedule_parameter').length","s.rows.filter(x=>x.kind==='alternative_schedule_group').reduce((a,g)=>a+g.quantities.length,0)")
t=t.replace("for(const s of scenes)for(const rr of s.rows.filter(x=>x.kind==='alternative_schedule_parameter')){","for(const s of scenes)for(const group of s.rows.filter(x=>x.kind==='alternative_schedule_group'))for(const rr of group.quantities){")
t=t.replace('canonical_parameters:70,alternative_schedule_parameters:10','canonical_parameters:expectedParameters,alternative_schedule_parameters:expectedOptions')
t=t.replace("'Stock/aliquot, retained fractions, separate alternatives, strict threshold and CCD-only nitrogen checks'","'Stock/mixture and independent workup boundaries, uncertainty, upper bound, PDF observation and SCF conflict'")
(A/'render_and_check.mjs').write_text(t,'utf-8')
