---
title: "Supermemory Alternatives: 7 Agent Memory Tools Compared"
description: "Supermemory alternatives compared (Oct 2026): Mem0, Zep, Graphiti, Letta, Cognee, Honcho and Hindsight. Licenses, self-hosting, memory models, RAG and pricing."
date: 2026-05-06
lastmod: 2026-10-09
slug: supermemory-alternatives
cluster: agent-memory
tags:
- Supermemory
- agent memory
- alternatives
- open source
keywords:
- supermemory alternatives
- supermemory alternative open source
- supermemory vs zep
- self-hosted supermemory alternative
faq:
- question: "What is the best open-source alternative to Supermemory?"
  answer: "For user-preference memory, Mem0 (Apache 2.0) is the closest match. For memory over documents and code with a knowledge graph, Cognee (Apache 2.0). For facts that change over time, Graphiti (Apache 2.0). For a memory server with background consolidation and reflection, Hindsight (MIT). Honcho (AGPL-3.0) fits per-user modeling."
- question: "Can I self-host Supermemory?"
  answer: "Yes, with limits. Supermemory local is a free single-process binary under a 'lite license'; its server source is not in the public repository. The pricing page lists a self-hosted option on the $399/month Scale plan, and Enterprise offers air-gapped or dedicated instances."
- question: "How does Supermemory compare to Mem0?"
  answer: "Both extract facts from conversations and scope them per user. Supermemory adds document RAG, connectors and auto-maintained user profiles in one hosted API. Mem0 is fully open source and self-hostable, with a simpler memory-only API; its graph memory is on the paid Platform."
---

