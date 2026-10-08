---
title: "n8n AI Agent Memory: Which Memory Node to Use"
description: "The memory options for the n8n AI Agent node: Simple Memory, session IDs, Postgres, Redis and MongoDB chat memory, deprecated Zep, external memory, clearing."
date: 2026-03-30
lastmod: 2026-10-08
slug: best-memory-for-ai-agent-n8n
aliases:
- /articles/ai-agent-simple-memory-n8n/
- /articles/llm-memory-n8n/
- /articles/memory-in-ai-agent-n8n/
- /articles/n8n-ai-agent-clear-memory/
- /articles/n8n-ai-agent-node-memory/
- /articles/n8n-ai-agent-simple-memory-session-id/
- /articles/n8n-ai-agent-window-buffer-memory/
- /articles/n8n-ai-long-term-memory/
- /articles/n8n-chatbot-memory/
- /articles/n8n-llm-memory/
tags:
- n8n
- AI Agent Memory
- Chat Memory
- Workflow Automation
- Long-Term Memory
keywords:
- n8n ai agent memory
- best memory for ai agent n8n
- n8n simple memory
- n8n window buffer memory
- n8n simple memory session id
- n8n postgres chat memory
- n8n redis chat memory
- n8n clear memory
- n8n long term memory
faq:
- question: "What is the best memory for an n8n AI Agent?"
  answer: "For testing, Simple Memory. For anything in production, Postgres Chat Memory or Redis Chat Memory, because they survive restarts and work in queue mode. If the agent must remember facts across separate conversations, add an external memory system on top, through a community node, an HTTP request or the MCP Client Tool."
- question: "How do I set the session ID for Simple Memory in n8n?"
  answer: "Set the Session ID option to Connected Chat Trigger Node to read the sessionId field from the Chat Trigger, or to Define below to supply your own key with an expression, such as a user ID or Telegram chat ID. If n8n can't find a session ID it throws a 'No session ID found' error."
- question: "How do I clear an n8n AI Agent's memory?"
  answer: "Use the Chat Memory Manager node with the Delete Messages operation and Delete Mode set to All Messages (or Last N), attached to the same memory node and session. You can also delete the rows or key in the backing database, set a Redis session TTL, or start a new session ID."
---

**The best memory for an n8n AI Agent** depends on where the workflow runs. Simple Memory (once called Window Buffer Memory) is fine for testing. For production, use Postgres Chat Memory or Redis Chat Memory, which survive restarts and queue mode. None of these remember facts across conversations, so long-term memory needs an external system.

