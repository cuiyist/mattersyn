"""N6: scan every allowlisted published text body; import/default invocation inert.

Candidate mode reads the existing CI build only. Published mode fetches every
selected public URL anonymously, verifies the approved bytes, and classifies the
actual response. Bodies are never saved. Existing release checks are unchanged.
"""
import argparse
import collections
from concurrent.futures import ThreadPoolExecutor
import datetime
import functools
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import time
import urllib.error
import urllib.parse
import urllib.request

NEW_BASE = 'https://cuiyist.github.io/nanoxtalsyn-site/'
AS_OF = '2026-11-09'
CATEGORIES = ('N4_identifiers', 'record_bytes', 'dated_history', 'anything_else')
TEXT_KINDS = {**dict.fromkeys(('.html', '.htm'), 'page'),
              **dict.fromkeys(('.js', '.mjs', '.cjs'), 'script'), '.css': 'style', '.svg': 'svg',
              **dict.fromkeys(('.json', '.jsonl', '.ndjson', '.csv', '.tsv', '.xml', '.map', '.xyz', '.sdf', '.mol', '.mol2', '.pdb', '.cif', '.cml', '.smi', '.smiles', '.yaml', '.yml', '.toml', '.ini', '.dat'), 'data'),
              **dict.fromkeys(('.md', '.txt', '.rst'), 'document')}
BINARY = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.avif', '.ico', '.woff', '.woff2', '.ttf', '.otf', '.pdf', '.zip', '.gz', '.bz2', '.xz', '.7z', '.mp4', '.webm', '.mp3', '.wav', '.wasm', '.npy', '.npz'}
OLD = re.compile('mattersyn', re.I)
OLD_REPO_URL = re.compile(r'(?:https?://(?:github\.com/|api\.github\.com/repos/|raw\.githubusercontent\.com/)|git@github\.com:)cuiyist/mattersyn(?:-site|2)?(?:\.git)?(?=[/?#\s\"\'<>]|$)|https?://cuiyist\.github\.io/mattersyn-site(?=[/?#\s\"\'<>]|$)', re.I)
URL = re.compile(r'https?://[^\s\"\'<>]+')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def pin(path):
    raw = Path(path).read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': digest(raw)}


def canonical(value):
    need(isinstance(value, str) and value and '\\' not in value and '\0' not in value
         and not PurePosixPath(value).is_absolute() and all(p not in {'', '.', '..'} for p in value.split('/')), 'Canonical manifest path required')
    return value


def inventory(root, manifest, phase):
    if phase == 'candidate':
        need(manifest.get('schema') == 'mattersyn-unapproved-build-candidate/1', 'Existing candidate manifest required')
    else:
        need(manifest.get('schema_version') == 'mattersyn-public-release-allowlist/1'
             and manifest.get('repo') == 'mattersyn-site', 'Exact normal Site allowlist required')
    rows = manifest.get('files'); need(isinstance(rows, list), 'Manifest files required')
    selected, excluded, seen = [], collections.Counter(), set()
    for row in rows:
        relative = canonical(row['path']); need(relative not in seen, 'Duplicate manifest path'); seen.add(relative)
        need(type(row.get('bytes')) is int and row['bytes'] >= 0 and re.fullmatch('[a-f0-9]{64}', str(row.get('sha256', ''))), 'Exact manifest bytes/SHA required')
        if phase == 'published':
            need(row.get('decision') == 'allow' and row.get('review_status') == 'approved', 'Every selected Site row must retain normal approval')
        file = root / relative
        need(file.resolve().is_relative_to(root.resolve()) and file.is_file() and not file.is_symlink(), 'Manifest leaf missing/unsafe in existing preview')
        suffix = file.suffix.lower(); kind = TEXT_KINDS.get(suffix)
        if kind is None and suffix not in BINARY:
            with file.open('rb') as stream:
                prefix = stream.read(4096)
            try:
                prefix.decode('utf8'); kind = 'other_text' if b'\0' not in prefix else None
            except UnicodeDecodeError:
                pass
        if kind is None:
            excluded[suffix or '[no suffix]'] += 1
        else:
            selected.append({**row, 'kind': kind})
    return selected, dict(excluded), len(rows)


