# Vertical Qualification Module

**Purpose:** Convert generic verticals to regulated niches with data moats AND product-fit BEFORE data discovery begins.

**When:** Execute immediately after Wave 0.5 Product Value Analysis, BEFORE Wave 2.

**Time:** 3-5 minutes

**Output:** 1-2 qualified niches with scores ≥30/50 AND Criterion 5 ≥5, ready for Wave 2 data discovery

**CRITICAL DEPENDENCY:** Requires Product Value Analysis output from Wave 0.5 (valid/invalid pain domains)

---

## Why This Matters

**The Blinq Failure Pattern:**
1. Wave 1 identifies: "Sales teams, professional services"
2. Wave 2 searches generic data: Crunchbase, Apollo, job postings
3. Synthesis generates: "Companies raising Series B and hiring sales"
4. Result: Generic messages that could be sent by any competitor

**The Correct Pattern:**
1. Wave 1 identifies: "Sales teams, professional services"
2. **NICHE CONVERSION:** "Sales teams" → "Multi-state insurance agents" (NIPR)
3. Wave 2 searches: NIPR, state licensing boards, CE databases
4. Synthesis generates: "Agencies with 14 new licenses in 45 days = compliance gap"
5. Result: Specific messages only we can send

---

## Process

### Step 1: List All Verticals from Wave 1

Extract every industry/vertical mentioned:
- Primary verticals (explicitly stated on website)
- Secondary verticals (mentioned in case studies, use cases)
- Adjacent verticals (logically related)

### Step 2: Check Auto-Reject List

Reference: `.claude/skills/blueprint-turbo/references/data-moat-verticals.md`

For EACH vertical, check if it's on the Auto-Reject list:

| Vertical | Auto-Reject? | Action |
|----------|--------------|--------|
| SaaS companies | YES | MUST convert to niche |
| Tech startups | YES | MUST convert to niche |
| B2B companies | YES | MUST convert to niche |
| Sales teams (generic) | YES | MUST convert to niche |
| Growing companies | YES | MUST convert to niche |
| Professional services | YES | MUST convert to niche |
| Marketing teams | YES | NO good niche exists |
| HR departments | YES | NO good niche exists |

**If vertical is NOT on Auto-Reject list:** Proceed to Step 3 scoring
**If vertical IS on Auto-Reject list:** Proceed to Step 4 niche conversion

### Step 3: Score Non-Rejected Verticals

For verticals NOT on auto-reject list, score using the rubric:

**Criterion 1: Regulatory Footprint (0-10)**
- 10: Heavy federal regulation (EPA, OSHA, CMS, FDA, FMCSA)
- 7-9: State-level licensing with public portals
- 4-6: Industry self-regulation
- 0-3: No regulatory oversight

**Criterion 2: Compliance-Driven Pain (0-10)**
- 10: Violations directly create solution-relevant pain
- 7-9: Regulations force behaviors creating pain
- 4-6: Indirect connection
- 0-3: No compliance-driven pain

**Criterion 3: Data Accessibility (0-10)**
- 10: Free public API, daily updates
- 7-9: Free portal, weekly updates
- 4-6: Paid API or manual access
- 0-3: No accessible data

**Criterion 4: Specificity Potential (0-10)**
- 10: Record numbers, dates, addresses all available
- 7-9: Multiple identifiers available
- 4-6: Basic entity data
- 0-3: Aggregate data only

**Criterion 5: Product-Solution Alignment (0-10) - CRITICAL**

This criterion uses the Product Value Analysis from Wave 0.5:

| Score | Description |
|-------|-------------|
| 9-10 | Niche's PRIMARY pain is directly solved by this product |
| 7-8 | Product solves one of niche's top 3 pains |
| 5-6 | Product tangentially helps with niche's pain |
| 3-4 | Weak connection, product is nice-to-have |
| 0-2 | No connection between niche pain and product value |

**How to Score Criterion 5:**

1. From Wave 0.5, retrieve:
   - Valid Pain Domains (product can solve)
   - Invalid Pain Domains (product cannot solve)

2. Identify the niche's PRIMARY pain (what the regulatory data reveals)

3. Check domain match:
   - Pain in VALID domain → Start at 7, adjust based on directness
   - Pain in INVALID domain → Auto-score 0-4 (product mismatch)

4. Ask validation question:
   "If this niche resolves this pain, would they NEED this product to do it?"
   - YES = 8-10
   - MAYBE = 5-7
   - NO = 0-4

**Total Score = Sum of 5 criteria (max 50)**

