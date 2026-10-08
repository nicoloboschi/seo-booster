---
title: "AI Agent Long-Term Memory: How It Works, How to Build It"
description: "How long-term memory works in AI agents: does AI have it, the index-retrieve-read pipeline, what LongMemEval found, its limits, and a LangMem example."
date: 2026-03-25
lastmod: 2026-10-08
slug: ai-agent-long-term-memory
aliases:
- /articles/agentic-ai-long-term-memory/
- /articles/ai-agent-chatbot-long-term-memory-note-storage-telegram/
- /articles/ai-agent-long-memory/
- /articles/ai-agent-that-remembers/
- /articles/ai-and-long-term-memory/
- /articles/building-long-term-memory-in-agentic-ai/
- /articles/deepseek-ai-agent-telegram-long-term-memory/
- /articles/does-ai-have-long-term-memory/
- /articles/giving-a-long-term-memory/
- /articles/helping-ai-have-long-term-memory/
- /articles/how-does-long-term-memory-work-in-ai/
- /articles/is-there-a-limit-to-long-term-memory/
- /articles/llm-memory-long-term/
- /articles/long-term-memory-ai-agent/
- /articles/long-term-memory-ai-model/
- /articles/long-term-memory-for-ai/
- /articles/long-term-memory-for-ai-agents/
- /articles/long-term-memory-in-ai/
- /articles/long-term-memory-in-ai-agents/
- /articles/long-term-memory-model-ai/
- /articles/long-term-memory-the-foundation-of-ai-self-evolution/
- /articles/when-will-ai-have-long-term-memory/
tags:
- Long-Term Memory
- AI Agent Memory
- Agentic AI
- LongMemEval
- LangMem
keywords:
- AI agent long-term memory
- long-term memory for AI agents
- does AI have long-term memory
- how does long-term memory work in AI
- building long-term memory in agentic AI
- LLM long-term memory
cluster: agent-memory
faq:
- question: "Does AI have long-term memory?"
  answer: "Language models themselves don't: they keep general knowledge in their weights but forget each conversation when the call ends. AI products and agents get long-term memory from software around the model, which saves facts and events to a database and retrieves the relevant ones into later prompts."
- question: "How does long-term memory work in AI agents?"
  answer: "In three stages. Indexing turns past sessions into stored items (raw turns, extracted facts, events) with search keys. Retrieval turns the new message into a query and fetches the most relevant items. Reading has the model use those items to answer. LongMemEval (Wu et al., 2024) uses this index-retrieve-read framing."
- question: "Is there a limit to long-term memory in AI?"
  answer: "Storage is rarely the limit; a database can hold millions of memories. The practical limits are retrieval quality, how well the system handles changed or conflicting facts, extraction errors, and the token budget for memories in each prompt. Accuracy on long-term memory benchmarks still falls well short of perfect."
---

**AI agent long-term memory** is information an agent keeps across sessions: facts about users, past events, and lessons from earlier tasks. The model can't hold it, because LLMs forget each conversation when the call ends. So the agent's code writes memories to an external store and, on each new turn, retrieves the few that matter into the prompt.

Building it well comes down to a handful of design choices: what to store, how to index it, how to search it, and how the model reads what comes back. This page walks through each, using findings from the LongMemEval benchmark, then shows a working example. The pillar guide, [AI agent memory explained](/articles/ai-agent-memory-explained/), covers memory types and tools in more breadth.

## What is long-term memory in AI agents?

**Long-term memory in an AI agent is persistent storage outside the model that keeps information across conversations and sessions, scoped to a user, agent or organization. The agent writes selected facts, events and lessons into it and retrieves the relevant ones into its context window when they're needed.**

LangGraph's [memory docs](https://docs.langchain.com/oss/python/langgraph/memory) define it by scope: long-term memory "is shared *across* conversational threads" and saved under custom namespaces such as a user ID. That's the line between it and short-term memory, which ends with the thread. The comparison is in [short-term vs long-term memory in agentic AI](/articles/short-term-and-long-term-memory-agentic-ai/).

