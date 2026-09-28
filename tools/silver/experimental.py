"""Explicit uncalibrated display projection. No calibrated/gold or training admission."""
from pathlib import Path
from collections import Counter
import argparse,copy,hashlib,json,re
import silver

SCHEMA='mattersyn-experimental-silver/1'
VALIDATOR_SHA='43ad5f3296f9ffdc9e3b12a55798b4e7c2613277b2442b1dafcb469b0bfabc2a'
def require(ok,message):
    if not ok:raise ValueError(message)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def checked_text(value,label,limit=500):
    require(isinstance(value,str) and 0<len(value)<=limit and not silver.PATH.search(value) and not re.search(r'[\x00-\x1f]',value),label+' is invalid')
    return value
def project(draft,pages,identity,receipt,scope,response,*,draft_sha256,pages_sha256):
    """Return allowlisted display data plus private diagnostics; never repairs a model claim."""
    require(sha(Path(silver.__file__).read_bytes())==VALIDATOR_SHA,'Validator dependency changed')
    sid=identity.get('source_id');require(silver.valid_id(sid),'Invalid source ID')
    require(draft.get('schema')==silver.VERSION+'/draft' and draft.get('source_id')==sid and draft.get('runner')=='local' and draft.get('saw_other_draft') is False,'Invalid local draft provenance')
    require(receipt.get('schema')=='mattersyn-local-draft-run/1' and receipt.get('external_document_transfer') is False and receipt.get('published') is False,'Invalid local run receipt')
    require(receipt.get('draft_sha256')==draft_sha256 and receipt.get('page_map_sha256')==pages_sha256,'Draft/page receipt differs')
    for key in ['pipeline_sha256','model_sha256']:
        require(bool(silver.HASH.fullmatch(draft.get(key,''))) and draft[key]==receipt.get(key),'Pipeline/model identity differs')
    require(bool(silver.HASH.fullmatch(draft.get('prompt_sha256',''))),'Prompt identity absent')
    require(scope.get('status')=='complete_model_draft_not_reviewed' and scope.get('external_transfer') is False,'Incomplete local response')
    require(response.get('done') is True and response.get('done_reason')=='stop' and response.get('model')==receipt.get('model'),'Incomplete/wrong raw model response')
    raw_claims=json.loads(response.get('message',{}).get('content','null'))
    require(isinstance(raw_claims,dict) and set(raw_claims)=={'claims'} and raw_claims['claims']==draft.get('claims'),'Draft differs from actual model output')
    requested=scope.get('input_pages');require(isinstance(requested,list) and requested and all(type(x)is int and x>0 for x in requested) and len(set(requested))==len(requested),'Invalid explicit page scope')
    require(identity.get('document_role')=='main' and type(identity.get('page_count'))is int and identity['page_count']==scope.get('source_total_pages') and max(requested)<=identity['page_count'],'Document scope differs')
    require(set(pages.get('documents',{}))=={'main'},'One explicit main document required')
    doc=pages['documents']['main'];require(doc.get('source_id')==sid and doc.get('document_sha256')==identity.get('source_sha256') and bool(silver.HASH.fullmatch(identity.get('source_sha256',''))),'Document identity differs')
    selected=copy.deepcopy(pages);selected['documents']['main']['pages']={str(n):doc['pages'][str(n)] for n in requested}
    require(isinstance(draft.get('claims'),list) and len(draft['claims'])<=4 and receipt.get('claims')==len(draft['claims']),'Claim inventory differs')
    require(all(isinstance(c,dict) for c in draft['claims']),'Claim must be an object')
    keys=[silver.claim_key(c) for c in draft['claims']]
    require(all(all(isinstance(v,(str,type(None))) for v in k) for k in keys),'Invalid claim key')
    counts=Counter(keys);fields=[];diagnostics=[]
    for index,c in enumerate(draft['claims']):
        errors=silver.validate_claim(c,selected,sid,{})
        if counts[keys[index]]!=1:errors.append('duplicate_or_conflicting_slot')
        if errors:
            diagnostics.append({'claim_index':index,'status':'withheld','reasons':sorted(set(errors))});continue
        fields.append({'recipe_id':c['recipe_id'],'sample_id':c.get('sample_id'),'slot_id':c['slot_id'],'field':c['field'],'value':c['value'],'unit':c.get('unit'),
            'document_id':'main','page':c['page'],'link_page':c['link_page'],'technique':c.get('technique'),
            'status':'machine_extracted_not_reviewed','mechanical_checks':'passed','training_ready':False,'training_weight':0})
    doi=checked_text(identity.get('doi'),'DOI',120)
    require(re.fullmatch(r'10\.\d{4,9}/[^\s?#]+',doi) is not None,'Invalid DOI')
    require(identity.get('url')=='https://doi.org/'+doi,'Source URL must match DOI')
    configuration={'input_pages':requested,'input_sha256':pages_sha256,'prompt_sha256':draft['prompt_sha256'],'pipeline_sha256':draft['pipeline_sha256']}
    entry={'source_id':sid,'doi':doi,'title':checked_text(identity.get('title'),'Title'), 'citation':checked_text(identity.get('citation'),'Citation',1000),'url':identity['url'],
        'document_sha256':identity['source_sha256'],'tier':'experimental_silver','scientific_review':'not_performed','calibration_state':'unmeasured','precision':None,'recall':None,
        'training_ready':False,'training_weight':0,'excluded_from':['gold','calibrated_silver','training_exports','gold_evaluation','structure_recipe_pair_counts'],
        'source_scope':{'role':'main','source_pages':identity['page_count'],'input_pages':requested,'full_paper_extraction':False,'figures_visually_reviewed':False,'si_reviewed':False},
        'extraction':{'model':checked_text(receipt.get('model'),'Model',80),'model_sha256':draft['model_sha256'],'prompt_sha256':silver.digest([draft['prompt_sha256']]),'pipeline_sha256':silver.digest([configuration]),'validator_sha256':VALIDATOR_SHA,'passes':1,'model_agreement_claimed':False,'chunks':1,'maximum_claims_per_chunk':4,'configuration_binding':'aggregate_of_chunk_fingerprints','chunk_configurations':[configuration]},
        'fields':fields,'withheld_claim_count':len(diagnostics),'limitations':['Automatic quote/value/unit checks do not establish scientific correctness, completeness or sample linkage.','Only the declared input pages were supplied to this draft; SI, figures and omitted fields were not reviewed.','Uncalibrated machine extraction is not a complete laboratory protocol.']}
    # The separately checked DOI HTTPS URL is not a local path. All other values remain checked.
    require(not silver.PATH.search(json.dumps({k:v for k,v in entry.items() if k!='url'},ensure_ascii=False)),'Private path in display data')
    return (entry if fields else None),{'source_id':sid,'claims':len(draft['claims']),'displayed':len(fields),'withheld':len(diagnostics),'rejections':diagnostics,'scientific_audit':False,'calibrated':False,'publication_credit':0}

