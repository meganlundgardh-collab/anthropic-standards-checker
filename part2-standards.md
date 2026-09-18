# Part 2 — Standards: Style Guide Excerpt + Content-Type Template

Scope call: this templates the **Tier 3 "Use in [Surface]" pattern** from Part 1's proposed IA — Cowork, Government, M365, Desktop-3P, Claude Science, Claude Tag all have their own "how does Skill/Plugin/Connector X work here" pages, and that's exactly where findings #2, #5, and #6 live. A style guide that only covered Tier 1 (the canonical definitions) wouldn't have prevented any of the actual problems we found — the problems are all in how the surface pages relate to the canonical ones.

*Scope correction, added after stress-testing against real surfaces (see the dated note at the end of this document): not all six surfaces named above actually have the single-primitive Tier 3 page shape this template assumes. It fits Cowork, Government, M365, and Desktop-3P. It does not fit Claude Tag, whose admin content is organized by task and scope rather than by primitive. Claude Science hasn't been fully checked either way. Treat "Cowork, Government, M365, Desktop-3P" as the confirmed scope of this template going in, not all six.*

---

## Style guide excerpt: how a surface page may reference a primitive

Five rules. Each one exists because of a specific Part 1 finding, and each one is written so a reviewer and a script would reach the same verdict on the same page.

**Rule 1 — A local definition may exist for context, but must not drift from canonical.**
A page documenting how a primitive works on a specific surface may restate a short (1–2 sentence) summary of what that primitive is, for the reader's benefit and for an LLM reading the page in isolation — that's not banned, and cutting it entirely would make pages worse for exactly the audience this estate's `llms.txt` is built for. What's not allowed is a local restatement that adds a new *substantive* claim — a component, capability, constraint, or mechanism — that the canonical Tier 1 definition doesn't have, or that's long/detailed enough to function as a substitute for it rather than a summary of it. The canonical link is required either way.

Grounding the same claim in the surface itself is fine and doesn't count as drift. "A plugin is a package that extends what Claude can do in Cowork" is a faithful paraphrase of the canonical "Plugins are reusable capability packages that extend Claude with custom functionality" — it adds *where*, not *what*, and that's exactly the kind of context that helps a reader (or an LLM reading the page in isolation). It would fail if it went on to claim something the canonical page doesn't say, e.g. "...including running background hooks automatically" — that's a capability claim, not a location, and it's the kind of addition that caused finding #5 in the first place.

A related edge case, surfaced by stress-testing (see the dated note below): a surface can also define something *genuinely distinct* that happens to share a name or a near-synonym with a canonical primitive — Claude Tag's admin-scoped "connection," for instance, is deliberately not the same thing as a personal "connector," and the page that defines it says so explicitly. That's not drift either, and this rule doesn't require it to link to `/docs/connectors/overview` as if it were one. The test stays the same either way: does the page assert a new claim *about the canonical primitive*, or is it describing something else that happens to be adjacent? Only the former is a violation.

*Conformance check:* extract any definitional or component claim from the surface page; compare it against the canonical page's current definition. Flag if the local text introduces a new component, capability, constraint, or mechanism claim absent from canonical, contradicts it, or runs long enough to be doing the canonical page's job (a length heuristic — more than ~2 sentences of definitional content before the first surface-specific heading — is a reasonable proxy, refined by human review). Surface-name grounding ("in Cowork," "for Claude for Government") is not itself a new claim and should not trigger a flag on its own — the check is for new *capability* claims, not for the surface's own name appearing in the sentence. This is a harder check than a pure structural scan; it needs semantic comparison, which is exactly the kind of judgment call Part 3's checker uses Claude for rather than pure regex.
*Origin:* finding #6. The problem there wasn't that Government's skills page had local text — it's that the local text could silently diverge from the canonical source (`skills/how-to.md`) with nothing catching it. The fix is a consistency check, not a ban on local content.
*Validated against real pages (2026-09-17):* Part 3 built and ran a checker for this exact rule — see the dated note at the end of this document for what it found, including a case that changed how the conformance check above should actually be implemented.

