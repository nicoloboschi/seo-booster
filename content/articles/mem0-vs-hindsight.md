---
title: "Mem0 vs Hindsight: Agent Memory Layers Compared"
description: "Mem0 vs Hindsight compared (Oct 2026): how each stores and retrieves memory, open-source vs hosted features, benchmarks and token cost, pricing, and which fits."
date: 2026-10-08
lastmod: 2026-10-08
slug: mem0-vs-hindsight
cluster: agent-memory
tags:
- Mem0
- Hindsight
- agent memory
- open source
keywords:
- mem0 vs hindsight
- hindsight vs mem0
- mem0 hindsight comparison
- hindsight or mem0
- mem0 vs hindsight benchmark
faq:
- question: "What is the difference between Mem0 and Hindsight?"
  answer: "Both are memory layers your agent calls to store and fetch memories. Mem0 extracts short facts in one LLM pass and returns them with a lean, token-efficient search. Hindsight extracts facts, entities and time data, consolidates them into observations in the background, searches four ways at once, and adds a reflect call that reasons over memories."
- question: "Is Hindsight more accurate than Mem0?"
  answer: "On the numbers both vendors publish, they are close. Mem0's own comparison page lists Hindsight ahead on LongMemEval (94.6 vs 94.4) and BEAM 1M (73.9 vs 64.1) and Mem0 ahead on LoCoMo (92.5 vs 92), with Mem0 using about 3-4x fewer tokens per retrieval. All of these are vendor-run, so test on your own data."
- question: "Which is better for self-hosting, Mem0 or Hindsight?"
  answer: "Both self-host on PostgreSQL with pgvector. Hindsight's open-source build includes all its retrieval strategies, graph links and background consolidation. Mem0's open-source SDK dropped graph memory in April 2026, and temporal reasoning, decay and the Dream consolidation process are Mem0 Platform features."
---

**Mem0 vs Hindsight** is a choice between two memory layers that sit beside your agent, not inside it. Mem0 keeps memory lean: one LLM pass extracts facts, and search returns a small set of them cheaply. Hindsight does more work per memory: it links entities and time, merges facts into observations in the background, and can reason over them with reflect.

Both are open source and both have a hosted version. This page compares them on memory model, retrieval, what's free versus paid, benchmarks and cost, using each project's README, docs and pricing pages as checked on 8 October 2026.

## What are Mem0 and Hindsight?

**Mem0 is an Apache 2.0 memory layer that uses an LLM to pull durable facts from conversations, stores them per user, agent or session, and returns the relevant ones on search. Hindsight is an MIT-licensed memory server from Vectorize that extracts facts, entities and time data into memory banks, searches them four ways in parallel, and reasons over them with a reflect operation.**

