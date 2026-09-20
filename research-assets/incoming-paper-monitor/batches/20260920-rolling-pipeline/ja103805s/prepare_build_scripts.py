"""Reuse the established inventory/build mechanics for the Evans contribution."""
from pathlib import Path
E=Path(__file__).resolve().parent
H=E.parents[1]/'20260919-five-paper-pilot/jp0219348'
t=(H/'build_heo_inventory.py').read_text(encoding='utf8')
t=t.replace('-heo-source-actual-local-snapshot','-evans-source-actual-local-snapshot').replace("newgroups=['heo2003']","newgroups=['evans2010']").replace('expected_new=10','expected_new=32').replace("'heo_source_records'","'evans_source_records'").replace("'single_heo_source_group'","'single_evans_source_group'")
(E/'build_evans_inventory.py').write_text(t,encoding='utf8')
t=(H/'build_and_check_site.py').read_text(encoding='utf8').replace('build_heo_inventory.py','build_evans_inventory.py').replace("'heo2003-protocol.mjs','heo2003-average-viewer.mjs','heo2003-reflection-viewer.mjs'","'evans2010-protocol.mjs'")
(E/'build_and_check_site.py').write_text(t,encoding='utf8')
print('Prepared Evans-specific reuse of established inventory and build scripts.')
