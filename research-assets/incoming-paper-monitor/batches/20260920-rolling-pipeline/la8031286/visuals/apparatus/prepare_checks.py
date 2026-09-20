"""Reuse test mechanics only; replace all paper-specific assertions."""
from pathlib import Path
A=Path(__file__).resolve().parent;T=A.parents[2]/'acsanm.2c04342/visuals/apparatus'
assert not(A/'package-freeze.json').exists()
s=(T/'render_and_check.mjs').read_text('utf-8').replace('Matuhina2023','Pati2009').replace('matuhina2023','pati2009').replace('Matuhina 2023','Pati 2009').replace('Matuhina et al. 2023','Pati et al. 2009').replace('39','35').replace("author:'/root'","author:'/root/backlog_eta'")
s=s.replace("o.id+'.svg'","scene.kind+'.svg'")
start=s.index("check(row('cs-reactivate'");end=s.index('for(const s of scenes)for(const group',start)
s=s[:start]+'''check(row('drip','addition_rate').value==='3–4 mL/min','Addition rate range');
check(row('poststir','post_precipitation_stirring_duration').value==='1 h','Post precipitation hold');
check(row('ambient-dry','ambient_drying_duration').value==='24 h','Dry before acetone');
check(row('diagnostic','filtrate_aliquot').value==='10 mL','Diagnostic aliquot only');
check(row('calcine','calcination_temperature').value==='200 °C','Calcination temperature');
check(scene('calcine').rows.some(r=>r.label==='Atmosphere'&&r.value.includes('Unreported')),'Calcination does not inherit air');
check(scene('tga-acquire').description.includes('in air'),'TGA air retained');
check(scene('diagnostic').rows.some(r=>r.value.includes('not returned')),'Diagnostic branch stays separate');
check(scene('xps-acquire').rows.some(r=>r.value.includes('<15 min')&&r.value.includes('>5 h')),'Exposure bounds retain separate contexts');
check(scene('xps-fit-analyze').rows.some(r=>r.value.includes('884.5')&&r.value.includes('884.8')),'Calibration conflict retained');
check(new Set(scenes.map(s=>s.kind)).size===35,'Unique scene for every record operation');
check(new Set(scenes.map(s=>s.operation_id)).size===19,'Nineteen source operations');
for(const s of scenes.filter(s=>s.record_id.endsWith('-route'))){
 const sol=s.record_id.split('-')[2],label={ethanol:'Anhydrous ethanol',propanol:'1-Propanol',butanol:'1-Butanol'}[sol];
 check(s.title.startsWith(label),'Source-specific solvent title');
 check(s.rows.some(x=>x.label==='Selected solvent'&&x.value.startsWith(label)),'Source-specific solvent condition');
}
''' +s[end:]
s=s.replace('Five paired preparations, lower-bound degassing, separate optical specimens and destructive digestion','Separate solvent routes, diagnostic fraction, drying order, calcination/TGA atmosphere and XPS exposure limits')
(A/'render_and_check.mjs').write_text(s,'utf-8')
s=(T/'render_previews.py').read_text('utf-8').replace("s['operation_id']+'.svg'","s['kind']+'.svg'").replace("s['operation_id']+'.png'","s['kind']+'.png'").replace("{'operation_id':s['operation_id']","{'scene_id':s['kind'],'record_id':s['record_id'],'operation_id':s['operation_id']").replace("str(start+j+1)+' '+item['operation_id']","str(start+j+1)+' '+item['scene_id']").replace("'operation_ids':[x['operation_id'] for x in group]","'scene_ids':[x['scene_id'] for x in group]").replace("'author':'/root'","'author':'/root/backlog_eta'")
(A/'render_previews.py').write_text(s,'utf-8')
