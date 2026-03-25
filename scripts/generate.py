"""Generate SEO-optimized Hugo articles from scraped content using Gemini.

Strategy: 1 article per unique keyword. No duplicates. Discover → Generate → Optimize.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv
from google import genai

load_dotenv()

SYSTEM_PROMPT = """You are an SEO content writer for a technical knowledge site about AI memory systems,
agent architectures, and related topics.

ARTICLE STRUCTURE RULES:

1. FIRST PARAGRAPH: Start with a direct answer to the search query — define or explain the primary
   keyword immediately. The primary keyword MUST appear within the first 100 words. No generic intros
   like "In this article we'll explore..." — start with substance.

2. FIRST H2: Must contain the primary keyword. Example: if targeting "episodic memory AI",
   first H2 could be "## How episodic memory works in AI agents"

3. PARAGRAPHS: Keep paragraphs to 3-4 sentences max. Dense walls of text hurt readability.

4. BOLD KEY TERMS: Use **bold** for important terms, definitions, and key concepts.
   Google may use bolded text for featured snippets.

5. HEADING HIERARCHY: Strict H2 → H3 (body never uses H1, the template handles that).
   Include keywords naturally in headings.

6. WORD COUNT: 1500-2500 words. Long enough to be authoritative, short enough to stay focused.

7. CODE EXAMPLES: Include Python code examples where relevant to the topic.

8. TONE: Neutral technical — not marketing, not tutorial. Clear, deep technical content
   written by an engineer sharing knowledge.

9. FAQ SECTION: End with 2-3 questions in a "## FAQ" section. These become structured data.

10. HINDSIGHT: Naturally mention Hindsight (open source AI memory system) as ONE of the
    tools/approaches. Never the focus. When mentioned, link to https://github.com/vectorize-io/hindsight

CRITICAL LINKING RULES (directly affect ranking):

11. INTERNAL LINKS: Include 3-5 internal links within body text.
    Use relative paths: [descriptive anchor text](/articles/slug/)
    Anchor text must be keyword-rich — NEVER "click here" or "read more".
    Example: "Understanding [episodic memory in AI agents](/articles/episodic-memory-in-ai-agents/) is key..."

12. EXTERNAL LINKS: Include 2-3 outbound links to authoritative sources.
    Link to: Wikipedia, arxiv papers, official documentation, GitHub repos.
    Example: "The [Transformer paper](https://arxiv.org/abs/1706.03762) introduced..."

