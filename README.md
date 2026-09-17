# Part 3 — Checker prototypes

Two automated checkers for Part 2's style guide, run against a real 50-page slice of claude.com/docs (the exact slice Part 1 audited: all Skills and Plugins pages, all 37 Connectors pages, and 9 previously-examined surface pages).

**`checker/link_checker.py`** — Rule 3: *"Internal links must resolve, and anchor text must match the destination's real title."* The core module. Picked first because it's the most mechanically checkable rule without needing a model in the loop — pure regex extraction plus set comparison — and because it's the rule that would have caught this project's own worst mistake (see "Evaluating the checker," below).

```
python3 checker/link_checker.py
```

Reads `scrape/` and `data/`, writes `output/findings.json`, prints a summary to stdout. `output/run_log.md` is a hand-written follow-up looking at specific results, not auto-generated.

**`checker/semantic_drift_checker.py`** — Rule 1: *"A local definition may exist for context, but must not drift from canonical."* A second, smaller, clearly-labeled module built time-permitting — see "Second module," below, for why it's architecturally different from the link checker and what it actually found.

```
python3 checker/semantic_drift_checker.py
```

Reads `scrape/`, writes `output/semantic_drift_candidates.json`. `output/semantic_drift_findings.md` has this run's actual verdicts and how they were produced.

## Why the data pipeline looks the way it does

