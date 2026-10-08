---
title: "Letta Alternatives: 7 Agent Memory Options Compared"
description: "What Letta (formerly MemGPT) does now, why teams look for Letta alternatives, and how Mem0, Zep, Graphiti, Cognee, LangMem, Hindsight and Supermemory compare."
date: 2026-05-06
lastmod: 2026-10-08
slug: letta-alternatives
tags:
- Letta
- MemGPT
- Agent Memory
- Open Source
- Memory Comparison
keywords:
- letta alternatives
- letta alternative open source
- memgpt alternatives
- letta vs mem0
- letta vs zep
- letta vs hindsight
- agent memory comparison
faq:
- question: "What are the main alternatives to Letta?"
  answer: "Mem0, Zep and its open-source engine Graphiti, Cognee, LangMem, Hindsight and Supermemory. Unlike Letta, which runs the whole agent, most of these are memory layers you call from your own agent code through an SDK, REST API or MCP server."
- question: "Is Letta the same as MemGPT?"
  answer: "Yes. Letta is the company and project formed by the authors of the 2023 MemGPT paper, and its README describes Letta as formerly known as MemGPT. The product has since moved from a Python API server to the Letta Harness, an open-source agent runtime built around git-backed memory files."
- question: "Is Letta open source?"
  answer: "Yes. The current Letta Harness (letta-ai/letta-code) is Apache 2.0 and can run fully locally without a Letta account. Letta Cloud and the Letta API platform are paid hosted services, with a free personal tier."
---

**Letta alternatives** are memory systems you can use instead of Letta (formerly MemGPT) to give agents long-term memory. The main ones are Mem0, Zep, Graphiti, Cognee, LangMem, Hindsight and Supermemory. Most teams switch because they want a memory layer for their own agent, while Letta is now a full agent runtime that owns the loop.

This page covers what Letta does today, the common reasons to look elsewhere, a comparison table, a short section per option, and how to choose. For a deeper look at Letta itself, see the [Letta guide](/articles/letta-ai-guide/).

## What is Letta, and what do Letta alternatives replace?

**Letta is an open-source platform for stateful agents that edit their own memory, built by the team behind the MemGPT paper.** Its current product, the **Letta Harness** (formerly Letta Code), runs the agent, stores its memory as files in a git repository, and adds background "dreaming" that reviews conversations and updates memory. It's available as a CLI, desktop app, web app and SDK.

