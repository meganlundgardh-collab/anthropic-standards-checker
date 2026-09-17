# Run log — judgment calls on `output/findings.json`

Written by hand after reading through the actual findings, not auto-generated. This is where the "a few checker mistakes" the assignment explicitly asked for actually get looked at, rather than just tolerated in aggregate.

Run: 50 pages scanned, 164 internal links extracted → 3 BROKEN, 28 ANCHOR_MISMATCH, 0 UNINDEXED, 0 UNVERIFIED, 133 OK.

## The 3 BROKEN — all real, all the same known problem

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
