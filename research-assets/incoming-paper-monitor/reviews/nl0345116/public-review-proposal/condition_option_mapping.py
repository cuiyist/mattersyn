conditionlinks={}
for rid,d in drafts.items():
 for n,option in enumerate(d.get('condition_options',[])):
  for name,q in option.get('parameters',{}).items():
   pointer=f'/condition_options/{n}/parameters/{name}'
   f=append_fact('topo',rid,pointer,'condition-option-'+option['id']+'-'+name,option['label']+' · '+name,q,q.get('evidence',option['evidence']),'condition_option_parameter',extra='Alternative source reagent grade; not co-added or a uniquely assigned figure specimen. '+option['label'])
   f['canonical_condition_option_id']=option['id'];conditionlinks[rid+'::'+option['id']+'::'+name]='topo'
out['counts']['condition_option_parameter_facts']=len(conditionlinks)
cp=O/'canonical-measurement-coverage.json';cc=read(cp);cc['condition_option_parameter_count']=len(conditionlinks);cc['condition_option_parameter_to_reader_item']=conditionlinks;cp.write_text(json.dumps(cc,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
