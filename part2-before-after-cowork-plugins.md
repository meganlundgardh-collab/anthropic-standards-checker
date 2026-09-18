# Part 2 — Before/After: `cowork/guide/plugins.md`

Applying the style guide rules and the "Use in [Surface]" template from `part2-standards.md` to a real page. Chosen because it violates three of the five rules at once (#2, #3, #5) and sits squarely in the Tier 3 layer the template targets.

---

## Before (current live content)

```markdown
# Install plugins

> Add packaged skills, connectors, and agents to Cowork from the plugin marketplace or a file.

A plugin is a package that extends what Claude can do in Cowork. Installing one can add skills, MCP connectors, subagents, slash commands, or hooks in a single step. Plugins come from the marketplace, from your organization, or from a file you upload.

Plugins are available in Cowork and Code. They aren't used in Chat.

## What a plugin can contain

A plugin's manifest declares any combination of the following.

| Component  | What it adds                                               |
| ---------- | ------------------------------------------------------------ |
| Skills     | Reusable instructions that teach Claude a workflow         |
| Connectors | MCP servers that give Claude access to an external service |
| Agents     | Specialized subagents Claude can delegate to               |
| Hooks      | Scripts that run at defined points in a session             |

After installing, open the plugin to see what it provides. Skills and agents appear as tabs; connectors and hooks have their own pages.

## Install a plugin

Open **Customize** in the sidebar, then **Plugins**.

<Steps>
  <Step title="Browse the marketplace">
    Select **Browse plugins** to see available plugins. The default marketplace
    is Anthropic's official catalog; you can add other marketplaces by URL.
  </Step>

  <Step title="Install">
    Select a plugin and click **Install**. If the plugin includes a connector
    that needs authentication, you're prompted to sign in.
  </Step>

  <Step title="Review components">
    Open the installed plugin to see its skills, connectors, agents, and hooks.
    Enable or disable individual components as needed.
  </Step>
</Steps>

To install from a file instead, select the upload option on the Plugins page and select the plugin package.

## Use a Git repository as a marketplace

A Git repository that contains plugin packages can serve as a marketplace. This is the typical way teams distribute their own plugins without publishing to the public catalog. Repositories on GitHub (including GitHub Enterprise) are supported; public repositories on GitLab and Bitbucket also work.

<Steps>
  <Step title="Add the repository">
    On the Plugins page, select **Add marketplace** and enter the repository's
    URL. Cowork accepts the standard `https://github.com/owner/repo` form and
    the `owner/repo` shorthand for GitHub.
  </Step>

  <Step title="Install plugins from it">
    Plugins defined in the repository appear alongside plugins from other
    marketplaces. Install them the same way.
  </Step>
</Steps>

Click **Update** on a marketplace to pull the latest plugins from its repository.

For administrator-managed marketplaces, see [MCP, plugins, skills, and hooks](/docs/cowork/3p/extensions) in the deployment guide.

## Limits

The following are the default limits for plugin packages and marketplaces.

| Limit                              | Value  |
| ----------------------------------- | ------ |
| Plugin package size (uncompressed) | 200 MB |
| Files per plugin package           | 5,000  |
| Marketplace repository archive     | 512 MB |
| Plugins per marketplace            | 500    |
| Marketplaces you can add           | 25     |

The in-app skill viewer previews individual files up to 1 MB. Larger files appear in the file list as "too large to preview" but are still available to Claude at runtime.

## Plugins managed by your organization

On Team and Enterprise plans, administrators can require certain plugins for everyone in the organization. Required plugins install automatically and show **This plugin is required by your organization**; you can't remove them.

For how administrators provision plugins, see [MCP, plugins, skills, and hooks](/docs/cowork/3p/extensions) in the deployment guide.

## Update and remove plugins

Cowork checks for plugin updates from the marketplace they came from. If you've edited a plugin's files locally, Cowork detects the change and warns you before an update would overwrite it.

To remove a plugin you installed, open it under **Customize → Plugins** and click **Uninstall**. Organization-managed plugins can only be removed by an administrator.

## Related

* [Plugins overview](/docs/plugins/overview) for how plugins work across Claude products
* [Submit a plugin](/docs/plugins/submit) to publish your own to the marketplace
* [MCP, plugins, skills, and hooks](/docs/cowork/3p/extensions) for administrator provisioning
```

---

## After (rewritten to spec)

```markdown
---
title: "Plugins in Cowork"
description: "Install, manage, and remove plugins in Cowork from the marketplace, your organization, or a file."
---

Plugins are reusable capability packages that extend Claude with custom
functionality — in Cowork, installing one adds its skills, connectors,
slash commands, sub-agents, and hooks in a single step. See
[Plugins overview](/docs/plugins/overview) for what a plugin can contain,
and [Plugin verification](/docs/plugins/verification) for how to evaluate
one before you install it.

Plugins are available in Cowork and Claude Code. They aren't used in Chat.

## Where plugins come from in Cowork

Plugins reach Cowork three ways: the plugin marketplace (Anthropic's
official catalog, browsable in-app), a Git repository your team hosts as
its own marketplace, or a plugin file you upload directly. On Team and
Enterprise plans, administrators can also require specific plugins for
everyone in the organization — see
[Plugins managed by your organization](#plugins-managed-by-your-organization)
below.

After installing, open the plugin to see what it provides: skills and
sub-agents appear as tabs, and connectors and hooks each have their own
page.

## Install or enable a plugin in Cowork

Before installing anything outside your organization's required set, see
[Plugin verification](/docs/plugins/verification) — plugins can run local
scripts and hooks, not just call tools, so it's worth knowing what you're
granting before you click Install.

Open **Customize** in the sidebar, then **Plugins**.

<Steps>
  <Step title="Browse the marketplace">
    Select **Browse plugins** to see available plugins. The default marketplace
    is Anthropic's official catalog; you can add other marketplaces by URL.
  </Step>

  <Step title="Install">
    Select a plugin and click **Install**. If the plugin includes a connector
    that needs authentication, you're prompted to sign in.
  </Step>

  <Step title="Review components">
    Open the installed plugin to see its skills, connectors, agents, and hooks.
    Enable or disable individual components as needed.
  </Step>
</Steps>

To install from a file instead, select the upload option on the Plugins page
and select the plugin package.

### Use a Git repository as a marketplace

A Git repository that contains plugin packages can serve as a marketplace.
This is the typical way teams distribute their own plugins without
publishing to the public catalog. Repositories on GitHub (including GitHub
Enterprise) are supported; public repositories on GitLab and Bitbucket also
work.

<Warning>
  A Git-repository marketplace doesn't go through the same review as the
  public catalog. Only add one you or your organization controls, or one
  from a source you trust as much as you'd trust running its code directly
  — see [Plugin verification](/docs/plugins/verification).
</Warning>

<Steps>
  <Step title="Add the repository">
    On the Plugins page, select **Add marketplace** and enter the repository's
    URL. Cowork accepts the standard `https://github.com/owner/repo` form and
    the `owner/repo` shorthand for GitHub.
  </Step>

  <Step title="Install plugins from it">
    Plugins defined in the repository appear alongside plugins from other
    marketplaces. Install them the same way.
  </Step>
</Steps>

Click **Update** on a marketplace to pull the latest plugins from its
repository.

### Update and remove a plugin

Cowork checks for plugin updates from the marketplace they came from. If
you've edited a plugin's files locally, Cowork detects the change and warns
you before an update would overwrite it.

To remove a plugin you installed, open it under **Customize → Plugins** and
click **Uninstall**. Organization-managed plugins can only be removed by an
administrator.

## Cowork-specific limits and admin controls

The following are the default limits for plugin packages and marketplaces.

| Limit                              | Value  |
| ----------------------------------- | ------ |
| Plugin package size (uncompressed) | 200 MB |
| Files per plugin package           | 5,000  |
| Marketplace repository archive     | 512 MB |
| Plugins per marketplace            | 500    |
| Marketplaces you can add           | 25     |

The in-app skill viewer previews individual files up to 1 MB. Larger files
appear in the file list as "too large to preview" but are still available
to Claude at runtime.

### Plugins managed by your organization

On Team and Enterprise plans, administrators can require certain plugins
for everyone in the organization. Required plugins install automatically
and show **This plugin is required by your organization**; you can't
remove them.

Cowork-specific admin provisioning documentation isn't published yet —
org-wide plugin sharing and management is still rolling out. For the
general mechanics of distributing a plugin (direct install, your own
marketplace, or the public directory), see
[Submitting your plugin](/docs/plugins/submit).

## Related

* [Plugins overview](/docs/plugins/overview) — what a plugin is and what it can contain
* [Plugin verification](/docs/plugins/verification) — how to evaluate a plugin before installing it
* [Submitting your plugin](/docs/plugins/submit) — how plugins get distributed, including your own marketplace
```

---

## What changed, and why

**Removed the "What a plugin can contain" table and the opening sentence's ad hoc component list** (Rules 2 and 5). The table's four items — Skills, Connectors, Agents, Hooks — was a fourth independent version of the list findings #5 already caught drifting across three other pages, and it wasn't even internally consistent with this same page's opening sentence, which said "skills, MCP connectors, subagents, slash commands, or hooks" (five items, different naming). Replaced both with a link to the canonical overview. The one genuinely useful, non-duplicated fact buried in that section — where each component shows up in the Cowork UI (tabs vs. own pages) — survived, moved into "Where plugins come from in Cowork," reworded so it's about UI location, not a redefinition of what the components are.

**Added verification links in two places** (Rule 4, finding #1). One general link near the top and, more importantly, a specific `<Warning>` callout immediately before "Use a Git repository as a marketplace" — that section is the single riskiest install path identified in the audit (an arbitrary, unreviewed Git repo, documented with zero caution language today), so it gets more than the baseline link.

*Open dependency, flagged rather than hidden:* both of these links point to `/docs/plugins/verification`, which doesn't exist yet — it's the Part 1 P0 recommendation, not something already shipped. This rewrite assumes that page ships first; a real PR applying this rewrite today would need to land after or alongside it, not before, or the links would be as broken as the one this rewrite is fixing.

**Fixed the cross-reference from finding #2 — all three instances — by disclosing a gap rather than picking a different wrong answer.** The original page links to `/docs/cowork/3p/extensions` — the Claude Desktop on third-party-providers admin guide, unrelated to Cowork's own org plugin management — three separate times, with identical anchor text each time ("MCP, plugins, skills, and hooks"): once at the end of "Use a Git repository as a marketplace," once under "Plugins managed by your organization," and once in the "Related" list. Three identical wrong links, never varied or corrected across three different contexts, is itself evidence nobody clicked through even once.

There isn't currently a page that documents Cowork-specific admin plugin provisioning in detail (`plugins/overview.md` itself says org-wide sharing and management for Cowork is "coming in the weeks ahead"). Rather than redirect all three instances to a different existing-but-still-wrong page, the rewrite treats them differently depending on what each was actually doing: the "Plugins managed by your organization" instance says plainly that this documentation doesn't exist yet and points to the one page that's actually relevant today (`plugins/submit.md`, for general distribution mechanics); the "Related" list instance gets that same replacement link, for consistency; and the "Use a Git repository as a marketplace" instance is dropped outright, since it was pure duplication — it pointed to the same (wrong) destination as the "Plugins managed by your organization" instance two sections later and added nothing the other two didn't already say. This is the single most consequential edit in this rewrite: the honest fix for a wrong link isn't always "point it somewhere else," and when the same wrong link is repeated, the honest fix isn't always to repeat the correction three times either — sometimes it's admitting the right destination doesn't exist, and cutting the redundant copies rather than dutifully re-fixing each one.

**Renamed the title** from "Install plugins" to "Plugins in Cowork," to match the content-type template's naming convention. Flagging this as a disclosed, reversible choice rather than a silent one — the original title's task-focus (it's fundamentally an install-flow page) is a reasonable alternative, and nothing about the URL/path needs to change either way. Open question for review, not a settled call.

**Restructured headings into the template's four required sections** (Where plugins come from / Install or enable / Cowork-specific limits and admin controls / Related), nesting the original page's finer-grained sections (Git-marketplace, update/remove, org-managed plugins) as subheadings within the appropriate parent. No content was cut for structural reasons beyond the duplicate cross-reference noted above — everything else that survived the Rule 2/5 removal was re-homed, not rewritten from scratch.

**Left alone, deliberately:** the Limits table. It's genuinely Cowork-specific, numeric, non-duplicated content — exactly what Rule 5 says a surface page is for, and a good contrast case against the component table it sits next to in the original, which looked similar (a table) but was actually the problem.
