# Blueprint GTM Skills System v1.1.0

Transform company URLs into data-driven GTM intelligence and mobile-responsive HTML playbooks using hard government data sources (EPA ECHO, OSHA, FDA, FMCSA).

**Built for consultants. Powered by Claude Code.**

## 📦 Repository Setup

This repository uses **dual remotes** for different purposes:

- **`origin`** (private): https://github.com/SantaJordan/blueprint-gtm-skills.git
  - Your main development repository
  - Push all code changes here: `git push origin main`

- **`publish`** (public): https://github.com/SantaJordan/blueprint-gtm-playbooks.git
  - GitHub Pages for published artifacts
  - Used by `publish-playbook.sh` to publish HTML playbooks

**Note:** The repository excludes large data files (5GB+ of databases, downloads, exports). After cloning, run setup scripts to regenerate local data. See project READMEs for details.

---

## Repository Structure

This repo contains **4 main systems**:

### 1. Blueprint GTM Skills (Local Execution)
- **`.claude/skills/`** - 8 Claude Code skills for GTM intelligence
- **`.claude/commands/`** - Slash commands (`/blueprint-turbo`)
- Run locally: `/blueprint-turbo https://company.com`

### 2. Blueprint Cloud Workers (Online Execution)
- **`agent-sdk-worker/`** - Node.js worker using Claude Agent SDK (Modal)
- **`blueprint-trigger-api/`** - Vercel API for mobile job queue
- **`blueprint-saas/`** - Next.js dashboard with Stripe payments

### 3. Contact Finder (SMB Discovery)
- **`contact-finder/`** - Find decision-makers at small businesses
- **`evaluation/`** - Testing framework for contact-finder
- **`domain-resolver/`** - Company name → domain resolution

### 4. Documentation
- **`docs/`** - Runbooks, distribution guides, templates
- **`CLAUDE.md`** - Quick reference for Claude Code

---

## What This System Does

**Input:** Company website URL
**Output:** Mobile-responsive HTML playbook with validated PQS/PVP messages backed by government database record numbers

### Two Workflow Options

#### 🚀 Blueprint Turbo (Recommended for Speed)
**13-17 minutes** | Single command | Parallel execution | Auto-publishes to GitHub Pages
```bash
/blueprint-turbo https://company.com
```
**Outputs:** HTML playbook + Instant shareable GitHub Pages URL

#### 🔬 Original Blueprint Skills (Maximum Thoroughness)
**30-45 minutes** | Multi-stage | Sequential deep-dive
```bash
"Run Blueprint GTM analysis for https://company.com"
```

**Both produce the same quality output:** Buyer-validated messages scoring 8.5+/10 for TRUE PVPs or 7.0+/10 for Strong PQS.

---

## Quick Start (5 Minutes)

### Step 1: Open This Directory in Claude Code

```bash
cd "/Users/jordancrawford/Desktop/Claude Skills"
```

### Step 2: Choose Your Workflow

**For Fast Turnaround (Sales Calls):**
```
/blueprint-turbo https://company.com
```

**For Maximum Thoroughness:**
```
"Run Blueprint GTM analysis for https://company.com"
```

### Step 3: Receive Your Deliverable

**Blueprint Turbo automatically outputs:**
1. **Shareable GitHub Pages URL:** `https://[username].github.io/blueprint-gtm-playbooks/blueprint-gtm-playbook-[company-name].html`
2. **Local HTML file:** `blueprint-gtm-playbook-[company-name].html`

**Playbook features:**
- Self-contained (inline CSS, no dependencies)
- Mobile-responsive
- Instantly shareable via URL (no manual upload needed)
- Professional Blueprint branding
- Version controlled in git

---

## The 4-Stage Blueprint Methodology

### Stage 1: Company Research (~5-10 min)
- Visits live website
- Researches ICP and personas
- Develops 3-5 pain segment hypotheses
- Emphasizes hard data opportunities

### Stage 2: Data Research (~10-15 min)
- Actively searches for government databases
- Verifies EPA ECHO, OSHA, FDA, FMCSA, permit databases
- Documents actual field names by visiting APIs/portals
- Rates segment feasibility (HIGH/MEDIUM/LOW)
- Suggests alternatives if segments aren't detectable

