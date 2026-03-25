"""Rank keywords by search volume signals and find opportunities.

Uses Google Autocomplete to estimate relative search volume.
Run: uv run seo-booster rank
"""

import time
import yaml
import httpx


SEED_TOPICS = [
    # AI Memory (core)
    "ai agent memory",
    "ai memory",
    "llm memory",
    "give ai memory",
    "ai remembers",
    "persistent memory ai",
    "long term memory ai",
    "chatbot memory",
    "ai conversation memory",
    # Agent Memory specifics
    "episodic memory ai",
    "semantic memory ai",
    "procedural memory ai",
    "memory consolidation ai",
    "memory retrieval ai",
    # Competitor terms
    "mem0",
    "zep ai",
    "letta ai",
    "memgpt",
    "cognee ai",
    # RAG & retrieval
    "rag vs",
    "retrieval augmented generation",
    "rag alternative",
    "rag limitations",
    # AI Agents (expanded topic)
    "ai agent",
    "ai agent framework",
    "ai agent architecture",
    "ai agent tools",
    "agentic ai",
    "autonomous ai agent",
    "multi agent",
    "ai agent builder",
    "ai agent open source",
    # Agent subtopics
    "ai agent planning",
    "ai agent reasoning",
    "ai agent tool use",
    "function calling llm",
    "ai agent orchestration",
    "ai agent evaluation",
    # Embeddings & vector
    "embedding model",
    "vector database ai",
    "similarity search ai",
    # Context & tokens
    "context window llm",
    "token limit llm",
    "long context llm",
]


def get_autocomplete(query: str) -> list[str]:
    """Get Google Autocomplete suggestions."""
    try:
        resp = httpx.get(
            "https://suggestqueries.google.com/complete/search",
            params={"client": "firefox", "q": query, "hl": "en"},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json()[1]
    except Exception:
        pass
    return []


def score_keyword(keyword: str) -> dict:
    """Score a keyword's search volume using multiple signals."""
    scores = {}

    # Signal 1: Direct autocomplete count
    suggestions = get_autocomplete(keyword)
    scores["direct_suggestions"] = len(suggestions)
    scores["exact_match"] = keyword.lower() in [s.lower() for s in suggestions]
    time.sleep(0.2)

    # Signal 2: Appears when typing partial query
    partial = keyword[:max(len(keyword) // 2, 8)]
    partial_suggestions = get_autocomplete(partial)
    scores["partial_match"] = any(keyword.lower() in s.lower() for s in partial_suggestions)
    time.sleep(0.2)

    # Signal 3: Alphabet expansion (how many variations exist)
    variation_count = 0
    for letter in "abcdefgh":
        variations = get_autocomplete(f"{keyword} {letter}")
        variation_count += len(variations)
        time.sleep(0.15)

    scores["variations"] = variation_count

    # Composite score (0-100)
    score = 0
    if scores["exact_match"]:
        score += 40
    if scores["partial_match"]:
        score += 20
    score += min(scores["direct_suggestions"] * 3, 20)  # max 20 from suggestions
    score += min(scores["variations"] // 4, 20)  # max 20 from variations

    scores["total_score"] = score
    scores["top_suggestions"] = suggestions[:5]

    return scores


def discover_opportunities(existing_keywords: list[str]) -> list[dict]:
    """Find new keyword opportunities from seed topics."""
    existing_lower = {k.lower() for k in existing_keywords}
    opportunities = []

    print(f"\n  Scanning {len(SEED_TOPICS)} seed topics for opportunities...\n")

    for seed in SEED_TOPICS:
        suggestions = get_autocomplete(seed)
        time.sleep(0.2)

        # Also get alphabet variations
        for letter in "abcdefghijklmno":
            more = get_autocomplete(f"{seed} {letter}")
            suggestions.extend(more)
            time.sleep(0.15)

        for sugg in set(suggestions):
            sugg_lower = sugg.lower()

            # Skip if we already target this
            if any(existing in sugg_lower or sugg_lower in existing for existing in existing_lower):
                continue

            # Must be related to memory, agents, or our niche
            relevant_terms = ["memory", "agent", "rag", "remember", "context", "embedding",
                              "vector", "llm", "chatbot", "persistent", "mem0", "zep", "letta",
                              "memgpt", "cognee", "hindsight", "agentic"]
            if not any(term in sugg_lower for term in relevant_terms):
                continue

            # Skip too short or too long
            words = sugg.split()
            if len(words) < 2 or len(words) > 8:
                continue

            opportunities.append(sugg)

    # Deduplicate and score top opportunities
    unique = sorted(set(opportunities))
    return unique


def run_keyword_ranking(keywords_path: str = "data/keywords.yaml"):
    """Rank all current keywords and discover new opportunities."""
    with open(keywords_path) as f:
        config = yaml.safe_load(f)

    keywords = config.get("keywords", [])
    keyword_names = [k["primary"] for k in keywords]

    print(f"\n{'='*70}")
    print(f"  KEYWORD RANKING — {len(keywords)} keywords")
    print(f"{'='*70}")

    # Score each keyword
    ranked = []
    for i, kw in enumerate(keywords, 1):
        name = kw["primary"]
        print(f"  [{i}/{len(keywords)}] Scoring: {name}", end="", flush=True)
        scores = score_keyword(name)
        ranked.append({"keyword": name, "slug": kw.get("slug", ""), **scores})
        print(f" → {scores['total_score']}/100")

    # Sort by score
    ranked.sort(key=lambda x: x["total_score"], reverse=True)

    # Print ranked list
    print(f"\n{'RANKED KEYWORDS':=^70}\n")
    for i, r in enumerate(ranked, 1):
        bar = "█" * (r["total_score"] // 5) + "░" * (20 - r["total_score"] // 5)
        exact = "✓" if r["exact_match"] else " "
        print(f"  {i:>2}. [{r['total_score']:>3}/100] {bar} {exact} {r['keyword']}")
        if r["top_suggestions"]:
            print(f"      Related: {', '.join(r['top_suggestions'][:3])}")

    # Tier breakdown
    print(f"\n{'TIERS':=^70}")
    tiers = {
        "A (60+)": [r for r in ranked if r["total_score"] >= 60],
        "B (30-59)": [r for r in ranked if 30 <= r["total_score"] < 60],
        "C (1-29)": [r for r in ranked if 1 <= r["total_score"] < 30],
        "D (0)": [r for r in ranked if r["total_score"] == 0],
    }
    for tier, items in tiers.items():
        kws = ", ".join(r["keyword"] for r in items) if items else "none"
        print(f"  {tier}: {len(items)} — {kws[:100]}")

    # Discover opportunities
    print(f"\n{'NEW OPPORTUNITIES':=^70}")
    opportunities = discover_opportunities(keyword_names)

    if opportunities:
        print(f"\n  Found {len(opportunities)} potential keywords:\n")
        for opp in opportunities[:40]:
            print(f"    → {opp}")
        if len(opportunities) > 40:
            print(f"    ... and {len(opportunities) - 40} more")
    else:
        print("  No new opportunities found.")

    print(f"\n{'='*70}\n")

    return ranked, opportunities
