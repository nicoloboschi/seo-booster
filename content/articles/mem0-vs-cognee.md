---
title: "Mem0 vs Cognee: User Memory vs Knowledge Graph"
description: "Mem0 vs Cognee compared (Oct 2026): fact extraction vs knowledge graphs, open-source graph memory, local models, APIs, pricing and when to use each."
date: 2026-06-16
lastmod: 2026-10-08
slug: mem0-vs-cognee
cluster: agent-memory
tags:
- Mem0
- Cognee
- knowledge graph
- agent memory
keywords:
- mem0 vs cognee
- cognee vs mem0
- mem0 cognee comparison
- open source graph memory
- cognee memory
faq:
- question: "What is the difference between Mem0 and Cognee?"
  answer: "Mem0 extracts short facts from conversations and stores them per user, agent or session for personalization. Cognee turns documents, code and conversations into a knowledge graph plus vector index that agents can query. Mem0 is built around users; Cognee is built around a body of knowledge."
- question: "Which has graph memory in open source, Mem0 or Cognee?"
  answer: "Cognee. Its Apache 2.0 engine builds and searches a knowledge graph locally. Mem0 removed graph memory from its open-source SDK in the April 2026 release; graph memory is now a feature of the hosted Mem0 Platform on the Pro and Enterprise plans."
- question: "Can Cognee run without an LLM API key?"
  answer: "Yes, since v1.6 (September 2026). With no key set, Cognee extracts the graph with a local GLiNER model and embeds with a local model, so text ingestion and retrieval work offline. You need an LLM key for generated answers and for LLM-based improvement stages."
---

**Mem0 vs Cognee** is a choice between two memory shapes. **Mem0** extracts short facts from conversations and stores them per user for personalization. **Cognee** turns documents, code and conversations into a knowledge graph plus vector index that agents search. Both are Apache 2.0 and self-hostable, but only Cognee keeps graph memory in its open-source version.

