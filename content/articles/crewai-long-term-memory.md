---
title: "CrewAI Long-Term Memory: The Unified Memory Class"
description: "How CrewAI long-term memory works since v1.10: one Memory class with scopes, LanceDB storage, composite recall scoring, embedder setup, and how to reset it."
date: 2026-03-31
lastmod: 2026-10-08
slug: crewai-long-term-memory
cluster: agent-memory
tags:
  - CrewAI
  - agent memory
  - long-term memory
  - multi-agent systems
keywords:
  - "crewai long term memory"
  - "crewai memory"
  - "crewai unified memory"
  - "crewai memory storage"
  - "crewai reset memory"
  - "crewai mem0"
faq:
  - question: "How does long-term memory work in CrewAI?"
    answer: "Since CrewAI 1.10 (February 2026), one Memory class stores everything. An LLM tags each saved item with a scope, categories and an importance score, and the item is embedded into a local LanceDB store. Recall ranks results by a mix of semantic similarity, recency and importance. Set memory=True on a Crew to recall before each task and save facts after it."
  - question: "Where does CrewAI store memory?"
    answer: "By default in ./.crewai/memory, as a LanceDB vector store. You can override the location with the storage argument of Memory or the CREWAI_STORAGE_DIR environment variable, or plug in your own backend through the StorageBackend protocol."
  - question: "Does CrewAI still have short-term, long-term and entity memory?"
    answer: "No. In current releases those separate classes, along with ExternalMemory, are gone. The docs describe a single Memory class that replaces short-term, long-term, entity and external memory. Older tutorials and some third-party integrations still target the pre-1.10 API."
---

**CrewAI long-term memory** is handled by one `Memory` class. You save text with `remember()` and get it back with `recall()`. An LLM tags each item with a scope, categories and an importance score, and CrewAI embeds it into a local LanceDB store. Turn on `memory=True` on a `Crew` and it recalls context before each task and saves facts after it.

That's the design since **CrewAI 1.10** (released February 27, 2026). Before it, CrewAI had separate short-term, long-term, entity and external memory, with SQLite for task results. Most tutorials online still show that older API, which no longer exists in current releases (1.15 as of October 2026). Facts here come from the [CrewAI memory docs](https://docs.crewai.com/en/concepts/memory) and the installed package.

## What is CrewAI long-term memory?

**CrewAI long-term memory is the persistent store that lets crews and agents reuse what they learned in earlier runs. In current CrewAI it is a single Memory object: records are LLM-analyzed, embedded, stored in LanceDB on disk, organized in a tree of scopes, and recalled by a score that blends similarity, recency and importance.**

It's "long-term" because it survives across `kickoff()` calls and process restarts, as long as the storage directory survives. Within a single task, the agent's working context is still its prompt, bounded by the model's [context window](/articles/context-window-of-an-llm/).

## How CrewAI memory changed in 1.10

| Before 1.10 | 1.10 and later |
|---|---|
| `ShortTermMemory` (ChromaDB vector store of recent context) | Replaced by `Memory` |
| `LongTermMemory` (SQLite table of task results) | Replaced by `Memory` |
| `EntityMemory` (people, places, concepts) | Replaced by `Memory` categories and scopes |
| `ExternalMemory` (e.g. Mem0 as a provider) | Removed; use a custom `StorageBackend` or call the provider yourself |
| `memory_config={"provider": "mem0"}` | Removed |
| Default OpenAI embedder `text-embedding-ada-002` (1536 dims) | `text-embedding-3-large` (3072 dims) |

In `crewai` 1.15, the `crewai.memory` package exports `Memory`, `MemoryScope`, `MemorySlice` and related types; the old classes are not there. If you upgrade with old local data, the docs warn about an **embedding dimension mismatch**. Either reset memory or pin the older embedder.

The change also breaks integrations built on `ExternalMemory`. Mem0's [CrewAI guide](https://docs.mem0.ai/integrations/crewai) now calls the Mem0 client directly, outside CrewAI's memory, and notes the removed `memory_config` shortcut. Hindsight's `hindsight-crewai` package pins `crewai<1.10` for the same reason. Check any memory plugin's supported CrewAI version before relying on it.

## Using memory in a crew

The simplest setup is `memory=True`, which uses defaults. For control, pass a configured `Memory`:

