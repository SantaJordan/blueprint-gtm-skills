# Blueprint Turbo

**Speed-optimized GTM intelligence system - complete Blueprint execution in 13-17 minutes with automatic GitHub Pages publishing.**

## Quick Start

```bash
/blueprint-turbo https://owner.com
```

That's it. Wait 13-17 minutes and receive:
- ✅ Complete HTML playbook with 2 PQS + 2 PVP messages
- ✅ Instant shareable GitHub Pages URL
- ✅ Calculation worksheets for every data claim
- ✅ Buyer-validated scores (≥7.0/10 for Strong PQS, ≥8.5/10 for TRUE PVPs)
- ✅ Ready to send to prospects immediately

## Output Example

```
✅ Wave 4/4: HTML playbook published!

📎 Shareable URL:
   https://santajordan.github.io/blueprint-gtm-playbooks/blueprint-gtm-playbook-owner.html

💾 Local file: blueprint-gtm-playbook-owner.html

Note: GitHub Pages may take 1-2 minutes to build. If URL doesn't work immediately, wait a moment and refresh.
```

**What you get:**
- Company-specific pain segments backed by real data
- Hyper-specific outreach messages with calculation worksheets
- Data source citations (government databases, competitive intelligence, velocity signals)
- Before/after comparison showing transformation from generic outreach
- **Automatic GitHub publishing** - No manual upload needed!

## Prerequisites

