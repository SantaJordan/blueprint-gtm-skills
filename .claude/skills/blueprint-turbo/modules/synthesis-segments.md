# Synthesis: Pain Segment Generation via Sequential Thinking

**Objective:** Generate 2-3 pain-qualified segment hypotheses that COMBINE available data sources

**Time:** 9-11 minutes

**Input:**
- Company context from Wave 1
- ICP and persona profiles from Wave 1
- **Product Value Analysis from Wave 0.5 (valid/invalid pain domains)**
- Data Availability Report from Wave 2
- Niche Qualification Results from Wave 1.5 (including Criterion 5 scores)

**Output:** 2-3 validated pain segments with data source combinations that PASS Gate 5 (Product Connection)

---

## CRITICAL CHANGES

1. Sequential Thinking now receives the Data Availability Report from Wave 2 as INPUT. Segments MUST use only discovered data sources.

2. **NEW: Product-Fit Validation Required.** Every segment MUST pass Gate 5 (Product Connection) before proceeding. Pain that doesn't connect to product value = AUTO-DESTROY.

3. **NEW: If all vertical segments fail Gate 5**, trigger Situation-Based Fallback (see bottom of this document).

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
- **NEW: Segments MUST pass Gate 5 (Product Connection)**
  - Pain identified must be in a VALID domain from Wave 0.5 Product Value Analysis
  - Resolving this pain must REQUIRE or BENEFIT FROM the product
  - If pain is in INVALID domain → AUTO-REJECT before drafting

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

## HARD GATE VALIDATION (MANDATORY)

**CRITICAL:** After generating segments, EACH segment MUST pass all 5 hard gates before proceeding to message generation.

**Load Validator:**
```
Read: .claude/skills/blueprint-pvp-deep/prompts/hard-gate-validator.md
Reference: .claude/skills/blueprint-pvp-deep/prompts/banned-patterns-registry.md
Reference: .claude/skills/blueprint-turbo/modules/product-fit-triage.md
```

**CRITICAL DEPENDENCY:** Gate 5 requires Product Value Analysis output from Wave 0.5

### Gate 1: Horizontal Disqualification

**Question:** Is the ICP operationally specific, or could it be "any B2B company"?

**FAIL if ICP can be described as:**
- "Any B2B company"
- "SaaS companies" (generic)
- "Sales teams" (without regulated context like insurance/RE)
- "Growing companies" or "Funded companies"
- "Companies with [department]"

**PASS if ICP includes:**
- Specific industry with regulatory oversight
- Operational context (processes, compliance requirements)
- Observable pain tied to detectable data

### Gate 2: Causal Link Constraint

**Question:** Does the signal DIRECTLY PROVE the pain (not just correlate)?

**The Test:** "Could a company have this signal but NOT have the pain?"
- If YES → Weak causal link → ❌ FAIL
- If NO → Strong causal link → ✅ PASS

**BANNED signals (ALWAYS fail Gate 2):**
- Recently raised funding
- Hiring for [role type]
- Growing headcount
- Expanding to new markets
- M&A activity
- Job postings
- Tech stack includes [tool]

**STRONG signals (can PASS Gate 2):**
- Open EPA violation → PROVES compliance pressure
- CMS <3 star rating → PROVES quality mandate
- FMCSA Conditional rating → PROVES safety intervention required
- Health dept grade drop → PROVES operational failure
- License expiration in 30 days → PROVES compliance deadline

### Gate 3: No Aggregates Ban

**Question:** Are statistics company-specific, or industry-wide aggregates?

**FAIL if segment uses:**
- "Industry average is X%" (without their specific data)
- "Companies like yours typically..."
- "Research shows that..."
- "[N]% of [industry] faces..."

**PASS if format is:**
- "Your [specific metric] vs [benchmark]"
- Their data point + comparison aggregate

### Gate 4: Technical Feasibility Audit

**Question:** Can you explain MECHANICALLY how to detect this data?

**For EVERY data claim, must answer:**
1. What is the data source? (API name, database, scraping target)
2. What is the specific field/attribute? (Field name, CSS selector)
3. How do we access it? (API call, web scrape, manual lookup)
4. What's the detection footprint? (What makes this visible externally?)

**FAIL if ANY claim is undetectable:**
- CRM data quality (internal system)
- Sales cycle length (internal metric)
- Employee satisfaction (not systematic)
- Budget constraints (not public)
- "BuiltWith for [non-web technology]"

### Gate 5: Product Connection (NEW - CRITICAL)

**Question:** Does resolving this pain require/benefit from our product?

**Referencing Wave 0.5 Product Value Analysis:**
- Valid Pain Domains: [List from Wave 0.5]
- Invalid Pain Domains: [List from Wave 0.5]

**FAIL if:**
- Pain is in INVALID domain from Wave 0.5
- Product is only tangentially related to pain
- Any competitor could solve this pain with their (different) product
- Connection between pain and product requires >2 logical jumps

**PASS if:**
- Pain is in VALID domain from Wave 0.5
- Product is PRIMARY solution to this pain
- Buying the product materially addresses the situation

**Validation Question:**
"If this prospect resolves this pain, would they NEED this product to do it?"
- YES = ✅ PASS
- MAYBE = ⚠️ Weak fit, may need revision
- NO = ❌ FAIL → AUTO-DESTROY (no revision possible)

