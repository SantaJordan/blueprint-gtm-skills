# ✅ Deployment Checklist - Blueprint Turbo Mobile Trigger

Use this checklist to deploy the complete system step-by-step.

## 📋 Pre-Deployment Checklist

- [x] Supabase project created: `hvuwlhdaswixbkglnrxu`
- [x] Supabase `blueprint_jobs` table created
- [x] Vercel account connected to Supabase
- [x] Auto-approval settings configured
- [x] All code files created

## 🚀 Deployment Steps

### Step 1: Deploy Vercel API

**Time: ~2 minutes**

```bash
cd blueprint-trigger-api
npm install
vercel
```

**Prompts & Answers:**
- Set up and deploy? → `Y`
- Which scope? → Select your account
- Link to existing project? → `N`
- Project name? → `blueprint-trigger-api`
- Directory? → `./` (press Enter)
- Override settings? → `N`

**After deployment:**
- [ ] Copy the deployment URL (e.g., `https://blueprint-trigger-api-xxxx.vercel.app`)
- [ ] Test API:
  ```bash
  curl -X POST https://your-url.vercel.app/api/queue-job \
    -H "Content-Type: application/json" \
    -d '{"companyUrl": "https://www.owner.com"}'
  ```
- [ ] Verify response shows `"success": true`

### Step 2: Install Mac Worker

**Time: ~3 minutes**

```bash
cd scripts
npm install
```

**Test worker manually first:**
```bash
node blueprint-worker.js
```

Expected output:
```
[2025-11-16T...] Blueprint Worker started
[2025-11-16T...] Polling interval: 30000ms (30s)
[2025-11-16T...] Worker is now polling for jobs...
```

- [ ] Worker starts without errors
- [ ] Press Ctrl+C to stop

**Install as service:**
```bash
npm run install-service
```

Expected output:
```
✓ Logs directory created
✓ LaunchAgents directory exists
✓ LaunchAgent loaded successfully
✓ Service is running
```

**Verify installation:**
```bash
launchctl list | grep com.blueprint.worker
```

Should show the service with a PID.

- [ ] Service installed successfully
- [ ] Service is running

### Step 3: Test End-to-End

**Time: ~15 minutes (one full Blueprint Turbo run)**

**Queue a test job:**
```bash
curl -X POST https://your-vercel-url.vercel.app/api/queue-job \
  -H "Content-Type: application/json" \
  -d '{"companyUrl": "https://www.owner.com"}'
```

**Monitor the worker:**
```bash
tail -f logs/blueprint-worker.log
```

**Expected sequence:**
1. Within 30 seconds: Worker finds the job
2. Job status → `processing`
3. Claude Code starts executing `/blueprint-turbo`
4. ~12-15 minutes later: Job completes
5. Job status → `completed`
6. Playbook URL populated

**Verification checklist:**
- [ ] Job created in Supabase (check dashboard)
- [ ] Worker picked up job within 30 seconds
- [ ] Claude Code executed without prompts
- [ ] Playbook generated and published
- [ ] Job marked as `completed` in Supabase
- [ ] `playbook_url` field populated

### Step 4: Create iOS Shortcut

**Time: ~5 minutes**

Open Shortcuts app on iPhone:

1. **Create New Shortcut**
   - [ ] Tap `+` button
   - [ ] Name: "Analyze with Blueprint"

2. **Add Actions (in order):**
   - [ ] **Get URLs from** → Shortcut Input
   - [ ] **Get Item from List** → First Item
   - [ ] **Get Contents of URL**:
     - URL: `https://your-vercel-url.vercel.app/api/queue-job`
     - Method: `POST`
     - Request Body: `JSON`
     - Add field "companyUrl" → Value: Item from List
   - [ ] **Show Notification** → "✅ Company added to Blueprint queue!"

3. **Configure Share Sheet**
   - [ ] Tap shortcut info (ⓘ)
   - [ ] Toggle ON: "Show in Share Sheet"
   - [ ] Enable: URLs, Safari Web Pages
   - [ ] Tap Done

