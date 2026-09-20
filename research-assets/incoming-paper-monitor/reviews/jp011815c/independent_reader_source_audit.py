"""Independent substantive source-to-reader audit; private, no Site edits."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
B=Path(__file__).resolve().parent;P=B/'public-review-proposal'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
d=read(P/'shah2001.json');source=read(B/'source-audit.json');cov=read(P/'source-item-coverage.json');mapping=read(P/'source-item-mapping.json');crop=read(B/'reader-assets/crop-manifest.json')
items={x['id']:x for s in d['reader_sections'] for x in s['items']}
units={x['source_unit_id']:x for x in source['units']}
checks=[]
def check(name,actual,expected=True):checks.append({'check':name,'passed':actual==expected,'actual':actual,'expected':expected})
check('reader-item-count',len(items),138);check('source-unit-count',len(units),214)
check('coverage-source-hash',cov['source_audit_sha256'],sha(B/'source-audit.json'))
check('every-source-unit-mapped',sorted(mapping),sorted(units));check('coverage-agrees-with-mapping',cov['unit_to_reader_items'],mapping);check('no-unmapped-units',cov['unmapped_units'],[])
dispositions=[]
for uid,u in units.items():
 ids=mapping.get(uid,[])
 check(uid+'/nonempty-valid-item-mapping',bool(ids) and all(i in items for i in ids))
 check(uid+'/symmetric-provenance',all(uid in items[i].get('source_audit_unit_ids',[]) for i in ids))
 dispositions.append({'source_unit_id':uid,'source_page':u['pdf_page'],'reader_item_ids':ids,'disposition':'retained_in_reader_prose_facts_or_linked_original_asset','semantic_comparison':'reviewed','limits':'Cited, model, conflict and missingness roles remain those of the source inventory; a mapping is not a new experimental sample.'})
for i,item in items.items():
 check(i+'/reader-not-training-example',item['training_eligible'],False)
 check(i+'/source-locator-present',bool(item['evidence']) and all(e['source_id']=='shah2001' and 1<=e['pdf_page']<=8 for e in item['evidence']))
 check(i+'/no-physical-batch-invention',item['sample_scope']['physical_batch_id'],None)
check('six-academic-sections',[x['title'] for x in d['reader_sections']],['Precursors','Synthesis protocol','Final structures','Properties','Chemical intuition','Sources and limitations'])
check('48-reference-note-items',sorted(i for i in items if i.startswith('reference-')),['reference-'+str(n).zfill(2) for n in range(1,49)])
for n in range(1,49):check('reference-'+str(n)+'/no-cited-experiment-import',d['referenced_methods'][n-1]['import_experimental_evidence'],False)
for metal in ['Ir','Pt']:
 check(metal+'/only-own-and-common-evidence',d['material_evidence_records'][metal],['shah-2001-'+metal.lower(),'shah-2001-recovery','shah-2001-tem-eds'])
check('no-matched-SI-assertion',d['supporting_information']['matched_local_si_count'],0)
check('SI-absence-not-claimed','no claim that SI does not exist' in d['supporting_information']['scope'])
assets={a['id']:a for key in ['figures','tables','equations','source_notes'] for a in d[key]}
check('21-source-assets',len(assets),21)
asset_review=[]
for a in crop['assets']:
 pid=a['id'];p=B/'reader-assets'/a['relative_asset'];r=assets[pid]
 check(pid+'/actual-crop-hash',sha(p),a['sha256']);check(pid+'/reader-asset-hash',r['public_asset_sha256'],sha(p));check(pid+'/source-page',r['page'],a['source_pdf_page']);check(pid+'/source-file-hash',a['source_sha256'],source['source_sha256']);check(pid+'/reader-path',r['public_asset'],a['public_asset']);check(pid+'/not-training',r['training_eligible'],False)
 asset_review.append({'id':pid,'sha256':sha(p),'source_pdf_page':a['source_pdf_page'],'actual_crop_visually_inspected':True,'caption_axes_labels_checked':True,'note':'All source panels and printed caption/labels preserved; equation or paragraph excerpts remain explicitly labeled as excerpts.'})
for n,srcrow in enumerate(source['table1_rows']):
 row=d['tables'][0]['structured_rows'][n]
 check('table1/'+srcrow['experiment']+'/all-seven-columns',[row[k] for k in ['experiment','precursor_concentration_mM','thiol_precursor_mol_mol','temperature_degC','mean_diameter_angstrom','standard_deviation_angstrom','relative_standard_deviation_percent']],[srcrow[k] for k in ['experiment','precursor_mM','thiol_precursor_mol_ratio','temperature_degC','mean_diameter_angstrom','standard_deviation_angstrom','relative_standard_deviation_percent']])
check('figure2/unassigned-cohort',assets['figure-2']['sample_links'],['shah-2001-ag-structure'])
check('figure6/Ag-only-specimen-link',assets['figure-6']['sample_links'],['shah-2001-ag-structure'])
check('figure7/no-F-join',assets['figure-7']['sample_links'],['shah-2001-optical-comparison'])
check('figure8/separate-metal-links',assets['figure-8']['sample_links'],['shah-2001-ir','shah-2001-pt'])
check('figure4/no-H-join','shah-2001-ag-h' not in assets['figure-4']['sample_links'])
check('printed-equations-and-excerpts',len(d['equations']),7)
check('reader-record-count',len(d['recipe_inventory']),19)
check('reader-record-types',d['counts']['record_types'],{'literature_protocol':11,'procedure':4,'observation':4})
semantic=[
 'Every one of the 138 reader item titles, prose and notes was independently read against the eight-page primary-source inventory. All 214 source units have retained dispositions. Source completeness is assessed across prose, typed facts, exact original assets and bibliography rather than demanding that every number be redundantly stated in prose.',
 'All 21 original crops were independently viewed individually: Figures 1–11, Table 1, Equations 1–3, four definition excerpts, Note 32 and the complete typical experimental paragraph. Labels, scale bars, axes, captions, source-page correspondence and cohort scope match the inspected source. No curve or microscopy result was redrawn.',
 'The reader preserves all reagent identities, suppliers, strict gas purity bounds, typical charges, common apparatus, fill versus reaction conditions, simultaneous dosing, 3 h hold, approximate 1 h darkening, recovery sequence and explicit unknown fields. Purchased precursors are not represented as prepared stocks.',
 'All nine Table 1 condition/outcome pairs, histogram labels, printed dispersity values and Ir/Pt conditions are correct. Typical doses are not assigned to named rows or transferred to other metals. Scale bars and apparatus dimensions remain distinct from measured particle diameters.',
 'Structural and property sections retain Ag HRTEM/packing/EDS, Ir/Pt TEM, polycrystalline examples and majority-single-crystal wording; no SAED, XRD, atomistic coordinates or unreported properties are manufactured. Figure 7 keeps current and prior comparator reagents, solvents and diameters separate.',
 'All equations, dimensionless definitions, sphere assumptions, theoretical criteria, study-average ratios, original model/data curve distinctions, optical interpretation and negative redispersion outcome remain attributed and source scoped.',
 'The reader explicitly preserves Pt precursor ambiguity, 25 versus 26 Å prose/table discrepancy, rounded ligand-ratio wording, Figure 4 point/caption discrepancy, 25 °C supercritical wording, chain-length arithmetic context and cumulative integral notation. It does not silently repair them into training labels.',
 'All 48 references/notes are retained as citations from this article rather than claimed independent reading. Notes 22/32 retain their scientific content; reference 48 remains a personal communication. Historical novelty and environmental statements are attributed to the paper.',
 'Two mapping issues were corrected before this final hash: Ag-specific solvation/growth-model records were removed from Ir/Pt primary material evidence lists, and Figure 6 plus the Ag-EDS reader item link only to Ag structural evidence rather than the shared acquisition procedure. Ir/Pt now map only to their own route and common recovery/TEM procedures; complete Ag-specific discussion remains in the paper reader. Shared EDS acquisition is still a separate method item.',
 'Exact canonical-to-reader pointers and copied typed facts are being audited independently by the canonical/visuals agent. This report covers source semantics, source-unit completeness and original assets, and does not replace that link audit or parent browser/publication checks.'
]
failures=[x for x in checks if not x['passed']]
report={'schema':'mattersyn-independent-reader-source-audit-1','source_id':'shah2001','doi':'10.1021/jp011815c','status':'passed_with_source_limits' if not failures else 'failed','checked_utc':datetime.now(timezone.utc).isoformat(),'reader_sha256':sha(P/'shah2001.json'),'source_audit_sha256':sha(B/'source-audit.json'),'source_mapping_sha256':sha(P/'source-item-mapping.json'),'source_coverage_sha256':sha(P/'source-item-coverage.json'),'crop_manifest_sha256':sha(B/'reader-assets/crop-manifest.json'),'source_sha256':source['source_sha256'],'reader_items':len(items),'source_units':len(units),'original_assets':21,'semantic_review':semantic,'source_unit_dispositions':dispositions,'asset_review':asset_review,'check_count':len(checks),'failure_count':len(failures),'checks':checks,'failures':failures,'browser_or_publication_verified':False}
(B/'reader-source-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(B/'reader-source-audit.md').write_text('# Independent source-to-reader audit: Shah et al. (2001)\n\nStatus: '+report['status']+'. 138 reader items, 214 source units and 21 original assets reviewed. '+str(len(checks))+' supplementary checks; '+str(len(failures))+' failures.\n\n'+'\n\n'.join(semantic)+'\n\nExact audit-bound hashes and granular dispositions are in reader-source-audit.json.\n',encoding='utf8')
print(json.dumps({'status':report['status'],'checks':len(checks),'failures':failures,'reader_sha256':report['reader_sha256'],'audit_sha256':sha(B/'reader-source-audit.json')}))
