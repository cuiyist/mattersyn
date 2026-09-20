from pathlib import Path
A=Path(__file__).resolve().parent
T=A.parents[2]/'acs.cgd.9b01519/visuals/apparatus'
t=(T/'protocol-template.mjs').read_text('utf-8')
t=t[:t.index('function draw(c)')]+(A/'draw-scenes.mjs').read_text('utf-8')+'\n'+t[t.index('function quantity(q)'):]
t=t.replace('Sommer','Matuhina').replace('sommer','matuhina').replace('2020','2023')
t=t.replace("fold:'fold'","fold:'fold',uL:'µL',uW:'µW','ug/L':'µg/L',degree_2theta:'° 2θ','Mohm cm':'MΩ cm'")
(A/'protocol-template.mjs').write_text(t,'utf-8')
(A/'render_previews.py').write_text((T/'render_previews.py').read_text('utf-8'),'utf-8')
t=(T/'render_and_check.mjs').read_text('utf-8').replace('Sommer','Matuhina').replace('sommer','matuhina').replace('2020','2023').replace('31','39')
start=t.index("check(row('synchrotron-load-acquire'")
end=t.index('for(const s of scenes)for(const group',start)
t=t[:start]+'''check(row('cs-reactivate','pre_injection_degassing_duration').value==='≥30 min','Lower bound retained');
check(row('nc-grow-quench','hold_after_injection').value==='5 s','Growth hold duration');
check(row('xrd-acquire','time_per_step').value==='17 s','Acquisition duration');
check(scene('nc-inject').rows.filter(x=>x.kind==='alternative_schedule_group').length===5,'Five paired preparation options');
check(scene('hexane-spin').description.includes('No visible precipitation'),'No invented control pellet');
check(scene('ta-acquire').rows.some(x=>x.label==='Figure S6'&&x.value.includes('180@NCs//0.7 only')),'S6 specimen boundary');
check(scene('icp-dissolve').rows.some(x=>x.value.includes('destructive')),'Destructive digestion boundary');
''' +t[end:]
t=t.replace('Stock/mixture and independent workup boundaries, uncertainty, upper bound, PDF observation and SCF conflict','Five paired preparations, lower-bound degassing, separate optical specimens and destructive digestion')
(A/'render_and_check.mjs').write_text(t,'utf-8')
