# Operations Notes

## Front-end asset cache busting

`index.html` references `assets/styles.css`, `assets/motion.js`, and
`assets/app.js` with a `?v=<tag>` query parameter, e.g.:

```html
<link rel="stylesheet" href="./assets/styles.css?v=taste-ui-0715a" />
<script src="./assets/motion.js?v=taste-ui-0715a" defer></script>
<script src="./assets/app.js?v=taste-ui-0715a" defer></script>
```

**Rule: any PR that changes `assets/app.js`, `assets/styles.css`, or
`assets/motion.js` must bump the `?v=` tag on every reference to that file in
`index.html`, in the same PR, and say why in the PR description.**

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
`taste-ui-0715b` for a second bump the same day) - keep using it unless there
is a reason to switch.

### What NOT to do

Do not automate this (e.g. a workflow step that rewrites `index.html`'s `?v=`
tag on every scheduled run). The scheduled `update-news.yml` workflow already
commits `data/*.json` every ~30 minutes; having it also touch `index.html`
would pull a source file into that same automated commit and create merge
conflicts between the bot's commits and any concurrent front-end PR touching
the same line. Bump the tag by hand, as part of the PR that changes the
asset, same as any other source change.
