from pathlib import Path
A=Path(__file__).resolve().parent;N=A.parent
s=(N.parent/'acsanm.2c04342/site-integration-independent-audit/check_promotion.py').read_text('utf8')
s=s.replace("same(baseline['record_count'],586,'independent old-record count')","same(baseline['record_count'],607,'independent old-record count')")
s=s.replace("canonical-proposal/v1/record-manifest.json","canonical-proposal/v2/record-manifest.json").replace("public-review-proposal/v1/matuhina2023.json","public-review-proposal/v2/pati2009.json").replace("reader/matuhina2023.json","reader/pati2009.json")
s=s.replace('The supplied 13-page main and 13-page SI extraction passed distinct source audit. Canonical and reader independent review remain pending. Historical pending flags in immutable source payloads describe the author-freeze stage.','The complete supplied four-page main and four-page matched SI extraction passed distinct source audit. Canonical and reader proposals remain unapproved pending their separate review. Historical pending flags in retained source payloads describe their author-freeze stage.')
s=s.replace("same(len(records),21,'21 records');same(Counter(r['reader_role'] for r in records.values()),Counter({'synthesis_route':1,'supporting_procedure':13,'contextual_observation':7}),'roles 1/13/7')", "same(len(records),19,'19 records');same(Counter(r['reader_role'] for r in records.values()),Counter({'synthesis_route':3,'supporting_procedure':11,'contextual_observation':5}),'roles 3/11/5')")
s=s.replace("),39,'39 operations'", "),35,'35 operations'").replace("),678,'678 measurements'", "),268,'268 measurements'")
s=s.replace("old_gaps={'The distinct supplied main/SI source audit passed; canonical and reader independent approval remain pending.','Molecular, apparatus, product-context, model, browser and publication gates remain separate.'}", "old_gaps={'Complete supplied main/SI source extraction passed distinct audit; canonical/reader, visual, browser and publication gates remain separate.'}")
s=s.replace("def effective_read(name):return bind(V/name)", "effective_map=bind(V/'annotation-correction-v2/effective-file-map.json')\ndef effective_read(name):\n row=effective_map[name];same(sha(row['path']),row['sha256'],'Effective metadata hash '+name);return bind(row['path'])")
s=s.replace("same(len(reg['entries']),28,'28 molecular entries')", "same(len(reg['entries']),20,'20 molecular entries')")
s=s.replace("same(len(sol['contexts']),5,'five stocks')", "same(len(sol['contexts']),6,'six stocks')").replace(")),15,'15 components'", ")),12,'12 components'")
s=s.replace("same(len(assets),82,'82 public files')", "same(len(assets),66,'66 public files')").replace("'selected_original_scientific_crop':30,'reviewed_chemical_reference':44,'independently_audited_apparatus':1,'reviewed_symbolic_product_context':7", "'selected_original_scientific_crop':20,'reviewed_chemical_reference':34,'independently_audited_apparatus':1,'reviewed_symbolic_product_context':11").replace("'30 crops44 chemicals1module7symbols'", "'20 crops34 chemicals1module11symbols'")
s=s.replace("public={a['path']:a for a in bind(V/'public-asset-proposal.json')['assets']}","public=bind(V/'annotation-correction-v2/effective-public-assets.json')")
s=s.replace("apparatus['public_assets'][0]['sha256']", "sha(G/'visuals/apparatus/pati2009-protocol.mjs')")
start=s.index("Q0=G/'visuals/product-context'");end=s.index("Q=A/'private-validator-projection'",start)
s=s[:start]+'''Q0=G/'visuals/product-context'
orig=bind(Q0/'public-product-contexts-proposal.json');products=bind(P/'products/product-contexts-additions.json');expected=copy.deepcopy(orig)
for rid,rows in expected['recordContexts'].items():
 for row in rows:row['binding_approved']=True
same(products,expected,'ALL public product fields identical except approved binding metadata')
same(sum(map(len,products['recordContexts'].values())),39,'39 product contexts')
same(len({(rid,r['sample_id']) for rid,rows in products['recordContexts'].items() for r in rows}),39,'39 exact record/sample pairs')
orig=bind(Q0/'registry-additions.json');preg=bind(P/'products/registry-additions.json');rest=copy.deepcopy(preg)
for o,n in zip(orig['entries'],rest['entries']):
 same(n['binding_approved'],True,'product gate true '+n['id']);same(n['published'],False,'product publication false '+n['id']);restore(n,o,['binding_approved','published','independentScientificAudit'])
same(rest,orig,'ALL eleven symbolic product identities/captions/assets unchanged');same(len(preg['entries']),11,'eleven product symbols')
check(not re.search(r'[A-Z]:[\\\\/]|file://',json.dumps(products)),'no private product paths')
identity=bind(G/'intake-identity.json');same(identity['source_generation'],1,'Generation one retained')
for x in identity['file_copies']:bind(x['source_path']);same(sha(x['source_path']),x['sha256'],'Current original source bytes '+x['role'])
''' +s[end:]
s=s.replace("'source_id':'matuhina2023'", "'source_id':'pati2009'")
s=s.replace("'counts':{'records':21,'routes_variants':1,'procedures':13,'observations':7,'operations':39,'measurements':678,'reader_links':links,'entries':28,'material_slots':55,'stocks':5,'stock_components':15,'public_files':82,'product_contexts':47,'product_symbols':7}", "'counts':{'records':19,'routes_variants':3,'procedures':11,'observations':5,'operations':35,'measurements':268,'reader_links':links,'entries':20,'material_slots':45,'stocks':6,'stock_components':12,'public_files':66,'product_contexts':39,'product_symbols':11}")
s=s.replace('ALL 55 assignments','ALL 45 assignments').replace('55 slot assignments','45 slot assignments').replace('Exact 82-file','Exact 66-file').replace('Matuhina','Pati')
mdstart=s.index("(A/'promotion-delta-audit.md').write_text")
mdend=s.index("\nprint(json.dumps",mdstart)
s=s[:mdstart]+'''(A/'promotion-delta-audit.md').write_text(f"# Pati promotion delta audit\\n\\nStatus: **{result['status']}**; {len(checks)} independent checks; {len(findings)} open findings.\\n\\nThe exact root-authored proposal `{result['proposal_freeze_sha256']}` preserves all scientific content in 19 records, 35 operation instances and 268 measurements. Three solvent routes, eleven procedures and five observations remain distinct; no training task or atomic model is admitted.\\n\\nAll reader prose, quantities, conflicts and sample associations remain unchanged. Twenty chemical identities, 45 slots and six stocks/twelve components use the passed molecular annotation overlay. Thirty-nine symbolic product contexts preserve unknown as-prepared composition, local microscopy versus bulk XRD, and XPS exposure histories. The 66 public files are 20 selected crops, 34 chemical files, eleven symbolic product images and one separately audited apparatus module. No source PDF, complete text or whole-page render is included.\\n\\nThis is a private promotion audit. Installed transport, browser rendering and public delivery remain separate gates.\\n",encoding='utf8')
''' +s[mdend:]
(A/'check_promotion.py').write_text(s,'utf8')
print('Prepared Pati-specific independent promotion comparison.')
