#!/usr/bin/env python3
"""
semantic_drift_checker.py -- Part 3, second module. Implements Part 2's Rule 1:
"A local definition may exist for context, but must not drift from canonical."

This is a genuinely different kind of checker than link_checker.py (Rule 3).
Rule 3 is pure structural comparison -- a link resolves or it doesn't, anchor
tokens overlap a title or they don't. Rule 1 is not: "does this sentence
assert a new capability about the canonical primitive" is a semantic
question, and Rule 1's own conformance check says so explicitly ("this is a
harder check than a pure structural scan; it needs semantic comparison").
So this checker is two stages:

  STAGE A (mechanical, this script does it in full, no network):
    For each candidate surface page, scan the whole page (not just the
    opening summary -- see find_definition_candidates_with_context()'s
    docstring for why) for any sentence that looks like it's defining
    "skill" / "plugin" / "connector" / "connection" ("A plugin is...",
    "A connection is...", "A plugin bundles..."). For each one, also
    capture *where* it lives: the enclosing section heading, the full
    paragraph it's part of, and that section's total sentence count --
    context a first version of this script didn't collect, which caused
    a real under-call (see below). Separately, the opening block (H1 to
    first H2) gets Rule 1's own length heuristic (more than ~2 sentences
    of definitional content before the first surface-specific heading is
    a possible canonical-substitute).

  STAGE B (semantic, needs a model in the loop):
    For each Stage A candidate, compare its sentence -- plus its section
    heading and surrounding paragraph -- against the current canonical
    definition and classify:
      CONSISTENT      - faithful summary/grounding, no new claim.
      DRIFT           - asserts a capability/component/constraint the
                        canonical page doesn't have, or contradicts it.
      DISTINCT_CONCEPT - not actually describing the canonical primitive;
                        it's a different, surface-specific concept that
                        happens to share a name or near-synonym (Rule 1's
                        own worked edge case: Claude Tag's admin-scoped
                        "connection" vs. the personal "connector").
    Stage B is also asked to separately flag a Rule 5 concern (a section
    restating authoring/build content that belongs on a different page)
    when the surrounding context suggests one, even though that doesn't
    change the Rule 1 verdict on the sentence itself.

    This needs real semantic judgment, which is why it's built as an actual
    Anthropic-API call (see call_model() below) rather than another regex --
    that's the honest architecture, not a shortcut. If ANTHROPIC_API_KEY is
    not set (true in the sandbox this prototype was built in), Stage B
    cannot run unattended here; the script writes the exact prompts to
    output/semantic_drift_candidates.json and stops, so a human -- or this
    same script pointed at a real key -- can complete it. See
    output/semantic_drift_findings.md for this run's actual Stage B verdicts
    and how they were produced.

    NOTE ON HOW THIS CONTEXT-AWARE VERSION CAME ABOUT: the first version of
    this script's Stage B prompt handed the model only the isolated matched
    sentence. That version scored government/desktop/skills.md's "A skill is
    a folder named after the skill, holding a SKILL.md file" as CONSISTENT,
    correctly, on Rule 1's own narrow terms -- but missed that the sentence
    opens a full authoring/build walkthrough that's a real Rule 5(b)
    violation, which only became visible on rereading the whole page by
    hand. This version exists specifically to close that gap by giving
    Stage B the same section-level context a human reviewer would use.

USAGE
    python3 checker/semantic_drift_checker.py
"""
import json
import os
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
SCRAPE = ROOT / "scrape"
OUTPUT = ROOT / "output"
MODEL_ID = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

# The canonical definition source for each primitive. "connection" isn't a
# canonical primitive at all -- it's mapped to "connector" on purpose, since
# that's the exact near-synonym pairing Rule 1's edge-case note names. If a
# checker is going to test whether it can tell "connection" and "connector"
# apart, it has to actually be handed that comparison, not a comparison
# against itself.
CANONICAL_PAGES = {
    "plugin": SCRAPE / "plugins" / "overview.md",
    "skill": SCRAPE / "skills" / "overview.md",
    "connector": SCRAPE / "connectors" / "overview.md",
    "connection": SCRAPE / "connectors" / "overview.md",  # deliberate cross-mapping, see above
}

