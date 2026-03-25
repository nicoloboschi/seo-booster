"""Track SERP positions for target keywords — where do we rank vs competitors?

Uses Gemini with Google Search grounding to check what sites appear
for our target keywords, simulating what users see in search results.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from google import genai

load_dotenv()

PROJECT_DIR = Path(__file__).parent.parent

# Our domains
OUR_DOMAINS = ["aiagentmemory.org", "vectorize.io"]

# Competitor domains
COMPETITOR_DOMAINS = {
    "mem0": ["mem0.ai", "github.com/mem0ai"],
    "zep": ["getzep.com", "github.com/getzep"],
    "letta": ["letta.com", "github.com/letta-ai"],
    "cognee": ["cognee.ai", "github.com/topoteretes/cognee"],
    "langchain": ["python.langchain.com", "langchain.com"],
    "llamaindex": ["llamaindex.ai", "docs.llamaindex.ai"],
}

# Keywords to track (subset of our most important targets)
TRACKED_KEYWORDS = [
    "ai agent memory",
    "best ai memory system",
    "ai agent memory framework",
    "mem0 alternative",
    "RAG vs agent memory",
    "how to add memory to ai agent",
    "open source ai memory",
    "long term memory ai agent",
    "ai that remembers conversations",
    "episodic memory ai",
]


def check_serp_position(client: genai.Client, keyword: str) -> dict:
    """Ask Gemini with search grounding to find top results for a keyword."""
    prompt = f"""Search for "{keyword}" and list the TOP 10 most relevant websites/pages
that appear in the results. For each result, give me:
1. The domain/URL
2. The title of the page
3. A one-line description

Format as a numbered list. Only include actual search results, not ads."""

    try:
        config = genai.types.GenerateContentConfig(
            max_output_tokens=2048,
            temperature=0.1,
            tools=[genai.types.Tool(google_search=genai.types.GoogleSearch())],
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config=config,
        )
        text = response.text.lower()

        # Check our position
        our_position = None
        for domain in OUR_DOMAINS:
            if domain in text:
                # Find approximate position by counting results before our mention
                lines = text.split("\n")
                for i, line in enumerate(lines):
                    if domain in line:
                        # Count numbered items before this line
                        position = sum(1 for l in lines[:i+1]
                                       if l.strip() and (l.strip()[0].isdigit() or l.strip().startswith("-")))
                        our_position = position
                        break
                if our_position:
                    break

        # Check competitor positions
        competitor_positions = {}
        for name, domains in COMPETITOR_DOMAINS.items():
            for domain in domains:
                if domain in text:
                    lines = text.split("\n")
                    for i, line in enumerate(lines):
                        if domain in line:
                            position = sum(1 for l in lines[:i+1]
                                           if l.strip() and (l.strip()[0].isdigit() or l.strip().startswith("-")))
                            competitor_positions[name] = position
                            break
                    break

        # Extract grounding sources
        grounding_sources = []
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            metadata = getattr(candidate, 'grounding_metadata', None)
            if metadata:
                chunks = getattr(metadata, 'grounding_chunks', []) or []
                for chunk in chunks:
                    web = getattr(chunk, 'web', None)
                    if web:
                        grounding_sources.append(getattr(web, 'uri', ''))

        # Check if our domain is in grounding sources
        our_domain_in_sources = any(
            any(d in src for d in OUR_DOMAINS) for src in grounding_sources
        )

        return {
            "keyword": keyword,
            "our_position": our_position,
            "our_in_sources": our_domain_in_sources,
            "competitor_positions": competitor_positions,
            "response_preview": response.text[:500],
        }

    except Exception as e:
        return {
            "keyword": keyword,
            "error": str(e),
            "our_position": None,
            "competitor_positions": {},
        }


def run_serp_check() -> dict:
    """Check SERP positions for all tracked keywords."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"error": "GEMINI_API_KEY not set"}

    client = genai.Client(api_key=api_key)
    results = []

    for kw in TRACKED_KEYWORDS:
        print(f"  Checking: {kw}")
        result = check_serp_position(client, kw)
        results.append(result)
        time.sleep(1)  # Rate limit

    # Summary
    keywords_we_rank = sum(1 for r in results if r.get("our_position"))
    keywords_in_sources = sum(1 for r in results if r.get("our_in_sources"))
    avg_position = None
    positions = [r["our_position"] for r in results if r.get("our_position")]
    if positions:
        avg_position = round(sum(positions) / len(positions), 1)

    # Competitor summary
    competitor_avg = {}
    for r in results:
        for name, pos in r.get("competitor_positions", {}).items():
            if name not in competitor_avg:
                competitor_avg[name] = []
            competitor_avg[name].append(pos)

    competitor_summary = {}
    for name, positions in competitor_avg.items():
        competitor_summary[name] = {
            "avg_position": round(sum(positions) / len(positions), 1),
            "keywords_ranking": len(positions),
        }

    report = {
        "timestamp": datetime.now().isoformat(),
        "results": results,
        "summary": {
            "keywords_tracked": len(TRACKED_KEYWORDS),
            "keywords_we_rank": keywords_we_rank,
            "keywords_in_sources": keywords_in_sources,
            "our_avg_position": avg_position,
            "competitors": competitor_summary,
        },
    }

    return report