**Rule 2 — Component lists must match the canonical enumeration exactly, or not exist.**
Any page that lists what a primitive contains (e.g., "a plugin can contain X, Y, Z") must reproduce the canonical page's list exactly — same items, same order — or omit the list and link instead.
*Conformance check:* extract any list following a "contains/bundles/adds" pattern for a defined primitive term; diff against the canonical list. Any addition, omission, or reordering fails. This is scoped narrowly on purpose — it targets lists of what a primitive *is composed of* (skills, connectors, agents, hooks). A surface-specific classification of where instances of a primitive *come from* — Claude Science's Featured / Local / Directory connector categories, for example — is a different kind of list and isn't what this rule is checking, even though a careless reading could conflate the two. See the dated note below for the case that surfaced this distinction.
*Origin:* finding #5 — four pages, four different plugin component lists, none of them coordinated.

**Rule 3 — Internal links must resolve, and anchor text must match the destination's real title.**
A link must point to a path confirmed live — checked against `llms.txt` and/or `sitemap.xml`, and by direct fetch when the two disagree, since finding #3 shows neither index alone is fully reliable on its own — and its anchor text must be the destination page's actual title or a faithful paraphrase, not a guess at what the linker assumed lived there.
*Conformance check:* crawl internal links; verify each resolves; fetch each destination's H1/frontmatter title; flag any link whose anchor text doesn't correspond to that title. This is the literal check that would have caught the Cowork → Desktop-3P mismatch in finding #2 before it shipped — and, applied as written, it would have caught all three instances of that mismatch on the same page, not just the first one found.
*Origin:* finding #2 and finding #3.

**Rule 4 — Risk-bearing instructions link to trust guidance before the first action.**
Any page instructing a reader how to install, add, or enable a Skill, Plugin, or Connector must link to that primitive's verification/trust-model page before the first imperative step ("Select...", "Click...", "Install...").
*Conformance check:* locate the first imperative instruction in the page body; confirm a link to `/docs/<primitive>/verification` appears at or before that point.
*Origin:* finding #1 — plugin installs currently carry no risk language at the point of installation, unlike connectors.

**Rule 5 — A surface page's content is limited to four things.**
A "Use in [Surface]" page may only contain: a brief, canonical-consistent summary plus a link to the full definition (Rule 1), where the primitive is provisioned on this surface, the actual install/enable steps for this surface, and surface-specific limits or admin controls. Nothing else — no independently authored component lists (Rule 2 covers the one exception: an exact match), no authoring/build instructions, no independent trust-tier explanations.
*Conformance check:* this is the one rule that's a checklist for a human reviewer more than a script (though Rules 1–4 above catch its most common violations mechanically) — see the template below, which encodes it directly as document structure.
*Validated against real pages (2026-09-17):* Part 3's Rule 1 checker produced a real, live instance of a Rule 5(b) violation while checking a different rule entirely — see the dated note at the end of this document. Worth noting as mild evidence for the claim two lines above: this rule really is harder to catch mechanically than the other four, since it took a human rereading a whole page (twice) to surface, not a script.

---

## Content-type template: "Use in [Surface]" page

This is the template Rule 5 is built into — fill in `{{Primitive}}` (Skill/Plugin/Connector) and `{{Surface}}` (Cowork/Claude for Government/etc.) and the structure itself prevents most of the findings from recurring, rather than relying on someone remembering the rules.

