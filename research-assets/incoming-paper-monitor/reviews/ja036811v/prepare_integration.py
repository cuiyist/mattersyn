from pathlib import Path
B=Path(__file__).resolve().parent;P=B.parent/'ja035980c'
t=(P/'integrate_review.py').read_text(encoding='utf8')
t=t.replace('banerjee2003','schwartz2003').replace('banerjee-2003-','schwartz-2003-').replace('len(drafts)==14','len(drafts)==30')
a=t.index("scope='");b=t.index('\nrecords=[]',a)
t=t[:a]+"scope='All14 main and4 matched SI pages text-read and visually inspected with independent source, canonical, molecular, reader and apparatus audits. Separate pure/doped routes, postprocessing, surface-bound control, magnetic aggregates and theoretical models retain distinct sample scopes. Missing parameters and source conflicts remain explicit; cited external works not independently inspected.'"+t[b:]
t=t.replace('All nine supplied main pages text and visually reviewed; independent source and canonical audits completed. Matched one-page SI also fully read and visually reviewed.','All14 main and4 matched SI pages text and visually reviewed; independent source and canonical audits completed.')
a=t.index('review.update(');b=t.index("\nfor item in review['recipe_inventory']",a)
t=t[:a]+"review.update(coverage_status='supplied_main_and_matched_si_text_and_visual_review_complete',source_review_promoted=True,independent_audit='All14 main and4 matched SI pages, canonical extraction, reader coverage, original crops, chemical identities and apparatus scenes independently audited. Publication tracked separately.',publication_status='Reviewed contribution for the existing MatterSyn atlas; deployment tracked separately.',training_note='Three pure/Co-doped/Ni-doped ZnO synthesis routes retain unknown per-batch conditions and source discrepancies. Postprocessing, deliberate surface-bound controls, optical specimens and magnetic aggregate powder remain distinct. Models and independent bulk crystal references are not measured sample coordinates or exact structure-to-recipe labels.')"+t[b:]
a=t.index("p=S/'dist/protocol-visuals.mjs'");b=t.index("p=S/'data/measurement-display.json'",a)
t=t[:a]+'''p=S/'dist/protocol-visuals.mjs';t=p.read_text(encoding='utf8');assert "from './schwartz2003-protocol.mjs'" not in t
t="import {buildSchwartz2003Scene,createSchwartz2003Art} from './schwartz2003-protocol.mjs';\\n"+t
t=t.replace('const sourceArt=createBanerjee2003Art','const sourceArt=createSchwartz2003Art(o,r)||createBanerjee2003Art')
t=t.replace('banerjee=buildBanerjee2003Scene(o,r);','banerjee=buildBanerjee2003Scene(o,r),schwartz=buildSchwartz2003Scene(o,r);').replace('banerjee?.caption||','schwartz?.caption||banerjee?.caption||').replace('||yi||banerjee){','||yi||banerjee||schwartz){').replace('||yi||banerjee)?','||yi||banerjee||schwartz)?');p.write_text(t,encoding='utf8')
p=S/'dist/crystal-viewer.mjs';t=p.read_text(encoding='utf8').replace("'yi2002','banerjee2003']","'yi2002','banerjee2003','schwartz2003']")
t=t.replace(" if(r.lineage?.source_group==='banerjee2003'&&entryId)"," if(r.lineage?.source_group==='schwartz2003'&&entryId)host.append(el('p','The paper supplies TEM and electron-diffraction evidence, but no measured atomic coordinates or refined dopant occupancies. The downloadable ZnO unit cell is an independent undoped host reference, not the Co/Ni-doped specimen or a fitted particle. Surface-bound controls and magnetic aggregates retain their own sample identities.','guide-notice'));\\n if(r.lineage?.source_group==='banerjee2003'&&entryId)")
p.write_text(t,encoding='utf8')
p=S/'dist/assets/crystal-references/registry.json';d=read(p);ref=next(x for x in d['entries']if x['id']=='zno-wurtzite')
cp=read(V/'crystal-reference-proposal.json');assert sha(p)==cp['registry_before_sha256']
for file,expected in cp['asset_hashes'].items():assert sha(p.parent/file)==expected
ref['record_ids']=list(dict.fromkeys(ref['record_ids']+cp['additional_record_ids']));ref['scope']=cp['scope'];write(p,d)
p=S/'scripts/build_atlas.py';t=p.read_text(encoding='utf8');assert "NAMES['ZnO:Co']" not in t
t=t.replace("NAMES['Pt']='Platinum nanocrystals'","NAMES['Pt']='Platinum nanocrystals'\\nNAMES['ZnO:Co']='Cobalt-doped zinc oxide quantum dots'\\nNAMES['ZnO:Ni']='Nickel-doped zinc oxide quantum dots'");p.write_text(t,encoding='utf8')
''' +t[b:]
t=t.replace("replace(\"'dataset_version':'0.18.0'\",\"'dataset_version':'0.19.0'\")","replace(\"'dataset_version':'0.19.0'\",\"'dataset_version':'0.20.0'\")")
t=t.replace("replace('0.18.0-r1','0.19.0-r1')","replace('0.19.0-r1','0.20.0-r1')").replace('Imported 14 audited records','Imported 30 audited records')
# The crystal reference proposal is included in the independent bindings audit.
t=t.replace("assert ba['record_hashes']", "assert sha(V/'crystal-reference-proposal.json')==ba['crystal_reference_sha256']\nassert ba['record_hashes']")
(B/'integrate_review.py').write_text(t,encoding='utf8')
print('Prepared gated root integration script; no Site files modified.')