def print_serp_report(report: dict):
    """Print formatted SERP report."""
    s = report.get("summary", {})

    print(f"\n{'='*60}")
    print(f"  SERP POSITION TRACKER — {report['timestamp'][:16]}")
    print(f"{'='*60}")

    print(f"\n  We rank for: {s.get('keywords_we_rank', 0)}/{s.get('keywords_tracked', 0)} keywords")
    print(f"  In search sources: {s.get('keywords_in_sources', 0)}/{s.get('keywords_tracked', 0)}")
    if s.get("our_avg_position"):
        print(f"  Our avg position: {s['our_avg_position']}")

    # Per-keyword results
    print(f"\n  Per-keyword positions:")
    for r in report.get("results", []):
        our_pos = r.get("our_position")
        pos_str = f"#{our_pos}" if our_pos else "  --"
        in_src = " (cited)" if r.get("our_in_sources") else ""
        comps = ", ".join(f"{n}:#{p}" for n, p in r.get("competitor_positions", {}).items())
        print(f"    [{pos_str:>4}]{in_src} {r['keyword']}")
        if comps:
            print(f"           vs {comps}")

    # Competitor leaderboard
    competitors = s.get("competitors", {})
    if competitors:
        print(f"\n  Competitor leaderboard:")
        sorted_comps = sorted(competitors.items(), key=lambda x: -x[1]["keywords_ranking"])
        for name, data in sorted_comps:
            bar = "█" * data["keywords_ranking"]
            print(f"    {name:>15}: {bar} ({data['keywords_ranking']}/{s['keywords_tracked']} keywords, avg #{data['avg_position']})")

    print(f"\n{'='*60}\n")


def save_serp_history(report: dict):
    """Save to history for trend tracking."""
    history_file = PROJECT_DIR / "data" / "_serp_history.jsonl"
    history_file.parent.mkdir(parents=True, exist_ok=True)
    with open(history_file, "a") as f:
        f.write(json.dumps(report) + "\n")


def format_serp_telegram(report: dict) -> str:
    """Format SERP report for Telegram."""
    s = report.get("summary", {})

    lines = [
        f"📊 <b>SERP Position Tracker</b>",
        f"",
        f"We rank: <b>{s.get('keywords_we_rank', 0)}/{s.get('keywords_tracked', 0)}</b> keywords",
        f"Cited in search: <b>{s.get('keywords_in_sources', 0)}/{s.get('keywords_tracked', 0)}</b>",
    ]

    if s.get("our_avg_position"):
        lines.append(f"Avg position: <b>#{s['our_avg_position']}</b>")

    competitors = s.get("competitors", {})
    if competitors:
        top = sorted(competitors.items(), key=lambda x: -x[1]["keywords_ranking"])[:3]
        comp_lines = [f"{n}: {d['keywords_ranking']}kw avg#{d['avg_position']}" for n, d in top]
        lines.append(f"\nTop competitors: {', '.join(comp_lines)}")

    return "\n".join(lines)
