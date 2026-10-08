---
title: "OpenAI Agents SDK Memory: Sessions and Sandbox Memory"
description: "How memory works in the OpenAI Agents SDK: Sessions for chat history (SQLite, Redis, SQLAlchemy, Conversations API), compaction, and sandbox agent memory files."
date: 2026-04-08
lastmod: 2026-10-08
slug: openai-agents-sdk-memory
cluster: agent-memory
aliases:
  - /articles/ai-powered-with-memory-agent-features/
  - /articles/debuts-ai-powered-memory-agent-features/
  - /articles/openai-ai-powered-browser-memory-agent-features/
  - /articles/openai-ai-powered-memory-agent-features/
tags:
  - OpenAI Agents SDK
  - OpenAI
  - agent memory
  - sessions
keywords:
  - "openai agents sdk memory"
  - "openai agents sdk session"
  - "openai agents sdk long-term memory"
  - "sqlitesession"
  - "openai agent memory"
faq:
  - question: "Does the OpenAI Agents SDK have memory?"
    answer: "Yes, in two forms. Sessions store conversation history and replay it on each Runner.run call, with backends such as SQLiteSession, RedisSession, SQLAlchemySession and OpenAIConversationsSession. Sandbox agents can also use a Memory capability that distills lessons from past runs into files like memories/MEMORY.md."
  - question: "How do I persist conversation history in the OpenAI Agents SDK?"
    answer: "Create a session, for example SQLiteSession('user-42', 'conversations.db'), and pass it as session= to Runner.run on every turn. The runner loads earlier items before the run and saves new ones after it. Without a file path, SQLiteSession is in-memory only."
  - question: "Does the OpenAI Agents SDK have long-term memory across conversations?"
    answer: "Not for general chat agents. Sessions are per session ID and hold raw history. Cross-run learning exists only for sandbox agents through the Memory capability. For user facts across sessions, add your own store or a memory service as a tool."
---

**OpenAI Agents SDK memory** comes in two parts. **Sessions** store a conversation's history and replay it on every `Runner.run`, so the agent remembers earlier turns. **Sandbox agent memory** distills lessons from past runs into Markdown files the agent reads next time. There's no built-in store of user facts across sessions.