This page compares how each one writes and reads memory, what runs locally, the APIs, and pricing. Facts come from the [Mem0 README](https://github.com/mem0ai/mem0), the [Cognee README](https://github.com/topoteretes/cognee), their docs and pricing pages, checked on 8 October 2026.

## What are Mem0 and Cognee?

**Mem0 is a memory layer that uses an LLM to pull durable facts from conversations, scoped to users, agents and sessions, and returns them by hybrid search. Cognee is a memory engine that builds a knowledge graph, vector index and relational store from your data, so agents can retrieve entities, relationships and source text.**

Mem0 answers "what do I know about this user?" Its sweet spot is a chat assistant that remembers preferences, plans and past decisions. It runs as a library, a Docker server, or the hosted Mem0 Platform.

Cognee answers "what does this body of knowledge say?" Its sweet spot is a "company brain" over docs, tickets and code. It runs as a Python library, a CLI, a Docker API server, or Cognee Cloud, with SDKs for Python, TypeScript and Rust.

## Mem0 vs Cognee at a glance

| | Mem0 | Cognee |
|---|---|---|
| License | Apache 2.0 | Apache 2.0 |
| Core API | `add`, `search`, `update`, `delete` | `remember`, `recall`, `improve`, `forget` |
| Main input | Chat messages | Documents, code, conversations |
| Memory unit | Extracted fact ("User prefers aisle seats") | Entities, relationships and chunks in a graph |
| Storage | Vector store + SQL + entity collection | Graph + vector + relational (local defaults: LadybugDB, LanceDB, SQLite) |
| Graph in open source | Removed in April 2026 | Yes |
| Retrieval | Semantic + BM25 + entity, fused | Graph, vector, summary or hybrid, auto-routed |
| Runs without an LLM key | No; extraction needs an LLM | Yes for text, since v1.6 |
| Hosted pricing (Oct 2026) | Free; Starter $19/mo; Pro $249/mo | Free 1M tokens; then $1 per 1M tokens |

## How Mem0 writes and reads memory

Each `add` makes **one LLM call** that extracts facts from the messages. Since the April 2026 algorithm, extraction is ADD-only: new facts sit beside old ones and nothing is overwritten automatically. Mem0 embeds each fact, extracts its entities into a side collection, and stores metadata in SQL.

`search` scores memories on semantic similarity, BM25 keywords and entity overlap. In the open-source library, keyword and entity search need the `[nlp]` extra and a spaCy model.

The graph change matters for this comparison. Mem0's [v2-to-v3 migration guide](https://docs.mem0.ai/migration/oss-v2-to-v3) says "Graph memory is removed from the open-source SDK," and the Neo4j, Memgraph and Kuzu integrations are gone. On the Platform, a built-in graph links memories through shared entities and boosts ranking. The [pricing page](https://mem0.ai/pricing) lists it on Pro ($249/month) and Enterprise.

More on the current design in [what is Mem0](/articles/what-is-mem0-ai/).

## How Cognee writes and reads memory

Cognee stores data in three layers: relational (documents and provenance), vector (embeddings) and graph (entities and relationships). Text becomes entities, relations and chunks. Code becomes a graph of symbols and dependencies.

Its four operations, from the README:

| Operation | What it does |
|---|---|
| `remember` | Store content or code in permanent memory, or in a session when you pass a session ID |
| `recall` | Retrieve context and answers, with automatic routing or a chosen search strategy |
| `improve` | Enrich memory, apply feedback, and move session knowledge into the graph |
| `forget` | Remove a specific item or dataset |

Since **v1.6** (18 September 2026), Cognee can extract the graph with a local **GLiNER** model and embed with a local model when no LLM key is set. The README is candid about limits: the bundled GLiNER extractor is "a demo" of the small-model pipeline, and running the whole stack on Postgres is a demo feature, with the production version "available as a licensed product."

```python
import asyncio
import cognee

async def main():
    await cognee.remember(
        "Our refund window is 30 days. Enterprise customers get 60 days.",
        dataset_name="support_policies",
    )
    results = await cognee.recall(
        "How long do enterprise customers have to request a refund?",
        datasets=["support_policies"],
    )
    for result in results:
        print(result)

asyncio.run(main())
```

Without an LLM key this returns matching source text; with `LLM_API_KEY` set, Cognee can generate an answer. The code matches the Cognee 1.6 README quickstart.

## Where each one is stronger

### Mem0's strengths

- **Small, stable API** that fits into any agent loop.
- **Per-user scoping** built in, with `user_id`, `agent_id` and `run_id` filters.
- **The widest integration list**: LangGraph, CrewAI, AutoGen, the OpenAI Agents SDK, Mastra, Vercel AI SDK, plus plugins for coding agents and Hermes Agent.
- **A self-hosted server** with dashboard, API keys and audit log.

### Cognee's strengths

- **Open-source graph memory** that runs locally.
- **Document and code ingestion**, with Google Drive and Gmail connectors added in v1.6.1.
- **Keyless local mode** for text, useful for privacy-sensitive setups.
- **Migration tooling**: its docs describe importing memory from Mem0, Letta, Zep and Graphiti with the COGX exchange format.

### Where each one is weaker

- Mem0 open source has **no graph, no temporal reasoning and no background consolidation**; those are Platform features.
- Cognee lists **bi-temporal memory with conflict resolution** under Enterprise on its [pricing page](https://www.cognee.ai/pricing), and some production backends are licensed.
- For plain per-user chat facts, a graph pipeline is more machinery than the job needs.

## Cost and benchmarks

**Write cost.** Mem0 makes one LLM call per `add`. Cognee's graph extraction is LLM-based by default but can use the local GLiNER model. At high message volume, extraction is usually the biggest bill for either.

**Hosted pricing.** Mem0 Platform's free tier gives 10,000 adds and 1,000 retrievals a month; Starter is $19 for 50,000 adds and 5,000 retrievals. Cognee Cloud gives 1M free tokens, then charges $1 per 1M tokens processed.

**Benchmarks.** Both publish their own numbers on different tests. Mem0 reports 92.5 on LoCoMo and 94.4 on LongMemEval, measured on its managed platform. Cognee reports 0.79 on BEAM 100K and 0.67 on BEAM 10M, and calls the 10M result "exploratory." None of these are independent, and they don't measure the same thing. Our LLM memory comparison lists the claims with sources.

## Mem0 or Cognee: how to choose

| Your memory is mostly... | Pick |
|---|---|
| Preferences and facts about individual users | Mem0 |
| Company documents, tickets and code | Cognee |
| Entity relationships you want to query in open source | Cognee |
| A simple API added to an existing agent | Mem0 |
| Offline or keyless text memory | Cognee |
| Facts that change over time, with history | Neither by default; look at Graphiti or Zep |

Some teams run both: Mem0 for user memory and Cognee for shared knowledge. If you'd rather have one system, the wider field is in [Mem0 alternatives](/articles/mem0-alternatives-compared/) and [Cognee alternatives](/articles/cognee-alternatives/). For background on graph-based memory, see [knowledge graphs for AI memory](/articles/ai-memory-knowledge-graph/), and for how memory fits an agent overall, [AI agent memory explained](/articles/ai-agent-memory-explained/).
