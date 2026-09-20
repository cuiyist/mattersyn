from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil
L=Path(__file__).resolve().parent;O=L/'site-integration-proposal';S=Path(r'[local path redacted]');D=S.parent.parent/'mattersyn-github-public-clean/mattersyn-site'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=D/'illustrated-guide.css';new=S/'dist/illustrated-guide.css'
shutil.copy2(old,O/'pre-mobile-illustrated-guide.css')
before=old.read_text(encoding='utf8');after=new.read_text(encoding='utf8')
addition='/* Long source digests remain readable without widening mobile record pages. */\n.protocol-copy small,.crystal-reference-card small{overflow-wrap:anywhere;word-break:normal;max-width:100%;}\n@media(max-width:620px){.record-main .lian-bulk-view{height:auto;aspect-ratio:1/1;min-height:260px;}}\n'
assert after.replace(addition,'')==before
source=L/'visuals/bulk-structure-proposal/lian2021-bulk-viewer.mjs';target=S/'dist/lian2021-bulk-viewer.mjs'
assert target.read_text(encoding='utf8')==source.read_text(encoding='utf8').replace('viewer.zoom(expanded?.95:1.45)','viewer.zoom(expanded?.95:(view.clientWidth<400?1.0:1.45))')
out={'status':'pending_independent_display_delta_audit','at':datetime.now(timezone.utc).isoformat(),'author':'/root','changes':[{'path':str(new),'before_sha256':sha(old),'after_sha256':sha(new),'only_added_rule':addition},{'path':str(target),'before_sha256':sha(source),'after_sha256':sha(target),'only_change':'ASU camera zoom uses1.0 for viewports below400px, otherwise original1.45; expansion camera unchanged.'}],'source_models_unchanged':True,'canonical_unchanged':True,'purpose':'Long provenance hashes wrap on narrow screens; listed sites and outlined cell fit initial mobile view.'}
(O/'mobile-display-delta.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out,indent=2))