The CoALA framework ([Sumers et al., 2023](https://arxiv.org/abs/2309.02427)) splits long-term memory into three types: **episodic** (past experiences), **semantic** (facts) and **procedural** (how to act). Most chat products store semantic facts. Task agents gain the most from episodic and procedural memory.

## Does AI have long-term memory?

The model doesn't. A language model's weights hold general knowledge from training, sometimes called parametric memory, but nothing about you or yesterday's chat. Every API call starts from a blank slate.

What users experience as an AI that remembers is a system feature. ChatGPT, Claude and Gemini all ship memory features that store user information outside the model and bring it back in later chats. Agent frameworks do the same with a memory store. How one product does it is covered in [Claude's long-term memory](/articles/claude-ai-long-term-memory/).

So "when will AI have long-term memory?" has two answers. As a product feature, it already does. Inside the model itself, as weights that keep learning from each conversation, it's still a research problem: fine-tuning per user is costly, and editing weights risks damaging what the model already knows.

## How long-term memory works: index, retrieve, read

[LongMemEval](https://arxiv.org/abs/2410.10813) (Wu et al., ICLR 2025) frames every long-term memory system as three stages over a key-value store:

1. **Indexing:** turn each past session into one or more stored items (values), each with keys used for search.
2. **Retrieval:** turn the current message into a query and fetch the most relevant items.
3. **Reading:** the LLM reads the retrieved items and writes the answer.

The paper names four control points inside those stages, and tested each one. Its findings are the most useful public evidence on what actually matters.

| Control point | The choice | What LongMemEval found |
|---|---|---|
| **Value** | Store whole sessions, single rounds, or extracted facts? | Rounds beat whole sessions. Compressing into facts alone loses detail and hurts overall accuracy, though it helps multi-session reasoning |
| **Key** | Index items by their own text, or add extracted facts, keyphrases and events as extra keys? | Adding extracted user facts as keys raised recall@k by 9.4% and QA accuracy by 5.4% |
| **Query** | Use the raw question, or expand it (for example with a time range)? | Time-aware query expansion raised temporal-question recall by 6.8% to 11.3% with a strong LLM |
| **Reading** | Dump results in, or structure them and have the model take notes first? | Chain-of-Note plus a structured format improved accuracy by up to 10 points, even with perfect retrieval |

The last row is easy to miss. Even when retrieval finds the right memories, the model can still misuse them. How memories are formatted in the prompt is part of the memory system.

## How to build long-term memory for an agent

A minimal build follows these steps:

1. **Choose the scope.** Per user, per agent, per team? This becomes your namespace or ID, and it's your main privacy boundary.
2. **Decide what to keep.** Durable preferences and facts, important events, lessons from failures. Not every message.
3. **Pick write timing.** During the turn (hot path, adds latency) or after it (background, adds lag).
4. **Index for several kinds of search.** Embeddings for fuzzy matches, keywords for names and IDs, timestamps for time questions.
5. **Retrieve before each model call** and cap memory at a fixed token budget.
6. **Handle updates and deletes.** Facts change; users ask to be forgotten.
7. **Evaluate on your own data.** Write 20 to 50 real questions and check what the agent recalls.

Here's steps 3 to 5 with LangMem's background memory manager and a LangGraph store, adapted from LangMem's [background quickstart](https://langchain-ai.github.io/langmem/background_quickstart/):

```python
from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnableConfig
from langgraph.func import entrypoint
from langgraph.store.memory import InMemoryStore
from langmem import create_memory_store_manager

store = InMemoryStore(index={"dims": 1536, "embed": "openai:text-embedding-3-small"})
llm = init_chat_model("anthropic:claude-sonnet-4-5")

# Extracts, updates and consolidates memories in the store after each turn
manager = create_memory_store_manager(
    "anthropic:claude-sonnet-4-5",
    namespace=("memories", "{user_id}"),  # filled from config at runtime
)

@entrypoint(store=store)
def chat(message: str, *, config: RunnableConfig):
    user_id = config["configurable"]["user_id"]
    hits = store.search(("memories", user_id), query=message, limit=5)
    known = "\n".join(h.value["content"]["content"] for h in hits)

    messages = [
        {"role": "system", "content": f"What you know about this user:\n{known}"},
        {"role": "user", "content": message},
    ]
    response = llm.invoke(messages)
    manager.invoke({"messages": messages[1:] + [response]})  # reads user_id from config
    return response.content

cfg = {"configurable": {"user_id": "alice"}}
chat.invoke("I'm allergic to peanuts and I live in Lisbon.", config=cfg)
print(chat.invoke("Any snack ideas for my flight?", config=cfg))
```

In production, swap `InMemoryStore` for `AsyncPostgresStore` and run the manager off the request path, for example with LangMem's `ReflectionExecutor`, which can delay processing until a conversation goes quiet. The same loop works with dedicated memory services; only the search and save calls change.

## Long-term memory tools

| Tool | How it stores long-term memory | Notes |
|---|---|---|
| Mem0 | LLM-extracted facts in a vector store, with entity linking | Library or hosted platform |
| Zep / Graphiti | Temporal knowledge graph; facts carry validity windows | Graphiti is open source; Zep is the managed service |
| Letta | Agent-editable memory files in a git-backed filesystem | A full agent runtime, not a plug-in library |
| LangMem | Any LangGraph store; hot-path tools or background extraction | Best fit if you already use LangGraph |
| Cognee | Knowledge graph plus vector and relational stores | Strong on turning documents into a graph |
| [Hindsight](https://github.com/vectorize-io/hindsight) | Facts and experiences on Postgres, consolidated into observations | Adds a `reflect` operation that reasons over memories |

Picking between them depends on your data and stack; the decision guide is in [how to pick the best AI memory framework](/articles/best-ai-memory-framework/).

## Is there a limit to long-term memory in AI?

Storage isn't the limit. A database holds millions of items. The real limits are elsewhere:

- **Retrieval quality.** LongMemEval found commercial chat assistants and long-context LLMs showed "a 30% accuracy drop" on information across sustained interactions, and that long-context LLMs lose 30% to 60% of their accuracy on its LongMemEval_S setting compared with being handed only the relevant sessions.
- **Changing facts.** When a user's situation changes, systems that can't tell old from new facts return either one.
- **Extraction errors.** An LLM decides what to save. It can drop details or record things that were never said, and every bad memory gets reused.
- **Token budget.** Only a few hundred to a few thousand tokens of memory fit usefully in each prompt. More memories mean more ranking, not more context.
- **Noise and drift.** Stores that only grow get worse over time without consolidation and expiry.

Vendor accuracy numbers on these benchmarks are almost all self-reported and use different models and judges, so they aren't directly comparable. Methods for testing your own setup are in [LLM memory evaluation](/articles/llm-memory-evaluation/).

## Long-term memory and AI self-evolution

Some researchers see long-term memory as the route to agents that improve after deployment. The 2024 report [Long Term Memory: The Foundation of AI Self-Evolution](https://arxiv.org/abs/2410.15665) (Jiang et al.) argues that models need long-term memory "to store and manage processed interaction data" in order to evolve during use, not only through bigger training runs. The authors report their LTM-based multi-agent framework, OMNE, took first place on the GAIA benchmark at the time.

CoALA makes a related point from the agent side. Storing task-relevant language in memory is "cheaper and quicker than parameter updates," so most agent learning today happens in memory, not in weights. That's likely to stay true until per-user model updates become cheap and safe.
