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


# --- Topic Cluster Architecture ---

# Predefined clusters for the AI memory niche. Each cluster has a pillar (broad head term)
# and supporting topics. Keywords are matched to clusters by keyword overlap.
TOPIC_CLUSTERS = [
    {
        "name": "ai-agent-memory",
        "pillar_keyword": "AI agent memory",
        "pillar_slug": "ai-agent-memory-explained",
        "description": "The definitive guide to AI agent memory systems",
        "match_terms": ["agent memory", "agent remember", "agentic memory", "agent recall",
                        "agent persistent", "agent state", "stateful agent"],
    },
    {
        "name": "memory-types",
        "pillar_keyword": "types of AI memory",
        "pillar_slug": "ai-agents-memory-types",
        "description": "All types of memory in AI systems explained",
        "match_terms": ["episodic memory", "semantic memory", "procedural memory",
                        "short term memory", "long term memory", "working memory",
                        "limited memory", "memory types", "memory hierarchy"],
    },
    {
        "name": "memory-frameworks",
        "pillar_keyword": "best ai memory system",
        "pillar_slug": "best-ai-memory-systems",
        "description": "Comparison of all AI memory frameworks and tools",
        "match_terms": ["mem0", "zep", "letta", "memgpt", "cognee", "hindsight",
                        "memory framework", "memory system compare", "alternative",
                        "memory tool", "open source memory"],
    },
    {
        "name": "ai-chat-memory",
        "pillar_keyword": "AI chat memory",
        "pillar_slug": "ai-that-remembers-conversations",
        "description": "How to give AI chatbots persistent memory",
        "match_terms": ["chat memory", "conversation memory", "remember conversation",
                        "chatbot memory", "assistant remember", "ai remember",
                        "character ai", "chat history", "persistent chat"],
    },
    {
        "name": "rag-and-retrieval",
        "pillar_keyword": "RAG vs agent memory",
        "pillar_slug": "rag-vs-agent-memory",
        "description": "RAG, embeddings, and retrieval for AI memory",
        "match_terms": ["rag", "retrieval", "embedding", "vector", "context window",
                        "knowledge base", "search", "index"],
    },
    {
        "name": "memory-architecture",
        "pillar_keyword": "AI memory architecture",
        "pillar_slug": "ai-agent-architecture-patterns",
        "description": "How to design and build AI memory systems",
        "match_terms": ["architecture", "design", "implement", "build", "pattern",
                        "consolidation", "benchmark", "evaluation", "system design"],
    },
]


def assign_clusters(keywords_path: str):
    """Assign topic cluster and role (pillar/supporting) to all keywords.

    Each keyword is matched to a cluster based on term overlap. The keyword with
    the matching pillar_slug becomes the pillar; all others are supporting.
    Unmatched keywords get cluster=None (standalone).
    """
    with open(keywords_path) as f:
        config = yaml.safe_load(f)

    keywords = config.get("keywords", [])
    if not keywords:
        print("No keywords to cluster.")
        return

    # Build cluster assignments
    assigned = 0
    pillar_count = 0
    supporting_count = 0

    for kw in keywords:
        primary = kw["primary"].lower()
        slug = kw.get("slug", "")
        related = " ".join(kw.get("related", [])).lower()
        full_text = f"{primary} {related} {slug}"

        best_cluster = None
        best_score = 0

        for cluster in TOPIC_CLUSTERS:
            # Check if this keyword is the pillar
            if slug == cluster["pillar_slug"]:
                best_cluster = cluster
                best_score = 999
                break

            # Score by match term overlap
            score = sum(1 for term in cluster["match_terms"] if term in full_text)
            if score > best_score:
                best_score = score
                best_cluster = cluster

        if best_cluster and best_score > 0:
            kw["cluster"] = best_cluster["name"]
            if slug == best_cluster["pillar_slug"]:
                kw["role"] = "pillar"
                pillar_count += 1
            else:
                kw["role"] = "supporting"
                supporting_count += 1
            assigned += 1
        else:
            # Standalone — not in any cluster
            kw.pop("cluster", None)
            kw.pop("role", None)

    with open(keywords_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, width=200)

    print(f"\nTopic clusters assigned: {assigned}/{len(keywords)} keywords clustered")
    print(f"  {pillar_count} pillar pages, {supporting_count} supporting pages")

    # Print cluster summary
    cluster_counts = {}
    for kw in keywords:
        c = kw.get("cluster", "unclustered")
        cluster_counts[c] = cluster_counts.get(c, 0) + 1

    print("\nCluster breakdown:")
    for name, count in sorted(cluster_counts.items()):
        pillar_slug = ""
        for cl in TOPIC_CLUSTERS:
            if cl["name"] == name:
                pillar_slug = cl["pillar_slug"]
                break
        suffix = f" (pillar: {pillar_slug})" if pillar_slug else ""
        print(f"  {name}: {count} articles{suffix}")


def get_cluster_siblings(keywords_path: str, slug: str) -> dict:
    """Get all sibling articles in the same cluster as the given slug.

    Returns dict with:
    - cluster_name: str
    - role: "pillar" or "supporting"
    - pillar_slug: str (the pillar article's slug)
    - siblings: list of {slug, primary, role} for all other articles in the cluster
    """
    with open(keywords_path) as f:
        config = yaml.safe_load(f)

    keywords = config.get("keywords", [])

    # Find this keyword's cluster
    target_kw = None
    for kw in keywords:
        if kw.get("slug") == slug:
            target_kw = kw
            break

    if not target_kw or not target_kw.get("cluster"):
        return {}

    cluster_name = target_kw["cluster"]

    # Find pillar slug
    pillar_slug = ""
    for cl in TOPIC_CLUSTERS:
        if cl["name"] == cluster_name:
            pillar_slug = cl["pillar_slug"]
            break

    # Collect siblings
    siblings = []
    for kw in keywords:
        if kw.get("cluster") == cluster_name and kw.get("slug") != slug:
            siblings.append({
                "slug": kw.get("slug", ""),
                "primary": kw["primary"],
                "role": kw.get("role", "supporting"),
            })

    return {
        "cluster_name": cluster_name,
        "role": target_kw.get("role", "supporting"),
        "pillar_slug": pillar_slug,
        "siblings": siblings,
    }