**[Mem0](https://github.com/mem0ai/mem0)** runs as a Python or TypeScript library, a self-hosted Docker server, or the hosted Mem0 Platform. It had about 66,800 GitHub stars in October 2026, the most of any agent memory project. Our page on [what Mem0 is](/articles/what-is-mem0-ai/) covers it in depth.

**[Hindsight](https://github.com/vectorize-io/hindsight)** runs as a Docker container, a pip-installed server, a Helm chart, an embedded Python server, or the managed Hindsight Cloud. It had about 47,100 stars. The [Hindsight overview](/articles/ai-memory-hindsight/) covers its design and limits.

Neither runs your agent. Your code (or a framework integration) calls them before and after model turns.

## Mem0 vs Hindsight at a glance

| | Mem0 | Hindsight |
|---|---|---|
| License | Apache 2.0 | MIT |
| Core calls | `add`, `search`, `update`, `delete` | `retain`, `recall`, `reflect` |
| What gets stored | Short extracted facts with embeddings and entities | World facts, experiences, observations, mental models |
| Write path | One LLM pass, ADD-only | LLM extraction of facts, entities, time and causal links, then background consolidation |
| Retrieval | Semantic + BM25 + entity matching, fused | Semantic + BM25 + graph + temporal, fused and reranked |
| Reasoning over memory | No; your prompt does it | `reflect` returns a cited answer |
| Graph in open source | Removed in April 2026 (Platform only) | Included |
| SDKs | Python, TypeScript, REST, CLI | Python, TypeScript, Go, REST, CLI |
| MCP | Hosted MCP server (Platform key) | MCP endpoint per bank, self-hosted or cloud |
| Storage | Vector store of your choice; server uses Postgres + pgvector | PostgreSQL + pgvector, Oracle 23ai, or embedded pg0 |
| Hosted pricing | Free; Starter $19/mo; Pro $249/mo | Usage-based, free credits to start |

Sources: the two READMEs, Mem0's [Platform vs Open Source](https://docs.mem0.ai/platform/platform-vs-oss) page and [pricing page](https://mem0.ai/pricing).

## How Mem0 stores and retrieves memory

Mem0 is built to be cheap per call. After an exchange, your code sends the messages to `add`. Since the April 2026 algorithm, an LLM extracts facts in a **single pass** and Mem0 only adds: "Memories accumulate; nothing is overwritten," in the README's words. A changed fact sits next to the old one, and you call `update` or `delete` for corrections.

On `search`, Mem0 scores semantic similarity, BM25 keyword match and entity overlap in parallel and fuses them, in a single retrieval call with no agentic loop. You put the top results in your prompt.

The open-source SDK and the hosted Platform share these calls, but several features are now **Platform-only**: graph memory, temporal reasoning, memory decay and the **Dream** background consolidation process. The README's benchmark scores also "reflect Mem0's managed platform, which includes proprietary optimizations not available in the open-source SDK."

## How Hindsight stores and retrieves memory

Hindsight does more work at write time. `retain` sends content to an LLM that extracts facts, dates, entities and relationships into an isolated **memory bank** (often one per user or agent). Entities attach to the memories they appear in, and memories link through shared entities, semantic neighbors and causal links.

A background step merges related facts into **observations**: deduplicated beliefs with supporting evidence that get refined as new facts arrive. **Mental models** are standing answers you define, refreshed in the background and read without an LLM call.

`recall` runs **four strategies in parallel**: semantic, BM25 keyword, graph and temporal. Results are merged with reciprocal rank fusion, reranked with a cross-encoder and cut to a token budget. `reflect` is an agent loop that reads mental models, observations and facts and returns an answer with citations. The FAQ puts reflect at 1-10 seconds versus 50-500 ms for recall.

All of this ships in the open-source build; Hindsight Cloud is the managed option.

## Code: the same task in each

Store a fact about a user, then fetch it before the next turn. Mem0, with the open-source library (defaults to OpenAI, needs `OPENAI_API_KEY`):

```python
from mem0 import Memory

memory = Memory()
memory.add("Alice moved to Berlin in March and works at a robotics startup.", user_id="alice")

hits = memory.search("Where does Alice live?", filters={"user_id": "alice"}, top_k=5)
context = "\n".join(h["memory"] for h in hits["results"])
```

Hindsight, with `hindsight-client` against a local server on port 8888:

```python
from hindsight_client import Hindsight

client = Hindsight(base_url="http://localhost:8888")
client.retain(
    bank_id="alice",
    content="Alice moved to Berlin in March and works at a robotics startup.",
    document_id="chat-2026-10-08",
)

results = client.recall(bank_id="alice", query="Where does Alice live?", max_tokens=2048)
context = "\n".join(r.text for r in results.results)

# Optional: let Hindsight reason over the bank and answer directly
answer = client.reflect(bank_id="alice", query="What should I know before calling Alice?")
```

The shape is the same: write after a turn, read before the next. The difference is what happens on the server between the two calls.

## Benchmarks and token cost

Both vendors publish scores, and both are self-run. Mem0's own [Mem0 vs Hindsight page](https://mem0.ai/compare/mem0-vs-hindsight) lists them side by side:

| Benchmark | Mem0 | Hindsight | Mem0 tokens / retrieval | Hindsight tokens / retrieval |
|---|---|---|---|---|
| LongMemEval | 94.4 | 94.6 | 6.7K | 23.9K |
| LoCoMo | 92.5 | 92 | 6.9K | 36.2K |
| BEAM 1M | 64.1 | 73.9 | 6.7K | 43.6K |
| BEAM 10M | 48.6 | 64.1 | under 7K | about 27K |

Hindsight's [benchmark site](https://benchmarks.hindsight.vectorize.io/) reports the same Hindsight scores (94.6 LongMemEval, 92 LoCoMo, 73.9 BEAM 1M, 64.1 BEAM 10M) but no token counts. The token columns are Mem0's measurements.

Read it this way: accuracy is close on the short benchmarks, Hindsight leads on the very long BEAM sets, and Mem0 returns far fewer tokens per retrieval. Mem0's page frames the gap as Hindsight spending about 4x the tokens for its edge. Token count per retrieval also depends on settings: Hindsight's `max_tokens` budget is yours to set. Mem0's scores come from its managed Platform, not the open-source SDK.

Older comparisons quote much lower Mem0 numbers, from before its April 2026 algorithm. The [LLM memory evaluation guide](/articles/llm-memory-evaluation/) explains what these benchmarks test and why a small test on your own data matters more than vendor tables.

## Self-hosting, hosting and cost

**Mem0 open source** costs only your LLM, embedder and vector store. Every `add` makes one extraction call. The self-hosted server adds Postgres with pgvector, a dashboard and API keys. The Platform's free Hobby tier allows 10,000 adds and 1,000 retrievals a month; Starter is $19/month and Pro, which includes graph memory and Dream, is $249/month. Mem0 lists SOC 2 and HIPAA for its Platform.

**Hindsight open source** costs your LLM calls plus a PostgreSQL database. Retain and consolidation both use an LLM, so writes cost more than Mem0's single pass; async retain and provider batch APIs reduce that. The FAQ asks for 4 GB of RAM minimum (8 GB recommended) to self-host. **Hindsight Cloud** is usage-based with no seat fee and free credits to start.

## Mem0 or Hindsight: how to choose

| If you... | Pick |
|---|---|
| Want the smallest token cost per retrieval | Mem0 |
| Need per-user preference memory in a chat or support app | Mem0 |
| Want SOC 2 / HIPAA on a hosted service today | Mem0 Platform |
| Want graph links, time queries and consolidation in open source | Hindsight |
| Want the memory layer to return a reasoned, cited answer | Hindsight (`reflect`) |
| Have very long histories (millions of tokens per user) | Hindsight, on BEAM results |
| Run simple n8n-style flows | Mem0, or plain files; Hindsight's README calls itself possibly "overkill" there |

Other tools take other positions: Zep and Graphiti track fact validity over time, Letta lets the agent edit its own memory, and Cognee builds graphs from documents. See [Mem0 alternatives](/articles/mem0-alternatives-compared/), [Mem0 vs Letta](/articles/mem0-vs-letta/) and the [LLM memory comparison](/articles/llm-memory-comparison/). For the concepts, start with [AI agent memory explained](/articles/ai-agent-memory-explained/).
