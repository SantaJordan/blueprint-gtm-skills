# Agent SDK Worker Notes

**Document Version:** 1.2
**Last Updated:** 2025-12-13

This document describes the **current** cloud execution path for Blueprint Turbo using the Claude Agent SDK (Modal worker). It intentionally omits retired worker flows.

---

## 1. Current Cloud Flow

All entrypoints converge on a single cloud worker:

```
Mobile (iOS Shortcut) OR blueprint-saas (Stripe)
        ↓
Vercel API (optional, for mobile)
        ↓
Supabase (blueprint_jobs)
        ↓ INSERT webhook (or poll cron fallback)
Modal Agent SDK Worker (agent-sdk-worker)
        ↓
Claude Code Engine + .claude/skills + MCP
        ↓
HTML playbook
        ↓
Upload to Vercel Playbooks (playbooks.blueprintgtm.com/{slug})
        ↓
Update Supabase (status, playbook_url)
        ↓ (Stripe jobs only)
POST /api/capture-payment (manual capture)
```

---

## 2. What the Cloud Worker Does

At a high level, the worker:

1. **Claims a job** from `blueprint_jobs` and marks it `processing`.
2. **Ensures skills/commands are available** in the container (project + user-level install for Linux compatibility).
3. **Optionally pre-fetches context via Apify** (if `APIFY_API_TOKEN` is present):
   - `apify/rag-web-browser` for key website pages (markdown)
   - `apify/google-search-scraper` for fast external context
4. **Builds the agent prompt** by combining:
   - A strict timebox + “best-effort” rules (to prevent infinite research)
   - The full Blueprint Turbo orchestrator from `.claude/commands/blueprint-turbo.md` with `$ARGUMENTS` replaced by the company URL
   - The pre-fetched context block (when enabled)
5. **Runs the Claude Agent SDK** with the Claude Code harness:
   - `systemPrompt: { preset: "claude_code" }`
   - `settingSources: ["project", "user"]`
   - MCP servers enabled (Sequential Thinking + Browser MCP)
6. **Finds the generated playbook HTML** (prefers `PLAYBOOK_PATH`, otherwise searches expected locations).
7. **Uploads HTML to Vercel** and returns a shareable URL: `https://playbooks.blueprintgtm.com/{slug}`.
8. **Updates Supabase** (`completed`/`failed`, `playbook_url`, error details).
9. **Triggers payment capture** for Stripe-created jobs (if configured).

---

## 3. Why the Worker Embeds the Turbo Command File

The worker embeds `.claude/commands/blueprint-turbo.md` directly into the Agent SDK prompt (with `$ARGUMENTS` substituted) to make execution deterministic in a non-interactive cloud environment.

This keeps the cloud worker aligned to the same “source of truth” as local Turbo: the command file + skills in `.claude/skills/`.

---

## 4. Performance & Reliability Levers

If cloud runs are slow or produce weaker evidence, these are the highest-impact levers:

- **Browser MCP actually being used**: if you see 0 browser-mcp tool calls and lots of WebFetch, Wave 1/2 will drag.
- **Apify pre-fetch**: reduces bot-blocking / JS-only page issues and cuts down tool-loop variance.
- **Timeboxing**: forces completion and prevents “research spirals” that lead to timeouts.
- **Observability logs**: wave transitions + tool call breakdown make it obvious where time is going.

---

## 5. Operations Checklist

- Supabase INSERT webhook points to: `https://[workspace]--blueprint-agent-sdk-worker-process-blueprint-job.modal.run`
- Modal secrets exist:
  - `blueprint-secrets` (Anthropic + Supabase + optional payment capture vars)
  - `blueprint-vercel` (`VERCEL_TOKEN`)
  - `apify-token` (`APIFY_API_TOKEN`, optional feature but expected by the wrapper)
- Verify worker health via logs: `modal app logs blueprint-agent-sdk-worker`
- For stuck jobs, reset via SQL (from the runbook): `docs/AGENT_SDK_RUNBOOK.md`