# The 9 surface pages from the Part 1 slice that have their own prose (not
# just a component table). scope_status mirrors part2-standards.md's own
# confirmed template scope, written down there *before* this checker
# existed: Cowork/Government/M365/Desktop-3P are confirmed-fit for the Tier
# 3 template; Claude Tag is explicitly out of scope (and is exactly the
# DISTINCT_CONCEPT adversarial case); Claude Science is unconfirmed.
SURFACE_PAGES = [
    ("cowork/guide/plugins.md", "Cowork", "confirmed-fit"),
    ("government/desktop/plugins.md", "Government", "confirmed-fit"),
    ("government/desktop/skills.md", "Government", "confirmed-fit"),
    ("office-agents/connectors-and-skills.md", "M365 (Office agents)", "confirmed-fit"),
    ("claude-tag/admins/add-connections.md", "Claude Tag", "out-of-scope (adversarial test case)"),
    ("claude-tag/admins/customize.md", "Claude Tag", "out-of-scope (adversarial test case)"),
    ("claude-tag/overview.md", "Claude Tag", "out-of-scope (adversarial test case)"),
    ("claude-science/overview.md", "Claude Science", "unconfirmed"),
    ("claude-science/enable-claude-science.md", "Claude Science", "unconfirmed"),
]

# Matches "A plugin is...", "A connection is...", "A plugin bundles...",
# case-insensitively, singular or plural ("skills are..."). Deliberately a
# simple English pattern, not a markdown/AST parser -- it will miss a
# definition phrased unusually, and that's a disclosed limitation (see the
# README), not a bug to quietly patch away.
#
# Second alternative, added after a hand sweep of all 9 surface pages found
# a real miss: claude-tag/admins/customize.md has an H3 section titled
# "### Channel connections are separate from personal connectors" -- a
# genuine, on-topic distinction between Claude Tag's "connection" and the
# canonical "connector" that the article-only pattern above can't see,
# because "Channel" sits where "a"/"an" would need to be. Deliberately
# narrow, not just "any word before the primitive": anchored to the start
# of the sentence (`^`, checked per-sentence since DEFINITION_RE is run on
# one split_sentences() output at a time) and restricted to the plural
# "are" form only. Both restrictions matter -- a hand sweep of near-miss
# phrases on these same 9 pages found several that look similar but are
# clearly NOT definitions ("Each connection is listed in the bundle...",
# "This plugin is required by your organization..."), and both happen to
# be singular "is" with a determiner ("Each", "This") rather than a
# category-level plural claim; requiring "are" and forbidding a mid-sentence
# match keeps those out without a denylist of determiners to maintain.
DEFINITION_RE = re.compile(
    r"(?:\b[Aa]n?\s+(plugin|skill|connector|connection)s?\s+(?:is|are|bundles?|adds?|extends?)\b)"
    r"|(?:^[A-Z][a-z]+\s+(plugin|skill|connector|connection)s\s+are\b)"
)


def strip_docs_index_box(text: str) -> str:
    """Every scraped page opens with a '> ## Documentation Index' blockquote
    that's a scraping/tooling artifact, not page content. Drop it."""
    lines = text.splitlines()
    out, in_box = [], False
    for line in lines:
        if line.strip().startswith("> ## Documentation Index"):
            in_box = True
            continue
        if in_box and line.strip().startswith(">"):
            continue
        in_box = False
        out.append(line)
    return "\n".join(out)


def extract_opening_block(text: str) -> str:
    """H1 to first H2, exclusive of both headings. Used ONLY for Rule 1's
    length heuristic ("more than ~2 sentences of definitional content
    before the first surface-specific heading") -- that heuristic is
    specifically about the opening summary, per the rule's own wording."""
    lines = strip_docs_index_box(text).splitlines()
    start, end = None, len(lines)
    for i, line in enumerate(lines):
        if start is None and line.startswith("# "):
            start = i + 1
        elif start is not None and line.startswith("## "):
            end = i
            break
    if start is None:
        return ""
    return "\n".join(lines[start:end])


