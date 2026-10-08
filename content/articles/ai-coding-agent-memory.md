---
title: "AI Coding Agent Memory: CLAUDE.md, AGENTS.md and More"
description: "How AI coding agents remember projects: Claude Code CLAUDE.md and auto memory, Codex AGENTS.md and memories, Cursor rules, Copilot Memory, and external memory tools."
date: 2026-04-02
lastmod: 2026-10-08
slug: ai-coding-agent-memory
aliases:
- /articles/persistent-memory-system-for-ai-coding-agents/
tags:
- coding agents
- Claude Code
- Codex
- Cursor
- agent memory
keywords:
- "ai coding agent memory"
- "persistent memory for ai coding agents"
- "claude code memory"
- "agents.md"
- "cursor memories"
- "codex memories"
cluster: agent-memory
faq:
- question: "How do AI coding agents remember a project between sessions?"
  answer: "Mostly through instruction files that load at the start of every session: CLAUDE.md for Claude Code, AGENTS.md for Codex and many others, and .cursor/rules for Cursor. Claude Code, Codex and GitHub Copilot also have automatic memory that saves learnings, each with its own storage, limits and defaults."
- question: "Should I use AGENTS.md or CLAUDE.md?"
  answer: "AGENTS.md is an open format read by Codex, Cursor, Copilot's coding agent, Gemini CLI and over 20 other tools. Claude Code reads AGENTS.md when no CLAUDE.md exists, or you can import it from CLAUDE.md with @AGENTS.md. Keeping one shared AGENTS.md avoids duplicate instructions."
- question: "Does Cursor still have Memories?"
  answer: "Cursor staff said on the official forum that the Memories feature was intentionally removed starting in version 2.1.x, and suggested running Export memories from the Command Palette and moving the content into Rules. Project rules in .cursor/rules and AGENTS.md are the supported way to persist instructions."
---

**AI coding agent memory** is how tools like Claude Code, Codex, Cursor and GitHub Copilot carry project knowledge from one session to the next. The main mechanism is a plain **instruction file** (CLAUDE.md, AGENTS.md or Cursor rules) loaded into every session. Some agents add **automatic memory** that saves lessons as they work. For more, teams add an external memory server.

Every session starts with an empty context window, so anything the agent should know about your build, conventions or past mistakes has to be written down somewhere and loaded back. This page compares how the major coding agents do it, from their official docs, checked October 2026.

## What is AI coding agent memory?

**AI coding agent memory is any information that persists outside the model and gets put back into a coding agent's context in a later session: instruction files you write, notes the agent writes for itself, indexed past sessions, and facts stored in an external memory service. Without it, the agent rediscovers your repo from scratch every time.**

It splits into two kinds, which map to the memory types in [AI agent memory explained](/articles/ai-agent-memory-explained/):

- **Instructions** (procedural memory): rules and commands you want followed every time, like "use pnpm" or "run `make lint` before committing."
- **Learnings** (episodic and semantic memory): things discovered while working, like "the API tests need a local Redis," or a fix that worked last week.

Instructions belong in version control. Learnings are often machine-local and generated.

## How each coding agent handles memory

| Agent | Instruction files | Automatic memory | Default | Limits (per docs) |
|---|---|---|---|---|
| **Claude Code** | `CLAUDE.md`, `CLAUDE.local.md`, `.claude/rules/`, or `AGENTS.md` | Auto memory in `~/.claude/projects/<project>/memory/` | On (local sessions) | First 200 lines or 25 KB of `MEMORY.md` loaded |
| **Codex** | `AGENTS.md`, `AGENTS.override.md`, fallback names | Memories in `~/.codex/memories/` | Off | 32 KiB of combined AGENTS.md |
| **Cursor** | `.cursor/rules/*.mdc`, `AGENTS.md`, user and team rules | Memories removed in 2.1.x | n/a | Rule modes control loading |
| **GitHub Copilot** | `AGENTS.md` and repo instructions | Copilot Memory (repo facts and user preferences) | On for individual plans; admin policy for orgs | Unused entries deleted after 28 days |

### Claude Code: CLAUDE.md and auto memory

Claude Code's [memory docs](https://code.claude.com/docs/en/memory) describe two systems, both loaded at session start.

**CLAUDE.md files** are instructions you write. They stack by scope: a managed policy file for the organization, `~/.claude/CLAUDE.md` for you, `./CLAUDE.md` or `./.claude/CLAUDE.md` for the team, and a gitignored `CLAUDE.local.md` for your private project notes. Files above the working directory load at launch; those in subdirectories load when Claude opens files there. You can import other files with `@path/to/file` (up to four hops deep), and split rules into `.claude/rules/*.md`, optionally scoped with `paths:` globs so they load only for matching files. The docs recommend keeping each CLAUDE.md under 200 lines.

**Auto memory** is notes Claude writes itself, in four types: `user`, `feedback`, `project` and `reference`. They live in `~/.claude/projects/<project>/memory/`, shared across worktrees of the same repo, with a `MEMORY.md` index plus one file per memory. Only the first 200 lines or 25 KB of `MEMORY.md` load at start; topic files are read on demand. Auto memory is machine-local and not shared across machines. Toggle it in `/memory`, or set `autoMemoryEnabled: false` or `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`.