**Supermemory alternatives** are other memory layers for AI agents: Mem0, Zep, Graphiti, Letta, Cognee, Honcho and Hindsight. People usually look for one when they need **fully open-source, self-run infrastructure** (Supermemory's local server is a closed-source binary), want memory without bundled RAG and connectors, or need a different memory model such as a temporal graph or an agent that manages its own memory.

Below: what Supermemory does, a comparison table, a short section on each alternative, and how to pick. Facts come from each project's README, docs and pricing page, checked on 8 October 2026.

## What Supermemory does, and why people look for alternatives

**Supermemory is a hosted memory and context API. It extracts facts from conversations, maintains a static and dynamic profile per user, runs hybrid search over memories and document chunks, and syncs data from Google Drive, Gmail, Notion, OneDrive and GitHub.** It also ships plugins for Claude Code, Cursor, Codex and other tools. Our [Supermemory explainer](/articles/supermemory-long-term-ai-memory-as-a-service/) covers how it works.

The common reasons to compare it with others:

1. **Open infrastructure.** The [GitHub repo](https://github.com/supermemoryai/supermemory) is MIT, but the docs say the local server's "source is not in the public repository." It's a free binary under a "lite license." Self-hosting beyond that is on the $399/month Scale plan or Enterprise.
2. **You only need memory.** If you already have a RAG stack, Supermemory's bundled document search and connectors are extra surface.
3. **A different memory model.** Temporal fact validity, agent-edited memory, or reflection over memories are things other systems lead on.
4. **Benchmarks you can compare.** Supermemory's headline LongMemEval number is Recall@15, a retrieval metric, while most vendors report answer accuracy.

## Supermemory alternatives at a glance

| Tool | What it is | License | Self-host | Memory model | Hosted pricing (Oct 2026) |
|---|---|---|---|---|---|
| **Supermemory** | Memory + RAG + profiles API | Repo MIT; server closed | Free local binary; Scale plan | Extracted facts, profiles, documents | Free $5 credits; Pro $19/mo |
| **Mem0** | Memory layer for user, session and agent facts | Apache 2.0 | Yes, library or Docker server | Extracted facts, entity linking, hybrid search | Free; Starter $19/mo; Pro $249/mo |
| **Zep** | Managed temporal context graph | Commercial | Enterprise BYOC only | Facts with validity windows per user or account | Free 10,000 credits/mo; Flex $125/mo |
| **Graphiti** | Open-source temporal graph framework | Apache 2.0 | Yes, with Neo4j, FalkorDB or Neptune | Bi-temporal knowledge graph with episodes | None (library) |
| **Letta** | Stateful agent harness | Apache 2.0 | Yes, local or App Server | Agent-edited memory files, message search, dreaming | Free; Pro $20/mo |
| **Cognee** | Knowledge graph memory engine | Apache 2.0 | Yes, pip or Docker | Graph + vector + relational | Free 1M tokens; $1 per 1M tokens |
| **Honcho** | Peer-modeling memory service | AGPL-3.0 | Yes, Docker or CLI | Per-peer representations, conclusions, summaries | Ingestion $2 per 1M tokens + per-query reasoning |
| **Hindsight** | Memory server with retain/recall/reflect | MIT | Yes, Docker, pip, Helm or embedded | Facts, experiences, observations, mental models | Pay as you go (retain $10 per 1M tokens) |

Prices are the vendors' published list prices and change often.

## Mem0

**Mem0** is the closest functional match for user memory. An LLM extracts facts from each `add` call in a single pass, and `search` fuses semantic, BM25 and entity signals. Memories are scoped by `user_id`, `agent_id` and `run_id`. It runs as a library, a self-hosted Docker server with dashboard and API keys, or the hosted Mem0 Platform.

Two caveats from Mem0's own docs: graph memory was removed from the open-source SDK in April 2026 and is now on the Platform's Pro plan, and its benchmark scores reflect the managed platform, not the open-source SDK.

- **Pick Mem0** if you want Supermemory-style user memory that you can run entirely yourself.
- **Look elsewhere** if you want document RAG and connectors in the same API.

More in [Mem0 vs Supermemory](/articles/mem0-vs-supermemory/), [what Mem0 is](/articles/what-is-mem0-ai/) and [Mem0 alternatives](/articles/mem0-alternatives-compared/).

## Zep and Graphiti

**Zep** builds a temporal context graph per user or account from chat and business data. Each fact carries a validity window, so when a user changes cities, the old fact is invalidated with a date rather than lost. It's a managed service; Community Edition was deprecated in April 2025.

**[Graphiti](https://github.com/getzep/graphiti)** is the Apache 2.0 engine under Zep. You run the graph database and build users and sessions yourself.

- **Pick Zep** for managed memory where "what's true now vs before" matters, such as customer and account state.
- **Pick Graphiti** for the same model on your own infrastructure.
- **Look elsewhere** if you don't want a graph database or need document RAG.

See what is Zep memory and [Zep alternatives](/articles/zep-alternatives/).

## Letta

**Letta** (formerly MemGPT) is an agent runtime, not a memory API. Letta Code agents keep memory as Markdown files in a git-backed store, search their own message history, and consolidate lessons in background "dreaming." It's Apache 2.0.

- **Pick Letta** if you're building the agent itself and want it to own its memory.
- **Look elsewhere** if you need memory behind an existing app. The Agent SDK is TypeScript only, and the Python client is deprecated.

Details in the Letta guide.

## Cognee

**Cognee** turns documents, code and conversations into a knowledge graph plus vector index, with `remember`, `recall`, `improve` and `forget` operations. Since v1.6 it can build and search text memory with local models and no LLM key. It has SDKs for Python, TypeScript and Rust.

- **Pick Cognee** if you used Supermemory mostly for document memory and want it open source with graph retrieval.
- **Look elsewhere** for simple per-user chat facts; the graph pipeline is more than that needs.

See Cognee alternatives.

## Honcho

**[Honcho](https://github.com/plastic-labs/honcho)** from Plastic Labs models users and agents as **peers**. You store messages on sessions; a background worker reasons over them and builds a representation of each peer, which you query in natural language or pull as prompt-ready context. It's AGPL-3.0, runs on Postgres with pgvector, and has a managed service and plugins for Claude Code, Codex, Cursor, OpenClaw and Hermes.

- **Pick Honcho** if you want deep per-user modeling ("what does this user respond to?"), including what one agent knows about another.
- **Look elsewhere** if AGPL is a problem for your distribution model, or you need document RAG.

More in [Honcho LLM memory](/articles/honcho-llm-memory/).

## Hindsight

**[Hindsight](https://github.com/vectorize-io/hindsight)** is an MIT-licensed memory server built around three operations. `retain` extracts facts, entities, time data and relationships with an LLM. `recall` runs semantic, BM25, graph and time-range searches in parallel and merges them with rank fusion and a cross-encoder reranker. `reflect` reasons over stored memories to answer harder questions.

In the background it consolidates facts into observations that keep their supporting evidence. It stores data in PostgreSQL with pgvector, ships an MCP endpoint per memory bank, and runs as Docker, pip, Helm or embedded in Python.

- **Pick Hindsight** if you want fully open, self-hosted memory with time-aware recall and consolidation, and no separate graph database.
- **Look elsewhere** if you want connectors and document RAG bundled in, as Supermemory provides. Every retain makes LLM calls, and the README says it "may be overkill" for simple automation workflows.

## How to choose a Supermemory alternative

Start from why you're leaving.

| If you need... | Look at |
|---|---|
| Open-source user memory you can run yourself | Mem0, Hindsight |
| Facts that change over time, with history | Zep, Graphiti, Hindsight |
| Memory over documents and code | Cognee |
| Rich modeling of each user or agent | Honcho |
| An agent that manages its own memory | Letta |
| Memory, RAG and connectors from one hosted API | Stay on Supermemory |

Two checks before you switch:

1. **Do you rely on Supermemory's RAG and connectors?** Most alternatives are memory-only. You'd pair them with your own retrieval stack; see RAG vs agent memory for where the line falls.
2. **Who pays for extraction?** Self-hosting removes per-token platform fees, but Mem0, Graphiti, Honcho and Hindsight all call an LLM on writes. Estimate tokens per message before comparing bills.

Vectorize publishes its own [Supermemory alternatives roundup](https://vectorize.io/articles/supermemory-alternatives); like any comparison from a memory vendor, read it as such. For a neutral fact sheet across eleven systems, see the [LLM memory comparison](/articles/llm-memory-comparison/).
