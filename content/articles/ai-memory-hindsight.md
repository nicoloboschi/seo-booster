---
title: "Hindsight AI Memory: How It Works and When to Use It"
description: "Hindsight is an open-source (MIT) agent memory system with retain, recall and reflect. How it stores and retrieves memories, its limits, and when to pick another tool."
date: 2026-06-17
lastmod: 2026-10-08
slug: ai-memory-hindsight
aliases:
- /articles/hindsight-llm-memory/
tags:
- Hindsight
- agent memory
- open source
- LLM memory
keywords:
- "hindsight ai memory"
- "hindsight llm memory"
- "hindsight agent memory"
- "vectorize hindsight"
- "hindsight retain recall reflect"
- "hindsight memory review"
cluster: agent-memory
faq:
- question: "What is Hindsight AI memory?"
  answer: "Hindsight is an open-source (MIT) memory system for AI agents, built by Vectorize. It stores facts, events and entities extracted from conversations, retrieves them with four search strategies in parallel, and can reason over them with a reflect operation. It runs self-hosted on PostgreSQL or as the managed Hindsight Cloud."
- question: "Is Hindsight free and open source?"
  answer: "Yes. The server, clients and integrations are MIT-licensed on GitHub (vectorize-io/hindsight) and can be self-hosted with Docker, pip, Helm or an embedded Python server. You pay for the LLM calls it makes. Hindsight Cloud is a separate, usage-based managed service."
- question: "When should I not use Hindsight?"
  answer: "Its own README says it may be overkill for simple n8n-style workflows. If you only need a short instruction file for a coding agent, a static user profile, or classic entity-to-entity graph queries in Cypher, simpler files, Mem0, or Graphiti on Neo4j can fit better."
---

**Hindsight** is an open-source agent memory system from Vectorize, released under the MIT license. It gives an AI agent three operations: **retain** (store and extract facts), **recall** (search memories) and **reflect** (reason over them to answer a question). It runs on PostgreSQL with pgvector, self-hosted or as the managed Hindsight Cloud.

This page is a neutral overview of Hindsight AI memory: what it stores, how retrieval works, what the benchmarks do and don't show, its real limits, and when another tool is the better pick. Facts come from the [GitHub README](https://github.com/vectorize-io/hindsight), the official docs and the paper, checked in October 2026.

## What is Hindsight AI memory?

**Hindsight is a memory server for LLM agents. When you send it text, an LLM pulls out facts, dates, entities and relationships and stores them in isolated memory banks. When the agent needs context, Hindsight searches those banks four ways at once and returns the best matches within a token budget.**

The README frames the goal as agents that "learn over time," not only agents that replay chat history. That's the main design choice. Most memory layers stop at storing and searching facts. Hindsight adds a background step that merges related facts into **observations** (beliefs backed by evidence), and a reflect call that reasons over them.

