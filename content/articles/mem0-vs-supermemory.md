---
title: "Mem0 vs Supermemory: Agent Memory APIs Compared"
description: "Mem0 vs Supermemory compared (Oct 2026): memory model, RAG and connectors, open source vs hosted, self-hosting, benchmarks, pricing, and which one fits your app."
date: 2026-10-09
lastmod: 2026-10-09
slug: mem0-vs-supermemory
cluster: agent-memory
tags:
- Mem0
- Supermemory
- agent memory
- open source
keywords:
- mem0 vs supermemory
- supermemory vs mem0
- mem0 supermemory comparison
- mem0 or supermemory
- supermemory mem0 benchmark
faq:
- question: "What is the difference between Mem0 and Supermemory?"
  answer: "Both extract facts from conversations and scope them per user. Mem0 is a memory-only layer you can run fully yourself under Apache 2.0. Supermemory is a hosted API that bundles memory with document RAG, auto-maintained user profiles and connectors to Google Drive, Gmail, Notion, OneDrive and GitHub."
- question: "Can I self-host Mem0 and Supermemory?"
  answer: "Mem0 yes: the library and the Docker server are open source. Supermemory has a free local binary under a 'lite license', but its server source is not public; a self-hosted option comes with the $399/month Scale plan, and Enterprise offers dedicated or air-gapped instances."
- question: "Which scores higher on LongMemEval, Mem0 or Supermemory?"
  answer: "It depends on whose number you read. Mem0's comparison page lists Mem0 at 94.4 and Supermemory at 85.2. Supermemory's README reports 95% Recall@15, a retrieval metric rather than answer accuracy, and its own report lists several configurations with different scores. All figures are vendor-run."
---

**Mem0 vs Supermemory** is a choice between a memory-only layer and a memory-plus-context API. Mem0 extracts short facts from conversations and returns them by hybrid search, and you can run all of it yourself. Supermemory does fact extraction too, but bundles it with user profiles, document RAG and data connectors behind one hosted API.

Both have a free tier and paid plans from $19/month, and both can run on your machine, though in very different ways. This page compares memory model, retrieval, self-hosting, benchmarks and pricing, using each project's README, docs and pricing pages and Mem0's own comparison page, checked on 9 October 2026.

## What are Mem0 and Supermemory?

**Mem0 is an Apache 2.0 memory layer that uses an LLM to pull durable facts from conversations, stores them per user, agent or session, and returns the relevant ones on search. Supermemory is a managed memory and context API that extracts facts, keeps a static and dynamic profile per user, and searches memories and document chunks in one call.**

