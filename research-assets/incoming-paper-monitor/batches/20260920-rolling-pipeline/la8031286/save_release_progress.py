"""Refresh the fixed-cutoff queue and reader-facing work after verified release."""
from pathlib import Path
from datetime import datetime,timezone
import json,subprocess,sys,hashlib
P=Path(__file__).resolve().parent;MON=P.parents[2];M=P.parents[4];S=M/'recipe-atlas';D=MON/'deadline-20260920'
read=lambda p:json.loads(p.read_text('utf8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
assert read(MON/'latest-publication.json')['dataset_version']=='0.31.0'
active=read(D/'active-cutoff.json');out=D/'pati-published-scope-20260920.json'
subprocess.run([sys.executable,str(D/'partition_deadline_scope.py'),'--cutoff-manifest',active['cutoff_manifest']['path'],'--ledger',str(MON/'ledger.json'),'--output',str(out)],check=True,capture_output=True)
counts=read(out)['counts'];active['counts']=counts;active['recorded_at']=datetime.now(timezone.utc).isoformat()
active['latest_status_partition']={'path':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()};save(D/'active-cutoff.json',active)
ed=read(MON/'public-progress-editorial.json')
ed['current_work']=[{'short_label':'Friedfeld et al. (2019)','title':'Conversion of InP Clusters to Quantum Dots','stage':'Full-source extraction and separate independent comparison',
 'summary':'The eight-page main article and 25-page supporting information have been read by the extractor and a separate reviewer. Extraction covers cluster conversion, ligand and isotope preparations, kinetics, diffraction and optical results. Final extraction/crop checks and independent comparison remain in progress.',
 'stages':[{'label':'Main/SI pairing and complete source reading','status':'complete','detail':'33 supplied pages inspected separately by author and auditor; original hashes matched intake.'},
 {'label':'Extraction and separate audit','status':'in_progress','detail':'The extraction author is checking figures and typed data. The independent reader has frozen a separate reading checkpoint; this is not approval of the author package.'},
 {'label':'Structured records and illustrations','status':'pending','detail':'Schema planning can proceed; canonical freezing waits for resolved source findings.'},
 {'label':'Website and publication','status':'pending','detail':'No Friedfeld contribution has been added to the live dataset.'}],
 'gaps':['Source tensions and numerical fit annotations remain explicit.','Exact specimen links, model provenance and training eligibility require their own review.']}]
n=counts['included_pending_scopes'];ed['estimate']['summary']=f'The two-month target covers the fixed existing collection. {n:,} provisional cutoff scopes remain pending, plus three nested identity cases. Achievable capacity and the recipe-bearing fraction remain unverified; screening is not complete scientific review.'
save(MON/'public-progress-editorial.json',ed)
for script in ['build_queue_report.py','build_public_progress.py']:
 subprocess.run([sys.executable,str(MON/script)],check=True)
print(json.dumps({'cutoff_counts':counts,'public_science':'0.31.0','Friedfeld_publication':False}))
