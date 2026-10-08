---
name: prune
description: Delete or merge weak pages on aiagentmemory.org - off-topic, duplicates, thin pages Google refuses to index. Use when cleaning up the site or when site-stats shows pages that hurt more than help.
---

# Prune

## Decide per page
| Case | Action |
|---|---|
| Off-topic (not memory for AI agents/LLMs: PC RAM, DRAM chips, games, Illustrator, human memory, dementia care, AI companions, "is AI intelligent") | **Delete**. No redirect. |
| Same question as another page (e.g. five "context window limits" pages) | **Merge**: keep the best one, move any unique useful part into it, add the old URL to its `aliases`, delete the rest. |
| On-topic, unique, but thin or wrong | Keep, mark for `write-article` rewrite. |
| On-topic, unique, decent | Keep. |

Pick the page to keep by: real Google impressions (`site-stats --pages`) > indexed > better slug > better content.

## How
1. Delete: `git rm content/articles/<slug>.md`.
2. Merge: in the kept page's front matter:
   ```yaml
   aliases:
     - /articles/old-slug/
   ```
   Hugo writes a redirect page at the old URL, so links and agents that saved it still land somewhere useful.
3. Fix internal links that point to deleted pages:
   `grep -rln "/articles/<slug>/" content/` and point them to the kept page or remove the link.
4. `hugo` must build clean. Check: `grep -rho "](/articles/[^)]*)" content | sort -u` against existing slugs + aliases.
5. Commit with the list of what went and why. Then `publish`, and send deleted + merged URLs to IndexNow.

## Why
- Google judges the whole site. Hundreds of weak or off-topic pages pull down the good ones
  ("helpful content" and "scaled content" signals work site-wide).
- Off-topic pages get a few human visits but teach agents nothing about agent memory and
  dilute what the site is "about". No redirect: there is no matching page, and redirecting to
  an unrelated page is treated as a soft 404 anyway.
- Duplicates split ranking between pages that compete with each other. One page wins more
  than five pages each ranking at position 60. Aliases keep the old URLs working.
