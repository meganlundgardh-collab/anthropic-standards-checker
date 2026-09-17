#!/usr/bin/env python3
"""
link_checker.py -- Part 3 prototype.

Implements Part 2's Rule 3: "Internal links must resolve, and anchor text
must match the destination's real title."

WHAT IT DOES
  1. Walks every scraped page under scrape/ (see scrape/ITS OWN README for
     how that scrape was produced -- WebFetch, not a raw HTTP crawl, because
     of this environment's network policy; a production version of this
     checker would run a normal crawler/HTTP client instead and the logic
     below would be unchanged).
  2. Extracts every internal markdown link: [anchor text](/path) or
     [anchor text](https://claude.com/docs/path).
  3. Resolves each link's target against data/known_pages.json (built by
     build_page_index.py from sitemap.xml + llms.txt) and, as a fallback,
     data/verified_overrides.json (the 5 pages that disagreement between
     those two sources sent me to go verify by hand -- see that file).
  4. Classifies each link:
       BROKEN          - target isn't a real page in any source. If the
                          anchor text closely matches another real page's
                          title, attach a "did you mean" suggestion.
       UNINDEXED       - target is a real, live page (in sitemap.xml and/or
                          verified live) but missing from llms.txt. This is
                          Part 1 finding #3's pattern, generalized.
       ANCHOR_MISMATCH - target resolves and we know its real title (from
                          llms.txt), but the anchor text doesn't look like
                          that title.
       UNVERIFIED      - target resolves but we have no title to compare
                          against (not in llms.txt, and not one of the 50
                          scraped pages) -- explicitly NOT counted as a pass.
                          A checker that reports "OK" when it actually just
                          has no data is worse than one that says "can't
                          tell." See the README's false-positive discussion.
       OK              - target resolves and anchor text matches its title.

USAGE
    python3 checker/link_checker.py

Writes output/findings.json (structured) and prints a human-readable
summary to stdout. output/run_log.md is written separately by hand after
reviewing findings.json, to capture *why* judgment calls were made about a
few specific results -- see that file.
"""
import json
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
SCRAPE = ROOT / "scrape"
OUTPUT = ROOT / "output"

STOPWORDS = {
    "a", "an", "the", "in", "on", "for", "to", "of", "and", "with", "your",
    "you", "is", "are", "at", "from", "by", "or", "as", "into", "how",
    "what", "when", "see",
}

LINK_RE = re.compile(
    r'(?<!!)\[([^\]]+)\]\((/(?!/)[^)\s]*|https://claude\.com/docs[^)\s]*)\)'
)


def normalize(url_or_path: str) -> str:
    # urlparse strips the fragment (and, for an absolute URL, everything but
    # the path) regardless of whether url_or_path is relative or absolute --
    # it doesn't require a scheme to do this correctly. The previous version
    # only called urlparse() when the string started with "http", so a
    # relative link with a #fragment (the common case: internal docs links
    # into glossary/concepts pages) passed through with the fragment still
    # attached, and could never match a fragment-less key in
    # known_pages.json. See run_log.md for the bug this caused and its
    # magnitude.
    path = urlparse(url_or_path).path
    path = re.sub(r"^/docs", "", path)
    path = re.sub(r"\.md$", "", path)
    path = path.rstrip("/")
    if path.endswith("/index"):
        path = path[: -len("/index")]
    if path == "":
        path = "/"
    return path


def tokenize(text: str) -> set:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if w not in STOPWORDS}


def similarity(a: str, b: str) -> float:
    """Overlap coefficient, not Jaccard: |A n B| / min(|A|,|B|).

    Chosen deliberately, and documented in the README's false-positive
    section: anchor text is routinely a short, legitimate fragment of a
    longer real title ("MCP tunnel" linking to "MCP tunnels", "the Google
    guide" linking to "Connect Google Drive, Calendar, and Gmail"). Jaccard
    (over the union) punishes exactly that pattern -- a short, correct
    anchor gets a low score purely because the title is longer. Dividing by
    the smaller set instead means a short anchor whose words all appear in
    the title still scores 1.0. This does not eliminate false positives
    (see the README) -- it removes one systematic, badly-calibrated source
    of them so the remaining ones are more informative to look at.
    """
    ta, tb = tokenize(a), tokenize(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / min(len(ta), len(tb))


def scrape_path_to_canonical(md_path: Path) -> str:
    rel = md_path.relative_to(SCRAPE)
    parts = list(rel.parts)
    if parts[-1] == "index.md":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1][: -len(".md")]
    return "/" + "/".join(parts) if parts else "/"


