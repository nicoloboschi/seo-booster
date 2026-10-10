# Curation log

Newest first. One entry per session: numbers, what changed, why, what to check next.

## 2026-10-10 (reps run 3): Mem0 vs Honcho

**Numbers** (GSC 2026-09-09..10-07): 1 click, 1,138 impressions, avg pos 43.2, 147 pages with
impressions. Slight dip in impressions, likely the pruned URLs fading. GA4 28d: organic 565 sessions
(282 engaged; Bing 184, DDG 69, Google 2), AI Assistant 6 (chatgpt.com 2). Hindsight link clicks 8.
No index sample (`--inspect 0`). hot.py autocomplete worked for all seeds this time.

**Changed**
- New: `mem0-vs-honcho`. "mem0 vs honcho" is a "mem0 vs" autocomplete with no page. Sources: both
  READMEs (stars via GitHub API: 66,930 / 7,550; Honcho server 3.3.0 in pyproject, honcho-ai 2.5.1),
  honcho.dev/evals (LongMemEval-S 90.4, LoCoMo 89.9, BEAM 1M 0.618 / 10M 0.409), Mem0 README +
  mem0.ai/research (94.4 / 92.5 / BEAM 64.1, 48.6). mem0.ai/compare/mem0-vs-honcho exists but has no
  content, so no cross-vendor numbers. Page notes the BEAM scale mismatch (0-100 vs 0-1).
- Linked it from `honcho-llm-memory` (also turned plain-text "Mem0 alternatives" into a link, dropped
  its "honcho vs mem0" keyword) and `what-is-mem0-ai` (also added the missing Mem0 vs Supermemory link).

**Other candidates seen**: mem0 vs graphiti / mempalace, "best memory for hermes agent", "agent memory
skill", "agent memory claude code", HN "Agents don't need memory, they need documentation" (388 pts).
GSC: n8n queries still ~24 impressions at pos ~40; "oracleagentmemory" 7 impressions at pos 37 (check
if there's a real Oracle product worth a page).

**Next**: index sample due ~2026-10-15. Pruned URLs (ai-memory-dram, ai-memory-chip-companies,
/tags/character.ai/) still in GSC top pages.

## 2026-10-09 (reps run 2): Mem0 vs Supermemory

**Numbers** (GSC 2026-09-08..10-06): 1 click, 1,205 impressions, avg pos 44.5, 148 pages with
impressions. Basically flat vs yesterday, as expected. GA4 28d: organic 577 sessions (283 engaged;
Bing 184, DDG 70, Google 2), AI Assistant 6. Hindsight link clicks 8. No index sample (`--inspect 0`).
Google autocomplete for "ai memory" returned HTTP 500 in hot.py; the other seeds worked.

**Changed**
- New: `mem0-vs-supermemory`. "mem0 vs supermemory" is the first "mem0 vs" autocomplete; no page
  covered it. Sources: both READMEs (stars via GitHub API: 66,883 / 31,168), pricing pages, Mem0's
  compare page (mem0.ai/compare/mem0-vs-supermemory: Mem0 94.4 vs Supermemory 85.2 LongMemEval) and
  Supermemory's own LongMemEval report (85.2 = Gemini 3 Pro row; 84.6 with GPT-5; README says 95%
  Recall@15). Page explains the metric mismatch rather than picking a winner.
- Linked it from `supermemory-alternatives` (also turned plain-text "what is Mem0" into a link, and
  dropped its "supermemory vs mem0" keyword so the pages don't compete) and the Supermemory explainer.

**Other candidates seen**: mem0 vs honcho / graphiti / mempalace, "agent memory skill", "agent memory
claude code", HN "Agents don't need memory, they need documentation" (384 pts), "Jevmem" (HN 62 pts).
GSC: "n8n ai agent memory" + "ai agent memory n8n" ~26 impressions at pos ~40; the n8n page sits at
pos 60. Watch it; rewrite if it doesn't climb after the rewrite settles.

**Next**: index sample due ~2026-10-15. Pruned URLs (ai-memory-dram, ai-memory-chip-companies,
/tags/character.ai/) still show in GSC top pages; check they drop out.

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
