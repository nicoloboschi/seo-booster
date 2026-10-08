---
title: "AI Memory MCP Servers: Official Server and Alternatives"
description: "What an AI memory MCP server is, how the official MCP memory server's knowledge graph works, and how Graphiti, Basic Memory, Mem0, MemPalace and Hindsight compare."
date: 2026-03-28
lastmod: 2026-10-08
slug: ai-memory-mcp-server
aliases:
- /articles/llm-memory-mcp/
- /articles/llm-memory-mcp-server/
tags:
- MCP
- Model Context Protocol
- agent memory
- tools
keywords:
- "ai memory mcp server"
- "llm memory mcp"
- "mcp memory server"
- "modelcontextprotocol server-memory"
- "best memory mcp server"
cluster: agent-memory
faq:
- question: "What is an MCP memory server?"
  answer: "It's a Model Context Protocol server that exposes memory operations, such as storing facts and searching them, as tools any MCP client can call. Claude Desktop, Claude Code, Cursor and other clients can then share one persistent memory without custom integration code."
- question: "How does the official MCP memory server store data?"
  answer: "The reference server @modelcontextprotocol/server-memory keeps a small knowledge graph of entities, relations and observations in a local memory.jsonl file. You can move the file with the MEMORY_FILE_PATH environment variable. It has nine tools, such as create_entities, add_observations and search_nodes, and no embeddings."
- question: "Which MCP memory server should I use?"
  answer: "For a quick personal setup, the official server or Basic Memory (Markdown files) are simplest. For semantic search over past chats, MemPalace runs locally. For temporal facts, Graphiti's MCP server. For extracted, multi-user memory, hosted or self-hosted servers like Mem0 or Hindsight."
---

