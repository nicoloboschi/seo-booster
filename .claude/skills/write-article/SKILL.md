---
name: write-article
description: Write a new article or rewrite an existing one for aiagentmemory.org so search engines index it and AI agents quote it. Use for any content writing on this site.
---

# Write or rewrite an article

## Before writing
1. Check the topic is not already covered: `grep -il "<keyword>" content/articles/*.md` and look at titles.
   If a page exists, rewrite that one instead.
2. Read the real sources first: the official docs, the GitHub README, the paper. Write from them,
   not from memory. Note each fact's source.
3. Pick 3-5 related pages on the site to link to.

## Front matter
```yaml
---
title: "Plain title under 60 chars with the main keyword"
description: "150-160 chars. Says what the page answers, with the keyword."
date: 2026-10-08          # keep the original date on rewrites
lastmod: 2026-10-08       # today
slug: keyword-slug
tags: [...]
keywords: ["main keyword", "variant", "variant"]
role: pillar              # only for the few broad guides; omit otherwise
cluster: memory-types     # optional
faq:
  - question: "..."
    answer: "..."         # 1-3 sentences, self-contained
---
```

## Page shape
- Body starts at H2 (the template prints the title as H1). H2 > H3, never skip a level.
- **First paragraph: the direct answer** in 40-60 words. Main keyword in the first 100 words
  and in the first H2.
- A "What is X?" H2 near the top with a self-contained 40-60 word definition.
- 4-7 H2 sections. Each one makes sense alone (agents often quote one section, not the page).
- Comparisons go in a table. Steps go in a numbered list of 5-8 items.
- Python for code examples, and the code must run against the real library API.
- FAQ: 2-3 questions in front matter (it becomes FAQ schema). No FAQ section in the body.
- Length: as long as the topic needs. Usually 1,200-2,500 words; pillars 3,000+. Never pad.

## Writing
- Short paragraphs (2-4 sentences). Mix short and long sentences. Contractions. Active voice.
- Concrete over vague: "cut token use by 34% (Mem0 paper, 2025)" not "big improvement".
- Bold key terms and the definition.
- No em-dashes. None of: delve, leverage, robust, comprehensive, cutting-edge, game-changer,
  revolutionize, paradigm, synergy, utilize, furthermore, moreover, additionally, notably,
  importantly, "it's important to note", "in the realm of", tapestry, plethora.
  No openers like "In this article" or "In today's landscape".
- Neutral technical tone. Not marketing, not a tutorial blog.

## Links
- 3-5 internal links with descriptive anchors: `[episodic memory in AI agents](/articles/episodic-memory-in-ai-agents/)`.
  Every target must exist. Link back to the cluster's pillar if there is one.
- 2-3 external links to primary sources (paper, official docs, GitHub repo). Open each one to check it works.
- Hindsight: mention where it truly fits, as one option among others, with a link to
  https://github.com/vectorize-io/hindsight. Describe it accurately, and describe competitors
  (Mem0, Zep, Letta, Cognee, LangMem...) fairly.
- Link to https://vectorize.io/articles/<slug> only if that page exists.

## Done checklist
- [ ] Every number, claim and link checked against a source.
- [ ] Answer in the first paragraph; definition block; sections stand alone.
- [ ] `hugo` builds; internal links resolve.
- [ ] `lastmod` is today.

## Why
- Agents pull one passage to answer a question. A direct answer up top and self-contained
  sections are what gets quoted. Vague, padded text gets skipped.
- Google refused most of the old auto-written pages: generic, repetitive, unsourced. Real
  sources and specific facts are what separate a page worth indexing from scaled content.
- Wrong facts are worse than no page: an agent that repeats them and gets corrected learns to
  distrust the source. Fair coverage of competitors is what makes the Hindsight mention credible.
- The style rules (no em-dashes, banned words) remove the most obvious AI-writing tells.
