"""Keep supplied main, standalone SI and matched main-plus-SI coverage distinct."""

MAIN_SI = 'supplied_main_and_matched_si'
MAIN_SELECTED_SI = 'supplied_main_and_selected_si'
MAIN_ONLY = 'supplied_main_only_si_unverified'
SI_ONLY = 'supplied_si_only_main_unverified'


def source_review_scope(review):
    scope = review.get('review_scope')
    roles = {doc['role'] for doc in review['documents']}
    if scope == SI_ONLY:
        if roles != {'si'}:
            raise ValueError('SI-only scope requires supplied SI and cannot include a main or unknown document')
        return {
            'scope': scope,
            'label': 'Complete supplied SI review; main unverified',
            'review_status': 'si_only_reviewed',
            'si_status': 'reviewed_standalone_main_unverified',
            'main_status': 'not_located_or_verified',
        }
    if 'main' not in roles:
        raise ValueError('A full main-article review requires a supplied main document')
    if scope == MAIN_SELECTED_SI:
        if roles != {'main', 'si'} or len(review['documents']) != 2:
            raise ValueError('Selected-SI scope requires exactly one main and one si document')
        return {
            'scope': scope,
            'label': 'Complete supplied main + selected matched SI pages; remaining SI unreviewed',
            'review_status': 'main_and_selected_si_reviewed',
            'si_status': 'partially_reviewed',
            'main_status': 'reviewed',
        }
    if scope == MAIN_SI:
        if 'si' not in roles:
            raise ValueError('Main-plus-SI scope requires a reviewed SI document')
        if roles != {'main', 'si'}:
            raise ValueError('Main-plus-SI scope requires exactly main and si document roles')
        return {
            'scope': scope,
            'label': 'Complete supplied main + matched SI review',
            'review_status': 'full_documents_reviewed',
            'si_status': 'matched_and_reviewed',
            'main_status': 'reviewed',
        }
    if scope == MAIN_ONLY:
        if roles != {'main'}:
            raise ValueError('Main-only scope requires exactly the main document role')
        return {
            'scope': scope,
            'label': 'Complete supplied main review; SI unverified',
            'review_status': 'main_only_reviewed',
            'si_status': 'not_located_or_verified',
            'main_status': 'reviewed',
        }
    raise ValueError('Explicit recognized review_scope is required')


def reviewed_page_count(review, *, inventory=False):
    """Validate complete coverage inventories; selected SI never implies full SI."""
    source_review_scope(review)
    partial = review['review_scope'] == MAIN_SELECTED_SI
    total = 0
    for doc in review['documents']:
        count = doc.get('page_count')
        if type(count) is not int or count < 1:
            raise ValueError('Invalid source page count')
        selected = partial and doc['role'] == 'si'
        if selected:
            chosen = doc.get('pages_read')
            if (not isinstance(chosen, list) or not chosen or len(chosen) >= count
                    or any(type(n) is not int or not 1 <= n <= count for n in chosen)
                    or chosen != sorted(set(chosen))):
                raise ValueError('Selected SI pages must be a unique ordered proper subset')
        if inventory:
            if selected:
                if doc.get('all_text_read') is not False or doc.get('all_visually_reviewed') is not False:
                    raise ValueError('Selected SI cannot claim complete document reading')
                total += len(chosen)
            else:
                if any(key in doc and doc[key] is not True for key in ('all_text_read', 'all_visually_reviewed')):
                    raise ValueError('Unread main or incomplete full-document inventory')
                if partial and not all(doc.get(key) is True for key in ('all_text_read', 'all_visually_reviewed')):
                    raise ValueError('Selected SI scope requires fully read main')
                total += count
            continue
        pages = doc.get('pages', [])
        nums = [p.get('page') for p in pages]
        if any(type(n) is not int for n in nums) or sorted(nums) != list(range(1, count + 1)):
            raise ValueError('Incomplete or duplicate page inventory')
        if any(type(p.get(key)) is not bool for p in pages for key in ('text_read', 'visual_review')):
            raise ValueError('Page reading flags must be explicit booleans')
        read = [p['page'] for p in pages if p['text_read'] and p['visual_review']]
        if selected:
            if any(p['text_read'] != p['visual_review'] for p in pages) or sorted(read) != chosen:
                raise ValueError('Selected SI inventory differs from declared reviewed pages')
        elif len(read) != count:
            raise ValueError('Unread or visually unchecked page')
        total += len(read)
    return total