### Stage 3: Message Generation (~15-20 min)
- Takes HIGH feasibility segments only
- Generates 3-5 variants per message type (PQS and PVP)
- Brutally critiques as buyer (destroy 60-70%)
- Validates all claims against government database fields
- Outputs only messages scoring **≥ 8.5/10 for TRUE PVPs** or **≥ 7.0/10 for Strong PQS**

### Stage 4: Explainer Builder (~5 min)
- Creates mobile-responsive HTML document
- Includes "Old Way" vs "New Way" comparison
- Shows top PQS and PVP play cards
- Complete with data sources and implementation notes

**Automatic Chaining:** Claude recognizes when each stage completes and automatically invokes the next skill.

---

## v1.1.0 Updates: PVP vs Strong PQS Classification

### What Changed

**Previous (v1.0.0):**
- All messages scoring 8.0+/10 were called "PVPs"

**Current (v1.1.0):**
- **TRUE PVP**: 8.5+/10 - Complete actionable information (names, contacts, prices, dates)
- **Strong PQS**: 7.0-8.4/10 - Excellent pain identification, but incomplete action info
- **Independently Useful Test**: Gatekeeper test - Can recipient take action WITHOUT replying?

### Why This Matters

Most excellent messages are **Strong PQS**, not TRUE PVPs. This is success!

**TRUE PVP Example (8.5+/10):**
> "Your Torrance facility (CA License #PR-8675309) has Sarah Chen listed as Quality Manager, but her LinkedIn shows she left in March 2025. I noticed Jenny Martinez now handles quality calls. Should I update our records to route future quality alerts to Jenny instead of Sarah?"

✅ Complete info: Facility ID, person names, dates, role change
✅ Independently useful: Recipient can update records without replying

**Strong PQS Example (7.5/10):**
> "Your Torrance facility received FDA Form 483 observation #2025-LAX-1247 on March 15, 2025 for temperature monitoring gaps in cold storage. I track 47 similar FDA observations where facilities added automated IoT sensors. What's your current temperature monitoring approach?"

✅ Excellent pain identification: Specific violation, record number, date
❌ Not independently useful: Requires reply to be valuable

### Realistic Expectations

- **Most segments generate Strong PQS (7.0-8.4)** - celebrate this as success
- **TRUE PVPs (8.5+) are rare** - require specific data (contact names, prices, agent details)
- **Both are valuable** - Strong PQS starts conversations, TRUE PVPs deliver standalone value

---

## Core Philosophy: Hard Data Only

### ✅ What We Use (Hard Signals)

**Government Enforcement Databases:**
- EPA ECHO (environmental violations with facility IDs)
- OSHA Establishment Search (safety citations with case numbers)
- FDA Warning Letters, Form 483s (inspection observations)
- FMCSA SAFER (trucking violations, safety ratings)
- State licensing databases (disciplinary actions, renewals)
- Building permit databases (project values, contractors)
- Court records (consent decrees, enforcement actions)

**Competitive Intelligence (Tier 2):**
- Menu pricing arbitrage + review velocity
- Tech stack + traffic patterns
- Pricing comparison with methodology disclosed

**Why:** Timestamped violations with record numbers enable messages like:
> "Your facility at 1234 Industrial Pkwy received EPA violation #2024-XYZ on March 15, 2025..."

### ❌ What We Avoid (Soft Signals)

- Job postings (everyone hires, too generic)
- M&A announcements (no specific pain indicated)
- Funding rounds (thousands qualify, no urgency)
- Tech stack changes alone (speculative, hard to verify)
- Generic industry trends (applies to everyone)

**Why:** Soft signals produce generic messages like:
> "I see you're hiring compliance people..."

**The Difference:** Hard data is verifiable, specific, and enables consulting-level intelligence delivery.

---

## System Architecture

### Directory Structure (Updated Nov 2025)

