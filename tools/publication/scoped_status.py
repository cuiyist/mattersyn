"""Versioned, fail-closed status contract for selected-paper release routes.

Version 1 preserves only the exact statuses that the historical release gate
accepted. New frozen packages use version 2 and one canonical display status;
new prose does not need a release-gate patch.
"""

SCOPED_INDEPENDENT_AUDIT = 'scoped_independent_audit'
CANONICAL_MAIN_STATUS = 'scoped_independently_audited'
LEGACY_MAIN_STATUSES = frozenset({
    'selected_colloidal_method_and_figure_independently_audited',
    'selected_recipe_and_figure_independently_audited',
    'selected_as_prepared_cds_route_and_figures_independently_audited',
    'selected_colloidal_methods_and_figures_independently_audited',
    'selected_synthesis_and_figures_independently_audited',
    'main_synthesis_and_figures_independently_audited',
    'scoped_synthesis_and_figures_independently_audited',
    'main_screen_hold_scoped_independently_audited',
    'all_main_pages_scoped_independently_audited',
    'main_pp1_2_scoped_independently_audited',
})


def eligible_scoped_status(row):
    if row.get('review_scope_kind') != SCOPED_INDEPENDENT_AUDIT:
        return False
    version = row.get('review_scope_contract_version')
    if type(version) is not int:
        return False
    if version == 1:
        return row.get('main_status') in LEGACY_MAIN_STATUSES
    if version == 2:
        return row.get('main_status') == CANONICAL_MAIN_STATUS
    return False
