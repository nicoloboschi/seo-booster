---
name: find-topics
description: Find questions about agent/LLM memory that people and agents ask but aiagentmemory.org doesn't answer well. Use before writing new pages.
---

# Find topics

## Sources, best first
1. **Search Console queries** (`site-stats --pages`, and the query list). A query with impressions
   but position > 20, and no page clearly about it, is a proven gap.
2. **Google Autocomplete**, for real phrasing:
   `curl -s "https://suggestqueries.google.com/complete/search?client=firefox&q=agent+memory+" | python3 -m json.tool`
   Try prefixes: "agent memory", "llm memory", "mem0 vs", "zep vs", "letta", "long term memory llm", "<tool> alternative".
3. **New things**: new memory tools, releases, papers (arxiv cs.CL / cs.AI "agent memory"),
   frameworks adding memory (LangGraph, CrewAI, OpenAI Agents SDK, Claude). First good page on a new
   thing ranks easily.
4. **Comparisons and alternatives** ("X vs Y", "X alternatives"): these pages already rank best here
   (zep-alternatives, gbrain-alternatives, llm-memory-comparison).

## Filter
- On topic: memory for AI agents and LLMs (types, architectures, tools, context windows, retrieval
  as memory, evaluation). Nothing else.
- Not already covered. If a page is close, rewrite it instead of adding a new one.
- Specific (3-5 words) beats broad.

Write the shortlist into `CURATION_LOG.md` with the source of each idea, then use `write-article`.

## Why
- Search Console shows what Google already connects to the site, so pages there rank fastest.
- Autocomplete is how people actually phrase the question; agents rephrase user questions in similar words.
- The old pipeline generated keywords and ran out of good ones, then drifted off-topic (RAM,
  games, Illustrator). The topic filter stops that.