def catalog(entries):
    require(entries and all(e and e.get('tier')=='experimental_silver' and e.get('fields') for e in entries),'No substantive experimental fields to publish')
    allowed={'source_id','doi','title','citation','url','document_sha256','tier','scientific_review','calibration_state','precision','recall','training_ready','training_weight','excluded_from','source_scope','extraction','fields','withheld_claim_count','limitations'}
    field_keys={'recipe_id','sample_id','slot_id','field','value','unit','document_id','page','link_page','technique','status','mechanical_checks','training_ready','training_weight'}
    nested={'source_scope':{'role','source_pages','input_pages','full_paper_extraction','figures_visually_reviewed','si_reviewed'},'extraction':{'model','model_sha256','prompt_sha256','pipeline_sha256','validator_sha256','passes','model_agreement_claimed','chunks','maximum_claims_per_chunk','configuration_binding','chunk_configurations'}}
    for e in entries:
        require(set(e)==allowed and all(isinstance(e[k],dict) and set(e[k])==v for k,v in nested.items()),'Unknown/missing public entry keys')
        require(all(isinstance(c,dict) and set(c)=={'input_pages','input_sha256','prompt_sha256','pipeline_sha256'} for c in e['extraction']['chunk_configurations']),'Unknown chunk provenance keys')
        require(e['scientific_review']=='not_performed' and e['calibration_state']=='unmeasured' and e['precision'] is None and e['recall'] is None and e['training_ready'] is False and e['training_weight']==0,'Experimental status changed')
        require(all(isinstance(f,dict) and set(f)==field_keys and f['training_ready'] is False and f['training_weight']==0 and f['status']=='machine_extracted_not_reviewed' for f in e['fields']),'Unknown field keys or admission')
        require(not silver.PATH.search(json.dumps({k:v for k,v in e.items() if k!='url'},ensure_ascii=False)),'Private path in public catalog')
        require(e['url']=='https://doi.org/'+e['doi'],'Bad source URL')
    require(len({e['source_id'] for e in entries})==len(entries) and len({e['doi'].lower() for e in entries})==len(entries),'Duplicate primary source')
    result={'schema':SCHEMA,'status':'experimental_machine_extraction_not_reviewed','calibration_state':'unmeasured','measured_accuracy':None,'training_ready':False,'publication_enabled':False,'gold_count_contribution':0,'calibrated_silver_count_contribution':0,'structure_pair_count_contribution':0,'completed_paper_count_contribution':0,'usable_complete_recipes':0,'distinct_sources':len(entries),'entries':entries}
    import jsonschema
    schema=json.loads(Path(__file__).with_name('experimental.schema.json').read_bytes())
    jsonschema.Draft202012Validator(schema).validate(result)
    return result

