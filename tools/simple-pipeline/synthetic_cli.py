"""Synthetic extraction/figure child; never calls a server or reads real papers."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


def save(path, value):
    path.write_text(json.dumps(value), encoding='utf8')


def request(work, stem, name, function):
    path = work / f'{stem}.request-times.jsonl'
    with path.open('a', encoding='utf8') as output:
        output.write(json.dumps({'event': 'start', 'name': name, 'time': time.monotonic(), 'pid': os.getpid()}) + '\n')
    time.sleep(0.08)
    function()
    with path.open('a', encoding='utf8') as output:
        output.write(json.dumps({'event': 'end', 'name': name, 'time': time.monotonic(), 'pid': os.getpid()}) + '\n')


def main():
    mode, rest = sys.argv[1], sys.argv[2:]
    if mode == 'check':
        # The real unchanged check command receives only invented synthetic text.
        path = Path(os.environ['SIMPLE_SYNTHETIC_CHECK_SCRIPT'])
        spec = importlib.util.spec_from_file_location('actual_simple_check', path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        parser = argparse.ArgumentParser(); parser.add_argument('work'); parser.add_argument('--out', required=True)
        module.cmd_check(parser.parse_args(rest))
        return 0
    parser = argparse.ArgumentParser()
    parser.add_argument('pdf'); parser.add_argument('--out', required=True); parser.add_argument('--model', required=True)
    parser.add_argument('--redo', action='store_true')
    args = parser.parse_args(rest)
    pdf, work = Path(args.pdf), Path(args.out)
    config = json.loads(pdf.read_text(encoding='utf8'))
    stem = pdf.stem
    invocations = work / f'{stem}.invocations.jsonl'
    with invocations.open('a', encoding='utf8') as output:
        output.write(json.dumps({'mode': mode, 'redo': args.redo, 'model': args.model,
                                'NO_PROXY': os.environ.get('NO_PROXY'),
                                'proxy_keys_present': [key for key in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy') if key in os.environ]}) + '\n')
    if mode == 'figures':
        if config.get('kind') == 'figure-fail':
            return 5
        request(work, stem, 'figure', lambda: save(work / f'{stem}.figures.json', []))
        return 0
    if mode != 'extract':
        raise ValueError('Only synthetic extract/figures and actual check are allowed')
    (work / f'{stem}.text.txt').write_text('[page 1]\nSynthetic CdSe prepared at 120 C for 3 minutes.\n', encoding='utf8')
    save(work / f'{stem}.pages.json', {'pages_read': [1], 'page_count': 1})
    for letter in ('A', 'B'):
        target = work / f'{stem}.pass{letter}.json'
        if target.exists() and not args.redo:
            continue
        def emit(letter=letter, target=target):
            kind = config.get('kind', 'ok')
            if letter == 'B' and (kind == 'always-fail' or kind == 'once-fail' and not args.redo):
                save(target, {'error': 'invented failure'}); return
            if letter == 'A' and kind == 'malformed-once' and not args.redo:
                save(target, {'pairs': [None]}); return
            temperature = {'value': 120, 'unit': 'C', 'quote': 'prepared at 120 C'}
            if kind == 'unfound-quote':
                temperature['quote'] = 'absent synthetic temperature 120 C'
            elif kind == 'wrong-number':
                temperature['value'] = 999
            elif kind == 'disagreement' and letter == 'B':
                temperature['value'] = 130
            save(target, {'title': 'Synthetic test only', 'doi': config['doi'], 'pairs': [] if kind == 'no-pairs' else [{
                'product': 'Synthetic CdSe', 'structure': {'composition': {'value': 'CdSe', 'quote': 'Synthetic CdSe'}},
                'recipe': {'reaction_temperature': temperature,
                           'reaction_time': {'value': 3, 'unit': 'min', 'quote': 'for 3 minutes'}}}]})
        request(work, stem, letter, emit)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
