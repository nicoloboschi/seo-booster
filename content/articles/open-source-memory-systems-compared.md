---
title: "Open Source AI Memory Systems Compared: GitHub Repos"
description: "Open-source AI memory systems compared: GitHub repos, licenses, stars (Oct 2026), languages and what each is good at. Mem0, Graphiti, Cognee, Hindsight."
date: 2026-03-24
lastmod: 2026-10-08
slug: open-source-memory-systems-compared
aliases:
- /articles/agent-memory-framework-github/
- /articles/ai-long-term-memory-github/
- /articles/best-open-source-ai-memory/
- /articles/best-open-source-llm-memory/
- /articles/github-llm-persistent-memory/
- /articles/llm-memory-awesome/
- /articles/llm-memory-bank/
- /articles/llm-memory-bank-github/
- /articles/llm-memory-github/
- /articles/llm-memory-open-source/
- /articles/open-source-agent-memory-framework/
- /articles/open-source-ai-memory-system/
tags:
- Open Source
- AI Agent Memory
- LLM Memory
- GitHub
keywords:
- open source memory systems
- open source ai memory
- open source agent memory framework
- llm memory github
- best open source llm memory
- llm memory bank github
cluster: agent-memory
faq:
- question: "What is the most popular open-source AI memory system on GitHub?"
  answer: "As of 8 October 2026, Mem0 (mem0ai/mem0) has the most GitHub stars of the dedicated memory projects at about 66,800, followed by Hindsight (about 47,000), Cognee and Graphiti (about 31,500 each) and Supermemory (about 31,200). Stars measure attention, not quality or fit."
- question: "Which open-source memory systems are fully open, with no paid-only core?"
  answer: "Graphiti, Hindsight, LangMem, Letta Code and Cognee's core can all be self-hosted from source under Apache-2.0 or MIT. Watch for open-core limits: Mem0 moved graph memory to its paid platform, Cognee's Postgres graph backend is a demo with a licensed production version, and Supermemory's local server is a free binary whose source isn't public."
- question: "What is an LLM memory bank?"
  answer: "A memory bank is an isolated store of memories for one user, agent or project. The term comes from the MemoryBank paper (Zhong et al., 2023) and is used by Hindsight (memory banks), Google's Vertex AI Agent Engine (Memory Bank) and several coding-agent setups that keep project notes in markdown files."
---

The leading **open-source AI memory systems** on GitHub are Mem0, Hindsight, Graphiti, Cognee, Letta, LangMem, MemOS, Memori, Honcho, Basic Memory and Memobase. Most are Apache-2.0 or MIT, written in Python, and self-hostable with Docker. They differ in storage (vectors, graphs, files), in how much is truly open versus paid, and in what they're built for.

This page covers only open-source projects: repos, licenses, stars, languages and strengths. Star counts and licenses come from the GitHub API on **8 October 2026**. For hosted options and benchmarks, see the [LLM memory comparison](/articles/llm-memory-comparison/). For background, see [AI agent memory explained](/articles/ai-agent-memory-explained/).

## What is an open-source AI memory system?

**An open-source AI memory system is a library or server, published under an open license, that stores what an LLM agent learns from conversations and work, then retrieves relevant memories into later prompts.** You can read the code, run it on your own infrastructure, and keep memory data under your control. Most also offer a paid hosted version.

## Open-source memory systems on GitHub: the table

