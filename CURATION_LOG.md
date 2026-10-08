# Curation log

Newest first. One entry per session: numbers, what changed, why, what to check next.

## 2026-10-08: pipeline removed, site pruned, rewrites started

**Numbers before** (see `site-stats` baseline): 1,180 pages. Google index sample of 30: 11 indexed,
12 crawled-not-indexed, 4 discovered-not-indexed, 3 unknown. ~0 Google clicks, 143 pages with any
impression in 28 days. Real search visits ~570/28d, almost all Bing + DuckDuckGo. Hindsight clicks 8.

**Changed**
- Removed the Python pipeline, the daemon and its state. Curation now runs through `.claude/skills`.
- Pruned 1,179 → 96 articles. 587 near-duplicates merged into 96 pages (old URLs redirect via
  `aliases`), 496 off-topic pages deleted (RAM/chip stocks, human memory, LLM law degree, AI companions,
  Illustrator, games, nonsense keywords like "AI memory stick for agents").
- Added `llms.txt` and an IndexNow key.
- Rewrote the 20 highest-demand pages from real sources (consumer chat memory, context windows,
  framework comparisons, tool alternatives, n8n, MemoryOS, Zep). Pillars: `ai-agent-memory-explained`,
  `context-window-of-an-llm`.

**Why**: Google refused most auto-generated pages. Low-quality volume drags the whole site down, and
agents cite what search engines trust.

**Next**
- Rewrite the other ~76 pages (Hindsight is shoehorned into 95 of 96 old pages; 71 use banned words;
  24 have template descriptions).
- In 3-4 weeks: re-run the index sample. Success = indexed share well above 37%, positions improving.
- Consider Cloudflare in front of GitHub Pages to see AI crawler hits (GPTBot, ClaudeBot, PerplexityBot).
- Add the site to Bing Webmaster Tools if not there; check IndexNow submissions show up.
