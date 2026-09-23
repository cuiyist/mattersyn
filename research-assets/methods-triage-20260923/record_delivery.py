"""Record the verified progress-only release; scientific publication is unchanged."""
from pathlib import Path
import json,subprocess
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
receipt=json.loads((ROOT/'research-assets/pair-priority-screen-20260922/live-progress-delivery.json').read_text(encoding='utf8'))
expected='91e83705514ca8b3f1755a83a051ef45080950ec'
assert receipt['passed'] and receipt['site_commit']==expected
assert all(x['matches_published_checkout']for x in receipt['checks'])
(HERE/'delivery-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
p=ROOT/'MEMORY.md';text=p.read_text(encoding='utf8')
heading='## 2026-09-23 — Parallel screening checkpoint delivered'
assert heading not in text
entry=f"""{heading}

Progress-only GitHub Pages deployment verified without login at{receipt['verified_at']}: site commit{expected}, Pages run35868138168. All four checked public artifacts match the isolated release checkout. The project source-screen checkpoint and memory were pushed in commit8afdc4070b0457269bfab22df43674fbec0dadba; this delivery receipt is saved in the follow-up project commit. No scientific records, training pairs or full-source documents were added to the website. Daily scheduling remains unchanged. Next screening should continue beyond checked shortlist scopes using research-assets/methods-triage-20260923/screened-scopes.json and preserve the independently supported additional source-role hold.

"""
p.write_text(entry+text,encoding='utf8')
print(json.dumps({'delivery_recorded':True,'site_commit':expected,'science_added':0}))
