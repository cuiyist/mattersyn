from pathlib import Path
import hashlib,json
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=json.loads((OUT/'scene-output.json').read_bytes())
assert len(rows)==14
assert sum(len(x['rows']) for x in rows)==59
assert len({sha(p) for p in (OUT/'scenes').glob('*.svg')})==14
at=datetime.now(timezone.utc).isoformat()
validation={'schema':'mattersyn.apparatus_author_check/1','at':at,'author':'/root','status':'author_checked_pending_independent_audit','records':4,'operations':14,'condition_rows':59,'distinct_svg_files':14,'visual_review':{'all_14_scenes_seen':True,'scope':'Private interactive preview, including the selected operation labels, apparatus illustrations, conditions, source-conflict notes and descriptions. Final site integration remains pending.','narrow_viewport':[390,844],'all_14_narrow_layouts_horizontal_overflow':False,'all_condition_terms_and_definitions_match':True,'browser_console_errors':0,'corrections':['Expanded apparatus viewBox to retain the complete Electron probe label.','Display-only spacing correction of At673 K to At 673 K.','Wash-volume statement retained as 10 mL; apparatus geometry remains unspecified.'],'viewport_restored':True},'limits':['Apparatus geometry is illustrative, not a measured source drawing.','Prose/table conflicts remain unresolved, not separate verified recipes.','Canonical records and source artifacts were not changed.','Source-scientific independent apparatus audit and final integrated browser review are still required.']}
(OUT/'author-validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
files=[{'path':p.relative_to(OUT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='package-freeze.json']
freeze={'schema':'mattersyn.apparatus_package_freeze/1','at':at,'author':'/root','status':'frozen_for_independent_audit','source_group':'heo2003','canonical_package_manifest_sha256':'10640012af6a21458edd6a84c24af2dea24562f950495a662930d682185fb05a','source_bundle_sha256':'b20a5d7745547a8f17644bcb583775e603865b8714ff74347e3cf00217390b7a','files':files}
(OUT/'package-freeze.json').write_text(json.dumps(freeze,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'files':len(files),'package_freeze_sha256':sha(OUT/'package-freeze.json')}))
