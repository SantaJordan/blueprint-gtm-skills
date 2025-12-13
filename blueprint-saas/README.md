# Blueprint SaaS (Playbooks)

Next.js app deployed on Vercel that handles Stripe checkout, Supabase job creation, and user status/playbook routing.

## End‑to‑End Flow

1. User enters a company domain on `/`.
2. `/api/create-checkout` creates a Stripe Checkout Session with manual capture and metadata `{ domain, company_url }`.
3. Stripe webhook `/api/stripe-webhook` listens for `checkout.session.completed` and inserts a `blueprint_jobs` row in Supabase (`status=pending`, `payment_status=authorized`).
4. Supabase INSERT webhook triggers the Modal Agent SDK Worker (`agent-sdk-worker`).
5. Worker executes the Blueprint Turbo orchestrator (`.claude/commands/blueprint-turbo.md`) via the Claude Agent SDK, uploads HTML to Vercel Playbooks, updates `playbook_url`, then calls `/api/capture-payment` to capture the Stripe intent.
6. Status page `/status/:slug` polls `/api/job-status?domain=:slug` until completed, then redirects to `playbook_url`.
7. Visiting `/:slug` redirects to the completed playbook, or to status if still running.

## Environment Variables (Vercel)

Required:
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `MODAL_WEBHOOK_SECRET` (must match the worker env)
- `BASE_URL` (defaults to `https://playbooks.blueprintgtm.com`)

Notes:
- Price is currently set for testing in `blueprint-saas/lib/stripe.ts`.

## Deployment

1. Deploy `blueprint-saas/` to Vercel.
2. Set the env vars above in Vercel.
3. Point your custom domain `playbooks.blueprintgtm.com` at this project.
4. Configure a Stripe webhook to `https://playbooks.blueprintgtm.com/api/stripe-webhook`.
5. Configure Supabase `blueprint_jobs` INSERT webhook to your Modal Agent SDK Worker endpoint.
6. Ensure Modal secrets include:
   - `VERCEL_TOKEN` (for playbook uploads)
   - `VERCEL_API_URL=https://playbooks.blueprintgtm.com`
   - `MODAL_WEBHOOK_SECRET` (same value as SaaS)

## Local Development

```bash
cd blueprint-saas
npm install
npm run dev
```

Create a local `.env.local` with the required variables.
