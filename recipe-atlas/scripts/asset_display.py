"""Apply private, exact-hash display overrides; never distribute original bytes.

Parent supplies cleared source-link SVGs and performs the broader legacy/data
reference transform. These helpers make paper-review hash validation and reviewed
Reader sidecar builds aware of the different public display asset.
"""
import copy,hashlib,json
from pathlib import Path
def load_overrides(root):
    path=root/'private-build/asset-display-overrides.json'
    if not path.exists():return {}
    data=json.loads(path.read_text(encoding='utf-8'))
    if data.get('schema')!='mattersyn-asset-display-overrides/1'or data.get('scope')!='private_build_input_do_not_deploy':raise ValueError('Invalid private display override scope')
    result={}
    for row in data['assets']:
        if row['original_path']in result:raise ValueError('Duplicate display override')
        target=(root/'dist'/row['display_path']).resolve()
        if not target.is_relative_to((root/'dist/assets/source-links').resolve())or target.suffix!='.svg':raise ValueError('Unsafe source-link card path')
        if not target.is_file()or hashlib.sha256(target.read_bytes()).hexdigest()!=row['display_sha256']:raise ValueError('Source-link card hash mismatch')
        if not row['source_url'].startswith('https://'):raise ValueError('Source URL must be HTTPS')
        if (root/'dist'/row['original_path']).exists():raise ValueError('Withheld original bytes remain in public artifact')
        result[row['original_path']]=row
    return result
def transform(value,overrides,private_log):
    if isinstance(value,list):return [transform(v,overrides,private_log)for v in value]
    if not isinstance(value,dict):return value
    result={k:transform(v,overrides,private_log)for k,v in value.items()}
    original=value.get('public_asset')or value.get('asset');row=overrides.get(original)
    if not row:return result
    reported=value.get('public_asset_sha256')or value.get('asset_sha256')or(value.get('sha256')if'public_asset'in value else None)
    if reported and reported!=row['original_sha256']:raise ValueError('Source asset/hash mismatch: '+original)
    private_log.append({'original_path':original,'original_sha256':row['original_sha256'],'source_record':copy.deepcopy(value)})
    key='public_asset'if'public_asset'in value else'asset';result[key]=row['display_path']
    if key=='public_asset':
        result['public_asset_sha256']=row['display_sha256']
        # Legacy original_assets used sha256 for the old crop. Keep that
        # original object only in private_log; publish an explicitly named
        # display hash instead of leaving an ambiguous stale hash alias.
        if'sha256'in result:result.pop('sha256')
    if'public_asset_sha256'in result:result['public_asset_sha256']=row['display_sha256']
    if'asset_sha256'in result:result['asset_sha256']=row['display_sha256']
    result.pop('original_crop_provenance',None)
    result['display_kind']='source_link';result['display_asset_sha256']=row['display_sha256'];result['display_note']=row['display_note'];result['source_url']=row['source_url'];result['original_figure_available']=False
    # Captions, measurement facts, figure/sample locators and conflicts unchanged.
    return result
def display_view(value,root,log_name):
    overrides=load_overrides(root)
    if not overrides:return value
    log=[];result=transform(value,overrides,log)
    path=root/'private-build'/log_name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(log,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result
