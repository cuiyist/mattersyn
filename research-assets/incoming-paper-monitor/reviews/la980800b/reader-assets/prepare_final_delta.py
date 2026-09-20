"""Prepare guarded reader-only amendments; source and Site remain read-only."""
from pathlib import Path
from datetime import datetime, timezone
import json,hashlib
B=Path(__file__).resolve().parent.parent
S=B.parents[3]/'recipe-atlas'
path=S/'data/paper-reviews/stiger1999.json'
d=json.loads(path.read_text(encoding='utf-8'))
proposal=json.loads((B/'public-review-proposal/stiger1999.json').read_text(encoding='utf-8'))
patch=[]
for n,fig in enumerate(d['figures']):
    if fig['id']=='figure-2':
        for field in ['quantitative_context','notes']:
            before=fig[field]
            after=[x.replace('scan 2 widely spaced dotted; scan 3 more closely spaced dotted',
                             'scan 2 dotted; scan 3 short dashed') for x in before]
            assert before!=after
            patch.append({'item_id':fig['id'],'json_pointer':f'/figures/{n}/{field}','before':before,'set':after})
    if fig['id']=='figure-6':
        addition=next(f for f in proposal['figures'] if f['id']=='figure-6')['quantitative_context'][-1]
        for field in ['quantitative_context','notes']:
            before=fig[field];assert addition not in before
            patch.append({'item_id':fig['id'],'json_pointer':f'/figures/{n}/{field}','before':before,'set':before+[addition]})
for si,sec in enumerate(d['reader_sections']):
    for ii,it in enumerate(sec['items']):
        if it['id']=='tem-transfer':
            before=it['text'];after=before.replace('optional solvent','any transfer solvent');assert before!=after
            patch.append({'item_id':it['id'],'json_pointer':f'/reader_sections/{si}/items/{ii}/text','before':before,'set':after})
out={'created_utc':datetime.now(timezone.utc).isoformat(),'source_ledger_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
     'scope':'Five reader-only fields. Preserve all root promotion, inventory, source-review and browser flags. No canonical values or scientific sample joins changed.',
     'patches':patch,'patch_count':len(patch)}
(B/'public-review-proposal/final-reader-delta.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
# Capture unchanged-science audit evidence for an eventual bounded final presentation check.
(B/'reader-assets/reader-audit-baseline.json').write_text(json.dumps({'ledger':d,'prior_audit':json.loads((B/'reader-assets/canonical-to-reader-audit.json').read_text(encoding='utf-8'))},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'patch_count':len(patch),'path':str(B/'public-review-proposal/final-reader-delta.json')}))
