from pathlib import Path
import json,hashlib,datetime
O=Path(__file__).resolve().parent;F=O.parent;C=F/'canonical-proposal/draft-v2'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
freeze=read(C/'package-freeze.json');bound={str(C/'package-freeze.json'):sha(C/'package-freeze.json')}
for typ in ['bound_files','external_bound_inputs']:
 for p,h in freeze.get(typ,{}).items():
  fp=Path(p) if Path(p).is_absolute() else C/p
  bound[str(fp)]=sha(fp)
for n in ['check_transport.py','transport-checks.json','check_schema.py','schema-and-eligibility-checks.json','check_scopes.py','scope-and-public-projection-checks.json','sample-link-omissions.json']:
 bound[str(O/n)]=sha(O/n)
findings=[{'id':'FR-CAN-01','severity':'reader_presentation','status':'open','scope':'Display prose, titles and notes only','finding':'Compressed extraction tokens, raw panel-assignment JSON and empty missingness sentences remain in human-facing reader prose.','examples':['operation-acid-charge','operation-acid-acidify','operation-acid-cold-hold','source-figures-figure-3','source-conflicts-c10','unit-friedfeld2019-unit-si-contents-1'],'required_change':'Use readable academic display text, retaining all raw source payloads and typed scientific fields unchanged.'},{'id':'FR-CAN-02','severity':'reader_binding','status':'open','scope':'62 source-sample_contexts-* cards','finding':'Cards link generic source-payload-context but omit the existing exact named sample in that owner record.','evidence_file':str(O/'sample-link-omissions.json'),'required_change':'Add the 62 existing record/sample/product-pointer links. Do not create a new sample or physical-batch association.'}]
manual=[
'Read all six reader sections, all 417 item titles/text and their notes; scientific narratives agree with the independently audited effective source, subject to the display corrections.',
'Reviewed all 30 record boundaries: one representative route, three explicit variants, 15 procedures and 11 observations; cited methods are gaps, not invented recipes.',
'Inspected all 58 operation instances, material-state fractions and acquisition input boundaries; distinct specimens are not physically pooled; drying has no reagent output.',
'Reviewed 77 material slots and all eight stocks. Varied-concentration stock excludes 20 mg / 0.00121 mmol, and common 1 mL solvent is explicitly inherited.',
'Reviewed all 39 condition alternatives: temperature-only series, exact acid/indium paired series, six concentration comparisons, exchange levels and unresolved 30/72 h pretreatment.',
'Checked labeled-acid CO2 condensation, external coolant separation, retained organic fractions, acid filtration/evaporation and crystal/mother-liquor separation.',
'Checked distillation residue retention and GPC product fraction-set wording; no exact InP/In2O3 proportion, purity or cross-technique batch join.',
'Checked prior cluster structure, current noncrystalline pretreatment, NMR solutions, 150/250 degree C TEM, FFT not SAED, Scherrer not TEM and oxide-mixture scopes.',
'Checked all source conflicts, including temperature labels, CO2 bulb volumes, NMR 202 Hz, 30/72 h, oleate/myristate, malformed DSC rate, eV values and fit-box/prose differences.',
'Checked all 51 selected original assets by exact hash and public path against passed source-audit assets; this audit does not claim a second fresh full 33-page or 51-crop visual examination.',
'Confirmed 207 semantic units, 65 source facts, 185 table quantities, 750 measurements, 2131 exact typed reader fields, all references/equations/schemes and 44 figure mappings mechanically.',
'Directly executed current schema/semantic eligibility and current reader validator on frozen private inputs, without executing the author builder. All tasks and atomic/publication approvals remain closed.'
]
out={'schema':'mattersyn-independent-canonical-reader-audit/1.0','status':'findings','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_id':'friedfeld2019','auditor':'peng1998_reader_assets','author':'norberg2004_extract','role_disclosure':'Auditor authored original source extraction but did not author canonical/reader records. Effective source revision 2 was independently audited and passed by backlog_eta. This is distinct source-to-canonical/reader transport review, not a self-audit of extraction or own product illustrations.','proposal_freeze_sha256':sha(C/'package-freeze.json'),'source_audit_sha256':sha(F/'source-independent-audit/independent-audit-v2.json'),'open_findings':findings,'canonical_scientific_findings':[],'supporting_check_counts':{'transport':read(O/'transport-checks.json')['check_count'],'scope_and_projection':read(O/'scope-and-public-projection-checks.json')['check_count'],'schema_records':30},'manual_scopes':manual,'actual_original_source_scope':'Original full 8 main + 25 SI pages were read/viewed during source authorship; this downstream pass uses the frozen independently passed source packet. Targeted source reinspection during accompanying product preparation covered main PDF 4/5 and SI10. No new full-page read is claimed here.','exclusions':['Molecular qualification and exact slot-binding audit','Own symbolic product-context proposal','Apparatus illustration audit','Site integration, browser, publication and training admission'],'bound_files':bound}
(O/'independent-audit-v2.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(O/'independent-audit-v2.md').write_text('# Friedfeld canonical/reader v2 audit\n\nStatus: findings. The canonical scientific transport passed; two reader corrections remain.\n\n'+out['role_disclosure']+'\n\n'+ '\n'.join('- '+s for s in manual)+'\n\n'+ '\n'.join('- '+x['id']+': '+x['finding'] for x in findings)+'\n\nSource, author records, reader and Site were not modified.\n',encoding='utf8')
print(sha(O/'independent-audit-v2.json'),len(bound))
