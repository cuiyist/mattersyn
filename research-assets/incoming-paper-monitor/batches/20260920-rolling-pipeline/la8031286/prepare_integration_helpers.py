"""Prepare root-only import/build helpers; this script never imports into Site."""
from pathlib import Path
P=Path(__file__).resolve().parent;A=P.parent/'acsanm.2c04342'
base=(A/'import_reviewed_matuhina.py').read_text('utf8').split('changes=[]')[0]
base=base.replace('Matuhina','Pati').replace('matuhina','pati').replace("P=O/'v2'","P=O/'v1'").replace('len(old)==586','len(old)==607')
tail=r'''changes=[]
def edit(rel,before,after,count=1):
 p=S/rel;t=p.read_text('utf8');assert t.count(before)==count,(rel,before[:80],t.count(before));backup(rel);p.write_text(t.replace(before,after),'utf8');changes.append({'file':rel,'before':before,'after':after,'occurrences':count})
rel='dist/protocol-visuals.mjs'
edit(rel,"import {buildMatuhina2023Scene", "import {buildPati2009Scene,createPati2009Art,createPati2009ConditionGrid} from './pati2009-protocol.mjs';\nimport {buildMatuhina2023Scene")
edit(rel,'const sourceArt=createMatuhina2023Art','const sourceArt=createPati2009Art(o,r)||createMatuhina2023Art')
edit(rel,'const matuhina=buildMatuhina2023Scene','const pati=buildPati2009Scene(o,r),matuhina=buildMatuhina2023Scene')
edit(rel,"el('p',matuhina?.caption","el('p',pati?.caption||matuhina?.caption")
edit(rel,'if(matuhina||sommer||','if(pati||matuhina||sommer||')
edit(rel,'const dl=matuhina?createMatuhina2023ConditionGrid','const dl=pati?createPati2009ConditionGrid(o,r):matuhina?createMatuhina2023ConditionGrid')
edit(rel,'&&!ghosh&&!sommer&&!matuhina)for','&&!ghosh&&!sommer&&!matuhina&&!pati)for')
edit(rel,"&&!ghosh&&!sommer&&!matuhina){const env=el('div')","&&!ghosh&&!sommer&&!matuhina&&!pati){const env=el('div')")
edit('scripts/build_dataset.py',"'dataset_version':'0.30.0'","'dataset_version':'0.31.0'",2)
edit('scripts/build_dataset.py',"('matuhina2023','private_unapproved_reader_proposal')}","('matuhina2023','private_unapproved_reader_proposal'),('pati2009','private_unapproved_reader')}")
edit('scripts/build_dataset.py',"('matuhina2023','Identity and role are source scoped; qualified molecular/component bindings remain separate.')}","('matuhina2023','Identity and role are source scoped; qualified molecular/component bindings remain separate.'),('pati2009','Named identity and printed formula retained separately; no molecular model approval.')}")
versions=[]
for p in list((S/'scripts').glob('build_*.py'))+list((S/'dist').glob('*.mjs'))+list((S/'dist').glob('*.html')):
 t=p.read_text('utf8');n=t.replace('0.30.0-r1','0.31.0-r1').replace('0.30.0-r2','0.31.0-r2')
 if n!=t:
  rel=p.relative_to(S).as_posix();backup(rel);p.write_text(n,'utf8');versions.append(rel)
assert all(sha(S/'data/records'/name)==h for name,h in old.items())
save(O/'code-delta.json',{'changes':changes,'cache_revision_files':versions})
save(O/'site-import-manifest.json',{'at':datetime.now(timezone.utc).isoformat(),'status':'integrated_locally_pending_browser_and_release','audits':audits,'proposal_freeze_sha256':sha(P/'package-freeze.json'),'product_context_freeze_sha256':sha(C/'package-freeze.json'),'new_records':19,'old_records_preserved':607,'new_routes':3,'new_training_tasks':0,'new_exact_structure_pairs':0,'new_molecular_entries':20,'new_phase_symbol_entries':11,'selected_source_crops':20,'apparatus_scenes':35,'symbolic_product_contexts':39,'record_sample_phase_contexts':39})
print(json.dumps({'integrated_records':19,'unchanged_old_records':607,'dataset_candidate':'0.31.0','published':False}))
'''
base=base.replace('pati2023','pati2009')
(P/'import_reviewed_pati.py').write_text(base+tail,'utf8')
t=(A/'build_matuhina_inventory.py').read_text('utf8').replace('matuhina2023','pati2009').replace('matuhina','pati').replace('expected_new=21','expected_new=19')
(P/'build_pati_inventory.py').write_text(t,'utf8')
t=(A/'build_and_check_site.py').read_text('utf8').replace('build_matuhina_inventory.py','build_pati_inventory.py').replace('matuhina2023-protocol.mjs','pati2009-protocol.mjs')
(P/'build_and_check_site.py').write_text(t,'utf8')
print('Prepared root-only Pati import/build/inventory helpers; no Site files changed.')
