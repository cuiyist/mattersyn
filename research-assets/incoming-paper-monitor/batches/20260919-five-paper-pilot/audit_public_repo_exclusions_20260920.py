"""Read-only repository path/history audit. Never emits raw text or secret values."""
from pathlib import Path, PurePosixPath
import subprocess, json, re, hashlib, collections, struct
from datetime import datetime, timezone

B=Path(__file__).resolve().parent
R=Path(r'[local path redacted]')
C=['git','-c','safe.directory='+R.as_posix(),'-C',str(R)]
def git(*args): return subprocess.check_output(C+list(args),text=True,encoding='utf-8',errors='replace')
head=git('rev-parse','HEAD').strip()
current=set(p for p in git('ls-files','-z').split('\0') if p)
history=set(p for p in git('log','--all','--format=','--name-only').splitlines() if p)
allpaths=current|history
allow_txt={
 'recipe-atlas/dist/vendor/3Dmol-min.js.LICENSE.txt', 'recipe-atlas/requirements-data.txt',
 'research-assets/incoming-paper-monitor/batches/20260919-five-paper-pilot/ja048427j/visuals/molecules/raw/nitrogen-nist-web-tool-excerpt.txt',
 'research-assets/incoming-paper-monitor/batches/20260919-five-paper-pilot/ja0496423/visuals/molecules/raw/nitrogen-nist-web-tool-excerpt.txt',
 'research-assets/incoming-paper-monitor/batches/20260919-five-paper-pilot/la036034c/visuals/components/vendor/3Dmol-min.js.LICENSE.txt',
 'research-assets/quality-20260918/relevance/build_atlas.py.reviewed.txt',
 'research-assets/training-migration/pbs2019-benchmark-original/data_columns_labels.txt',
 'requirements-data.txt', 'dist/vendor/3Dmol-min.js.LICENSE.txt'
}
def classify(p):
 n=PurePosixPath(p).name.lower(); ext=PurePosixPath(p).suffix.lower()
 if ext in ('.pdf','.doc','.docx','.ppt','.pptx','.zip','.xls','.xlsx'):
  return 'original_document_or_archive_requires_local_retention'
 if p in allow_txt or n.endswith('.license.txt'):
  return None
 if '/private/text/' in p or '/cache/text/' in p or '/first-page-text/' in p:
  return 'raw_full_or_page_text_cache'
 if p.startswith('research-assets/') and ext=='.txt':
  return 'individual_raw_source_text'
 if ext not in ('.png','.jpg','.jpeg','.webp'): return None
 # These are source-page render directories, not apparatus/model previews.
 if '/source-render/' in p or '/audit-pages/' in p:
  return 'source_page_render'
 if '/norberg2004/pages/' in p:
  return 'source_page_render'
 if n.startswith('pages-contact-') or ('/pages/' in p and n.startswith('contact-')):
  return 'source_page_contact_sheet'
 if '/jp0219348/reader-assets/si-' in p:
  if re.fullmatch(r'(?:si-\d+|p\d+)-(?:native|header|left-(?:top|bottom)|right-(?:top|bottom)|[lr](?:top|bottom))\.png',n):
   return 'complete_SI_scan_or_tiled_page_equivalent'
 # Match source-labelled pages; deliberately do not match figure/table/equation crops.
 if re.search(r'(?:^|[-_])(?:main|si|page)[-_]?(?:page[-_]?)?\d+(?:\.png|\.jpg|\.jpeg|\.webp)$',n):
  return 'source_page_render'
 if n in ('peng2000-source-1.png','peng2000-source-2.png'):
  return 'source_page_render'
 return None

excluded=[]
for p in sorted(allpaths):
 cat=classify(p)
 if not cat:continue
 onhead=p in current; q=R/p
 excluded.append({'path':p,'category':cat,'in_current_index':onhead,'in_reachable_history_path_union':p in history,
                  'current_bytes':q.stat().st_size if onhead and q.is_file() else None,
                  'current_sha256':hashlib.sha256(q.read_bytes()).hexdigest() if onhead and q.is_file() else None})

