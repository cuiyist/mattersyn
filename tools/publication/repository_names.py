"""Exact public repository aliases; stored release-policy labels stay unchanged."""
import argparse
import re
import sys

SOURCE_REPO = 'cuiyist/nanoxtalsyn'
SITE_REPO = 'cuiyist/nanoxtalsyn-site'
SITE_URL = 'https://cuiyist.github.io/nanoxtalsyn-site/'
CI_WORKFLOW_NAME = 'NanoXtalSyn source and build checks'
SITE_PUBLISH_WORKFLOW_NAME = 'NanoXtalSyn site publish'
PAGES_WORKFLOW_NAME = 'NanoXtalSyn validated Pages release'
LEGACY_SITE_PUBLISH_WORKFLOW_NAME = 'MatterSyn site publish'
LEGACY_PAGES_WORKFLOW_NAME = 'MatterSyn validated Pages release'

_REPOSITORIES = {
    'mattersyn': SOURCE_REPO,
    'mattersyn-site': SITE_REPO,
    'mattersyn2': 'cuiyist/nanoxtalsyn2',
}
_POLICY_LABELS = {}
for _label, _slug in _REPOSITORIES.items():
    for _alias in (_label, 'cuiyist/'+_label, _slug, _slug.split('/', 1)[1]):
        _POLICY_LABELS[_alias] = _label


def policy_repo_label(repository):
    """Accept only the six exact old/new names under the fixed owner."""
    if not isinstance(repository, str) or repository not in _POLICY_LABELS:
        raise ValueError('Unknown repository identity')
    return _POLICY_LABELS[repository]


def canonical_repository(repository):
    return _REPOSITORIES[policy_repo_label(repository)]


def built_source_commit(message):
    """Read either known Publish footer, without accepting a different owner/repo."""
    commits = re.findall(r'\bBuilt from cuiyist/(?:mattersyn|nanoxtalsyn) ([0-9a-f]{40})(?=[.\s]|$)', message)
    if len(set(commits)) > 1:
        raise ValueError('Publish message names conflicting source commits')
    return commits[0] if commits else ''


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['built-source'])
    parser.parse_args(argv)
    print(built_source_commit(sys.stdin.read()))


if __name__ == '__main__':
    main()