4. **Test Shortcut**
   - [ ] Open Safari → Go to company website
   - [ ] Tap Share button
   - [ ] See "Analyze with Blueprint"
   - [ ] Tap it
   - [ ] See success notification

### Step 5: Full Integration Test

**Test the complete flow from phone to playbook:**

1. **On iPhone:**
   - [ ] Browse to a company you haven't analyzed yet
   - [ ] Tap Share → "Analyze with Blueprint"
   - [ ] See success notification

2. **On Mac:**
   - [ ] Open Terminal
   - [ ] Run: `tail -f logs/blueprint-worker.log`
   - [ ] Within 30 seconds, see job picked up
   - [ ] Watch Claude Code execute

3. **Wait for completion** (~12-15 minutes)
   - [ ] Worker logs show completion
   - [ ] Check Supabase dashboard
   - [ ] Job status is `completed`
   - [ ] `playbook_url` is populated

4. **Verify playbook:**
   - [ ] Visit the playbook URL
   - [ ] Playbook loads correctly
   - [ ] Contains analysis for correct company

## 🎉 Post-Deployment

### Optional Enhancements

- [ ] Add home screen widget for one-tap access
- [ ] Set up Siri voice command
- [ ] Create status dashboard
- [ ] Add push notifications
- [ ] Configure API authentication

### Documentation Review

- [ ] Read [MOBILE_TRIGGER_README.md](MOBILE_TRIGGER_README.md)
- [ ] Bookmark [PHONE_SETUP.md](PHONE_SETUP.md) for reference
- [ ] Save Vercel URL somewhere secure

### Monitoring Setup

Add these commands to your notes:

```bash
# Check worker status
launchctl list | grep com.blueprint.worker

# View logs
tail -f logs/blueprint-worker.log

# Restart worker
launchctl unload ~/Library/LaunchAgents/com.blueprint.worker.plist
launchctl load ~/Library/LaunchAgents/com.blueprint.worker.plist

# Check Supabase queue
# Visit: https://supabase.com/dashboard/project/hvuwlhdaswixbkglnrxu
```

## 🐛 Troubleshooting

If anything fails, run the test script:

```bash
./scripts/test-system.sh
```

Common issues:

| Issue | Fix |
|-------|-----|
| API deployment fails | Check Vercel account is connected |
| Worker won't start | Check Node.js is installed: `node --version` |
| No jobs picked up | Check worker is running: `launchctl list \| grep blueprint` |
| Claude prompts for approval | Check `.claude/settings.local.json` has auto-approval |
| Shortcut network error | Verify Vercel URL in shortcut is correct |

See [PHONE_SETUP.md](PHONE_SETUP.md) for detailed troubleshooting.

## ✅ Success Criteria

You know it's working when:

1. ✅ You can trigger from phone in <5 seconds
2. ✅ Worker picks up job within 30 seconds
3. ✅ Claude Code runs without prompts
4. ✅ Playbook publishes to GitHub Pages
5. ✅ Job marked complete in Supabase
6. ✅ You can queue multiple companies

## 📊 System Health Check

Run this weekly to ensure everything is working:

```bash
# 1. Check worker is running
launchctl list | grep com.blueprint.worker

# 2. Check recent log activity
tail -20 logs/blueprint-worker.log

# 3. Test API endpoint
curl -X POST https://your-url.vercel.app/api/queue-job \
  -H "Content-Type: application/json" \
  -d '{"companyUrl": "https://test.com"}'

# 4. Check Supabase for stuck jobs
# Visit dashboard and look for jobs stuck in 'processing' status
```

## 🎊 Deployment Complete!

Once all checkboxes are marked:

✅ **System is live and operational**
✅ **You can analyze companies from anywhere**
✅ **Mac processes jobs automatically**
✅ **Results publish to GitHub Pages**

**Total deployment time:** ~20 minutes (excluding first test run)
**Total cost:** $0/month
**Total convenience:** Infinite! 🚀

---

**Need help?** See [PHONE_SETUP.md](PHONE_SETUP.md) for detailed instructions and troubleshooting.

**Ready to use?** Open Safari on your iPhone, go to any company, and tap Share → "Analyze with Blueprint"!
