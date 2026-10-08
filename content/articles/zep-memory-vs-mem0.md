---
title: "Zep vs Mem0: Temporal Graph vs Fact Memory"
description: "Zep vs Mem0 compared (Oct 2026): temporal context graph vs extracted facts, open source, self-hosting, APIs, pricing, the benchmark dispute, how to pick."
date: 2026-04-11
lastmod: 2026-10-08
slug: zep-memory-vs-mem0
cluster: agent-memory
tags:
- Zep
- Mem0
- Graphiti
- agent memory
keywords:
- zep vs mem0
- zep memory vs mem0
- mem0 vs zep
- graphiti vs mem0
- zep or mem0
faq:
- question: "What is the difference between Zep and Mem0?"
  answer: "Zep stores memory in a temporal knowledge graph where each fact has a validity window, so it can tell what is true now from what used to be true. Mem0 extracts facts into a vector store with entity linking and hybrid search, and since April 2026 appends new facts instead of overwriting old ones."
- question: "Is Zep or Mem0 open source?"
  answer: "Mem0's library and self-hosted server are Apache 2.0. Zep's managed service is not open source, and Zep Community Edition is deprecated. Zep's open-source project is Graphiti, an Apache 2.0 temporal graph framework that you run with your own Neo4j, FalkorDB or Neptune database."
- question: "Which scores higher on LoCoMo, Zep or Mem0?"
  answer: "It depends on who ran the test. Mem0's 2025 paper scored Zep at 65.99% and Mem0's graph variant at 68.44%. Zep said the setup was wrong and reported 75.14% for itself. Both are vendor-run numbers with different setups, so test on your own data."
---

**Zep vs Mem0** is a choice between two ways of storing what an agent learns. **Zep** keeps a temporal knowledge graph where every fact has a validity window, so old facts are invalidated rather than lost. **Mem0** extracts short facts into a vector store with entity linking, and ranks them by semantic, keyword and entity match. Mem0 is open source; Zep is a managed service with Graphiti as its open-source core.

This page compares the memory model, open-source status, APIs, pricing and benchmarks of each, based on their docs, READMEs and pricing pages as of 8 October 2026.

## What are Zep and Mem0?

**Zep is a managed context platform that builds a temporal context graph per user or account from messages and business data, and returns a prompt-ready block of relevant facts. Mem0 is an Apache 2.0 memory layer that uses an LLM to extract facts from conversations, stores them per user, agent or session, and returns them on search.**

Zep's design is described in the paper [Zep: A Temporal Knowledge Graph Architecture for Agent Memory](https://arxiv.org/abs/2501.13956) (Rasmussen et al., 2025). Its engine is **[Graphiti](https://github.com/getzep/graphiti)**, released separately under Apache 2.0. See [what is Zep memory](/articles/what-is-zep-memory/) for the full picture.

Mem0's design is described in [arXiv 2504.19413](https://arxiv.org/abs/2504.19413), and its algorithm was rewritten in April 2026. See [what is Mem0](/articles/what-is-mem0-ai/).

## Zep vs Mem0 at a glance

| | Zep | Mem0 |
|---|---|---|
| Product form | Managed service (Zep Cloud) | Library, self-hosted server, or Mem0 Platform |
| Open source | Graphiti (Apache 2.0); Community Edition deprecated | Library and server (Apache 2.0) |
| Memory model | Temporal graph: entities, facts as edges, episodes as provenance | Extracted facts with embeddings plus an entity collection |
| Changed facts | Old fact gets an invalid date; history kept | New fact stored next to old one (ADD-only); retrieval ranks the current one |
| Retrieval | Context Block, or graph search with RRF, MMR or cross-encoder reranking | Semantic + BM25 + entity, fused |
| Graph in open source | Yes, via Graphiti (bring Neo4j, FalkorDB or Neptune) | No; removed in April 2026, now Platform-only |
| SDKs | Python, TypeScript, Go | Python, TypeScript, REST, CLI |
| Self-host the full product | Enterprise BYOC only | Yes, Docker server |
| Hosted pricing | Free 10,000 credits/mo; Flex $125/mo | Free; Starter $19/mo; Pro $249/mo |

## How Zep handles memory

Zep organizes data into **users**, **threads** and **episodes**. Every message added to a user's threads becomes an episode in that user's graph. Zep extracts **entities** (nodes) and **facts** (edges) from each episode.

When new data contradicts a fact, Zep doesn't delete it. It sets the time the old fact became invalid. That's the core difference from most memory layers: you can ask what's true now, or what was true last month. Graphiti calls these graphs **bi-temporal**.

Retrieval has two paths. `thread.get_user_context()` returns a **Context Block**, a prompt-ready string assembled from the user's graph. `graph.search()` is the low-level path with scopes (edges, nodes, episodes) and a choice of reranker. With the `zep-cloud` v3 SDK:

```python
import os
from zep_cloud.client import Zep
from zep_cloud.types import Message

zep = Zep(api_key=os.environ["ZEP_API_KEY"])
zep.user.add(user_id="dana")
zep.thread.create(thread_id="dana-1", user_id="dana")

zep.thread.add_messages(
    "dana-1",
    messages=[Message(role="user", name="Dana", content="I switched from Python to Go at work.")],
)

context = zep.thread.get_user_context(thread_id="dana-1")
print(context.context)  # prompt-ready block, built in the background
```

