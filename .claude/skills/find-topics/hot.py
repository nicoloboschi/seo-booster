#!/usr/bin/env python3
"""What's hot right now in agent/LLM memory. Standard library only.

Usage: python3 .claude/skills/find-topics/hot.py [--days 14]

Prints, newest signals first:
  - Hacker News stories (by points)  -> what developers are talking about
  - GitHub repos created recently (by stars) -> new tools worth a page
  - arXiv papers (newest)            -> new research worth a page
  - Google Autocomplete suggestions  -> how people phrase the question
Then marks each item [covered] if a page on the site already mentions its key term.
"""
import argparse
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from pathlib import Path

ART = Path(__file__).resolve().parents[3] / "content" / "articles"
QUERIES = ["agent memory", "llm memory", "long-term memory agent", "memory layer ai", "mem0", "letta", "zep memory",
           "context engineering", "agentic memory"]
UA = {"User-Agent": "aiagentmemory-curator/1.0"}

ap = argparse.ArgumentParser()
ap.add_argument("--days", type=int, default=14)
args = ap.parse_args()
since = date.today() - timedelta(days=args.days)
site = " ".join(p.read_text().lower() for p in ART.glob("*.md"))


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
        return r.read().decode()


def covered(term):
    return "[covered]" if term and term.lower() in site else ""


def section(title, fn):
    print(f"\n== {title}")
    try:
        fn()
    except Exception as e:  # one dead source shouldn't hide the others
        print(f"  (failed: {e})")


def hn():
    seen = {}
    ts = int(time.mktime(since.timetuple()))
    for q in QUERIES:
        url = f"https://hn.algolia.com/api/v1/search?query={urllib.parse.quote(q)}&tags=story&numericFilters=created_at_i>{ts}"
        for h in json.loads(get(url))["hits"]:
            seen[h["objectID"]] = h
    for h in sorted(seen.values(), key=lambda h: -(h.get("points") or 0))[:15]:
        print(f"  {h.get('points') or 0:4}pts  {h['title'][:90]}  https://news.ycombinator.com/item?id={h['objectID']}")


def github():
    seen = {}
    for q in ["agent memory", "llm memory", "memory layer", "mcp memory"]:
        url = ("https://api.github.com/search/repositories?sort=stars&order=desc&per_page=10&q="
               + urllib.parse.quote(f"{q} created:>{since - timedelta(days=60)}"))
        for r in json.loads(get(url))["items"]:
            seen[r["full_name"]] = r
    for r in sorted(seen.values(), key=lambda r: -r["stargazers_count"])[:15]:
        name = r["name"]
        print(f"  {r['stargazers_count']:6}*  {r['full_name']:45} {(r['description'] or '')[:60]}  {covered(name)}")


def arxiv():
    q = urllib.parse.quote('(abs:"agent memory" OR abs:"long-term memory" OR abs:"memory-augmented") AND (cat:cs.CL OR cat:cs.AI)')
    feed = ET.fromstring(get(f"http://export.arxiv.org/api/query?search_query={q}&sortBy=submittedDate&sortOrder=descending&max_results=15"))
    ns = {"a": "http://www.w3.org/2005/Atom"}
    for e in feed.findall("a:entry", ns):
        title = re.sub(r"\s+", " ", e.find("a:title", ns).text).strip()
        print(f"  {e.find('a:published', ns).text[:10]}  {title[:95]}  {e.find('a:id', ns).text}")


def autocomplete():
    for q in ["agent memory ", "llm memory ", "ai memory ", "mem0 vs ", "best memory for "]:
        sugg = json.loads(get("https://suggestqueries.google.com/complete/search?client=firefox&q=" + urllib.parse.quote(q)))[1]
        print(f"  {q.strip():18} " + " | ".join(f"{s}{'*' if s.lower() in site else ''}" for s in sugg[:8]))
    print("  (* = exact phrase already on the site)")


section(f"Hacker News, last {args.days} days", hn)
section("GitHub repos created in the last ~2 months, by stars", github)
section("arXiv, newest", arxiv)
section("Google Autocomplete", autocomplete)