def extract_full_body(text: str) -> str:
    """Everything after the H1, docs-index box stripped. Used for finding
    definitional sentences -- unlike the length heuristic, a definition can
    legitimately appear anywhere on the page (e.g. inside a later section
    explaining a term in more depth), not only in the opening summary. An
    earlier version of this script only scanned the opening block and, as a
    result, MISSED the single most important candidate in this whole run --
    claude-tag/admins/add-connections.md's definition of "connection" lives
    under its first H2 ("## Your first Access bundle"), not before it. Left
    here as a documented reminder of a real Stage A bug this build caught
    and fixed, not quietly corrected out of the history."""
    lines = strip_docs_index_box(text).splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith("# "):
            start = i + 1
            break
    if start is None:
        return ""
    return "\n".join(lines[start:])


def split_sentences(block: str) -> list:
    # Simple split, not linguistically exact -- good enough for the length
    # heuristic and for isolating the sentence a definition regex matched.
    #
    # Strip trailing markdown line-continuation backslashes ("...research.\"
    # at end of line, a manual <br/> used across several scraped pages --
    # e.g. claude-science/enable-claude-science.md) BEFORE collapsing
    # whitespace, not after. Left in place, a backslash like that survives
    # whitespace collapse as "research.\ Local connectors...", and the
    # sentence-boundary split below requires whitespace immediately after
    # [.!?] -- the backslash sits in that gap, so no split happens there,
    # silently merging two real sentences into one and hiding whichever
    # definitional sentence started the second half (this is exactly what
    # hid "Directory connectors are..." from DEFINITION_RE -- see
    # output/semantic_drift_findings.md's "What changed in the third
    # pass"). Only strips a backslash immediately followed by whitespace,
    # so an escaped markdown character like "\*" or "\_" (backslash
    # followed by a non-whitespace character) is left alone.
    block = re.sub(r"\\(\s)", r"\1", block)
    block = re.sub(r"\s+", " ", block).strip()
    if not block:
        return []
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", block) if s.strip()]


def find_definition_candidates(block: str):
    """Returns list of (primitive, local_text) for each definitional
    sentence found in the block. Superseded by
    find_definition_candidates_with_context() below -- kept because
    canonical_definition() still uses the plain sentence-list shape for
    the (short, single-section) canonical overview pages, where section
    context doesn't apply."""
    candidates = []
    for sentence in split_sentences(block):
        m = DEFINITION_RE.search(sentence)
        if m:
            candidates.append(((m.group(1) or m.group(2)).lower(), sentence))
    return candidates


def find_definition_candidates_with_context(text: str):
    """Like find_definition_candidates(), but also returns *where* the
    sentence lives: which H2 section it's under (or "(opening summary)"),
    the full paragraph it's part of, and how many sentences that whole
    section runs to.

    This exists to close a real gap the first version of this script had.
    Candidate #5 in this run's first pass -- government/desktop/skills.md's
    "A skill is a folder named after the skill, holding a SKILL.md file" --
    scored CONSISTENT when judged as an isolated sentence, because on its
    own it doesn't contradict canonical or claim a new capability. But that
    sentence is the opening line of a full "Building and deploying your own
    skills" section that goes on to re-derive frontmatter format, packaging,
    and upload steps -- a Rule 5(b) violation (restating authoring/build
    content a Tier 3 page shouldn't carry) that the isolated-sentence view
    had no way to see. Handing Stage B the section heading, the full
    paragraph, and the section's total length is what would have let it
    catch that the first time, instead of needing a human to reread the
    whole page afterward. See output/semantic_drift_findings.md for the
    corrected verdict this produced.
    """
    lines = strip_docs_index_box(text).splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith("# "):
            start = i + 1
            break
    if start is None:
        return []

    # Walk the body, splitting into (heading, section_lines) chunks on H2s.
    sections = []
    heading = "(opening summary)"
    buf = []
    for line in lines[start:]:
        if line.startswith("## "):
            sections.append((heading, buf))
            heading = line[3:].strip()
            buf = []
        elif re.match(r"^#{3,6}\s+", line):
            # An H3-H6 heading (e.g. "### Channel connections are separate
            # from personal connectors") only ends a *section* on H2; deeper
            # headings stay inside the current section's body. But left with
            # its literal "###" marker, a heading like that becomes its own
            # blank-line-separated paragraph (see the paragraph split below)
            # whose text starts with "###" -- which breaks DEFINITION_RE's
            # sentence-start anchor for the modifier-noun branch, and would
            # read strangely in a Stage B prompt either way. Strip the
            # marker so the heading is handled as plain prose, the same as
            # every other sentence on the page.
            buf.append(re.sub(r"^#{3,6}\s+", "", line))
        else:
            buf.append(line)
    sections.append((heading, buf))

    candidates = []
    for heading, section_lines in sections:
        section_text = "\n".join(section_lines)
        section_sentence_count = len(split_sentences(section_text))
        # Paragraphs = blank-line-separated chunks of the raw section text,
        # so a matched sentence can be reported with its full surrounding
        # paragraph, not just itself.
        paragraphs = [p for p in re.split(r"\n\s*\n", section_text) if p.strip()]
        for para in paragraphs:
            para_sentences = split_sentences(para)
            for sentence in para_sentences:
                m = DEFINITION_RE.search(sentence)
                if m:
                    candidates.append(
                        {
                            "primitive": (m.group(1) or m.group(2)).lower(),
                            "sentence": sentence,
                            "section_heading": heading,
                            "paragraph_context": " ".join(para_sentences),
                            "section_sentence_count": section_sentence_count,
                        }
                    )
    return candidates