```
Claude Skills/
├── README.md (this file)
├── docs/
│   ├── DISTRIBUTION_GUIDE.md
│   ├── LICENSE_TERMS.md
│   └── CUSTOMER_README_TEMPLATE.md
├── examples/
│   └── wingwork/
│       └── final-playbook.html
├── archive/
│   └── pre-nov-2025-cleanup.zip
└── .claude/skills/
    ├── blueprint-turbo/              [v1.1.0] ⚡ Fast workflow (12-15 min)
    │   ├── SKILL.md
    │   ├── README.md
    │   ├── docs/
    │   │   ├── MCP_SETUP.md
    │   │   ├── TROUBLESHOOTING.md
    │   │   ├── BENCHMARKS.md
    │   │   ├── CHANGELOG.md
    │   │   └── READINESS_CHECKLIST.md
    │   ├── archive/
    │   │   ├── UPDATES_2025-11-10.md
    │   │   └── WINGWORK_TEST_RESULTS_2025-01-10.md
    │   ├── prompts/
    │   │   ├── methodology.md         [v1.1.0 - PVP vs PQS definitions]
    │   │   ├── calculation-worksheets.md
    │   │   ├── data-discovery-queries.md
    │   │   └── explainer-template.md
    │   ├── references/
    │   │   └── common-databases.md
    │   ├── templates/
    │   │   └── playbook-html-template.html
    │   └── examples/
    │       └── [example playbooks]
    │
    ├── blueprint-company-research/    [v1.1.0] Stage 1
    │   ├── SKILL.md
    │   └── references/
    │       ├── methodology.md         [v1.1.0 - copied from turbo]
    │       ├── PAIN_SEGMENTS_REFERENCE.md
    │       └── ICP_FRAMEWORK.md
    │
    ├── blueprint-data-research/       [v1.1.0] Stage 2
    │   ├── SKILL.md
    │   └── references/
    │       ├── methodology.md         [v1.1.0 - copied from turbo]
    │       ├── FIELD_LEVEL_TEMPLATE.md
    │       └── TEXADA_STANDARD.md
    │
    ├── blueprint-message-generation/  [v1.1.0] Stage 3
    │   ├── SKILL.md
    │   └── references/
    │       ├── methodology.md         [v1.1.0 - copied from turbo]
    │       ├── TEXADA_TEST.md
    │       ├── MESSAGE_PRINCIPLES.md
    │       └── BUYER_CRITIQUE_FRAMEWORK.md
    │
    ├── blueprint-explainer-builder/   [v1.1.0] Stage 4
    │   ├── SKILL.md
    │   └── references/
    │       ├── methodology.md         [v1.1.0 - copied from turbo]
    │       ├── EXPLAINER_TEMPLATE.md
    │       └── DESIGN_SYSTEM.md
    │
    └── blueprint-gtm-complete/        [v1.1.0] Original all-in-one
        ├── SKILL.md
        └── references/
            └── methodology.md         [v1.1.0 - copied from turbo]
```

---

## Blueprint Turbo vs Original Skills: When to Use Each

| Factor | Blueprint Turbo | Original Blueprint Skills |
|--------|----------------|---------------------------|
| **Speed** | 13-17 minutes | 30-45 minutes |
| **Use Case** | Sales calls, fast turnaround | Strategic analysis, thoroughness |
| **Execution** | `/blueprint-turbo URL` | Auto-chains through 4 stages |
| **Parallelization** | 4 waves with 15-20 parallel calls | Sequential execution |
| **Quality** | Same (buyer-validated) | Same (buyer-validated) |
| **MCP Required** | Browser + Sequential Thinking | None (uses WebFetch) |
| **Output** | HTML playbook + GitHub Pages URL | HTML playbook (local file) |
| **Auto-Publish** | ✅ Yes (automatic) | ❌ No (manual script) |

**Rule of Thumb:**
- Need it fast (during sales call)? → **Blueprint Turbo**
- Want maximum thoroughness? → **Original Blueprint skills**
- Don't have MCP servers set up? → **Original Blueprint skills**

---

## Data Confidence Tiers

### Tier 1: Pure Government Data (90-95% Confidence)
- **Best for:** Regulated industries (healthcare, manufacturing, environment)
- **Examples:** EPA violations, OSHA citations, CMS quality ratings
- **Message style:** Direct statements with record numbers

### Tier 2: Hybrid Approaches (60-75% Confidence)
- **Best for:** Private business pain (pricing, competition, efficiency)
- **Examples:** Menu pricing arbitrage + review velocity
- **Message style:** Hedged language ("estimated," "tracked," "based on")

### Tier 3: Pure Competitive/Velocity (50-70% Confidence)
- **Best for:** Industries with zero regulatory footprint
- **Examples:** SaaS pricing comparison, app store rating velocity
- **Use sparingly:** Only when Tier 1 and 2 are impossible