**CRITICAL: Criterion 5 is a HARD GATE**
- Criterion 5 < 5 → AUTO-REJECT regardless of data score
- A niche can have excellent data (40/40) but if product doesn't solve its pain → REJECT

### Step 4: Convert Auto-Reject Verticals to Niches

For each auto-rejected vertical, find regulated niches:

```
CONVERSION SEARCH PATTERN:

1. WebSearch: "[vertical] licensing board database"
2. WebSearch: "[vertical] government records public"
3. WebSearch: "[vertical] compliance violations database"
4. WebSearch: "[vertical] state regulation lookup"

Reference: data-moat-verticals.md Niche Conversion Table
```

**Example Conversions:**

| Generic | Search | Regulated Niche Found | Data Source |
|---------|--------|----------------------|-------------|
| "Sales teams" | "sales licensing board" | Insurance agents | NIPR |
| "Sales teams" | "sales license lookup" | Real estate agents | State RE boards |
| "Professional services" | "professional license database" | Contractors | State licensing |
| "Healthcare" | "healthcare facility ratings" | Nursing homes | CMS Care Compare |

### Step 5: Score Converted Niches

Apply same 5-criterion rubric to each converted niche.

### Step 6: Select Best Niche(s)

**Decision Matrix (NEW - includes Product-Fit Gate):**

**FIRST: Check Criterion 5 (Product-Fit)**

| Criterion 5 Score | Action |
|-------------------|--------|
| ≥7 | Excellent product-fit, proceed to total score check |
| 5-6 | Acceptable product-fit, proceed to total score check |
| <5 | **AUTO-REJECT** regardless of data score |

**THEN: Check Total Score (only if Criterion 5 ≥5)**

| Total Score | Criterion 5 | Decision |
|-------------|-------------|----------|
| ≥35 | ≥7 | **TIER 1** - Excellent data moat + product-fit |
| ≥30 | ≥5 | **TIER 2** - Good data moat + acceptable product-fit |
| 25-29 | ≥5 | **CONDITIONAL** - Try internal data combinations |
| <25 OR C5<5 | Any | **REJECT** - Insufficient fit |

**Selection Rules:**
1. **Criterion 5 is the FIRST filter** - reject all niches with C5 < 5
2. From remaining niches, select highest total score (≥30/50)
3. If multiple niches qualify, select top 2 max
4. If NO niche has C5 ≥5: **TRIGGER SITUATION-BASED FALLBACK**
5. If still nothing: Warn user, this may not be Blueprint-compatible

**Example: Blinq (Digital Business Cards)**

| Niche | Data Score (C1-C4) | C5 (Product-Fit) | Total | Decision |
|-------|-------------------|------------------|-------|----------|
| Insurance agents (NIPR) | 32/40 | 2/10 ❌ | 34/50 | REJECT (C5<5) |
| Real estate agents | 28/40 | 3/10 ❌ | 31/50 | REJECT (C5<5) |
| Conference attendees | 18/40 | 9/10 ✅ | 27/50 | CONDITIONAL (weak data) |

**Result:** All high-data niches fail C5 → Trigger Situation-Based Fallback

---

## Output Format

```markdown
# Vertical Qualification Results

## Input Verticals from Wave 1
1. [Vertical 1]
2. [Vertical 2]
3. [Vertical 3]

## Auto-Reject Check

| Vertical | Auto-Reject? | Action |
|----------|--------------|--------|
| [Vertical 1] | YES/NO | Convert/Score |
| [Vertical 2] | YES/NO | Convert/Score |

## Niche Conversions Attempted

### [Generic Vertical] → Niche Conversion

**Search Queries Executed:**
- "[vertical] licensing board database" → Found: [result]
- "[vertical] government records" → Found: [result]

**Niches Identified:**
1. [Niche 1] - Data Source: [source]
2. [Niche 2] - Data Source: [source]

## Scoring Results

### [Niche/Vertical Name]

| Criterion | Score | Rationale |
|-----------|-------|-----------|
| Regulatory Footprint | X/10 | [Why] |
| Compliance-Driven Pain | X/10 | [Why] |
| Data Accessibility | X/10 | [Why] |
| Specificity Potential | X/10 | [Why] |
| **Product-Solution Alignment** | **X/10** | [Pain domain: VALID/INVALID, Why product does/doesn't solve] |
| **TOTAL** | **XX/50** | |

**Product-Fit Gate:** ✅ PASS (C5≥5) / ❌ FAIL (C5<5)
**Verdict:** PROCEED / CONDITIONAL / REJECT / TRIGGER SITUATION FALLBACK

[Repeat for each niche/vertical]

## Final Selection

**Selected Niche(s) for Wave 2:**
1. [Niche] - Score: XX/50 (C5: X/10) - Data Source: [source]
2. [Niche] - Score: XX/50 (C5: X/10) - Data Source: [source] (if applicable)

**Rejected:**
- [Vertical/Niche] - Score: XX/50 (C5: X/10) - Reason: [why]

**Product-Fit Summary:**
- Niches passing C5 gate (≥5): [N]
- Niches failing C5 gate (<5): [N]
- Action: PROCEED / TRIGGER SITUATION FALLBACK / NO-FIT WARNING

## Proceeding to Wave 2 with: [Selected Niche(s)]
```