An **AI memory MCP server** is a [Model Context Protocol](https://modelcontextprotocol.io/) server that gives any MCP client tools to save and recall memories. Instead of each app building its own memory, Claude Desktop, Claude Code, Cursor or a custom agent connect to the same server and call tools like `add_observations` or `search_nodes`. The official reference server stores a small knowledge graph in a JSONL file.

This page explains how memory over MCP works, walks through the official server, compares the main alternatives, and covers security. Facts come from each project's README, checked October 2026.

## What is an MCP memory server?

**An MCP memory server is a process that speaks the Model Context Protocol and exposes memory as tools: write a fact, search memories, delete an entry. The model decides when to call them. Because MCP is a shared standard, one memory server can serve every MCP-capable assistant on a machine or team.**

MCP tools are "model-controlled," per the [spec](https://modelcontextprotocol.io/specification/2025-11-25/server/tools): the model discovers and calls them based on the conversation. That's the key behavior difference from memory that an app injects automatically. With MCP, memory works only if the model chooses to save and search, which is why most memory servers ship a suggested system prompt. The two patterns are compared in [how AI memory works](/articles/how-ai-memory-works/).

## The official MCP memory server

The reference implementation is [`@modelcontextprotocol/server-memory`](https://github.com/modelcontextprotocol/servers/tree/main/src/memory) in the `modelcontextprotocol/servers` repo. It models memory as a **knowledge graph**:

- **Entities**: nodes with a unique name, a type (like `person`) and a list of observations.
- **Relations**: directed links between entities, written in active voice (`works_at`).
- **Observations**: single facts attached to an entity, added or removed one at a time.

It exposes nine tools:

| Tool | What it does |
|---|---|
| `create_entities` | Add entities with types and observations |
| `create_relations` | Link entities |
| `add_observations` | Add facts to existing entities |
| `delete_entities` / `delete_observations` / `delete_relations` | Remove data |
| `read_graph` | Return the whole graph |
| `search_nodes` | Search names, types and observation text |
| `open_nodes` | Fetch specific entities by name |

Data lives in `memory.jsonl`, by default in the server's directory; set `MEMORY_FILE_PATH` to put it somewhere durable. There are no embeddings, so search matches text, not meaning. It's a reference server: easy to read and run, but meant as a starting point. It works well for a few hundred facts about one user. It isn't built for large histories or multiple tenants.

Claude Desktop config:

```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "env": { "MEMORY_FILE_PATH": "/Users/me/.mcp/memory.jsonl" }
    }
  }
}
```

The README also suggests a system prompt that tells the model to start each chat by retrieving memory and to watch for identity, behaviors, preferences, goals and relationships worth saving.

## Calling a memory server from Python

You can use the same server from your own agent with the official MCP Python SDK (`pip install mcp`). This starts the reference server over stdio, writes an entity, and searches it:

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server = StdioServerParameters(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-memory"],
    env={"MEMORY_FILE_PATH": "/tmp/agent-memory.jsonl"},
)

async def main():
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await session.call_tool("create_entities", {
                "entities": [{
                    "name": "Alice",
                    "entityType": "person",
                    "observations": ["Prefers Python", "Works on the billing service"],
                }]
            })
            result = await session.call_tool("search_nodes", {"query": "billing"})
            print(result.content[0].text)

asyncio.run(main())
```

Swap the command and arguments to talk to any other memory server; the session code stays the same.

## Other memory MCP servers compared

| Server | Storage | Search | Tools | License | Good for |
|---|---|---|---|---|---|
| **Official server-memory** | Local JSONL graph | Text match | 9 | MIT moving to Apache 2.0 | Small personal memory, learning MCP |
| **[Graphiti MCP](https://github.com/getzep/graphiti/tree/main/mcp_server)** | FalkorDB (default) or Neo4j 5.26+ | Hybrid graph search over temporal facts | 13 | Apache 2.0 | Facts that change over time |
| **Basic Memory** | Markdown files + SQLite index | Full-text and graph context | 21 | AGPL-3.0 | Notes you also read in Obsidian |
| **MemPalace** | Local ChromaDB + SQLite graph | Semantic search over verbatim text | 45 | MIT | Searching past chats locally |
| **Mem0** | Mem0 Platform | Semantic, filtered | 9 | Hosted service | Managed user memory |
| **Hindsight** | PostgreSQL + pgvector | Semantic, BM25, graph and temporal in parallel | Per-bank endpoint | MIT | Extracted, multi-user memory you can self-host |

Notes on each:

- **Graphiti MCP** (from Zep) exposes `add_memory`, `search_nodes`, `search_memory_facts` and others over HTTP at `http://localhost:8000/mcp/` by default, or stdio for Claude Desktop. It needs an LLM key (OpenAI by default) because ingestion extracts entities and facts, and it warns that very small local models may fail at structured output.
- **[Basic Memory](https://github.com/basicmachines-co/basic-memory)** writes plain Markdown with wikilinks and frontmatter, so the same folder opens as an Obsidian vault. Tools include `write_note`, `read_note`, `search_notes` and `build_context`. See [LLM memory with Obsidian](/articles/llm-memory-obsidian/).
- **MemPalace** stores conversations verbatim and searches them semantically, with no LLM needed. See [MemPalace](/articles/mempalace-ai-memory-system/).
- **Mem0**'s original `mem0ai/mem0-mcp` repo was archived in March 2026; its README now points to a hosted server at `https://mcp.mem0.ai/mcp`, which needs a Mem0 API key.
- **Hindsight** mounts an MCP endpoint per memory bank at `/mcp/{bank_id}/` on its API server. The endpoint is open by default, and you enable API-key auth with a tenant extension.

Choosing comes down to what memory should be. If it's notes you want to read and edit, use a file-based server. If it's searchable history, use a vector store. If it's facts that change, use a temporal graph. If many users or agents share it, use a server with tenancy and auth. The broader trade-offs are in the [LLM memory comparison](/articles/llm-memory-comparison/).

## Security for memory MCP servers

A memory server is a write path into every future prompt, so it deserves more care than a read-only tool. The MCP spec says servers **must** validate inputs, implement access controls, rate-limit calls and sanitize outputs, and that clients should keep a human in the loop who can deny tool calls.

In practice:

1. **Turn on auth for any network-reachable server.** Several servers, including Hindsight's, are open by default on localhost.
2. **Separate memory per user or project**, with banks, files or namespaces, so one person's data can't reach another's prompt.
3. **Treat recalled memories as untrusted input.** Text saved from a web page or email can carry instructions.
4. **Review writes** when the agent reads untrusted content, or make memory read-only in those sessions.
5. **Back up the store.** A JSONL file or database you can roll back makes cleanup possible after a bad write.

The attacks this guards against, like MINJA and AgentPoison, are covered in [AI memory injection](/articles/ai-memory-injection/).