**The scrape is WebFetch-based, not a raw crawl — that's an environment constraint, not a design choice.** This sandbox's outbound network policy blocks raw HTTP calls to claude.com; all page content came through the WebFetch tool (via 5 parallel sub-agents, each fetching 10 pages with a literal/verbatim prompt so the content wasn't summarized/lossy). A production version of this checker would run a normal crawler or HTTP client against the live site or a build artifact; the checking logic in `link_checker.py` doesn't care where the markdown came from and would be unchanged.

**Ground truth comes from two independent indexes, not one, because one alone is provably unreliable.** `claude.com/docs/llms.txt` (Anthropic's own curated index for LLM consumers) and `claude.com/docs/sitemap.xml` (a standard, presumably build-generated sitemap) are two separately-produced lists of every page on the site. `checker/build_page_index.py` unions them into `data/known_pages.json`. They mostly agree — for this slice, exactly (37/2/2 for Connectors/Skills/Plugins). Where they don't agree site-wide, trusting either one alone would have been a mistake in a different direction each time, and finding out which one was wrong took a live fetch, not just picking the "more official-sounding" source. That's not a hypothetical: it's exactly what happened while building this checker (next section).

## Evaluating the checker: what happened while building it

This is the assignment's explicit ask — "how would you evaluate the checker itself?" — and the honest answer came from a real incident during this checker's own data prep, not a hypothetical.

Building `data/verified_overrides.json` (the manual live-check for the handful of pages where `llms.txt` and `sitemap.xml` disagree) required re-examining Part 1's finding #3, which had originally claimed `connectors/building/mcpb.md` was a real page missing from `llms.txt`. A clean, literal re-fetch showed that claim was wrong — the page *is* listed. Looking for a replacement piece of evidence, an automated fetch of `third-party/claude-desktop/models` returned a 404, so that got proposed as the new example of an index problem — and that was *also* wrong: the page loads fine (confirmed independently in a human's own browser), and a second fetch of the same URL with a literal `.md` suffix returned full real content. The most likely explanation is a stale cache entry or a tool-specific quirk on that exact route; the precise mechanism was never fully pinned down, only that the automated result was false.

What survived, independently verified by a human opening each page directly rather than trusting any single automated fetch, was narrower and real: `sitemap.xml` (not `llms.txt`) is missing four live pages that `llms.txt` correctly lists. That's the finding that made it into Part 1's memo and into `data/verified_overrides.json`.

**The lesson, and it's a direct, worked answer to the "how do you evaluate this checker" question:** a single automated fetch returning an error is not proof a link is dead. This checker's own data-prep process produced a false positive from exactly that mistake, twice, within the same hour. Concretely, that means:

- **False-positive tolerance and why:** for a BROKEN verdict specifically, the cost of being wrong is asymmetric — a false BROKEN sends someone chasing a link that was never actually dead, and if that happens more than rarely, people stop trusting the tool's BROKEN output at all (the same failure mode this checker's own build process just demonstrated firsthand). A production version of this checker should not report BROKEN off a single fetch; it should retry with backoff and require at least two failures (ideally on different days, to rule out transient outages) before surfacing a page as dead, and should always emit *what* failed (status code, timeout, etc.) so a human isn't re-debugging from scratch. ANCHOR_MISMATCH is a softer signal by design — it's explicitly not "your link is wrong," it's "go look at this" — so it can tolerate a much higher false-positive rate than BROKEN can; `output/run_log.md` shows this run's ANCHOR_MISMATCH bucket is genuinely about half checker artifacts (mostly a missing stemming step — "submission" vs. "submitting" doesn't token-match) and half plausible real findings, and that's an acceptable mix for a signal that's meant to be triaged by a person, not acted on automatically.
- **How to detect degradation:** track the false-positive rate of each bucket over time by spot-checking a sample of flagged links each run (the way `run_log.md` does here, by hand, for this one run) — if ANCHOR_MISMATCH's real-finding rate drops as the docs site's naming conventions drift from what the similarity heuristic assumes, or if BROKEN's confirmed-real rate drops because of a change in fetch behavior (a redirect policy change, a new auth wall, a CDN quirk), that's the signal to retune the metric or the retry logic — not to keep shipping the same thresholds indefinitely.
- **What keeps it from going stale:** the ground-truth index (`known_pages.json`) is only as current as the last time `build_page_index.py` ran against live `llms.txt`/`sitemap.xml`; it should run on a schedule (or on every docs deploy) rather than once, and `verified_overrides.json` — the file this whole incident lives in — needs the same discipline: it's hand-verified truth, but "hand-verified on 2026-09-17" has a shelf life, and a page that's confirmed live today isn't guaranteed live in six months. A production checker should re-verify overrides periodically rather than treating a manual confirmation as permanent.

## Classification scheme

Each internal link on each scraped page gets exactly one status:

| Status | Meaning |
|---|---|
| `BROKEN` | Target isn't a real page in either index or the verified-overrides fallback. Attaches a "did you mean" suggestion when the anchor text closely resembles another real page's title. |
| `UNINDEXED` | Target is a real, live page but missing from `llms.txt` — Part 1 finding #3's original pattern, generalized (empty on this run; see `run_log.md`). |
| `ANCHOR_MISMATCH` | Target resolves and its real title is known, but the anchor text doesn't look like that title. |
| `UNVERIFIED` | Target resolves but no title is available to compare against (not in `llms.txt`, not one of the 50 scraped pages) — deliberately *not* counted as a pass. A checker that reports "OK" when it actually has no data would be worse than one that says "can't tell." |
| `OK` | Target resolves and anchor text matches its title. |

## Anchor-title similarity: what it is and why it changed mid-build

`similarity(anchor, title)` is an **overlap coefficient** — `|tokens(anchor) ∩ tokens(title)| / min(|tokens(anchor)|, |tokens(title)|)` — not Jaccard. The first version used Jaccard (over the *union* of tokens) and produced a 35% (57/164) ANCHOR_MISMATCH rate; reading through the flags showed most of them were short, legitimate anchors being penalized purely for being shorter than the real title ("MCP tunnel" linking to a page titled "MCP tunnels overview" scores low under Jaccard for no reason other than the title having an extra word). Switching to overlap coefficient — dividing by the smaller set instead of the union — means a short anchor whose words all appear in the title scores a perfect 1.0, and cut the rate to 17% (28/164).

That fix is documented as a deliberate, principled improvement, not a tuning pass aimed at this one sample: the remaining 28 flags were read by hand and mostly turned out to be a *different*, still-real limitation — no stemming, so "submission" and "submitting" don't token-match even though they're the same word. That wasn't patched here on purpose (see `run_log.md`'s Group A/Group B breakdown) — fixing it would have made this run's output cleaner but wouldn't be evidence the fix generalizes, and the assignment specifically asked for real output including checker mistakes rather than a scrubbed sample.

## Second module: Rule 1 semantic-drift checker

`checker/semantic_drift_checker.py` targets Rule 1 instead of Rule 3, and it's a genuinely different kind of checker, not just more of the same code. Rule 3 is pure structural comparison — a link resolves or it doesn't, tokens overlap or they don't. Rule 1 can't work that way: "does this sentence assert a new capability about the canonical primitive" is a semantic question, and Rule 1's own conformance check in `part2-standards.md` says so directly — it calls this "the kind of judgment call Part 3's checker uses Claude for rather than pure regex." So this module is two stages:

