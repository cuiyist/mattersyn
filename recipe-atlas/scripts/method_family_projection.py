"""Compact public display projection; detailed diagnostics remain build/report only."""
def compact_method_families(result):
    families=[]
    for family in result['families']:
        families.append({
            'id':family['id'],'kind':family['kind'],'label':('Processing of '+result['material_formula'])if family['kind']=='processing'else family['label'],
            'paper_count':family['paper_count'],
            'papers':[{'citation':paper['citation'],'record_ids':list(paper['record_ids'])} for paper in family['papers']],
        })
    compact={'schema':'mattersyn-method-families-compact/1','default_record_id':result['default_record_id'],'families':families}
    flattened=[rid for family in families for paper in family['papers'] for rid in paper['record_ids']]
    assert len(flattened)==result['record_count'] and len(set(flattened))==len(flattened)
    assert compact['default_record_id']==(families[0]['papers'][0]['record_ids'][0] if families else None)
    return compact