def record_pins(blueprint):
    need(blueprint.get('schema') == 'mattersyn-build-input-blueprint/1', 'Normal Source blueprint required')
    prefix = 'recipe-atlas/data/records/'
    return {'data/records/' + row['path'][len(prefix):]: row for row in blueprint.get('input_files', [])
            if row.get('path', '').startswith(prefix) and row['path'].endswith('.json')}


def dated_spans(relative, text, identifiers):
    """Only pre-Nov9 date fields with exact pinned LF section bytes qualify."""
    if not relative.endswith('.md'):
        return []
    lines = text.splitlines(keepends=True); positions = []; offset = 0
    for line in lines:
        positions.append(offset); offset += len(line)
    headings = [(i, len(match[1]), match[2]) for i, line in enumerate(lines) if (match := re.match(r'^(#{1,6})\s+(.*)', line))]
    approved = {(row['date'], row['section_LF_sha256']) for row in identifiers.get('dated_history_sections', [])
                if row['path'] == relative and row['date'] < AS_OF}
    spans = []
    for index, (line, level, title) in enumerate(headings):
        dates = re.findall(r'\b(20\d{2}-\d{2}-\d{2})\b', title)
        if len(dates) != 1:
            continue
        try:
            date = datetime.date.fromisoformat(dates[0]).isoformat()
        except ValueError:
            continue
        end = next((other for other, depth, _ in headings[index + 1:] if depth <= level), len(lines))
        section = ''.join(lines[line:end]); section_hash = digest(section.replace('\r\n', '\n').replace('\r', '\n').encode())
        if (date, section_hash) in approved:
            spans.append((positions[line], positions[end] if end < len(positions) else len(text), {'date': date, 'section_LF_sha256': section_hash}))
    return spans


def technical_tokens(identifiers, published_paths):
    exact = set(identifiers.get('schema_tokens', [])) | set(identifiers.get('env_tokens', [])) | set(identifiers.get('global_tokens', [])) | set(identifiers.get('technical_folder_tokens', [])) | set(identifiers.get('schema_URIs', [])) | set(identifiers.get('internal_marker_tokens', []))
    for path in published_paths:
        if OLD.search(path):
            exact.add(path)
            if OLD.search(PurePosixPath(path).name):
                exact.add(PurePosixPath(path).name)
    return tuple(sorted(exact, key=len, reverse=True))


def token_spans(relative, text, identifiers, exact):
    spans = []
    for token in sorted(exact, key=len, reverse=True):
        need(isinstance(token, str) and token.casefold() != 'mattersyn' and OLD.search(token), 'No bare-brand N4 exemption')
        if token not in text: continue  # A missing literal cannot satisfy its exact-token regex.
        tail = (r'(?![A-Za-z0-9_./:-])' if token in identifiers.get('internal_marker_tokens', []) else
                r'(?![A-Za-z0-9_.-])' if token in identifiers.get('technical_folder_tokens', []) else r'(?![A-Za-z0-9_./-])')
        spans.extend((m.start(), m.end(), 'exact_technical_token') for m in re.finditer(r'(?<![A-Za-z0-9_])' + re.escape(token) + tail, text))
    for prefix in identifiers.get('artifact_prefixes', []):
        spans.extend((m.start(), m.end(), 'artifact_name') for m in re.finditer(re.escape(prefix) + r'[A-Za-z0-9_.$/{\}-]*', text))
    labels = '|'.join(re.escape(x) for x in identifiers.get('repo_labels', []))
    patterns = [r'[\"\'](?:repo|repo_kind|repo_label|repository_label)[\"\']\s*:\s*[\"\'](?P<label>' + labels + r')[\"\']',
                r'\brepo(?:_kind|_label)?\s*(?:==|!=)\s*[\"\'](?P<label>' + labels + r')[\"\']',
                r'--repo\s+(?P<label>' + labels + r')(?=[\s\"\']|$)']
    if relative.startswith('tools/mattersyn-release/') and relative.endswith('.py'):
        patterns.append(r'[\"\'](?P<label>' + labels + r')[\"\']')
    if relative.startswith('.release-control/'):
        patterns.append(r'[\"\'](?P<label>' + labels + r')[\"\']\s*:')
    for pattern in patterns:
        spans.extend((m.start('label'), m.end('label'), 'policy_repo_label') for m in re.finditer(pattern, text))
    return spans


