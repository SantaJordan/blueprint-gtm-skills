# Agent SDK Migration Notes

**Document Version:** 1.0
**Created:** 2025-12-08
**Status:** Phase 0 - Discovery Complete

---

## 1. How the System Works Today

### The Local Flow (`/blueprint-turbo` inside Claude Code)

When you run `/blueprint-turbo https://company.com` locally in Claude Code:

```
User types: /blueprint-turbo https://owner.com
    ↓
Claude Code CLI loads:
  - .claude/commands/blueprint-turbo.md (61KB orchestrator)
  - .claude/settings.json (hooks, allowed tools)
  - .claude/settings.local.json (pre-approved permissions)
  - CLAUDE.md (project instructions)
    ↓
Wave 0.5: Product Value Analysis
  - Loads: modules/product-fit-triage.md
  - Anchors all work on actual product capabilities
    ↓
Wave 1: Explosive Intelligence Gathering (0-4 min)
  - 15-20 PARALLEL calls (Browser MCP or WebFetch)
  - 4-5 company website pages
  - 6-8 market research searches
  - Output: Company context, ICP, persona
    ↓
Wave 1.5: Niche Conversion (automatic)
  - Loads: modules/vertical-qualification.md
  - Converts generic verticals → regulated niches
  - Hard gate: Product-Solution Alignment ≥ 5/10
    ↓
Wave 2: Data Landscape Scan (4-9 min)
  - 15-20 PARALLEL searches across 4 categories
  - Government/regulatory, competitive intel, velocity signals, tech/operational
  - Output: Data Availability Report with feasibility ratings
    ↓
Synthesis: Sequential Thinking MCP (9-11 min)
  - Invokes: mcp__sequential-thinking__sequentialthinking
  - Generates 2-3 pain segment hypotheses
  - Uses ACTUAL data fields from Wave 2
    ↓
Hard Gate Validation (1-2 min)
  - Invokes: Skill(blueprint-validator)
  - 5 mandatory gates (product-pain alignment, anti-patterns, data detectability, specificity, completeness)
    ↓
Wave 3: Message Generation (11-14 min)
  - 2 PQS + 2 PVP messages per segment
  - Calculation worksheets (show math)
  - Buyer critique (cynical persona, 7 criteria)
  - Keep only messages scoring ≥8.0/10
    ↓
Wave 4: HTML Assembly (14-15 min)
  - Loads: templates/html-template.html
  - Self-contained, mobile-responsive HTML
    ↓
Wave 4.5: GitHub Pages Publishing (15-16 min)
  - git add, commit, push to publish remote
  - Generate shareable URL
    ↓
OUTPUT:
  - Local file: blueprint-gtm-playbook-owner.html
  - Shareable URL: https://santajordan.github.io/blueprint-gtm-playbooks/...
```

**Key characteristics:**
- **Total time:** 12-15 minutes
- **Parallelization:** 15-20 concurrent web calls per wave
- **MCP dependencies:** Sequential Thinking (REQUIRED), Browser MCP (optional, +5-10 min without)
- **Quality:** Rigorous 5-gate validation, buyer critique, 8.0+ score threshold
- **Output:** Self-contained HTML playbook + GitHub Pages URL

### The Phone Trigger Flow (iPhone → Vercel → Supabase → Modal)

```
iPhone Safari → Share Sheet → "Analyze with Blueprint" Shortcut
    ↓
iOS Shortcut POSTs to: https://blueprint-trigger-api.vercel.app/api/queue-job
  Body: {"companyUrl": "https://owner.com"}
    ↓
Vercel API (blueprint-trigger-api/api/queue-job.js)
  - Validates URL
  - Inserts into Supabase: blueprint_jobs table, status='pending'
  - Returns: {id, statusUrl}
    ↓
Supabase Webhook (on INSERT)
  - Triggers Modal endpoint immediately
    ↓
Modal Worker (blueprint-worker/main.py)
  - Pulls job from webhook payload
  - Updates status → 'processing'
  - Executes 10-wave Python pipeline:
      Wave 1: wave1_company_research.py
      Wave 0.5: wave05_product_fit.py
      Wave 1.5: wave15_niche_conversion.py
      Wave 2: wave2_data_landscape.py
      Wave 2.5: wave25_situation_fallback.py (conditional)
      Synthesis: synthesis.py
      Hard Gates: hard_gates.py
      Wave 3: wave3_messages.py
      Wave 4: wave4_html.py
      Wave 4.5: wave45_publish.py
  - Updates Supabase: status='completed', playbook_url='...'
    ↓
GitHub Pages
  - HTML playbook published
  - User checks status page → gets playbook URL
```