- **Stage A (mechanical, fully automated, no network):** finds each surface page's local definition of a primitive — a sentence like "A plugin is..." or "A connection is..." — anywhere on the page, plus a structural length-heuristic flag over the opening summary block.
- **Stage B (semantic, needs a model in the loop):** compares each local definition against the current canonical definition and returns one of three verdicts — CONSISTENT, DRIFT, or **DISTINCT_CONCEPT**. That third category exists specifically because of what the Part 2 template stress test found: Claude Tag's admin-scoped "connection" is a deliberately different concept from a personal "connector," and a checker with only two buckets (consistent/drift) would have flagged it as drift for the same reason a naive human read of Rule 1 would have — it doesn't match canonical, because it isn't describing canonical in the first place.

**Why Stage B is a real API integration, not a mock.** `call_model()` in the script makes an actual call to `api.anthropic.com` with the literal comparison prompt, and would run unattended with `ANTHROPIC_API_KEY` set. This build environment has network access to that host but no key configured, so Stage B could not run automatically here — the script detects that, writes every extracted candidate and its exact prompt to `output/semantic_drift_candidates.json`, and stops rather than faking a result. `output/semantic_drift_findings.md` has this run's actual Stage B verdicts, produced by applying the same prompt by hand, labeled as exactly that.

**What it found, run against the 9 surface pages:** 8 definitional candidates extracted (4 pages had no local definition to check at all, and correctly produced no verdict rather than a forced one). The headline result is Claude Tag's "connection" sentence correctly coming back DISTINCT_CONCEPT rather than DRIFT — the specific case this module exists to get right. But the same page's "A plugin is a packaged set of skills" sentence, one section later, came back genuine DRIFT (canonical plugins bundle connectors and slash commands and sub-agents too, not just skills) — a real, previously-undocumented instance of Rule 1's pattern. And the Government surface's plugins page produced the most concrete new finding: it defines a plugin as including "hooks," a component that appears nowhere on the canonical `plugins/overview.md` page (confirmed by grep across the whole file, not just the summary) — the same drift pattern Part 1's finding #5 already caught in component *tables*, showing up independently in defining *prose*.

**One candidate exposed a real gap in Stage B's own design, and it's been fixed.** The Government skills page's "A skill is a folder named after the skill, holding a SKILL.md file" scored CONSISTENT under Rule 1 on its own terms — correctly — but that sentence opens a 25-sentence section that's actually a full skill-authoring/build walkthrough duplicating `/docs/skills/how-to`, a Rule 5(b) violation. The first version of Stage B's prompt only ever saw the isolated sentence, so it couldn't see that; catching it took a human rereading the whole page afterward. Stage A now walks each page section-by-section and hands Stage B the enclosing heading, that section's length, and the full surrounding paragraph, and the prompt explicitly asks it to flag a Rule 5 concern from that context even when it doesn't change the Rule 1 verdict. Rerunning against all 8 candidates with the new context produced the identical Rule 1 verdicts on every one — nothing flipped — but this one now surfaces its Rule 5 problem in the same pass instead of needing a second human read. Full verdicts, rationale, the before/after on this fix, and three remaining disclosed checker limitations are in `output/semantic_drift_findings.md`.

## Files

- `checker/build_page_index.py` — builds `data/known_pages.json` from `sitemap-urls.txt` + `llms-txt-raw.txt`.
- `checker/link_checker.py` — Rule 3 checker; run this for link validity.
- `checker/semantic_drift_checker.py` — Rule 1 checker; run this for definition drift. See "Second module," above.
- `data/verified_overrides.json` — hand-verified live status for the 5 pages the two indexes disagree on, including the `models` false-404 incident described above.
- `scrape/` — 50 verbatim page snapshots (WebFetch, literal-content prompts; see the environment-constraint note above).
- `output/findings.json` — structured output of the last `link_checker.py` run.
- `output/run_log.md` — hand-annotated read-through of that run's actual findings, including which ANCHOR_MISMATCH flags look like real problems vs. checker artifacts.
- `output/semantic_drift_candidates.json` — Stage A output of `semantic_drift_checker.py`: extracted local definitions and their exact Stage B prompts.
- `output/semantic_drift_findings.md` — Stage B verdicts for this run, and how they were produced.
