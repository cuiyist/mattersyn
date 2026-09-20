"""Prepare Sommer-specific root tools; this does not mutate Site data."""
from pathlib import Path
N=Path(__file__).resolve().parent;G=N.parent/'ja212032q'
t=(G/'import_reviewed_ghosh.py').read_text('utf8')
t=t.replace("C=O/'product-context-v1'","C=N/'product-context-proposal'")
a=t.index('for name,proposal in ');b=t.index('old={',a)
t=t[:a]+'''for name,proposal,path in [
 ('promotion-delta-audit.json',P,N/'site-integration-independent-audit/promotion-delta-audit.json'),
 ('product-context-audit.json',C,N/'product-context-independent-audit/independent-audit.json')]:
 audit=read(path)
 assert audit['status']=='passed' and not audit.get('open_findings') and audit['proposal_freeze_sha256']==sha(proposal/'package-freeze.json')
 audits[name]=sha(path)
 frozen=read(proposal/'package-freeze.json')
 if 'files' in frozen:
  for f in frozen['files']:assert sha(proposal/f['path'])==f['sha256']
 else:
  for path,h in frozen['bound_files'].items():assert sha(Path(path))==h
'''+t[b:]
t=t.replace('==546','==567').replace("'old_records_preserved':546","'old_records_preserved':567").replace("'unchanged_old_records':546","'unchanged_old_records':567")
t=t.replace("for e in read(P/'molecules/registry-additions.json')['entries']:","for e in read(P/'molecules/registry-additions.json')['entries']+read(C/'registry-additions.json')['entries']:")
t=t.replace("assert e['id'] not in known;e['published']=True;registry['entries'].append(e)","assert e['id'] not in known;e.update(published=True,binding_approved=True);registry['entries'].append(e)\n if e['id'].endswith('-observed-phase-symbol'):\n  src=C/e['svgPath'];assert sha(src)==e['assetHashes']['svgPath'];cp(src,V/e['svgPath'])")
t=t.replace("reader/ghosh2012.json","reader/sommer2020.json").replace("paper-reviews/ghosh2012.json","paper-reviews/sommer2020.json")
t=t.replace("reader['presentation_gates']['site_integration']=True;","reader['presentation_gates'].update(site_integration=True,symbolic_product_contexts=True);reader['remaining_gaps']=[x for x in reader['remaining_gaps'] if x!='Source, canonical/reader, molecular and apparatus audits passed. Symbolic product-context binding, integrated browser and publication gates remain separate.'];")
a=t.index("edit(rel,\"import {buildLian2021Scene");b=t.index('versions=[]',a)
t=t[:a]+'''edit(rel,"import {buildGhosh2012Scene", "import {buildSommer2020Scene,createSommer2020Art,createSommer2020ConditionGrid} from './sommer2020-protocol.mjs';\\nimport {buildGhosh2012Scene")
edit(rel,'const sourceArt=createGhosh2012Art','const sourceArt=createSommer2020Art(o,r)||createGhosh2012Art')
edit(rel,'const ghosh=buildGhosh2012Scene','const sommer=buildSommer2020Scene(o,r),ghosh=buildGhosh2012Scene')
edit(rel,"el('p',ghosh?.caption","el('p',sommer?.caption||ghosh?.caption")
edit(rel,'if(ghosh||lian||','if(sommer||ghosh||lian||')
edit(rel,'const dl=ghosh?createGhosh2012ConditionGrid','const dl=sommer?createSommer2020ConditionGrid(o,r):ghosh?createGhosh2012ConditionGrid')
edit(rel,'&&!lian&&!ghosh)for','&&!lian&&!ghosh&&!sommer)for')
edit(rel,"&&!lian&&!ghosh){const env=el('div')","&&!lian&&!ghosh&&!sommer){const env=el('div')")
edit('scripts/build_dataset.py',"'dataset_version':'0.28.0'","'dataset_version':'0.29.0'",2)
edit('scripts/build_dataset.py',"('ghosh2012','private_unapproved_reader_proposal')}","('ghosh2012','private_unapproved_reader_proposal'),('sommer2020','private_unapproved_reader_proposal')}")
edit('scripts/build_dataset.py',"('ghosh2012','Source-qualified identity only; molecular/product visual binding is separately pending.')}","('ghosh2012','Source-qualified identity only; molecular/product visual binding is separately pending.'),('sommer2020','Chemical identity and source role only; independently qualified molecular/component bindings remain pending.')}")
edit('scripts/build_dataset.py',"record['lineage']['source_group']=='ghosh2012' else", "record['lineage']['source_group'] in {'ghosh2012','sommer2020'} else")
edit('scripts/build_dataset.py',"not in {'lian2021','ghosh2012'}", "not in {'lian2021','ghosh2012','sommer2020'}")

'''+t[b:]
t=t.replace("'0.27.0-r1','0.28.0-r1'","'0.28.0-r1','0.29.0-r1'").replace("'0.27.0-r2','0.28.0-r2'","'0.28.0-r2','0.29.0-r2'")
t=t.replace("'new_records':21","'new_records':19").replace("'new_routes':5","'new_routes':3").replace("'new_molecular_entries':25","'new_molecular_entries':28,'new_phase_symbol_entries':3").replace("'selected_source_crops':36","'selected_source_crops':20").replace("'apparatus_scenes':33","'apparatus_scenes':31").replace("'symbolic_product_contexts':45","'symbolic_product_contexts':77,'record_sample_phase_contexts':45").replace("'integrated_records':21","'integrated_records':19").replace("'dataset_candidate':'0.28.0'","'dataset_candidate':'0.29.0'")
(N/'import_reviewed_sommer.py').write_text(t,'utf8')
t=(G/'build_ghosh_inventory.py').read_text('utf8').replace('ghosh','sommer').replace('Ghosh','Sommer').replace('2012','2020').replace('expected_new=21','expected_new=19')
(N/'build_sommer_inventory.py').write_text(t,'utf8')
t=(G/'build_and_check_site.py').read_text('utf8').replace('ghosh','sommer').replace('2012','2020')
(N/'build_and_check_site.py').write_text(t,'utf8')
for name in ['import_reviewed_sommer.py','build_sommer_inventory.py','build_and_check_site.py']:compile((N/name).read_text('utf8'),str(N/name),'exec')
print('Prepared root import and build tools; no Site change.')