**Key characteristics:**
- **Total time:** ~15-20 minutes (varies)
- **Execution:** Sequential Python code calling Anthropic API
- **No MCP servers:** Sequential Thinking is replicated as a prompt template
- **No Claude Code tools:** No Read, Write, Edit, Bash—just API responses
- **No skill access:** References are Python dicts, not the rich .claude/skills/ library

---

## 2. Where the Current Cloud Approach Sucks

### Root Cause Analysis

The Modal worker is a **complete reimplementation** of Blueprint Turbo in Python. It doesn't use Claude Code or the Agent SDK—it calls the Anthropic API directly with custom prompts for each wave.

This explains the quality gap:

| Factor | Local (Claude Code) | Cloud (Modal Worker) | Impact |
|--------|---------------------|----------------------|--------|
| **Tool Loop** | Claude's autonomous tool loop with Read/Write/Edit/Bash | None - just API text responses | Claude can't explore files, run scripts, or iterate |
| **MCP Servers** | Sequential Thinking MCP, Browser MCP | Prompt-based simulation | Missing structured reasoning and parallel browsing |
| **Skill Library** | Full .claude/skills/ with 60KB+ of methodology, templates, references | Python dicts with abbreviated versions | Less guidance, missing nuance |
| **Parallelization** | 15-20 concurrent tool calls per wave | Sequential API calls (or OpenRouter dual-provider) | 2-3x slower |
| **Validation** | blueprint-validator skill with 5-gate framework | Hardcoded Python validation | Less thorough, more brittle |
| **Context Persistence** | Claude Code maintains session context | Fresh context per wave | Loses nuance between waves |
| **Publishing** | Native git operations via Bash tool | PyGitHub API calls | Works but less integrated |

### Specific Quality Issues

1. **Missing Sequential Thinking MCP**
   - Local: `mcp__sequential-thinking__sequentialthinking` enforces stepwise reasoning
   - Cloud: `sequential_thinking.py` is a prompt template—Claude doesn't actually "think step by step" with external validation

2. **No Browser MCP Parallelization**
   - Local: 15-20 concurrent browser tabs in Wave 1 and Wave 2
   - Cloud: Sequential WebSearch/WebFetch via Serper API

3. **Abbreviated Prompts**
   - Local: 60KB blueprint-turbo.md with full methodology, edge cases, examples
   - Cloud: Wave files have shorter prompts, missing nuance

4. **No Tool-Based Iteration**
   - Local: Claude can Read files, grep for patterns, Write intermediate artifacts
   - Cloud: Claude just generates text—can't verify, explore, or refine

5. **Context Loss Between Waves**
   - Local: Single Claude session maintains all context
   - Cloud: Each wave is a separate API call, context passed via Python dicts

6. **Validation Gaps**
   - Local: blueprint-validator skill with banned-patterns-registry.md, hard-gate-validator.md
   - Cloud: hard_gates.py with subset of validation rules

### Cost/Performance Tradeoffs

| Metric | Local | Cloud (Modal) |
|--------|-------|---------------|
| Execution time | 12-15 min | 15-20 min |
| Claude API cost | ~$2-3 | ~$2.50 (Opus + Sonnet mix) |
| Infrastructure cost | Free (local Mac) | ~$0.15 Modal + free tier (Supabase, Vercel) |
| Total cost per job | ~$2-3 | ~$2.65 |
| Quality score | 8.0+/10 consistently | 6-7/10 often |

---

## 3. What the Claude Agent SDK Offers

The Claude Agent SDK wraps the Claude Code CLI programmatically, providing:

### Core Capabilities

