"""Keep supplied-main coverage distinct from a matched main-plus-SI review."""

MAIN_SI = 'supplied_main_and_matched_si'
MAIN_ONLY = 'supplied_main_only_si_unverified'


def source_review_scope(review):
    scope = review.get('review_scope')
    roles = {doc['role'] for doc in review['documents']}
    if 'main' not in roles:
        raise ValueError('A full main-article review requires a supplied main document')
    if scope == MAIN_SI:
        if 'si' not in roles:
            raise ValueError('Main-plus-SI scope requires a reviewed SI document')
        return {
            'scope': scope,
            'label': 'Complete supplied main + matched SI review',
            'review_status': 'full_documents_reviewed',
            'si_status': 'matched_and_reviewed',
        }
    if scope == MAIN_ONLY:
        if 'si' in roles:
            raise ValueError('Main-only scope cannot include a reviewed SI document')
        return {
            'scope': scope,
            'label': 'Complete supplied main review; SI unverified',
            'review_status': 'main_only_reviewed',
            'si_status': 'not_located_or_verified',
        }
    raise ValueError('Explicit recognized review_scope is required')
