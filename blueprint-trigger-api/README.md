# Blueprint Trigger API

API endpoint for queuing Blueprint GTM analyses from mobile devices.

## Deployment

1. Install Vercel CLI if you haven't already:
```bash
npm install -g vercel
```

2. Deploy to Vercel:
```bash
cd blueprint-trigger-api
vercel
```

3. Follow the prompts:
   - Link to existing project or create new one
   - Set project name: `blueprint-trigger-api`
   - Link to Vercel account

4. After deployment, you'll get a URL like: `https://blueprint-trigger-api.vercel.app`

## Environment Variables

The following environment variables are configured in `vercel.json`:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_ANON_KEY`: Your Supabase anonymous/publishable key

## Usage

### Queue a new job

```bash
curl -X POST https://blueprint-trigger-api.vercel.app/api/queue-job \
  -H "Content-Type: application/json" \
  -d '{"companyUrl": "https://example.com"}'
```

Response:
```json
{
  "success": true,
  "job": {
    "id": "uuid-here",
    "companyUrl": "https://example.com",
    "status": "pending",
    "createdAt": "2025-11-16T..."
  },
  "message": "Job queued successfully! Your Mac will process it soon."
}
```

## iOS Shortcuts Integration

See `PHONE_SETUP.md` for instructions on creating an iOS Shortcut to call this API.
