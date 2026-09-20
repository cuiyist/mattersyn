# Site delivery, access and durable memory

## Existing site or new site

Inspect `.openai/hosting.json` before any Sites lifecycle action. Reuse the existing project and architecture for edits. A local source snapshot does not authorize modifying its original hosted project. For a new site, use the current Sites creation workflow rather than copying another site's project ID.

Follow the available Sites building/hosting skills for previews, version packaging and publication. Use their current helper and tool contracts; do not freeze an old plugin version, port, token workflow or runtime path into a new project.

For the original static MatterSyn site, `dist` is the authored static application, not disposable generated output. If a packaging helper is incompatible with this architecture or local shell, adapt staging to the current static archive contract. Do not replace a working architecture solely to satisfy a starter template. Validate archive contents and exclude `.git`, caches, credentials, downloaded paper collections and unrelated research data.

Publishing invariants:

- The source commit used to build/package the site must be the exact pushed state supplied when saving a version. Obtain the full SHA from the checkout after a successful push.
- Keep repository credentials ephemeral and out of source, URLs, logs and memory.
- Use the site's actual current audience to select deployment. Preserve an already public site across updates; do not silently privatize it or assume every site is owner-private.
- Publishing a website and making it public are distinct actions. Change access only within the user's requested audience. Do not require redundant conversational approval when the session already authorizes the action; follow current tool/system permission requirements.
- Verify deployment completion before claiming success. Reuse the site's existing browser tab for handoff when available.

## Check public access

## MatterSyn GitHub publication choice

The user's latest September 19 choice supersedes the earlier one-public-repository answer. Keep code, memory, skills, structured research data and audit history in PRIVATE `cuiyist/mattersyn`. Publish only website assets in PUBLIC `cuiyist/mattersyn-site`, with the intended Pages address `https://cuiyist.github.io/mattersyn-site/`. Keep downloaded papers and SI local. Existing Site hosting is a historical deployment until the GitHub migration is verified; do not claim the new address is live merely because files are staged.

Separate the public deployment directory from the private project before committing. Preserve available source Git history in the private backup, exclude credentials/runtime dependencies and raw paper/SI files, and record an explicit included/excluded manifest. Verify repository visibility before each first push. GitHub project Pages uses a path prefix: test material, paper and recipe routes, relative data/assets, downloads and interactive viewers under that prefix. Keep canonical scientific values and immutable audits unchanged when adapting presentation URLs; record any deployment-only transformations. Record exact pushed commits and completed Pages deployment, then verify anonymous access. Future publishing must use the verified current destination in project memory.

## Anonymous access verification

When public access is requested, check the current site access mode and use the supported access-change tool. Verify the published root or intended route through an anonymous request with no cookies, Authorization header or bypass token. Check both final URL and actual page content; HTTP200 can still be a login page.

If the anonymous request redirects to authentication, resolve the access setting or hosting behavior before saying the site is public. If an old browser tab remains on a cached login screen after anonymous access succeeds, provide the direct site link and suggest reopening it in a fresh/private window. Do not ask the user to share credentials.

## Memory update

Use the project's existing memory file when present. Record decisions and durable results, not a transcript or command log:

- Research intent and user design preferences.
- Selected paper/DOI and precise method scope; main/SI availability and verification status.
- Location of structured extraction, original sources, source code and scientific-model provenance.
- Important unresolved quantities, inconsistent values, sample links or model limitations.
- Latest site URL, publication outcome, current access and how access was verified.
- Prior examples preserved and how to reach them.
- Changes to reusable workflow preferences, such as stage-specific diagrams and adjacent condition cards.

Keep website status current when changing papers or access. Distinguish accepted user choices from assistant suggestions. Do not include unrelated app settings, credentials, cookies, access bypasses or temporary command output. Never treat memory as authority over fresh access/tool state or the user's latest instruction.
