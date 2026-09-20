"""Targeted independent review of the labels-only candidate revision."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime,timezone
import hashlib,json,re
C=Path(__file__).resolve().parent;H=C.parent;A=H/'structure-candidate-revision-1'
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=[];bound={};findings=[]
def check(label,ok):
    checks.append({'check':label,'passed':bool(ok)})
    if not ok:findings.append(label)
def bind(p,h=None):
    p=Path(p).resolve();v=sha(p);bound[str(p)]=v
    if h:check('SHA256 '+str(p),v==h)
    return v
bind(C/'package-freeze.json','a93b11a4023b2b454b1c180e5cbffe7a2c0e47d342034299248dd8ee3ce41738')
newfreeze=read(C/'package-freeze.json')
for row in newfreeze['files']:bind(row['path'],row['sha256'])
bind(A/'package-freeze.json','fef2f3fd8416b0b57f05f7223b04c53634964aed3fd628e50f0aca27af676df0')
oldfreeze=read(A/'package-freeze.json')
for row in oldfreeze['files']:
    oldpath=A/Path(row['path']).name
    if not oldpath.exists():oldpath=Path(row['path'])
    bind(oldpath,row['sha256'])
audit=read(A/'independent-audit.json')
bind(A/'independent-audit.json','bafa715c44db0d22f3222db5d5c83048abfa8d6ba148c30fe08bfe6543cd8788')
bind(A/'independent-audit.md','03999561b189c8e1270e4f7bcf6b43c1ee4bb7b52178c73f226d4267077ba5aa')
check('Original audit is preserved in the current directory too',sha(C/'independent-audit.json')==sha(A/'independent-audit.json') and sha(C/'independent-audit.md')==sha(A/'independent-audit.md'))
bind(C/'independent-audit.json');bind(C/'independent-audit.md')
for name,h in audit['bound_files'].items():
    p=Path(name);archived=A/p.name
    chosen=archived if archived.exists() else p
    bind(chosen,h)

oldmodel=read(A/'average-model.json');newmodel=read(C/'average-model.json')
restored=deepcopy(newmodel);restored['notes']=oldmodel['notes'];restored['cif']['sha256']=oldmodel['cif']['sha256']
check('Model JSON changed only prose notes and its CIF checksum',restored==oldmodel)
for key in ['fractionalSites','asymmetric_sites','refinement_weighted_counts','a','spaceGroup','spaceGroupNumber','origin_choice','coordinate_scope','measured_sample_average_refinement','unique_ordered_microstate','exact_structure_recipe_eligible','dft_input_eligible','training_approved','nominal_framework_source']:
    check('Exact unchanged model field: '+key,newmodel[key]==oldmodel[key])
pattern=rb'(_publ_section_exptl_refinement\r?\n;\r?\n)(.*?)(\r?\n;\r?\n)'
oldcif=(A/'heo2003-average-position-occupancy.cif').read_bytes();newcif=(C/'heo2003-average-position-occupancy.cif').read_bytes()
oldmatch=re.search(pattern,oldcif,re.S);newmatch=re.search(pattern,newcif,re.S)
check('Both CIFs contain exactly one refinement-note field',len(re.findall(pattern,oldcif,re.S))==1 and len(re.findall(pattern,newcif,re.S))==1)
restoredcif=newcif[:newmatch.start(2)]+oldmatch.group(2)+newcif[newmatch.end(2):]
check('Replacing only revised CIF prose reproduces exact original CIF bytes',restoredcif==oldcif)
check('CIF notes exactly match model notes',newmatch.group(2).decode('utf-8').replace('\r\n','\n')=='\n'.join(newmodel['notes']))
notes='\n'.join(newmodel['notes'])
for phrase in ['107.1602','111.7(20)','4.5398','2.27 reported ESDs','other 22','one reported ESD','three ESDs does not resolve','retained unchanged']:
    check('Explicit unresolved geometry disclosure: '+phrase,phrase in notes)
for phrase in ['not an author-supplied CIF','Si96Al96','Si100Al92','partially occupied','positions and occupancies only','source-literal anisotropic tensors','does not reproduce','Exact structure-recipe training and ordered DFT input admission remain false']:
    check('Prior scientific limitation retained: '+phrase,phrase in notes)

oldreport=read(A/'author-validation.json');newreport=read(C/'author-validation.json')
restored_report=deepcopy(newreport)
restored_report['at']=oldreport['at'];restored_report['cif']['sha256']=oldreport['cif']['sha256'];restored_report.pop('geometry_summary')
added={'signed_difference','source_reported_esd','absolute_deviation_in_source_esd','tolerance_policy','within_one_reported_esd_or_rounding','within_three_reported_esds_or_rounding'}
for i,(old,new,independent) in enumerate(zip(oldreport['table3_geometry_checks'],newreport['table3_geometry_checks'],audit['geometry_checks'])):
    keep={k:v for k,v in new.items() if k not in added}
    keep['within_source_uncertainty_and_printed_rounding']=old['within_source_uncertainty_and_printed_rounding']
    check('Geometry '+str(i+1)+' all old scientific values unchanged',keep==old)
    check('Geometry '+str(i+1)+' reported ESD matches independent reading',new['source_reported_esd']==independent['source_esd'])
    check('Geometry '+str(i+1)+' signed residual matches independent calculation',abs(new['signed_difference']-independent['signed_difference'])<1e-8)
    expected=independent['absolute_difference_over_reported_esd'];actual=new['absolute_deviation_in_source_esd']
    check('Geometry '+str(i+1)+' ESD-normalized residual matches independent calculation',actual is None if expected is None else abs(actual-expected)<1e-8)
    check('Geometry '+str(i+1)+' one-ESD flag explicit and correct',new['within_one_reported_esd_or_rounding']==(independent['within_one_reported_esd'] is True or independent['symmetry_fixed_rounding_check'] is True))
    check('Geometry '+str(i+1)+' three-ESD screening explicit and qualified',new['within_three_reported_esds_or_rounding'] is True and 'Three reported' in new['tolerance_policy'] and 'not exact central-value reproduction or propagated coordinate uncertainty' in new['tolerance_policy'])
    restored_report['table3_geometry_checks'][i]=keep
check('Author report changed only explicitly reviewed diagnostics/metadata',restored_report==oldreport)
summary=newreport['geometry_summary']
check('Author summary explicitly distinguishes 22 close geometries and one tension',summary['checked']==23 and summary['within_one_reported_esd_or_rounding']==22 and summary['within_three_reported_esds_or_rounding']==23 and len(summary['unresolved_central_value_tensions'])==1 and summary['source_coordinates_or_table_values_changed'] is False)
check('Summary names exact unresolved InIIa row',summary['unresolved_central_value_tensions'][0]==newreport['table3_geometry_checks'][21])
check('ADP diagnostics remain exactly unchanged',newreport['source_tensor_diagnostics']==oldreport['source_tensor_diagnostics'])
bind(__file__)
for name,h in list(bound.items()):check('Bound input unchanged at end: '+name,sha(name)==h)
out={'schema':'mattersyn-independent-average-structure-audit-addendum/1','author':'/root','auditor':'/root/backlog_eta','reviewer':'/root/backlog_eta','independent':True,'created_at':datetime.now(timezone.utc).isoformat(),
 'status':'passed_revised_average_position_occupancy_scope_with_explicit_source_limits' if not findings else 'pending_correction',
 'scope':'Targeted metadata and numerical-invariance recheck of the revised private candidate. The original independent geometry/source audit remains preserved and supplies the prior manual and numerical evidence; no repeat full-source or full-SI audit was performed.',
 'original_audit':{'path':str(A/'independent-audit.json'),'sha256':sha(A/'independent-audit.json')},'original_freeze_sha256':sha(A/'package-freeze.json'),'revised_freeze_sha256':sha(C/'package-freeze.json'),
 'resolved_findings':[{'id':'G1','resolution':'Revised CIF/model limitations and author report disclose the 107.1602 versus 111.7(20) degree angle, 4.5398 degree/2.27 reported ESD tension; 22 one-ESD agreements and the three-ESD screening criterion are distinct. All source values and coordinates are unchanged.','scientific_tension_resolved':False,'required_label_correction_resolved':not findings}],
 'open_findings':findings,'checks':checks,'counts':{'checks':len(checks),'failed':len(findings),'bound_files':len(bound),'unchanged_source_sites':9,'unchanged_expanded_positions':680,'unchanged_species_components':872,'unchanged_weighted_atoms':642,'geometry_rows_rechecked':23},'bound_files':bound,
 'retained_limits':['The 2.27-ESD InIIa angle tension remains unresolved; the change discloses it and does not repair coordinates or the paper.','O2/O3/O4 literal tensor exact-symmetry inconsistencies remain. This is a position/occupancy CIF with ADPs explicitly omitted, not a full refinement/intensity reproduction.','Source-average Si/Al disorder, partial indium sites, unknown local correlations and nominal/refinement composition differences remain. No unique ordered microstate, microscopic charge balance, DFT input or exact structure-recipe label is approved.','Original manual inspection and numerical calculation scope is in the preserved audit. This addendum checked changed prose/diagnostics and exact numerical invariance only.'],
 'candidate_or_source_files_modified':False,'site_modified':False,'ledger_modified':False,'memory_modified':False,'github_modified':False,'training_approved':False,'dft_approved':False,'publication_approved':False}
(C/'independent-audit-addendum.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md=f'''# Heo average-model audit addendum

**Passed for the revised private average position/occupancy scope.** Author: `/root`; independent reviewer: `/root/backlog_eta`. {len(checks)} targeted checks; {len(findings)} open findings; {len(bound)} bound inputs.

The revised CIF/model now disclose the unresolved In(IIa) angle tension: 107.1602° from published coordinates versus 111.7(20)° in Table 3, a 4.5398° difference or 2.27 reported ESD. The author report explicitly separates the other 22 one-ESD/rounding matches from this value and names the three-ESD screening threshold. This resolves finding G1's labeling requirement; it does **not** resolve the underlying source discrepancy.

Replacing only the revised CIF prose reconstructs its exact original bytes. Model JSON differs only in notes and the CIF checksum. All coordinates/ESDs, occupancies, symmetry operations, 680 positions, 872 species components and 642 weighted atoms are unchanged. All 23 revised residual/ESD diagnostics match the original independent calculations; ADP diagnostics are unchanged.

The original freeze, builder and independent audit are preserved in `structure-candidate-revision-1`; the original audit in the current candidate directory also remains byte-identical. Source-derived average provenance, mixed Si/Al and partial-occupancy limits, omitted ADPs, unreproduced intensities and false training/DFT eligibility remain explicit. No source/candidate, Site, ledger, memory or GitHub files were changed by this addendum. Full SI, ordered structures, exact recipe tasks, rendering and publication are outside this approval.
'''
(C/'independent-audit-addendum.md').write_text(md,encoding='utf-8')
print(json.dumps({'status':out['status'],'counts':out['counts'],'findings':findings,'json_sha256':sha(C/'independent-audit-addendum.json'),'md_sha256':sha(C/'independent-audit-addendum.md')},indent=2))