def canonical_definition(primitive: str) -> str:
    path = CANONICAL_PAGES[primitive]
    text = strip_docs_index_box(path.read_text())
    block = extract_opening_block(text)
    sentences = split_sentences(block)
    # First 1-2 sentences of the canonical page's own opening block is its
    # definition, by construction (that's what "overview" pages open with).
    return " ".join(sentences[:2])


PROMPT_TEMPLATE = """You are checking two documentation style rules against a surface page.

Rule 1: a local restatement of a primitive's definition must not introduce a new capability, component, or constraint claim beyond what the canonical definition establishes, and must not contradict it. A surface page MAY instead be describing a genuinely distinct concept that happens to share a name or near-synonym with the canonical primitive -- that is not a violation of Rule 1.

Rule 5: a "Use in [Surface]" page may only contain a brief canonical-consistent summary, where the primitive is provisioned on this surface, actual install/enable steps for this surface, and surface-specific limits/admin controls. It must NOT restate authoring/build instructions that belong on the primitive's own build/how-to page instead.

Primitive under test: {primitive}
Canonical definition (from {canonical_source}):
\"\"\"{canonical_text}\"\"\"

Sentence under review (from {source_page}, surface: {surface}):
\"\"\"{local_text}\"\"\"

Context: this sentence appears under the heading "{section_heading}" on that page, in a section that runs to {section_sentence_count} sentences total. Here is the full paragraph the sentence is part of, for context (the sentence under review may be all or part of this paragraph):
\"\"\"{paragraph_context}\"\"\"

Return exactly one verdict for the sentence under Rule 1, plus a one-sentence rationale. If the surrounding context (not just the isolated sentence) suggests a separate Rule 5 problem -- e.g. this sentence opens or sits inside a section that is substantially restating authoring/build content rather than surface-specific summary/install/limits content -- say so explicitly in the rationale even though it doesn't change the Rule 1 verdict on the sentence itself.

- CONSISTENT: the sentence is a faithful summary or grounding of the canonical definition, with no new capability/component/constraint claim.
- DRIFT: the sentence asserts something about the canonical primitive that the canonical definition does not state, or contradicts it.
- DISTINCT_CONCEPT: the sentence is not actually describing the canonical primitive -- it's a different, surface-specific concept that happens to share a name or a similar name.

Format exactly:
VERDICT: <verdict>
RATIONALE: <one sentence, and flag any Rule 5 concern from the context if present>
"""


