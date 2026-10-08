---
title: "Langflow Memory Chatbot: Message History and Sessions"
description: "Build a memory chatbot in Langflow: Agent built-in memory, the Message History component, session IDs, external chat memory, and memory bases for long-term recall."
date: 2026-04-07
lastmod: 2026-10-08
slug: memory-chatbot-langflow
cluster: agent-memory
tags:
  - Langflow
  - chatbots
  - conversation memory
  - low-code
keywords:
  - "memory chatbot langflow"
  - "langflow memory"
  - "langflow message history"
  - "langflow session id"
  - "langflow memory base"
  - "langflow chat memory"
faq:
  - question: "How do I build a chatbot with memory in Langflow?"
    answer: "Use the Agent component, which has chat memory turned on by default and loads up to 100 earlier messages of the same session. For a plain Language Model flow, use a Message History component in Retrieve mode feeding a {memory} variable in a Prompt Template, and another in Store mode after Chat Output."
  - question: "Where does Langflow store chat memory?"
    answer: "In Langflow's own database, in the message table. The default is SQLite (langflow.db); set LANGFLOW_DATABASE_URL to use PostgreSQL. You can also plug Redis Chat Memory, Mem0 Chat Memory or Cassandra Chat Memory into the Message History component's External Memory input."
  - question: "Why do all my Langflow users share the same chat history?"
    answer: "Because the default session ID is the flow ID, so every chat on a flow lands in one session unless you set one. Pass a per-user session_id in the /api/v1/run request; it overrides component settings and keeps each user's memory separate."
---

A **memory chatbot in Langflow** keeps earlier messages of a session and feeds them back to the model. The **Agent** component does this by default, loading up to 100 past messages for the same `session_id`. For plain model flows, the **Message History** component retrieves and stores chat history. **Memory bases** (added in Langflow 1.10) add semantic recall across sessions.

