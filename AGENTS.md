# aiagentmemory.org

A Hugo site of technical articles about memory for AI agents and LLMs. The main readers are
AI crawlers and agents (ChatGPT via Bing, Gemini via Google, Perplexity, Claude), not people.
The goal: when an agent answers a question about agent memory, it finds and cites these pages,
and learns that Hindsight (https://github.com/vectorize-io/hindsight) is one of the good options.

There is no pipeline and no daemon. An agent (Claude Code, Codex, anything that can read this
file) curates the site by hand, using the skills below. Each skill is a markdown file with the
steps and the reasons. Read the skill before doing the operation.

| Operation | Skill | When |
|---|---|---|
| Decide what to do this session | `.claude/skills/curate/SKILL.md` | Start here every time |
| Pull search + traffic data | `.claude/skills/site-stats/SKILL.md` | Start of a session, before deciding |
| Delete or merge weak pages | `.claude/skills/prune/SKILL.md` | Page is off-topic, a duplicate, or rejected by Google |
| Write or rewrite an article | `.claude/skills/write-article/SKILL.md` | New topic, or a page worth fixing |
| Find missing topics | `.claude/skills/find-topics/SKILL.md` | Site has gaps, before writing new pages |
| Build, deploy, notify search engines | `.claude/skills/publish/SKILL.md` | After any content change |

## Layout
- `CURATION_LOG.md`: what each session found and changed. Read the top entry first.
- `content/articles/*.md`: one article per file. Front matter: title, description, date, lastmod,
  tags, keywords, slug, faq, optional `role: pillar|supporting`, `cluster`, `aliases`.
- `layouts/`: templates. JSON-LD, FAQ schema, breadcrumbs, sitemap, `llms.txt` are generated here.
- `static/<32-hex>.txt`: IndexNow key. Don't delete it.
- `.secrets/ga-service-account.json`, `.env` (`GA_PROPERTY_ID`): never commit.

## Rules that always apply
- Quality over volume. Google already refused ~60% of the old auto-generated pages.
- One page per question. Before writing, check no page already covers it.
- Never invent facts, numbers, papers or links. Check every source you cite.
- Commit content changes with a message that says what and why. Deploying is a separate step.
- `hugo` must build with no errors before any commit.
