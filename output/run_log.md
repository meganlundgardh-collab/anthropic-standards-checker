# Run log — judgment calls on `output/findings.json`

Written by hand after reading through the actual findings, not auto-generated. This is where the "a few checker mistakes" the assignment explicitly asked for actually get looked at, rather than just tolerated in aggregate.

Run: 50 pages scanned, 262 internal links extracted → 3 BROKEN, 109 ANCHOR_MISMATCH, 0 UNINDEXED, 0 UNVERIFIED, 150 OK.

**This is the second run.** The first run extracted only 164 links. See "What changed in this rerun," below, for why, and for a new false-positive pattern this fix surfaced that the first run couldn't have shown at all.

## What changed in this rerun (fragment-link fix)

`LINK_RE` (the regex that finds internal markdown links) excluded any link whose target contained a `#fragment` — not by matching it and dropping the fragment, but by failing to match the link at all, silently, so those links never became findings. `normalize()` had a second, compounding bug: it only stripped fragments via `urlparse()` for links starting with `http`, so even a widened regex would have produced un-resolvable targets like `/claude-tag/concepts/glossary#access-bundle` for the far more common case of a relative link.

Verified before fixing: a fragment-aware scan of all 50 scraped pages found 98 internal links with a `#` fragment, out of roughly 262 total — over a third of all internal links on this slice of the docs, invisible to every run of this checker until now. `findings.json` had zero entries with `#` in `href`, confirming none of them had ever been extracted. This is concentrated on Claude Tag's admin pages, which lean heavily on `#section` cross-references into shared glossary/concepts pages — exactly the kind of link this checker exists to validate, and exactly the kind it was silently skipping.

The fix: widened `LINK_RE`'s character classes to allow `#` (previously explicitly excluded), so the full href — path plus fragment — is captured. Rewrote `normalize()` to always run the target through `urlparse()` rather than only for `http`-prefixed strings; `urlparse()` turns out to strip the fragment (and resolve to just `.path`) correctly for a relative string with no scheme too, so this isn't a special case, it's the general one the original code should have used from the start.

Rerunning: **262 links extracted (164 + 98, exactly as predicted), 3 BROKEN (unchanged), 28 non-fragment ANCHOR_MISMATCH (unchanged — same findings as the first run, see below), 133 non-fragment OK (unchanged).** Nothing about the pre-existing findings moved, which is the result you want from a fix that's supposed to only add previously-invisible data, not change how existing data gets classified. The 98 newly-visible fragment links split 81 ANCHOR_MISMATCH / 17 OK / 0 BROKEN — see "The new fragment ANCHOR_MISMATCH pattern," below.

## The new fragment ANCHOR_MISMATCH pattern (81 of the 98 newly-visible links)

Of the 81, 72 have anchor/title token overlap of exactly 0.0 — not "loosely related," zero shared words. Reading through a sample makes the cause obvious and structural, not incidental: a fragment link's anchor text is almost always naming the specific term or section the fragment points to (`'Access bundle'`, `'scope'`, `'environment'`, `'channel manager'`), while this checker's ANCHOR_MISMATCH logic compares that anchor text against the *whole target page's* title (`'Glossary'`, `'Restrict where Claude Tag operates'`, `'Configure per-channel access'`). Those two things are supposed to be different — an anchor reading `'Access bundle'` that links to a specific glossary entry has no reason to resemble the word `'Glossary'` — so comparing them at all is close to a category error for this link shape, not a borderline judgment call the way the stemming gap is.

The clearest concentration: 12 of these land on `/claude-tag/admins/attach-to-scope`, 9 on `/connectors/building/authentication`, 7 on `/claude-tag/concepts/glossary` — pages that are exactly the kind of shared-reference target a well-organized docs site *should* be linking into by section, which means this checker's current logic would flag nearly every well-formed fragment link on this site as a mismatch. That's a much bigger false-positive rate (81 of 262 total findings, ~31%) than the stemming gap ever produced, and unlike stemming it isn't a tokenizer weakness — the comparison itself is against the wrong ground truth. A more correct version would need `known_pages.json` (or a heading index built the way `semantic_drift_checker.py`'s Stage A already walks page sections) to carry per-section headings, and compare a fragment link's anchor text against *that* heading, not the page title, while falling back to the page-title comparison for fragment-less links exactly as today.