EXPORT_TASKS = {'precursor_selection', 'partial_protocol', 'size_conditioned_recipe', 'exact_structure_recipe', 'success_prediction', 'optical_outcome'}


def semantic_digest(value):
    return digest(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode())


def record_loader(root, records, manifest):
    """Reuse existing preview bytes in RAM, requiring BOTH Source and Site pins."""
    @functools.lru_cache(maxsize=None)
    def load(record_id):
        relative = 'data/records/' + record_id + '.json'
        canonical(relative)
        source = records.get(relative); approved = manifest.get(relative)
        need(source and approved and (source['bytes'], source['sha256']) == (approved['bytes'], approved['sha256']), 'Aggregate record Source/Site pin differs')
        raw = (root / relative).read_bytes()
        need((len(raw), digest(raw)) == (source['bytes'], source['sha256']), 'Aggregate record reference byte pin differs')
        value = json.loads(raw)
        need(value.get('record_id') == record_id, 'Aggregate record ID differs')
        return value, source
    return load


def record_export_spans(relative, text, load_record):
    """Exact exported record objects/fields, never a path-only JSON exemption.

    build_dataset writes records.jsonl as unchanged record objects; the six
    task exports carry record_id plus the canonical semantic record SHA. Only
    literal string VALUES copied from that pinned record may qualify there.
    """
    task = PurePosixPath(relative).stem
    full = relative == 'data/records.jsonl'
    training = relative == 'data/exports/' + task + '.jsonl' and task in EXPORT_TASKS
    if load_record is None or not (full or training):
        return []
    spans = []; offset = 0
    for line in text.splitlines(keepends=True):
        if OLD.search(line):
            row = json.loads(line); rid = row.get('record_id')
            need(isinstance(rid, str), 'Record export provenance ID missing')
            original, source = load_record(rid)
            proof = {'record_id': rid, 'Source_record_sha256': source['sha256']}
            if full:
                need(row == original, 'Full record JSONL differs from pinned canonical record')
                spans.append((offset, offset + len(line), {**proof, 'basis': 'exact_record_object_in_JSONL'}))
            else:
                need(row.get('task') == task and row.get('record_sha256') == semantic_digest(original)
                     and set(row) <= {'record_id', 'task', 'input', 'output', 'provenance', 'group_id', 'split', 'record_sha256'}, 'Training export record/task/digest shape differs')
                leaves = {}
                def visit(value, pointer=''):
                    if isinstance(value, str) and OLD.search(value): leaves.setdefault(value, pointer)
                    elif isinstance(value, dict):
                        for key, child in value.items(): visit(child, pointer + '/' + str(key).replace('~', '~0').replace('/', '~1'))
                    elif isinstance(value, list):
                        for i, child in enumerate(value): visit(child, pointer + '/' + str(i))
                visit(original)
                for match in re.finditer(r'"(?:\\.|[^"\\])*"', line):
                    # A JSON key is never a copied record value.
                    if re.compile(r'\s*:').match(line, match.end()): continue
                    value = json.loads(match[0])
                    if value in leaves:
                        spans.append((offset + match.start(), offset + match.end(), {**proof, 'basis': 'exact_copied_record_string_field', 'Source_field': leaves[value]}))
        offset += len(line)
    return spans