The design is described in the paper [Hindsight is 20/20: Building Agent Memory that Retains, Recalls, and Reflects](https://arxiv.org/abs/2512.12818) (Latimer et al., December 2025). The paper names two parts: **TEMPR** (Temporal Entity Memory Priming Retrieval), which handles retain and recall, and **CARA** (Coherent Adaptive Reasoning Agents), which handles reflect.

For where this fits among memory types in general, see [AI agent memory explained](/articles/ai-agent-memory-explained/).

## How Hindsight stores memories

### Memory banks

A **memory bank** is an isolated store, usually one per user or per agent. Banks don't share data. The docs give two patterns for multi-user apps: one bank per user (strongest isolation, no cross-user queries), or one shared bank with tags like `user:alice` that you filter on at recall time.

Each bank can carry **disposition traits** (skepticism, literalism and empathy, each on a 1-5 scale) and a mission. These only shape reflect, not storage.

### Four kinds of memory

The README lists four memory types:

| Type | What it holds | Where it comes from |
|---|---|---|
| **World facts** | Facts about people, places and things | Extracted by an LLM at retain time |
| **Experiences** | What the agent itself did or saw | Extracted at retain time |
| **Observations** | Deduplicated beliefs with supporting quotes and a proof count | Background consolidation of many facts |
| **Mental models** | Standing answers to questions you define | Synthesized from observations and facts, refreshed in the background |

**Observations** are refined, not overwritten. When new evidence arrives, the consolidation engine updates the existing observation and keeps the history. A near-duplicate check (cosine threshold 0.97 by default) merges observations that say the same thing in different words.

**Mental models** are the cheapest read. The README says reading one is a database read with no retrieval and no LLM call. A **knowledge page** is a mental model with a folder location and document-style defaults, meant to be browsed like a wiki.

### The graph is event-centric

Hindsight's graph isn't a classic triple store. The FAQ describes memories as the anchor: entities attach to the memories they appear in, and memories link to each other through shared entities, precomputed semantic neighbors and extracted causal links (`causes`, `enables`, `prevents`). Entities never link directly to other entities.

That choice keeps history. If Alice changes jobs, the old memory still says she worked at Acme, and a new one says she works somewhere else. Nothing has to be deleted or rewritten. The tradeoff is that you can't run arbitrary entity-to-entity path queries the way you would in Neo4j. For that style, see [knowledge graphs for AI memory](/articles/ai-memory-knowledge-graph/).

## How retain, recall and reflect work

### Retain

`retain` takes raw content, a conversation or a document. An LLM extracts facts, time data, entities and relationships, then Hindsight normalizes them into canonical entities, time series and search indexes. The docs recommend sending a whole conversation as one document with a stable ID and re-retaining it as it grows; the same ID replaces the old facts instead of duplicating them. They also say not to pre-summarize, since a message like "yes, option 2" means nothing without the surrounding turns.

### Recall

`recall` runs **four retrieval strategies in parallel**:

1. **Semantic**: vector similarity.
2. **Keyword**: BM25, for exact names and IDs.
3. **Graph**: links through shared entities, semantic neighbors and causal edges.
4. **Temporal**: time-range filtering for questions like "what happened last spring."

Results are merged with reciprocal rank fusion, reranked with a cross-encoder, and trimmed to a `max_tokens` budget (4,096 by default). The FAQ gives typical latency of 50-100 ms without reranking and 200-500 ms with it.

### Reflect

`reflect` is an agent loop that searches mental models first, then observations, then raw facts, and writes an answer shaped by the bank's disposition. It returns citations for which memories informed the answer and can return structured output against a schema. The FAQ puts reflect at 1-10 seconds, against 50-500 ms for recall. Use recall when your own prompt will do the reasoning; use reflect when you want a grounded answer back.

### A minimal Python example

This uses the `hindsight-client` package against a local server on port 8888, matching the [Python SDK docs](https://hindsight.vectorize.io/sdks/python):

```python
from hindsight_client import Hindsight

client = Hindsight(base_url="http://localhost:8888")

# Store a memory; an LLM extracts facts and entities on the server
client.retain(
    bank_id="user-123",
    content="Alice moved to Berlin in March and now works at a robotics startup.",
    document_id="chat-2026-10-08",
)

# Search: returns ranked memories within a token budget
results = client.recall(bank_id="user-123", query="Where does Alice live?", max_tokens=2048)
for r in results.results:
    print(r.type, r.text)

# Reason over memories and get an answer back
answer = client.reflect(bank_id="user-123", query="What should I know before calling Alice?")
print(answer.text)
```

Clients also exist for Node.js/TypeScript (`@vectorize-io/hindsight-client`) and Go, plus a CLI and REST API.

## Deployment, models and integrations

**Deployment.** The README lists Docker (`ghcr.io/vectorize-io/hindsight:latest`, API on 8888, UI on 9999), Docker Compose with an external PostgreSQL, `pip install hindsight-api` on bare metal, a Helm chart for Kubernetes, and an embedded Python server (`pip install hindsight-all`). Storage is PostgreSQL with pgvector, or Oracle AI Database 23ai. Self-hosting needs Python 3.11+ and 4 GB of RAM minimum (8 GB recommended), per the FAQ.

**LLM providers.** Retain and reflect need an LLM. Hindsight supports 25+ providers set through `HINDSIGHT_API_LLM_PROVIDER`: OpenAI, Anthropic, Gemini, Groq, Bedrock, Vertex AI, DeepSeek, local Ollama, LM Studio and llama.cpp, any OpenAI-compatible endpoint, and LiteLLM. It can also run on a Claude Code or Codex subscription instead of an API key.

**MCP.** Every bank gets its own MCP endpoint at `/mcp/{bank_id}/`, so Claude Code, Cursor and other MCP clients can use it directly. The endpoint is open by default; you turn on API-key auth with a tenant extension.

**Integrations.** The README lists 60+, including LangGraph, LlamaIndex, CrewAI, Pydantic AI, the OpenAI Agents SDK, Google ADK and Vercel AI SDK; coding agents such as Claude Code, Codex, Cursor and Cline; no-code tools like n8n and Dify; and memory-provider plugins for Hermes Agent and OpenClaw. A LiteLLM wrapper adds automatic recall and retain to existing OpenAI or Anthropic clients.

**Safety features.** An opt-in **Memory Defense** policy scans retained content against 45 patterns for secrets and PII and redacts or blocks matches. That's useful context for [memory poisoning risks](/articles/ai-memory-injection/), though pattern scanning won't catch a well-written malicious instruction.

## Benchmarks: what the numbers say

The paper reports results on LongMemEval and LoCoMo:

- With the open-source **GPT-OSS-20B** as backbone, the abstract says Hindsight "lifts overall accuracy from 39% to 83.6%" against a full-context baseline on the same model.
- With **GPT-OSS-120B** running memory and **Gemini-3 Pro** writing the final answers, Hindsight reached **91.4%** on LongMemEval and **89.61%** on LoCoMo.

The README says these results were "independently reproduced by research collaborators" at Virginia Tech's Sanghani Center and The Washington Post, and that other vendors' scores are self-reported. Read that carefully: collaborators are not an arm's-length audit, and the paper's results are the authors' own. Scores across memory systems also use different answer models, judges and settings, so a table of vendor numbers isn't a fair race. The [LLM memory evaluation guide](/articles/llm-memory-evaluation/) explains how these benchmarks work and why a small test on your own data matters more.

## Limits and tradeoffs

Hindsight is a heavier system than a vector store or a markdown file. Its real costs:

- **Every retain calls an LLM.** Extraction and consolidation cost tokens and add write latency. Async retain moves it off the request path, and the docs say provider batch APIs (OpenAI, Groq) cut extraction cost by 50% with up to 24-hour delay.
- **You run a database.** Self-hosting means PostgreSQL with pgvector (or the embedded `pg0`), workers and migrations. The FAQ documents "zombie" background tasks after Docker restarts if `HINDSIGHT_API_WORKER_ID` isn't stable.
- **Small models extract worse.** Fact quality depends on the extraction model. The docs point to a model leaderboard, but a weak local model will produce weaker memories.
- **No direct entity-to-entity graph.** If your use case is ontology queries ("all suppliers two hops from X"), a property graph fits better.
- **Cross-bank queries are client-side.** The docs note multi-bank queries need your own orchestration.
- **Reflect is slow for hot paths.** At 1-10 seconds, it suits background work or answers a user waits for, not every turn of a voice agent.
- **Overkill for simple flows.** The README itself says Hindsight "may be overkill" for simple workflows like those built in n8n.

## When another tool fits better

| If you need | Consider | Why |
|---|---|---|
| Explicit fact validity windows in a graph DB | Graphiti / Zep | Bi-temporal edges on Neo4j or FalkorDB; query what was true at a date |
| A simple user-fact API with wide integrations | Mem0 | Lighter model; runs in-process as a library |
| An agent that edits its own memory blocks | Letta | Full stateful agent runtime, memory in the context window |
| Instructions for one coding agent on one repo | CLAUDE.md or AGENTS.md | A checked-in file is simpler, reviewable and free |
| Peer and user modeling across agents | Honcho | Built around reasoning about users and peers |

Hindsight is a reasonable choice when an agent runs long-lived, open-ended work and should change behavior from feedback: support agents, AI employees, coding agents that share lessons across a team. It's less compelling when a static profile or a document search would do. The [LLM memory comparison](/articles/llm-memory-comparison/) puts it side by side with ten other systems, and [Mem0 vs Hindsight](/articles/mem0-vs-hindsight/) compares it head to head with the most-used memory layer, including token cost per retrieval.
