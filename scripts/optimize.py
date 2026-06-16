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


def _clean_llm_article(raw: str) -> str | None:
    """Normalize an LLM article response into a single clean front-matter + body doc.

    Handles common Gemini failure modes that previously corrupted files:
    - leading code fences (```markdown ... ```)
    - a chatty preamble before the real article ("Here's the updated article...")
    - a stray ' ---' delimiter jammed onto the end of a front-matter value line
    - a duplicate front-matter block emitted after a preamble

    Returns the cleaned document, or None if it can't be made well-formed.
    """
    import re

    text = raw.strip()

    # Strip surrounding code fences if present.
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        text = text.rsplit("```", 1)[0]
        text = text.strip()

    # If the model emitted a chatty preamble followed by a fresh front-matter
    # block, drop everything up to that block (keep the LAST front-matter block).
    preamble = re.search(r"\n*.*updated article.*\n+(?=---\n)", text, re.IGNORECASE)
    if preamble:
        text = text[preamble.end():]

    # Must start with a front-matter opener.
    if not text.startswith("---\n"):
        return None

    # Remove any ' ---' jammed onto the end of a line *inside* the front matter
    # (delimiter accidentally appended to a value). Only operate before the
    # real closing delimiter.
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    fm = re.sub(r" ---(?=\n)", "", text[:end])
    body = text[end:]
    text = fm + body

    return text


def _validate_front_matter(content: str) -> bool:
    """Check that content has exactly one valid YAML front-matter block, a
    non-empty body, and no duplicate/leftover front-matter delimiters."""
    import re
    import yaml
    fm_match = re.match(r"^---\n(.*?\n)---\n", content, re.DOTALL)
    if not fm_match:
        return False
    try:
        fm = yaml.safe_load(fm_match.group(1))
        if not isinstance(fm, dict):
            return False
    except yaml.YAMLError:
        return False
    body = content[fm_match.end():]
    # Body must have real content...
    if len(body.strip()) < 200:
        return False
    # ...and must not contain a duplicate front-matter block (a '---' line
    # followed by front-matter keys) or a chatty LLM preamble. A lone '---'
    # used as a markdown horizontal rule is fine.
    if re.search(r"^---\s*\n+(title|description|date|slug|tags|keywords|faq)\s*:",
                 body, re.MULTILINE):
        return False
    if "updated article" in body.lower()[:500]:
        return False
    return True


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

        # AEO strategy: CTR 0 is expected — we target AI agents, not human clicks.
        # Optimize for position improvement instead of CTR.
        if page["impressions"] > 100 and page["position"] > 10:
            instructions.append(
                f"Position optimization: {page['impressions']} impressions "
                f"but position {page['position']}. Strengthen content depth, "
                f"add definition blocks and structured data for AI extraction, "
                f"ensure primary keyword in first 100 words and first H2."
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

            optimized = _clean_llm_article(response.text or "")

            # Validate YAML front matter before writing
            if not optimized or not _validate_front_matter(optimized):
                print(f"  ✗ Skipped: LLM returned invalid/unsafe article output")
                continue

            backup_file = content_path / f"{slug}.md.bak"
            backup_file.write_text(article_content)

            article_file.write_text(optimized)

            # Run post-processor to fix YAML quoting, AI scrubbing, etc.
            from scripts.postprocess import postprocess_article
            pp_fixes = postprocess_article(article_file)
            if pp_fixes:
                print(f"    Post-processed: {len(pp_fixes)} fixes")

            # Validate again after post-processing
            final_content = article_file.read_text()
            if not _validate_front_matter(final_content):
                print(f"  ✗ Rolled back: post-processing broke YAML")
                article_file.write_text(article_content)
                continue

            optimized_count += 1
            print(f"  → Optimized and saved. Backup at {backup_file}")

        except Exception as e:
            print(f"  ✗ Failed: {e}")

    print(f"\nOptimized {optimized_count} articles.")
