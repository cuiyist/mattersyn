"""Private metadata-only Batch6 caption plan/binder; uses the unchanged reviewed adapter.
No model calls unless Root separately invokes that adapter. Pending captions must be bound before applying.
"""
import argparse, hashlib, importlib.util, json, re, sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
m=None

def source_adapter(source):
    """Load only the selected Source's installed split-aware adapter and registry."""
    source=Path(source).resolve()
    registry=source/'recipe-atlas/scripts/reader_presentation_registry.py'
    adapter=source/'tools/simple-pipeline/local_caption_backfill.py'
    before_path=sys.path[:];registry_present='reader_presentation_registry' in sys.modules;before_registry=sys.modules.get('reader_presentation_registry')
    try:
        spec=importlib.util.spec_from_file_location('reader_presentation_registry',registry)
        loader=importlib.util.module_from_spec(spec);spec.loader.exec_module(loader)
        sys.modules['reader_presentation_registry']=loader
        spec=importlib.util.spec_from_file_location('caption_adapter',adapter)
        value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
        return value
    finally:
        sys.path[:]=before_path
        if not registry_present:sys.modules.pop('reader_presentation_registry',None)
        else:sys.modules['reader_presentation_registry']=before_registry

def origin_fields(value):
    result={}
    for key in ('saved_response_recovery','manual_origin','manual_paraphrase'):
        if key in value:
            if type(value[key]) is not bool:raise ValueError('Caption origin flag must remain boolean')
            result[key]=value[key]
    return result
def prepare(batch,out):
    hand=m.read(batch/'handoff-summary.json');manifest=m.read(batch/'manifest.json');byname={p['filename']:p for p in manifest['papers']};papers=[];holds=[]
    for row in hand['papers']:
        meta=byname[row['filename']];doi=row['doi'];stem=Path(row['filename']).stem;path=batch/'work'/f'{stem}.figures.json';figures=m.read(path) if path.exists() else []
        sid='pending-'+batch.name+'-'+hashlib.sha256(doi.encode()).hexdigest()[:16];selected=[]
        for f in figures:
            caption=str(f.get('caption') or '').strip();page=f.get('page');digest=f.get('asset_sha256');label=f.get('figure')
            if not caption or not isinstance(page,int) or page<1 or not digest:holds.append({'doi':doi,'figure':label,'reason':'missing saved caption/page/crop hash'});continue
            crop=batch/'work/figures'/f['file']
            if not crop.is_file() or m.sha(crop.read_bytes())!=digest:raise ValueError('Saved crop changed')
            key=sid+'-'+m.norm(label)+'-p'+str(page)+'-'+digest[:8]
            selected.append({'figure_key':key,'figure':label,'page':page,'public_asset':'','public_asset_sha256':digest,'private_caption':caption,'saved_metadata_path':str(path),'saved_metadata_sha256':m.sha(path.read_bytes())})
        if not selected:continue
        f=out/'private-inputs'/f'{sid}.json';m.write(f,{'doi':doi,'source_id':sid,'record_ids':[],'batch':batch.name,'figures':selected,'binding_pending':True})
        papers.append({'doi':doi,'source_id':sid,'record_ids':[],'batch':batch.name,'figures':len(selected),'private_input':str(f),'private_input_sha256':m.sha(f.read_bytes()),'binding_pending':True})
    result={'schema':'local-caption-backfill-plan-1','batches':[batch.name],'papers':papers,'holds':holds,'paper_count':len(papers),'figure_count':sum(p['figures'] for p in papers),'binding_pending':True,'must_bind_before_shared_apply':True,'publication_credit':0,'local_model_requests':0,'shared_files_changed':False,'raw_caption_payloads_private':True}
    m.write(out/'caption-plan-pending-binding.json',result);print(json.dumps({k:result[k] for k in ['paper_count','figure_count','binding_pending','publication_credit','local_model_requests']}));return result

def bind(source,updates,out):
    m=source_adapter(source)
    side=m.read(source/'recipe-atlas/data/reader-presentation-reviewed.json');bydoi={}
    for p in sorted((source/'recipe-atlas/data/records').glob('*.json')):
        r=m.read(p)
        if r.get('quality',{}).get('review_status')!='source_extracted':continue
        sid=r['lineage']['source_group'];s=next((s for s in r['sources'] if s['id']==sid),{})
        if s.get('doi'):bydoi.setdefault(s['doi'].lower(),{}).setdefault(sid,[]).append(r['record_id'])
    old=m.read(updates);bound=[];holds=[]
    for paper in old['papers']:
        status=paper.get('caption_status','local_model_paraphrase_not_independently_reviewed')
        if status not in ('local_model_paraphrase_not_independently_reviewed','manual_source_caption_paraphrase_not_independently_reviewed'):raise ValueError('Unsupported caption origin status')
        groups=bydoi.get(paper['doi'].lower(),{})
        if len(groups)!=1:holds.append({'doi':paper['doi'],'reason':'not yet integrated or ambiguous SourceExtract identity'});continue
        sid,rids=next(iter(groups.items()));figures=[]
        for f in paper['figures']:
            matches=[x for x in side['figures_by_source'].get(sid,[]) if x.get('public_asset_sha256')==f['public_asset_sha256'] and (x.get('source_locator') or {}).get('page')==f['page'] and m.norm((x.get('source_locator') or {}).get('figure'))==m.norm(f['figure'])]
            if len(matches)!=1:holds.append({'doi':paper['doi'],'figure':f['figure'],'page':f['page'],'reason':'no unique current Reader label/page/crop match'});continue
            x=matches[0];asset=x['public_asset']
            if m.sha((source/'recipe-atlas/static'/asset).read_bytes())!=f['public_asset_sha256']:raise ValueError('Current public crop changed')
            figures.append({'figure_key':x['id'],'figure':f['figure'],'page':f['page'],'public_asset':asset,'public_asset_sha256':f['public_asset_sha256'],'public_caption':f['public_caption']}|origin_fields(f))
        if figures:bound.append({'doi':paper['doi'],'source_id':sid,'record_ids':rids,'figures':figures,'caption_status':status}|origin_fields(paper))
    result={'schema':'public-caption-updates-1','papers':bound,'figure_count':sum(len(p['figures']) for p in bound),'holds':holds,'binding_pending':False,'independent_audit':False,'shared_files_changed':False}
    result.update(origin_fields(old))
    m.write(out/'public-caption-updates-bound.json',result);print(json.dumps({'papers_bound':len(bound),'figures_bound':result['figure_count'],'holds':len(holds),'shared_files_changed':False}));return result

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','bind']);p.add_argument('--batch',type=Path);p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--updates',type=Path);a=p.parse_args()
    if a.command=='plan':
        if not a.batch:p.error('plan requires explicit --batch')
        global m
        m=source_adapter(a.source);prepare(a.batch,a.out)
    else:
        if not a.updates:p.error('bind requires --updates')
        bind(a.source,a.updates,a.out)
if __name__=='__main__':main()