**Decision:** System automatically selects the highest confidence tier available based on discovered data sources.

---

## Quality Standards

### Company Research
**Good Output:**
- 3-5 specific pain segments with trigger events
- Each segment has initial data hypothesis (government databases)
- Persona deeply profiled (expertise level, what they already know)
- No generic pain points ("needs to save time")

**Red Flags:**
- Segments without specific triggers
- Data hypotheses mention job postings or M&A
- Pain points could apply to anyone

### Data Research
**Good Output:**
- Each segment has specific government database identified (with URL)
- ACTUAL field names documented (not assumed)
- Feasibility ratings with clear rationale
- HIGH feasibility segments ready for message generation

**Red Flags:**
- Generic "there's probably data" without verification
- No specific database URLs or field names
- All segments rated HIGH without critical evaluation

### Message Generation (v1.1.0)
**Good Output:**
- TRUE PVPs score ≥ 8.5/10 (complete actionable info)
- Strong PQS score 7.0-8.4/10 (excellent pain identification)
- Every claim verified against database fields (✅ Provable)
- Messages use actual record numbers, dates, violation IDs
- 60-70% of drafts destroyed for quality

**Red Flags:**
- Messages scoring < 7.0 included in final selection
- Generic data claims without record numbers
- Obvious insights that experts already know
- High-effort questions or meeting requests

### Explainer Document
**Good Output:**
- Mobile-responsive HTML (no external dependencies)
- Messages display without mid-sentence line breaks
- Data sources clearly identified
- "Old Way" email is realistic and bad
- File size under 2MB

**Red Flags:**
- External CSS/JS dependencies
- Messages with line breaks within sentences
- Missing "why this works" explanations

---

## Usage Patterns

### Pattern 1: Fast Turnaround (Turbo)
```
/blueprint-turbo https://company.com
```
**Timeline:** 12-15 minutes for complete playbook

### Pattern 2: Standard Full Analysis (Original)
```
"Run Blueprint GTM analysis for https://company.com"
```
**Timeline:** 30-45 minutes, auto-chains through 4 stages

### Pattern 3: Stop After Research
```
"Research company and data sources for https://company.com but don't generate messages yet"
```
Claude stops after data research for review before proceeding.

### Pattern 4: Resume From Checkpoint
```
"I have company research and data research completed. Generate messages for the HIGH feasibility segments."
```
Claude invokes message-generation skill directly.

---

## Troubleshooting

### Issue: "No HIGH feasibility segments found"
**Cause:** Pain segments aren't detectable with hard government data

**Solution:**
1. Review alternative segments suggested by data research
2. Return to company research with new hypotheses
3. Focus on industries with strong regulatory oversight

### Issue: "Messages scoring below 7.0"
**Cause:** Data isn't specific enough or insights are obvious

**Solution:**
1. Check if claims use actual record numbers and dates
2. Verify insights are non-obvious
3. Ensure questions are easy to answer
4. Confirm no meeting requests or solution pitches

### Issue: "Soft signals appearing in messages"
**Cause:** Falling back to job postings, M&A when hard data is difficult

**Solution:**
1. Be ruthless in data research - push harder for government databases
2. Destroy any message mentioning hiring, funding, growth indicators
3. If no hard data exists, pivot segments
4. Better to have 1 strong message than 5 weak ones

### Issue: "HTML not mobile-responsive"
**Cause:** Line breaks within sentences or missing viewport meta tag

**Solution:**
1. Remove all line breaks within sentences
2. Verify viewport meta tag present
3. Test on actual mobile device or browser dev tools

**For Blueprint Turbo specific issues:** See `.claude/skills/blueprint-turbo/docs/TROUBLESHOOTING.md`

---

## Examples

### Real-World Example: Wingwork
**Located in:** `examples/wingwork/final-playbook.html`

**Demonstrates:**
- Complete HTML playbook output
- PQS and PVP messages with calculation worksheets
- Data source citations
- Mobile-responsive design
- Blueprint branding

**View it:** Open the HTML file in any browser to see the final deliverable format.

---

## For Consultants

### When to Use This System

**✅ Good Use Cases:**
- Company sells into regulated industries (manufacturing, healthcare, food, transportation, construction)
- Target customers face compliance, safety, or environmental requirements
- Pain segments can be detected through government enforcement actions
- Client wants data-driven outreach, not generic personalization