def load_known_pages():
    known = json.loads((DATA / "known_pages.json").read_text())
    overrides = json.loads((DATA / "verified_overrides.json").read_text())
    return known, {k: v for k, v in overrides.items() if not k.startswith("_")}


def title_for(path: str, known: dict, overrides: dict, scraped_titles: dict):
    """Best-effort real title for a resolved path, and where it came from."""
    entry = known.get(path)
    if entry and entry.get("llms_title"):
        return entry["llms_title"], "llms.txt"
    if path in scraped_titles:
        return scraped_titles[path], "scraped H1"
    return None, None


def resolves(path: str, known: dict, overrides: dict):
    if path in known and (known[path]["in_sitemap"] or known[path]["in_llms_txt"]):
        return True, known[path]["in_llms_txt"]
    if path in overrides:
        return overrides[path]["verified_live"], False  # verified-only pages are all llms.txt-listed already, so False here means "check overrides dict directly if needed"
    return False, False


def extract_h1(text: str) -> str | None:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return None


def slugify(text: str) -> str:
    """GitHub-style heading-anchor slug: lowercase, strip everything except
    word characters/spaces/hyphens, spaces to hyphens. This is what turns a
    heading like "## DCR and CIMD details" into the fragment
    "#dcr-and-cimd-details" that a link into that section actually uses.

    Known gap, not fixed here: doesn't dedupe repeated headings the way
    GitHub does (appending -1, -2, ... to the second/third occurrence of the
    same heading text on one page). Not observed in this run's 50 pages;
    would need a per-page seen-slugs counter if it came up.
    """
    s = text.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s


def extract_section_headings(text: str) -> dict:
    """Map heading-anchor slug -> raw heading text, for every H2-H6 on a
    scraped page. Lets a fragment link's anchor text be compared against the
    specific section it targets instead of the whole page's title -- see
    README's fragment-link section for why that distinction matters."""
    headings = {}
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r"^(#{2,6})\s+(.*)$", line)
        if m:
            heading_text = re.sub(r"[*_`]", "", m.group(2)).strip()
            if heading_text:
                headings[slugify(heading_text)] = heading_text
    return headings


