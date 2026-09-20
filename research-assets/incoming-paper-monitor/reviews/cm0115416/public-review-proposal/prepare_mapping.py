"""Assemble reusable exact-pointer mapping with Yi-specific semantic targets."""
from pathlib import Path
O=Path(__file__).resolve().parent;B=O.parent;old=B.parent/'jp0208743/public-review-proposal/canonical_mapping.py'
s=old.read_text(encoding='utf8');header=s[:s.index('operation_targets=')].replace('7452+n','2909+n');loop=s[s.index('rowlinks={}') : s.index("out['record_formulation_labels']")]
loop=loop.replace("target='sulfur-source'","target='stock-a-composition' if stock['id']=='solution-a-stock' else 'stock-b-composition'")
loop=loop.replace('Repeated common glass steps are inherited context, not evidence of separate physical fusion batches.','Shared preparation steps retain source-defined applicability; repeated procedure context does not establish separate physical batches or supply missing variant charges.')
footer="""
out['record_formulation_labels']={rid:[p['sample_id'] for p in d.get('products',[])] for rid,d in drafts.items()}
out['record_formulation_scope_note']='Record IDs are required for sample labels. Source-specific 800 °C XRD/TEM, generic optical/sizing contexts, five temperature endpoints, incomplete Er variants and bulk comparator remain distinct; shared protocols do not establish physical batch identity.'
out['counts'].update({'typed_characterization_rows':len(rowlinks),'linked_operations':len(operationlinks),'operation_parameter_facts':len(parameterlinks),'reagent_quantity_facts':len(materiallinks),'stock_quantity_facts':len(stocklinks)})
(O/'canonical-measurement-coverage.json').write_text(json.dumps({'measurement_count':len(rowlinks),'measurement_to_reader_item':rowlinks,'operation_count':len(operationlinks),'operation_to_reader_item':operationlinks,'operation_parameter_count':len(parameterlinks),'operation_parameter_to_reader_item':parameterlinks,'material_quantity_count':len(materiallinks),'material_quantity_to_reader_item':materiallinks,'stock_quantity_count':len(stocklinks),'stock_quantity_to_reader_item':stocklinks,'draft_sha256':{k:sha(B/'canonical-drafts'/f'{k}.json') for k in drafts}},ensure_ascii=False,indent=2)+'\\n',encoding='utf8')
"""
(O/'canonical_mapping.py').write_text(header+(O/'canonical_targets.py').read_text(encoding='utf8')+'\n'+loop+footer,encoding='utf8');print('Prepared exact Yi canonical mapping')
