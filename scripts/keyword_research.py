"""Keyword research — validate and discover keywords using Google Autocomplete and Trends."""

import json
import re
import time
from pathlib import Path

import httpx
import yaml


def get_autocomplete_suggestions(query: str) -> list[str]:
    """Get Google Autocomplete suggestions for a query."""
    url = "https://suggestqueries.google.com/complete/search"
    params = {
        "client": "firefox",
        "q": query,
        "hl": "en",
    }
    try:
        resp = httpx.get(url, params=params, timeout=10)
        data = resp.json()
        # Response format: [query, [suggestions]]
        if len(data) >= 2 and isinstance(data[1], list):
            return [s for s in data[1] if isinstance(s, str)]
    except Exception:
        pass
    return []


def get_related_searches(seed_keywords: list[str]) -> dict[str, list[str]]:
    """Get autocomplete suggestions for each seed keyword + variations."""
    results = {}

    for kw in seed_keywords:
        suggestions = set()

        # Base query
        suggestions.update(get_autocomplete_suggestions(kw))
        time.sleep(0.3)

        # Add alphabet suffixes for more long-tail ideas
        for letter in "abcdefghijklmnop":
            more = get_autocomplete_suggestions(f"{kw} {letter}")
            suggestions.update(more)
            time.sleep(0.2)

        # Add question prefixes
        for prefix in ["what is", "how to", "why", "best"]:
            more = get_autocomplete_suggestions(f"{prefix} {kw}")
            suggestions.update(more)
            time.sleep(0.2)

        # Remove the seed itself
        suggestions.discard(kw)
        results[kw] = sorted(suggestions)

    return results


def score_keyword(keyword: str, suggestions: list[str]) -> dict:
    """Score a keyword based on autocomplete signals."""
    # If it appears in autocomplete for related terms, it has search volume
    appearances = 0
    for sugg_list in suggestions.values() if isinstance(suggestions, dict) else [suggestions]:
        for s in sugg_list:
            if keyword.lower() in s.lower():
                appearances += 1

    return {
        "keyword": keyword,
        "autocomplete_appearances": appearances,
        "has_search_volume": appearances > 0,
    }


def research_and_validate(keywords_path: str, output_path: str = "data/keyword-research.json"):
    """Research all keywords from config and validate with autocomplete data."""
    kw_file = Path(keywords_path)
    if not kw_file.exists():
        print("No keywords file found.")
        return

    with open(kw_file) as f:
        config = yaml.safe_load(f)

    keywords = config.get("keywords", [])
    seed_terms = [
        "ai agent memory",
        "ai memory",
        "best ai memory",
        "llm memory",
        "long term memory ai",
        "ai that remembers",
        "persistent memory llm",
        "rag vs memory",
        "ai memory system",
        "give ai memory",
        "chatbot memory",
        "agent memory framework",
        "ai conversation memory",
        "embedding model memory",
        "vector database memory",
        "context window llm",
        "mem0",
        "zep memory",
        "letta memgpt",
    ]

    print(f"Researching {len(seed_terms)} seed terms via Google Autocomplete...\n")

    # Get autocomplete data
    autocomplete_data = get_related_searches(seed_terms)

    total_suggestions = sum(len(v) for v in autocomplete_data.values())
    print(f"  Found {total_suggestions} autocomplete suggestions\n")

    # Score existing keywords
    print("Validating existing keywords:")
    validated = []
    for kw in keywords:
        primary = kw["primary"]

        # Check if this keyword appears in any autocomplete results
        found_in = 0
        matching_suggestions = []
        for seed, suggestions in autocomplete_data.items():
            for s in suggestions:
                if primary.lower() in s.lower() or any(
                    r.lower() in s.lower() for r in kw.get("related", [])
                ):
                    found_in += 1
                    matching_suggestions.append(s)

        status = "VALIDATED" if found_in > 0 else "LOW VOLUME"
        print(f"  [{status:>10}] {primary} ({found_in} autocomplete matches)")

        validated.append({
            "keyword": primary,
            "slug": kw.get("slug", ""),
            "autocomplete_matches": found_in,
            "validated": found_in > 0,
            "matching_suggestions": matching_suggestions[:5],
        })

    # Discover NEW keyword opportunities from autocomplete
    print(f"\nDiscovering new keyword opportunities...")
    all_suggestions = set()
    for suggestions in autocomplete_data.values():
        all_suggestions.update(suggestions)

    # Filter to suggestions that look like good article targets
    existing_primaries = {kw["primary"].lower() for kw in keywords}
    new_opportunities = []
    for sugg in sorted(all_suggestions):
        sugg_lower = sugg.lower()
        # Skip if we already target this
        if any(ep in sugg_lower or sugg_lower in ep for ep in existing_primaries):
            continue
        # Keep ONLY if related to memory systems (strict filter to avoid off-topic noise)
        must_have = ["memory", "remember", "context window", "rag", "embedding", "vector"]
        nice_to_have = ["agent", "llm", "ai", "chatbot", "conversation"]
        has_must = any(term in sugg_lower for term in must_have)
        has_nice = any(term in sugg_lower for term in nice_to_have)
        if has_must or (has_nice and len(sugg.split()) >= 3):
            new_opportunities.append(sugg)

    print(f"  Found {len(new_opportunities)} new keyword opportunities:\n")
    for opp in new_opportunities[:30]:
        print(f"    → {opp}")

    # Save report
    report = {
        "researched_at": str(Path(keywords_path)),
        "seed_terms": seed_terms,
        "autocomplete_data": {k: v[:20] for k, v in autocomplete_data.items()},
        "validated_keywords": validated,
        "new_opportunities": new_opportunities,
        "summary": {
            "total_keywords": len(keywords),
            "validated": sum(1 for v in validated if v["validated"]),
            "low_volume": sum(1 for v in validated if not v["validated"]),
            "new_opportunities_found": len(new_opportunities),
        },
    }

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))
    print(f"\n  Report saved to {output_path}")

    # Summary
    s = report["summary"]
    print(f"\n  Summary: {s['validated']}/{s['total_keywords']} keywords validated, "
          f"{s['new_opportunities_found']} new opportunities found")

    return report


def add_opportunities_to_config(research_path: str, keywords_path: str, max_add: int = 20):
    """Add top new opportunities from research to keywords config."""
    research = json.loads(Path(research_path).read_text())
    opportunities = research.get("new_opportunities", [])

    if not opportunities:
        print("No new opportunities to add.")
        return

    with open(keywords_path) as f:
        config = yaml.safe_load(f)

    existing_slugs = {kw.get("slug", "") for kw in config.get("keywords", [])}
    added = 0

    for opp in opportunities[:max_add]:
        slug = re.sub(r"[^a-z0-9]+", "-", opp.lower()).strip("-")
        if slug in existing_slugs:
            continue

        config["keywords"].append({
            "primary": opp,
            "related": [],
            "slug": slug,
            "instructions": f"Article about {opp}, discovered via Google Autocomplete.",
        })
        existing_slugs.add(slug)
        added += 1

    with open(keywords_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

    print(f"Added {added} new keywords from research to {keywords_path}")
