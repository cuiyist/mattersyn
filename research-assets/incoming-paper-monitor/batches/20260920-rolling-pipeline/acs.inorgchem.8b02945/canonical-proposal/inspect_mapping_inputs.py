from pathlib import Path
import json,hashlib,datetime
C=Path(__file__).resolve().parent;F=C.parent
x=json.loads((F/'source-facts.json').read_text('utf8'))
outline={'status':'mutable_source_mapping_aid_not_canonical','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_facts_sha256':hashlib.sha256((F/'source-facts.json').read_bytes()).hexdigest(),'protocols':[{'id':p['id'],'title':p['title'],'kind':p['kind'],'operation_ids':[o['id']for o in p['operations']],'sample_ids':p.get('sample_ids',[])}for p in x['protocols']],'stocks':x['stocks'],'facts':[{'id':f['id'],'title':f.get('title'),'class':f.get('fact_class'),'context':f.get('sample_scope',f.get('context')),'quantities':[{k:q.get(k)for k in ['meaning','raw_text','unit','status']}for q in f.get('quantities',[])]}for f in x['facts']],'sample_contexts':[{k:s.get(k)for k in ['id','label','kind','reported_whole_composition','parent_context_ids','source_fact_ids']}for s in x['sample_contexts']]}
(C/'mapping-input-outline.json').write_text(json.dumps(outline,ensure_ascii=False,indent=2)+'\n','utf8')
for p in outline['protocols']:print(p['id']+' | '+p['kind']+' | '+','.join(p['operation_ids']))
print('STOCKS')
for s in x['stocks']:print(s['id']+' | '+json.dumps({k:v for k,v in s.items()if k not in ['evidence','quantities']},ensure_ascii=False))
print('FACT QUANTITIES')
for f in outline['facts']:print(f['id']+' | '+', '.join(q['meaning']+'='+q['raw_text']+' '+str(q['unit'])for q in f['quantities']))
