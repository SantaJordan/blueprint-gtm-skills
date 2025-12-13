# Agent SDK Worker (Node.js)

Cloud Blueprint Turbo execution using Claude Agent SDK.
Runs on Modal.com, triggered by Supabase webhook.

**Status:** Active - Primary worker for new deployments

---

Blueprint Turbo worker using the Claude Agent SDK.

## Overview

This worker processes Blueprint Turbo jobs using the Claude Code engine via the Claude Agent SDK. It provides 90-95% quality parity with local Claude Code execution by:

- Loading `.claude/skills/` as the single source of truth
- Executing the Blueprint Turbo orchestrator from `.claude/commands/blueprint-turbo.md` (embedded into the prompt with `$ARGUMENTS` substituted)
- Using MCP servers (Sequential Thinking + Browser MCP) inside the Modal container
- Publishing HTML to Vercel Playbooks (`https://playbooks.blueprintgtm.com/{slug}`)
- Adding timeboxing + observability logs to reduce cloud timeouts and diagnose slowdown
- Optionally pre-fetching website + search context via Apify to reduce tool-loop variance

## Quick Start

### Local Development

```bash
# Install dependencies
npm install

# Set environment variables
export ANTHROPIC_API_KEY="sk-ant-..."
export SUPABASE_URL="https://..."
export SUPABASE_SERVICE_KEY="sb_secret_..."
export VERCEL_TOKEN="..."  # For cloud publishing
export APIFY_API_TOKEN="apify_api_..."  # Optional: pre-fetch

# Test with a URL (bypasses Supabase)
npm run process-job -- --url https://owner.com

# Process a job from Supabase
npm run process-job -- <job-id>

# Poll for pending jobs
npm run process-job -- --poll
```

### Modal Deployment

```bash
# Deploy to Modal
modal deploy modal/wrapper.py

# Test deployment
modal run modal/wrapper.py --url https://owner.com

# View logs
modal app logs blueprint-agent-sdk-worker
```

## Project Structure

```
agent-sdk-worker/
├── src/
│   ├── index.ts      # Entry point (webhook + CLI)
│   ├── worker.ts     # Core worker logic + Vercel publishing
│   ├── supabase.ts   # Database operations
│   ├── config.ts     # Environment config
│   └── cli.ts        # CLI entry point
├── modal/
│   └── wrapper.py    # Modal deployment wrapper
├── package.json
└── tsconfig.json
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude API key |
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Yes | Supabase service key |
| `VERCEL_TOKEN` | Yes | Vercel PAT for publishing to `playbooks.blueprintgtm.com` |
| `APIFY_API_TOKEN` | No | Enables Apify pre-fetch (rag-web-browser + google-search-scraper) |
| `VERCEL_API_URL` | If using Stripe | Base URL of the SaaS Vercel app (for `/api/capture-payment`) |
| `MODAL_WEBHOOK_SECRET` | If using Stripe | Shared secret to authorize capture-payment calls |
| `SKILLS_REPO_URL` | No | Skills repo URL |
| `SKILLS_REPO_PATH` | No | Local path for skills repo |

## How It Works

1. **Job received** via Supabase webhook or polling
2. **Skills repo** cloned/updated to get latest `.claude/skills/`
3. **Prompt built** by embedding `.claude/commands/blueprint-turbo.md` content and substituting `$ARGUMENTS` with the company URL (plus timeboxing + optional Apify pre-fetch context)
4. **Agent SDK** runs the prompt with:
   - `systemPrompt: { preset: 'claude_code' }`
   - `settingSources: ['project', 'user']` (Linux skill discovery workaround)
   - `mcpServers` for Sequential Thinking + Browser MCP
5. **Playbook file** located from `PLAYBOOK_PATH` marker or inferred from output
6. **HTML uploaded** to Vercel via REST API → `https://playbooks.blueprintgtm.com/{slug}`
7. **Supabase** updated with status and `playbook_url`
8. **Payment capture** triggered via SaaS API (if job has Stripe intent)

> **Note:** Local CLI uses GitHub Pages for publishing via `.claude/skills/blueprint-github-publish`. This worker uses Vercel for proper HTML serving.

## Documentation

- [Runbook](../docs/AGENT_SDK_RUNBOOK.md) - Operations guide
- [Migration Notes](../docs/AGENT_SDK_MIGRATION_NOTES.md) - Architecture decisions

## License

Private - Blueprint GTM