Ingestion is asynchronous, so new facts can take a moment to appear.

## How Mem0 handles memory

Mem0 is simpler. Your code calls `add` with messages and a `user_id`. One LLM call extracts facts like "Dana uses Go at work." Mem0 embeds them, links their entities, and stores them.

Since the April 2026 algorithm, Mem0 doesn't update or delete during extraction. "Dana switched from Python to Go" is stored as a new fact next to any older "Dana uses Python" memory, and time-aware retrieval is meant to rank the current one first. You correct memories explicitly with `update` and `delete`.

```python
from mem0 import Memory

memory = Memory()  # OpenAI + local Qdrant defaults
memory.add("I switched from Python to Go at work.", user_id="dana")

hits = memory.search("what language does Dana use?", filters={"user_id": "dana"}, top_k=5)
for h in hits["results"]:
    print(h["memory"], h["score"])
```

The graph difference matters. Mem0's [migration guide](https://docs.mem0.ai/migration/oss-v2-to-v3) says graph memory "is removed from the open-source SDK." The Platform has a built-in entity graph that boosts ranking, but it doesn't track validity windows the way Zep does.

## Open source and self-hosting

This is where the two diverge most.

**Mem0** you can run yourself completely: the library, or the Docker server with Postgres and pgvector, a dashboard and API keys. You supply the LLM and embedder.

**Zep** you can't, unless you buy Enterprise. Zep stopped maintaining **Community Edition** in April 2025; the code sits unsupported in the `legacy/` folder of getzep/zep. Bring Your Own Cloud deployment is an Enterprise feature on the [Zep pricing page](https://www.getzep.com/pricing). The open-source path is **Graphiti**: the same temporal graph engine, but you run Neo4j, FalkorDB or Neptune and build users, threads and context assembly yourself. Our [Zep Docker guide](/articles/zep-memory-docker/) covers what self-hosting looks like now.

## Pricing

| | Zep Cloud | Mem0 Platform |
|---|---|---|
| Free | 10,000 credits/month | 10,000 adds and 1,000 retrievals/month |
| Entry paid | Flex: $125/month, 50,000 credits | Starter: $19/month, 50,000 adds and 5,000 retrievals |
| Next tier | Flex Plus: $375/month, 200,000 credits | Pro: $249/month, 500,000 adds, graph memory |
| Billing unit | 1 credit per 350 bytes ingested; retrieval unmetered | Requests: adds and retrievals counted separately |
| Enterprise | Custom; BYOC, BYOK, SLA | Custom; on-prem, SSO, SLA |

Zep bills on **ingestion**; searches are free. Mem0 bills on **requests**, and retrievals are the tighter limit on the lower tiers. Which is cheaper depends on whether your app writes a lot and reads a little, or the reverse.

## Benchmarks and the LoCoMo dispute

The two companies have argued publicly over numbers.

- Mem0's 2025 paper scored **Zep at 65.99%** on LoCoMo (LLM-as-judge), below **Mem0 at 66.88%** and **Mem0g at 68.44%**. It also measured Zep's graph at over 600,000 tokens per conversation.
- Zep replied in May 2025 that Mem0 had set Zep up wrong: both speakers mapped to one user, timestamps pasted into message text instead of `created_at`, and searches run sequentially. Zep reported **75.14%** for itself in [its rebuttal](https://www.getzep.com/blog/lies-damn-lies-statistics-is-mem0-really-sota-in-agent-memory/).
- Zep's own paper reports **94.8% on DMR** and up to **18.5% higher accuracy on LongMemEval** than baselines.
- Mem0 now reports **92.5 on LoCoMo** and **94.4 on LongMemEval** for its April 2026 algorithm, measured on its managed platform.

Every figure here is vendor-run, with different models, judges and settings. The [Mem0 paper breakdown](/articles/mem0-building-production-ready-ai-agents/) and LLM memory evaluation explain why these numbers don't line up.

## Zep or Mem0: how to choose

| If you need... | Pick |
|---|---|
| To know which version of a fact is current, with history | Zep (or Graphiti) |
| Customer or account context built from business data plus chat | Zep |
| A fully self-hosted, open-source memory server | Mem0 |
| Open-source temporal graph and you can run a graph DB | Graphiti |
| Simple per-user preference memory with a small API | Mem0 |
| Low entry price for a hosted service | Mem0 |
| Retrieval cost that doesn't grow with query volume | Zep |

If facts in your domain change often (addresses, plans, account status), Zep's validity windows are the stronger model; see temporal reasoning in AI memory. If you mostly store stable preferences and want to own the stack, Mem0 is the easier fit. Other options, including Letta, Cognee and [Hindsight](https://github.com/vectorize-io/hindsight), are compared in [Zep alternatives](/articles/zep-alternatives/) and Mem0 alternatives. Vectorize also publishes a [Mem0 vs Zep comparison](https://vectorize.io/articles/mem0-vs-zep).
