from pathlib import Path
O=Path(__file__).resolve().parent;B=O.parent
s=(B.parent/'cm0115416/public-review-proposal/canonical_mapping.py').read_text(encoding='utf8')
header=s[:s.index('operation_targets=')];start=header.index('def canon_evidence');end=header.index('def append_fact')
header=header[:start]+'''def canon_evidence(es):
 ee=[]
 for e in es:
  match=re.search(r'(Main|SI) PDF p\\. (\\d+)',e['locator'],re.I);n=int(match.group(2)) if match else None;role='si' if match and match.group(1).lower()=='si' else 'main'
  ee.append({'source_id':SID,'document_role':role,'pdf_page':n,'printed_page':10341+n if n and role=='main' else None,'locator':e['locator']})
 return ee
'''+header[end:]
loop=s[s.index('rowlinks={}'):s.index("out['record_formulation_labels']")]
loop=loop.replace("target='stock-a-composition' if stock['id']=='solution-a-stock' else 'stock-b-composition'","target=stock_targets[stock['id']]")
loop=loop.replace('Shared preparation steps retain source-defined applicability; repeated procedure context does not establish separate physical batches or supply missing variant charges.','Upstream nanotube oxidation may be inherited by the composite route; this does not establish separate experimental batches or fill unreported conditions.')
footer="""
out['record_formulation_labels']={rid:[p['sample_id'] for p in d.get('products',[])] for rid,d in drafts.items()}
out['record_formulation_scope_note']='Always pair record and sample IDs. Pristine/oxidized nanotubes, attached CdTe, free washings, no-tube comparator, control oxidation levels and author models are distinct contexts; common study identity does not establish a single physical batch.'
out['counts'].update({'typed_characterization_rows':len(rowlinks),'linked_operations':len(operationlinks),'operation_parameter_facts':len(parameterlinks),'reagent_quantity_facts':len(materiallinks),'stock_quantity_facts':len(stocklinks)})
(O/'canonical-measurement-coverage.json').write_text(json.dumps({'measurement_count':len(rowlinks),'measurement_to_reader_item':rowlinks,'operation_count':len(operationlinks),'operation_to_reader_item':operationlinks,'operation_parameter_count':len(parameterlinks),'operation_parameter_to_reader_item':parameterlinks,'material_quantity_count':len(materiallinks),'material_quantity_to_reader_item':materiallinks,'stock_quantity_count':len(stocklinks),'stock_quantity_to_reader_item':stocklinks,'draft_sha256':{k:sha(B/'canonical-drafts'/f'{k}.json') for k in drafts}},ensure_ascii=False,indent=2)+'\\n',encoding='utf8')
"""
(O/'canonical_mapping.py').write_text(header+(O/'canonical_targets.py').read_text(encoding='utf8')+'\n'+loop+footer,encoding='utf8');print('Prepared Banerjee canonical field mapping')
