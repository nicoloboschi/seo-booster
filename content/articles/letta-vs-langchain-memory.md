---
title: "Letta vs LangChain Memory: Harness vs Library (2026)"
description: "Letta vs LangChain memory in 2026: Letta Code's self-editing, git-backed memory files versus LangGraph checkpointers, stores and Deep Agents. When to pick each."
date: 2026-06-16
lastmod: 2026-10-08
slug: letta-vs-langchain-memory
cluster: agent-memory
tags:
  - Letta
  - LangChain
  - LangGraph
  - MemGPT
  - agent memory
keywords:
  - "letta vs langchain memory"
  - "letta vs langchain"
  - "letta vs langgraph"
  - "memgpt vs langchain memory"
  - "letta memory vs langgraph store"
faq:
  - question: "What is the difference between Letta and LangChain memory?"
    answer: "Letta is an agent harness where the agent manages its own memory: memory is stored as git-backed Markdown files that the agent edits, with background 'dreaming' to consolidate it. LangChain gives you storage primitives in Python, a LangGraph checkpointer for thread history and a store for long-term data, and your code decides what to save."
  - question: "Can I use Letta from Python like LangChain?"
    answer: "Not for new projects. Letta's FAQ says its Agent SDK is TypeScript only, and the Python letta-client package is marked deprecated. LangChain and LangGraph are Python-first, with JavaScript versions as well."
  - question: "Is Letta the same as MemGPT?"
    answer: "Letta was built by the MemGPT researchers and grew from the 2023 MemGPT paper, which had the LLM page information in and out of its own context. In 2026 the main Letta product is Letta Code, which replaced the older Python API server."
---

**Letta vs LangChain memory** is a choice between a harness and a library. **Letta** runs the agent for you and lets it edit its own memory, stored as git-backed Markdown files. **LangChain** gives you Python building blocks: a LangGraph checkpointer for chat history and a store for long-term facts. Your code decides what goes in.

Older comparisons describe Letta as a Python server with memory blocks and LangChain as `ConversationBufferMemory`. Both pictures are out of date. Letta retired its Python API server in 2026, and LangChain deprecated its memory classes. This page compares what each ships as of October 2026.

## What is the difference between Letta and LangChain memory?

**Letta memory is agent-managed: the model reads and rewrites its own memory files, and background agents consolidate them. LangChain memory is developer-managed: LangGraph saves thread state with a checkpointer and JSON documents in a store, and your code or tools decide what to write and when to read it.**

That one difference drives most others. With Letta, you get opinions: memory layout, self-editing tools, consolidation. With LangChain, you get storage and wire the memory policy yourself, or adopt LangChain's own opinionated harness, Deep Agents.

## How Letta handles memory in 2026

Letta grew out of the [MemGPT paper](https://arxiv.org/abs/2310.08560) (Packer et al., 2023), which treated the context window like RAM and let the LLM page data in and out with function calls. The idea survives; the product changed. Per the [Letta Code repository](https://github.com/letta-ai/letta-code), the main product is now **Letta Code**: a CLI, desktop app, App Server and TypeScript Agent SDK. The `letta-ai/letta` README says its `archive` branch holds "the retired Letta V1 API server."

Letta's memory now has these parts:

- **MemFS**: memory as Markdown files with YAML front matter in a git repository. Root-level files load into the system prompt each turn; subfolders load on demand. Every edit is a commit.
- **Message search**: the full conversation history, searchable by the agent.
- **Dreaming** (formerly sleep-time agents): background subagents that review recent conversations and update memory.
- **Skills**: reusable instruction files the agent learns and stores.

For Python developers, this is the main friction. Letta's FAQ says the Agent SDK is TypeScript only. The `letta-client` Python package still talks to the REST API, but its docs mark it deprecated. Our [Letta guide](/articles/letta-ai-guide/) covers setup, the memory model and pricing in detail.

## How LangChain handles memory in 2026

LangChain's memory lives in LangGraph. The [LangChain short-term memory docs](https://docs.langchain.com/oss/python/langchain/short-term-memory) describe two layers:

- **Checkpointer**: saves agent state per `thread_id` (InMemory, SQLite, Postgres, Redis, MongoDB). This is conversation history.
- **Store**: JSON documents under namespaces like `("users", user_id)`, with optional embedding search. This is long-term memory.

The old classes, such as `ConversationBufferMemory`, are deprecated since 0.3.1 and moved to `langchain-classic`. See [LLM memory in LangChain](/articles/llm-memory-langchain/) for the full migration map.

On top of that, LangChain offers two opinionated layers:

1. **LangMem**: memory tools and background extraction on the store. Its last PyPI release was October 2025.
2. **Deep Agents** (`deepagents`): LangChain's agent harness. Its [long-term memory](https://docs.langchain.com/oss/python/deepagents/long-term-memory) is file-based too. You route a path such as `/memories/` to a `StoreBackend` and list memory files like `/memories/AGENTS.md`, which load into the prompt.

That last point narrows the gap. If you compare Letta Code to Deep Agents, both are harnesses with file-shaped memory. If you compare Letta to plain LangGraph, you're comparing a finished memory design to storage primitives.

## Letta vs LangChain memory at a glance

| | Letta (Letta Code) | LangChain / LangGraph |
|---|---|---|
| What it is | Agent harness and runtime | Library and graph runtime; Deep Agents harness on top |
| Who decides what to remember | The agent, via memory tools and dreaming | Your code, tools you write, or LangMem |
| Always-in-context memory | Root MemFS files in the system prompt | Whatever you inject: system prompt, `memory=` files in Deep Agents |
| Conversation history | Stored per agent, searchable | Checkpointer per `thread_id` |
| Long-term storage | Git-backed Markdown files (MemFS) | Store: JSON documents, optional vector index |
| Consolidation | Built in (dreaming, `/doctor` audits) | Not built in; LangMem background manager or your own job |
| Versioning | Every memory edit is a git commit | Checkpoint history per thread; store has no version history |
| Primary SDK language | TypeScript (Python client deprecated) | Python and JavaScript |
| Self-hosting | Local backend or `letta server` App Server | Any database you run |
| License | Apache 2.0 | MIT |

## When to pick Letta, and when to pick LangChain

**Pick Letta** when the agent is the product: a long-lived assistant or coding agent that should learn about its users and itself over weeks. Memory as readable, diffable files is a real advantage for debugging. Accept that you're adopting its runtime and a TypeScript-first SDK.

**Pick LangChain/LangGraph** when you're building a Python application with specific control flow: support bots, RAG pipelines, multi-step workflows. You want to choose exactly which facts persist, where they're stored, and who can read them. Accept that the memory policy is your code.

**Pick neither as the memory layer** when you already have an agent and just want it to remember users. Dedicated memory services sit beside any framework: Mem0, Zep and [Hindsight](https://github.com/vectorize-io/hindsight) all extract facts from conversations and return relevant ones at query time, and each has LangChain or LangGraph integrations. Our comparisons of [Mem0 vs Letta](/articles/mem0-vs-letta/) and [Letta alternatives](/articles/letta-alternatives/) cover that route.

For the concepts underneath all of these, from context windows to memory tiers, start with the [AI agent memory guide](/articles/ai-agent-memory-explained/).
