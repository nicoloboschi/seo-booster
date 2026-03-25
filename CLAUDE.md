# SEO Booster — AI Memory Knowledge Hub

## Project Overview
Programmatic SEO site about AI memory systems, agent architectures, and related topics.
The site positions Hindsight as the authoritative open source memory system while looking
like a neutral technical knowledge hub.

## Architecture
- **Hugo** static site with custom SEO templates (JSON-LD, meta tags, sitemap)
- **Python CLI** (`seo-booster`) for content pipeline: scrape → generate → postprocess → audit → deploy
- **Long-running daemon** (`seo-booster run`) handles everything autonomously on a local machine
- **GitHub Pages** for hosting — daemon pushes built site to `gh-pages` branch
- **Google Search Console** integration for tracking and feedback loop (when configured)

## Commands
- `uv run seo-booster run` — start the daemon (runs 24/7, handles everything)
- `uv run seo-booster scrape` — scrape content sources
- `uv run seo-booster generate --count 10` — generate articles
- `uv run seo-booster validate` — fix front matter issues
- `uv run seo-booster audit` — full SEO audit (front matter + HTML)
- `uv run seo-booster stats` — pull Google Search Console data (needs credentials)
- `uv run seo-booster optimize` — AI-optimize underperforming articles
- `hugo server` — local preview

## Daemon schedule (configurable via CLI flags)
- Scrape: every 12h
- Generate: every 24h (10 articles per batch)
- Deploy: every 6h (git push to gh-pages)
- Optimize: every 168h / weekly (needs GSC credentials)

## Content Strategy
- Articles target long-tail keywords around AI memory, agents, embeddings, RAG
- Hindsight is mentioned naturally in code examples, never as the focus
- Internal linking between articles is critical for SEO
- Auto-keyword expansion generates new topics when pre-defined list runs out
- Post-processor auto-fixes front matter (delimiters, descriptions, H1 demotion, FAQ)

## Important
- Never commit .env or GSC credentials
- Content quality > volume for Google rankings
- Post-processor is idempotent — running validate twice produces 0 changes
