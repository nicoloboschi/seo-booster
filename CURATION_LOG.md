# Curation log

Newest first. One entry per session: numbers, what changed, why, what to check next.

## 2026-10-08 (reps run 1): Mem0 vs Hindsight

**Numbers** (GSC 2026-09-07..10-05, still mostly pre-prune data): 1 click, 1,199 impressions, avg pos
43.8, 148 pages with impressions. GA4 28d: organic 593 sessions (286 engaged; Bing 183, DDG 75,
Google 2), AI Assistant 5. Hindsight link clicks 8. No index sample this run (`--inspect 0`; last
sample is today's baseline).

**Changed**
- New: `mem0-vs-hindsight`. "mem0 vs hindsight" is a Google autocomplete phrase, no page covered it.
  Sources: both READMEs, Mem0 docs/pricing, Mem0's own compare page (mem0.ai/compare/mem0-vs-hindsight)
  and benchmarks.hindsight.vectorize.io. Benchmark scores agree across both vendors; token counts are
  Mem0's measurements, labeled so. Skipped vectorize.io/articles/hindsight-vs-mem0 as a source: it is
  dated March 2026 and has stale claims (old Mem0 49.0% LongMemEval, star counts).
- Linked the new page from `what-is-mem0-ai` (also turned plain-text Mem0 vs Letta/Cognee into links)
  and `ai-memory-hindsight`. No other rewrites: all pages were rewritten today, wait for data.

**Other hot-topic candidates seen** (not written): "Agents don't need memory, they need documentation"
(HN 380 pts, opinion piece; could feed a section in `ai-coding-agent-memory`), "mem0 vs supermemory",
"mem0 vs honcho", "mem0 vs graphiti", "agent memory mcp", AML-memory/agent-memory-leaderboard (1.2k stars).

**Next**: the GSC top-pages list still shows pruned URLs (ai-memory-dram etc.); check they now redirect
or 404 and drop out over the next weeks. Index sample due ~2026-10-15.

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
- Rewrote all 95 remaining pages from primary sources (docs, READMEs, pricing pages, papers), checked
  2026-10-08. Merged `langchain-chatbot-with-memory-github` into `chatbot-with-memory-langgraph`.
  Pillars: `ai-agent-memory-explained`, `context-window-of-an-llm`. Hindsight now on 61/95 pages, always
  as one option among others (was 95/96, shoehorned).
- New homepage (guides + full article list), robots.txt with sitemap, `find-topics/hot.py`.
- Scheduled daily curation with reps: `~/.reps/jobs/aiagentmemory/JOB.md` (one new article max per run).

**Why**: Google refused most auto-generated pages. Low-quality volume drags the whole site down, and
agents cite what search engines trust.

**Next**
- Facts to re-check when they age: Hermes holographic plugin leaves core on 2026-10-15; vendor pricing
  (Zep, Mem0, Supermemory, Vertex, AgentCore); context window tables ("as of October 2026").
- Hindsight integrations that are behind: `hindsight-crewai` pins crewai<1.10 (ExternalMemory removed);
  the Dify plugin isn't on the Dify Marketplace.
- In 3-4 weeks: re-run the index sample. Success = indexed share well above 37%, positions improving.
- Consider Cloudflare in front of GitHub Pages to see AI crawler hits (GPTBot, ClaudeBot, PerplexityBot).
- Add the site to Bing Webmaster Tools if not there; check IndexNow submissions show up.
