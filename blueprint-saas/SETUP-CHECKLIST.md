# Blueprint GTM Payment Setup Checklist

Follow these steps to fix the payment and workflow triggering issues.

## 1. Fix Vercel Environment Variables

**Go to:** Vercel Dashboard → blueprint-saas project → Settings → Environment Variables

### Required Variables

| Variable | Value | Notes |
|----------|-------|-------|
| `STRIPE_SECRET_KEY` | `sk_live_...` or `sk_test_...` | Copy fresh from Stripe, no extra spaces |
| `STRIPE_PUBLISHABLE_KEY` | `pk_live_...` or `pk_test_...` | Match mode with secret key |
| `STRIPE_WEBHOOK_SECRET` | `whsec_...` | From Stripe webhook endpoint |
| `BASE_URL` | `https://playbooks.blueprintgtm.com` | No trailing slash |
| `SUPABASE_URL` | `https://xxx.supabase.co` | Your Supabase project URL |
| `SUPABASE_SERVICE_KEY` | `eyJ...` | Supabase service role key |
| `MODAL_WEBHOOK_SECRET` | (your secret) | Shared secret for Modal auth |

### Common Issues

- **Invalid character in STRIPE_SECRET_KEY**: Delete and re-add the variable
- **Copy/paste issue**: Type the key manually or ensure no newlines
- **Wrong mode**: Use `sk_test_*` for testing, `sk_live_*` for production

After updating, **redeploy the project** for changes to take effect.

---

## 2. Configure Stripe Webhook

**Go to:** Stripe Dashboard → Developers → Webhooks

### Create/Edit Webhook Endpoint

| Setting | Value |
|---------|-------|
| Endpoint URL | `https://playbooks.blueprintgtm.com/api/stripe-webhook` |
| Events | `checkout.session.completed`, `payment_intent.canceled` |

### Get Signing Secret

1. Click on the webhook endpoint
2. Click "Reveal" next to "Signing secret"
3. Copy the `whsec_...` value
4. Add to Vercel as `STRIPE_WEBHOOK_SECRET`

### Test the Webhook

1. Go to the webhook endpoint in Stripe
2. Click "Send test webhook"
3. Select `checkout.session.completed`
4. Send and check Vercel logs for `[stripe-webhook]` messages

---

## 3. Configure Supabase Database Webhook

**Go to:** Supabase Dashboard → Database → Webhooks (or Database Functions)

### Option A: Database Webhook (Preferred)

Create a new webhook:

| Setting | Value |
|---------|-------|
| Name | `trigger-modal-worker` |
| Table | `blueprint_jobs` |
| Events | `INSERT` |
| Type | HTTP Request |
| Method | `POST` |
| URL | `https://[your-modal-workspace]--blueprint-agent-sdk-worker-process-blueprint-job.modal.run` |
| Headers | `Content-Type: application/json` |

**To get the Modal URL:**
```bash
modal app list
# Find blueprint-agent-sdk-worker and note the URL
```

### Option B: Rely on Cron (Fallback)

The Modal worker has a built-in cron that polls for pending jobs every 5 minutes.
If webhook setup is complex, this fallback will work (with 5-min delay).

Check cron is deployed:
```bash
modal app logs blueprint-agent-sdk-worker
# Look for "[Cron] Found pending job:" messages
```

---

## 4. Verify Database Schema

**Go to:** Supabase Dashboard → Table Editor → `blueprint_jobs`

Required columns:
- `id` (uuid, primary key)
- `company_url` (text)
- `status` (text) - values: pending, processing, completed, failed
- `playbook_url` (text, nullable)
- `error_message` (text, nullable)
- `checkpoint_wave` (text, nullable) - optional, enables resume/checkpointing
- `checkpoint_data` (jsonb, nullable) - optional, enables resume/checkpointing
- `stripe_checkout_session_id` (text, nullable)
- `stripe_payment_intent_id` (text, nullable)
- `customer_email` (text, nullable)
- `payment_status` (text) - values: pending, authorized, captured, failed, refunded
- `payment_captured_at` (timestamptz, nullable)
- `amount_cents` (integer)
- `created_at` (timestamptz)

If table doesn't exist, run the migration in `supabase-migration.sql`.

---

## 5. Test the Flow

### Run Local Test
```bash
cd blueprint-saas
npm install  # Install tsx dependency
npm run test:payment
```

### Run Against Live Environment
```bash
npm run test:payment:live
```

### Manual Test
1. Go to https://playbooks.blueprintgtm.com
2. Enter a test domain (e.g., test123.com)
3. Complete Stripe checkout with test card: `4242 4242 4242 4242`
4. Watch Vercel logs for `[create-checkout]`, `[stripe-webhook]` messages
5. Verify job appears in Supabase
6. Check Modal logs for processing

---

## Debugging Commands

```bash
# Watch Vercel logs in real-time
npx vercel logs playbooks.blueprintgtm.com --follow

# Check Modal worker logs
modal app logs blueprint-agent-sdk-worker

# Query Supabase for recent jobs (via SQL editor)
SELECT * FROM blueprint_jobs ORDER BY created_at DESC LIMIT 10;
```

---

## Expected Log Flow

1. `[create-checkout] Environment check: {...}`
2. `[create-checkout] Processing: { domain, slug, ... }`
3. User completes Stripe checkout
4. `[stripe-webhook] Received webhook request`
5. `[stripe-webhook] Signature verified, event type: checkout.session.completed`
6. `[stripe-webhook] Creating job in Supabase...`
7. `[stripe-webhook] Job created successfully: { jobId, ... }`
8. Modal worker: `[Worker] Processing job {id} for {url}`
9. (execution time varies by company + data availability)
10. Modal worker: `[Worker] Job {id} completed successfully`
11. `[job-status] Found job: { status: completed, ... }`
