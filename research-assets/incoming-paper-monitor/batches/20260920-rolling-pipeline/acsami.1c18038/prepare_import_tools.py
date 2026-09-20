"""Prepare, but do not run, Lian integration helpers from the validated pattern."""
from pathlib import Path
L=Path(__file__).resolve().parent; N=L.parent/'acs.inorgchem.7b01711'
text=(N/'import_reviewed_morrison.py').read_text(encoding='utf8')
text=text.replace('Morrison','Lian').replace('morrison','lian').replace('2017','2021')
text=text.replace('len(old)==512','len(old)==530').replace('old_records_preserved\':512','old_records_preserved\':530').replace('unchanged_old_records\':512','unchanged_old_records\':530')
text=text.replace("'new_records':18","'new_records':16").replace("'integrated_records':18","'integrated_records':16").replace("'new_routes':2","'new_routes':3").replace("'new_molecular_entries':29","'new_molecular_entries':15").replace("'selected_source_crops':30","'selected_source_crops':53").replace("'apparatus_scenes':24","'apparatus_scenes':21").replace("'symbolic_product_contexts':17","'symbolic_product_contexts':22")
# Current dispatcher begins with Morrison, so prepend Lian at that exact point.
text=text.replace("edit(rel,\"import {buildEvans2010Scene\", \"import {buildLian2021Scene,createLian2021Art,createLian2021ConditionGrid} from './lian2021-protocol.mjs';\\nimport {buildEvans2010Scene\")", "edit(rel,\"import {buildMorrison2017Scene\", \"import {buildLian2021Scene,createLian2021Art,createLian2021ConditionGrid} from './lian2021-protocol.mjs';\\nimport {buildMorrison2017Scene\")")
text=text.replace("'const sourceArt=createEvans2010Art','const sourceArt=createLian2021Art(o,r)||createEvans2010Art'", "'const sourceArt=createMorrison2017Art','const sourceArt=createLian2021Art(o,r)||createMorrison2017Art'")
text=text.replace("'const evans=buildEvans2010Scene','const lian=buildLian2021Scene(o,r),evans=buildEvans2010Scene'", "'const morrison=buildMorrison2017Scene','const lian=buildLian2021Scene(o,r),morrison=buildMorrison2017Scene'")
text=text.replace("\"el('p',evans?.caption\",\"el('p',lian?.caption||evans?.caption\"", "\"el('p',morrison?.caption\",\"el('p',lian?.caption||morrison?.caption\"")
text=text.replace("'if(evans||heo||nagasaki||ribeiro||norberg){','if(lian||evans||heo||nagasaki||ribeiro||norberg){'", "'if(morrison||evans||heo||nagasaki||ribeiro||norberg){','if(lian||morrison||evans||heo||nagasaki||ribeiro||norberg){'")
text=text.replace("'const dl=evans?createEvans2010ConditionGrid','const dl=lian?createLian2021ConditionGrid(o,r):evans?createEvans2010ConditionGrid'", "'const dl=morrison?createMorrison2017ConditionGrid','const dl=lian?createLian2021ConditionGrid(o,r):morrison?createMorrison2017ConditionGrid'")
text=text.replace("'if(!aerosol&&!heo&&!evans)for','if(!aerosol&&!heo&&!evans&&!lian)for'", "'if(!aerosol&&!heo&&!evans&&!morrison)for','if(!aerosol&&!heo&&!evans&&!morrison&&!lian)for'")
text=text.replace("\"if(!heo&&!evans){const env=el('div')\",\"if(!heo&&!evans&&!lian){const env=el('div')\"", "\"if(!heo&&!evans&&!morrison){const env=el('div')\",\"if(!heo&&!evans&&!morrison&&!lian){const env=el('div')\"")
old='edit(\'scripts/build_dataset.py\',"r[\'lineage\'][\'source_group\']==\'evans2010\' and l[\'relation\']==\'source_reader_pending_independent_audit\'","r[\'lineage\'][\'source_group\'] in {\'evans2010\',\'lian2021\'} and l[\'relation\']==\'source_reader_pending_independent_audit\'")'
new='edit(\'scripts/build_dataset.py\',"(\'morrison2017\',\'private_reader_pending_independent_review\')}","(\'morrison2017\',\'private_reader_pending_independent_review\'),(\'lian2021\',\'private_unapproved_reader_proposal\')}")'
assert old in text;text=text.replace(old,new)
text=text.replace('0.26.0','__NEXT__').replace('0.25.0','0.26.0').replace('__NEXT__','0.27.0')
for name,content in [('import_reviewed_lian.py',text),('build_lian_inventory.py',(N/'build_morrison_inventory.py').read_text(encoding='utf8').replace('morrison','lian').replace('2017','2021').replace('expected_new=18','expected_new=16')),('build_and_check_site.py',(N/'build_and_check_site.py').read_text(encoding='utf8').replace('morrison','lian').replace('2017','2021'))]:
 path=L/name;assert not path.exists();compile(content,str(path),'exec');path.write_text(content,encoding='utf8')
print('Prepared Lian import/build scripts; shared Site unchanged.')
