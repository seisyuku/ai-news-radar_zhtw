# Operations Notes

## Front-end asset cache busting

`index.html` references `assets/styles.css`, `assets/motion.js`, and
`assets/app.js` with a `?v=<tag>` query parameter, e.g.:

```html
<link rel="stylesheet" href="./assets/styles.css?v=taste-ui-0716a" />
<script src="./assets/motion.js?v=taste-ui-0716a" defer></script>
<script src="./assets/app.js?v=taste-ui-0716a" defer></script>
```

**Rule: any PR that changes `assets/app.js`, `assets/styles.css`, or
`assets/motion.js` must bump the `?v=` tag on every reference to that file in
`index.html`, in the same PR, and say why in the PR description.**

This rule is enforced by `tests/test_asset_versions.py`, backed by
`tests/asset_manifest.json` (a `{tag: {file: sha256}}` record of what each
asset looked like at each released tag). `pytest` fails red if the three
assets' content doesn't match the manifest entry for the `?v=` tag currently
referenced in `index.html` - whether because a file changed without a version
bump, or a version was bumped without updating the manifest. There is no way
to silently violate the rule and still pass CI.

### Why this matters

GitHub Pages sits behind a CDN, and browsers cache static assets aggressively.
`data/*.json` is fetched unversioned and updates every ~30 minutes via the
scheduled workflow, so readers' browsers pick up new data quickly - but the
front-end JS/CSS that renders that data can stay cached far longer. Without a
version bump, a shipped front-end change (new field, new rendering logic, a
bug fix) can sit invisible for readers who already have the old
`app.js`/`styles.css` cached, while they're already receiving the new
`data/*.json` shape. That mismatch is exactly the class of bug this rule
exists to prevent: new data + old code silently reading fields or DOM
structure it doesn't understand.

### How to bump it

Pick a new tag and replace `?v=<old-tag>` with `?v=<new-tag>` on every
reference in `index.html` (`styles.css`, `motion.js`, `app.js` - keep them in
sync even if only one file actually changed, so there is only ever one tag to
reason about). The existing convention is `taste-ui-MMDDx` (month, day, and a
letter suffix for same-day revisions, e.g. `taste-ui-0715a`, then
`taste-ui-0716a` for a second bump the same day) - keep using it unless there
is a reason to switch.

Standard workflow, in order: **1) change the asset file(s) → 2) bump the
`?v=` tag in `index.html` → 3) add a new entry to
`tests/asset_manifest.json` with the sha256 of each of the three asset files
at their new content → 4) run `pytest tests/test_asset_versions.py`** to
confirm it's green before committing. Compute the hashes with:

```sh
python3 -c "
import hashlib
for name in ('app.js', 'styles.css', 'motion.js'):
    print(name, hashlib.sha256(open(f'assets/{name}', 'rb').read()).hexdigest())
"
```

### What NOT to do

Do not automate this (e.g. a workflow step that rewrites `index.html`'s `?v=`
tag on every scheduled run). The scheduled `update-news.yml` workflow already
commits `data/*.json` every ~30 minutes; having it also touch `index.html`
would pull a source file into that same automated commit and create merge
conflicts between the bot's commits and any concurrent front-end PR touching
the same line. Bump the tag by hand, as part of the PR that changes the
asset, same as any other source change.