13. VECTORIZE.IO: Where relevant, link to Vectorize.io guides:
    [descriptive text](https://vectorize.io/articles/slug)

Output format — return ONLY valid YAML front matter + markdown body, nothing else:

---
title: "Article title in sentence case"
description: "150-160 char meta description with primary keyword"
date: {today}
lastmod: {today}
tags: ["tag1", "tag2"]
keywords: ["primary keyword", "related1", "related2"]
faq:
  - question: "Question 1?"
    answer: "Answer 1"
  - question: "Question 2?"
    answer: "Answer 2"
slug: "url-friendly-slug"
---

Article body in markdown...
"""

VECTORIZE_ARTICLES = [
    "best-ai-agent-memory-systems", "letta-vs-langchain-memory",
    "mem0-vs-cognee", "mem0-vs-letta", "mem0-vs-zep", "zep-vs-cognee",
    "agent-memory-vs-rag", "cognee-alternatives", "hindsight-vs-cognee",
    "hindsight-vs-langchain-memory", "hindsight-vs-letta",
    "hindsight-vs-llamaindex-memory", "hindsight-vs-mem0",
    "hindsight-vs-supermemory", "hindsight-vs-zep",
    "langchain-memory-alternatives", "letta-alternatives",
    "llamaindex-memory-alternatives", "mem0-alternatives",
    "supermemory-alternatives", "zep-alternatives",
]


def _get_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set. Add it to .env")
    return genai.Client(api_key=api_key)


def _generate_text(client: genai.Client, prompt: str, system: str = "") -> str:
    """Call Gemini and return the text response."""
    config = genai.types.GenerateContentConfig(
        system_instruction=system if system else None,
        max_output_tokens=8192,
        temperature=0.7,
    )
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt,
        config=config,
    )
    return response.text


def generate_articles(input_dir: str, output_dir: str, keywords_path: str, dry_run: bool,
                      count: int = 10, auto_expand: bool = False):
    """Generate 1 article per unique keyword. Skip keywords that already have an article.
    Keywords are manually curated — no auto-expansion."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    keywords_file = Path(keywords_path)
    if keywords_file.exists():
        with open(keywords_file) as f:
            keywords_config = yaml.safe_load(f)
    else:
        keywords_config = {"keywords": []}

    # Read scraped items for source context
    scraped_items = []
    for f in sorted(input_path.glob("*.json")):
        if f.name.startswith("_"):
            continue
        scraped_items.append(json.loads(f.read_text()))

    # Track generated articles
    generated_file = output_path / "_generated.json"
    generated = json.loads(generated_file.read_text()) if generated_file.exists() else {}

    client = _get_client()
    today = datetime.now().strftime("%Y-%m-%d")

    all_keywords = list(keywords_config.get("keywords", []))

    # Filter to keywords we haven't generated yet
    pending = []
    for kw in all_keywords:
        slug = kw.get("slug", kw["primary"].lower().replace(" ", "-"))
        if slug not in generated:
            pending.append(kw)

    # Auto-expand if we're running low on pending keywords
    if auto_expand and len(pending) < count:
        needed = max(count * 2, 20) - len(pending)
        existing_slugs = list(generated.keys()) + [
            kw.get("slug", kw["primary"].lower().replace(" ", "-")) for kw in all_keywords
        ]
        print(f"Running keyword research to find {needed} new targets...")
        try:
            from scripts.keyword_research import research_and_validate, add_opportunities_to_config
            research_and_validate(keywords_path)
            add_opportunities_to_config("data/keyword-research.json", keywords_path, max_add=needed)

            # Reload keywords after research added new ones
            with open(keywords_file) as f:
                keywords_config = yaml.safe_load(f)
            all_keywords = list(keywords_config.get("keywords", []))
            pending = [kw for kw in all_keywords
                       if kw.get("slug", kw["primary"].lower().replace(" ", "-")) not in generated]
        except Exception as e:
            print(f"  Keyword research failed: {e}")

    # Take up to count pending keywords
    batch = pending[:count]

    if not batch:
        print("All keywords have articles. Run 'seo-booster research --add-opportunities' to discover more.")
        return

    # Collect existing article slugs for internal linking
    existing_articles = list(generated.keys())
    for md in output_path.glob("*.md"):
        if md.name.startswith("_"):
            continue
        if md.stem not in existing_articles:
            existing_articles.append(md.stem)

    print(f"\nGenerating {len(batch)} articles ({len(generated)} existing, {len(pending)} pending)...\n")

    for i, kw in enumerate(batch, 1):
        target = kw["primary"]
        slug = kw.get("slug", target.lower().replace(" ", "-"))

        # Find relevant scraped content
        relevant = _find_relevant(scraped_items, target, kw.get("related", []))
        if relevant:
            source_context = "\n\n---\n\n".join(
                f"Source: {item['source']}\nTitle: {item['title']}\n\n{item['content'][:3000]}"
                for item in relevant[:3]
            )
        else:
            source_context = "No specific source content. Generate based on your knowledge."

        # Find relevant Vectorize articles to link to
        relevant_vectorize = [a for a in VECTORIZE_ARTICLES
                              if any(k in a for k in target.lower().split() if len(k) > 3)]
        vectorize_instruction = ""
        if relevant_vectorize:
            links = ", ".join(f"https://vectorize.io/articles/{a}" for a in relevant_vectorize[:3])
            vectorize_instruction = f"\nRelevant Vectorize.io guides to link to: {links}"

        prompt = f"""Generate an SEO-optimized article targeting:

Primary keyword: {target}
Related keywords: {', '.join(kw.get('related', []))}
Target slug: {slug}
Today's date: {today}

Source content for reference (rewrite, don't copy):
{source_context}

Existing articles on the site (link to these where relevant using /articles/slug/ paths):
{', '.join(existing_articles[:30]) if existing_articles else 'None yet'}
{vectorize_instruction}

{kw.get('instructions', '')}
"""

        print(f"  [{i}/{len(batch)}] {target} → {slug}")

        if dry_run:
            print(f"    [DRY RUN] Would generate: {slug}.md")
            continue

        try:
            article_content = _generate_text(
                client, prompt,
                system=SYSTEM_PROMPT.replace("{today}", today),
            )

            # Strip markdown code fences
            if article_content.startswith("```"):
                article_content = article_content.split("\n", 1)[1].rsplit("```", 1)[0]

            article_file = output_path / f"{slug}.md"
            article_file.write_text(article_content)

            generated[slug] = {
                "keyword": target,
                "generated_at": datetime.now().isoformat(),
                "sources": [item["url"] for item in relevant[:3]] if relevant else [],
            }
            existing_articles.append(slug)
            print(f"    → {article_file}")

        except Exception as e:
            print(f"    ✗ {e}")

        if i < len(batch):
            time.sleep(1)

    generated_file.write_text(json.dumps(generated, indent=2))

    # Post-process to fix front matter
    if not dry_run:
        print("\nPost-processing...")
        from scripts.postprocess import postprocess_all
        postprocess_all(output_dir)

    print(f"\nDone. {len(generated)} total articles. {len(pending) - len(batch)} keywords remaining.")


def _find_relevant(items: list[dict], primary: str, related: list[str]) -> list[dict]:
    """Find scraped items relevant to the target keywords."""
    keywords = [primary.lower()] + [r.lower() for r in related]
    scored = []
    for item in items:
        text = f"{item.get('title', '')} {item.get('content', '')}".lower()
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scored.append((score, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored]
