# Synthesis: Pain Segment Generation via Sequential Thinking

**Objective:** Generate 2-3 pain-qualified segment hypotheses that COMBINE available data sources

**Time:** 9-11 minutes

**Input:**
- Company context from Wave 1
- ICP and persona profiles from Wave 1
- Data Availability Report from Wave 2

**Output:** 2-3 validated pain segments with data source combinations

---

## CRITICAL CHANGE

Sequential Thinking now receives the Data Availability Report from Wave 2 as INPUT. Segments MUST use only discovered data sources.

---

## Execute Sequential Thinking MCP

Invoke: `mcp__sequential-thinking__sequentialthinking`

### Prompt Template

```
I need to generate 2-3 pain-qualified segment hypotheses for [COMPANY NAME] using ONLY the data sources discovered in Wave 2.

CONTEXT FROM WAVE 1:

**Company:** [Name and core offering]
**Business Model:** [SaaS/Marketplace/Service/etc.]

**ICP:**
- Industries: [Specific industries]
- Company scale: [Size indicators]
- Operational context: [Key processes, workflows]

**Target Persona:**
- Job Title: [Specific title]
- Responsibilities: [Key duties]
- KPIs: [What they're measured on]
- Key Pains: [Top 3-5 pains from research]
- Information Blind Spots: [What they don't know]

DATA AVAILABILITY REPORT FROM WAVE 2:

GOVERNMENT DATA (HIGH feasibility sources):
[List each HIGH feasibility gov source with:]
- Source name
- Key fields available
- Update frequency
- URL/API endpoint
- Potential use case

COMPETITIVE INTELLIGENCE (HIGH/MEDIUM feasibility sources):
[List each source with:]
- Source name / method
- Data points available
- Cost and accessibility
- Potential use case

VELOCITY SIGNALS (HIGH feasibility sources):
[List each source with:]
- Source name
- Fields available
- API details
- Potential use case

TECH/OPERATIONAL (discovered sources):
[List each source with:]
- Source name / method
- What can be detected
- Accessibility
- Potential use case

---

TASK: Use sequential thinking to generate 2-3 pain segment hypotheses. For each thought:

1. Review what data is ACTUALLY available (from Wave 2 report above)
2. Consider which COMBINATION of data sources could detect a painful situation
3. Think about whether this combination passes Texada Test:
   - Hyper-specific (uses actual field names from Wave 2)?
   - Factually grounded (not inferred, but proven by data)?
   - Non-obvious synthesis (connects multiple data points they don't have)?
4. If using ONLY government data → can create pure PQS messages
5. If using government + competitive/velocity → creates hybrid PVP with confidence disclosure
6. Reject segments that require too much inference or weak data
7. Revise if Texada Test fails

REQUIREMENTS:
- Segments MUST use data sources rated HIGH or MEDIUM feasibility in Wave 2
- Must COMBINE 2-3 data sources (not rely on single source)
- Pure government data combinations = highest confidence (90%+)
- Hybrid combinations (gov + competitive + velocity) = good confidence (60-75%) if disclosed
- Avoid segments requiring INFERENCE without data proof
- Must be situations the persona DOESN'T already know about (non-obvious synthesis)

EXAMPLE (OWNER.COM):

SEGMENT 1: High-Volume Independent Restaurants with Platform Dependency

Data Combination:
- Google Maps review velocity (>100 reviews/month) [HIGH feasibility - Wave 2]
- Menu price arbitrage (DoorDash markup >25%) [MEDIUM feasibility - Wave 2]
- No direct ordering system (website tech check) [MEDIUM feasibility - Wave 2]

Texada Check:
✅ Hyper-specific: Exact review counts, specific markup %, binary tech presence
✅ Factually grounded: All three data points are OBSERVABLE (not inferred)
✅ Non-obvious: They know they use DoorDash, but don't know:
   - Their review velocity compared to benchmarks
   - Their exact markup % across menu items
   - How this combination signals commission pressure

Confidence: 60-75% (will disclose in message as 'likely paying $X-Y range')

Data Source Attribution:
- Review velocity: Google Maps API (reviews[].time field)
- Pricing: Web scraping (manual or Apify)
- Tech stack: Website inspection or BuiltWith

OUTPUT: 2-3 pain segment hypotheses with:
- Segment name
- Data source combination (specific sources from Wave 2 report)
- Actual field names or data points to extract
- Texada Test validation (passes/fails, why)
- Confidence level (90%+ pure government, 60-75% hybrid, <60% reject)
- Message type (PQS for government, PVP for hybrid)
- Whether inference is required (if yes, must be minimal and disclosed)
```

