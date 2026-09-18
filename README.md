# Anthropic Take-Home — Technical Docs & Content Engineer

Slice audited: **Skills, Plugins, and Connectors** — the take-home's suggested cross-cutting primitives on claude.com/docs.

## What's in this repo

- **[Part 1 — Audit memo](./part1-audit-memo.md)** — what's wrong (prioritized), what to delete/merge, a proposed information architecture, and what to measure.
- **[Part 2 — Standards](./part2-standards.md)** — a style guide excerpt (5 rules) and a fillable content-type template for "Use in [Surface]" pages.
- **[Part 2 — Before/after](./part2-before-after-cowork-plugins.md)** — `cowork/guide/plugins.md` rewritten against the Part 2 template, with a note on what changed and why.
- **[Part 3 — Checker system](./part3/)** — two working checker prototypes run against a 50-page scrape of the real docs, plus how I'd evaluate the checkers themselves. Start with [`part3/README.md`](./part3/README.md).
- **[Part 4 — Adoption without authority](./part4-adoption-without-authority.md)** — how to get adoption from teams that don't report to this role, and what to do about a team that ignores it.

## Running the checkers

From `part3/`:

```
python3 checker/build_page_index.py    # builds data/known_pages.json from the two site indexes
python3 checker/link_checker.py        # Rule 3: link validity + anchor-text match, writes output/findings.json
python3 checker/semantic_drift_checker.py   # Rule 1: semantic drift; needs ANTHROPIC_API_KEY for Stage B (override the model via ANTHROPIC_MODEL)
```

Full methodology, engineering decisions, and both checkers' evaluation write-ups (false-positive tolerance, degradation detection, staleness prevention) are in [`part3/README.md`](./part3/README.md).