def classify(relative,raw,records,identifiers,exact_tokens,load_record=None):
    text=raw.decode('utf-8-sig');matches=list(OLD.finditer(text))
    if not matches:return collections.Counter(),[]
    expected=records.get(relative)
    record_exact=expected is not None and(len(raw),digest(raw))==(expected['bytes'],expected['sha256'])
    histories=dated_spans(relative,text,identifiers)if not record_exact else[]
    exports=record_export_spans(relative,text,load_record)if not record_exact else[]
    if not record_exact:
        # Preserve every token/config/regex validation without scanning the body.
        token_spans(relative,'',identifiers,exact_tokens)
    tokens=None;old_urls=None;export_index=0
    counts=collections.Counter();evidence=[];cursor=0;line_number=1;line_start=0
    for match in matches:
        start=match.start();category='anything_else';proof='no_exact_N4_proof'
        while export_index<len(exports)and exports[export_index][1]<=start:export_index+=1
        field=(exports[export_index][2]if export_index<len(exports)and exports[export_index][0]<=start<exports[export_index][1]else None)
        if record_exact:category,proof='record_bytes','exact_Source_blueprint_bytes_SHA256'
        elif field:category,proof='record_bytes',field
        elif history:=next((p for a,z,p in histories if a<=start<z),None):category,proof='dated_history',history
        else:
            if old_urls is None:old_urls=[(m.start(),m.end())for m in OLD_REPO_URL.finditer(text)]
            if any(a<=start<z for a,z in old_urls):proof='current_old_repository_or_Pages_URL'
            else:
                if tokens is None:tokens=token_spans(relative,text,identifiers,exact_tokens)
                if token:=next((p for a,z,p in tokens if a<=start<z),None):category,proof='N4_identifiers',token
        line_number+=text.count('\n',cursor,start)
        previous_newline=text.rfind('\n',cursor,start)
        if previous_newline>=0:line_start=previous_newline+1
        cursor=start;counts[category]+=1
        evidence.append({'line':line_number,'column':start-line_start+1,'category':category,'proof':proof})
    return counts,evidence


def transient(error):
    if isinstance(error, urllib.error.HTTPError):
        return error.code == 429 or 500 <= error.code < 600
    return isinstance(error.reason if isinstance(error, urllib.error.URLError) else error, (TimeoutError, ConnectionResetError))


def anonymous_bytes(url, expected_bytes):
    request = urllib.request.Request(url, headers={'User-Agent': 'NanoXtalSyn-N6-public-text-scan', 'Cache-Control': 'no-cache'})
    with urllib.request.urlopen(request, timeout=60) as response:
        final = urllib.parse.urlsplit(response.geturl()); base = urllib.parse.urlsplit(NEW_BASE)
        need(response.status == 200 and final.scheme == base.scheme and final.netloc == base.netloc and final.path == urllib.parse.urlsplit(url).path, 'Unexpected public response/redirect')
        return response.read(expected_bytes + 1)


def read_live(row, source, fetch=anonymous_bytes, sleep=time.sleep):
    url = NEW_BASE + urllib.parse.quote(row['path'], safe='/._-~') + '?n_source=' + source
    failures = []
    for attempt in range(1, 4):
        try:
            raw = fetch(url, row['bytes'])
        except Exception as error:
            retryable = transient(error)
            failures.append({'attempt': attempt, 'outcome': 'fetch_error', 'error_class': type(error).__name__,
                             'http_status': error.code if isinstance(error, urllib.error.HTTPError) else None, 'retryable': retryable})
            if retryable and attempt < 3:
                sleep(attempt); continue
            return None, {'attempts': attempt, 'final_outcome': 'fetch_error', 'attempt_failures': failures}
        actual = digest(raw)
        if (len(raw), actual) != (row['bytes'], row['sha256']):
            failures.append({'attempt': attempt, 'outcome': 'bytes_or_SHA256_mismatch', 'actual_bytes': len(raw), 'actual_sha256': actual, 'retryable': False})
            return None, {'attempts': attempt, 'final_outcome': 'bytes_or_SHA256_mismatch', 'attempt_failures': failures}
        return raw, ({'attempts': attempt, 'final_outcome': 'exact_bytes_SHA256_match', 'attempt_failures': failures} if failures else None)


