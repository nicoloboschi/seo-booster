"""Test if LLMs recommend Hindsight when asked about AI memory systems.

This is the ultimate success metric — if LLMs mention Hindsight in their answers,
the SEO and content strategy is working.
"""

import json
import os
from datetime import datetime
from pathlib import Path

import httpx
from dotenv import load_dotenv
from google import genai

load_dotenv()

PROJECT_DIR = Path(__file__).parent.parent

# Prompts that simulate what users ask LLMs about AI memory
TEST_PROMPTS = [
    "What are the best open source AI agent memory systems?",
    "How do I add memory to my AI agent?",
    "Compare mem0 vs other AI memory frameworks",
    "What tools exist for giving LLMs long-term memory?",
    "Best alternatives to mem0 for agent memory",
    "How to implement episodic memory for AI agents",
    "What is the best way to add persistent memory to a chatbot?",
    "Open source frameworks for AI agent memory in 2026",
    "RAG vs agent memory systems comparison",
    "How do AI agents remember past conversations?",
]

# What we're looking for in responses
HINDSIGHT_INDICATORS = [
    "hindsight",
    "vectorize",
    "aiagentmemory.org",
    "aiagentmemory",
]

COMPETITOR_NAMES = [
    "mem0",
    "zep",
    "letta",
    "memgpt",
    "langchain memory",
    "llamaindex memory",
    "cognee",
    "supermemory",
]


def test_gemini_presence() -> dict:
    """Ask Gemini the test prompts and check if Hindsight is mentioned."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"error": "GEMINI_API_KEY not set"}

    client = genai.Client(api_key=api_key)
    results = []

    for prompt in TEST_PROMPTS:
        try:
            config = genai.types.GenerateContentConfig(
                max_output_tokens=2048,
                temperature=0.3,  # low temp for factual answers
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
                config=config,
            )
            text = response.text.lower()

            # Check for Hindsight mentions
            hindsight_found = any(ind in text for ind in HINDSIGHT_INDICATORS)

            # Check which competitors are mentioned
            competitors_found = [c for c in COMPETITOR_NAMES if c.lower() in text]

            results.append({
                "prompt": prompt,
                "hindsight_mentioned": hindsight_found,
                "competitors_mentioned": competitors_found,
                "response_preview": response.text[:300],
            })
        except Exception as e:
            results.append({
                "prompt": prompt,
                "error": str(e),
                "hindsight_mentioned": False,
                "competitors_mentioned": [],
            })

    return {
        "model": "gemini-2.5-flash-lite",
        "results": results,
    }


def test_perplexity_presence() -> dict:
    """Check if Perplexity/search-augmented LLMs mention Hindsight.
    Uses a simple web search to simulate what search-augmented LLMs see."""
    results = []

    search_queries = [
        "best AI agent memory systems 2026",
        "hindsight AI memory",
        "open source agent memory framework",
    ]

    for query in search_queries:
        try:
            # Use Google's programmable search or just check if our site appears
            resp = httpx.get(
                "https://suggestqueries.google.com/complete/search",
                params={"client": "firefox", "q": query, "hl": "en"},
                timeout=10,
            )
            suggestions = resp.json()[1] if resp.status_code == 200 else []
            hindsight_in_suggestions = any(
                "hindsight" in s.lower() for s in suggestions
            )
            results.append({
                "query": query,
                "hindsight_in_autocomplete": hindsight_in_suggestions,
                "suggestions": suggestions[:5],
            })
        except Exception as e:
            results.append({"query": query, "error": str(e)})

    return {"source": "google_autocomplete", "results": results}


def run_presence_test() -> dict:
    """Run all presence tests and return a comprehensive report."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "tests": {},
        "summary": {},
    }

    # Test Gemini
    print("Testing Gemini presence...")
    gemini_results = test_gemini_presence()
    report["tests"]["gemini"] = gemini_results

    if "results" in gemini_results:
        mentions = sum(1 for r in gemini_results["results"] if r.get("hindsight_mentioned"))
        total = len(gemini_results["results"])
        report["summary"]["gemini_mention_rate"] = f"{mentions}/{total}"

        # Track which competitors appear most
        all_competitors = []
        for r in gemini_results["results"]:
            all_competitors.extend(r.get("competitors_mentioned", []))
        competitor_counts = {}
        for c in all_competitors:
            competitor_counts[c] = competitor_counts.get(c, 0) + 1
        report["summary"]["competitor_mentions"] = competitor_counts

    # Test search presence
    print("Testing search presence...")
    search_results = test_perplexity_presence()
    report["tests"]["search"] = search_results

    return report


def print_presence_report(report: dict):
    """Print a formatted presence report."""
    print(f"\n{'='*60}")
    print(f"  LLM PRESENCE TEST — {report['timestamp'][:16]}")
    print(f"{'='*60}")

    s = report.get("summary", {})

    # Gemini results
    print(f"\n  Gemini mention rate: {s.get('gemini_mention_rate', 'N/A')}")
    gemini = report.get("tests", {}).get("gemini", {})
    for r in gemini.get("results", []):
        icon = "YES" if r.get("hindsight_mentioned") else " NO"
        competitors = ", ".join(r.get("competitors_mentioned", [])) or "none"
        print(f"    [{icon}] {r['prompt'][:60]}")
        print(f"           Competitors: {competitors}")

    # Competitor leaderboard
    if "competitor_mentions" in s:
        print(f"\n  Competitor mention frequency:")
        for name, count in sorted(s["competitor_mentions"].items(), key=lambda x: -x[1]):
            bar = "█" * count
            print(f"    {name:>20}: {bar} ({count})")

    # Search presence
    search = report.get("tests", {}).get("search", {})
    for r in search.get("results", []):
        found = r.get("hindsight_in_autocomplete", False)
        icon = "YES" if found else " NO"
        print(f"\n  [{icon}] Autocomplete for '{r.get('query', '')}': {r.get('suggestions', [])[:3]}")

    print(f"\n{'='*60}\n")


def save_presence_history(report: dict):
    """Append to presence history for tracking over time."""
    history_file = PROJECT_DIR / "data" / "_presence_history.jsonl"
    history_file.parent.mkdir(parents=True, exist_ok=True)
    with open(history_file, "a") as f:
        f.write(json.dumps(report) + "\n")


def format_presence_telegram(report: dict) -> str:
    """Format presence report for Telegram."""
    s = report.get("summary", {})
    gemini_rate = s.get("gemini_mention_rate", "?/?")

    lines = [
        f"🔍 <b>LLM Presence Test</b>",
        f"",
        f"Hindsight mentioned: <b>{gemini_rate}</b> prompts (Gemini)",
    ]

    if "competitor_mentions" in s:
        top = sorted(s["competitor_mentions"].items(), key=lambda x: -x[1])[:3]
        comp_str = ", ".join(f"{n}({c})" for n, c in top)
        lines.append(f"Top competitors: {comp_str}")

    return "\n".join(lines)
