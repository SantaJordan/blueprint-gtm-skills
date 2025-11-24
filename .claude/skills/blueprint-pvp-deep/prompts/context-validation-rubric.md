# Context Validation Rubric for PVP Generation

**Purpose:** Ensure the PVP agent has sufficient, high-quality context before attempting to generate Gold Standard PVPs (8.0+).

**When to Use:** Phase 0 of PVP generation process, BEFORE any synthesis or drafting begins.

---

## Required Context Categories

The PVP agent MUST have ALL of these categories to proceed:

1. **Company Context** - Understanding of the sender company
2. **ICP Corp Profile** - Understanding of sender's typical customers
3. **Target Persona** - Understanding of the specific buyer/recipient
4. **Data Landscape** - Catalog of available public data sources
5. **Pain Segments** (Optional but preferred) - Pre-identified pain-qualified segments

---

## Validation Checklist

### 1. Company Context (REQUIRED)

**Minimum Requirements:**
- [ ] Company name identified
- [ ] Core offering/product described (at least 1 sentence)
- [ ] Business model inferred (SaaS / Marketplace / Service / Product / Other)

**Quality Indicators (aim for at least 3/5):**
- [ ] Specific value proposition documented
- [ ] Key differentiators vs competitors identified
- [ ] Customer success stories or case studies found
- [ ] Pricing model understood (if relevant)
- [ ] Company scale/maturity inferred (startup / growth / enterprise)

**VERDICT:**
- **PASS:** Minimum requirements met + at least 2 quality indicators
- **NEEDS MORE:** Missing minimum requirements OR <2 quality indicators
- **If NEEDS MORE:** Invoke Wave 1 (company research) module

---

### 2. ICP Corp Profile (REQUIRED)

**Minimum Requirements:**
- [ ] At least ONE specific industry identified (not "B2B" or "SMB")
- [ ] Company scale indicators present (employee range OR revenue range OR operational scale)
- [ ] At least TWO specific pains documented

