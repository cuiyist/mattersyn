"""Freeze the bounded source revision after actual enlarged-crop inspection."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,runpy
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
old=read(P/'source-extraction-revision-1/package-freeze.json');assert read(P/'package-freeze.json')['revision']==1
# Polish the exact reviewer-requested phrasing before the new freeze, keeping the saved v1 immutable.
a='computes the reported average lifetime computed from amplitude and lifetime coefficients.';b='computes the reported average lifetime from amplitude and lifetime coefficients.'
for n in ['source-facts.json','source_author_data.py','prepare_source_revision_2.py']:
 p=P/n;t=p.read_text(encoding='utf-8')
 if a in t:p.write_text(t.replace(a,b),encoding='utf-8')
h=read(P/'source-correction-history.json')
for d in h['deltas']:
 if isinstance(d.get('after'),str):d['after']=d['after'].replace(a,b)
write(P/'source-correction-history.json',h)
assets=read(P/'original-assets-manifest.json');now=datetime.now(timezone.utc).isoformat()
for a in assets['assets']:
 if a['id']in['figure-1','figure-s4']:a['manual_visual_review']='Extraction author reopened the expanded original crop individually and verified the complete 1300 / 90 final tick glyphs and right whitespace. Distinct revision audit remains pending.'
write(P/'original-assets-manifest.json',assets)
visual=read(P/'author-visual-review.json');visual.update(reviewed_at=now,revision=2)
visual['actual_manual_scope']['revision_2_enlarged_crops_reopened']=['figure-1','figure-s4']
visual['bound_assets']={a['path']:a['sha256']for a in assets['assets']};visual['contact_sheets']={str(p):sha(p)for p in sorted((P/'private').glob('crop-contact-*.png'))}
write(P/'author-visual-review.json',visual)
runpy.run_path(str(P/'validate_extraction.py'),run_name='__main__');v=read(P/'extraction-validation.json')
author=read(P/'author-validation.json');author.update(validated_at=now,revision=2,checks_count=v['check_count'],actual_manual_scope=visual['actual_manual_scope'],mechanical_validation={'path':'extraction-validation.json','sha256':sha(P/'extraction-validation.json')});write(P/'author-validation.json',author)
notes=P/'extraction-notes.md';notes.write_text(notes.read_text(encoding='utf-8')+'\nRevision 2 preserves revision 1 byte-for-byte under `source-extraction-revision-1/`. The independent reviewer requested one fact-level Table 2 locator, an accurate descriptive label for the reported lifetime formula, and two right crop margins. All 194 fact quantities, 272 table cells, equation expressions and 34 unaffected crops remain unchanged; no scientific numeric value changed. Both expanded crops were reopened individually and their last axis labels are complete. The exact correction history and original preservation map are retained. This author revision does not certify its independent audit.\n',encoding='utf-8')
paths=[Path(p)for p in old['bound_files']]+[P/'prepare_source_revision_2.py',Path(__file__),P/'source-correction-history.json',P/'source-extraction-revision-1/preservation-map.json',P/'source-extraction-revision-1/package-freeze.json']
bound={str(p):sha(p)for p in sorted(set(paths),key=str)}
new={**old,'revision':2,'frozen_at':now,'bound_files':bound,'bound_file_count':len(bound),'author_check_count':v['check_count'],'supersedes_freeze_sha256':sha(P/'source-extraction-revision-1/package-freeze.json'),'correction_history_sha256':sha(P/'source-correction-history.json'),'revision_scope':'Fact-level locator, lifetime descriptive wording and two right crop margins only. All numeric/table/formula data unchanged.'}
write(P/'package-freeze.json',new)
print(json.dumps({'freeze_sha256':sha(P/'package-freeze.json'),'facts_sha256':sha(P/'source-facts.json'),'source_tables_sha256':sha(P/'source-tables.json'),'bound_files':len(bound),'checks':v['check_count'],'correction_history_sha256':sha(P/'source-correction-history.json')}))
