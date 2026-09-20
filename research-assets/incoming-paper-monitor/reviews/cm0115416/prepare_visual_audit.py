from pathlib import Path
B=Path(__file__).resolve().parent
old=B.parent/'jp0208743'/'visuals';V=B/'visuals'
renderer=(old/'render_dantas_scenes.mjs').read_text(encoding='utf8').replace('Dantas2002','Yi2002').replace('dantas2002','yi2002').replace('record_count:16','record_count:18')
(V/'render_yi_scenes.mjs').write_text(renderer,encoding='utf8')
(V/'render_scene_contacts.py').write_bytes((old/'render_scene_contacts.py').read_bytes())
diagnostic=(old/'diagnose_scene_geometry.py').read_text(encoding='utf8')
(V/'diagnose_scene_geometry.py').write_text(diagnostic,encoding='utf8')
print('Prepared three private rendering/diagnostic helpers; apparatus module untouched.')