```markdown
---
title: "{{Primitive}} in {{Surface}}"
description: "One sentence: what's different about {{primitive}} on {{surface}}. Not what a {{primitive}} is."
---

<!--
TEMPLATE: "Use in [Surface]" page (Tier 3).
Applies to any page documenting how Skills, Plugins, or Connectors work on a
specific product surface (Cowork, Claude for Government, Claude for M365,
Claude Desktop on 3P, Claude Science, Claude Tag).

REQUIRED: all four sections below, in order.
The opening summary (below) may briefly restate what {{primitive}} is, for
readers and LLMs encountering this page in isolation, and may ground it in
{{Surface}} by name ("a plugin is a package that extends what Claude can do
in Cowork") — that's context, not drift. It must not add a new capability,
component, or constraint the canonical page doesn't have (style guide
Rule 1). If in doubt, keep it to one sentence and let the link do the rest.
FORBIDDEN in any section:
  (a) an independently authored list of what the primitive is composed of
      that isn't an exact match to /docs/{{primitive}}/overview (Rule 2)
  (b) restating authoring/build rules already covered by /docs/{{primitive}}/build
  (c) defining a trust/verification tier system
      -> link to /docs/{{primitive}}/verification instead
Remove this comment block before publishing.
-->

{{One or two sentences on what {{primitive}} is, consistent with the
canonical definition, optionally grounded in {{Surface}} by name — omit if
you have nothing to add beyond the link.}}
See [{{Primitive}} overview](/docs/{{primitive}}/overview) for the full
definition and what a {{primitive}} can contain, and
[{{Primitive}} verification](/docs/{{primitive}}/verification) for how to
evaluate one before you install it.

## Where {{primitive}}s come from in {{Surface}}

<!-- Surface-specific only: who provisions them here (admin vs. self-serve),
     what delivery mechanisms exist on this surface specifically. -->

## Install or enable a {{primitive}} in {{Surface}}

<!-- The actual click-path for THIS surface. Before the first imperative
     step ("Select...", "Click...", "Install..."), a link to
     /docs/{{primitive}}/verification must already have appeared, per
     style guide Rule 4. -->

## {{Surface}}-specific limits and admin controls

<!-- What's actually different here: file-type restrictions, packaging
     rules, org-managed vs. self-managed, availability caveats.
     This is usually the only section with genuinely non-duplicated content. -->

## Related

<!-- Must include a link to /docs/{{primitive}}/overview (Tier 1) and
     /docs/{{primitive}}/build (Tier 2). May include sibling Tier-3 pages
     for the other two primitives on this same surface. -->
```

The template can't fully enforce Rules 1 and 2 by itself, since both depend on whether content *matches* something elsewhere rather than whether a section exists — that's the checker's job in Part 3. What the template does enforce by construction is section order and presence (Rule 5) and the placement of the verification link ahead of the first instruction (Rule 4).

**Scope of this template**, made explicit after stress-testing it against two surfaces it hadn't yet been checked on (full findings in the dated note below): this template is for a *single-primitive, per-surface* page — the shape Cowork, Government, M365, and Desktop-3P actually use, where a surface has a page (or a small few) dedicated to "how Skills work here," "how Plugins work here," and "how Connectors work here," separately. It is not a fit for a surface whose admin content is organized by *task or scope* instead of by *primitive*. Claude Tag is the clearest counter-example found so far and is out of scope for this template as written; it would need its own content-type pattern, likely organized around scope and configuration layer rather than primitive.

---

