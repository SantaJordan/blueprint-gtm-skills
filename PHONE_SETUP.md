# 📱 Phone Setup Guide - Blueprint Turbo Mobile Trigger

This guide shows you how to trigger Blueprint Turbo analyses from your iPhone.

## 🎯 What You'll Get

- **Share Sheet Integration**: Browse to any company website → Tap Share → "Analyze with Blueprint"
- **One-Tap Execution**: Company added to queue instantly
- **Background Processing**: Your always-on Mac processes the job automatically
- **Results on GitHub**: Playbook published to GitHub Pages when complete

---

## 📋 Prerequisites

Before starting, make sure you've completed:

1. ✅ Deployed Vercel API (see below)
2. ✅ Installed Mac Worker (see below)
3. ✅ Have your Vercel API URL ready

---

## 🚀 Step 1: Deploy Vercel API

### 1.1 Install Dependencies

```bash
cd blueprint-trigger-api
npm install
```

### 1.2 Deploy to Vercel

```bash
# If you don't have Vercel CLI installed:
npm install -g vercel

# Deploy
vercel
```

Follow the prompts:
- **Set up and deploy?** Yes
- **Which scope?** Your account
- **Link to existing project?** No
- **Project name?** `blueprint-trigger-api`
- **Directory?** `./` (just press Enter)
- **Override settings?** No

### 1.3 Get Your API URL

After deployment, Vercel will show your URL:
```
https://blueprint-trigger-api-xxxx.vercel.app
```

**Save this URL** - you'll need it for the iOS Shortcut!

### 1.4 Test the API

```bash
curl -X POST https://blueprint-trigger-api-xxxx.vercel.app/api/queue-job \
  -H "Content-Type: application/json" \
  -d '{"companyUrl": "https://www.owner.com"}'
```

You should see:
```json
{
  "success": true,
  "job": { ... },
  "message": "Job queued successfully! Your Mac will process it soon."
}
```

---

## 💻 Step 2: Install Mac Worker

### 2.1 Install Dependencies

```bash
cd scripts
npm install
```

### 2.2 Test the Worker Manually

Before installing as a service, test it works:

```bash
node blueprint-worker.js
```

You should see:
```
[2025-11-16T...] Blueprint Worker started
[2025-11-16T...] Polling interval: 30000ms (30s)
[2025-11-16T...] Worker is now polling for jobs...
```

Leave it running and test by queuing a job via the API (Step 1.4). You should see the worker pick it up and execute `/blueprint-turbo`.

**Press Ctrl+C to stop** once you've verified it works.

### 2.3 Install as LaunchAgent (Auto-Start on Boot)

```bash
npm run install-service
```

This will:
- Copy the LaunchAgent plist to `~/Library/LaunchAgents/`
- Start the worker service
- Configure it to run on startup

**Verify it's running:**
```bash
launchctl list | grep com.blueprint.worker
```

**View logs:**
```bash
tail -f ../logs/blueprint-worker.log
```

---

## 📱 Step 3: Create iOS Shortcut

### 3.1 Open Shortcuts App

1. Open the **Shortcuts** app on your iPhone
2. Tap the **+** button (top right) to create a new shortcut

### 3.2 Add Actions

Add these actions in order:

#### Action 1: Get URL from Input
1. Search for "**Get URLs from**"
2. Tap to add it
3. Set it to: "Get URLs from **Shortcut Input**"

#### Action 2: Get First URL
1. Search for "**Get Item from List**"
2. Tap to add it
3. Set it to: "Get **First Item** from **URLs**"

#### Action 3: Make HTTP Request
1. Search for "**Get Contents of URL**"
2. Tap to add it
3. Configure it:
   - **URL**: `https://blueprint-trigger-api-xxxx.vercel.app/api/queue-job`
     (Replace `xxxx` with your actual Vercel URL!)
   - **Method**: `POST`
   - **Request Body**: `JSON`
   - Tap "**Add new field**" → "**Text**"
   - **Key**: `companyUrl`
   - **Value**: Tap and select "**Item from List**" (the URL from step 2)

#### Action 4: Show Notification
1. Search for "**Show Notification**"
2. Tap to add it
3. Set **Text** to: "✅ Company added to Blueprint queue!"

### 3.3 Configure Shortcut Details

1. Tap the shortcut name at the top and rename it: **Analyze with Blueprint**
2. Tap the icon and choose a color/icon you like
3. Tap **Done** (top right)

