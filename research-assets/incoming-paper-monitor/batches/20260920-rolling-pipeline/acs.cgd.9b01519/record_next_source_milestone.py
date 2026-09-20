from pathlib import Path
from datetime import datetime,timezone
import json,sys
N=Path(__file__).resolve().parent;MON=N.parents[2];M=N.parents[4];sys.path.insert(0,str(MON));import monitor
p=MON/'public-progress-editorial.json';e=json.loads(p.read_text('utf8'))
c=next(x for x in e['current_work'] if x['short_label']=='Pati et al. (2009)')
c['summary']='The supplied four-page main article reports room-temperature precipitation of CeO₂ in different alcohols, with workup and calcination. The four-page SI contains XPS analysis, fitting and a quantitative table. Extraction and separate comparison are underway; the SI pairing evidence uses the paper declaration, matching XPS content and document metadata.'
c=next(x for x in e['current_work'] if x['short_label']=='Matuhina et al. (2023)')
c['stage']='Frozen main/SI extraction under independent comparison; structured data in preparation'
c['summary']='All 26 supplied pages have been read and visually inspected by the author and a separate reviewer. The frozen source extraction preserves 62 facts, 186 quantities, seven tables/55 rows, 39 operations and 30 selected original crops. Final independent comparison is underway; data and reader drafts remain outside the published atlas.'
c['stages'][1].update(label='Frozen extraction and independent comparison',detail='Author extraction is frozen. The separate reviewer compares it against independently read originals and table transcriptions; author checks do not imply approval.')
p.write_text(json.dumps(e,ensure_ascii=False,indent=2)+'\n','utf8')
monitor.checkpoint(MON/'ledger.json','mattersyn-primary',group_id='10.1021_acsanm.2c04342',note='All26supplied main/SI pages read; source author package frozen for distinct independent comparison. Canonical/reader drafting begins outside Site; no source/canonical/visual approval inferred.',data={'current_step':'Frozen source under independent audit; canonical draft preparation','source_freeze':{'path':str(N.parent/'acsanm.2c04342/package-freeze.json'),'sha256':'e57825801f343b57b48ff66722a686b9fda045a04baeb71c5d1fc946f75c0151'}})
p=M/'MEMORY.md';text='''## 2026-09-20 — Matuhina source freeze and next review gates

Matuhina source package is frozen at acsanm.2c04342/package-freeze.json SHA e57825801f343b57b48ff66722a686b9fda045a04baeb71c5d1fc946f75c0151 (138 bound files). All 26 main/SI pages inspected; 62 facts, 186 quantities, seven tables/55 rows, 301 printed cells plus 20 repeated grouping fields, 39 operations, 14 scopes, 28 materials/five stocks, 41 contexts, 30 crops and 55 references. Thirteen source discrepancies remain explicit. Norberg now independently compares the frozen extraction; Backlog prepares canonical/reader drafts pending the source outcome. No Matuhina Site import or atomic/training approval.

Pati has four main and four SI pages. Correction to the reviewer’s initial description: SI contains XPS Figure S1, fitting, Table S1 and references; morphology is in the main. Do not claim morphology SI or a title/byline match. Peng extracts; Norberg has independently read all eight pages and transcribed 20 Table S1 numeric cells. Pati source freeze and final comparison remain pending. Both papers remain separate from the verified Sommer dataset 0.29.0 release. Root alone owns Site/ledger.
''';p.write_text(text+'\n'+p.read_text('utf8'),'utf8')
print('Saved source milestone and corrected SI scope; no new scientific data published.')
