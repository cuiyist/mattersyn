"""A partial progress card must not prevent the rest of the queue from rendering."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('node'), 'Node is required for the progress renderer check')
class ProgressRenderTests(unittest.TestCase):
    def test_optional_stages_and_trial_hold_render_the_complete_page(self):
        data = json.loads((ROOT / 'data/release-progress.json').read_bytes())
        data['current_work'] = [{'short_label': 'Completed paper', 'title': 'Example',
                                 'stage': 'Published', 'summary': 'Verified.'}]
        data['estimate']['status'] = 'trial_finished_awaiting_user_review'
        script = r"""
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const [modulePath, data] = JSON.parse(fs.readFileSync(0, 'utf8'));
class Element {
  constructor(tag) { this.tag = tag; this.children = []; this.dataset = {}; }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children = nodes; }
  setAttribute(name, value) { this[name] = value; }
}
const nodes = new Map();
const document = {createElement: tag => new Element(tag),
  getElementById: id => {
    if (!nodes.has(id)) nodes.set(id, new Element(id));
    return nodes.get(id);
  }};
let source = fs.readFileSync(modulePath, 'utf8').split("let last='',running=false;")[0];
source = source.replaceAll('import.meta.url', "'https://example.test/mattersyn-site/progress.mjs'");
vm.runInNewContext(source + '\nrender(input);',
  {document, input: data, URL, Intl, Date, location: {origin: 'https://example.test'}});
assert.equal(nodes.get('current-work').children.length, 1);
assert.equal(nodes.get('queue-metrics').children.length, 4);
assert.ok(nodes.get('completion-estimate').children.length > 0);
assert.match(nodes.get('review-progress-brief').textContent, /paused for review/);
assert.doesNotMatch(nodes.get('review-progress-brief').textContent, /Active papers are published/);
"""
        result = subprocess.run([shutil.which('node'), '-e', script],
                                input=json.dumps([str(ROOT / 'static/progress.mjs'), data]),
                                text=True, capture_output=True, encoding='utf8')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
