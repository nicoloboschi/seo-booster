---
name: curate
description: Run one curation session on aiagentmemory.org - read the data, pick the few changes that matter most, do them, publish. Use when asked to "work on the site", "curate", "what next", or on a schedule.
---

# Curate

One session = a small number of good changes, not a batch of new pages.

## Steps
1. Run `site-stats`. Compare with the last entry in `CURATION_LOG.md`.
2. Pick at most 3-5 actions, in this order of value:
   1. **Fix what is broken**: build errors, 404s from internal links, pages Google flagged.
   2. **Rewrite pages that are close**: Google position 5-30, or pages agents read, but the
      page is thin or vague. Small rewrite, big payoff.
   3. **Prune**: off-topic or duplicate pages still live.
   4. **New page**: only for a real gap found by `find-topics`.
3. Do them with the matching skill (`prune`, `write-article`).
4. `publish`.
5. Append to `CURATION_LOG.md`: date, key numbers, what changed, why, what to check next time.

## Why
- The old daemon wrote ~10 pages a day. Google read most of them and refused to index them.
  Volume made the site look like spam, which hurts every page, including the good ones.
- Agents cite pages that search engines trust. A few strong pages beat many weak ones.
- The log is the memory between sessions. Without it each session re-decides the same things.
- Changes take 2-6 weeks to show in Search Console. Don't undo a change because the numbers
  didn't move after a few days.
