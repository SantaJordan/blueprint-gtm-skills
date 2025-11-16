# 🚀 Quick Start - Mobile Trigger Setup

Get Blueprint Turbo running from your phone in 10 minutes!

## ⚡ Super Fast Setup

### 1. Deploy Vercel API (2 minutes)

```bash
cd blueprint-trigger-api
npm install
vercel
```

Save the URL you get (e.g., `https://blueprint-trigger-api-xxxx.vercel.app`)

### 2. Install Mac Worker (3 minutes)

```bash
cd scripts
npm install
npm run install-service
```

### 3. Create iOS Shortcut (5 minutes)

Open Shortcuts app → New Shortcut → Add these actions:

1. **Get URLs from** Shortcut Input
2. **Get First Item** from URLs
3. **Get Contents of URL** (POST to `https://your-vercel-url.vercel.app/api/queue-job`)
   - Method: POST
   - JSON Body: `{"companyUrl": "Item from List"}`
4. **Show Notification** "✅ Company added to Blueprint queue!"

Enable in Share Sheet → Done!

### 4. Test It! (30 seconds)

1. Open Safari → Go to any company website
2. Tap Share → "Analyze with Blueprint"
3. Done! Check `tail -f logs/blueprint-worker.log` to watch it run

---

## 📖 Full Instructions

See [PHONE_SETUP.md](PHONE_SETUP.md) for detailed step-by-step instructions with screenshots.

---

## ✅ What You've Built

**Phone Trigger Flow:**
```
iPhone Safari
    ↓ Share Sheet
iOS Shortcut
    ↓ HTTP POST
Vercel API
    ↓ Insert Job
Supabase Queue
    ↓ Poll (every 30s)
Mac Worker
    ↓ Execute
/blueprint-turbo
    ↓ Publish
GitHub Pages
```

**You can now:**
- ✅ Trigger analyses from anywhere
- ✅ Queue multiple companies
- ✅ Let your Mac process in background
- ✅ Get results on GitHub Pages
- ✅ Use Siri voice commands
- ✅ One-tap from any app

---

## 🔍 Quick Commands

```bash
# View worker logs
tail -f logs/blueprint-worker.log

# Restart worker
launchctl unload ~/Library/LaunchAgents/com.blueprint.worker.plist
launchctl load ~/Library/LaunchAgents/com.blueprint.worker.plist

# Test API
curl -X POST https://your-vercel-url.vercel.app/api/queue-job \
  -H "Content-Type: application/json" \
  -d '{"companyUrl": "https://www.owner.com"}'

# Check Supabase jobs
# Visit: https://supabase.com/dashboard/project/hvuwlhdaswixbkglnrxu
# → Table Editor → blueprint_jobs
```

---

**That's it! You're done! 🎉**

Now go trigger some analyses from your phone!