def main():
    known, overrides = load_known_pages()

    md_files = sorted(SCRAPE.rglob("*.md"))
    scraped_titles = {}
    section_headings = {}  # canonical_path -> {slug: heading_text}, scraped pages only
    for md in md_files:
        text = md.read_text(errors="replace")
        if text.startswith("FETCH_FAILED"):
            continue
        h1 = extract_h1(text)
        if h1:
            scraped_titles[scrape_path_to_canonical(md)] = h1
        section_headings[scrape_path_to_canonical(md)] = extract_section_headings(text)

    # Precompute a title index for "did you mean" suggestions on broken links.
    title_index = []  # (title, canonical_path)
    for path, entry in known.items():
        if entry.get("llms_title"):
            title_index.append((entry["llms_title"], path))
    for path, title in scraped_titles.items():
        title_index.append((title, path))

    findings = []
    counts = defaultdict(int)

    for md in md_files:
        text = md.read_text(errors="replace")
        if text.startswith("FETCH_FAILED"):
            continue
        source_path = scrape_path_to_canonical(md)

        for match in LINK_RE.finditer(text):
            anchor, href = match.group(1), match.group(2)
            target = normalize(href)
            frag = urlparse(href).fragment or None
            if target == source_path:
                continue  # self-link / anchor-only, not interesting here

            in_known = target in known and (known[target]["in_sitemap"] or known[target]["in_llms_txt"])
            in_override = target in overrides
            exists = in_known or (in_override and overrides[target]["verified_live"])
            confirmed_dead = in_override and not overrides[target]["verified_live"]

            entry = {
                "source_page": source_path,
                "anchor_text": anchor,
                "href": href,
                "resolved_target": target,
            }

            if confirmed_dead:
                entry["status"] = "BROKEN"
                entry["reason"] = overrides[target]["evidence"]
                best = max(title_index, key=lambda t: similarity(anchor, t[0]), default=None)
                if best and similarity(anchor, best[0]) >= 0.5:
                    entry["did_you_mean"] = {"title": best[0], "path": best[1]}
                counts["BROKEN"] += 1

            elif not exists:
                entry["status"] = "BROKEN"
                entry["reason"] = "Target path not found in sitemap.xml, llms.txt, or verified_overrides.json."
                best = max(title_index, key=lambda t: similarity(anchor, t[0]), default=None)
                if best and similarity(anchor, best[0]) >= 0.5:
                    entry["did_you_mean"] = {"title": best[0], "path": best[1]}
                counts["BROKEN"] += 1

            else:
                in_llms = known.get(target, {}).get("in_llms_txt", False)
                if not in_llms and not (in_override and overrides[target]["verified_live"]):
                    entry["status"] = "UNINDEXED"
                    entry["reason"] = "Target is a real, live page but is missing from llms.txt."
                    counts["UNINDEXED"] += 1
                elif not in_llms and in_override:
                    entry["status"] = "UNINDEXED"
                    entry["reason"] = "Target verified live by hand; missing from both sitemap.xml and llms.txt."
                    counts["UNINDEXED"] += 1
                else:
                    real_title, title_source = title_for(target, known, overrides, scraped_titles)
                    if real_title is None:
                        entry["status"] = "UNVERIFIED"
                        entry["reason"] = "Target resolves but no known title (not in llms.txt, not one of the 50 scraped pages) to compare anchor text against."
                        counts["UNVERIFIED"] += 1
                    else:
                        # Default comparison is against the whole page's title.
                        # For a fragment link into a page we actually scraped,
                        # compare against the specific section it targets
                        # instead -- a fragment link's anchor text is supposed
                        # to name the section, not the page, so comparing it
                        # to the page title is close to a category error (see
                        # README's fragment-link section / run_log.md).
                        compare_text, compare_source = real_title, title_source
                        if frag:
                            headings = section_headings.get(target)
                            if headings is None:
                                entry["fragment_note"] = (
                                    f"Target page {target!r} wasn't one of the 50 scraped "
                                    "pages, so no section-heading data exists for it here; "
                                    "falling back to comparing anchor text against the page "
                                    "title, the same as a fragment-less link."
                                )
                            elif frag in headings:
                                compare_text, compare_source = headings[frag], "scraped section heading"
                                entry["section_heading"] = headings[frag]
                            else:
                                entry["fragment_note"] = (
                                    f"Target page was scraped, but no H2-H6 heading's anchor "
                                    f"slug matches fragment {frag!r} (may target a definition-"
                                    "list term, bold inline text, or a manually-set HTML "
                                    "anchor id, none of which this checker extracts). Falling "
                                    "back to comparing anchor text against the page title."
                                )
                        sim = similarity(anchor, compare_text)
                        entry["real_title"] = real_title
                        entry["real_title_source"] = title_source
                        entry["compared_against"] = compare_text
                        entry["compared_against_source"] = compare_source
                        entry["anchor_title_similarity"] = round(sim, 2)
                        if sim >= 0.5:
                            entry["status"] = "OK"
                            counts["OK"] += 1
                        else:
                            entry["status"] = "ANCHOR_MISMATCH"
                            entry["reason"] = f"Anchor text {anchor!r} doesn't look like {compare_source} {compare_text!r} (token overlap {sim:.2f})."
                            counts["ANCHOR_MISMATCH"] += 1

            findings.append(entry)

    OUTPUT.mkdir(exist_ok=True)
    (OUTPUT / "findings.json").write_text(json.dumps(findings, indent=2))

    total_links = len(findings)
    print(f"Scraped pages checked: {len(md_files)}")
    print(f"Internal links extracted: {total_links}")
    print()
    for status in ["BROKEN", "ANCHOR_MISMATCH", "UNINDEXED", "UNVERIFIED", "OK"]:
        print(f"  {status:16s} {counts[status]}")
    print()
    print("--- BROKEN ---")
    for f in findings:
        if f["status"] == "BROKEN":
            dym = f" -> did you mean {f['did_you_mean']['path']!r} ({f['did_you_mean']['title']!r})?" if "did_you_mean" in f else ""
            print(f"  [{f['source_page']}] {f['anchor_text']!r} -> {f['href']}{dym}")
    print()
    print("--- ANCHOR_MISMATCH ---")
    for f in findings:
        if f["status"] == "ANCHOR_MISMATCH":
            print(f"  [{f['source_page']}] {f['anchor_text']!r} -> {f['resolved_target']} (compared against {f['compared_against_source']}: {f['compared_against']!r}, overlap {f['anchor_title_similarity']})")
    print()
    print("--- UNINDEXED ---")
    for f in findings:
        if f["status"] == "UNINDEXED":
            print(f"  [{f['source_page']}] {f['anchor_text']!r} -> {f['resolved_target']}")

    print(f"\nWrote {OUTPUT / 'findings.json'}")


if __name__ == "__main__":
    main()