---

## Output Format

The Sequential Thinking MCP should produce 2-3 segments in this format:

```markdown
# Pain Segment Hypotheses

## Segment 1: [Name]

**Data Source Combination:**
1. [Source Name from Wave 2] - [Fields: specific field names]
   - Feasibility: HIGH/MEDIUM
   - What it detects: [Specific data point]

2. [Source Name from Wave 2] - [Fields: specific field names]
   - Feasibility: HIGH/MEDIUM
   - What it detects: [Specific data point]

3. [Source Name from Wave 2] - [Fields: specific field names]
   - Feasibility: HIGH/MEDIUM
   - What it detects: [Specific data point]

**Pain Hypothesis:**
[Description of the painful situation this combination detects]

**Why Persona Doesn't Know:**
[Explanation of the information asymmetry or synthesis complexity]

**Texada Test Validation:**
- ✅/❌ Hyper-specific: [Why passes/fails]
- ✅/❌ Factually grounded: [Why passes/fails]
- ✅/❌ Non-obvious synthesis: [Why passes/fails]

**Verdict:** PASS / FAIL
[If FAIL, explain why and either revise or reject]

**Confidence Level:** [90-95% / 60-75% / 50-60%]
**Data Type:** [Pure Government / Hybrid / Competitive Only]
**Message Type:** [PQS / PVP]

**Inference Required:** [Minimal/None / Moderate / High]
**Disclosure Strategy:** [If inference required, how to disclose in message]

---

## Segment 2: [Name]

[Same structure as Segment 1]

---

## Segment 3 (Optional): [Name]

[Same structure as Segment 1]
```

---

## Sequential Thinking Process

The Sequential Thinking MCP should follow this iterative process:

**Thought 1-2:** Review available data sources and persona pains
**Thought 3-5:** Generate initial segment ideas by combining data sources
**Thought 6-8:** Evaluate each idea against Texada Test
**Thought 9-11:** Revise segments that fail, reject if unfixable
**Thought 12-14:** Validate confidence levels and message type classification
**Final Thought:** Select top 2-3 segments that pass all criteria

---

## Validation Criteria

Each segment must meet ALL of these criteria:

### Data Grounding
- [ ] Uses ONLY data sources from Wave 2 report
- [ ] All sources rated HIGH or MEDIUM feasibility
- [ ] Specific field names documented
- [ ] Combines 2-3 data sources (not single source)

### Texada Test
- [ ] **Hyper-specific:** Uses exact field names, specific thresholds
- [ ] **Factually grounded:** All claims are observable/provable
- [ ] **Non-obvious:** Persona wouldn't easily discover this themselves

### Confidence & Feasibility
- [ ] Confidence level is appropriate for data type:
  - Pure government: 90-95%
  - Hybrid (gov + competitive/velocity): 60-75%
  - Competitive/velocity only: 50-70%
- [ ] If confidence <60%, segment is rejected

### Persona Relevance
- [ ] Addresses a specific pain from Wave 1 research
- [ ] Creates information asymmetry (they don't know this)
- [ ] Actionable insight (not just interesting trivia)

---

## Error Handling

**No data source combinations pass Texada Test:**
- Primary: Loosen specificity slightly while maintaining factual grounding
- Fallback: Generate segments with "disclosed limitations" (clearly state what's inferred)
- Hard limit: If no segments pass after 2 revision cycles, this ICP may not be suitable for data-driven PVPs
- Document why segments failed and recommend manual research

**All combinations require high inference:**
- Primary: Focus on pure government data (highest confidence)
- Fallback: Use hybrid with clear disclosure language
- Reject: Segments requiring >40% inference without data proof
- Document inference concerns in output

**Only 1 viable segment emerges:**
- Primary: That's acceptable - quality over quantity
- Action: Generate 2 variants of the strong segment for Wave 3
- Continue execution with 1 HIGH quality segment

---

## Success Criteria

- [ ] 2-3 pain segments generated
- [ ] Each segment uses ACTUAL data from Wave 2 report
- [ ] All segments pass Texada Test
- [ ] Confidence levels documented and appropriate
- [ ] Clear guidance on PQS vs PVP message type
- [ ] Specific field names and data sources attributed
- [ ] Inference levels documented and manageable (<40%)

---

**Progress Output:**
```
🧠 Synthesis: Generated [N] pain segments from available data sources (Sequential Thinking MCP complete)
```