**Quality Indicators (aim for at least 4/6):**
- [ ] Industries are SPECIFIC with evidence (e.g., "Healthcare - mentioned in 5 case studies")
- [ ] At least THREE specific pains documented with evidence sources
- [ ] Operational context detailed (key processes, typical workflows, tech stack)
- [ ] Regulatory environment understood (if applicable to industry)
- [ ] Second layer analysis present (ICP's customers and their dynamics)
- [ ] Pain evidence is STRONG (from reviews, case studies, job descriptions - not assumed)

**VERDICT:**
- **PASS:** All minimum requirements + at least 3 quality indicators
- **NEEDS MORE:** Missing minimum requirements OR <3 quality indicators
- **If NEEDS MORE:** Reinvoke Wave 1 with deeper ICP focus OR perform targeted ICP research

---

### 3. Target Persona (REQUIRED)

**Minimum Requirements:**
- [ ] Job title is SPECIFIC (not "Manager" or "Executive" - need actual title like "VP of Operations")
- [ ] At least TWO key responsibilities documented
- [ ] At least TWO specific pains documented

**Quality Indicators (aim for at least 4/7):**
- [ ] Job title is highly specific and research-backed
- [ ] KPIs documented (what they're measured on)
- [ ] Workflow/daily context understood (what their day looks like)
- [ ] At least THREE specific pains documented
- [ ] Information blind spots identified (what they DON'T know)
- [ ] Value drivers documented (what would genuinely impress them)
- [ ] Evidence from job descriptions, forums, or professional articles

**VERDICT:**
- **PASS:** All minimum requirements + at least 3 quality indicators
- **NEEDS MORE:** Missing minimum requirements OR <3 quality indicators
- **If NEEDS MORE:** Perform targeted persona research (job boards, forums, LinkedIn)

---

### 4. Data Landscape (REQUIRED)

**Minimum Requirements:**
- [ ] At least FIVE data sources cataloged
- [ ] At least TWO sources rated HIGH feasibility
- [ ] Feasibility ratings present for all sources (HIGH/MEDIUM/LOW)

**Quality Indicators (aim for at least 5/8):**
- [ ] At least TEN data sources cataloged across multiple categories
- [ ] At least THREE sources rated HIGH feasibility
- [ ] Specific field names documented for top sources
- [ ] API availability documented for each source
- [ ] Cost/pricing information documented
- [ ] Update frequency documented (real-time/daily/weekly/monthly)
- [ ] Sources span multiple categories (Government + Competitive + Velocity + Tech)
- [ ] Sources mapped to specific persona pains

**VERDICT:**
- **PASS:** All minimum requirements + at least 4 quality indicators
- **NEEDS MORE:** Missing minimum requirements OR <4 quality indicators
- **If NEEDS MORE:** Invoke Wave 2 (data landscape scan) module OR perform focused data research on specific categories

---

### 5. Pain Segments (PREFERRED, not required)

**If Available:**
- [ ] 2-3 pain segments pre-identified
- [ ] Each segment has data source combinations documented
- [ ] Segments passed Texada Test
- [ ] Confidence levels documented

**VERDICT:**
- **HAVE SEGMENTS:** Use as starting point for PVP generation
- **NO SEGMENTS:** Generate during PVP process (Phase 1 - Deep Data Synthesis)
- **If NO SEGMENTS:** Invoke Synthesis module OR generate using Sequential Thinking in Phase 1

---

## Overall Context Quality Assessment

After checking all categories, assess overall readiness:

### Scoring System

Count PASS verdicts:
- **5/5 categories PASS:** ✅ EXCELLENT - Proceed with high confidence
- **4/5 categories PASS:** ✅ GOOD - Proceed (gather more on 1 missing category if time permits)
- **3/5 categories PASS:** ⚠️ MARGINAL - Recommend gathering more context before proceeding
- **<3 categories PASS:** ❌ INSUFFICIENT - MUST gather more context

### Decision Matrix

**EXCELLENT (5/5) or GOOD (4/5):**
- ✅ **Action:** Proceed to Phase 1 (Deep Data Synthesis)
- **Confidence:** HIGH - Well-positioned to generate Gold Standard PVPs

**MARGINAL (3/5):**
- ⚠️ **Action:** Ask user if they want to proceed OR gather more context
- **Risks:** May struggle to generate 5 Gold Standard PVPs (8.0+)
- **Recommendation:** Invest 3-5 minutes gathering context on failing categories

**INSUFFICIENT (<3/5):**
- ❌ **Action:** MUST gather more context - DO NOT proceed to PVP generation
- **Risks:** High likelihood of weak PVPs that fail buyer evaluation
- **Requirement:** Invoke necessary modules (Wave 1, Wave 2, Synthesis) to reach GOOD level

---

## Context Gathering Decision Tree

Use this logic to determine what to invoke:

```
IF Company Context = NEEDS MORE:
  → Invoke: wave1-company-research.md

IF ICP Profile = NEEDS MORE:
  → Check: Was Wave 1 already run?
    → YES: Perform targeted ICP research (WebSearch + sequential thinking)
    → NO: Invoke: wave1-company-research.md

IF Persona = NEEDS MORE:
  → Perform targeted persona research:
    - WebSearch: "[persona job title] responsibilities KPIs [industry]"
    - WebSearch: "[persona job title] job description [industry]"
    - WebSearch: "[persona job title] challenges pain points"
    - Use sequential thinking to synthesize findings

IF Data Landscape = NEEDS MORE:
  → Check: Was Wave 2 already run?
    → YES: Perform focused data research on missing categories
    → NO: Invoke: wave2-data-landscape.md

IF Pain Segments = NO SEGMENTS:
  → Check: Do we have Company + ICP + Data Landscape?
    → YES: Invoke: synthesis-segments.md OR generate in Phase 1
    → NO: Gather prerequisite context first
```

---

## Context Quality Flags

During validation, flag these quality concerns:

### RED FLAGS (Critical - Must Address):
- 🚩 Generic industry labels ("B2B", "SMB", "Enterprise")
- 🚩 Generic persona titles ("Manager", "Executive", "Leader")
- 🚩 Pains are assumed (no evidence sources cited)
- 🚩 No HIGH feasibility data sources found
- 🚩 Data sources don't map to any persona pains

### YELLOW FLAGS (Warning - Should Address if Time):
- ⚠️ Only 1-2 industries identified (narrow)
- ⚠️ Pains are sparse (<3 documented)
- ⚠️ No second layer analysis (ICP's customers)
- ⚠️ Data landscape missing entire category (e.g., no government data)
- ⚠️ Field names not documented for data sources

### GREEN FLAGS (Excellent - Indicates Strong Context):
- ✅ Multiple specific industries with evidence
- ✅ 5+ persona pains with evidence sources
- ✅ 10+ data sources with 3+ HIGH feasibility
- ✅ Specific field names documented
- ✅ Second layer analysis present
- ✅ Pre-identified pain segments available

---

## Output Format for Phase 0

After validation, output:

```markdown
# Phase 0: Context Validation Results

## Validation Summary

**Company Context:** ✅ PASS / ⚠️ NEEDS MORE
**ICP Profile:** ✅ PASS / ⚠️ NEEDS MORE
**Target Persona:** ✅ PASS / ⚠️ NEEDS MORE
**Data Landscape:** ✅ PASS / ⚠️ NEEDS MORE
**Pain Segments:** ✅ AVAILABLE / ⚠️ MISSING

**Overall Readiness:** ✅ EXCELLENT / ✅ GOOD / ⚠️ MARGINAL / ❌ INSUFFICIENT

**PASS Count:** [X]/5 categories

## Quality Flags
**Red Flags:** [List any critical concerns]
**Yellow Flags:** [List any warnings]
**Green Flags:** [List any excellent indicators]

## Decision

**PROCEED to Phase 1:** [YES/NO/WITH CAUTION]

**Justification:** [Explain the readiness assessment]

**Context Gaps Identified:**
1. [Gap 1 - and whether it needs addressing]
2. [Gap 2 - and whether it needs addressing]

**Recommended Actions:**
- [Action 1: e.g., "Invoke wave1-company-research.md"]
- [Action 2: e.g., "Perform targeted persona research"]
- OR: "No additional context needed - proceed to Phase 1"

## Estimated Impact on PVP Quality

**With current context:**
- Expected number of 8.0+ PVPs: [0-5]
- Confidence level: HIGH / MEDIUM / LOW
- Primary limiting factor: [What's holding back quality]

**With recommended context gathering:**
- Expected number of 8.0+ PVPs: [Improved estimate]
- Additional time required: [X] minutes
- Value of investment: [HIGH / MEDIUM / LOW]
```

---

## Key Principles

1. **Context is everything** - Great PVPs are impossible without great context
2. **Quality over speed** - Better to spend 5 minutes gathering context than generate weak PVPs
3. **Be honest** - If context is insufficient, say so clearly
4. **Be specific** - Don't just say "needs more" - say exactly what's missing
5. **Validate rigorously** - Gold Standard PVPs (8.0+) require Gold Standard context

---

## Success Criteria

Context validation succeeds when:
- [ ] All 5 categories assessed with clear PASS/NEEDS MORE verdict
- [ ] Overall readiness rated (EXCELLENT/GOOD/MARGINAL/INSUFFICIENT)
- [ ] Specific gaps identified with concrete recommendations
- [ ] Decision made: Proceed / Gather more context / Abort
- [ ] If proceeding: Confidence level in PVP quality potential is documented
