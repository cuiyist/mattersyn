"""Citation-only scan of an admitted batch; never alter checked pair files."""
import argparse
from datetime import datetime, timezone
import hashlib
import html
import importlib.util
import json
from pathlib import Path
import re
import unicodedata


FIELDS = ('title', 'authors', 'year', 'journal')
PLACEHOLDERS = {'', 'not reported', 'not available', 'not provided', 'not provided in the text', 'not specified', 'not mentioned', 'n/a', 'none', 'unknown', 'authors', 'author', 'title', 'paper', 'article', 'year', 'journal'}
JOURNAL_TITLES = {'acs nano', 'acs publications', 'journal of physical chemistry', 'journal of physical chemistry b', 'journal of physical chemistry c', 'the journal of physical chemistry', 'the journal of physical chemistry b', 'the journal of physical chemistry c', 'chemistry of materials', 'nano letters', 'applied physics letters', 'journal of the american chemical society', 'langmuir', 'nanotechnology', 'nature', 'nature materials', 'scientific reports', 'advanced materials', 'full paper', 'research article', 'communication', 'article', 'articles'}
STAMP = re.compile(r'downloaded\s+(?:via|from|by)|download\s+stamp|copyright\s*\d|©\s*\d|pubs\.acs\.org|www\.[a-z0-9.-]+|accessed\s+on', re.I)


def text(value):
    return ' '.join(html.unescape(str(value or '')).split())


def authority_text(value):
    clean = re.sub(r'</?[^>]+>', '', html.unescape(str(value or '')))
    return ' '.join(clean.split())


def normalized(value):
    return re.sub(r'[^a-z0-9]', '', text(value).lower())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def author_identity(value):
    # Publisher metadata is given-name-first. Compare surnames and leading initials;
    # full given names and abbreviated middle names remain presentation choices.
    value = re.sub(r'(?<=\.)(?=\w)', ' ', authority_text(value))
    if value.count(',') == 1:
        family, given = value.split(',', 1)
        value = given.strip() + ' ' + family.strip()
    folded = unicodedata.normalize('NFKD', value).casefold()
    tokens = [re.sub(r'[^a-z0-9]', '', token) for token in folded.split()]
    tokens = [token for token in tokens if token]
    if tokens and tokens[-1] in {'jr', 'sr', 'ii', 'iii', 'iv'}:
        tokens.pop()
    if not tokens:
        return None
    return tokens[-1], tokens[0][0] if len(tokens) > 1 else None


def author_lists_agree(authors, official):
    if not isinstance(official, list) or not official or any(not isinstance(v, str) or not v for v in official):
        return None
    if not authors or re.search(r'\bet\s+al\.?', authors, re.I):
        return None  # Existing incomplete-author flag already covers this case.
    if ';' in authors:
        names = [re.sub(r'^\s*(?:and|&)\s+', '', v).strip() for v in authors.split(';') if v.strip()]
    elif len(official) == 1 and authors.count(',') == 1:
        names = [authors]  # A single family-comma-given name.
    else:
        names = [v.strip() for v in re.split(r'\s*(?:,|\band\b|&)\s*', authors) if v.strip()]
    left, right = [author_identity(v) for v in names], [author_identity(v) for v in official]
    if any(v is None for v in left + right):
        return None
    return len(left) == len(right) and all(a[0] == b[0] and (a[1] is None or b[1] is None or a[1] == b[1])
                                         for a, b in zip(left, right))