**Gate 5 Examples:**
| Pain | Product | Gate 5 | Rationale |
|------|---------|--------|-----------|
| "CE deadline in 45 days" | Digital business cards | ❌ FAIL | Cards don't help with CE compliance |
| "No time to print cards before conference" | Digital business cards | ✅ PASS | Product is direct solution |
| "CMS <3 star rating" | Compliance training software | ✅ PASS | Training addresses quality issues |

### Validation Output Format

For EACH segment, document:

```markdown
## Hard Gate Validation: [Segment Name]

**Gate 1 (Horizontal):** ✅ PASS / ❌ FAIL
- ICP: [description]
- Rationale: [why passes/fails]

**Gate 2 (Causal Link):** ✅ PASS / ❌ FAIL
- Signal: [data signal used]
- Pain: [what it proves]
- "Could have signal without pain?": YES/NO
- Rationale: [why passes/fails]

**Gate 3 (Aggregates):** ✅ PASS / ❌ FAIL
- Statistics used: [list]
- Company-specific?: YES/NO
- Rationale: [why passes/fails]

**Gate 4 (Feasibility):** ✅ PASS / ❌ FAIL
- Data claims: [list]
- Detection mechanism for each: [API field/selector]
- Rationale: [why passes/fails]

**Gate 5 (Product Connection):** ✅ PASS / ❌ FAIL
- Pain identified: [what pain]
- Product: [what company sells]
- Pain domain: VALID / INVALID (from Wave 0.5)
- "Would they NEED this product to resolve?": YES/NO/MAYBE
- Rationale: [why passes/fails]

**VERDICT:** ✅ VALIDATED / ❌ AUTO-DESTROY
```

### Decision Logic

| Result | Action |
|--------|--------|
| All 5 gates PASS | ✅ Proceed to message generation |
| Gate 3 only fails | ONE revision attempt (add specific data) |
| Gate 4 only fails | ONE revision attempt (substitute data source) |
| Gate 1, 2, or 5 fails | ❌ DESTROY immediately (fundamental flaw) |
| 2+ gates fail | ❌ DESTROY immediately |
| Still fails after revision | ❌ DESTROY (no second attempt) |

**CRITICAL: Gate 5 failures indicate product-pain mismatch.**
- If segment passes Gates 1-4 but fails Gate 5: The data is good but doesn't connect to product
- Do NOT attempt revision - the pain domain is wrong
- Consider situation-based fallback or no-fit response

### Minimum Requirement

- At least 2 segments MUST pass all 5 gates
- If <2 pass all 5 gates: Check if Gate 5 was the blocker
- If Gate 5 blocked all segments: Trigger SITUATION-BASED FALLBACK
- If still <2 after situation fallback: Trigger NO-FIT RESPONSE

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

## SITUATION-BASED FALLBACK (CONDITIONAL)

**TRIGGER:** Execute when ALL vertical segments fail Gate 5 (Product Connection)

**Objective:** Generate SITUATION-based segments instead of forcing irrelevant vertical data

**Load Module:**
```
Read: .claude/skills/blueprint-turbo/modules/situation-segments.md
```

### When to Trigger

| Condition | Action |
|-----------|--------|
| All segments pass Gates 1-4 but fail Gate 5 | TRIGGER situation fallback |
| Product type is "horizontal" (serves any business) | TRIGGER situation fallback |
| All regulated niches have Criterion 5 < 5 | TRIGGER situation fallback |

### Situation Fallback Process

1. **From Wave 0.5 Product Value Analysis, extract:**
   - Core Problem Solved
   - Urgency Triggers (time/scale/change pressure)
   - Who Experiences This

2. **For each urgency trigger, generate situation segment:**
   - What data proves this situation exists?
   - Is that data externally observable?
   - Does the situation create IMMEDIATE need for product?

3. **Validate situation segments against Gate 5:**
   - Situation must create direct need for product (not tangential)
   - Product must be the solution to the situation
   - Buying product must resolve the immediate problem

### Example: Blinq (Digital Business Cards)

**Vertical Segments (ALL FAILED Gate 5):**
- Insurance agents (NIPR data) → Pain: CE deadlines → ❌ Cards don't solve CE
- Real estate agents (license data) → Pain: License renewal → ❌ Cards don't solve renewal

**Situation Segments (TRIGGERED):**
1. **Conference Urgency**
   - Data: New license + conference attendance signal
   - Pain: No time to print cards before event
   - Gate 5: ✅ PASS (digital cards = instant solution)

2. **Rapid Onboarding**
   - Data: LinkedIn hiring velocity (15+ hires/month)
   - Pain: Can't provision cards fast enough
   - Gate 5: ✅ PASS (digital cards scale instantly)

### Situation Fallback Output

If situation segments pass Gate 5:
```
🔄 Situation Fallback: Generated [N] timing plays (vertical segments failed product-fit)
```

If situation segments also fail:
```
⚠️ No-Fit: Both vertical and situation segments failed product-fit. See recommendations.
```

---

**Progress Output:**
```
🧠 Synthesis: Generated [N] pain segments from available data sources (Sequential Thinking MCP complete)
```

**Progress Output (Situation Fallback):**
```
🔄 Synthesis: Vertical segments failed Gate 5. Generated [N] situation-based segments (Product-fit validated)
```

**Progress Output (No-Fit):**
```
⚠️ Synthesis: No segments passed Gate 5 (Product Connection). Triggering No-Fit Response.
```
