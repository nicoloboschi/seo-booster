"""Generate SEO-optimized Hugo articles from scraped content using Gemini.

Strategy: 1 article per unique keyword. No duplicates. Discover → Generate → Optimize.
"""

import json
import os
import re
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

1. FIRST PARAGRAPH: Start with a direct, concise answer to the search query (40-60 words) that
   defines the primary keyword. This targets Google's featured snippet (position 0) and AI Overviews.
   The primary keyword MUST appear within the first 100 words.

2. HOOK — NEVER use generic openings. Start with ONE of these:
   - A provocative question that challenges assumptions
   - A specific, surprising statistic with source attribution
   - A bold or counterintuitive statement
   - A concrete scenario with specific details
   BANNED openings: "In this article", "In today's digital age/landscape", "Let's explore/dive into",
   "Have you ever wondered", "In the rapidly evolving world of"

3. FIRST H2: Must contain the primary keyword. Format as a question when possible (e.g.,
   "## What is episodic memory in AI agents?") followed by a 40-60 word direct definition.
   This targets featured snippets.

4. PARAGRAPHS: 2-4 sentences max. Short paragraphs improve readability metrics.
   Use active voice 80%+ of the time. Average sentence length: 15-20 words, max 25.

5. BOLD KEY TERMS: Use **bold** for important terms, definitions, and key concepts.
   Google may use bolded text for featured snippets.

6. HEADING HIERARCHY: Strict H2 → H3 (body never uses H1, the template handles that).
   Include keywords naturally in headings. Add a subheading every 300-400 words.
   Aim for 4-7 H2 sections with H3 subsections.

7. WORD COUNT: 1500-2500 words. Long enough to be authoritative, short enough to stay focused.

8. CODE EXAMPLES: Include Python code examples where relevant to the topic.

