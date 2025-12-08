# Agent SDK Worker Runbook

**Version:** 1.0.0
**Last Updated:** 2025-12-08

This runbook describes how to operate the Agent SDK Worker for Blueprint Turbo.

---

## Overview

The Agent SDK Worker replaces the previous Modal Python worker with a Claude Agent SDK-based implementation. It provides:

- **90-95% quality parity** with local `/blueprint-turbo` execution
- **Single source of truth**: Uses `.claude/skills/` directly
- **Native MCP support**: Sequential Thinking MCP for synthesis
- **Automatic skill loading**: Via `settingSources: ['project']`

---

## Architecture

```
iPhone → Vercel API → Supabase → Modal Webhook
                                      ↓
                              Agent SDK Worker (Node.js)
                                      ↓
                              query("/blueprint-turbo {url}")
                                      ↓
                              Claude Code Engine
                                      ↓
                              HTML playbook + git push
                                      ↓
                              Update Supabase
```

---

## Local Development

### Prerequisites

1. Node.js 20+
2. npm
3. Environment variables configured

### Setup

```bash
cd agent-sdk-worker
npm install
```

### Environment Variables

Create a `.env` file or export these variables:

```bash
# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Supabase
export SUPABASE_URL="https://hvuwlhdaswixbkglnrxu.supabase.co"
export SUPABASE_SERVICE_KEY="sb_secret_..."

# GitHub
export GITHUB_TOKEN="ghp_..."
export GITHUB_OWNER="SantaJordan"
export GITHUB_REPO="blueprint-gtm-playbooks"
```

### Running Locally

**Test with a URL (bypasses Supabase):**
```bash
npm run process-job -- --url https://owner.com
```

**Process a specific job by ID:**
```bash
npm run process-job -- <job-id>
```

**Poll for pending jobs:**
```bash
npm run process-job -- --poll
```

---

## Modal Deployment

### Prerequisites

1. Modal account and CLI installed
2. Modal secrets configured

### Configure Secrets

Ensure the `blueprint-secrets` Modal secret contains:
- `ANTHROPIC_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `GITHUB_TOKEN`

### Deploy

```bash
cd agent-sdk-worker
modal deploy modal/wrapper.py
```

### Test Deployment

```bash
# Test with a URL
modal run modal/wrapper.py --url https://owner.com

# Test with a job ID
modal run modal/wrapper.py --job-id abc123

# Run poll cron manually
modal run modal/wrapper.py --poll
```

### View Logs

```bash
modal app logs blueprint-agent-sdk-worker
```

---

## Supabase Webhook Configuration

### Update Webhook URL

1. Go to Supabase Dashboard → Database → Webhooks
2. Find the `blueprint_jobs` INSERT webhook
3. Update URL to the new Modal endpoint:
   ```
   https://[your-modal-workspace]--blueprint-agent-sdk-worker-process-blueprint-job.modal.run
   ```

### Webhook Payload

The webhook should send the full record:
```json
{
  "record": {
    "id": "uuid",
    "company_url": "https://...",
    "status": "pending",
    "created_at": "..."
  }
}
```

---

## Monitoring

### Job Status Check

Query Supabase for job status:
```sql
SELECT id, company_url, status, playbook_url, error_message, created_at
FROM blueprint_jobs
ORDER BY created_at DESC
LIMIT 10;
```

### Common Statuses

| Status | Meaning |
|--------|---------|
| `pending` | Job queued, waiting for worker |
| `processing` | Worker has claimed job |
| `completed` | Playbook generated successfully |
| `failed` | Error during processing |

### Check for Stuck Jobs

```sql
SELECT * FROM blueprint_jobs
WHERE status = 'processing'
AND started_at < NOW() - INTERVAL '30 minutes';
```

---

## Troubleshooting

### Job Stuck in `pending`

1. Check if Modal function is deployed: `modal app list`
2. Check webhook configuration in Supabase
3. Manually trigger poll: `modal run modal/wrapper.py --poll`

### Job Stuck in `processing`

The worker may have crashed. Reset and retry:
```sql
UPDATE blueprint_jobs
SET status = 'pending', started_at = NULL
WHERE id = '<job-id>' AND status = 'processing';
```

### Agent SDK Errors

Common errors and fixes:

| Error | Cause | Fix |
|-------|-------|-----|
| `Claude Agent SDK not installed` | SDK missing | Run `npm install` |
| `Missing required environment variable` | Env not set | Check Modal secrets |
| `Git pull failed` | Network issue | Will use cached repo |
| `No playbook URL found` | Skill didn't publish | Check skill output, may need GitHub API fallback |

### MCP Server Issues

If Sequential Thinking MCP fails:
1. Check if `@sequentialthinking/mcp-server` is installed globally
2. The worker will fall back to prompt-based reasoning (slightly lower quality)

---

## Rollback Procedure

If the Agent SDK Worker has issues:

### 1. Revert Webhook

Update Supabase webhook back to old Modal endpoint:
```
https://[workspace]--blueprint-gtm-worker-process-blueprint-job.modal.run
```

### 2. Verify Old Worker

```bash
cd blueprint-worker
modal app list  # Check if old worker is still deployed
```

### 3. Test Old Worker

```bash
modal run main.py --url https://owner.com
```

---

## Performance Benchmarks

| Metric | Target | Notes |
|--------|--------|-------|
| Execution time | 15-18 min | May be longer for complex companies |
| Success rate | 95%+ | Track via Supabase |
| Quality score | 8.0+/10 | Compare to local output |

---

## Maintenance Tasks

### Weekly

- [ ] Check for stuck jobs (status = 'processing' for >30 min)
- [ ] Review error messages for patterns
- [ ] Verify playbook URLs are accessible

### Monthly

- [ ] Update npm dependencies: `npm update`
- [ ] Review Modal costs
- [ ] Compare output quality to local execution

### On Demand

- [ ] Redeploy after skill updates: `modal deploy modal/wrapper.py`
- [ ] Clear npm cache if issues: `npm cache clean --force`

---

## Contact

For issues with the Agent SDK Worker, check:
1. Modal logs: `modal app logs blueprint-agent-sdk-worker`
2. Supabase job records
3. GitHub Pages deployment status

---

*End of Runbook*