---

## Edge Cases

### No Niche Scores ≥25

**Try Internal Data Hybrid:**
1. What data does the SENDER company have? (from internal data inference)
2. Can sender's aggregated data + public data create PVPs?
3. If yes: Proceed with hybrid approach, score as 20-24 (conditional)
4. If no: Warn user

**Warning Output:**
```markdown
⚠️ VERTICAL QUALIFICATION WARNING

No regulated niche found with score ≥25/40.

**Attempted Niches:**
- [Niche 1]: Score XX/40 - [weakness]
- [Niche 2]: Score XX/40 - [weakness]

**Internal Data Hybrid Attempted:** [Yes/No]
- Sender internal data: [what they might have]
- Potential combination: [if any]

**Recommendation:**
1. This ICP may not be suitable for data-driven Blueprint GTM
2. Consider: [alternative approach or vertical]
3. Proceed with PQS-only approach (lower confidence)

**User Decision Required:** Proceed with limited data / Abort / Try different vertical
```

### Company Only Serves B2B SaaS

If target company's ONLY customers are B2B SaaS (no regulated verticals):

1. Check if they have internal data that could be aggregated
2. If sender has 100+ customers → internal benchmarking possible
3. If no regulated niche AND no internal data → Blueprint may not be suitable

**Output:**
```markdown
⚠️ BLUEPRINT COMPATIBILITY WARNING

This company serves horizontally (B2B SaaS to B2B SaaS).
No regulated vertical found in their customer base.

**Options:**
1. Internal Data Only: If sender has 100+ customers, can create benchmark PVPs
2. PQS-Only Approach: Use competitive intelligence for pain identification
3. Abort: This use case may not be Blueprint-compatible

**Recommendation:** [Based on analysis]
```

### Multiple High-Scoring Niches

If 3+ niches score ≥25:

1. Select top 2 by score
2. Prioritize diversity (different data sources)
3. Document why others were deprioritized

---

## Integration with Wave 2

**Wave 2 Input Changes:**

Instead of searching for generic industry data, Wave 2 receives:

```markdown
## Wave 2 Input: Qualified Niches

**Primary Niche:** [Niche name]
- Score: XX/40
- Data Source(s): [Specific sources to search]
- Pain Signal(s): [What to look for]

**Secondary Niche (if applicable):** [Niche name]
- Score: XX/40
- Data Source(s): [Specific sources]
- Pain Signal(s): [What to look for]

**Search Priority:**
1. [Primary niche data source] - MUST find
2. [Secondary niche data source] - Should find
3. [Supporting sources] - Nice to have
```

---

## Success Criteria

Vertical qualification succeeds when:

- [ ] Product Value Analysis (Wave 0.5) output available with valid/invalid pain domains
- [ ] All Wave 1 verticals checked against auto-reject list
- [ ] Auto-rejected verticals converted to niches
- [ ] All niches scored using 5-criterion rubric (including Product-Solution Alignment)
- [ ] At least 1 niche has Criterion 5 ≥5 (product-fit gate passed)
- [ ] At least 1 niche scores ≥30/50 total with C5≥5
- [ ] Selected niche has identifiable data source
- [ ] Wave 2 receives specific niche with confirmed product-fit

**If NO niche passes Criterion 5 gate:**
- [ ] Situation-based fallback triggered (Wave 2.5)
- [ ] OR No-fit warning issued with clear recommendations

---

## Quick Reference: Scoring Shortcuts

**Instant 30+ (Tier 1):**
- CMS databases (Care Compare, Nursing Home Compare)
- EPA ECHO
- FMCSA SAFER
- FDA Warning Letters
- Major city health departments (NYC, LA, Chicago, SF)

**Likely 25-29 (Tier 2):**
- State licensing boards (contractors, professionals)
- NIPR (insurance agents)
- State real estate boards
- FINRA BrokerCheck (manual only)

**Usually <20 (Reject):**
- Any "B2B SaaS" vertical
- Any "tech company" vertical
- Any industry without government oversight
