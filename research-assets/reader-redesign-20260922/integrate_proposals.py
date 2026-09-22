from pathlib import Path
import json, shutil
WORK=Path(__file__).resolve().parent
ROOT=WORK.parents[1]/'recipe-atlas'
DIST=ROOT/'dist'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
# Preserve concurrent root edits: replacements are limited to agent-owned modules.
for f in (WORK/'metrics-proposal/files').rglob('*'):
    if f.is_file():
        out=ROOT/f.relative_to(WORK/'metrics-proposal/files');out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,out)
p=ROOT/'scripts/build_dataset.py';s=p.read_text(encoding='utf-8')
if 'from structure_recipe_metrics import' not in s:
    s='from structure_recipe_metrics import load_structure_policy, structure_recipe_coverage\n'+s
    s=s.replace('    groups=build_groups(records);','    structure_policy = load_structure_policy(ROOT)\n    structure_coverage = structure_recipe_coverage(records, structure_policy, ROOT / "dist")\n    groups=build_groups(records);')
    s=s.replace('ee=eligibility(r);','ee=eligibility(r, structure_policy);').replace('x=training_view(r,task);','x=training_view(r,task, structure_policy);')
    s=s.replace("    queue=ROOT/'data/pilot-source-queue.json'","    report['structure_recipe_coverage'] = {k:v for k,v in structure_coverage.items() if k != 'records'}\n    dump(public / 'structure-recipe-coverage.json', structure_coverage)\n    queue=ROOT/'data/pilot-source-queue.json'")
scope='Sample-coordinate availability, explicit source links and exact-task readiness are reported separately in structure_recipe_coverage; none is an independent-experiment count.'
s=s.replace('No source-reviewed exact experimental CIF-to-complete-recipe pair is established.',scope).replace('No verified exact experimental CIF-to-complete-recipe pairs.',scope).replace("'0.33.0'","'0.34.0'")
p.write_text(s,encoding='utf-8')
shutil.copy2(WORK/'presentation-proposal/reader-presentation.json',DIST/'data/reader-presentation.json')
cp=WORK/'crystal-proposal';regpath=DIST/'assets/crystal-references/registry.json';reg=read(regpath)
entries={r['id']:r for r in reg['entries']}
for item in read(cp/'registry-additions.json')['entries'] if isinstance(read(cp/'registry-additions.json'),dict) else read(cp/'registry-additions.json'):entries[item['id']]=item
for change in read(cp/'existing-binding-extensions.json'):
    ref=entries[change['id']]
    ref['record_ids']=sorted(set(ref['record_ids']+change['add_record_ids']))
    ref['bindingScopes']={rid:change['phaseScope'] for rid in change['add_record_ids']}
    ref['sourceType']=change['sourceType'];ref['defaultForSample']=False
reg['entries']=list(entries.values());write(regpath,reg)
shutil.copytree(cp/'assets/crystal-references',DIST/'assets/crystal-references',dirs_exist_ok=True)
shutil.copy2(cp/'provenance.json',DIST/'assets/crystal-references/reader-reference-provenance.json')
shutil.copy2(cp/'all-material-gap-matrix.json',DIST/'data/reader-structure-coverage.json')
print('Integrated metrics, presentation and qualified reference assets; canonical records untouched.')
