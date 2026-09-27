"""Keep supplied main, standalone SI and matched main-plus-SI coverage distinct."""

MAIN_SI = 'supplied_main_and_matched_si'
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
