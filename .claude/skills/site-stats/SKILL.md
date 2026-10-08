---
name: site-stats
description: Pull Google Search Console, index status and GA4 numbers for aiagentmemory.org and read them correctly. Use before deciding what to change, or when asked how the site is doing.
---

# Site stats

```bash
uv run .claude/skills/site-stats/stats.py              # 28 days, 30-URL index sample
uv run .claude/skills/site-stats/stats.py --days 90 --pages --inspect 0   # every page with impressions
```

## Auth
- Search Console uses your Google login. If it fails:
  `gcloud auth application-default login --scopes=https://www.googleapis.com/auth/webmasters.readonly,https://www.googleapis.com/auth/cloud-platform`
  then `gcloud auth application-default set-quota-project seo-booster-491310`.
- GA4 uses `.secrets/ga-service-account.json` and `GA_PROPERTY_ID` in `.env`.
- Bing Webmaster Tools has no script here. Check it in the browser if needed.

## How to read the numbers
- **Index sample** is the most important line. "Crawled - currently not indexed" means Google
  read the page and judged it not worth keeping. If that share grows, quality is the problem,
  not discovery.
- **Impressions and position** matter more than clicks. Agents that search Google (Gemini, AI
  Overviews) use the same index and ranking. Position under 10 = likely cited; over 50 = invisible.
- **GA4 cannot see AI crawlers.** They don't run JavaScript. GA shows humans plus scrapers.
- In GA, ignore "Direct" sessions with ~0 engagement (mostly a Singapore scraper). Use
  **engaged sessions** and the **Bing / DuckDuckGo** rows. Bing feeds ChatGPT search, so Bing
  traffic is a stand-in for "ChatGPT can find us".
- **Hindsight link clicks** = the only direct sign the site does its job with humans.

## Baseline (2026-10-08, before pruning)
- 1,180 pages in sitemap. Index sample of 30: 11 indexed, 12 crawled-not-indexed,
  4 discovered-not-indexed, 3 unknown.
- Google: ~0 clicks/week, ~300-1,000 impressions/week, 143 pages with any impression, avg pos ~50-90.
- GA 28d: organic 570 sessions (268 engaged; Bing 170, DDG 70, Google 2). Hindsight clicks 8.