def scan(root, manifest, blueprint, identifiers, phase, source, fetch=anonymous_bytes, sleep=time.sleep, workers=8, event=lambda row: None):
    need(identifiers.get('schema') == 'NanoXtalSyn-N4-exact-identifier-pins/1' and identifiers.get('as_of') == AS_OF, 'Fixed owner-date identifier pins required')
    need(1 <= workers <= 8 and phase in {'candidate', 'published'}, 'Bounded phase/workers required')
    rows, excluded, total = inventory(root, manifest, phase)
    need(manifest.get('source_commit') == source, 'Manifest Source differs from explicit Source')
    records = record_pins(blueprint); paths = {row['path'] for row in manifest['files']}
    exact_tokens = technical_tokens(identifiers, paths)
    load_record = record_loader(root, records, {row['path']: row for row in manifest['files']})
    selected_kinds = collections.Counter(row['kind'] for row in rows)
    totals = collections.Counter(); matched_files = collections.Counter(); scanned_kinds = collections.Counter(); http_kinds = collections.Counter()
    examples = {key: [] for key in CATEGORIES}; errors = []; retries = []; matched_unique = 0
    def one(row):
        try:
            if phase == 'published':
                raw, attempts = read_live(row, source, fetch, sleep)
                if raw is None: return row, None, None, attempts, None
            else:
                raw = (root / row['path']).read_bytes(); attempts = None
                need((len(raw), digest(raw)) == (row['bytes'], row['sha256']), 'Candidate manifest byte pin differs')
            counts, evidence = classify(row['path'], raw, records, identifiers, exact_tokens, load_record)
            return row, counts, evidence, attempts, None
        except Exception as error:
            return row, None, None, None, {'error_class': type(error).__name__, 'message': str(error)[:160]}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for index, (row, counts, evidence, attempts, error) in enumerate(pool.map(one, rows), 1):
            if attempts:
                record = {'path': row['path'], **attempts}; retries.append(record); event({'kind': 'transport', **record})
            if error or counts is None:
                record = {'path': row['path'], 'kind': row['kind'], 'detail': error or attempts}; errors.append(record); event({'kind': 'scan_failure', **record}); continue
            scanned_kinds[row['kind']] += 1
            if phase == 'published': http_kinds[row['kind']] += 1
            if counts:
                matched_unique += 1; totals.update(counts); matched_files.update(counts.keys())
                for item in evidence:
                    if len(examples[item['category']]) < 20:
                        examples[item['category']].append({'path': row['path'], 'sha256': row['sha256'], **item})
                if counts['anything_else']:
                    event({'kind': 'anything_else', 'path': row['path'], 'sha256': row['sha256'], 'counts': dict(counts), 'positions': [x for x in evidence if x['category'] == 'anything_else']})
            if index % 500 == 0:
                print(json.dumps({'N6_selected_processed': index, 'selected_total': len(rows), 'failures': len(errors), 'anything_else': totals['anything_else']}), flush=True)
    return {'schema': 'NanoXtalSyn-N6-full-published-text-scan/1', 'phase': phase, 'passed': not errors and totals['anything_else'] == 0,
            'source_commit': source, 'site_url': NEW_BASE if phase == 'published' else None, 'owner_as_of': AS_OF,
            'allowlisted_file_count': total, 'selected_text_file_count': len(rows), 'selected_files_by_kind': dict(selected_kinds),
            'scanned_files_by_kind': dict(scanned_kinds), 'anonymous_HTTP_verified_files': sum(http_kinds.values()), 'HTTP_verified_by_kind': dict(http_kinds),
            'excluded_binary_or_nontext_files_by_suffix': excluded, 'matching_files_unique': matched_unique,
            'occurrences': {key: totals[key] for key in CATEGORIES}, 'files_with_category': {key: matched_files[key] for key in CATEGORIES},
            'file_category_counts_are_not_additive': True, 'evidence_samples_no_source_text': examples,
            'failure_count': len(errors), 'failures': errors, 'transport_attempt_records': retries,
            'all_selected_HTTP_verified': phase == 'published' and sum(http_kinds.values()) == len(rows) and not errors,
            'record_byte_pin_count': len(records), 'bodies_saved': 0, 'Source_or_remote_mutations': 0}


