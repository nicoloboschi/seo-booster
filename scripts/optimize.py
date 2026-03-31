"""Apply AI-driven optimizations to underperforming articles using Gemini."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

load_dotenv()


OPTIMIZE_PROMPT = """You are an SEO optimizer. Given an article and its performance data,
suggest and apply specific improvements.

Rules:
- Only change what's needed — don't rewrite the whole article
- Focus on: title, meta description, H2/H3 headings, keyword density, FAQ section
- Keep the same tone and style
- Preserve all internal links
- Return the FULL updated article (front matter + body), nothing else

Performance data:
{stats}

Current article:
{article}

What to optimize:
{instructions}
"""


def _get_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set. Add it to .env")
    return genai.Client(api_key=api_key)


def apply_optimizations(report_path: str, content_dir: str):
    """Read SEO report and optimize underperforming articles."""
    report_file = Path(report_path)
    if not report_file.exists():
        print(f"No report found at {report_path}. Run 'seo-booster stats' first.")
        return

    data = json.loads(report_file.read_text())
    content_path = Path(content_dir)
    client = _get_client()

    pages = data.get("pages", [])
    page_queries = data.get("page_queries", [])

    optimized_count = 0

    for page in pages:
        url = page["key"]
        slug = url.rstrip("/").split("/")[-1]
        article_file = content_path / f"{slug}.md"

        if not article_file.exists():
            continue

        instructions = []

        if page["impressions"] > 100 and page["ctr"] < 3.0:
            instructions.append(
                f"Title/description optimization: {page['impressions']} impressions "
                f"but only {page['ctr']}% CTR. Make the title more compelling and "
                f"ensure the meta description includes the primary keyword."
            )

        if 4 <= page["position"] <= 15:
            related_queries = [pq for pq in page_queries if pq["page"] == url]
            query_list = ", ".join(pq["query"] for pq in related_queries[:5])
            instructions.append(
                f"Content depth: Position {page['position']}. "
                f"Ranking queries: {query_list}. "
                f"Add more depth around these terms, add an FAQ entry, "
                f"ensure keywords appear in H2/H3 headings."
            )

        if not instructions:
            continue

        article_content = article_file.read_text()
        stats_summary = json.dumps(page, indent=2)

        print(f"Optimizing: {slug}")
        print(f"  Issues: {'; '.join(instructions)}")

        try:
            config = genai.types.GenerateContentConfig(
                max_output_tokens=8192,
                temperature=0.3,
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=OPTIMIZE_PROMPT.format(
                    stats=stats_summary,
                    article=article_content,
                    instructions="\n".join(instructions),
                ),
                config=config,
            )

            optimized = response.text
            if optimized.startswith("```"):
                optimized = optimized.split("\n", 1)[1].rsplit("```", 1)[0]

            backup_file = content_path / f"{slug}.md.bak"
            backup_file.write_text(article_content)

            article_file.write_text(optimized)

            # Run post-processor to fix YAML quoting, AI scrubbing, etc.
            from scripts.postprocess import postprocess_article
            pp_fixes = postprocess_article(article_file)
            if pp_fixes:
                print(f"    Post-processed: {len(pp_fixes)} fixes")

            optimized_count += 1
            print(f"  → Optimized and saved. Backup at {backup_file}")

        except Exception as e:
            print(f"  ✗ Failed: {e}")

    print(f"\nOptimized {optimized_count} articles.")
