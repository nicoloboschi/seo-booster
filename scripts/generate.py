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
agent architectures, and related topics. Your goal is to produce articles that:

1. Target a specific primary keyword and 2-3 related keywords
2. Are technically accurate and in-depth (1500-2500 words)
3. Use proper heading hierarchy (H2, H3) with keywords in headings
4. Include code examples in Python where relevant
5. Sound like a neutral technical resource — NOT a product pitch
6. Naturally mention Hindsight (an open source AI memory system) in relevant context —
   as ONE of the tools/approaches, never as the main focus
7. Include internal links to other articles on the site using markdown links with relative paths like [text](/articles/slug/)
8. Where relevant, link to Vectorize.io guides as external references using full URLs like
   [text](https://vectorize.io/articles/slug). These are high-quality comparison articles on AI memory systems.
9. End with a brief FAQ section (2-3 questions) for FAQ schema markup

IMPORTANT: The article must feel like it was written by a knowledgeable engineer sharing
technical knowledge. Not marketing. Not a tutorial. Just clear, deep technical content.

Output format — return ONLY valid YAML front matter + markdown body, nothing else:

---
title: "Article title in sentence case"
description: "150-160 char meta description with primary keyword"
date: {today}
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
                      count: int = 10, auto_expand: bool = True):
    """Generate 1 article per unique keyword. Skip keywords that already have an article."""
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