*Next: apply this to a real page — before/after rewrite of `cowork/guide/plugins.md`, which currently violates Rules 2, 3, and 5 (its component table is an independently authored list that doesn't match canonical, and it's long enough to be doing the canonical page's job rather than summarizing it).*

---

## Red-team consistency check (2026-09-17)

Checked this document against the corrected Part 1 memo (see its own red-team log: finding #2 was corrected from "the link appears twice" to "the link appears three times," and finding #1 gained supporting evidence from the M365 precedent). Findings:

- **Rule 3 and Rule 4's origin/conformance references to findings #1 and #2** don't depend on the instance count and needed no change — Rule 3's conformance check description has been sharpened slightly (above) to note it catches all instances of a repeated bad link, not just the first, since that's now a more precise description of what actually happened on the page this rule was written against.
- **Rule 1's worked example** (the "extends what Claude can do in Cowork" sentence, added in response to Megan's second review comment) doesn't reference finding #2 or the instance count at all — unaffected by the correction.
- **The applied example** (`part2-before-after-cowork-plugins.md`) was the one place the "twice" error had actually propagated — its "Before" transcript was missing the third instance of the link and its "What changed, and why" section described fixing one instance rather than three. Both are now corrected there; see that document's "What changed, and why" section for the full three-instance breakdown.
- No other cross-references in this document needed correction.

## Template stress test against Claude Tag and Claude Science (2026-09-17)

At Megan's request, tested whether the four-section "Use in [Surface]" template holds up against two surfaces not yet checked against it: Claude Tag (Claude in Slack) and Claude Science. Fetched Claude Tag's `admins/customize` and `admins/add-connections` pages, and Claude Science's `overview` and `enable-claude-science` pages, directly from the live site.

**Result: the template does not fit Claude Tag, for two separate reasons — one structural, one semantic.**

Structural: Claude Tag has no per-primitive Tier 3 page at all. Its real content shape is organized by admin task and scope, not by primitive: "Customize Claude Tag" (`admins/customize`) is a single reference page covering four peer configuration layers — Connections, Plugins and skills, Custom instructions, Channel memory — as one table, with plugins folded in as one row alongside two concepts (custom instructions, channel memory) that aren't primitives this audit covers at all. "Attach plugins" is a subsection of the *connections* page (`admins/add-connections`), not its own page. There's no standalone "Skills in Claude Tag" page — skills only appear as "what a plugin is packaged from." Forcing this content into four required per-primitive sections would mean breaking apart a page that's arguably better as a unified reference (the four layers genuinely interact — you attach a plugin to the same bundle that carries its matching connection) into three or more awkward, narrower splinters. That's a worse outcome than leaving it alone.

Semantic: Claude Tag explicitly and deliberately distinguishes a **connection** (an admin-managed, channel/workspace-scoped credential inside an Access bundle) from a **connector** (a personal, claude.ai-scoped primitive) — the `add-connections` page has its own section, "Connections vs claude.ai connectors," warning readers not to conflate them: *"The connection gallery lists credential types the agent can hold, not the connectors your organization or its members have set up on claude.ai... a connector on someone's personal claude.ai account doesn't appear here."* Rule 1, applied literally without the edge-case language now added above, would require this page to link to `/docs/connectors/overview` as the canonical definition of what a "connection" is — but that would actively mislead a reader, since a connection isn't a restatement of the canonical connector concept, it's a related-but-distinct one. Similarly, Claude Science's connector-enablement page (`enable-claude-science`) introduces its own three-way sub-taxonomy — Featured / Local / Directory connectors — that a careless application of Rule 2 ("component lists must match canonical exactly") could misflag as drift, even though it's a legitimate surface-specific classification of connector *sources*, not a restatement of what a connector *contains*.

**What this changed:** added an explicit scope boundary to the template and the style-guide intro (above) rather than trying to stretch the template to fit every surface. Rule 1 and Rule 2 each got a short clarifying paragraph naming the edge case, rather than a rewrite — the rules' underlying tests ("a new claim *about the canonical primitive*" for Rule 1; "what a primitive is composed of" for Rule 2) already excluded these cases in spirit, but a reviewer applying them without the context in this note could plausibly have misfired on `add-connections` or `enable-claude-science`. Naming it explicitly closes that gap without weakening either rule.

This is a real limitation, not a footnote to bury: the template covers 4 of the 6 surfaces named in finding #7's structural-imbalance count (Cowork, Government, M365, Desktop-3P) cleanly. Claude Tag needs its own content-type pattern if this work extended to it — likely organized around *scope and layer* the way `admins/customize` already is, not around primitive. Claude Science's Tier-3-shaped pages (single primitive, single surface, an install/enable flow) look closer to a fit than Claude Tag's — nothing found so far rules it out — but it hasn't been fully checked against all five rules, so it's left as "probably fits, not confirmed" rather than added to the confirmed list.

## Rule 3 origin correction (2026-09-17)

Rule 3's origin footnote used to say a link must be "live and indexed (or flagged as pending-index per the `llms.txt` gap in finding #3)." That specific carve-out no longer describes what finding #3 actually found — finding #3 was rewritten after a two-step retraction during Part 3's data prep (full saga in `part1-audit-memo.md`'s red-team log, "pass 3" entry): the real, narrower finding is that `sitemap.xml` — not `llms.txt` — is missing four real, live pages that `llms.txt` correctly lists, plus one case where a checker's own fetch produced a false negative (a page that looked dead on one check and wasn't).

The rule and its conformance check are unchanged by this — the underlying test was always "verify against a real source before trusting the raw link," not "trust `llms.txt` specifically." Only the origin footnote and the pending-index carve-out needed rewording, which is reflected in Rule 3's body text above (now: check against both indexes, and fetch directly when they disagree). Worth carrying forward into Part 3's own write-up: the same saga is also the clearest available evidence for why an automated version of this rule needs retry/second-confirmation logic before it reports a link as BROKEN — a single fetch returning an error isn't proof the target is actually dead, exactly the mistake made (and caught) twice during this document's own fact-checking.

## Rule 1 and Rule 5 validated against real Part 3 output (2026-09-17)

Part 3 built a second checker module targeting Rule 1 specifically (the link checker targets Rule 3). Run against the 9 surface pages in this audit's slice, it produced three results worth recording here, since they're evidence about whether these rules actually work, not just whether they're well-argued on paper.

**The DISTINCT_CONCEPT edge case this document added above — the Claude Tag "connection" vs. "connector" distinction — is exactly what the checker needed to get right, and it did.** Without a first-class DISTINCT_CONCEPT verdict (as opposed to a plain consistent/drift binary), an automated version of Rule 1 would have flagged `claude-tag/admins/add-connections.md`'s definition of "connection" as drift, for the same reason a literal reading of the rule without this document's edge-case language would have. Building the exception in as its own category, rather than leaving it to reviewer judgment, is what let the checker reach the same conclusion this document's own stress test reached by hand.

**Rule 1 also caught two real, previously undocumented violations, extending findings #5 and #6.** `government/desktop/plugins.md`'s opening definitional sentence — not a component table, the actual "a plugin is..." claim — asserts hooks as a plugin component, and a second instance on the same page claims hooks specifically run locally "at defined points during a session," a mechanism claim canonical `plugins/overview.md` makes nowhere at all. That's finding #5's pattern (four pages, four different plugin component lists), independently confirmed to also live in defining prose, not just tables. Separately, `government/desktop/skills.md`'s SKILL.md re-derivation — finding #6's origin case — turned out on inspection to be the opening line of a full 25-sentence authoring/build walkthrough duplicating `/docs/skills/how-to`: a clean instance of Rule 5(b), not just a borderline restatement. Full detail, including the exact sentences and rationale, is in the Part 3 repo's `output/semantic_drift_findings.md`.

**Getting the second finding right took two passes, and that's itself informative for Rule 1's own conformance check as written above.** The checker's Stage B initially judged that SKILL.md sentence in isolation — correctly, on Rule 1's own narrow terms, since the sentence itself doesn't contradict canonical — and missed the Rule 5 problem sitting one level up. Only widening what Stage B was shown (the sentence's section heading, the section's length, and its full surrounding paragraph) surfaced it directly. The practical implication for this rule's conformance check: "extract any definitional or component claim from the surface page" (as written above) should mean extracting it *with its surrounding context*, not as an isolated sentence — a checker (or a reviewer) that only ever looks at the extracted fragment will systematically miss cases where the local definition is a symptom of a bigger structural problem rather than being wrong on its own terms.