The docs stress one limit: CLAUDE.md is context, "not enforced configuration." To block an action, use a hook or permission rule. For Claude's chat-app memory, which is separate, see [Claude AI long-term memory](/articles/claude-ai-long-term-memory/).

### Codex: AGENTS.md and memories

Codex builds an instruction chain from [AGENTS.md files](https://agents.md/). It reads one global file from `~/.codex` (`AGENTS.override.md` if present, else `AGENTS.md`), then walks from the repo root down to the current directory, taking at most one file per directory. Files concatenate root-first, so closer files win. Combined size stops at `project_doc_max_bytes`, 32 KiB by default. You can add other file names with `project_doc_fallback_filenames` in `~/.codex/config.toml`.

Codex **memories** are separate and off by default. Turn them on in settings or with `memories = true` under `[features]`. Codex then turns eligible past chats into files under `~/.codex/memories/` in the background, after a chat has been idle, skipping short sessions and redacting secrets. `/memories` controls whether the current chat uses or produces memories. OpenAI's docs say to "keep required team guidance in `AGENTS.md`," treating memories as a recall layer, not the source of rules that must always apply.

### Cursor: rules

Cursor's [rules docs](https://cursor.com/docs/context/rules) list four kinds: **project rules** as `.mdc` files in `.cursor/rules` (version-controlled), **user rules** in settings, **team rules** from the dashboard (Team and Enterprise plans, can be enforced), and **AGENTS.md** in the root or subfolders. Project rules load in one of four modes: always, when the agent judges them relevant from the description, when files matching `globs` are in context, or only when @-mentioned.

Cursor used to have an automatic **Memories** feature. On the official forum, a Cursor staff member wrote that "the Memories feature was intentionally removed starting from version 2.1.x," and suggested running **Export memories** from the Command Palette and moving the result into Rules.

### GitHub Copilot: Copilot Memory

[Copilot Memory](https://docs.github.com/en/copilot/concepts/agents/copilot-memory) is in public preview. It stores **repository facts** (conventions, architecture decisions, build commands) and **user preferences**. Repository facts come only from users with write access and **cite the code that supports them**; before using one, Copilot checks those citations against the current branch and drops facts that no longer hold. Entries unused for 28 days are deleted. Memory is shared across Copilot cloud agent, code review, CLI and agentic autofix. It's on by default for individual plans; organizations need an admin to enable the policy.

Citation checking is the most interesting design here. It addresses the main failure of coding memory: notes that were true once and quietly go stale.

## What to put in each layer

A workable split, based on what each vendor's docs recommend:

1. **Build, test and lint commands** go in AGENTS.md or CLAUDE.md. The agent needs them every session.
2. **Hard rules** ("never push to main") go in permissions or hooks, with a reminder in the instruction file.
3. **Path-specific conventions** go in scoped rules (`.claude/rules/` with `paths:`, Cursor globs, nested AGENTS.md).
4. **Long procedures** go in skills or docs the agent reads on demand, not in always-loaded files.
5. **Personal preferences** go in user-level files (`~/.claude/CLAUDE.md`, user rules, `CLAUDE.local.md`).
6. **Lessons and gotchas** can go to auto memory, then get promoted into the shared file once the team agrees.
7. **Long history** (why a decision was made six months ago) belongs in an external memory or searchable session archive.

Keep instruction files short. Everything in them costs tokens on every turn and competes for attention.

## Sharing one file across agents

If a team uses several agents, maintain **one AGENTS.md**. The format is stewarded by the Agentic AI Foundation under the Linux Foundation, and agents.md says it's used by over 60,000 open-source projects and read by Codex, Cursor, Copilot's coding agent, Gemini CLI, Jules, Aider, Zed, Windsurf and others.

Claude Code reads `AGENTS.md` directly when there's no `CLAUDE.md` (v2.1.277+). If you want both, put a one-line `CLAUDE.md` that imports it:

```markdown
@AGENTS.md

## Claude-specific
- Use the Read tool before editing large files.
```

## External memory for coding agents

Built-in memory is per machine and per tool. Teams that want lessons shared across developers, agents and months of history add an external store, usually over MCP:

- **Session archives.** MemPalace mines Claude Code, Codex and Cursor transcripts into a local verbatim index with auto-save hooks; see [MemPalace](/articles/mempalace-ai-memory-system/).
- **Markdown knowledge bases.** Basic Memory keeps notes as Markdown with an SQLite index and exposes them as MCP tools.
- **Extraction-based memory servers.** Mem0, Zep and Hindsight store extracted facts. Hindsight ships a coding-agents package (`@vectorize-io/hindsight-coding-agents`) for per-repo project memory and integrations for Claude Code, Codex, Cursor and others.

Each adds a dependency and, for extraction-based tools, LLM calls per write. Start with instruction files; add a server when the same lesson keeps getting lost across people or machines. The options are compared on [AI memory MCP servers](/articles/ai-memory-mcp-server/).

Memory files are also an attack surface. A malicious instruction written into a memory file, or committed in a shared CLAUDE.md, loads into every future session. Claude Code asks for approval before loading imports from outside the repo for that reason. More on the risk in [AI memory injection](/articles/ai-memory-injection/).