**[Mem0](https://github.com/mem0ai/mem0)** runs as a Python or TypeScript library, a self-hosted Docker server, or the hosted Mem0 Platform. It's the most-starred agent memory project, with about 66,900 GitHub stars in October 2026. See [what Mem0 is](/articles/what-is-mem0-ai/) for the details.

**[Supermemory](https://github.com/supermemoryai/supermemory)** runs mainly as a hosted API, with a local single-binary server for individual developers. Its repository (MIT, about 31,000 stars) holds the apps, SDKs and plugins. Our [Supermemory explainer](/articles/supermemory-long-term-ai-memory-as-a-service/) covers how it works.

## Mem0 vs Supermemory at a glance

| | Mem0 | Supermemory |
|---|---|---|
| License | Apache 2.0, server included | Repo MIT; server source not public |
| Scope key | `user_id`, `agent_id`, `run_id` | Namespace (user, project, repo...) |
| What gets stored | Short extracted facts with entities | Extracted facts, user profiles, document chunks |
| Write path | One LLM pass, ADD-only | Extraction, updates, contradiction handling, expiry |
| Retrieval | Semantic + BM25 + entity matching, fused | Hybrid search over memories and chunks, optional rerank |
| Document RAG | No; bring your own | Built in (PDFs, images, video, code) |
| Connectors | No | Google Drive, Gmail, Notion, OneDrive, GitHub, web crawler |
| SDKs | Python, TypeScript, REST, CLI | Python, TypeScript, REST |
| MCP | Hosted MCP server | Hosted MCP server (`memory`, `recall`, `context`) |
| Self-host | Library or Docker server, free | Free local binary ("lite license"); Scale plan or Enterprise |
| Hosted pricing | Free; Starter $19/mo; Pro $249/mo | Free ($5 credits); Pro $19/mo; Max $100/mo; Scale $399/mo |

Sources: the [Mem0 README](https://github.com/mem0ai/mem0), the [Supermemory README](https://github.com/supermemoryai/supermemory), [Mem0 pricing](https://mem0.ai/pricing) and [Supermemory pricing](https://supermemory.ai/pricing).

## How each one handles memory

**Mem0** is built to be lean. Your code sends messages to `add` after an exchange. Since the April 2026 algorithm, an LLM extracts facts in a single pass and Mem0 only adds; a changed fact sits next to the old one until you call `update` or `delete`. On `search`, it scores semantic similarity, BM25 keywords and entity overlap in parallel and fuses them in one call. Graph memory, temporal reasoning, decay and the Dream consolidation process are Platform-only features.

**Supermemory** takes on more of the lifecycle itself. Its README lists a memory engine that "extracts facts from conversations, tracks updates, resolves contradictions, and automatically forgets expired information." Its example: "I just moved to SF" supersedes "I live in NYC," and "I have an exam tomorrow" expires once the date passes. It also keeps a **profile** per user, split into static facts ("Senior engineer at Acme") and dynamic recent context, which you can fetch without a query.

The practical difference: with Mem0 you decide when facts get corrected. With Supermemory the service decides, which is less work and less control. For background on why this matters, see [memory decay in AI](/articles/ai-memory-decay/).

## RAG and connectors: the biggest gap

This is where the two products differ most. Mem0 is memory only. If your agent also needs to search a knowledge base, you run a separate RAG stack next to it.

Supermemory treats documents and memories as one problem. It ingests PDFs, images (with OCR), video (with transcription) and code (with AST-aware chunking), syncs Google Drive, Gmail, Notion, OneDrive and GitHub through connectors, and returns document chunks and personal memories in the same `search` call. The `search_mode` parameter switches between `"hybrid"`, `"memories"` and `"chunks"`.

If you already have retrieval in place, Supermemory's bundle is extra surface. If you don't, it saves building one. Our page on [RAG vs agent memory](/articles/rag-vs-agent-memory/) explains where the line between the two usually falls.

## Code: the same task in each

Store a fact about a user, then fetch it before the next turn. Mem0, with the open-source library (defaults to OpenAI, needs `OPENAI_API_KEY`):

```python
from mem0 import Memory

memory = Memory()
memory.add("Dana prefers short answers and works in Go.", user_id="dana")

hits = memory.search("How should I answer Dana?", filters={"user_id": "dana"}, top_k=5)
context = "\n".join(h["memory"] for h in hits["results"])
```

Supermemory, with the v5 Python SDK (release 5.0.0, needs `SUPERMEMORY_API_KEY`):

```python
from supermemory import Supermemory

client = Supermemory()
client.add("dana", content="Dana prefers short answers and works in Go.")

response = client.search("dana", query="How should I answer Dana?", limit=5)
context = "\n".join(r.memory or r.chunk for r in response.results)

# Profile facts, no query needed
profile = client.profile("dana").profile
```

Older Supermemory examples that pass `container_tag=` or `q=` use the pre-v5 API.

## Benchmarks: read the metric, not the headline

The two vendors report different things, so their headline numbers can't be compared directly.

| Source | Mem0 | Supermemory | What it measures |
|---|---|---|---|
| [Mem0's comparison page](https://mem0.ai/compare/mem0-vs-supermemory) | 94.4 on LongMemEval | 85.2 on LongMemEval | Answer accuracy (vendor-run) |
| Mem0's comparison page | 92.5 LoCoMo; 64.1 / 48.6 BEAM 1M / 10M | Not listed | Answer accuracy |
| Mem0's comparison page | Under 7K tokens per retrieval | "Not published" | Tokens returned per call |
| Supermemory README | n/a | 95% Recall@15 on LongMemEval, about 720 tokens of context | Retrieval recall |

The 85.2% figure matches one row of Supermemory's own [LongMemEval report](https://supermemory.ai/research/longmembench) (Gemini 3 Pro as the answer model, GPT-4o as judge). That report also lists other configurations, including 84.6% with GPT-5, so the score depends on which model reads the retrieved memory. Mem0's scores come from its managed Platform, not the open-source SDK.

**Recall@15** asks whether the right evidence shows up in the top 15 results. It says nothing about whether the model then answers correctly. Supermemory also maintains MemoryBench, an open-source harness that runs Supermemory, Mem0, Zep and others on the same tests. Running something like it on your own data beats any vendor table; see the [LLM memory evaluation guide](/articles/llm-memory-evaluation/).

## Self-hosting and cost

**Mem0 open source** costs only your LLM, embedder and vector store. The self-hosted server adds Postgres with pgvector, a dashboard and API keys. The hosted Platform has a free tier (10,000 adds and 1,000 retrievals a month), Starter at $19/month and Pro at $249/month, which includes graph memory. Mem0 lists SOC 2 and HIPAA for its Platform.

**Supermemory local** is a single binary that serves the same API on `localhost:6767` with local embeddings and any LLM, including Ollama. Its docs say it is "free within its lite license limit" and that "its server source is not in the public repository." It runs one process with one API key and no connectors. Hosted plans run on usage credits: Free ($5), Pro $19/month ($20 credits), Max $100/month ($130), Scale $399/month ($600, with a self-hosted option). Usage is billed per 1,000 "SM tokens" and per 1,000 search queries.

So if open, self-run infrastructure is a hard requirement, Mem0 meets it and Supermemory mostly doesn't.

## Mem0 or Supermemory: how to choose

| If you... | Pick |
|---|---|
| Need memory you can run fully yourself, source included | Mem0 |
| Want the smallest, simplest memory API next to an existing RAG stack | Mem0 |
| Want memory, document search and connectors from one API | Supermemory |
| Want the service to handle contradictions and expiring facts | Supermemory |
| Want a per-user profile you can inject at the start of every chat | Supermemory |
| Need SOC 2 / HIPAA on a hosted memory service | Mem0 Platform |

Neither is the only option. Zep and Graphiti track how facts change over time, Cognee builds knowledge graphs from documents, and [Hindsight](https://github.com/vectorize-io/hindsight) is an MIT-licensed memory server with graph and time-aware recall plus a `reflect` call that reasons over memories. Compare them in [Mem0 vs Hindsight](/articles/mem0-vs-hindsight/), [Supermemory alternatives](/articles/supermemory-alternatives/) and [Mem0 alternatives](/articles/mem0-alternatives-compared/). For the concepts behind all of these, start with [AI agent memory explained](/articles/ai-agent-memory-explained/).