**Required MCP Servers:**
- [Browser MCP](https://github.com/modelcontextprotocol/servers/tree/main/src/browser) - For parallel web research
- [Sequential Thinking MCP](https://github.com/sequentialthinking/mcp-server) - For segment hypothesis generation

**Setup Instructions:** See [MCP_SETUP.md](./MCP_SETUP.md) for installation steps.

**Without MCP Servers:**
- Browser MCP → Falls back to sequential WebFetch (slower, still functional)
- Sequential Thinking MCP → Cannot proceed (required for synthesis)

## When to Use Blueprint Turbo vs. Original Skills

| Factor | Blueprint Turbo | Original Blueprint Skills |
|--------|----------------|---------------------------|
| **Speed** | 13-17 minutes | 30-45 minutes |
| **Use Case** | Sales calls, fast turnaround | Strategic analysis, thoroughness |
| **Execution** | Single command | Multi-stage manual invocation |
| **Parallelization** | 4 waves with 15-20 parallel calls | Sequential execution |
| **Quality** | Same (buyer-validated ≥7.0/10) | Same (buyer-validated ≥7.0/10) |
| **Output** | HTML playbook + GitHub Pages URL | HTML playbook (local file) |
| **Auto-Publish** | ✅ Yes (automatic) | ❌ No (manual script) |

**Rule of Thumb:**
- Need it fast (during sales call)? → Blueprint Turbo
- Want maximum thoroughness? → Original Blueprint skills (`/blueprint-gtm-complete`)

## How It Works

### 4-Wave Parallel Architecture

**Wave 1 (0-4 min): Company Intelligence**
- 15-20 parallel WebFetch/WebSearch calls
- Company offering, ICP, personas, value prop extraction
- Market positioning and competitor analysis

**Wave 2 (4-9 min): Multi-Modal Data Discovery**
- 15-20 parallel searches across 4 categories:
  - Government/Regulatory (EPA, OSHA, CMS, FDA, state boards)
  - Competitive Intelligence (pricing, tech stack, reviews)
  - Velocity Signals (review growth, traffic, hiring)
  - Tech/Operational (integrations, compliance badges)
- Outputs Data Availability Report with feasibility ratings

**Synthesis (9-11 min): Segment Generation**
- Sequential Thinking MCP generates 2-3 pain segment hypotheses
- Uses AVAILABLE data sources from Wave 2 (not assumptions)
- Validates with Texada Test (hyper-specific, factually grounded, non-obvious)

**Wave 3 (11-14 min): Message Generation + Critique**
- Generate 2 PQS + 2 PVP messages per segment (8 total)
- Calculation worksheets for every data claim
- Buyer critique with persona adoption (5 criteria × 0-10 scoring)
- Texada Test validation
- Keep only ≥8.0/10 messages (top 2 PQS + 2 PVP)

**Wave 4 (14-15 min): HTML Playbook Assembly**
- Populate Blueprint-branded template
- Include calculation worksheets and data sources
- Mobile-responsive, self-contained HTML
- Ready to send immediately

## Data Confidence Tiers

Blueprint Turbo supports 3 tiers of data approaches:

### Tier 1: Pure Government Data (90-95% Confidence)
- **Best for:** Regulated industries (healthcare, manufacturing, environment)
- **Examples:** EPA violations, OSHA citations, CMS quality ratings
- **Message style:** Direct statements with record numbers
- **Example:** "Your facility received EPA violation #987654321 on March 15, 2025..."

### Tier 2: Hybrid Approaches (60-75% Confidence)
- **Best for:** Private business pain (pricing, competition, efficiency)
- **Examples:** Menu pricing arbitrage + review velocity, tech stack + traffic
- **Message style:** Hedged language ("estimated," "tracked," "based on")
- **Example:** "I tracked your menu pricing... costing you an estimated $4,200/month..."

### Tier 3: Pure Competitive/Velocity (50-70% Confidence)
- **Best for:** Industries with zero regulatory footprint
- **Examples:** SaaS pricing comparison, app store rating velocity
- **Message style:** Heavy hedging with transparent methodology
- **Use sparingly:** Only when Tier 1 and 2 are impossible

**Decision:** Blueprint Turbo automatically selects the highest confidence tier available based on discovered data sources.

## Example Outputs

See [examples/](./examples/) directory for sample playbooks:

- **[example-playbook-owner-com.html](./examples/example-playbook-owner-com.html)** - Restaurant tech company (Tier 2 hybrid: pricing + velocity)
- **[example-playbook-healthcare.html](./examples/example-playbook-healthcare.html)** - Healthcare provider (Tier 1: pure government data)

## Key Files

| File | Purpose |
|------|---------|
| [SKILL.md](./SKILL.md) | Full documentation (architecture, troubleshooting, use cases) |
| [MCP_SETUP.md](./MCP_SETUP.md) | MCP server installation and configuration |
| [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) | Debugging guide with real error examples |
| [prompts/methodology.md](./prompts/methodology.md) | Buyer critique rubric, message formats, Texada Test |
| [prompts/calculation-worksheets.md](./prompts/calculation-worksheets.md) | Calculation worksheet templates and examples |
| [prompts/data-discovery-queries.md](./prompts/data-discovery-queries.md) | 20 search query templates for Wave 2 |
| [references/common-databases.md](./references/common-databases.md) | Industry database catalog with field names |

## Troubleshooting Quick Reference

**"Sequential Thinking MCP not found"**
- Install: See [MCP_SETUP.md](./MCP_SETUP.md#sequential-thinking-mcp)
- **Critical:** Blueprint Turbo cannot run without this

**"Zero HIGH feasibility segments"**
- Fallback 1: Uses MEDIUM segments with disclosed confidence
- Fallback 2: Returns to synthesis, generates 2 more segments (+3 min)
- Fallback 3: Widens to adjacent industries

**"All messages score <8.0"**
- Generates 2 additional variants per segment (+2 min)
- If still failing, lowers threshold to 7.5 with disclaimer
- Hard limit: Never ships <7.0 messages

**Full guide:** See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

## Performance

- **Execution time:** 12-15 minutes (vs. 30-45 for original)
- **Speed improvement:** 60-70% faster
- **Quality:** Same buyer validation standards (≥8.0/10)
- **Parallelization:** 15-20 concurrent calls per wave
- **Benchmarks:** See [BENCHMARKS.md](./BENCHMARKS.md)

## Version

**Current:** v1.0.0 (November 2025)

See [CHANGELOG.md](./CHANGELOG.md) for version history.

## Credits

**Methodology:** Jordan Crawford, Blueprint GTM
**Philosophy:** "The message isn't the problem. The LIST is the message."

## Related Skills

Blueprint Turbo is part of the Blueprint GTM family:

- **blueprint-company-research** - Stage 1: Company intelligence
- **blueprint-data-research** - Stage 2: Database validation
- **blueprint-message-generation** - Stage 3: Message creation + critique
- **blueprint-explainer-builder** - Stage 4: HTML generation
- **blueprint-gtm-complete** - Original all-in-one execution (30-45 min)

**These are NOT deprecated.** Use original skills for maximum thoroughness when time permits.