### 3.4 Enable Share Sheet

1. Tap the **ⓘ** icon on your shortcut
2. Toggle **ON**: "Show in Share Sheet"
3. Under "Share Sheet Types", enable:
   - ✅ **URLs**
   - ✅ **Safari Web Pages**
4. Tap **Done**

---

## 🎉 Step 4: Test It!

### From Safari:
1. Open Safari and go to any company website (e.g., `https://www.owner.com`)
2. Tap the **Share** button
3. Scroll down and tap **Analyze with Blueprint**
4. You should see: "✅ Company added to Blueprint queue!"

### What Happens Next:
1. 📤 URL sent to Vercel API
2. 💾 Job added to Supabase queue
3. ⏰ Within 30 seconds, Mac worker picks up the job
4. 🤖 Claude Code executes `/blueprint-turbo`
5. 📊 Playbook generated and published to GitHub Pages
6. ✅ Job marked as complete in database

### Check Job Status:

You can check the job was created in Supabase:
1. Go to https://supabase.com/dashboard/project/hvuwlhdaswixbkglnrxu
2. Click **Table Editor** → **blueprint_jobs**
3. See your queued/processing/completed jobs

---

## 🔍 Troubleshooting

### Shortcut says "Network error"
- Check your Vercel URL is correct in the shortcut
- Make sure you deployed the API successfully
- Test the API with curl (see Step 1.4)

### Worker not picking up jobs
- Check worker is running: `launchctl list | grep com.blueprint.worker`
- Check logs: `tail -f logs/blueprint-worker.log`
- Restart worker: `launchctl unload ~/Library/LaunchAgents/com.blueprint.worker.plist && launchctl load ~/Library/LaunchAgents/com.blueprint.worker.plist`

### Claude Code asks for approval
- Make sure `.claude/settings.local.json` has all the auto-approval rules
- The worker should have set `CLAUDE_CODE_AUTO_APPROVE=true`

### Jobs failing
- Check error logs: `tail -f logs/blueprint-worker-error.log`
- Check the `error_message` column in Supabase `blueprint_jobs` table
- Make sure Claude Code CLI is installed: `which claude`

---

## 🎊 You're All Set!

You can now trigger Blueprint Turbo analyses from anywhere:

- 🏖️ At the beach
- ☕ At a coffee shop
- 🚗 In the car (using Siri - just say "Hey Siri, Analyze with Blueprint")
- 🛋️ On the couch

Your Mac at home will process everything automatically and publish to GitHub Pages!

---

## 💡 Pro Tips

### Add a Home Screen Widget
1. Go to your shortcut
2. Tap **ⓘ** → **Add to Home Screen**
3. Now you have a one-tap button on your home screen!

### Use Siri Voice Commands
Just say: **"Hey Siri, Analyze with Blueprint"**
(You'll need to paste the URL when prompted, or use it from the Share Sheet)

### Queue Multiple Companies
The worker processes jobs sequentially. You can:
1. Browse to Company A → Share → Analyze
2. Browse to Company B → Share → Analyze
3. Browse to Company C → Share → Analyze

All three will queue up and process one after another!

### Check Completion
- Watch logs in real-time: `tail -f logs/blueprint-worker.log`
- Check Supabase table for completed jobs and their `playbook_url`
- Results appear on your GitHub Pages site automatically

---

## 🔐 Security Notes

- The Vercel API is public but only accepts company URLs
- Supabase uses Row Level Security (currently open - you can restrict this)
- Worker uses service role key (stored locally on Mac)
- No sensitive data is transmitted through the API

If you want to add authentication:
1. Add an API key to Vercel environment variables
2. Update the shortcut to send the API key in headers
3. Update `api/queue-job.js` to validate the API key

---

## 📚 Additional Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Supabase Documentation](https://supabase.com/docs)
- [iOS Shortcuts User Guide](https://support.apple.com/guide/shortcuts/welcome/ios)
- [macOS LaunchAgents Guide](https://support.apple.com/guide/terminal/script-management-with-launchd-apdc6c1077b-5d5d-4d35-9c19-60f2397b2369/mac)

---

**Need Help?** Check the logs first:
```bash
# Worker logs
tail -f logs/blueprint-worker.log

# Worker errors
tail -f logs/blueprint-worker-error.log

# Test API
curl -X POST <your-vercel-url>/api/queue-job -H "Content-Type: application/json" -d '{"companyUrl": "https://test.com"}'
```

Happy analyzing! 🚀