# Report only file paths, category names and counts for secret-like matches.
patterns={
 'github_classic_token':re.compile(rb'gh[pousr]_[A-Za-z0-9]{30,}'),
 'github_fine_grained_token':re.compile(rb'github_pat_[A-Za-z0-9_]{50,}'),
 'openai_key_shape':re.compile(rb'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{35,}'),
 'aws_access_key_shape':re.compile(rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
 'private_key_pem_header':re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
 'slack_token_shape':re.compile(rb'\bxox[baprs]-[A-Za-z0-9-]{20,}'),
}
secret_hits=[]; scanned_files=0; scanned_bytes=0
for p in sorted(current):
 if PurePosixPath(p).suffix.lower() not in ('.txt','.json','.jsonl','.py','.md','.html','.js','.mjs','.css','.xml','.toml','.yaml','.yml','.tmp','.diff','.patch',''):
  continue
 raw=(R/p).read_bytes();scanned_files+=1;scanned_bytes+=len(raw)
 for name,pat in patterns.items():
  count=len(pat.findall(raw))
  if count:secret_hits.append({'path':p,'detector':name,'match_count':count,'review_status':'requires_bounded_false_positive_check_no_values_returned'})

refs=[]
for p in sorted(current):
 if not p.startswith('recipe-atlas/') or not p.endswith('.json'):continue
 raw=(R/p).read_bytes()
 if b'norberg2004/pages/' not in raw:continue
 d=json.loads(raw)
 def walk(v,ptr=''):
  if isinstance(v,dict):
   for k,x in v.items():walk(x,ptr+'/'+str(k).replace('~','~0').replace('/','~1'))
  elif isinstance(v,list):
   for i,x in enumerate(v):walk(x,ptr+'/'+str(i))
  elif isinstance(v,str) and 'norberg2004/pages/' in v:
   refs.append({'file':p,'json_pointer':ptr,'page_asset_reference':v})
 walk(d)

cats=collections.Counter(x['category'] for x in excluded)
bytes_cats={k:sum(x['current_bytes']or 0 for x in excluded if x['category']==k) for k in cats}
publicpaths=[x['path'] for x in excluded if x['in_current_index'] and x['path'].startswith('recipe-atlas/dist/')]
source_meta_samples=[]
for folder in ['research-assets/corpus-20260917/private/content-cache','research-assets/corpus-20260917/private/evidence-candidates','research-assets/incoming-paper-monitor/corpus-screening/20260919/cache/content']:
 p=next(p for p in sorted(current) if p.startswith(folder+'/') and p.endswith('.json'))
 d=json.loads((R/p).read_text(encoding='utf-8-sig'))
 source_meta_samples.append({'path':p,'top_level_keys':list(d), 'disposition':'retain metadata/structured snippets; full text is stored in the excluded separate text path; sample structural inspection, not exhaustive content certification'})

result={
 'schema':'mattersyn-private-public-projection-exclusion-audit/1','created_at':datetime.now(timezone.utc).isoformat(),
 'author':'/root/norberg2004_extract','scope':'Read-only current tracked paths plus every path named by reachable Git history; source/cache structural inspection and high-confidence current-text secret-pattern scan. No raw source text or secret values emitted.',
 'repository':str(R),'head':head,'head_after':git('rev-parse','HEAD').strip(),'commit_count':int(git('rev-list','--count','--all')),
 'refs':git('for-each-ref','--format=%(refname) %(objectname)').splitlines(),
 'tracked_files':len(current),'reachable_history_path_union':len(history),'combined_path_union':len(allpaths),
 'proposed_exclusion_counts':dict(cats),'proposed_current_bytes_by_category':bytes_cats,
 'proposed_current_file_count':sum(x['in_current_index'] for x in excluded),
 'proposed_allhistory_path_count':len(excluded),'proposed_current_total_bytes':sum(x['current_bytes']or 0 for x in excluded),
 'excluded_paths':excluded,'explicit_retained_txt_paths':sorted(allow_txt & allpaths),
 'minimal_scope_limit':'Path-based proposal covers known raw source caches, page render naming and reconstructed full-page SI tiles. Keep selected original figure/table/equation crops, bounded cell-detail audit crops, typed numerical tables, canonical facts, audited prose, code, memory, skills and audit manifests. Do not delete audit records merely because their locally retained inputs are not public.',
 'norberg_full_page_public_assets':publicpaths,
 'norberg_reader_references':refs,
 'norberg_required_projection_delta':[
  'These 16 full-page images are actively referenced, not unused: remove their public image links in the public reader projection and dist copy, preserving the scientific text, page locators, hash/provenance and typed values.',
  'reader_sections[3].items[16] and equations[6] reference main-03: retain the equation fact and source locator; a separately audited bounded equation crop could replace the whole page later.',
  'reader_sections[5].items[86..101] and source_notes[0..15] link all 12 main and 4 SI pages. Preserve notes without public page-image attachment.',
  'Current reader metadata uses SI paths si-1..4 while tracked public files use si-01..04; removal should match both forms. Do not silently recertify old frozen reader hash after this projection change.'
 ],
 'history_considerations':[
  'Deleting files in a new commit or adding .gitignore does not remove original cached text/page images from the 32-commit reachable history.',
  'History must be sanitized at every commit/tree or a fresh sanitized public projection must be built. Keep the unfiltered local checkout unchanged.',
  'Retaining the current remote privately under an archive name and publishing a separate clean projection avoids deliberately making its original object store public; root owns any visibility/rename/push operation.',
  'If preserving public development history is required, filter the historical trees with the same path policy and preserve commit-message/date provenance where appropriate; full raw cache content is still excluded. Do not infer deleted/unreachable server objects are inaccessible from a force push alone.',
  'This path inventory uses git log --all --name-only, rather than only rev-list --objects path labels, because one deduplicated Git blob can occur under multiple paths.'
 ],
 'future_sync_policy':{
  'implementation':'classify(path) function in this private helper; exact current/history path list is the release denylist',
  'review_trigger':'Any newly generated raw source format, nonstandard page-render basename or embedded full-text payload must be reviewed before public sync. Filename rules alone cannot certify arbitrary future content.',
  'required_extra_rules':['Original papers/SI and archive/document suffixes stay local under the existing source-input policy.', 'Raw complete paper/page text caches stay local, including .tmp variants.', 'Every public deployment projection must strip source-page URLs before excluding their images; preserve selected figure assets and source locators.', 'Retain hash-only local source provenance and label locally withheld assets explicitly; do not rewrite prior scientific audits as if their inputs were never present.'],
  'no_blanket_exclusions':['research-assets/**','reader-assets/**','*.json','*.tsv','all *.png','MEMORY.md','skills/**']
 },
 'secret_like_content_scan':{'files_scanned':scanned_files,'bytes_scanned':scanned_bytes,'detectors':list(patterns),'findings':secret_hits,
   'scope_limit':'High-confidence format patterns over current tracked text only; no entropy/generic-password completeness claim. Prior history secret scan is inherited from root evidence, not independently repeated here. No credential values reported.'},
 'unexpected_personal_path_findings':[],
 'personal_path_limit':'Tracked top-level paths are project code/data/research-assets, memory and skills. Local username/path provenance may appear in authorized memory/audits; not automatically excluded as unrelated content. No exhaustive PII/content classification.',
 'metadata_sample_inspection':source_meta_samples,
 'mutations':'Only this private helper and its private report/manifest; no source, repository, Site, Git config, remote or visibility mutation.'
}
assert result['head']==result['head_after']
(B/'public-repository-exclusion-proposal-20260920.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(B/'public-repository-excluded-paths-20260920.txt').write_text('\n'.join(x['path']for x in excluded)+'\n',encoding='utf-8')
md=f'''Private public-projection exclusion audit — 20 September 2026 UTC

Audited local repository HEAD `{head}`: {len(current):,} tracked files, {result['commit_count']} reachable commits, {len(history):,} historical paths. No remote or visibility changes performed.

Propose excluding **{result['proposed_current_file_count']:,} current files / {result['proposed_current_total_bytes']:,} bytes**, and the corresponding **{len(excluded):,} historical paths**. Exact paths/categories/current hashes are in the JSON and companion path list. These are raw full/page texts and source page renders, including complete SI scan tiles; selected figures, typed numerical tables, source facts, memory, skills and audit records stay.

Category counts across history: {dict(cats)}.

**Norberg's 16 public full-page PNGs are referenced, not unused.** Two reader JSONs contain {len(refs)} exact links in total. Remove only those public image attachments/URLs in a separate public projection while retaining prose, numeric facts, notes and locators. The path/pointer list identifies equation 7/main page 3 and all 16 source-note page attachments. Current SI filenames are zero-padded while the model URLs are not; account for both. Preserve all 24 selected scientific crops.

The current unfiltered history contains the excluded equivalents. A new deletion commit or ignore rule is insufficient. Preserve the original local checkout and private archive; use a clean filtered public projection/history, then the same denylist plus reviewed source-format rules for future sync. Git blob deduplication makes `rev-list --objects` pathname output insufficient by itself; this report uses the union of every path in reachable commit changes.

High-confidence secret-pattern scan: {scanned_files:,} current text files / {scanned_bytes:,} bytes; {len(secret_hits)} path-only findings requiring review. This is not a blanket secrets/PII guarantee; baseline historical secret audit was not repeated. No unrelated personal paths identified in the project path inventory. Authorized memory and audit provenance may contain local usernames/paths.

The audit retained sampled cache metadata/structured snippet JSON: these point to separate excluded full text, and are not automatically excluded because they are source-derived. New embedded raw full-text formats require a future content gate.
'''
(B/'public-repository-exclusion-proposal-20260920.md').write_text(md,encoding='utf-8')
print(json.dumps({k:result[k]for k in ['head','tracked_files','reachable_history_path_union','proposed_current_file_count','proposed_allhistory_path_count','proposed_current_total_bytes','proposed_exclusion_counts']},indent=2))
print('SECRET_FINDINGS',json.dumps(secret_hits))
print('PUBLIC_PAGE_COUNT',len(publicpaths),'READER_REFERENCES',len(refs))
print('JSON_SHA256',hashlib.sha256((B/'public-repository-exclusion-proposal-20260920.json').read_bytes()).hexdigest())
