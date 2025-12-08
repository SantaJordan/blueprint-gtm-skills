# Agent SDK Worker

Blueprint Turbo worker using the Claude Agent SDK.

## Overview

This worker processes Blueprint Turbo jobs by invoking the `/blueprint-turbo` command via the Claude Agent SDK. It provides 90-95% quality parity with local Claude Code execution by:

- Loading `.claude/skills/` as the single source of truth
- Using the Sequential Thinking MCP for synthesis
- Running the exact same command flow as local execution

## Quick Start

### Local Development

```bash
# Install dependencies
npm install

# Set environment variables
export ANTHROPIC_API_KEY="sk-ant-..."
export SUPABASE_URL="https://..."
export SUPABASE_SERVICE_KEY="sb_secret_..."
export GITHUB_TOKEN="ghp_..."

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
│   ├── worker.ts     # Core worker logic
│   ├── supabase.ts   # Database operations
│   ├── config.ts     # Environment config
│   ├── github.ts     # GitHub API fallback
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
| `GITHUB_TOKEN` | Yes | GitHub PAT for publishing |
| `GITHUB_OWNER` | No | GitHub username (default: SantaJordan) |
| `GITHUB_REPO` | No | Repository name (default: blueprint-gtm-playbooks) |
| `SKILLS_REPO_URL` | No | Skills repo URL |
| `SKILLS_REPO_PATH` | No | Local path for skills repo |

## How It Works

1. **Job received** via Supabase webhook or polling
2. **Skills repo** cloned/updated to get latest `.claude/skills/`
3. **Agent SDK** invokes `/blueprint-turbo {url}` with:
   - `settingSources: ['project']` to load skills
   - `mcpServers` for Sequential Thinking
   - `allowedTools` for web fetching, file ops
4. **Playbook URL** extracted from agent output
5. **Supabase** updated with status and URL

## Documentation

- [Runbook](../docs/AGENT_SDK_RUNBOOK.md) - Operations guide
- [Migration Notes](../docs/AGENT_SDK_MIGRATION_NOTES.md) - Architecture decisions

## License

Private - Blueprint GTM
