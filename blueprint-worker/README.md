# Blueprint GTM Worker

Serverless worker that processes Blueprint GTM jobs using Modal.com.

## Architecture

```
Supabase (blueprint_jobs table)
    │
    └── INSERT webhook ──► Modal Worker (process_blueprint_job)
                                │
                                ├── Wave 1: Company Research
                                ├── Wave 0.5: Product Fit Analysis
                                ├── Wave 1.5: Niche Conversion
                                ├── Wave 2: Data Landscape
                                ├── Synthesis: Sequential Thinking
                                ├── Hard Gates: 5-Gate Validation
                                ├── Wave 3: Message Generation
                                ├── Wave 4: HTML Assembly
                                └── Wave 4.5: GitHub Pages Publish
                                        │
                                        └── Updates Supabase (playbook_url)
```

## Setup

### 1. Install Modal CLI

```bash
pip install modal
```

### 2. Authenticate with Modal

```bash
modal token set --token-id YOUR_TOKEN_ID --token-secret YOUR_TOKEN_SECRET
```

### 3. Create Secrets

Run the setup script:
```bash
chmod +x setup_secrets.sh
./setup_secrets.sh
```

Or manually:
```bash
modal secret create blueprint-secrets \
    ANTHROPIC_API_KEY="sk-ant-..." \
    SERPER_API_KEY="..." \
    SUPABASE_URL="https://xxx.supabase.co" \
    SUPABASE_SERVICE_KEY="eyJ..." \
    GITHUB_TOKEN="ghp_..." \
    GITHUB_OWNER="SantaJordan" \
    GITHUB_REPO="blueprint-gtm-playbooks"
```

### 4. Deploy

```bash
cd blueprint-worker
modal deploy main.py
```

You'll see output like:
```
✓ Created web endpoint: https://santajordan--blueprint-gtm-worker-process-blueprint-job.modal.run
```

### 5. Configure Supabase Webhook

In Supabase Dashboard:

1. Go to **Database > Webhooks** (or **Database > Integrations > Webhooks**)
2. Click **Create a new hook**
3. Configure:
   - **Name:** `blueprint-job-created`
   - **Table:** `blueprint_jobs`
   - **Events:** `INSERT`
   - **Type:** `HTTP Request`
   - **Method:** `POST`
   - **URL:** (copy from Modal deploy output, e.g., `https://santajordan--blueprint-gtm-worker-process-blueprint-job.modal.run`)
   - **Headers:**
     ```
     Content-Type: application/json
     ```

**Note:** The webhook will send the full row data on INSERT, which includes:
```json
{
  "type": "INSERT",
  "table": "blueprint_jobs",
  "record": {
    "id": "uuid",
    "company_url": "https://...",
    "status": "pending",
    "created_at": "..."
  }
}
```

### 6. Ensure Supabase Table Schema

Make sure your `blueprint_jobs` table has these columns:

```sql
CREATE TABLE blueprint_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_url TEXT NOT NULL,
  status TEXT DEFAULT 'pending',
  playbook_url TEXT,
  company_name TEXT,
  error TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  started_at TIMESTAMP WITH TIME ZONE,
  completed_at TIMESTAMP WITH TIME ZONE,
  failed_at TIMESTAMP WITH TIME ZONE
);

-- Enable Row Level Security (optional but recommended)
ALTER TABLE blueprint_jobs ENABLE ROW LEVEL SECURITY;

-- Allow anonymous read access for status checking
CREATE POLICY "Allow anonymous read" ON blueprint_jobs
  FOR SELECT USING (true);
```

## Testing

### Local Test
```bash
modal run main.py --company-url "https://owner.com"
```

### End-to-End Test
```bash
curl -X POST https://your-vercel.vercel.app/api/queue-job \
  -H "Content-Type: application/json" \
  -d '{"companyUrl": "https://owner.com"}'
```

## Cost Breakdown

| Component | Cost |
|-----------|------|
| Claude Opus (key decisions) | ~$1.50 |
| Claude Sonnet (bulk work) | ~$0.90 |
| Serper API (~50 searches) | ~$0.05 |
| Modal compute (~15 min) | ~$0.15 |
| **Total per run** | **~$2.60** |

## File Structure

```
blueprint-worker/
├── main.py                    # Modal app + orchestrator
├── setup_secrets.sh           # Secrets configuration script
├── tools/
│   ├── web_fetch.py           # Async HTTP fetching
│   ├── web_search.py          # Serper API wrapper
│   └── sequential_thinking.py # Prompt-based reasoning
└── waves/
    ├── wave1_company_research.py
    ├── wave05_product_fit.py
    ├── wave15_niche_conversion.py
    ├── wave2_data_landscape.py
    ├── synthesis.py
    ├── hard_gates.py
    ├── wave3_messages.py
    ├── wave4_html.py
    └── wave45_publish.py
```

## Backup Cron

The worker includes a backup cron job that polls for pending jobs every 5 minutes.
This ensures jobs are processed even if the Supabase webhook fails.