Some history helps here. The [MemGPT paper](https://arxiv.org/abs/2310.08560) (Packer et al., 2023) proposed "virtual context management": treat the LLM's context window like an operating system treats RAM, and page information in and out of slower storage. Letta grew out of that work.

The product has changed a lot since. According to the [letta-ai/letta README](https://github.com/letta-ai/letta), the old Letta V1 API server is retired and lives on an `archive` branch; active development is in `letta-ai/letta-code`. Per the [Letta docs](https://docs.letta.com/):

- **Memory blocks and MemFS.** An agent's memory is a set of Markdown files in a git repo the agent owns. Files under `system/` go into the system prompt every turn; the rest stay out of context until the agent reads them.
- **Dreaming.** Background subagents review recent conversations and consolidate lessons into memory. You configure when it triggers (every N steps, on context compaction, or off).
- **Agent SDK.** The Letta Agent SDK targets JavaScript and TypeScript projects. A Python client, `letta-client`, still exists for the Letta API.
- **Self-hosting.** The CLI and App Server can run fully locally with no Letta account. Self-hosted agents aren't reachable through chat.letta.com and aren't backed up automatically.
- **Pricing.** Free personal plan (limited agents), Pro at $20/month for up to 20 stateful agents, and an API plan at $20/month plus $0.10 per active agent per month and $0.00015 per second of tool execution, with LLM usage billed on top.

## Why teams look for Letta alternatives

These are the common reasons, based on how Letta works now:

1. **You want memory, not a runtime.** Letta runs the agent loop, tools and context. If your agent already lives in LangGraph, CrewAI, the OpenAI Agents SDK or plain Python, a memory layer you call is a smaller change.
2. **Your stack is Python.** The Python V1 server is retired. The harness ships on npm (Node.js 22.19+) and the Agent SDK is JS/TS. Python teams that self-hosted the old server face a migration either way.
3. **You want memory written by a pipeline, not by the agent.** In Letta, the agent decides what to write to its memory files. Some teams prefer automatic extraction on every message, with fixed rules for conflicts and updates.
4. **You need structured recall.** Letta memory is text files plus message search. Systems built on knowledge graphs or time-aware facts handle questions like "what changed since March?" more directly.
5. **Per-agent pricing.** The API plan charges per active agent per month. If you run one agent per end user, a usage-based memory service may cost less. Check the numbers for your own workload.

None of these make Letta a bad choice. If you want agents that persist, learn across machines and manage their own context, it's built for exactly that.

## Letta alternatives compared

| System | What it is | License | Self-host | Hosted | Memory model | SDKs / access |
|---|---|---|---|---|---|---|
| **Letta** | Agent runtime with self-edited memory | Apache 2.0 | Yes (CLI, App Server) | Letta Cloud | Memory blocks as git-backed files, dreaming | JS/TS SDK, REST API |
| **Mem0** | Memory layer | Apache 2.0 | Yes (library or Docker server) | Mem0 Platform | Extracted facts, entity linking, hybrid search | Python, Node |
| **Zep** | Managed context graph service | Commercial | Enterprise BYOC only | Zep Cloud | Temporal knowledge graph | Python, TypeScript, Go |
| **Graphiti** | Temporal knowledge graph framework | Apache 2.0 | Yes (Neo4j, FalkorDB, Neptune) | Via Zep | Bi-temporal graph with episodes | Python, MCP server |
| **Cognee** | Knowledge graph memory engine | Apache 2.0 | Yes (local, Docker) | Cognee Cloud | Graph plus embeddings | Python, CLI, MCP |
| **LangMem** | Memory toolkit for LangGraph | MIT | Yes (library) | Via LangGraph Platform | Extracted memories in a LangGraph store | Python |
| **Hindsight** | Memory server | MIT | Yes (Docker, pip) | Hindsight Cloud | Facts, experiences, observations, mental models | Python, Node, Go, REST, MCP |
| **Supermemory** | Memory and context API | MIT (repo) | Yes (local server) | Supermemory API | Extracted facts, user profiles, hybrid RAG | TypeScript SDK, REST, MCP |

Licenses are from each project's GitHub repo as of October 2026.

## Each alternative in short

### Mem0

**Mem0** is a memory layer you add to an existing agent. It comes as a library (`pip install mem0ai`), a self-hosted server via Docker Compose, or the managed Mem0 Platform. Its April 2026 algorithm extracts facts in one LLM call, only adds memories (no overwrites), links entities across memories, and scores semantic, BM25 keyword and entity matches together. Mem0's README notes its published benchmark scores come from the managed platform, which has optimizations the open-source SDK doesn't. Compare it directly in [Mem0 vs Letta](/articles/mem0-vs-letta/).

### Zep and Graphiti

**Zep** is a managed service that builds a temporal knowledge graph per user and returns a prompt-ready Context Block. Facts have validity windows, so Zep can tell current facts from outdated ones. Its open-source engine, **Graphiti**, does the graph part on your own Neo4j, FalkorDB or Neptune. Zep's old Community Edition is deprecated. See [what Zep memory is](/articles/what-is-zep-memory/) for pricing and setup.

### Cognee

**Cognee** turns documents, conversations and other data into a knowledge graph with embeddings, through `cognee.remember()` and `cognee.recall()`. It can run locally without an LLM key, using a small local extraction model. It ships an MCP server and a managed Cognee Cloud. It suits teams whose "memory" is mostly a domain knowledge base. The team's research is in a [2025 arXiv paper](https://arxiv.org/abs/2505.24478) on optimizing the interface between knowledge graphs and LLMs.

### LangMem

**LangMem** from LangChain gives agents tools to save and search memories during a conversation, plus a background manager that extracts and consolidates memories after it. It stores data in LangGraph's long-term memory store, so it's the natural pick if you already run LangGraph. It can also refine an agent's prompt over time, based on its interactions.

### Hindsight

**Hindsight** is an open-source memory server (MIT) with three operations: **retain** stores content and extracts facts, entities and time data; **recall** runs semantic, BM25 keyword, graph and temporal search in parallel and merges the results; **reflect** answers a question by reasoning over a memory bank. In the background it merges related facts into observations that keep their evidence. It runs in Docker on Postgres with pgvector, exposes an MCP endpoint per bank, and has integrations for LangGraph, CrewAI, Pydantic AI, n8n and others. The design is described in a [December 2025 paper](https://arxiv.org/abs/2512.12818). Code and docs are on [GitHub](https://github.com/vectorize-io/hindsight).

### Supermemory

**Supermemory** is a memory and context API that extracts facts from conversations, keeps user profiles, handles updates and contradictions, and combines memory with document RAG and connectors (Google Drive, Notion, Gmail and others). It's available as a hosted API, with a local server for self-hosting and plugins for coding agents. Its self-hosting docs explain what the local version includes compared with Enterprise.

## How to choose a Letta alternative

Start from what you're replacing:

- **You want Letta's model, without Letta running your agent:** look at LangMem (agent-managed memory tools inside LangGraph) or Hindsight (memory server with reasoning over memories).
- **You want simple user memory with minimal setup:** Mem0 or Supermemory.
- **Facts change and history matters:** Zep (managed) or Graphiti (self-hosted).
- **Your memory is mostly documents and domain knowledge:** Cognee.
- **You need everything self-hosted and open source:** Mem0, Graphiti, Cognee, LangMem and Hindsight all run on your infrastructure. See this [comparison of open-source memory systems](/articles/open-source-memory-systems-compared/) for more detail.

Then test with your own data. Vendor benchmark scores are mostly self-reported and use different setups, so a small evaluation on real conversations tells you more. For a broader map of memory types and tools, see [AI agent memory explained](/articles/ai-agent-memory-explained/). Vectorize also maintains a separate [Letta alternatives comparison](https://vectorize.io/articles/letta-alternatives).
