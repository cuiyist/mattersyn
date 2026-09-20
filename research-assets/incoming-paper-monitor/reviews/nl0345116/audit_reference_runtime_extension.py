"""Private, targeted read-only audit of the proposed PbSe validator/renderer delta."""
from pathlib import Path
import ast, base64, copy, hashlib, importlib.util, json, subprocess
from collections import Counter
from datetime import datetime, timezone

B = Path(__file__).resolve().parent
S = B.parents[3] / 'recipe-atlas'
V = B / 'visuals'
ASSETS = V / 'crystal-reference'
CID = 'sashchiuk-2004-pbse-ideal-reference'
read = lambda p: json.loads(p.read_text(encoding='utf8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
checks = []
def check(condition, label):
    checks.append({'check': label, 'passed': bool(condition)})

proposal_path = V / 'crystal-reference-proposal.json'
proposal = read(proposal_path)
source_audit = read(B / 'crystal-source-audit.json')
entry = proposal['entries'][0]
check(source_audit['status'].startswith('passed'), 'Independent source/artifact audit passed')
check(sha(proposal_path) == source_audit['crystal_reference_sha256'], 'Exact audited crystal proposal hash')
for f in proposal['files']:
    check(sha(ASSETS / f['path']) == f['sha256'] == source_audit['artifact_hashes'][f['path']], 'Audited asset hash: ' + f['path'])
check(entry['spaceGroupNumber'] == 1 and entry['prototypeSpaceGroupNumber'] == 225, 'Expanded P1 export distinct from ideal Fm-3m prototype')
check(entry['finiteModelPeriodic'] is False and entry['structureAssetRole'] == 'illustrative', 'Actual registry finite/illustrative flags are correct')

validator_path = B / 'check_quality-proposal.py'
spec = importlib.util.spec_from_file_location('private_quality_proposal', validator_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.CRYSTALS = {CID: module.CRYSTALS[CID]}
raw_load = module.load
records = {p.stem: read(p) for p in (B / 'canonical-drafts').glob('*.json')}

class PrivateAudit(module.Audit):
    def asset(self, base, relative, digest, label):
        return super().asset(ASSETS, relative, digest, label)

def run_validator(mutate=None):
    rows = copy.deepcopy(proposal)
    unit = read(ASSETS / entry['modelPath'])
    finite = read(ASSETS / entry['finiteModelPath'])
    if mutate:
        mutate(rows['entries'][0], unit, finite)
    def private_load(path):
        if path.name == 'registry.json': return rows
        if path.name == 'pbse-ideal-unit-cell.json': return unit
        if path.name == 'pbse-illustrative-block.json': return finite
        return raw_load(path)
    module.load = private_load
    audit = PrivateAudit(B)
    audit.byid = records
    audit.crystals()
    return {'checks': audit.counts['checks'], 'errors': audit.errors}

positive = run_validator()
check(not positive['errors'], 'Actual proposed PbSe crystal validator passes against frozen private artifacts')
negative = []
mutations = [
    ('P1 export changed to 225', lambda e,u,f: e.update(spaceGroupNumber=225)),
    ('Prototype changed from 225', lambda e,u,f: e.update(prototypeSpaceGroupNumber=1)),
    ('Wrong source hash', lambda e,u,f: u['source'].update(source_sha256='0'*64)),
    ('Wrong rounded cell parameter', lambda e,u,f: u['cell'].update(a=6.2)),
    ('Finite model made periodic', lambda e,u,f: f.update(periodic=True)),
    ('Finite model promoted to training', lambda e,u,f: f.update(training_eligible=True)),
    ('Finite model promoted to measured', lambda e,u,f: f.update(measured_sample_structure=True)),
    ('Finite model evidence promoted', lambda e,u,f: f.update(evidence_type='measured')),
    ('Unit-cell Pb:Se composition changed', lambda e,u,f: u['atoms'][0].update(element='Se')),
    ('Finite Pb:Se composition changed', lambda e,u,f: f['atoms'][0].update(element='Se')),
    ('Reference attached to an unrelated record', lambda e,u,f: e['record_ids'].append('unrelated')),
    ('Registry promoted to training', lambda e,u,f: e.update(trainingEligible=True)),
]
for name, mutate in mutations:
    result = run_validator(mutate)
    check(bool(result['errors']), 'Validator rejects in-memory negative control: ' + name)
    negative.append({'mutation': name, 'rejected': bool(result['errors']), 'errors': result['errors']})

gaps = []
for name, mutate in [
    ('finiteModelPeriodic', lambda e,u,f: e.update(finiteModelPeriodic=True)),
    ('structureAssetRole', lambda e,u,f: e.update(structureAssetRole='measured_sample')),
]:
    result = run_validator(mutate)
    if not result['errors']: gaps.append(name)

integrator_path = B / 'integrate_review.py'
integrator = integrator_path.read_text(encoding='utf8')
tree = ast.parse(integrator)
replacement = []
for node in ast.walk(tree):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'replace' and len(node.args) == 2:
        try: old, new = [ast.literal_eval(x) for x in node.args]
        except (ValueError, TypeError): continue
        if isinstance(old, str) and old.startswith('viewer.setStyle({}, {sphere:'):
            replacement.append((old, new))
check(len(replacement) == 1, 'Exactly one finite-renderer style replacement in integrator')
old, new = replacement[0]
renderer_path = S / 'dist/finite-crystal-reference.mjs'
runtime = renderer_path.read_text(encoding='utf8')
if old in runtime:
    original, proposed = runtime, runtime.replace(old, new)
    observed_runtime = 'original_style_before_integration'
else:
    check(new in runtime, 'Integrated runtime matches proposed color block')
    proposed, original = runtime, runtime.replace(new, old)
    observed_runtime = 'proposed_style_already_integrated'
check(original.count(old) == 1 and proposed.count(new) == 1, 'Replacement applies once')
check(original.replace(old, '') == proposed.replace(new, ''), 'All non-style runtime code remains byte-for-byte identical')
check("{Pb:'#8b9bae',Se:'#bc8957'}" in new and "||'#6b95b3'" in new, 'Exact Pb and Se colors with unchanged Si/other-element fallback')

js = r"""
import {readFileSync} from 'node:fs';
const before = await import('data:text/javascript;base64,'+BEFORE);
const after = await import('data:text/javascript;base64,'+AFTER);
const pbse = JSON.parse(readFileSync(MODEL, 'utf8'));
const result = [];
function check(v,name){result.push({check:name,passed:!!v});}
function viewer(){const calls=[];return {calls,clear(){calls.push(['clear']);},addModel(){return {addAtoms(a){calls.push(['atoms',a]);}};},setStyle(...a){calls.push(['style',...a]);},zoomTo(){calls.push(['zoom']);},rotate(...a){calls.push(['rotate',...a]);},render(){calls.push(['render']);}};}
const a=viewer(),b=viewer();
const ca=before.drawFiniteReference(a,pbse),cb=after.drawFiniteReference(b,pbse);
check(JSON.stringify(a.calls.filter(x=>x[0]!=='style'))===JSON.stringify(b.calls.filter(x=>x[0]!=='style')),'Runtime preserves all atom coordinates, bonds, camera and render operations');
check(ca===cb && cb===pbse.caption,'Finite caption return unchanged');
const styles=b.calls.filter(x=>x[0]==='style');
check(styles.length===2,'PbSe receives exactly two element selections');
for(const [el,color]of[['Pb','#8b9bae'],['Se','#bc8957']]){
 const s=styles.find(x=>x[1].elem===el);
 check(!!s&&s[2].sphere.color===color&&s[2].sphere.radius===.37&&s[2].stick.radius===.07&&s[2].stick.color==='#a0b7c6',el+' correct atom color, unchanged geometry/stick style');
}
const si={...pbse,atoms:[{...pbse.atoms[0],element:'Si',bonds:[],bondOrder:[]}]};
const sv=viewer();after.drawFiniteReference(sv,si);
check(sv.calls.find(x=>x[0]==='style')[2].sphere.color==='#6b95b3','Existing Si fallback preserved');
for(const [key,value]of[['periodic',true],['training_eligible',true],['measured_sample_structure',true],['representation','periodic_cell']]){
 let rejected=false;try{after.finiteReferenceAtoms({...pbse,[key]:value});}catch{rejected=true;}
 check(rejected,'Existing renderer rejects '+key+'='+value);
}
check(JSON.stringify(before.finiteReferenceAtoms(pbse))===JSON.stringify(after.finiteReferenceAtoms(pbse)),'All 4096 finite atoms unchanged by color extension');
console.log(JSON.stringify(result));
"""
for key, val in {
    'BEFORE': base64.b64encode(original.encode()).decode(),
    'AFTER': base64.b64encode(proposed.encode()).decode(),
    'MODEL': str(ASSETS / entry['finiteModelPath']),
}.items(): js = js.replace(key, json.dumps(val))
process = subprocess.run(['node', '--input-type=module', '-e', js], capture_output=True, text=True)
check(process.returncode == 0, 'Node mock-renderer validation executes without error')
runtime_checks = json.loads(process.stdout) if process.returncode == 0 else []
checks.extend(runtime_checks)
findings = []
if gaps:
    findings.append({'severity': 'nonblocking_consistency', 'scope': 'validator_registry_metadata', 'fields': gaps, 'finding': 'The actual proposal has correct values, and pinned model bytes plus model-level flags protect the rendered geometry. The PbSe registry branch does not independently reject contradictory values in these registry-only fields.', 'suggestion': 'Assert finiteModelPeriodic is False and structureAssetRole equals illustrative, matching the ideal-Si branch.'})
if 'plus one pinned ideal silicon reference' in validator_path.read_text(encoding='utf8'):
    findings.append({'severity': 'nonblocking_report_text', 'finding': 'Final validator report scope still describes one ideal silicon reference; the registry now has ideal silicon and PbSe references.', 'suggestion': 'Update the scope description to seven database CIFs plus two constructed ideal references.'})
report = {
    'source_id': 'sashchiuk2004', 'status': 'passed_with_nonblocking_consistency_notes' if findings else 'passed',
    'audited_at': datetime.now(timezone.utc).isoformat(),
    'scope': 'Targeted independent review of the changed PbSe publication validator and exact finite-renderer color extension. Executes only the crystal validator against private artifacts with virtual registry paths, plus an in-memory mock-renderer comparison. Does not run integration, full publication checks or a browser.',
    'proposal_sha256': sha(validator_path), 'validator_proposal_sha256': sha(validator_path),
    'crystal_reference_proposal_sha256': sha(proposal_path),
    'independent_crystal_audit_sha256': sha(B / 'crystal-source-audit.json'),
    'integrate_review_sha256': sha(integrator_path),
    'renderer_observed_state': observed_runtime,
    'renderer_original_content_sha256': hashlib.sha256(original.encode()).hexdigest(),
    'renderer_proposed_content_sha256': hashlib.sha256(proposed.encode()).hexdigest(),
    'positive_validator': positive, 'negative_controls': negative,
    'checks': checks, 'check_count': len(checks), 'findings': findings,
    'errors': [x['check'] for x in checks if not x['passed']],
    'site_mutated': False,
}
if report['errors']: report['status'] = 'failed'
(B / 'reference-runtime-extension-audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
print(json.dumps({k: report[k] for k in ['status','check_count','proposal_sha256','positive_validator','findings','errors']}, ensure_ascii=False, indent=2))