```python
from crewai import Agent, Crew, Memory, Process, Task

memory = Memory(
    storage="./crew_memory",      # default: ./.crewai/memory or $CREWAI_STORAGE_DIR/memory
    recency_half_life_days=14,    # default 30
)

researcher = Agent(
    role="Researcher",
    goal="Find facts about the customer's account",
    backstory="Careful analyst.",
    memory=memory.scope("/agent/researcher"),  # private branch of the memory tree
)

task = Task(
    description="Summarize open issues for ACME Corp.",
    expected_output="A short list of issues.",
    agent=researcher,
)

crew = Crew(agents=[researcher], tasks=[task], memory=memory, process=Process.sequential)
crew.kickoff()
```

When memory is on, the crew recalls relevant records **before** each task and extracts facts from the output **after** it. Saves run on a background thread; `kickoff()` waits for pending writes before it returns. Agents without their own memory use the crew's.

### Using Memory directly

You can also use `Memory` outside a crew, which helps for testing what it stored:

```python
from crewai import Memory

memory = Memory()
memory.remember("ACME renewed their contract in March; they want SSO next.",
                scope="/customers/acme", source="user:alice")

for match in memory.recall("What does ACME want next?", scope="/customers/acme", limit=5):
    print(f"[{match.score:.2f}] {match.record.content}")
```

Inside a CrewAI Flow, the same calls are available as `self.remember()`, `self.recall()` and `self.extract_memories()`.

## How CrewAI recall works

Each saved record goes through an LLM (default `gpt-4o-mini`) that infers its scope, categories and importance. On save, **consolidation** checks for near-duplicates (default similarity threshold 0.85) and merges or drops them. `remember_many()` queues a batch in the background and drops in-batch duplicates at 0.98 similarity.

Recall ranks by a **composite score**:

| Signal | Default weight |
|---|---|
| Semantic similarity | 0.5 |
| Recency (30-day half-life) | 0.3 |
| Importance | 0.2 |

`recall()` has two depths. `depth="shallow"` is a direct vector search with that scoring and no LLM calls. `depth="deep"` (the default) runs a multi-step recall flow with LLM query analysis, though queries under 200 characters skip the analysis step. Use shallow when latency matters more than precision.

The weighting is a reasonable heuristic, similar to the recency-importance-relevance scoring from the Generative Agents paper. It isn't time-aware in a stronger sense: an old fact and a newer, contradicting one can both come back, and the higher-scored one wins. For why that matters, see [temporal reasoning in AI memory](/articles/temporal-reasoning-ai-memory/).

## Scopes, privacy and multi-agent isolation

Records live in a **tree of scopes**, like `/company/knowledge` or `/agent/writer`. Two tools control who sees what:

- `memory.scope("/agent/researcher")` returns a view restricted to one subtree.
- `memory.slice(scopes=[...], read_only=True)` reads from several branches; writing to a read-only slice raises `PermissionError`.

Records can also be private. `remember(..., source="user:alice", private=True)` hides a record from recall unless the caller passes the same `source`. For multi-user apps, put the user ID in the scope or source on every call. CrewAI won't infer it.

## Storage, embedders and reset commands

**Storage.** The built-in backend is LanceDB on local disk, with a Qdrant Edge option. You can supply your own backend by implementing the `StorageBackend` protocol (`save`, `search` and friends) and passing it as `storage=`. That's the path for a shared database when several workers run the same crew.

**Embedders.** The default is OpenAI `text-embedding-3-large`. Pass `embedder={"provider": "ollama", "config": {"model_name": "mxbai-embed-large"}}` to run locally. The docs list OpenAI, Azure, Google, Vertex, Cohere, VoyageAI, Bedrock, Hugging Face, Jina, WatsonX and sentence-transformers. Pair it with `Memory(llm="ollama/llama3.2")` for a fully local setup.

**Inspecting and resetting.**

- `crewai memory` opens a terminal browser of stored records.
- `crewai reset-memories -m` wipes memory from the CLI.
- `crew.reset_memories(command_type="memory")`, `memory.reset()` or `memory.forget(scope="/project/old")` do it in code.
- `memory.tree()` and `memory.info("/path")` show record counts per scope.

## When CrewAI's built-in memory is enough

For a single crew on one machine, built-in memory works well. It's local, it needs no extra service, and the scope tree maps cleanly to multi-agent roles.

The limits appear at scale. LanceDB on local disk doesn't share across servers unless you write a backend. Memory quality depends on the analysis LLM. And there's no built-in notion of facts that expire or get replaced. Teams that need shared, multi-tenant memory across many crews usually move it to a separate service; our comparison of [open-source memory systems](/articles/open-source-memory-systems-compared/) and the general [AI agent memory guide](/articles/ai-agent-memory-explained/) cover the options. For how CrewAI's memory compares to other frameworks' defaults, see the [AI agent framework comparison](/articles/ai-agent-framework-comparison/).
