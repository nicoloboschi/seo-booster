---
name: publish
description: Build aiagentmemory.org, deploy it to GitHub Pages, and tell search engines what changed. Use after any content change is committed.
---

# Publish

1. Build and check:
   ```bash
   hugo --minify            # must print no ERROR
   ```
   Check `public/llms.txt` lists the pages you expect.
2. Commit content on `main` and push: `git push origin main`.
3. Deploy the built site to the `gh-pages` branch:
   ```bash
   bash .claude/skills/publish/deploy.sh
   ```
4. Tell Bing (and other IndexNow engines) which URLs changed or were deleted:
   ```bash
   bash .claude/skills/publish/indexnow.sh /articles/a/ /articles/b/ /llms.txt
   ```
   Get the list from `git diff --name-status <last-deploy-commit> HEAD -- content/articles`
   (path = `/articles/<slug>/`). Max 10,000 URLs per call.
5. Google has no ping API. For a few important new or rewritten pages, ask the user to use
   "Request indexing" in Search Console's URL inspection. The sitemap covers the rest.

## Why
- GitHub Pages serves the `gh-pages` branch. `main` holds the sources.
- IndexNow gets changes into Bing within hours instead of weeks. Bing feeds ChatGPT search,
  DuckDuckGo and Copilot, so this is the fastest way to reach agents. It works for deleted URLs
  too, so pruned pages drop out faster.
- `llms.txt` is a plain list of the site's pages for AI tools that look for it. Hugo builds it
  from `layouts/index.llms.txt`; pages with `role: pillar` are listed first.