```python
from claude_agent_sdk import query, ClaudeAgentOptions

options = ClaudeAgentOptions(
    # Use Claude Code's exact system prompt
    system_prompt={"type": "preset", "preset": "claude_code"},

    # Load .claude/settings.json and CLAUDE.md
    setting_sources=["project"],

    # Enable all Claude Code tools
    tools={"type": "preset", "preset": "claude_code"},

    # Load MCP servers
    mcp_servers={
        "sequential-thinking": {"command": "npx", "args": ["@sequentialthinking/mcp-server"]},
        "browser": {"command": "npx", "args": ["@anthropic-ai/mcp-server-browser"]}
    }
)

async for message in query(
    prompt="/blueprint-turbo https://owner.com",
    options=options
):
    print(message)
```

### What This Unlocks

1. **Full Tool Access**: Read, Write, Edit, Bash, Grep, Glob, WebFetch, WebSearch—same as local
2. **MCP Server Support**: Can load Sequential Thinking MCP, Browser MCP, etc.
3. **Skill Library Access**: Can load .claude/skills/ via setting_sources
4. **Session Persistence**: Maintains context across multiple queries
5. **Hooks**: Can intercept tool execution for logging/auditing
6. **Cost Control**: max_budget_usd, max_turns limits

### Key Differences from Current Approach

| Current (Modal + API) | With Agent SDK |
|-----------------------|----------------|
| Python reimplementation | Claude Code engine directly |
| No tools | Full tool loop |
| Prompt-based thinking | MCP-based thinking |
| Sequential waves | Single autonomous session |
| Context passed manually | Context persists naturally |
| Custom validation | Skill-based validation |

---

## 4. Open Questions & Assumptions

### Questions Requiring Clarification

1. **MCP Server Portability**
   - Can Sequential Thinking MCP run headless (no browser)?
   - Answer: Yes, it's a stdio-based MCP server

2. **Modal Compatibility**
   - Can Agent SDK run on Modal (spawns Claude Code CLI as subprocess)?
   - Assumption: Should work if Claude Code is installed in Modal image

3. **Environment Variables**
   - Agent SDK requires `ANTHROPIC_API_KEY` in environment
   - Need to ensure Modal secrets are accessible

4. **Timeout Constraints**
   - Modal has 60-minute timeout
   - Blueprint Turbo typically takes 12-15 minutes—should be fine

5. **Git Authentication**
   - Agent SDK uses Bash for git operations
   - Need GitHub token configured in environment

### Assumptions Made

1. **Claude Code CLI can be installed in Modal image**
   - Will need to add `npm install -g @anthropic-ai/claude-code` to image setup

2. **MCP servers can run in Modal environment**
   - Sequential Thinking MCP is stdio-based, should work
   - Browser MCP may not work (needs Chrome)—but has WebFetch fallback

3. **Agent SDK startup overhead is acceptable**
   - ~1-2 seconds to spawn Claude Code subprocess
   - Acceptable for 12-15 minute jobs

4. **Session management not needed**
   - Each Blueprint job is independent
   - Can use query() instead of ClaudeSDKClient

---

## 5. Next Steps

Phase 1 will evaluate these options:
- **Option A**: Harden current Modal + API approach
- **Option B**: Build Agent SDK–based worker
- **Option C**: Use plain Messages API with manual tool handling
- **Option D**: Other alternatives (containerized Claude Code, gateway, etc.)

The evaluation will score each option on:
- Quality parity with local `/blueprint-turbo`
- Reliability / debuggability
- Implementation complexity
- Long-term maintainability
- Ability to reuse `.claude/skills/`

---

## 6. Options & Decision (Phase 1)

### Option Comparison Table

| Option | Quality Parity | Implementation | Maintenance | Skill Reuse | Scalability |
|--------|---------------|----------------|-------------|-------------|-------------|
| **A: Harden Modal Worker** | 70-80% | 10-15 days | HIGH (sync prompts manually) | Partial (embed prompts) | HIGH |
| **B: Agent SDK Worker** | 90-95% | 9-12 days | LOW (single source of truth) | Full (.claude/skills/) | MEDIUM |
| **C: Plain API + Tool Loop** | 70-85% | 3-4 weeks | HIGH (build everything) | None | HIGH |
| **D.1: Docker Container** | 95%+ | 2-3 weeks | MEDIUM | Full | MEDIUM |
| **D.3: Hybrid Mac/Linux** | 98%+ | 4-6 weeks | HIGH (hardware) | Full | LOW |