**❌ Poor Use Cases:**
- Pure software/SaaS companies with no regulatory oversight
- Consumer products without regulatory angle
- Generic "efficiency" solutions without measurable triggers
- Industries with minimal government data availability

### Training New Consultants

1. **Start with Blueprint Turbo** - fastest way to see the full workflow
2. **Try a manufacturing company** - EPA ECHO + OSHA provide rich data
3. **Attempt a healthcare provider** - CMS, Joint Commission, state health departments
4. **Test a transportation company** - FMCSA SAFER database
5. **Then use Original Skills** - for deeper understanding of each stage

**Key Lessons:**
- Not every segment is detectable
- Hard data beats clever copy every time
- Buyer role-play validation is brutally honest
- Most messages are Strong PQS (7.0-8.4), not TRUE PVPs (8.5+) - this is success!

### Customization

**To modify for your use case:**
1. Add industry-specific databases to references
2. Adjust buyer critique scoring in methodology
3. Customize HTML branding in explainer templates
4. Add your examples to examples directory

**Keep core principles:**
- Hard data emphasis
- Active discovery via web search
- Buyer validation required
- Realistic PVP vs Strong PQS classification

---

## Setup Requirements

### For Original Blueprint Skills
- **Required:** Claude Code
- **No MCP servers needed**
- **Internet access** for WebFetch and WebSearch

### For Blueprint Turbo
- **Required:** Claude Code
- **Required MCP Servers:**
  - Browser MCP (parallel web research)
  - Sequential Thinking MCP (segment synthesis)
- **Setup Guide:** `.claude/skills/blueprint-turbo/docs/MCP_SETUP.md`

---

## Version History

### v1.1.0 (November 2025)
**Major Update: PVP vs Strong PQS Classification**

**Key Changes:**
1. **TRUE PVP threshold**: 8.0+ → 8.5+ (requires complete actionable info)
2. **Strong PQS range**: 7.0-8.4 (excellent pain identification)
3. **Independently Useful Test**: Added as gatekeeper for TRUE PVPs
4. **Action Extraction Phase**: New validation phase before buyer critique
5. **Realistic expectations**: Most segments generate Strong PQS (success!)
6. **Texada Test**: Updated with TRUE PVP examples (Floorzap, Skimmer)
7. **Documentation**: methodology.md copied to all 5 skills
8. **Directory reorganization**: Created docs/ folders, cleaned up structure

**All skills updated:** turbo, company-research, data-research, message-generation, explainer-builder, gtm-complete

### v1.0.0 (October 2025)
- Initial release with 4-stage workflow
- Blueprint Turbo parallel architecture
- Hard data emphasis throughout
- Buyer critique validation

---

## Support & Resources

**Full Documentation:**
- Blueprint Turbo: `.claude/skills/blueprint-turbo/README.md`
- Methodology Reference: `.claude/skills/blueprint-turbo/prompts/methodology.md` (v1.1.0)
- Troubleshooting: `.claude/skills/blueprint-turbo/docs/TROUBLESHOOTING.md`
- MCP Setup: `.claude/skills/blueprint-turbo/docs/MCP_SETUP.md`

**Philosophy:** This system embodies Jordan Crawford's Blueprint GTM methodology:

> "The message isn't the problem. The LIST is the message."

---

## Sharing Playbooks via GitHub Pages

### ✨ Automatic Publishing (Default for Blueprint Turbo)

**Blueprint Turbo now automatically publishes to GitHub Pages!**

When you run `/blueprint-turbo https://company.com`, it will:
1. Generate the HTML playbook
2. Automatically commit and push to GitHub
3. Output the shareable GitHub Pages URL instantly

**No manual steps needed** - just run turbo and get your URL.

### Quick Setup (One-Time - Required for Auto-Publishing)

1. **Create GitHub Repository:**
   ```bash
   # Initialize git (if not already done)
   git init

   # Create public GitHub repo
   gh repo create blueprint-gtm-playbooks --public --source=. --remote=origin
   ```

2. **Enable GitHub Pages:**
   - Go to repository Settings → Pages
   - Set source to: `main` branch, `/ (root)` directory
   - Save changes
   - Your playbooks will be accessible at: `https://[username].github.io/blueprint-gtm-playbooks/[filename].html`

