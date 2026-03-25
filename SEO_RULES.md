# SEO Rules for AI Agent Memory Knowledge Hub

This file defines all SEO rules that the content generation pipeline follows.
These rules are encoded in the system prompt (`scripts/generate.py`) and enforced
by the post-processor (`scripts/postprocess.py`) and audit (`scripts/seo_audit.py`).

## Article Structure

| Rule | Requirement | Why |
|------|-------------|-----|
| First 100 words | Must contain primary keyword | Google weighs early keyword placement heavily |
| First H2 | Must contain primary keyword | Signals topic relevance to crawlers |
| Opening paragraph | Direct answer to the search query | Targets featured snippets (position 0) |
| Intro style | No generic "In this article..." | Google and users penalize filler |
| Paragraph length | Max 3-4 sentences | Readability affects bounce rate → affects ranking |
| Bold text | Bold key terms and definitions | May appear in featured snippets |
| Word count | 1500-2500 words | Authoritative but focused |
| Heading hierarchy | H1 → H2 → H3, never skip | Crawlers use this for content structure |
| FAQ section | 2-3 questions at the end | Feeds JSON-LD FAQ schema for rich results |

## Linking

| Rule | Requirement | Why |
|------|-------------|-----|
| Internal links | 3-5 per article, in body text | Distributes page authority, helps crawlers |
| External links | 2-3 to authoritative sources | Signals trust (arxiv, Wikipedia, official docs) |
| Anchor text | Descriptive, keyword-rich | "click here" is worthless; "episodic memory in AI agents" is gold |
| Vectorize.io | Link where relevant | Backlinks to vectorize.io/articles/* |
| Hindsight | Link to GitHub when mentioned | https://github.com/vectorize-io/hindsight |

## Front Matter (YAML)

```yaml
---
title: "Sentence case title under 60 chars"
description: "150-160 char meta description with primary keyword"
date: 2026-03-25
lastmod: 2026-03-25          # content freshness signal
tags: ["tag1", "tag2"]
keywords: ["primary", "related1", "related2"]
faq:
  - question: "What is X?"
    answer: "Direct answer..."
  - question: "Why does X matter?"
    answer: "Because..."
slug: "url-friendly-slug"
---
```

## Technical SEO (enforced by templates + post-processor)

| Element | Status | Implementation |
|---------|--------|----------------|
| Title tag | Auto, <60 chars | `head-seo.html` truncates |
| Meta description | Auto, 150-160 chars | Post-processor extends if short |
| Canonical URL | Auto | Hugo permalink |
| Open Graph | Auto | `og:title`, `og:description`, `og:type`, `og:url` |
| Twitter Card | Auto | `summary_large_image` |
| JSON-LD Article | Auto | From front matter |
| JSON-LD FAQ | Auto | From `faq` field in front matter |
| Breadcrumb schema | Auto | On every article page |
| Single H1 | Enforced | Post-processor demotes body H1 → H2 |
| Sitemap | Auto | Hugo generates `/sitemap.xml` |
| robots.txt | Auto | Hugo generates |
| Favicon | Auto | SVG linked in head |
| Viewport | Auto | Meta tag in head |
| lang="en" | Auto | On `<html>` tag |
| OG image | Auto | 5 SVG images, deterministic per article |
| Google Analytics | Auto | GA4 tag when ID is set |
| No JavaScript | By design | Pure HTML+CSS = fast crawling |

## Keyword Strategy

| Rule | Detail |
|------|--------|
| Source | Google Autocomplete (real search data, not guesses) |
| Type | Long-tail (3-5 words) |
| Scope | AI memory, agents, embeddings, RAG, context windows |
| Coverage | 1 article per keyword, never duplicate |
| Expansion | Auto-discover every 6h via research command |
| Validation | Must appear in autocomplete results |

## Content Rules

| Rule | Detail |
|------|--------|
| Tone | Neutral technical — not marketing, not tutorial |
| Hindsight | Mentioned naturally as one tool, never the focus |
| Code | Python examples where relevant |
| Updates | Optimize underperforming articles via GSC data |
| No duplication | 1 article per keyword prevents cannibalization |

## Monitoring

| What | How | Frequency |
|------|-----|-----------|
| SEO audit | `seo-booster audit` | Every 50 articles |
| Health check | `seo-booster health` | Hourly (Telegram report) |
| GSC stats | `seo-booster stats` | Hourly |
| Keyword research | `seo-booster research` | Every 6h |
| Site uptime | Health check HTTP 200 | Hourly |
| Content freshness | Scrape age check | Hourly |