### Detailed Analysis

#### Option A: Harden Current Modal Worker
**What:** Improve the existing Python implementation by embedding full skill prompts, enhancing sequential thinking simulation, and implementing complete 5-gate validation.

**Pros:**
- No new dependencies
- Faster iteration
- Known cost model
- Can ship improvements incrementally

**Cons:**
- Architectural ceiling at 70-80% quality
- No true MCP server integration
- Must manually sync prompts with .claude/skills/
- Context management burden (pass context between waves)

**Verdict:** Good for quick wins, but fundamentally limited.

#### Option B: Claude Agent SDK Worker (RECOMMENDED)
**What:** Build a new worker using the Claude Agent SDK (TypeScript or Python) that wraps the Claude Code CLI and can use the exact same skills, commands, and MCP servers as local execution.

**Pros:**
- Single source of truth: loads `.claude/skills/` directly
- Native MCP support (Sequential Thinking, optionally Browser)
- Claude Code's context management and prompt caching
- Official Anthropic SDK with ongoing support
- Higher quality ceiling (90-95%)

**Cons:**
- New dependency (SDK is pre-1.0)
- Requires Node.js in Modal (subprocess or custom image)
- Browser MCP may not work in serverless (WebFetch fallback acceptable)

**Verdict:** Best balance of quality and implementation effort.

#### Option C: Plain Messages API + Manual Tool Loop
**What:** Build a custom tool execution loop that parses `tool_use` blocks and manually executes Read, Write, Bash, WebFetch, etc.

**Pros:**
- Full control over implementation
- No SDK dependency

**Cons:**
- Must reverse-engineer Claude Code's tool schemas
- No MCP server integration
- Context explosion (no automatic compaction)
- Highest implementation effort (3-4 weeks)

**Verdict:** More work for same quality as Option A.

#### Option D.1: Containerized Claude Code
**What:** Run Claude Code CLI in a Docker container with bundled MCP servers.

**Pros:**
- Identical to local execution
- All MCP servers work
- 95%+ quality

**Cons:**
- Modal doesn't support Docker-in-Docker natively
- Cold start latency (30-60 seconds)
- More complex deployment

**Verdict:** Good fallback if Agent SDK has compatibility issues.

#### Option D.3: Hybrid Mac/Linux Remote Executor
**What:** Modal handles queuing, remote Mac Mini runs Claude Code.

**Pros:**
- 98%+ quality (identical to local)
- All features work

**Cons:**
- Single point of failure
- Can't auto-scale
- 4-6 weeks implementation
- Hardware/maintenance burden

**Verdict:** Overkill for current needs.

### Decision: Option B (Agent SDK Worker)

**Recommended Option: B - Claude Agent SDK Worker**

**Rationale:**

1. **Quality Parity**: Agent SDK can achieve 90-95% parity with local `/blueprint-turbo` because it uses the exact same Claude Code engine. The 5-10% gap is primarily from Browser MCP limitations in serverless (acceptable with WebFetch fallback).

2. **Single Source of Truth**: By using `settingSources: ['project']`, the Agent SDK loads `.claude/skills/` and `CLAUDE.md` directly. Updates to skills benefit both local and cloud execution automatically.

3. **MCP Server Support**: Agent SDK natively supports MCP servers. Sequential Thinking MCP can run in serverless (stdio-based). Browser MCP can be omitted for v1 with graceful fallback.

4. **Implementation Efficiency**: 9-12 days is comparable to Option A (10-15 days) but with higher quality ceiling and lower maintenance burden.

5. **Anthropic Alignment**: The Agent SDK is Anthropic's official solution for programmatic agent execution. It will improve over time, and those improvements flow through automatically.

**Implementation Strategy:**
1. **Phase 1 (v1)**: Agent SDK on Modal with Sequential Thinking MCP, WebFetch fallback (no Browser MCP)
2. **Phase 2 (v2)**: Add Browser MCP via Mac Mini or Playwright headless if needed
3. **Phase 3 (v3)**: Hybrid architecture for premium tier if demand justifies

---

*End of Phase 1 Options & Decision*
