"""Freeze private canonical/reader author proposals for a distinct review."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
P=Path(__file__).resolve().parent;C=P/'canonical-proposal'/'v1';V=P/'public-review-proposal'/'v1'
assert not(C/'package-manifest.json').exists(),'Frozen proposal must be revised separately.'
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
source=read(P/'package-freeze.json');auditpath=P/'source-independent-audit'/'independent-audit-v2.json';audit=read(auditpath)
assert audit['status']=='passed'and not audit['open_author_corrections']
assert audit['package_freeze_sha256']==sha(P/'package-freeze.json')
for path,h in source['bound_files'].items():assert sha(path)==h,path
for path,h in audit['bound_files'].items():assert sha(path)==h,path
cm=read(C/'record-manifest.json');rm=read(V/'reader-manifest.json');review=read(V/'morrison2017.json')
records={r['record_id']:read(r['path'])for r in cm['records']}
assert len(records)==18 and sum(len(r['operations'])for r in records.values())==24
assert all(r['quality']['review_status']=='imported_unreviewed'and r['quality']['requested_tasks']==[]and not r.get('collection')and r['structure_assets']==[]for r in records.values())
assert all(sha(r['path'])==r['sha256']for r in cm['records'])
assert all(sha(V/name)==h for name,h in rm['outputs'].items())
assert review['counts']['source_table_cells']==471 and review['counts']['typed_reader_fields']==1170
assert review['training_eligible']is False and review['source_review_promoted']is False
notes='''# Morrison 2017 — private canonical and reader proposal v1

The complete main/SI source extraction passed a distinct scientific audit after four bounded typing corrections. The original source revision and correction history remain preserved. This proposal requires its own independent canonical/reader audit; source passage does not approve its mappings.

The 18 records comprise two literature route families (excess-precursor thick-shell growth and controlled monolayer shell growth), eight supporting procedures and eight observation/reference contexts. The room-temperature precursor exposure/back-exchange branch remains a supporting procedure. All 24 source operations preserve their own conditions, inputs and retained fractions. Optical outcomes, yields and measured dimensions are retained as observations rather than synthesis-input parameters. The TEM branch does not consume the final optical dispersion.

The proposal represents all 72 source facts, 185 fact quantities, 176 source units and 471 table cells. It contains 64 material slots, five stock slots, 41 record-local specimen/model/reference contexts and 822 typed measurement/context entries. Those slot and context counts are not counts of independently prepared samples. Printed raw tokens, scales, uncertainties, bounds and source discrepancies remain accessible through field mappings and the private curated sidecar.

The reader contains five academic sections plus Sources and limitations, with 252 items and 1,170 exact canonical fields. Thirty selected original excerpts are proposed separately from all full-page renders and complete text caches. All 27 page-coverage entries, 52 references, original figure/table/scheme/equation distinctions and explicitly limited specimen associations are retained. The reader carries no local source paths or whole-page attachments.

The measured single-crystal tables describe Cd(PTC)2·THF precursor, not CdSe/CdS belts. No CIF, ordered model, molecular geometry or product atomic asset is created or admitted. Upstream ammonium phenyldithiocarbamate and CdSe-belt recipes remain cited-only. The 0.512 g starting charge is a dispersion mass, the total shell thickness spans both broad faces, and the same-specimen optical link in Figure 7 does not establish a universal TEM/XRD/elemental/optical sample join.

All records remain imported_unreviewed with no collection promotion and empty requested_tasks. No training rows, exact structure pairs, visual bindings, browser validation, Site imports or publication are approved. Current independent review should focus on phase-specific flow, source-bound quantities, specimen/context boundaries, the ten retained discrepancies and complete table transport.
'''
(C/'proposal-notes.md').write_text(notes,encoding='utf-8')
(V/'README.md').write_text('Private reader proposal: `morrison2017.json`. Exact field/item mappings are in `source-item-coverage.json`; candidate crop transport and future component/diagram slots are in `reader-bindings-proposal.json`. Canonical and reader independent review, molecular/apparatus qualification and browser/publication gates remain pending. Complete-source payloads are intentionally absent.\n',encoding='utf-8')
paths=[p for root in [C,V]for p in root.iterdir()if p.is_file()]
paths += [P/'build_canonical_proposal.py',P/'build_reader_proposal.py',Path(__file__),P/'package-freeze.json',auditpath,P/'source-correction-history.json',P/'source-facts.json',P/'source-inventory.json',P/'source-tables.json',P/'page-coverage.json',P/'original-assets-manifest.json']
paths += [Path(a['path'])for a in read(P/'original-assets-manifest.json')['assets']]
paths += [Path(p)for p in cm['input_modules']]
paths += [Path(p)for p in rm['input_hashes']]
bound={str(p.resolve()):sha(p)for p in sorted(set(paths),key=str)}
manifest={'schema':'mattersyn-private-canonical-reader-freeze/1','source_id':'morrison2017','doi':'10.1021/acs.inorgchem.7b01711','version':1,'author':'/root/backlog_eta','frozen_at':datetime.now(timezone.utc).isoformat(),'status':'author_proposal_source_audit_passed_canonical_reader_audit_pending','source_generation':2,'bundle_sha256':source['bundle_sha256'],'source_freeze_sha256':sha(P/'package-freeze.json'),'source_audit':{'path':str(auditpath),'sha256':sha(auditpath),'reviewer':audit['reviewer'],'status':audit['status'],'scope':audit['scope']},'canonical_record_manifest_sha256':sha(C/'record-manifest.json'),'reader_manifest_sha256':sha(V/'reader-manifest.json'),'reader_sha256':sha(V/'morrison2017.json'),'canonical_counts':cm['counts'],'reader_counts':review['counts'],'author_checks':{'canonical':read(C/'author-validation.json')['check_count'],'reader':read(V/'author-validation.json')['check_count']},'bound_files':bound,'bound_file_count':len(bound),'independent_canonical_reader_approval':False,'training_approved':False,'visual_model_approved':False,'browser_approved':False,'site_imported':False,'published':False,'publication_exclusions':['Original PDFs','Complete-source payload manifest','All private/text files','All source-render full-page images','Any complete-page attachments or local source paths'],'scope_notes_path':str(C/'proposal-notes.md')}
write(C/'package-manifest.json',manifest)
print(json.dumps({'manifest':str(C/'package-manifest.json'),'sha256':sha(C/'package-manifest.json'),'reader_sha256':sha(V/'morrison2017.json'),'bound_files':len(bound),'canonical_checks':manifest['author_checks']['canonical'],'reader_checks':manifest['author_checks']['reader']}))