| Project | Repo | License | Stars (8 Oct 2026) | Main language | Good at |
|---|---|---|---|---|---|
| Mem0 | [mem0ai/mem0](https://github.com/mem0ai/mem0) | Apache-2.0 | 66,802 | Python | Drop-in user, session and agent memory for chat apps |
| Hindsight | [vectorize-io/hindsight](https://github.com/vectorize-io/hindsight) | MIT | 47,001 | Python | Agents that learn over time; fact vs experience separation, `reflect` |
| Cognee | [topoteretes/cognee](https://github.com/topoteretes/cognee) | Apache-2.0 | 31,588 | Python | Knowledge graphs from docs, code and conversations; runs without an LLM key |
| Graphiti | [getzep/graphiti](https://github.com/getzep/graphiti) | Apache-2.0 | 31,541 | Python | Temporal knowledge graphs where facts have validity windows |
| Supermemory | [supermemoryai/supermemory](https://github.com/supermemoryai/supermemory) | MIT (see note) | 31,155 | TypeScript | Memory + RAG + connectors behind one API; coding-agent plugins |
| Letta | [letta-ai/letta](https://github.com/letta-ai/letta) / [letta-code](https://github.com/letta-ai/letta-code) | Apache-2.0 | 25,073 / 3,543 | TypeScript (letta-code) | Stateful agents that edit their own memory, skills and prompts |
| Memori | [MemoriLabs/Memori](https://github.com/MemoriLabs/Memori) | Apache-2.0 | 17,103 | Python | Memory on your existing SQL database through a wrapped LLM client |
| MemOS | [MemTensor/MemOS](https://github.com/MemTensor/MemOS) | Apache-2.0 | 11,754 | TypeScript (per GitHub) | Memory "operating system" with memory cubes, skill reuse, OpenClaw/Hermes plugins |
| Honcho | [plastic-labs/honcho](https://github.com/plastic-labs/honcho) | AGPL-3.0 | 7,519 | Python | Modeling users, agents and groups ("peers") over time |
| Basic Memory | [basicmachines-co/basic-memory](https://github.com/basicmachines-co/basic-memory) | AGPL-3.0 | 4,115 | Python | Local markdown knowledge base shared by you and your AI over MCP |
| Memobase | [memodb-io/memobase](https://github.com/memodb-io/memobase) | Apache-2.0 | 2,925 | Python | User profiles and event timelines for chatbots, low-latency reads |
| Microsoft Kernel Memory | [microsoft/kernel-memory](https://github.com/microsoft/kernel-memory) | MIT | 2,233 | C# | .NET memory and RAG; labeled a research project |
| LangMem | [langchain-ai/langmem](https://github.com/langchain-ai/langmem) | MIT | 1,697 | Python | Memory tools and background manager for LangGraph agents |
| MemoryOS | [BAI-LAB/MemoryOS](https://github.com/BAI-LAB/MemoryOS) | Apache-2.0 | 1,594 | Python | Research system (EMNLP 2025 Oral) for personalized agent memory |

Stars measure attention, not quality. LangMem has few stars because it ships as part of the LangChain ecosystem; Letta's older `letta` repo holds most of its stars while new work happens in `letta-code`. One project with a familiar name, [Memary](https://github.com/kingjulio8238/Memary), hasn't had a commit since October 2024.

## How open is "open source"? Read the fine print

Several projects are **open core**: the repo is open, but some features or the best-performing version are paid. Check these before you build on one.

- **Mem0:** graph memory was removed from the open-source SDK in v3 and "is not being replaced by an OSS equivalent." Mem0 also says its April 2026 benchmark scores come from the managed platform with "proprietary optimizations not available in the open-source SDK."
- **Zep:** Zep Community Edition is deprecated and moved to a `legacy/` folder. **Graphiti** is the open-source part; Zep itself is a managed service.
- **Supermemory:** the repo is MIT, but its self-hosting docs say the local server's "source is not in the public repository." It's a free binary under a "lite license," not code you can build.
- **Cognee:** the core is Apache-2.0, but running the graph store on Postgres is a demo; "the production-ready version is available as a licensed product."
- **Letta:** the Letta V1 API server is retired to an `archive` branch. Current development is the Letta Code harness, which defaults to Letta Cloud but has a local backend.
- **Hindsight:** MIT; its pricing page lists self-hosting as free with no usage limits. The paid part is the managed cloud.
- **AGPL projects (Honcho, Basic Memory):** free to self-host, but if you modify them and offer them as a network service, AGPL-3.0 requires you to publish your changes. Many companies' legal teams treat AGPL differently from MIT or Apache.

## What each open-source memory system is built for

### Mem0

Extracts facts from conversations and stores them per user, session or agent. Runs as a library (local Qdrant and SQLite by default), a Docker server (Postgres + pgvector), or Mem0's cloud. Hybrid BM25 and entity search need the `[nlp]` extra. Good first choice for chat personalization. More in [what is Mem0](/articles/what-is-mem0-ai/) and [Mem0 alternatives](/articles/mem0-alternatives-compared/).

### Hindsight

Built by Vectorize. Organizes memory into world facts, the agent's experiences, consolidated observations and mental models, with `retain`, `recall` and `reflect` operations. Recall runs semantic, BM25, graph and temporal search in parallel. Ships as Docker, pip, Helm or an embedded Python package, with clients for Python, Node.js, Go and a CLI, and a built-in MCP endpoint per bank. Its own README says it may be overkill for simple workflows. Described in the paper [Hindsight is 20/20](https://arxiv.org/abs/2512.12818).

### Graphiti

Builds temporal knowledge graphs: entities, facts with validity windows, and the raw episodes they came from. Old facts are invalidated, not deleted, so you can query past states. Needs a graph database (Neo4j, FalkorDB or Amazon Neptune; Kuzu support is deprecated). Includes an MCP server. See [Zep alternatives](/articles/zep-alternatives/) and [knowledge graphs for AI memory](/articles/ai-memory-knowledge-graph/).

### Cognee

Turns text, code and conversations into a graph plus vector index, with file-based defaults (SQLite, LanceDB, Kuzu) so it runs with no setup. Version 1.6.0 (September 2026) added keyless workflows using local models. It has plugins for Claude Code, Codex and OpenClaw. See [Mem0 vs Cognee](/articles/mem0-vs-cognee/) and [Cognee alternatives](/articles/cognee-alternatives/).

### Supermemory

The main repo is TypeScript and MIT licensed, and its plugins for Claude Code, Cursor, Codex, OpenCode and OpenClaw are separate open-source repos. The memory engine you self-host is the free local binary noted above, not code from the repo. See [Supermemory explained](/articles/supermemory-long-term-ai-memory-as-a-service/).

### Letta

From the authors of [MemGPT](https://arxiv.org/abs/2310.08560). Letta Code agents keep memory in MemFS, a git-backed filesystem, and rewrite their own memory, skills and prompts. Best when you want the whole agent runtime, not just a memory layer. See [Letta alternatives](/articles/letta-alternatives/).

### LangMem

Memory tools an agent calls during a conversation, plus a background manager that extracts and consolidates memories, on top of LangGraph's store. Least effort if you already run LangGraph. See [LLM memory with LangChain](/articles/llm-memory-langchain/).

### Smaller and specialized projects

- **Honcho**: peer-centric memory with background reasoning, on Postgres + pgvector. See [Honcho LLM memory](/articles/honcho-llm-memory/).
- **MemOS**: memory cubes, async ingestion, local SQLite plugins for OpenClaw and Hermes Agent.
- **Memori**: stores agent state in your own database ("BYODB"); its older home was GibsonAI. See [Memori by GibsonAI](/articles/ai-agents-memory-storage-memori-gibsonai/).
- **Basic Memory**: plain markdown files plus a local SQLite index, exposed over MCP.
- **Memobase**: a profile and event timeline per user, built on FastAPI, Postgres and Redis.

## What is an LLM memory bank?

**A memory bank is an isolated store of memories for one user, agent or project.** The idea goes back to [MemoryBank](https://arxiv.org/abs/2305.10250) (Zhong et al., 2023), which added long-term memory to chatbots and used a forgetting mechanism inspired by the Ebbinghaus forgetting curve. Today the word shows up in three places:

- **Hindsight** calls each isolated store a bank, with strict isolation between banks.
- **Google's Vertex AI Agent Engine** has a managed Memory Bank; see [Vertex AI Agent Engine Memory Bank](/articles/vertex-ai-agent-engine-memory-bank/).
- **Coding-agent "memory bank" setups** keep project notes in markdown files that the agent reads at the start of each session.

People searching GitHub for "awesome LLM memory" lists will find several, but as of October 2026 the ones we checked were small (under 10 stars). The repos in the table above are a better starting point.

## How to try an open-source memory system in ten minutes

Cognee's quickstart runs fully local, with no API key:

```python
# pip install "cognee[gliner]"
import asyncio
import cognee

async def main():
    # Extracts a small graph and embeds the text with local models
    await cognee.remember(
        "Marie Curie was born in Warsaw and worked at the University of Paris.",
        dataset_name="local_quickstart",
    )
    results = await cognee.recall(
        "Where was Marie Curie born?",
        datasets=["local_quickstart"],
    )
    for result in results:
        print(result)

asyncio.run(main())
```

To pick a repo for production, run through this list:

1. **Check the license** against how you'll ship (internal tool, SaaS, on-prem product).
2. **Check what's gated**: read the pricing page for features that are cloud-only.
3. **Check activity**: recent commits, open issues and release notes in the last 90 days.
4. **Check dependencies**: Postgres only, or also a graph DB, Redis and a vector DB?
5. **Check the LLM cost per write**: most systems call an LLM on every memory add.
6. **Run your own test**: 20-50 real questions on your data, with two candidates.

For a decision guide by use case, see [the best AI memory framework for your agent](/articles/best-ai-memory-framework/).
