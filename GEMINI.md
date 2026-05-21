# Universal AI Development Workflow Context

## Purpose

This setup is not for one project only. It is a universal AI/vibe-coding development environment for all projects, including:

- SentinelX
- Indian algo trading platform
- Dynamic Bubble website
- AI/physics research projects
- future startup/project work

The goal is to build a professional multi-agent AI engineering workflow on Windows using VS Code, PowerShell, Cline, MCP servers, Gemini CLI, Codex CLI, Ollama, GitHub, Infisical, and git-secrets.

---

## System

- OS: Windows
- Main editor: VS Code
- Terminal: PowerShell / VS Code integrated terminal
- GitHub username: tanmay-alpha
- Git name: Tanmay Mangal
- Git email: mangaltanmay7@gmail.com
- Main test repo: C:\Users\TANMAY\SentinelX
- Laptop: HP Omen 14
- GPU: RTX 4060 8GB
- CPU: Intel i7-14650HX
- RAM: 16GB
- SSD: 1TB

Important constraint:
The laptop heats and slows when too many agents/models run at the same time. Use only one heavy agent at a time.

---

## Completed Setup

### Phase 1 — Git + VS Code Base

Git global identity configured:

- user.name = Tanmay Mangal
- user.email = mangaltanmay7@gmail.com
- GitHub username = tanmay-alpha

VS Code configured for AI-assisted coding.

---

### Phase 2 — Playwright + n8n

Installed:

- Playwright
- Chromium
- n8n
- pm2

Purpose:

- Playwright: browser automation/testing
- n8n: local automation workflows
- pm2: local process manager

n8n works at:

http://localhost:5678

Do not keep n8n running all the time if RAM/heat is an issue.

---

### Phase 3 — AI Coding Stack

Installed:

- Ollama
- qwen2.5-coder:7b
- deepseek-r1:7b
- Cline VS Code extension
- Continue.dev
- Gemini Code Assist
- GitHub Copilot

Ollama models:

- qwen2.5-coder:7b
- deepseek-r1:7b

Cline connected to Ollama using:

- Provider: Ollama
- Base URL: http://localhost:11434
- Model: qwen2.5-coder:7b
- API key: empty

Continue.dev configured with local Ollama models.

---

### Phase 4 — Security

Installed and configured:

- git-secrets
- Infisical CLI

git-secrets global secret patterns added for:

- GitHub tokens
- OpenAI keys
- Firecrawl keys
- Google API keys
- AWS keys

Fake secret scan was tested successfully.

Universal env template created:

C:\Users\TANMAY\ai-workspace\templates\.env.example

SentinelX has:

- .env ignored
- .env.example committed
- git-secrets hooks installed

Infisical:

- CLI installed
- login successful
- SentinelX linked with .infisical.json
- TEST_SECRET=hello_from_infisical stored and retrieved successfully

Important:
Never paste real API keys in chat/screenshots. Regenerate exposed keys.

---

### Phase 5 — Cline MCP Server Stack

Cline MCP config path:

C:\Users\TANMAY\AppData\Roaming\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json

MCP servers configured and showing green:

- filesystem
- github
- memory
- sequential-thinking
- context7
- firecrawl
- fetch
- git-mcp-server

Brave Search MCP skipped because Brave API appeared paid/subscription-based.

Fetch replacement:

- @tokenizin/mcp-npx-fetch

Git MCP replacement:

- @cyanheads/git-mcp-server

GitHub MCP uses:

GITHUB_PERSONAL_ACCESS_TOKEN

not GITHUB_TOKEN.

Firecrawl MCP configured with Firecrawl API key.

Important:
Firecrawl key was exposed in screenshot once, so regenerate it later.

---

### Phase 6 — Gemini CLI

Installed Gemini CLI:

@google/gemini-cli

Gemini CLI authenticated with Google account.

Gemini shows:

- Signed in with Google
- Plan: Gemini Code Assist in Google One AI Pro

Gemini CLI should be used inside VS Code integrated terminal.

Useful Gemini commands:

/ide enable
/ide status

Gemini role:

- huge repo analysis
- long logs
- architecture review
- second opinion
- large-context reasoning

---

### Codex CLI

Codex CLI installed and working.

It showed:

- OpenAI Codex v0.132.0
- model: gpt-5.5 xhigh
- directory: ~\SentinelX

There is also Codex panel inside VS Code.

Important difference:

- Codex VS Code panel = IDE-integrated quick coding tasks
- Codex CLI = terminal-native autonomous coding agent

Codex should use ChatGPT Plus account if possible:

codex logout
codex login

Choose:

Sign in with ChatGPT

not API key.

Codex role:

- autonomous implementation
- repo edits
- code changes
- bug fixing
- terminal coding workflows

---

## Current Workflow Strategy

Use agents by role:

| Tool | Role |
|---|---|
| ChatGPT | planning, debugging, prompt writing, strategy |
| Gemini CLI | huge-context repo analysis and architecture |
| Codex CLI | autonomous terminal coding implementation |
| Codex VS Code panel | quick IDE coding tasks |
| Cline + MCP | tool orchestration, docs, scraping, git, filesystem |
| Ollama | local/free fallback |
| Continue.dev | local autocomplete |
| GitHub Copilot | autocomplete/cloud backup |
| Context7 | latest docs |
| Firecrawl | scraping/research |
| git-secrets | secret leak prevention |
| Infisical | secret vault |

---

## Fallback Plan When Limits Finish

Use this order:

1. Gemini CLI for huge analysis
2. Codex VS Code panel for quick code tasks
3. Codex CLI for terminal implementation
4. Cline + MCP for tool-based work
5. Ollama local models for free fallback
6. ChatGPT for planning/prompts/debugging

---

## RAM / Heat Rule

Do not run all agents at once.

Recommended lightweight mode:

- VS Code open
- one agent active only:
  - Gemini CLI OR Codex CLI OR Cline
- Ollama off unless needed
- n8n off unless needed
- Chrome tabs minimized

Useful commands:

pm2 status
pm2 stop n8n-local

ollama ps
ollama stop qwen2.5-coder:7b
ollama stop deepseek-r1:7b

---

## Daily Workflow

1. Open project in VS Code.
2. Use Gemini CLI for large analysis.
3. Use Codex CLI or Codex panel for implementation.
4. Use Cline + MCP when needing:
   - filesystem
   - GitHub
   - docs
   - Firecrawl
   - git operations
   - sequential planning
5. Run tests.
6. Review git diff.
7. Commit safely.
8. Push.

---

## Important Instruction For Any AI Agent

Do not assume this setup is only for SentinelX. It is universal.

Do not install more tools unless clearly useful.

Prioritize:
- stability
- low RAM usage
- safe secrets
- project architecture
- clean git workflow
- step-by-step execution

Always ask before making large destructive changes.

Never expose or commit secrets.