This page covers both against the Python SDK (`openai-agents` 0.23, October 2026), using the official [Sessions docs](https://openai.github.io/openai-agents-python/sessions/). It also clears up a common mix-up with ChatGPT's own memory features.

## What is memory in the OpenAI Agents SDK?

**Memory in the OpenAI Agents SDK is the conversation state the runner carries between turns. A Session object loads prior items before each run and saves new items after it, in SQLite, Redis, a SQL database or OpenAI's Conversations API. Sandbox agents can add a Memory capability that writes reusable lessons to files.**

An agent run is stateless by default. If you call `Runner.run` twice without passing history, the second call knows nothing about the first. The SDK's [running agents docs](https://openai.github.io/openai-agents-python/running_agents/) list four ways to carry state forward:

| Strategy | Where history lives | Best for |
|---|---|---|
| `result.to_input_list()` | Your app | Small loops, full control, any model provider |
| `session=` | Your storage, managed by the SDK | Persistent chat, resumable runs, custom stores |
| `conversation_id` | OpenAI Conversations API | Server-side conversation shared across services |
| `previous_response_id` | OpenAI Responses API | Light server-side chaining, no conversation object |

The last two work only with the OpenAI Responses API. The docs advise picking one strategy per conversation; a session can't be combined with `conversation_id` or `previous_response_id` in the same run.

## Sessions: conversation history

A **session** is a store keyed by a session ID. Pass it on every turn:

```python
import asyncio

from agents import Agent, Runner, SQLiteSession


async def main():
    agent = Agent(name="Assistant", instructions="Reply concisely.")
    session = SQLiteSession("user-42", "conversations.db")  # omit the path for in-memory

    await Runner.run(agent, "My name is Dana and I'm vegetarian.", session=session)
    result = await Runner.run(agent, "Suggest a dinner for me.", session=session)
    print(result.final_output)

    # Session API
    print(await session.get_items(limit=4))  # most recent items
    await session.pop_item()                 # undo the last item
    # await session.clear_session()          # wipe the conversation


asyncio.run(main())
```

Before each run, the runner prepends the stored items to the new input. After the run, it saves only the new items.

### Session backends

| Session | Import | Storage |
|---|---|---|
| `SQLiteSession` | `from agents import SQLiteSession` | SQLite file or in-memory |
| `AsyncSQLiteSession` | `agents.extensions.memory` | SQLite, async driver |
| `SQLAlchemySession` | `agents.extensions.memory` | Any SQLAlchemy database, such as Postgres or MySQL |
| `RedisSession` | `agents.extensions.memory` | Redis |
| `MongoDBSession` | `agents.extensions.memory` | MongoDB |
| `DaprSession` | `agents.extensions.memory` | Dapr state stores |
| `AdvancedSQLiteSession` | `agents.extensions.memory` | SQLite with branching and usage tracking |
| `EncryptedSession` | `agents.extensions.memory` | Wrapper that encrypts another session |
| `OpenAIConversationsSession` | `from agents import OpenAIConversationsSession` | OpenAI Conversations API |
| `OpenAIResponsesCompactionSession` | `agents.memory` | Wrapper that compacts another session |

You can also write your own by implementing the session protocol: `get_items`, `add_items`, `pop_item` and `clear_session`.

## Keeping session history small

Sessions grow forever by default. Long histories cost tokens and eventually overflow the [context window](/articles/context-window-of-an-llm/). The SDK gives you three controls:

1. **`SessionSettings(limit=N)`** in `RunConfig(session_settings=...)` loads only the last N items.
2. **`session_input_callback`** in `RunConfig` lets you rewrite the history list before it goes to the model, for example `lambda history, new: history[-10:] + new`. Only new items get saved, so pruning doesn't re-save old ones.
3. **`OpenAIResponsesCompactionSession`** wraps another session and calls the Responses API `compact` endpoint when history grows. By default it triggers once 10 or more candidate items exist. It works with OpenAI Responses models only.

Cutting history by item count can split a tool call from its result. The compaction wrapper handles that boundary for you; a hand-written callback has to. For the general tradeoffs, see [LLM memory compression](/articles/llm-memory-compression/).

## Sandbox agent memory: lessons across runs

The newer **sandbox agents** (`SandboxAgent`, which work inside a filesystem and shell) have a separate feature: the **Memory capability**. The [sandbox memory docs](https://openai.github.io/openai-agents-python/sandbox/memory/) say it is distinct from Sessions. It doesn't replay chat; it distills lessons from earlier runs.

How it works:

- After each run, the conversation is appended to `sessions/<rollout-id>.jsonl` in the workspace.
- When the session closes, a model summarizes each conversation into raw notes (phase 1), then a consolidation agent writes `memories/MEMORY.md` and a short `memories/memory_summary.md` (phase 2).
- At the next run, the summary is injected into the prompt. The agent searches `MEMORY.md` and opens per-run summaries only when it needs detail.
- With `live_update` on (the default), the agent can fix stale entries mid-run.

```python
from agents.sandbox import SandboxAgent
from agents.sandbox.capabilities import Filesystem, Memory, Shell

agent = SandboxAgent(
    name="Repo reviewer",
    instructions="Inspect the workspace and keep useful lessons for follow-up runs.",
    capabilities=[Memory(), Filesystem(), Shell()],  # Memory reads need Shell; live updates need Filesystem
)
```

The limits are worth knowing. Memory only survives if the sandbox state survives, through a live session, persisted state or a snapshot. A fresh sandbox starts empty. Raw memories are capped (256 by default) and the oldest drop first. Phase 1 drops system, developer and reasoning content and truncates long conversations. This is closer to [procedural memory](/articles/ai-agent-procedural-memory/), "how to do the job here," than to remembering a user.

## Long-term user memory with the Agents SDK

For a chat agent that should remember a user next week in a new session, the SDK has nothing built in. Sessions are per session ID and store raw items, not facts. The usual patterns:

- **Reuse a stable session ID per user.** Simple, but history grows without bound and old details get trimmed away.
- **Add a memory tool.** Give the agent `function_tool`s that write facts to your database and search them. You own extraction and retrieval.
- **Use a memory service.** Mem0 documents an Agents SDK integration, and [Hindsight](https://github.com/vectorize-io/hindsight) ships `hindsight-openai-agents`, which adds retain, recall and reflect as `FunctionTool`s. These handle fact extraction and search for you.

Our guide on [how to give AI agents memory](/articles/how-to-give-ai-agents-memory/) compares those patterns in detail.

## Not the same as ChatGPT memory

Several searches mix the Agents SDK up with OpenAI's consumer features. ChatGPT has its own saved memories and chat-history reference, covered in [how to find ChatGPT memory](/articles/how-to-find-chatgpt-memory/). [ChatGPT Atlas](https://openai.com/index/introducing-chatgpt-atlas/), OpenAI's browser launched in October 2025, adds optional "browser memories" that carry context from pages you visit into later chats. You can view, archive or delete them in settings. None of those features are available to agents you build with the SDK. In the SDK, memory is whatever your sessions and tools store.