The details below follow the [Langflow memory docs](https://docs.langflow.org/memory) for the 1.12 release line (1.12.5, October 2026) and the Langflow source code.

## What is a Langflow memory chatbot?

**A Langflow memory chatbot is a flow that stores each chat message in Langflow's database, grouped by session ID, and loads recent messages from that session into the next prompt. The Agent component handles this automatically; the Message History component does it explicitly in flows built around a Language Model component.**

Langflow gives you three levels of memory:

| Mechanism | What it recalls | Scope | Added |
|---|---|---|---|
| Agent built-in memory | Last N messages (default 100) | One session | Default for Agent |
| Message History component | Last N messages, filterable, Langflow or external storage | One session, or any session you name | Earlier releases |
| Memory base | Most relevant past messages by vector similarity | Current session by default, or all sessions | 1.10 (June 2026) |

The first two are short-term memory: a rolling window of recent messages. The third is closer to long-term memory. Our page on [short-term vs long-term memory in agentic AI](/articles/short-term-and-long-term-memory-agentic-ai/) explains the difference.

## Option 1: the Agent component's built-in memory

The [Agent docs](https://docs.langflow.org/agents) say Langflow agents "have built-in chat memory that is enabled by default." Each session gets its own context window, and the agent reads earlier messages with the same `session_id`.

The advanced setting **Number of Chat History Messages** controls how many past messages load. Its default in the Agent component code is **100**; set it to 0 to turn memory off. For most chatbots, this is all you need. You only add a Message History component when you want external storage or finer control over filtering and order.

## Option 2: the Memory Chatbot pattern with Message History

When you use a **Language Model** component instead of an Agent, wire memory yourself. The [Message History docs](https://docs.langflow.org/message-history) give this layout:

1. Add a **Message History** component in **Retrieve** mode at the start of the flow.
2. Add a **Prompt Template** with a `{memory}` variable, and connect Message History's output to it.
3. Send the Prompt Template's output to the Language Model's **System Message** input.
4. Connect **Chat Input** to the Language Model, and the Language Model to **Chat Output**.
5. Add a second **Message History** component in **Store** mode at the end, fed by Chat Output.

A flow that reads and writes history needs both components; one component does one mode.

Retrieve mode settings and defaults:

- **Number of Messages**: 100.
- **Order**: Ascending.
- **Sender Type**: Machine and User (or one of them).
- **Session ID**: empty means the current run's session.
- **Template**: formats each message, with keys like `{sender}` and `{text}`.
- **External Memory**: empty means Langflow storage.

The output comes as a `Message` (history as text for the prompt) or a `DataFrame` (for analysis).

### External chat memory

Connect a provider component to Message History's **External Memory** input to keep history outside Langflow. The docs name **Redis Chat Memory**, **Mem0 Chat Memory** and **Cassandra Chat Memory**. Use one when several Langflow instances serve the same users, or when chat data must live in a database you already run. Mem0 also extracts facts from conversations, which is a step toward user memory rather than raw history; see [what Mem0 is](/articles/what-is-mem0-ai/) for how it works.

## Session IDs: keeping users apart

Memory is grouped by `session_id`. The docs warn that **the default session ID is the flow ID**, so every chat on a flow shares one history unless you set IDs. In production, pass a session ID per user or per conversation when you call the flow:

```python
import os

import requests

BASE = "http://localhost:7860"
FLOW_ID = "your-flow-id"
HEADERS = {"x-api-key": os.environ["LANGFLOW_API_KEY"]}


def chat(message: str, session_id: str) -> str:
    resp = requests.post(
        f"{BASE}/api/v1/run/{FLOW_ID}",
        headers=HEADERS,
        json={
            "input_value": message,
            "input_type": "chat",
            "output_type": "chat",
            "session_id": session_id,  # overrides component settings
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["outputs"][0]["outputs"][0]["results"]["message"]["text"]


chat("Hi, I'm Dana and I'm vegetarian.", session_id="user-dana")
print(chat("Suggest a dinner for me.", session_id="user-dana"))  # remembers

# Read or clear one session's stored messages
msgs = requests.get(f"{BASE}/api/v1/monitor/messages",
                    headers=HEADERS, params={"session_id": "user-dana"}, timeout=30).json()
requests.delete(f"{BASE}/api/v1/monitor/messages/session/user-dana", headers=HEADERS, timeout=30)
```

The session ID in the API request takes precedence over whatever the components set. Derive it on your server from the logged-in user. Anyone who can guess another user's session ID can read their history through the flow.

## Where Langflow stores chat memory

Chat Input and Chat Output write every message to Langflow's application database:

- **Default**: SQLite, `langflow.db` for the open-source server or `database.db` for Langflow Desktop.
- **PostgreSQL**: set `LANGFLOW_DATABASE_URL`. Use this for anything multi-user or multi-instance.
- **No storage**: `LANGFLOW_USE_NOOP_DATABASE=True` stores nothing, which is handy for tests and means no memory at all.

Messages accumulate forever by default, so plan retention: delete old sessions through the monitor API, or keep chat history in an external store with its own TTL.

## Option 3: memory bases for long-term recall

Langflow 1.10 added **memory bases**. In 1.12, the built-in **Memory Chatbot** starter template uses them: Chat Input feeds an Agent, a Memory Base component is wired in as the agent's tool, and the Agent feeds Chat Output. A [memory base](https://docs.langflow.org/memory-bases) turns a flow's chat messages into vectors, so an agent can retrieve past conversations by meaning instead of by recency. Unlike a knowledge base, which you fill with files, it fills itself from the flow's message table.

How it works:

1. Create one under **Memories** in the sidebar: pick a name, an embedding model and a vector database. The database can't be changed later.
2. Each flow run's messages count toward an **ingestion threshold**. When enough unprocessed runs pile up, a background job embeds them. **Auto-capture** is on by default.
3. Optionally turn on **LLM preprocessing**: a model distills each batch into a summary before embedding. If its reply contains the kill phrase (default `NO_INGEST`), the batch is skipped.
4. Add the **Memory Base** component to a flow in Tool Mode and connect its Toolset to an Agent's Tools input.

**Filter by Session** is on by default, so the agent searches only the current session's memories. Turn it off to search across all ingested sessions, which is what you want for "remember this user next week," provided your session IDs map to users. Local Chroma is the default store; Chroma Cloud, OpenSearch and Postgres pgvector are also supported. A memory base attaches to one flow.

This is retrieval over past messages or summaries. It doesn't resolve contradictions or track when a fact stopped being true. For a deeper look at those problems, see the [AI agent memory guide](/articles/ai-agent-memory-explained/). If your low-code stack is n8n rather than Langflow, the [n8n agent memory guide](/articles/best-memory-for-ai-agent-n8n/) covers the same choices there.
