"""Apply one source-confirmed digit correction and qualify one degraded sign.

Preserve the complete first freeze, including its original reading history.
Earlier SI chunks, native source pixels and unrelated author fields are unchanged.
"""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal
import json, csv, hashlib, shutil, copy
B=Path(__file__).resolve().parent
stem='si-pages11-12'
read=lambda p:json.loads(Path(p).read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
mp=B/(stem+'-manifest.json');manifest=read(mp);initial_sha=sha(mp)
assert initial_sha=='0e70e5d2c4afccde345e96fbcbb2fd4d33336a206f11b7e54b49855242e7a3a8'
for p,h in {**manifest['files'],**manifest['original_evidence']}.items():assert sha(p)==h,p
archive=B/(stem+'-author-revision-1');archive.mkdir(exist_ok=False)
archived={}
for p,h in list(manifest['files'].items())+[(str(mp),initial_sha)]:
    p=Path(p);target=archive/p.relative_to(B)
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(p,target);assert sha(target)==h
    archived[str(target)]=h
blocks=read(B/(stem+'-author-blocks.json'))
typed=read(B/(stem+'-transcription.json'));old=copy.deepcopy(typed)
cp=read(B/(stem+'-author-checkpoint.json'))
with (B/(stem+'-reflections.tsv')).open(encoding='utf8',newline='') as f:
    table=list(csv.DictReader(f,delimiter='\t'))
author=B/'author_si_pages11_12.py';script=author.read_text(encoding='utf8')
columns=typed['field_order'];changes=[]
for key,rn,col,before,after,hkl,kind,detail in [
    ('11R',33,'sigma_Fobs2','7604.83','7694.83',[5,11,27],'source_confirmed_digit_correction','p11-R33-detail.png'),
    ('12L',12,'Fcal2','3757.09','[sign_unresolved]3757.09',[11,17,27],'source_sign_qualification','p12-L12-detail.png')]:
    tokens=blocks[key][rn-1].split();ci=columns.index(col)
    assert tokens[ci]==before and [int(v) for v in tokens[:3]]==hkl
    beforeline=' '.join(tokens);tokens[ci]=after;afterline=' '.join(tokens)
    blocks[key][rn-1]=afterline
    assert script.count(beforeline)==1
    script=script.replace(beforeline,afterline)
    rid=f'si-p{int(key[:-1]):02d}-{key[-1]}-r{rn:03d}'
    row=next(r for r in typed['rows'] if r['row_id']==rid)
    assert row['hkl']==hkl and row['raw_cells'][col]==before
    row['raw_cells'][col]=after
    cell=next(c for c in row['cells'] if c['cell_id']==rid+'-'+col)
    assert cell['raw_text']==before
    cell['raw_text']=after
    if kind=='source_confirmed_digit_correction':
        cell['numeric_value']=7694.83
        reason='The independent reader found an author digit typo. The author reopened the native-pixel detail: the uncertainty is clearly 7694.83, not 7604.83.'
    else:
        reason='The retained scan has a separated tiny pre-digit mark before clear digits 3757.09. On magnified reinspection, the author could not conclusively distinguish a scan speck from a degraded sign. Both signs remain possible; the signed value is withheld without using the physical meaning of Fcal^2 to choose a sign.'
        cell.update({'numeric_value':None,'transcription_status':'source_sign_unresolved',
                     'source_comparison_status':'visually_compared_sign_unresolved',
                     'visible_digits':'3757.09','magnitude_value':3757.09,
                     'sign_status':'unresolved_from_retained_scan','signed_value_candidates':[-3757.09,3757.09],
                     'raw_text_includes_editorial_annotation':True,
                     'editorial_annotation':'[sign_unresolved] is a curator label, not printed source text. The clear digits are 3757.09.',
                     'uncertainty_note':reason})
        typed['unresolved_numeric_tokens_in_chunk'].append({
            'cell_id':cell['cell_id'],'visible_digits':'3757.09','raw_text':after,'numeric_value':None,
            'magnitude_value':3757.09,'signed_value_candidates':[-3757.09,3757.09],
            'reason':reason,'evidence':cell['evidence']})
    ts=next(x for x in table if x['page']==str(int(key[:-1])) and x['block']==key[-1] and x['row']==str(rn))
    assert ts[col]==before;ts[col]=after
    dp=B/'reader-assets/si-pages11-12-independent'/detail
    changes.append({'cell_id':cell['cell_id'],'hkl':hkl,'kind':kind,'before':before,'after':after,
                    'reason':reason,'source_crop':cell['evidence']['original_crop_path'],
                    'source_crop_sha256':cell['evidence']['original_crop_sha256'],
                    'auditor_detail_crop':str(dp),'auditor_detail_sha256':sha(dp)})

def diff(a,b,p=''):
    if type(a)!=type(b):return [(p,a,b)]
    if isinstance(a,dict):
        return [d for k in dict.fromkeys([*a,*b]) for d in
                ([(p+'/'+k,a.get(k),b.get(k))] if k not in a or k not in b else diff(a[k],b[k],p+'/'+k))]
    if isinstance(a,list):
        assert len(a)==len(b)
        return [d for i,(x,y) in enumerate(zip(a,b)) for d in diff(x,y,p+'/'+str(i))]
    return [] if a==b else [(p,a,b)]
row_deltas=diff(old['rows'],typed['rows'])
changed_raw=[(a['row_id'],k,a['raw_cells'][k],b['raw_cells'][k])
             for a,b in zip(old['rows'],typed['rows']) for k in columns if a['raw_cells'][k]!=b['raw_cells'][k]]
assert len(changed_raw)==2
assert {p.split('/')[1] for p,_,_ in row_deltas}=={'77','101'}
assert all(c['evidence']==d['evidence'] for a,b in zip(old['rows'],typed['rows']) for c,d in zip(a['cells'],b['cells']))
checks=[]
def check(name,ok):checks.append({'check':name,'passed':bool(ok)});assert ok,name
for row in typed['rows']:
    for cell in row['cells']:
        col=cell['evidence']['column_key'];text=cell['raw_text'];value=cell['numeric_value']
        ok=text==row['raw_cells'][col]
        if value is not None:ok=ok and Decimal(text)==Decimal(str(value))
        elif col=='marker':ok=ok and text=='o'
        else:
            ok=ok and cell['sign_status']=='unresolved_from_retained_scan' and text=='[sign_unresolved]'+cell['visible_digits']
            ok=ok and cell['signed_value_candidates']==[-cell['magnitude_value'],cell['magnitude_value']]
        check(cell['cell_id']+' raw/typed/uncertainty consistency',ok)
check('One definite digit correction and one sign qualification;1258 raw tokens unchanged',len(changed_raw)==2)
check('All original per-cell evidence and sample links are unchanged',all(c['evidence']==d['evidence'] and a['hkl']==b['hkl'] and a['source_sample_label']==b['source_sample_label'] for a,b in zip(old['rows'],typed['rows']) for c,d in zip(a['cells'],b['cells'])))
check('The initial11R35 sign qualification is unchanged',old['unresolved_numeric_tokens_in_chunk'][0]==typed['unresolved_numeric_tokens_in_chunk'][0])
check('All36 definite negative observations and zero-observation list are unchanged',old['negative_observations']==typed['negative_observations'] and old['zero_observations']==typed['zero_observations'])
check('1078 resolved numeric cells and two sign-uncertain numeric fields',sum(c['numeric_value'] is not None for r in typed['rows'] for c in r['cells'])==1078 and len(typed['unresolved_numeric_tokens_in_chunk'])==2)
check('All80 prior source/chunk/audit files are unchanged',all(sha(p)==h for p,h in cp['preserved_prior_files'].items()))
check('All native source assets are unchanged',all(sha(p)==h for p,h in cp['bound_original_evidence'].items()))
typed['counts']['resolved_numeric_cells']=1078;typed['counts']['unresolved_sign_cells']=2
typed['status']='author_source_compared_two_signs_unresolved_independent_numerical_audit_pending'
typed['policies']['uncertain_sign']='Two clear magnitudes, Fobs^2 1965.46 at SI11R35 and Fcal^2 3757.09 at SI12L12, have unresolved leading signs. Their signed numeric_value fields are null. Each has both signed candidates. The TSV and raw_text use an explicitly editorial [sign_unresolved] prefix; neither token may be parsed as a positive measurement.'
save(B/(stem+'-author-blocks.json'),blocks);save(B/(stem+'-transcription.json'),typed)
author.write_text(script,encoding='utf8')
with (B/(stem+'-reflections.tsv')).open('w',encoding='utf8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['page','block','row']+columns,delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(table)
validation=B/(stem+'-correction-validation.json')
save(validation,{'schema':'mattersyn-bounded-numerical-delta-validation/1','status':'passed_author_delta_checks',
                 'source_id':'heo2003','typed_row_leaf_changes':row_deltas,
                 'definite_numeric_digit_corrections':1,'new_sign_qualifications':1,
                 'printed_tokens_changed':2,'printed_tokens_unchanged':1258,
                 'checks':checks,'check_count':len(checks),'source_evidence_unchanged':True,
                 'earlier_chunks_unchanged':True,'independent_recheck':'pending'})
cp['actual_scope'].update(typed['counts'])
cp['status']='author_comparison_complete_two_signs_unresolved_independent_numerical_audit_pending'
cp['manual_source_comparison']+=' After the first freeze, the author reopened two native magnified details: SI11R33 sigma(Fobs^2) was corrected to7694.83, and the sign of SI12L12 Fcal^2 was explicitly withheld because its separated tiny pre-digit mark is not conclusive. These are separately recorded as a digit correction and a source-sign qualification.'
cp['unresolved_numeric_tokens_in_chunk']=typed['unresolved_numeric_tokens_in_chunk']
cp['policies']=typed['policies']
cp['initial_freeze_programmatic_checks']={'manifest_sha256':initial_sha,'checks':cp['programmatic_checks'],'count':cp['programmatic_check_count'],'scope':'Initial freeze only; final bounded-delta checks below supersede the one-sign counts.'}
cp['programmatic_checks']=checks;cp['programmatic_check_count']=len(checks)
cp['bound_files']={p:sha(p) for p in cp['bound_files']}
for p in [validation,Path(__file__)]:cp['bound_files'][str(p)]=sha(p)
cp['bounded_correction']={'history':str(B/(stem+'-correction-history.json')),
                         'initial_manifest_sha256':initial_sha,'raw_tokens_changed':2,
                         'definite_numeric_digit_corrections':1,'new_sign_qualifications':1,
                         'independent_recheck':'pending'}
save(B/(stem+'-author-checkpoint.json'),cp)
history=B/(stem+'-correction-history.json')
save(history,{'schema':'mattersyn-si-numerical-correction-history/1','at':datetime.now(timezone.utc).isoformat(),
              'source_id':'heo2003','transcription_author':'/root/peng1998_reader_assets',
              'finding_auditor':'/root/norberg2004_extract','status':'author_corrected_awaiting_distinct_final_recheck',
              'chunk_pages':[11,12],'changes':changes,'prior_files':archived,
              'initial_manifest_sha256':initial_sha,
              'corrected_files':{str(p):sha(p) for p in [B/(stem+'-author-blocks.json'),B/(stem+'-reflections.tsv'),B/(stem+'-transcription.json'),B/(stem+'-author-checkpoint.json'),author,validation]},
              'source_and_prior_chunks_unchanged':True,'other1258printed_tokens_unchanged':True,
              'historical_builder_note':'build_si_pages11_12.py describes the initial frozen package. This separate bounded correction script derives revision2 and intentionally preserves that builder and its prior validation history.',
              'prefreeze_history_note':'The sign-uncertainty report documents the earlier11R35 qualification; its initial/final-reading hashes identify that historical step. The complete pre-correction package is preserved with relative paths in author-revision-1.'})
manifest['revision']=2;manifest['prior_manifest_sha256']=initial_sha
manifest['counts']={**typed['counts'],'checks':len(checks)}
manifest['unresolved_sign_cell_ids']=[u['cell_id'] for u in typed['unresolved_numeric_tokens_in_chunk']]
manifest['files']={p:sha(p) for p in manifest['files']}
for p in [validation,history,Path(__file__)]:manifest['files'][str(p)]=sha(p)
manifest['bounded_correction_history']=str(history);manifest['independent_audit']='final_recheck_pending'
save(mp,manifest)
print(json.dumps({'counts':manifest['counts'],'hashes':{k:sha(B/(stem+s)) for k,s in {
    'manifest':'-manifest.json','transcription':'-transcription.json','tsv':'-reflections.tsv',
    'checkpoint':'-author-checkpoint.json','history':'-correction-history.json'}.items()},'archive':str(archive)},indent=2))