def call_model(prompt: str) -> str | None:
    """Real Stage B: an actual Anthropic API call. Returns the raw response
    text, or None if no API key is configured (this prototype's sandbox has
    network access to api.anthropic.com but no key -- see README)."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(
            {
                "model": MODEL_ID,
                "max_tokens": 200,
                "messages": [{"role": "user", "content": prompt}],
            }
        ).encode(),
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read())
    return body["content"][0]["text"]


def main():
    candidates = []
    for rel_path, surface, scope_status in SURFACE_PAGES:
        full_path = SCRAPE / rel_path
        text = full_path.read_text()
        block = extract_opening_block(text)
        sentence_count = len(split_sentences(block))

        defs = find_definition_candidates_with_context(text)
        if not defs:
            candidates.append(
                {
                    "source_page": "/" + rel_path[:-3],
                    "surface": surface,
                    "scope_status": scope_status,
                    "opening_block_sentence_count": sentence_count,
                    "status": "NO_LOCAL_DEFINITION",
                    "note": "Stage A found no sentence matching the definitional pattern "
                    "('A <primitive> is/are/bundles/adds/extends...') anywhere on the page. "
                    "Nothing to compare -- correctly abstains rather than forcing a verdict.",
                }
            )
            continue

        for d in defs:
            primitive, local_text = d["primitive"], d["sentence"]
            canonical_text = canonical_definition(primitive)
            canonical_source = str(CANONICAL_PAGES[primitive].relative_to(SCRAPE))
            prompt = PROMPT_TEMPLATE.format(
                primitive=primitive,
                canonical_source=canonical_source,
                canonical_text=canonical_text,
                source_page="/" + rel_path[:-3],
                surface=surface,
                local_text=local_text,
                section_heading=d["section_heading"],
                section_sentence_count=d["section_sentence_count"],
                paragraph_context=d["paragraph_context"],
            )
            entry = {
                "source_page": "/" + rel_path[:-3],
                "surface": surface,
                "scope_status": scope_status,
                "primitive": primitive,
                "cross_mapped_to_canonical": primitive == "connection",
                "opening_block_sentence_count": sentence_count,
                "length_heuristic_flag": sentence_count > 2,
                "local_text": local_text,
                "section_heading": d["section_heading"],
                "section_sentence_count": d["section_sentence_count"],
                "paragraph_context": d["paragraph_context"],
                "canonical_text": canonical_text,
                "canonical_source": canonical_source,
                "stage_b_prompt": prompt,
                "status": "PENDING_STAGE_B",
            }
            candidates.append(entry)

    OUTPUT.mkdir(exist_ok=True)

    ran_any_model_call = False
    for c in candidates:
        if c.get("status") != "PENDING_STAGE_B":
            continue
        response = call_model(c["stage_b_prompt"])
        if response is None:
            continue
        ran_any_model_call = True
        vm = re.search(r"VERDICT:\s*(\w+)", response)
        rm = re.search(r"RATIONALE:\s*(.+)", response)
        c["status"] = vm.group(1) if vm else "UNPARSEABLE"
        c["rationale"] = rm.group(1).strip() if rm else response.strip()
        c["verdict_source"] = "anthropic-api"

    out_path = OUTPUT / "semantic_drift_candidates.json"
    out_path.write_text(json.dumps(candidates, indent=2))

    print(f"Surface pages checked: {len(SURFACE_PAGES)}")
    print(f"Definitional candidates extracted: {sum(1 for c in candidates if 'stage_b_prompt' in c)}")
    print(f"Pages with no local definition (correctly abstained): "
          f"{sum(1 for c in candidates if c['status'] == 'NO_LOCAL_DEFINITION')}")
    print(f"Length-heuristic flags (>2 sentence opening block): "
          f"{sum(1 for c in candidates if c.get('length_heuristic_flag'))}")
    print()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY is not set -- Stage B (the semantic comparison) cannot run")
        print("unattended in this environment. All extracted candidates and their exact")
        print(f"Stage B prompts were written to {out_path} for a human, or this same")
        print("script pointed at a real key, to complete.")
        print()
        print("See output/semantic_drift_findings.md for this run's actual Stage B verdicts")
        print("(produced by applying the prompt above by hand -- see that file for how).")
    elif ran_any_model_call:
        print(f"Stage B complete via the Anthropic API. Wrote {out_path}")
    else:
        print(f"No candidates required Stage B. Wrote {out_path}")


if __name__ == "__main__":
    main()