def citation_flags(meta, authority=None):
    flags = []
    for field in FIELDS:
        value = text(meta.get(field))
        if value.lower() in PLACEHOLDERS:
            flags.append({'field': field, 'category': 'missing_or_placeholder_citation'})
        elif STAMP.search(value):
            flags.append({'field': field, 'category': 'download_footer_or_web_stamp'})
    title = text(meta.get('title'))
    if title.lower().strip('.:') in JOURNAL_TITLES or (meta.get('journal') and normalized(title) == normalized(meta['journal'])):
        flags.append({'field': 'title', 'category': 'journal_heading_as_title'})
    authors = text(meta.get('authors'))
    if re.search(r'\bet\s+al\.?\b', authors, re.I):
        flags.append({'field': 'authors', 'category': 'incomplete_author_list'})
    if re.search(r'\b(?:university|institute|laboratory|department|copyright)\b', authors, re.I):
        flags.append({'field': 'authors', 'category': 'affiliation_or_footer_as_authors'})
    if authors and re.search(r'\d|[†‡*]', authors):
        flags.append({'field': 'authors', 'category': 'author_footnote_or_nonnames'})
    year = text(meta.get('year'))
    if year.lower() not in PLACEHOLDERS and not re.fullmatch(r'(?:18|19|20)\d{2}', year):
        flags.append({'field': 'year', 'category': 'invalid_publication_year'})
    if authority:
        cite = authority['citation']
        if authors.lower() not in PLACEHOLDERS and author_lists_agree(authors, cite.get('authors')) is False:
            flags.append({'field': 'authors', 'category': 'doi_authority_author_identity_mismatch'})
        if meta.get('title') != authority_text(cite['title'][0]):
            flags.append({'field': 'title', 'category': 'doi_authority_title_mismatch'})
        dates = cite.get('published-print') or cite.get('published') or cite.get('published-online')
        if dates and str(dates['date-parts'][0][0]) != year:
            flags.append({'field': 'year', 'category': 'doi_authority_print_or_publication_year_mismatch'})
    return [dict(values) for values in dict.fromkeys(tuple(sorted(row.items())) for row in flags)]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--batch', required=True)
    ap.add_argument('--pairs', type=Path, required=True)
    ap.add_argument('--route-summary', type=Path, required=True)
    ap.add_argument('--converter', type=Path, required=True)
    ap.add_argument('--authority', type=Path, required=True)
    ap.add_argument('--additional-findings', type=Path)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    if not re.fullmatch(r'batch[1-9][0-9]*', args.batch):
        ap.error('--batch must be an explicit batch identifier such as batch31')
    if args.out.exists():
        raise ValueError('Preserve previous preflight and its findings')
    summary = json.loads(args.route_summary.read_text(encoding='utf-8-sig'))
    projected = {str(row['doi']).lower(): row for row in summary['papers']}
    authorities = {row['doi']: row for row in json.loads(args.authority.read_text(encoding='utf-8-sig'))['records'] if 'citation' in row}
    additional = {}
    if args.additional_findings:
        for item in json.loads(args.additional_findings.read_text(encoding='utf-8'))['items']:
            if item['doi'] not in projected or item['field'] not in FIELDS:
                raise ValueError('Additional findings must be scoped citation metadata')
            additional.setdefault(item['doi'], []).append(item)
    spec = importlib.util.spec_from_file_location('citation_metadata_converter', args.converter)
    converter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(converter)
    rows = []
    for path in sorted(args.pairs.glob('*.pairs.json')):
        original = path.read_bytes()
        doc = json.loads(original.decode('utf-8-sig'))
        doi = str(doc.get('doi') or '').strip().lower()
        if doi not in projected:
            raise ValueError('Original checked document lacks final saved projection')
        metadata = {field: doc.get(field) if doc.get(field) is not None else '' for field in FIELDS}
        ids = [row['record_id'] for row in projected[doi].get('records', [])]
        eligible = [row['record_id'] for row in projected[doi].get('records', []) if row.get('eligible') is True]
        metadata_identity = dict(metadata, doi=doi, id=doc['id'])
        flags = citation_flags(metadata, authorities.get(doi))
        for finding in additional.get(doi, []):
            if metadata[finding['field']] != finding['expected_before']:
                raise ValueError('Additional metadata finding is stale')
            flags.append({'field': finding['field'], 'category': finding['category']})
        rows.append({'doi': doi, 'id': doc['id'], 'pair_file': str(path.resolve()),
            'pair_sha256': hashlib.sha256(original).hexdigest(), 'citation_metadata': metadata,
            'defective_fields': flags,
            'projected_source_id': converter.Builder(metadata_identity).source_id,
            'projected_stable_record_ids': ids, 'projected_eligible_record_ids': eligible,
            'saved_projection_only': True, 'pair_count': len(doc.get('pairs') or [])})
    flagged = [row for row in rows if row['defective_fields']]
    unresolved = [row['doi'] for row in flagged if row['doi'] not in authorities]
    result = {'schema': 'private-simple-bibliographic-preflight-2', 'batch': args.batch,
        'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
        'completed_pair_files': len(rows), 'metadata_flags': len(flagged),
        'flagged_dois': [row['doi'] for row in flagged],
        'defective_field_count': sum(len(row['defective_fields']) for row in flagged),
        'items': rows, 'route_summary_sha256': sha(args.route_summary),
        'converter_sha256': sha(args.converter), 'authority_metadata_sha256': sha(args.authority),
        'additional_metadata_findings_sha256': sha(args.additional_findings) if args.additional_findings else None,
        'unresolved_flagged_authorities': unresolved, 'pair_mutations': 0,
        'ids_regenerated': False, 'scientific_payload_or_quotes_saved': False,
        'publication_or_eligibility_credit': 0, 'shared_writes': 0}
    with args.out.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'completed_pair_files': len(rows), 'flagged_papers': len(flagged),
                      'flagged_dois': result['flagged_dois'],
                      'unresolved_flagged_authorities': unresolved, 'pair_mutations': 0, 'shared_writes': 0}))


if __name__ == '__main__':
    main()

