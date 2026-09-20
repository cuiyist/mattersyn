from pathlib import Path
import json
O=Path(__file__).resolve().parent;F=O.parent;C=F/'canonical-proposal/draft-v2'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
r=read(C/'reader/friedfeld2019.json');m=read(C/'record-manifest.json');sf=read(F/'source-extraction-revision-2/source-facts.json');inv=read(F/'source-extraction-revision-2/source-inventory.json');cov=read(C/'source-to-field-coverage.json');rc=read(C/'reader/source-item-coverage.json')
for sec in r['reader_sections']:
 lines=[]
 for it in sec['items']:
  lines.append('ITEM '+it['id']+' | '+it['title']+'\n'+it['text'])
  if it.get('notes'):lines.append('NOTES '+json.dumps(it['notes'],ensure_ascii=False))
  links=it.get('sample_scope',{}).get('canonical_sample_links',[])
  if links:lines.append('SAMPLES '+json.dumps(links,ensure_ascii=False,separators=(',',':')))
 (O/('reader-prose-'+sec['id']+'.txt')).write_text('\n\n'.join(lines),encoding='utf8')
lines=[]
for e in m['records']:
 rec=read(e['path']);lines.append('\nRECORD '+rec['record_id'])
 for op in rec['operations']:lines.append(json.dumps(op,ensure_ascii=False,separators=(',',':')))
 lines.append('STATES '+json.dumps(rec.get('material_states'),ensure_ascii=False,separators=(',',':')))
 lines.append('MATERIALS '+json.dumps(rec['materials'],ensure_ascii=False,separators=(',',':')))
 lines.append('STOCKS '+json.dumps(rec.get('stock_solutions'),ensure_ascii=False,separators=(',',':')))
 (O/('record-'+rec['record_id']+'.json')).write_text(json.dumps(rec,ensure_ascii=False,indent=2),encoding='utf8')
(O/'all-operation-material-stock-reading.txt').write_text('\n'.join(lines),encoding='utf8')
def first(x):return next(iter(x.items())) if isinstance(x,dict) else x[0]
def brief(x):print(json.dumps(x,ensure_ascii=False,indent=2)[:7000])
brief({'inventory_keys':list(inv),'units0':inv.get('source_units',[None])[0],'source_fact_q':sf['facts'][1]['quantities'][0],'table_cell':read(F/'source-tables.json')['tables'][0]['rows'][0]['cells'][0], 'reader_fact_bound':next(f for s in r['reader_sections'] for i in s['items'] for f in i['facts'] if f.get('json_pointer','').startswith('/measurements/')),'source_unit_map':first(rc['source_units']),'reader_fact_map':first(rc['source_facts']), 'reader_table_map':first(rc['table_cells'])})