def project_chunks(chunks,pages,identity,*,pages_sha256):
    """Recheck exact whole-page/excerpt inputs, preserving per-call configuration provenance."""
    require(identity.get('page_map_sha256')==pages_sha256,'Original page-map identity differs')
    entries=[];diagnostics=[];input_pages=[];configurations=[];models=set();seen=set()
    for chunk in chunks:
        scope=chunk['scope'];draft=chunk['draft'];selected=chunk['pages']
        require(set(map(str,scope['input_pages']))<=set(selected['documents']['main']['pages']),'Selected-page declaration differs')
        for page in scope['input_pages']:
            full=pages['documents']['main']['pages'][str(page)];value=selected['documents']['main']['pages'][str(page)]
            if 'original_page_start_offset' in scope:
                start,end=scope['original_page_start_offset'],scope['original_page_end_offset']
                require(type(start)is int and type(end)is int and 0<=start<end<=len(full),'Invalid source excerpt offsets')
                require(scope.get('original_page_sha256')==sha(full.encode()) and scope.get('excerpt_sha256')==sha(value.encode()) and value==full[start:end],'Original source excerpt differs')
            else:require(value==full,'Whole-page input differs from original')
        binding=(chunk['pages_sha256'],draft['pipeline_sha256'],tuple(scope['input_pages']));require(binding not in seen,'Same configured chunk supplied twice');seen.add(binding)
        entry,diag=project(draft,selected,identity,chunk['receipt'],scope,chunk['response'],draft_sha256=chunk['draft_sha256'],pages_sha256=chunk['pages_sha256'])
        input_pages.extend(scope['input_pages']);models.add(draft['model_sha256']);diagnostics.append(diag)
        configurations.append({'input_pages':scope['input_pages'],'input_sha256':chunk['pages_sha256'],'prompt_sha256':draft['prompt_sha256'],'pipeline_sha256':draft['pipeline_sha256']})
        if entry:entries.append(entry)
    require(chunks and len(models)==1,'Chunks use different models')
    input_pages=sorted(set(input_pages))
    result={'source_id':identity['source_id'],'claims':sum(x['claims'] for x in diagnostics),'displayed':0,'withheld':sum(x['withheld'] for x in diagnostics),'chunks':diagnostics,'input_pages':input_pages,'scientific_audit':False,'calibrated':False,'publication_credit':0}
    if not entries:return None,result
    entry=copy.deepcopy(entries[0]);fields=[f for e in entries for f in e['fields']]
    key=silver.claim_key
    counts=Counter(key(f) for f in fields);duplicate_count=sum(counts[key(f)]>1 for f in fields)
    entry['fields']=[f for f in fields if counts[key(f)]==1];entry['withheld_claim_count']=result['withheld']+duplicate_count
    entry['source_scope']['input_pages']=input_pages
    entry['extraction'].update(chunks=len(chunks),maximum_claims_per_chunk=4,prompt_sha256=silver.digest([c['prompt_sha256'] for c in configurations]),pipeline_sha256=silver.digest(configurations),configuration_binding='aggregate_of_chunk_fingerprints',chunk_configurations=configurations)
    result.update(displayed=len(entry['fields']),withheld=entry['withheld_claim_count'],cross_chunk_duplicate_claims=duplicate_count)
    return (entry if entry['fields'] else None),result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ['draft','pages','identity','receipt','scope','response','output','diagnostics']:p.add_argument('--'+k,required=True)
    a=p.parse_args();raw={k:Path(getattr(a,k)).read_bytes() for k in ['draft','pages','identity','receipt','scope','response']};d={k:json.loads(v) for k,v in raw.items()}
    entry,diagnostics=project(**d,draft_sha256=sha(raw['draft']),pages_sha256=sha(raw['pages']))
    for name,value in [('diagnostics',diagnostics),('output',catalog([entry]) if entry else None)]:
        file=Path(getattr(a,name));require(not file.exists(),'Output already exists')
        if value is not None:file.parent.mkdir(parents=True,exist_ok=True);file.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in diagnostics.items() if k!='rejections'}))
if __name__=='__main__':main()
