from pathlib import Path
B=Path(__file__).resolve().parents[1];O=Path(__file__).resolve().parent
s=(B.parent/'ja036811v/public-review-proposal/validate_proposal.py').read_text(encoding='utf8').replace('schwartz2003','sashchiuk2004')
s=s.replace("ck('main/SI page count',[sources[k]['page_count'] for k in ['main','si']],[14,4])","ck('Supplied main page count',[sources[k]['page_count'] for k in sources],[7]);ck('SI not silently verified',r['supporting_information']['status'],'not_located')")
s=s.replace('list(range(1,52))','list(range(1,68))').replace("sorted(['figure-'+str(n) for n in range(1,12)]+['si-figure-'+str(n) for n in range(1,7)])","['figure-'+str(n) for n in range(1,6)]")
s=s.replace(" for n,m in enumerate(d['measurements']):expected.add((rid,f'/measurements/{n}'))"," for n,m in enumerate(d['measurements']):expected.add((rid,f'/measurements/{n}'))\n for n,o in enumerate(d.get('condition_options',[])):expected.update((rid,f'/condition_options/{n}/parameters/{k}') for k in o.get('parameters',{}))")
a=s.index("ck('Figure 5 scoped microscopy'");z=s.index("result={'status'",a)
s=s[:a]+"""ck('Figure1 individual and sphere contexts',assets['figure-1']['sample_links'],['sashchiuk-2004-individual-structure','sashchiuk-2004-sphere-structure'])
ck('Figure2 unresolved route remains observation context',assets['figure-2']['sample_links'],['sashchiuk-2004-wire-structure'])
ck('Figure4 optical aliquot context',assets['figure-4']['sample_links'],['sashchiuk-2004-absorption'])
ck('Figure5 device and electrical context',assets['figure-5']['sample_links'],['sashchiuk-2004-device-fabrication','sashchiuk-2004-electrical'])
ck('Material evidence record IDs',sorted(r['material_evidence_records']['PbSe']),sorted(drafts))
ck('All applicable source assets',sorted(r['material_original_asset_ids']['PbSe']),sorted(assets))
ck('Four explicit route evidence mappings',sorted(r['route_evidence_contexts']),sorted(x for x,d in drafts.items() if d['record_type']=='literature_protocol'))
ck('DOI displayed without inserted whitespace','10.1021/nl0345116' in items['identity']['text'])
"""+s[z:]
(O/'validate_proposal.py').write_text(s,encoding='utf8')