This page covers each n8n memory node, how session IDs work, how to clear memory, and how to add long-term memory. Node names and options come from the [n8n docs](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.memorybufferwindow/) and the [n8n source code](https://github.com/n8n-io/n8n/tree/master/packages/@n8n/nodes-langchain/nodes/memory).

## What is n8n AI Agent memory?

**n8n AI Agent memory is a sub-node that stores the chat history of a conversation and passes recent turns back to the AI Agent node on each run.** Without it, every message reaches the model with no context. The memory node decides where the history lives (n8n's process, Postgres, Redis, MongoDB) and how many past turns the model sees.

Only agents can use it. The n8n docs state plainly that "AI agent nodes can use memory, but AI chains can't." So if you need conversation history, build the flow around the AI Agent node, not the Basic LLM Chain.

Every chat memory node is a form of [short-term memory for AI agents](/articles/short-term-memory-ai-agents/): it replays recent messages. It doesn't extract facts, merge them, or search old conversations by meaning.

## The n8n memory nodes compared

These are the memory sub-nodes listed in the n8n integrations docs, with their main settings.

| Node | Where history lives | Key settings | Status | Use it for |
|---|---|---|---|---|
| **Simple Memory** | n8n process memory, no credentials | Session ID, Context Window Length | Active | Tests and single-instance demos |
| **Postgres Chat Memory** | Postgres table (default `n8n_chat_histories`) | Session ID, Table Name, Context Window Length | Active | Most production chatbots |
| **Redis Chat Memory** | Redis list per session | Session ID, Session Time To Live, Context Window Length | Active | Fast history with auto-expiry |
| **MongoDB Chat Memory** | MongoDB collection | Session ID, Collection Name, Database Name, Context Window Length | Active | Teams already on MongoDB |
| **Xata** | Xata | Session ID, Context Window Length | Listed in docs | Existing Xata users |
| **Zep** | Zep server | Session ID | Deprecated from n8n 1.108.0 | Don't start new workflows on it |
| **Motorhead** | Motorhead server | Session ID | Deprecated from n8n 2.8.0; project no longer maintained | Migrate away |

The deprecation notes come from n8n's [deprecated nodes list](https://docs.n8n.io/integrations/builtin/deprecated-nodes/), which says deprecated nodes get no more updates or fixes. Existing workflows keep running.

### Simple Memory (Window Buffer Memory)

**Simple Memory** keeps chat history inside the running n8n process. The node description in the source reads "Stores in n8n memory, so no credentials required." Older templates call it Window Buffer Memory; n8n's AI Agent troubleshooting page says to delete and re-add the node if an old version throws errors.

Three limits matter:

1. **It breaks in queue mode.** The docs warn not to use it if n8n runs in queue mode, because "n8n can't guarantee that every call to Simple Memory will go to the same worker."
2. **It's not durable.** History sits in an in-memory map. A restart wipes it.
3. **Idle sessions expire.** In the current source, buffers not accessed for one hour are cleared on the next memory call.

The source also prefixes each session key with the workflow ID. Two different workflows using the same session ID won't share Simple Memory history.

### Postgres, Redis and MongoDB chat memory

These three nodes store history in a database you run, so it survives restarts and works across queue-mode workers.

**Postgres Chat Memory** creates its table if it doesn't exist. The underlying LangChain store writes one row per message with `id`, `session_id` and `message` columns. **Redis Chat Memory** stores each session as a Redis list and adds a **Session Time To Live** in seconds, so idle chats expire on their own. The default is 0, meaning no expiry. **MongoDB Chat Memory** lets you pick the database and collection.

### What Context Window Length does

**Context Window Length** is the number of past interactions the model receives. The default is 5. Under the hood it's LangChain's `BufferWindowMemory`, which returns the last `k * 2` messages, so 5 means the last five user and AI exchanges (10 messages).

The database nodes still store the full history. The window only limits what goes into the prompt. A long window raises token cost on every call.

## How session IDs work in n8n memory

**The session ID decides which conversation a message belongs to.** Get it wrong and users see each other's history, or every message starts fresh. Current versions of the memory nodes offer a **Session ID** option with two choices:

| Option | What it does | When to use it |
|---|---|---|
| **Connected Chat Trigger Node** (default) | Reads a field called `sessionId` from the input, as output by the Chat Trigger | Workflows started by n8n's chat trigger or embedded chat |
| **Define below** | Uses a key you set, static text or an expression | Telegram, Slack, WhatsApp, webhooks, any trigger without a `sessionId` |

With Define below, use a stable per-user value, for example `{{ $json.message.chat.id }}` from a Telegram trigger. If n8n can't find a session ID, it throws "No session ID found", and the error tells you to change the Session ID parameter. The docs suggest a static key such as `my_test_session` only for testing.

Sharing history between nodes takes care. The docs warn that several memory nodes of the same type use the same memory instance by default. In recent node versions, n8n's editor shows a different hint: with Connected Chat Trigger Node, the session is scoped to that one memory node, and to share it you switch to Define below and use the same key in each node. If two agents must read the same history, set the key explicitly in both.

## How to clear n8n AI Agent memory

n8n has a node for this: **Chat Memory Manager**. Attach it to the same memory sub-node (and session) the agent uses.

1. Add a **Chat Memory Manager** node where the reset should happen, for example after a "/reset" command.
2. Connect the same memory sub-node type the agent uses, with the same session key.
3. Set **Operation Mode** to **Delete Messages**.
4. Set **Delete Mode** to **All Messages** to wipe the session, or **Last N** with a Messages Count to drop recent turns.
5. To replace history instead, use **Insert Messages** with **Override All Messages**.
6. Use **Get Many Messages** with Simplify Output to check what's stored.

Outside n8n, you can clear the store directly. For Postgres, delete the session's rows. For Redis, delete the key, which is the session ID itself. This Python script does both:

```python
import psycopg
import redis

SESSION_ID = "user-42"

# Postgres Chat Memory (default table name)
with psycopg.connect("postgresql://n8n:secret@localhost:5432/n8n") as conn:
    conn.execute(
        "DELETE FROM n8n_chat_histories WHERE session_id = %s", (SESSION_ID,)
    )

# Redis Chat Memory: each session is a list stored under the session ID
redis.Redis(host="localhost", port=6379).delete(SESSION_ID)
```

For Simple Memory, there's no table to clear. Use Chat Memory Manager, switch to a new session ID, or wait for the one-hour idle cleanup. A restart also clears it.

## Long-term memory for n8n agents

Chat memory nodes replay recent messages. They don't remember that a user said "I'm vegetarian" three weeks and two sessions ago, unless that message still sits in the window. For that, you need [persistent memory across sessions](/articles/persistent-memory-ai/): a system that extracts facts, stores them, and retrieves the relevant ones by meaning.

There are four practical routes in n8n:

| Route | How it connects | Notes |
|---|---|---|
| **Vector store as a tool** | n8n's vector store nodes (PGVector, Qdrant, Pinecone and others) | You design what to store and when |
| **Community memory node** | Installed from Settings, Community Nodes | Runs before or after the agent as normal steps |
| **MCP Client Tool** | Agent calls tools on a memory server over MCP | Supports HTTP Streamable; SSE is marked deprecated |
| **HTTP Request node** | Calls a memory API directly | Works with any service that has a REST API |

### Memory servers you can reach from n8n

**Hindsight** is an open-source (MIT) agent memory system. It ships an n8n community node, `@vectorize-io/n8n-nodes-hindsight`, with three operations: **Retain** (store content in a memory bank), **Recall** (search a bank) and **Reflect** (an LLM-written answer over the bank). It's a regular workflow node, so the usual pattern is Recall before the agent and Retain after. Every Hindsight server also exposes an MCP endpoint per bank at `/mcp/{bank_id}/`, which the MCP Client Tool can call. The [Hindsight README](https://github.com/vectorize-io/hindsight) itself notes that it "may be overkill" for simple n8n workflows.

**Zep** dropped out of the built-in node list: the Zep memory and vector store nodes are deprecated. Zep Cloud still has a REST API you can call from the HTTP Request node. See [what Zep memory is](/articles/what-is-zep-memory/) for its current product.

Other memory servers with MCP endpoints include Supermemory (hosted at `https://mcp.supermemory.ai/mcp`) and Graphiti, whose repo includes an MCP server. For more options, see the list of [AI memory MCP servers](/articles/ai-memory-mcp-server/).

## Which n8n memory should you pick?

- **Building or testing a workflow:** Simple Memory. No setup.
- **Production chatbot on one instance or queue mode:** Postgres Chat Memory. Durable, easy to inspect and clear with SQL.
- **High-traffic chat where old sessions should expire:** Redis Chat Memory with a Session Time To Live.
- **Already on MongoDB:** MongoDB Chat Memory.
- **Agent must remember facts across sessions:** keep a chat memory node for recent turns, and add an external memory system for long-term facts.
- **Workflows on Zep or Motorhead nodes:** plan a migration; both are deprecated.

For the wider picture of memory types and tools beyond n8n, see [AI agent memory explained](/articles/ai-agent-memory-explained/).
