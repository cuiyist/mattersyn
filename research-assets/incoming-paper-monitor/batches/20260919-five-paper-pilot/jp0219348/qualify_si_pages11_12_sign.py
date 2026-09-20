"""Preserve the initial reading and explicitly qualify one unreadable scan sign."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil, runpy
B = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not (B/'si-pages11-12-manifest.json').exists()
archive = B/'si-pages11-12-author-prefreeze-reading'
archive.mkdir(exist_ok=False)
names = ['author_si_pages11_12.py','si-pages11-12-author-blocks.json']
before = {}
for n in names:
    shutil.copyfile(B/n, archive/n)
    before[str(archive/n)] = sha(archive/n)
p = B/names[0]
t = p.read_text(encoding='utf8')
old = '9 11 27 2443.17 1965.46 7694.14 o'
new = '9 11 27 2443.17 [sign_unresolved]1965.46 7694.14 o'
assert t.count(old) == 1
p.write_text(t.replace(old,new),encoding='utf8')
runpy.run_path(str(p),run_name='__main__')
initial = json.loads((archive/names[1]).read_text(encoding='utf8'))
final = json.loads((B/names[1]).read_text(encoding='utf8'))
changes = [(k,i+1,a,b) for k in initial for i,(a,b) in enumerate(zip(initial[k],final[k])) if a != b]
assert changes == [('11R',35,old,new)]
report = {
    'schema':'mattersyn-si-prefreeze-uncertain-sign/1',
    'created_at':datetime.now(timezone.utc).isoformat(),
    'author':'/root/peng1998_reader_assets',
    'cell_id':'si-p11-R-r035-Fobs2',
    'source_locator':'SI PDF p.11, printed p.51, Supporting Table1, right block body row35, hkl (9,11,27), Fobs^2',
    'initial_author_reading':'1965.46',
    'clear_visible_digits':'1965.46',
    'final_editorial_token':'[sign_unresolved]1965.46',
    'numeric_value':None,
    'signed_value_candidates':[-1965.46,1965.46],
    'reason':'The native scan contains a tiny degraded mark before clear digits 1965.46. The author reopened the native crop and magnified detail after the independent reader raised a possible minus sign. Neither a definite minus nor definite absence of a sign is supported. The bracketed prefix is editorial and is not printed source text. The magnitude is retained without selecting a signed value.',
    'comparison_scope':'Both full pages, both headers and all eight native column crops were actually inspected by the author. No other raw token was changed in this pre-freeze qualification.',
    'source_crop':'reader-assets/si-numerical-pages11-12/si-11-right-bottom.png',
    'source_crop_sha256':sha(B/'reader-assets/si-numerical-pages11-12/si-11-right-bottom.png'),
    'archived_initial_reading':before,
    'final_reading':{str(B/n):sha(B/n) for n in names},
    'changed_raw_tokens':1,
    'unchanged_raw_tokens':1259,
    'independent_numerical_audit':'pending',
    'source_pixels_modified':False,
}
(B/'si-pages11-12-sign-uncertainty.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':'qualified_without_sign_inference','changed_tokens':1,'archive':str(archive)},indent=2))