def published_binding(args, manifest):
    values = {key: json.loads(getattr(args, key).read_bytes()) for key in ('build_receipt', 'stage_receipt', 'push_receipt', 'live_receipt')}
    build, stage, push, live = (values[key] for key in ('build_receipt', 'stage_receipt', 'push_receipt', 'live_receipt'))
    need(all(v.get('source_commit') == args.source_commit for v in values.values()), 'Existing publisher Source identities differ')
    need(push.get('pushed') is True and push.get('site_commit') == args.site_commit and push.get('site_base_commit') == stage.get('site_base_commit'), 'Actual push/stage identity differs')
    need(build.get('candidate_tree_sha256') == build.get('final_tree_sha256') and build.get('allowlist_sha256') == pin(args.manifest)['sha256'], 'Exact gated manifest/build binding differs')
    need(manifest.get('source_commit') == args.source_commit and manifest.get('release_id') == build.get('release_id') == stage.get('release_id'), 'Published allowlist release binding differs')
    need(live.get('passed') is True and live.get('anonymous') is True and live.get('site_url') == NEW_BASE and not live.get('mismatched_files') and not live.get('failed_paper_routes') and not live.get('failed_material_routes'), 'Existing new-Pages anonymous checks must pass first')
    need(live.get('pages_runs') and all(row[1] == 'success' for row in live['pages_runs']), 'Existing Pages success required')
    return {key: pin(getattr(args, key)) for key in values}


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--scan', action='store_true')
    for name in ('root', 'manifest', 'source-blueprint', 'identifiers', 'out', 'build-receipt', 'stage-receipt', 'push-receipt', 'live-receipt'):
        parser.add_argument('--' + name, type=Path)
    parser.add_argument('--phase', choices=['candidate', 'published']); parser.add_argument('--source-commit'); parser.add_argument('--site-commit')
    args = parser.parse_args()
    if not args.scan:
        print('DEFAULT_INERT_NO_SCAN_NETWORK_OR_FILES'); return 0
    need(os.environ.get('GITHUB_ACTIONS') == 'true', 'Full N6 scan runs in existing GitHub CI/publisher only')
    need(all(getattr(args, x) is not None for x in ('root', 'manifest', 'source_blueprint', 'identifiers', 'out', 'phase')) and re.fullmatch('[a-f0-9]{40}', args.source_commit or ''), 'Explicit scan inputs/full Source required')
    need(not args.out.resolve().is_relative_to(args.root.resolve()) and not args.out.exists(), 'Fresh scan receipt outside existing tree required')
    manifest = json.loads(args.manifest.read_bytes()); binding = None
    if args.phase == 'published':
        need(re.fullmatch('[a-f0-9]{40}', args.site_commit or '') and all(getattr(args, k) for k in ('build_receipt', 'stage_receipt', 'push_receipt', 'live_receipt')), 'Actual successful publisher binding required')
        binding = published_binding(args, manifest)
    args.out.parent.mkdir(parents=True, exist_ok=True); events = args.out.with_suffix(args.out.suffix + '.events.jsonl')
    with events.open('xb') as stream:
        def event(value):
            stream.write((json.dumps(value, ensure_ascii=False) + '\n').encode()); stream.flush()
        result = scan(args.root, manifest, json.loads(args.source_blueprint.read_bytes()), json.loads(args.identifiers.read_bytes()), args.phase, args.source_commit, event=event)
    result.update(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), site_commit=args.site_commit,
                  manifest=pin(args.manifest), Source_record_blueprint=pin(args.source_blueprint), N4_identifier_pins=pin(args.identifiers),
                  publisher_binding=binding, failure_events=pin(events), existing_verify_live_route_bindings_are_separate=True)
    with args.out.open('xb') as stream: stream.write(encoded(result))
    print(json.dumps({'N6_receipt': pin(args.out), 'passed': result['passed'], 'selected': result['selected_text_file_count'], 'HTTP_verified': result['anonymous_HTTP_verified_files'], 'occurrences': result['occurrences'], 'failures': result['failure_count']}))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
