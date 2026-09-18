# Part 2 — Standards: Style Guide Excerpt & Content-Type Template

**Scope:** This templates the Tier 3 "Use in [Surface]" pattern from Part 1. It fits surfaces organized by primitive (Cowork, Gov, M365, Desktop-3P) but intentionally excludes task-organized surfaces like Claude Tag, which would need its own (organized around scope and configuration layer.) 

---

## Style guide excerpt: How a surface page may reference a primitive

**Rule 1 — A local definition may exist for context, but must not drift from canonical.**
Surface pages may summarize a primitive for context (1-2 sentences), but must not introduce substantive claims (new capabilities, components, constraints) absent from the canonical Tier 1 definition. 

Grounding the claim in the surface itself doesn't count as drift. E.g. "A plugin is a package that extends what Claude can do in Cowork" is a faithful paraphrase of the canonical "Plugins are reusable capability packages that extend Claude with custom functionality" — it adds *where*, not *what*. 

*Exception*: Distinct, domain-specific concepts that share terminology (e.g., Claude Tag's admin-scoped "connection") are exempt - see Stage B of the semantic checker prototype. 

**Rule 2 — Component lists must match the canonical exactly.**
Any page that lists what a primitive *contains* (e.g., "a plugin can contain X, Y, Z") must reproduce the canonical page's list exactly — same items, same order — or omit the list and link instead.

*Note*: This is scoped narrowly on purpose; it targets lists of what a primitive is *composed of* (skills, connectors, agents, hooks). A surface-specific classification of where instances of a primitive *come from* (e.g. Claude Science's Featured/Local/Directory connector categories) is similar, but not within scope.

**Rule 3 — Internal links must resolve, and anchor text must match the destination's real title.**
Links must point to a confirmed-live path, validated against both indexes and a direct fetch. Anchor text must accurately reflect the destination page's real title or specific section heading. 

**Rule 4 — Risk-bearing instructions link to trust guidance before the first action.**
Any page instructing a reader how to install, add, or enable a Skill, Plugin, or Connector must link to that primitive's verification/trust-model page *before* the first imperative step ("Select...", "Click...", "Install...").

**Rule 5 — A surface page's content is limited to four things.**
"Use in [Surface]" pages should only contain: a canonical-consistent summary, provisioning sources, install steps, and surface-specific limits/admin controls. Independent build/authoring instructions and trust-tier explanations are not in scope.

---

## Content-type template: "Use in [Surface]" page

This is the template Rule 5 is built into — fill in `{{Primitive}}` (Skill/Plugin/Connector) and `{{Surface}}` (Cowork/Claude for Government/etc.) and the structure itself prevents most of the findings from recurring, rather than relying on someone remembering the rules.

```markdown
---
title: "{{Primitive}} in {{Surface}}"
description: "One sentence: what's different about {{primitive}} on {{surface}}. Not what a {{primitive}} is."
---

<!--
Remove this comment block before publishing.

TEMPLATE: "Use in [Surface]" page (Tier 3).
Applies to any page documenting how Skills, Plugins, or Connectors work on a
specific product surface (Cowork, Claude for Government, Claude for M365,
Claude Desktop on 3P, Claude Science, Claude Tag).

REQUIRED: all four sections below, in order.
The opening summary (below) may briefly restate what {{primitive}} is, for
readers and LLMs encountering this page in isolation, and may ground it in
{{Surface}} by name ("a plugin is a package that extends what Claude can do
in Cowork"). It must not add a new capability, component, or constraint the
canonical page doesn't have. If in doubt, keep it to one sentence and let the
link do the rest.

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
     /docs/{{primitive}}/verification must already have appeared. -->

## {{Surface}}-specific limits and admin controls

<!-- What's actually different here: file-type restrictions, packaging
     rules, org-managed vs. self-managed, availability caveats.
     This is usually the only section with genuinely non-duplicated content. -->

## Related

<!-- Must include a link to /docs/{{primitive}}/overview (Tier 1) and
     /docs/{{primitive}}/build (Tier 2). May include sibling Tier-3 pages
     for the other two primitives on this same surface. -->
```
---
