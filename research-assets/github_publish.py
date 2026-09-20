"""Scoped GitHub publishing; credentials stay in Git Credential Manager and memory."""
from pathlib import Path
import argparse, json, os, subprocess, urllib.request, urllib.error

GIT = r'C:\Program Files\Git\cmd\git.exe'
OWNER = 'cuiyist'
REPOSITORIES = {'mattersyn': True, 'mattersyn-site': False}

def credential():
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='never')
    result = subprocess.run([GIT, 'credential', 'fill'], input='protocol=https\nhost=github.com\nusername=cuiyist\n\n', text=True, capture_output=True, env=env)
    if result.returncode:
        raise SystemExit('GitHub credential lookup failed; reconnect Git Credential Manager.')
    fields = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
    if not fields.get('password'):
        raise SystemExit('GitHub credential is unavailable.')
    return fields['password']

def api(path, method='GET', payload=None):
    request = urllib.request.Request('https://api.github.com'+path, method=method,
        headers={'Accept':'application/vnd.github+json', 'Authorization':'Bearer '+TOKEN,
                 'User-Agent':'MatterSyn-project-publishing', 'X-GitHub-Api-Version':'2026-03-10'},
        data=json.dumps(payload).encode() if payload is not None else None)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.status, json.loads(response.read() or b'{}')
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return 404, {}
        raise SystemExit(f'GitHub {method} {path} failed with HTTP {error.code}; no credential details logged.')

parser = argparse.ArgumentParser()
parser.add_argument('action', choices=['identity', 'create', 'status', 'enable-pages'])
args = parser.parse_args()
TOKEN = credential()
_, user = api('/user')
if user.get('login', '').lower() != OWNER:
    raise SystemExit('Connected GitHub account is not the requested owner; stopped.')
result = {'account': user['login']}
if args.action == 'identity':
    result['user_id'] = user['id']
else:
    result['repositories'] = []
    for name, private in REPOSITORIES.items():
        status, repo = api(f'/repos/{OWNER}/{name}')
        if status == 404 and args.action == 'create':
            status, repo = api('/user/repos', 'POST', {'name':name, 'private':private,
                'description': 'MatterSyn private research project, structured synthesis data and audit history' if private else 'MatterSyn materials synthesis atlas — public website',
                'homepage': 'https://cuiyist.github.io/mattersyn-site/', 'auto_init':False})
        if status != 404 and repo.get('private') is not private:
            raise SystemExit(f'{name} has unexpected visibility; upload stopped.')
        result['repositories'].append({'name':name, 'exists':status!=404,
            'private':repo.get('private'), 'url':repo.get('html_url'), 'default_branch':repo.get('default_branch')})
    if args.action in ('status', 'enable-pages'):
        status, pages = api(f'/repos/{OWNER}/mattersyn-site/pages')
        if status == 404 and args.action == 'enable-pages':
            status, pages = api(f'/repos/{OWNER}/mattersyn-site/pages', 'POST',
                {'source':{'branch':'main', 'path':'/'}, 'build_type':'legacy'})
        result['pages'] = {'exists':status!=404, **{k:pages.get(k) for k in ('status','html_url','source','https_enforced','build_type')}}
        build_status, build = api(f'/repos/{OWNER}/mattersyn-site/pages/builds/latest')
        if build_status != 404:
            result['latest_build'] = {k:build.get(k) for k in ('status','commit','error','created_at','updated_at')}
print(json.dumps(result, indent=2))
