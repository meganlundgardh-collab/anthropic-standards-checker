#!/usr/bin/env python3
"""
build_page_index.py

Builds the "ground truth" page index the checker validates links against.

Two independent sources are combined on purpose, not just one:
  - data/sitemap-urls.txt   : every URL in claude.com/docs/sitemap.xml
                               (machine-generated, presumably build-time output
                               -- this is our best proxy for "does this page
                               really exist".)
  - data/llms-txt-raw.txt   : every link in claude.com/docs/llms.txt
                               (Anthropic's own curated/generated index for
                               LLM consumers -- this is our proxy for "is this
                               page discoverable the way the docs site itself
                               tells an LLM to discover it".)

Part 1 finding #3 found a page (connectors/building/mcpb) that is live and
linked-to but missing from llms.txt. That finding motivates *why* this
checker cross-references two sources instead of trusting either one alone:
a link-validity checker that only trusted llms.txt would have quietly
treated a real page as "not indexed" and might flag links to it as
suspicious, when the actual problem is the index, not the link.

Output: data/known_pages.json, a dict keyed by normalized path
        (e.g. "/connectors/building/mcpb") with:
          - in_sitemap:  bool
          - in_llms_txt: bool
          - llms_title:  the title llms.txt gives it, if listed
          - sources:     which raw inputs contributed this path

Also prints a short discrepancy report to stdout -- this *is* one of the
checker's real findings, generated fresh from the current live site, not
hand-curated from Part 1.
"""
import json
import re
from pathlib import Path
from urllib.parse import urlparse

DATA = Path(__file__).parent.parent / "data"


def normalize(url: str) -> str:
    """Strip domain, /docs prefix, trailing .md, trailing slash -> bare path."""
    path = urlparse(url).path
    path = re.sub(r"^/docs", "", path)
    path = re.sub(r"\.md$", "", path)
    path = path.rstrip("/")
    # llms.txt sometimes indexes a section by its /index.md; sitemap indexes
    # the same page without the /index suffix (e.g. connectors/github/index.md
    # vs connectors/github). Normalize /foo/index -> /foo so the two sources
    # can be compared on equal footing; this equivalence is itself worth
    # flagging as a systematic naming inconsistency between the two indexes,
    # not silently swallowed -- see the printed report below.
    if path.endswith("/index"):
        path = path[: -len("/index")]
    if path == "":
        path = "/"
    return path


def load_sitemap():
    urls = [
        line.strip()
        for line in (DATA / "sitemap-urls.txt").read_text().splitlines()
        if line.strip()
    ]
    return {normalize(u) for u in urls}


def load_llms_txt():
    """Returns dict: normalized_path -> (title, raw_url, used_index_suffix)."""
    out = {}
    for line in (DATA / "llms-txt-raw.txt").read_text().splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
        raw_url, title = [p.strip() for p in line.split("|", 1)]
        norm = normalize(raw_url)
        used_index = raw_url.rstrip().endswith("/index.md")
        out[norm] = (title, raw_url, used_index)
    return out


def main():
    sitemap_paths = load_sitemap()
    llms = load_llms_txt()
    llms_paths = set(llms.keys())

    all_paths = sitemap_paths | llms_paths
    known_pages = {}
    for path in sorted(all_paths):
        in_sitemap = path in sitemap_paths
        in_llms = path in llms_paths
        title, raw_url, used_index = llms.get(path, (None, None, False))
        known_pages[path] = {
            "in_sitemap": in_sitemap,
            "in_llms_txt": in_llms,
            "llms_title": title,
            "llms_txt_raw_url": raw_url,
            "llms_txt_used_index_suffix": used_index,
        }

    out_path = DATA / "known_pages.json"
    out_path.write_text(json.dumps(known_pages, indent=2, sort_keys=True))

    # --- discrepancy report ---
    only_sitemap = sorted(sitemap_paths - llms_paths)
    only_llms = sorted(llms_paths - sitemap_paths)
    index_suffix_paths = sorted(p for p, v in known_pages.items() if v["llms_txt_used_index_suffix"])

    print(f"Total unique paths (union of both sources): {len(all_paths)}")
    print(f"  In sitemap.xml:  {len(sitemap_paths)}")
    print(f"  In llms.txt:     {len(llms_paths)}")
    print()
    print(f"In sitemap.xml but MISSING from llms.txt: {len(only_sitemap)}")
    for p in only_sitemap:
        print(f"  - {p}")
    print()
    print(f"In llms.txt but MISSING from sitemap.xml: {len(only_llms)}")
    for p in only_llms:
        print(f"  - {p}  (llms.txt title: {llms[p][0]!r})")
    print()
    print(f"Paths where llms.txt uses an /index.md suffix sitemap.xml doesn't: {len(index_suffix_paths)}")
    for p in index_suffix_paths:
        print(f"  - {p}  (raw llms.txt URL: {known_pages[p]['llms_txt_raw_url']})")

    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
