from pathlib import Path
import json
B=Path(__file__).resolve().parent;P=B.parent/'nl015685v';V=B/'visuals'
for name in ['run_build.py','verify_archive.py']:
 t=(P/name).read_text(encoding='utf-8').replace('besson2002','dantas2002').replace('besson-','dantas-');(B/name).write_text(t,encoding='utf-8')
t=(P/'visuals/render_besson_scenes.mjs').read_text(encoding='utf-8').replace('Besson2002','Dantas2002').replace('besson2002','dantas2002').replace('600 415','600 420').replace('record_count:12','record_count:16');(V/'render_dantas_scenes.mjs').write_text(t,encoding='utf-8')
(V/'render_scene_contacts.py').write_text((P/'visuals/render_scene_contacts.py').read_text(encoding='utf-8'),encoding='utf-8')
t=(P/'build_inventory_actual.py').read_text(encoding='utf-8').replace('besson2002','dantas2002').replace('besson','dantas').replace('six supplied main','five supplied main').replace("'page_count':6","'page_count':5")
start=t.index("'notes':['Silica-host preparation")
end=t.index(']}',start)+2
t=t[:start]+"'notes':['Shared glass preparation and six annealing conditions preserve the upstream powder batch, sulfur-source uncertainty and separate optical/AFM specimen cohorts.','Seven original figures and procedural/source excerpts are retained. AFM height distributions, absorption, photoluminescence, excitation-power behavior and author model calculations retain their own sample scopes.','Optical size/radius ambiguity and questionable aluminum-crucible wording remain explicit. No measured atomic lattice, absent Raman spectrum or raw data are invented.']}"+t[end:]
(B/'build_inventory_actual.py').write_text(t,encoding='utf-8')
print('Private rendering, inventory, build and archive helpers prepared.')