**That's it!** All future `/blueprint-turbo` runs will auto-publish.

### Manual Publishing (Fallback Method)

If you need to manually publish an existing playbook or if auto-publishing fails:

```bash
./publish-playbook.sh blueprint-gtm-playbook-[company-name].html
```

This script will:
1. Add the HTML file to git
2. Commit with timestamp
3. Push to GitHub
4. Output the shareable URL

**Example:**
```
✅ Published: https://[username].github.io/blueprint-gtm-playbooks/blueprint-gtm-playbook-mirrorweb.html
```

### Benefits

- **Instant shareable URLs** - No manual upload needed
- **Version history** - All playbooks tracked in git
- **Free hosting** - GitHub Pages is free for public repos
- **Professional URLs** - Clean, permanent links
- **No dependencies** - Works with self-contained HTML files

---

## Cloud / Mobile Trigger System

### Overview

There are two supported entrypoints:

1. **Mobile trigger (consultant / local execution):** iOS Shortcut → Vercel Trigger API → Supabase queue → local Mac worker (`scripts/blueprint-worker.js`) → GitHub Pages URL.
2. **Paid SaaS (fully cloud, recommended):** `blueprint-saas` (Stripe checkout) → Stripe webhook inserts job in Supabase → Modal Agent SDK Worker → Vercel Playbooks hosting (`playbooks.blueprintgtm.com`) → optional payment capture.

### Architecture

**Mobile trigger (local worker):**
```
iPhone → Vercel Trigger API → Supabase → Local Mac Worker → GitHub Pages
                                            ↓
                                     Claude Code CLI
```

**Paid SaaS (cloud worker):**
```
User → blueprint-saas (Stripe) → Supabase → Modal Agent SDK Worker → Vercel Playbooks
                                               ↓
                                    Blueprint Turbo orchestrator
```

### Components

| Component | Location | Purpose |
|-----------|----------|---------|
| **Vercel Trigger API** | `blueprint-trigger-api/` | Receives URL from iOS, queues job |
| **Local Mac Worker** | `scripts/` | Polls Supabase and runs local Claude Code |
| **SaaS Dashboard** | `blueprint-saas/` | Stripe checkout + status UI |
| **Agent SDK Worker** | `agent-sdk-worker/` | Cloud worker that runs the Blueprint Turbo orchestrator and publishes to Vercel Playbooks |

### Agent SDK Worker (Recommended for Cloud)

The Agent SDK Worker provides **90-95% quality parity** with local `/blueprint-turbo` by:
- Loading `.claude/skills/` as the single source of truth
- Using Sequential Thinking MCP for synthesis
- Executing the Blueprint Turbo orchestrator from `.claude/commands/blueprint-turbo.md` (embedded prompt with `$ARGUMENTS` substituted)
- Publishing HTML to Vercel (`playbooks.blueprintgtm.com`)
- Capturing Stripe payments after successful delivery (when jobs were created via SaaS)

**Documentation:**
- [README](agent-sdk-worker/README.md) - Quick start guide
- [Runbook](docs/AGENT_SDK_RUNBOOK.md) - Operations guide
- [Migration Notes](docs/AGENT_SDK_MIGRATION_NOTES.md) - Architecture decisions

### Quick Start

```bash
# Deploy Agent SDK Worker to Modal
cd agent-sdk-worker
npm install
modal deploy modal/wrapper.py
```

Then configure the Supabase webhook to point to the new Modal endpoint.

---

## Next Steps

1. **Choose your workflow:**
   - Fast: `/blueprint-turbo https://company.com`
   - Thorough: `"Run Blueprint GTM analysis for https://company.com"`

2. **Review the HTML playbook** delivered

3. **Publish to GitHub Pages** for shareable URL (optional)

4. **Iterate** on segments or messages as needed

5. **Deploy** the best messages with confidence

**Remember:** The goal isn't perfection on first run. The goal is intelligence-driven targeting with verifiable hard data. Sometimes that means pivoting segments. Sometimes that means acknowledging data limitations. Always it means being honest about what's provable vs. what's inferred.

Most importantly: **Celebrate Strong PQS (7.0-8.4) as success.** TRUE PVPs (8.5+) are rare and require specific data (contact names, prices, agent details). Both are valuable.

---

**That's Blueprint GTM v1.1.0.**