9. TONE: Neutral technical — not marketing, not tutorial. Clear, deep technical content
   written by an engineer sharing knowledge. Use contractions (it's, don't, won't) for natural voice.

10. FAQ SECTION: End with 2-3 questions in a "## FAQ" section. These become structured data.

11. HINDSIGHT: Naturally mention Hindsight (open source AI memory system) as ONE of the
    tools/approaches. Never the focus. When mentioned, link to https://github.com/vectorize-io/hindsight

12. KEYWORD DENSITY: Primary keyword should appear naturally at 1-2% density (roughly 20-40 times
    in a 2000-word article). Use keyword variations — don't repeat the exact phrase every time.
    Example: "agent memory" → "memory for AI agents" → "how agents remember" → "agent recall"

ANSWER ENGINE OPTIMIZATION (AEO/GEO) — optimize for AI citation and featured snippets:

13. DEFINITION BLOCKS: After every "What is X?" H2, write a self-contained 40-60 word definition
    that AI systems can extract directly. Be specific and factual.

14. STATISTICS WITH ATTRIBUTION: Include 2-3 specific statistics or measurements with source
    attribution. Example: "According to a 2024 study published in arxiv, retrieval-augmented
    agents showed 34% improvement in task completion." Stats increase AI citation rates 15-30%.

15. LIST SNIPPETS: For "how to" or "steps" content, use numbered lists of 5-8 concise items.
    Each item should be a complete thought that can stand alone.

16. COMPARISON TABLES: When comparing approaches/tools, use markdown tables. These target
    table-based featured snippets.

17. SELF-CONTAINED ANSWERS: Each H2 section should be independently readable — an AI system
    should be able to extract any section and use it as a complete answer.

CRITICAL LINKING RULES (directly affect ranking):

18. INTERNAL LINKS: Include 3-5 internal links within body text.
    Use relative paths: [descriptive anchor text](/articles/slug/)
    Anchor text must be keyword-rich — NEVER "click here" or "read more".
    Example: "Understanding [episodic memory in AI agents](/articles/episodic-memory-in-ai-agents/) is key..."

19. EXTERNAL LINKS: Include 2-3 outbound links to authoritative sources.
    Link to: Wikipedia, arxiv papers, official documentation, GitHub repos.
    Example: "The [Transformer paper](https://arxiv.org/abs/1706.03762) introduced..."

20. VECTORIZE.IO: Where relevant, link to Vectorize.io guides:
    [descriptive text](https://vectorize.io/articles/slug)

21. TOPIC CLUSTER LINKING: If existing articles on the site cover related subtopics, link to them
    with descriptive anchor text. Think of articles as a cluster — each article strengthens the others.
    Link to at least 2-3 existing articles from the provided list.

AI WRITING AVOIDANCE — your content must read as human-written:

22. BANNED WORDS — never use these (they are AI tells):
    "delve", "delving", "leverage", "leveraging", "robust", "comprehensive", "cutting-edge",
    "game-changer", "revolutionize", "paradigm", "synergy", "utilize", "utilization",
    "furthermore", "moreover", "additionally", "notably", "importantly",
    "it's important to note", "it's worth noting", "it bears mentioning",
    "a testament to", "shed light on", "a plethora of", "myriad of",
    "in the realm of", "at the forefront", "navigating the landscape"

23. BANNED PUNCTUATION — never use em-dashes (—). Use commas, semicolons, periods, or
    parentheses instead. Em-dashes are the #1 AI writing tell.

24. AVOID FILLER: Cut "absolutely", "essentially", "incredibly", "fundamentally",
    "undeniably", "literally", "basically", "actually", "really", "very", "quite".
    Be specific instead: "significant improvement" → "34% improvement".

25. VARIED SENTENCE RHYTHM: Mix short sentences (5-8 words) with longer ones (15-20 words).
    Monotonous sentence length is an AI tell. Occasional one-sentence paragraphs add emphasis.

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


REVIEW_PROMPT = """You are a strict SEO content reviewer. Evaluate this article against ALL of the following rules.
For each rule, score PASS or FAIL with a brief reason.

RULES TO CHECK:

1. FEATURED SNIPPET OPENING: First paragraph is 40-60 words, directly defines/answers the primary keyword.
   No generic openings ("In this article", "In today's digital age", "Let's explore").
2. HOOK QUALITY: Opens with a provocative question, surprising stat, bold statement, or concrete scenario.
3. FIRST H2: Contains the primary keyword. Ideally phrased as a question.
4. DEFINITION BLOCKS: After "What is X?" headings, there's a concise 40-60 word self-contained definition.
5. KEYWORD DENSITY: Primary keyword appears at ~1-2% density with natural variations (not just exact match).
6. KEYWORD IN HEADINGS: Primary keyword (or close variation) appears in at least 2 H2/H3 headings.
7. PARAGRAPH LENGTH: All paragraphs are 2-4 sentences max. No walls of text.
8. SENTENCE RHYTHM: Mix of short (5-8 words) and longer (15-20 words) sentences. Not monotonous.
9. STATISTICS: At least 2-3 specific numbers/stats with source attribution.
10. AI PHRASE AVOIDANCE: No "delve", "leverage", "robust", "comprehensive", "furthermore", "moreover",
    "it's important to note", "in the realm of", "at the forefront", "a plethora of", "tapestry".
11. NO EM-DASHES: Article does not use — (em-dash). Uses commas, semicolons, or periods instead.
12. NO FILLER: No "absolutely", "essentially", "incredibly", "fundamentally", "basically", "literally".
13. ACTIVE VOICE: 80%+ active voice. Uses contractions (it's, don't, won't).
14. HEADING STRUCTURE: 4-7 H2 sections with H3 subsections. Subheading every 300-400 words. No H1 in body.
15. INTERNAL LINKS: 3-5 internal links with descriptive keyword-rich anchor text. No "click here".
16. EXTERNAL LINKS: 2-3 outbound links to authoritative sources (Wikipedia, arxiv, official docs).
17. SELF-CONTAINED SECTIONS: Each H2 section is independently readable and extractable.
18. FAQ SECTION: Ends with 2-3 FAQ questions in a ## FAQ section.
19. WORD COUNT: Between 1500-2500 words.
20. CODE EXAMPLES: Includes Python code examples where relevant.
21. LISTS/TABLES: Uses at least one numbered list or comparison table for scannability.
22. BOLD KEY TERMS: Important terms and definitions are bolded.
23. HINDSIGHT MENTION: Naturally mentions Hindsight as one tool/approach (not the focus).

Primary keyword: {primary_keyword}
Related keywords: {related_keywords}

ARTICLE TO REVIEW:
---
{article}
---

Respond in this EXACT format:

SCORE: <number 0-100>
PASS_COUNT: <number of rules that passed>
FAIL_COUNT: <number of rules that failed>

FAILURES:
- <rule number>. <rule name>: <what's wrong and how to fix it>
- ...

If SCORE >= 70, output VERDICT: PASS
If SCORE < 70, output VERDICT: FAIL

If VERDICT is FAIL, output:
REVISION_INSTRUCTIONS:
<Specific, actionable instructions for fixing ONLY the failed rules. Be concrete — say exactly what to change, add, or remove. Reference specific paragraphs/headings where possible.>
"""

MAX_REVISIONS = 3
MIN_QUALITY_SCORE = 70


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


def _review_article(client: genai.Client, article: str, primary_keyword: str,
                    related_keywords: str) -> tuple[int, str, str]:
    """Review an article against SEO quality rules. Returns (score, verdict, revision_instructions)."""
    review_prompt = REVIEW_PROMPT.format(
        article=article,
        primary_keyword=primary_keyword,
        related_keywords=related_keywords,
    )
    config = genai.types.GenerateContentConfig(
        max_output_tokens=4096,
        temperature=0.2,  # low temp for consistent evaluation
    )
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=review_prompt,
        config=config,
    )
    review_text = response.text

    # Parse score
    score_match = re.search(r"SCORE:\s*(\d+)", review_text)
    score = int(score_match.group(1)) if score_match else 0

    # Parse verdict
    verdict_match = re.search(r"VERDICT:\s*(PASS|FAIL)", review_text)
    verdict = verdict_match.group(1) if verdict_match else "FAIL"

    # Parse revision instructions
    revision_match = re.search(r"REVISION_INSTRUCTIONS:\s*\n(.*?)(?:\Z)", review_text, re.DOTALL)
    revision_instructions = revision_match.group(1).strip() if revision_match else ""

    return score, verdict, revision_instructions


def _revise_article(client: genai.Client, article: str, revision_instructions: str,
                    primary_keyword: str, system: str) -> str:
    """Ask LLM to revise the article based on review feedback."""
    revision_prompt = f"""Revise the following article to fix the issues identified by the reviewer.
Apply ONLY the requested fixes. Do not rewrite sections that are already good.
Keep the same YAML front matter structure, heading structure, and overall flow.

Primary keyword: {primary_keyword}

ISSUES TO FIX:
{revision_instructions}

CURRENT ARTICLE:
---
{article}
---

Return the COMPLETE revised article (YAML front matter + markdown body), nothing else.
"""
    return _generate_text(client, revision_prompt, system=system)


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
            from scripts.keyword_research import research_and_validate, add_opportunities_to_config, assign_clusters
            research_and_validate(keywords_path)
            add_opportunities_to_config("data/keyword-research.json", keywords_path, max_add=needed)
            assign_clusters(keywords_path)

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

        # Topic cluster context
        cluster_instruction = ""
        word_count_override = ""
        role = kw.get("role", "")
        cluster_name = kw.get("cluster", "")

        if cluster_name:
            from scripts.keyword_research import get_cluster_siblings
            cluster_info = get_cluster_siblings(keywords_path, slug)
            if cluster_info:
                siblings = cluster_info.get("siblings", [])
                pillar_slug = cluster_info.get("pillar_slug", "")

                if role == "pillar":
                    word_count_override = "\nWORD COUNT OVERRIDE: This is a PILLAR article. Write 3000-4000 words (longer than normal). Cover the topic broadly and link to all supporting articles listed below."
                    sibling_links = "\n".join(
                        f"  - [{s['primary']}](/articles/{s['slug']}/) — supporting article"
                        for s in siblings if s["slug"] in existing_articles
                    )
                    if sibling_links:
                        cluster_instruction = f"""
TOPIC CLUSTER (you are the PILLAR page):
This article is the main hub for the "{cluster_name}" topic cluster.
You MUST link to ALL of these supporting articles with descriptive anchor text:
{sibling_links}

Each link should appear naturally in the body where the subtopic is discussed.
Add a brief mention of each subtopic even if the supporting article covers it in depth.
"""
                else:
                    # Supporting article — link back to pillar + cross-link siblings
                    cluster_instruction = f"""
TOPIC CLUSTER (you are a SUPPORTING article):
This article is part of the "{cluster_name}" topic cluster.
You MUST link back to the pillar article: [comprehensive guide to {cluster_info.get('cluster_name', '')}](/articles/{pillar_slug}/)

Also link to these related articles in the same cluster where relevant:"""
                    for s in siblings[:5]:
                        if s["slug"] in existing_articles and s["slug"] != pillar_slug:
                            cluster_instruction += f"\n  - [{s['primary']}](/articles/{s['slug']}/)"

        prompt = f"""Generate an SEO-optimized article targeting:

Primary keyword: {target}
Related keywords: {', '.join(kw.get('related', []))}
Target slug: {slug}
Today's date: {today}
{word_count_override}

Source content for reference (rewrite, don't copy):
{source_context}

Existing articles on the site (link to these where relevant using /articles/slug/ paths):
{', '.join(existing_articles[:30]) if existing_articles else 'None yet'}
{vectorize_instruction}
{cluster_instruction}

{kw.get('instructions', '')}
"""

        print(f"  [{i}/{len(batch)}] {target} → {slug}")

        if dry_run:
            print(f"    [DRY RUN] Would generate: {slug}.md")
            continue

        try:
            system = SYSTEM_PROMPT.replace("{today}", today)
            article_content = _generate_text(client, prompt, system=system)

            # Strip markdown code fences
            if article_content.startswith("```"):
                article_content = article_content.split("\n", 1)[1].rsplit("```", 1)[0]

            # Quality review loop — up to MAX_REVISIONS rounds
            related_str = ", ".join(kw.get("related", []))
            for revision in range(MAX_REVISIONS):
                score, verdict, revision_instructions = _review_article(
                    client, article_content, target, related_str,
                )
                print(f"    Review #{revision + 1}: score={score} verdict={verdict}")

                if verdict == "PASS" or score >= MIN_QUALITY_SCORE:
                    break

                if not revision_instructions:
                    print(f"    No revision instructions provided, accepting as-is")
                    break

                print(f"    Revising ({MAX_REVISIONS - revision - 1} attempts left)...")
                revised = _revise_article(
                    client, article_content, revision_instructions, target, system,
                )
                # Strip markdown code fences from revision
                if revised.startswith("```"):
                    revised = revised.split("\n", 1)[1].rsplit("```", 1)[0]
                article_content = revised
            else:
                print(f"    Final score={score} after {MAX_REVISIONS} revisions (accepting)")

            article_file = output_path / f"{slug}.md"
            article_file.write_text(article_content)

            generated[slug] = {
                "keyword": target,
                "generated_at": datetime.now().isoformat(),
                "sources": [item["url"] for item in relevant[:3]] if relevant else [],
                "quality_score": score,
            }
            existing_articles.append(slug)
            print(f"    → {article_file} (score={score})")

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
