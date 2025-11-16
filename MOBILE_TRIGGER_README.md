# 📱 Blueprint Turbo Mobile Trigger System

> Run Blueprint GTM analyses from your iPhone while your Mac does the work

## 🎯 Overview

This system lets you trigger Blueprint Turbo analyses from your phone. Just browse to any company website, tap Share, select "Analyze with Blueprint", and your always-on Mac will automatically process the analysis and publish to GitHub Pages.

## 🏗️ Architecture

```
Phone (Trigger) → Vercel API → Supabase Queue → Mac Worker → Claude Code → GitHub Pages
```

**Flow:**
1. 📱 Browse company on iPhone → Tap Share
2. ☁️ iOS Shortcut sends URL to Vercel API
3. 💾 Vercel adds job to Supabase queue
4. 🔄 Mac worker polls queue every 30s
5. 🤖 Worker executes `/blueprint-turbo <url>`
6. 📊 Playbook published to GitHub Pages
7. ✅ Job marked complete

## 📚 Documentation

| File | Purpose |
|------|---------|
| **[QUICK_START.md](QUICK_START.md)** | ⚡ 10-minute setup guide |
| **[PHONE_SETUP.md](PHONE_SETUP.md)** | 📱 Detailed iOS Shortcut instructions |
| **[SETUP_COMPLETE.md](SETUP_COMPLETE.md)** | ✅ Complete system documentation |

## 🚀 Quick Start

### Prerequisites
- ✅ Supabase account (already set up: `hvuwlhdaswixbkglnrxu`)
- ✅ Vercel account
- ✅ Always-on Mac
- ✅ iPhone with Shortcuts app
- ✅ Claude Code CLI installed

### 1. Deploy Vercel API (2 min)
```bash
cd blueprint-trigger-api
npm install
vercel
```

Save your deployment URL!

### 2. Install Mac Worker (3 min)
```bash
cd scripts
npm install
npm run install-service
```

### 3. Create iOS Shortcut (5 min)

See [PHONE_SETUP.md](PHONE_SETUP.md) for step-by-step instructions.

**Quick version:**
1. Open Shortcuts app → New Shortcut
2. Add: Get URLs → Get First → HTTP POST → Notification
3. Configure POST to your Vercel URL
4. Enable in Share Sheet

### 4. Test! (30 sec)
1. Safari → Company website
2. Share → "Analyze with Blueprint"
3. Watch: `tail -f logs/blueprint-worker.log`

## 🛠️ Components

### 1. Supabase Queue
- **Purpose**: Central job queue
- **Table**: `blueprint_jobs`
- **Dashboard**: [View](https://supabase.com/dashboard/project/hvuwlhdaswixbkglnrxu)

### 2. Vercel API
- **Files**: `blueprint-trigger-api/`
- **Endpoint**: `POST /api/queue-job`
- **Deploy**: `vercel`

### 3. Mac Worker
- **Files**: `scripts/blueprint-worker.js`
- **Service**: `com.blueprint.worker`
- **Install**: `npm run install-service`
- **Logs**: `logs/blueprint-worker.log`

### 4. iOS Shortcut
- **Name**: "Analyze with Blueprint"
- **Type**: Share Sheet
- **Trigger**: Safari, any browser

## 🧪 Testing

Run the test script to verify everything is configured:

```bash
./scripts/test-system.sh
```

## 📊 Monitoring

### Check Worker Status
```bash
launchctl list | grep com.blueprint.worker
```

### View Logs
```bash
tail -f logs/blueprint-worker.log
```

### Check Queue
Visit [Supabase Dashboard](https://supabase.com/dashboard/project/hvuwlhdaswixbkglnrxu) → Table Editor → `blueprint_jobs`

### Test API
```bash
curl -X POST https://your-url.vercel.app/api/queue-job \
  -H "Content-Type: application/json" \
  -d '{"companyUrl": "https://www.owner.com"}'
```

## 🔧 Configuration

### Auto-Approval Settings
Updated in `.claude/settings.local.json`:
- All MCP tools auto-approved
- Bash commands auto-approved
- No manual intervention needed

### Polling Interval
Edit `scripts/blueprint-worker.js`:
```javascript
const POLL_INTERVAL_MS = 30000; // 30 seconds
```

### Concurrent Jobs
Currently processes 1 job at a time sequentially. To enable parallel processing, modify the worker to handle multiple jobs.

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Network error in Shortcut | Check Vercel URL is correct |
| Worker not picking up jobs | `launchctl list \| grep blueprint` |
| Jobs stuck in processing | Check error logs, update job status manually |
| Claude asks for approval | Verify `.claude/settings.local.json` |

See [PHONE_SETUP.md](PHONE_SETUP.md) for detailed troubleshooting.

## 💰 Cost

All free tiers:
- Supabase: Free (500MB limit)
- Vercel: Free (100GB bandwidth)
- Claude Code: Your existing subscription
- GitHub Pages: Free

**Total: $0/month**

## 🎨 Future Enhancements

- [ ] Push notifications on completion
- [ ] Status dashboard web page
- [ ] API authentication
- [ ] Multi-worker support
- [ ] Queue priority system
- [ ] Slack/Discord notifications

## 📁 File Structure

```
Blueprint-GTM-Skills/
├── blueprint-trigger-api/      # Vercel API
│   ├── api/
│   │   └── queue-job.js       # API endpoint
│   ├── package.json
│   ├── vercel.json
│   └── README.md
├── scripts/                    # Mac Worker
│   ├── blueprint-worker.js    # Main worker script
│   ├── install-launchagent.js # Service installer
│   ├── com.blueprint.worker.plist
│   ├── test-system.sh         # Test script
│   └── package.json
├── logs/                       # Created on first run
│   ├── blueprint-worker.log
│   └── blueprint-worker-error.log
├── .claude/
│   └── settings.local.json    # Auto-approval config
├── QUICK_START.md             # Fast setup guide
├── PHONE_SETUP.md             # Detailed iOS guide
├── SETUP_COMPLETE.md          # Full documentation
└── MOBILE_TRIGGER_README.md   # This file
```

## 🚦 Status

✅ Supabase database created
✅ Auto-approval configured
✅ Vercel API ready to deploy
✅ Mac worker ready to install
✅ Documentation complete

**Ready to deploy!**

## 📞 Need Help?

1. Check logs: `tail -f logs/blueprint-worker.log`
2. Read docs: [PHONE_SETUP.md](PHONE_SETUP.md)
3. Test components: `./scripts/test-system.sh`

---

**Built with:** Node.js, Supabase, Vercel, iOS Shortcuts, macOS LaunchAgents, Claude Code

**License:** MIT (or your preferred license)

**Version:** 1.0.0

**Last Updated:** 2025-11-16