All three are `/docs/cowork/3p/extensions`, linked from `cowork/guide/plugins.md`, and all three are exactly Part 1's finding #2: a link to a path that was renamed/never existed as written. Each one correctly resolves a "did you mean" suggestion of `/third-party/claude-desktop/extensions` (anchor text `'MCP, plugins, skills, and hooks'` on both sides, overlap 1.0 — about as confident a suggestion as this metric can produce). This is the checker doing its job: it caught all three instances on the same page, which is exactly what a human skim missed the first time around (Part 1's original finding said "twice"; a fresh fetch during red-teaming found three).

## The 28 ANCHOR_MISMATCH — a mix of real problems and checker limitations

Read through all 28 by hand. They split roughly into two groups:

**Group A — checker false positives caused by no stemming (the majority, ~18 of 28).** The overlap-coefficient metric compares raw tokens, so it treats `submission`/`submitting`, `plugin`/`plugins`, `connector`/`connectors`, `submit`/`submitting`, and `setup`/`set up` (a compound word vs. two split words) as completely unrelated tokens, even though they're the same word to a human. Examples:
- `'submission guidelines'` → real title `'Submitting to the Connectors Directory'`, overlap 0.0 — obviously the right link, wrong only because "submission" and "submitting" don't share a token.
- `'setup'` → real title `'Set up Claude Tag'`, overlap 0.0 — same problem, compound vs. split.
- `'Memory'` (×3, same source page) → real title `'What Claude Tag remembers'`, overlap 0.0 — "memory" and "remembers" share a root a stemmer would catch and this tokenizer doesn't.

This is a known, documented limitation, not an oversight: adding a stemmer (or a small edit-distance/lemma step) would likely close most of Group A. It wasn't added here, on purpose — see the README's "evaluating the checker" section for why leaving it visible is more useful than quietly patching it to zero on this one sample.

**Group B — plausible real terminology drift (the more interesting ~10 of 28).** These have genuinely zero word overlap because the anchor text and the real page title appear to be using different names for the same thing, not just different word forms of the same name:
- `'MCP Bundles (MCPB)'` linking to a page titled `'Desktop extensions'` (`connectors/overview` → `connectors/custom/desktop-extensions`). These may be the same underlying feature under two different names used in two different places, which is worth a human docs-team look, not a checker fix — a script can flag "these don't match," it can't decide which name is the mistake.
- `'skill authoring guide'` (×2, from `government/desktop/skills.md`) linking to a page titled `'Creating custom skills'` — plausibly a stale anchor phrase left over from an earlier page title.
- `'MCP server'` (from `government/desktop/plugins.md`) linking to `'Connectors overview'` — anchor uses implementation-level language ("MCP server") where the target page is framed at the product-concept level ("Connectors"). Possibly intentional, possibly drift.
- `'review criteria'` linking to a page now titled `'Pre-submission checklist'` — reads like the page was renamed and the linking anchor wasn't updated to match, which is precisely the class of problem Rule 3 exists to catch.

These four (and a few similar ones) are flagged here rather than folded silently into the "false positive" bucket, because they're the closest thing this run produced to genuinely new findings beyond what Part 1 already had — small, surface-level instances of the same drift pattern findings #2 and #3 already established, just not big enough on their own to warrant a numbered finding.

## 0 UNINDEXED, 0 UNVERIFIED

No scraped page links to any of the 5 llms.txt/sitemap.xml-disagreement pages in `verified_overrides.json`, so these buckets are empty on this run — not because the logic is unused (see `checker/link_checker.py`'s classification comments), just because the 50-page sample didn't happen to link there. Worth noting explicitly rather than leaving silently zero: an empty bucket in one run is not the same claim as "this checker never finds anything here."
