"""Create authored source-link cards and replace withheld image references.

Never reads or edits the original raster image. Operates only in the new release
artifact directory. Scientific records are retained byte-for-byte.
"""
from pathlib import Path
import argparse, copy, hashlib, html, importlib.util, json, re
from functools import lru_cache
from safe_paths import checked_path, preflight_tree

TEXT={'.json','.jsonl','.html','.js','.mjs','.css','.md','.csv','.txt'}
def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
@lru_cache(maxsize=1)
def display_guard():
    # One shared validator keeps build-time substitution and release gating in
    # agreement. User direction is a display basis, not a copyright clearance.
    path=Path(__file__).resolve().parents[1]/'mattersyn-release/public_release_guard.py'
    spec=importlib.util.spec_from_file_location('mattersyn_display_guard',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def rows(registry):
    for asset in registry.get('assets',[]):
        if asset.get('rights',{}).get('status')=='user_directed_display':
            locations=asset.get('delivery_paths',[])
            if not locations:raise RuntimeError('user_directed_display_delivery_missing_or_ambiguous')
            for location in locations:
                reason=display_guard().user_directed_display_error(asset,location.get('repo'),location.get('path'))
                if reason:raise RuntimeError(reason)
            continue
        if asset.get('rights',{}).get('status') in {'not_source_derived','authored','license-cleared','license_cleared','permission-granted','permission_granted','approved','cleared'}:continue
        for location in asset.get('delivery_paths',[]):
            if location.get('repo')=='mattersyn-site':yield asset,location
def url_for(asset):
    values=asset.get('fallback',{}).get('source_links',[])
    for value in values:
        url=value if isinstance(value,str) else value.get('url') or value.get('source_url')
        if url and url.startswith('https://'):return url
    for binding in asset.get('source_bindings',[])+asset.get('provenance_bindings',[]):
        doi=binding.get('doi')or binding.get('source_doi')
        if doi:return doi if str(doi).startswith('https://')else'https://doi.org/'+str(doi)
        for url in binding.get('reference_urls',[]):
            if url.startswith('https://doi.org/'):return url
    # A source-library link explicitly represents an unresolved exact source.
    return 'https://cuiyist.github.io/mattersyn-site/library.html'

def card(url):
    label=url.replace('https://doi.org/','DOI: ')
    if len(label)>88:label=label[:85]+'...'
    return ('''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540" role="img" aria-label="Source link; original image is not reproduced"><rect width="960" height="540" rx="24" fill="#f5f8fc"/><rect x="32" y="32" width="896" height="476" rx="18" fill="white" stroke="#cad8e8"/><path d="M92 98h56v68H92z M102 116h34 M102 130h34 M102 144h25" fill="none" stroke="#225da5" stroke-width="4"/><text x="180" y="135" font-family="Arial,sans-serif" font-size="34" font-weight="600" fill="#13364d">Source figure</text><text x="84" y="234" font-family="Arial,sans-serif" font-size="26" fill="#25465a">The original image is available in the cited publication.</text><text x="84" y="284" font-family="Arial,sans-serif" font-size="23" fill="#486174">This card is a source link, not a measured image or plot.</text><text x="84" y="364" font-family="Arial,sans-serif" font-size="20" fill="#225da5">'''+html.escape(label)+'''</text><text x="84" y="442" font-family="Arial,sans-serif" font-size="21" fill="#486174">Use the publication link beside this card to read the source.</text></svg>\n''').encode('utf-8')

def authored_graphic(kind):
    if kind=='og.png':
        return b'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630"><rect width="1200" height="630" fill="#f5f8fc"/><rect x="80" y="90" width="88" height="88" rx="22" fill="#2258df"/><text x="101" y="155" fill="white" font-family="Arial,sans-serif" font-size="58" font-weight="700">M</text><text x="80" y="300" font-family="Arial,sans-serif" font-size="86" fill="#13364d" font-weight="600">MatterSyn</text><text x="84" y="385" font-family="Arial,sans-serif" font-size="37" fill="#486174">Materials synthesis and characterization</text><path d="M84 440h1000" stroke="#cbd7e5" stroke-width="2"/><text x="84" y="508" font-family="Arial,sans-serif" font-size="28" fill="#225da5">Recipes, measured outcomes and traceable sources</text></svg>\n'
    return b'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="800" viewBox="0 0 800 800"><rect width="800" height="800" rx="32" fill="#f5f8fc"/><path d="M345 125h110v218c110 45 160 162 109 263-67 130-262 130-329 0-51-101-1-218 110-263z" fill="#e4f4fa" stroke="#29566f" stroke-width="10"/><path d="M242 505c-16 89 30 154 102 177 91 29 174-6 206-82 14-35 15-65 8-95z" fill="#66b8c5" opacity=".75"/><path d="M327 120h146 M347 167h106 M267 725h266" fill="none" stroke="#29566f" stroke-width="10" stroke-linecap="round"/><circle cx="335" cy="576" r="12" fill="white" opacity=".75"/><circle cx="461" cy="616" r="9" fill="white" opacity=".75"/><text x="400" y="60" text-anchor="middle" font-family="Arial,sans-serif" font-size="25" fill="#486174">Illustrative reaction vessel</text><text x="400" y="775" text-anchor="middle" font-family="Arial,sans-serif" font-size="21" fill="#486174">Apparatus schematic; dimensions are illustrative</text></svg>\n'

SCRIPT='''const index=await fetch(new URL('data/source-figure-links.json',import.meta.url)).then(r=>{if(!r.ok)throw Error('Source-link index unavailable');return r.json()});
const owners=new WeakMap();
function enhance(){for(const img of document.images){let path;try{path=new URL(img.currentSrc||img.src,document.baseURI).pathname}catch{continue}const match=path.match(/assets\\/source-links\\/[^/]+\\.svg$/);const row=match&&index.assets[match[0]];const old=owners.get(img);if(!row){if(old){old.remove();owners.delete(img)}continue}if(old?.dataset.sourceLinkPath===match[0])continue;if(old)old.remove();const note=document.createElement('p');note.className='source-figure-link-note';note.dataset.sourceLinkPath=match[0];note.style.cssText='font:14px/1.5 system-ui,sans-serif;color:#486174;margin:10px 0;max-width:100%';const a=document.createElement('a');a.href=row.source_url;a.target='_blank';a.rel='noopener noreferrer';a.textContent=row.source_identified?'Read the original figure in the cited publication':'Find the source in the source library';a.style.color='#185ca5';note.append(a,document.createTextNode(' · '+row.display_note));img.insertAdjacentElement('afterend',note);img.alt='Source link — original figure not reproduced';owners.set(img,note)}}
enhance();new MutationObserver(enhance).observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['src']});
'''

def normalized_asset(value):
    if not isinstance(value,str):return None
    while value.startswith('../'):value=value[3:]
    return value[2:]if value.startswith('./')else value

def display_asset(row):
    return {'file':row['display_path'],'sha256':row['display_sha256'],'kind':'source_link','source_url':row['source_url'],'display_note':row['display_note']}

def project_display_json(value,lookup,private,metadata_path,pattern,replacements,pointer='',protected=False):
    if isinstance(value,dict):
        original=value.get('original_figure_asset')
        if isinstance(original,dict)and normalized_asset(original.get('file'))in lookup:
            row=lookup[normalized_asset(original['file'])]
            if original.get('sha256')!=row['original_sha256']:raise RuntimeError('Original figure identity mismatch')
            private.append({'metadata_path':metadata_path,'pointer':pointer+'/original_figure_asset','original':copy.deepcopy(original)})
            value['display_asset']=display_asset(row)
            original['source_asset_locator']=original.pop('file')
            original['redistribution_status']='withheld'
            original['visual_review_scope']='Privately retained original crop; the public card is not measured data.'
        public_path=normalized_asset(value.get('public_asset'))
        if public_path in lookup:
            row=lookup[public_path];claimed=value.get('public_asset_sha256')
            if claimed is not None and claimed!=row['original_sha256']:raise RuntimeError('Original public figure identity mismatch')
            private.append({'metadata_path':metadata_path,'pointer':pointer,'original':copy.deepcopy(value)})
            value['source_crop_sha256']=row['original_sha256']
            value['public_asset']=row['display_path'];value['public_asset_sha256']=row['display_sha256']
            value['display_asset']=display_asset(row);value['display_kind']='source_link';value['display_note']=row['display_note'];value['source_url']=row['source_url']
        return {k:project_display_json(v,lookup,private,metadata_path,pattern,replacements,pointer+'/'+k,protected or k=='source_asset_locator')for k,v in value.items()}
    if isinstance(value,list):return [project_display_json(v,lookup,private,metadata_path,pattern,replacements,pointer+'/'+str(i),protected)for i,v in enumerate(value)]
    if isinstance(value,str)and not protected and pattern:return pattern.sub(lambda m:replacements[m.group()],value)
    return value

def main():
    p=argparse.ArgumentParser();p.add_argument('--phase',choices=['prepare','prebuild','postbuild'],required=True);p.add_argument('--root',required=True);p.add_argument('--source-root',required=True);p.add_argument('--registry',required=True);a=p.parse_args();source=preflight_tree(Path(a.source_root).absolute());root=checked_path(source,Path(a.root).absolute());registry=json.loads(Path(a.registry).read_text(encoding='utf-8'))
    if root.name!='dist' or not root.is_relative_to(source):raise RuntimeError('Only a distinct build dist inside source root is supported')
    overrides=[];public={};replacements={};new_assets=[]
    for asset,location in rows(registry):
        if asset.get('classification')=='unknown'and location['path']not in {'og.png','assets/flask.png'}:raise RuntimeError('Unknown graphic origin requires a distinct reviewed display decision')
        original=location['path'];checked_path(root,root/original);is_illustration=original in {'og.png','assets/flask.png'};url='https://cuiyist.github.io/mattersyn-site/'if is_illustration else url_for(asset);raw=authored_graphic(original)if is_illustration else card(url);display='assets/source-links/'+sha(raw)[:24]+'.svg';destination=checked_path(root,root/display)
        if not destination.resolve().is_relative_to(root/'assets/source-links'):raise RuntimeError('Invalid card destination')
        if a.phase!='prepare':destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(raw)
        row={'original_path':original,'original_sha256':asset['asset_hash'],'display_path':display,'display_sha256':sha(raw),'source_url':url,'display_note':'Original MatterSyn explanatory illustration; dimensions are schematic.'if is_illustration else'Original figure not reproduced; redistribution clearance is pending. This source-link card is not measured data.'}
        overrides.append(row);replacements[original]=display
        if not is_illustration:public[display]={'source_url':url,'source_identified':'doi.org/'in url,'display_note':row['display_note']}
        new_assets.append({'path':display,'sha256':sha(raw),'classification':'authored_diagram','rights_status':'authored','source_url':url})
    save(source/'private-build/asset-display-overrides.json',{'schema':'mattersyn-asset-display-overrides/1','scope':'private_build_input_do_not_deploy','assets':overrides})
    save(source/'private-build/source-link-generated-assets.json',{'schema':'mattersyn-generated-source-links/1','assets':list({x['path']:x for x in new_assets}.values())})
    if a.phase=='prepare':print(json.dumps({'prepared_overrides':len(overrides)}));return
    save(root/'data/source-figure-links.json',{'schema':'mattersyn-source-figure-links/1','assets':public})
    (root/'source-figure-links.mjs').write_text(SCRIPT,encoding='utf-8')
    if a.phase=='postbuild':
        changed=[];private=[];lookup={x['original_path']:x for x in overrides};pattern=re.compile('|'.join(re.escape(x)for x in sorted(replacements,key=len,reverse=True)))if replacements else None
        for path in root.rglob('*'):
            checked_path(root,path)
            if not path.is_file()or path.suffix not in TEXT:continue
            rel=path.relative_to(root).as_posix()
            if rel.startswith('data/records/')or rel=='data/records.jsonl'or rel.startswith('data/exports/'):continue
            raw=path.read_text(encoding='utf-8')
            if path.suffix=='.json':
                before=json.loads(raw);after=project_display_json(copy.deepcopy(before),lookup,private,rel,pattern,replacements)
                clean=json.dumps(after,ensure_ascii=False,indent=2)+'\n'if before!=after else raw
            else:clean=pattern.sub(lambda m:replacements[m.group()],raw)if pattern else raw
            if path.suffix=='.html'and'source-figure-links.mjs'not in clean:
                prefix='../'*len(Path(rel).parent.parts);clean=clean.replace('</body>','<script type="module" src="'+prefix+'source-figure-links.mjs"></script></body>')
            if clean!=raw:path.write_text(clean,encoding='utf-8');changed.append(rel)
        for original in replacements:
            target=(root/original).resolve()
            if not target.is_relative_to(root):raise RuntimeError('Out-of-artifact original path')
            if target.is_file():raise RuntimeError('Withheld original unexpectedly present; rebuild from cleared inputs')
        save(source/'private-build/source-link-transform-report.json',{'changed_files':changed,'held_paths':len(replacements),'generated_cards':len(public),'canonical_records_and_exports_modified':False})
        save(source/'private-build/legacy-original-figure-provenance.json',{'scope':'Private original display objects before publication-only substitution; do not deploy.','objects':private})
        print(json.dumps({'held_paths':len(replacements),'generated_cards':len(public),'changed_files':len(changed)}))

if __name__=='__main__':main()
