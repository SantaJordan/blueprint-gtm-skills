# Wave 1: Company & Market Intelligence Gathering

**Objective:** Launch 15-20 parallel calls to gather ALL company/market/database intelligence

**Time:** 0-4 minutes

**Input:** Company URL

**Output:** Structured company context, ICP profile, and target persona

---

## Execution

### Company Website Analysis (4-5 parallel WebFetch)

Parse company URL and extract base domain. Then execute these WebFetch calls IN PARALLEL:

1. WebFetch: Company homepage
2. WebFetch: /about or /company or /our-story page
3. WebFetch: /customers or /case-studies or /success-stories page
4. WebFetch: /solutions or /product or /platform page
5. WebFetch: /blog (latest 2-3 posts)

Extract:
- Company core offering and value proposition
- Target market/industries served
- Customer success stories and use cases
- Key differentiators and unique advantages

### Market & ICP Research (6-8 parallel WebSearch)

Execute these searches IN PARALLEL:

1. WebSearch: "[company name] customer reviews"
2. WebSearch: "[company name] case studies success stories"
3. WebSearch: "[company name] target customers industries"
4. WebSearch: "what problems does [company name] solve"
5. WebSearch: "[company name] vs competitors comparison"
6. WebSearch: "[inferred user role - e.g., 'operations manager'] pain points challenges"
7. WebSearch: "[inferred user role] job description responsibilities KPIs"
8. WebSearch: "[industry] common operational challenges data"

Extract:
- ICP characteristics (company size, industries, operational context)
- Target persona (job title, responsibilities, KPIs, blind spots)
- Common pain points and trigger events
- Evidence of what customers value

---

## Output Format

Return a structured markdown report with these sections:

```markdown
## Company Context
**Company Name:** [Name]
**Company URL:** [URL]
**Core Offering:** [1-2 sentence description of what they sell/do]
**Value Proposition:** [Primary benefits they claim to deliver]
**Business Model:** [SaaS / Marketplace / Service Business / Product / Other - infer from offering]
**Key Differentiators:** [What makes them unique vs competitors]

## ICP Corp Profile
**Industries Served:** [Specific industries with evidence - e.g., "Healthcare (mentioned in 3 case studies)", "Financial Services (reviews mention banks)"]
**Company Scale Indicators:**
- Employee range: [e.g., "50-500 based on customer logos"]
- Revenue indicators: [e.g., "Mid-market, $10M-100M ARR based on case studies"]
**Operational Context:** [Key processes, typical workflows, relevant technologies these companies use]
**Key Business Pains:** [Top 3-5 specific pains with evidence sources]
1. [Pain 1] - [Evidence: "mentioned in X reviews/cases"]
2. [Pain 2] - [Evidence: ...]
3. [Pain 3] - [Evidence: ...]

**Regulatory Environment:** [If applicable based on industry - e.g., "HIPAA for healthcare", "SOC 2 for SaaS companies"]

## Second Layer (ICP's Customers)
**ICP's Customer Industries:** [Who does the ICP sell to / serve?]
**Market Dynamics Affecting Them:** [Trends, economic factors, tech shifts affecting ICP's customers]
**External Triggers Creating ICP Urgency:** [Events/changes in ICP's customer base that create pain for ICP]

## Target Persona
**Job Title:** [SPECIFIC title - not generic. e.g., "VP of Operations" not just "Manager"]
**Key Responsibilities:** [Day-to-day workflow, what they actually do]
**Probable KPIs:** [What metrics are they measured on / care about?]
**Primary Pains & Frustrations:** [Specific challenges relevant to potential PVPs]
1. [Pain 1 - specific]
2. [Pain 2 - specific]
3. [Pain 3 - specific]

**Information Environment & Blind Spots:** [What info do they lack? Where might non-obvious data help?]
**Value Drivers:** [What kind of insights would genuinely impress or solve major problems for them?]

## Industry/Vertical for Data Discovery
**Primary Industry:** [The main industry vertical to focus data research on]
**Secondary Industry (if applicable):** [Alternative vertical if data is sparse]

## Research Quality Assessment
**ICP Specificity:** [HIGH / MEDIUM / LOW - how specific is the ICP profile?]
**Persona Detail:** [HIGH / MEDIUM / LOW - how detailed is persona understanding?]
**Evidence Quality:** [HIGH / MEDIUM / LOW - how strong is evidence for pains?]
**Data-Readiness:** [HIGH / MEDIUM / LOW - how well-positioned for data source discovery?]

**Gaps Identified:** [List any critical information gaps that need additional research]
**Confidence Level:** [Overall confidence in this research: HIGH / MEDIUM / LOW]
```

---

## Error Handling

**Website Requires JavaScript:**
- Primary: WebFetch fails on SPA
- Fallback: Use Browser MCP chrome_navigate + chrome_get_web_content
- Continue execution

**Company Information Sparse:**
- Primary: Direct website analysis
- Fallback: WebSearch for "[company name] company profile" "[company name] about"
- Minimum viable: Company name, core offering, one industry

**No Clear ICP:**
- Primary: Customer logos and case studies
- Fallback: Infer from product description and competitor analysis
- Document uncertainty in output

---

## Success Criteria

- [ ] Company name and core offering identified
- [ ] Business model inferred (SaaS/Marketplace/Service/Product)
- [ ] At least one specific industry identified for ICP
- [ ] At least 3 persona pains documented with evidence
- [ ] Target persona job title is SPECIFIC (not generic)
- [ ] Industry vertical identified for Wave 2 data discovery
- [ ] Overall quality assessment: MEDIUM or HIGH

---

**Progress Output:**
```
✅ Wave 1: Company intelligence gathered (15-20 parallel calls complete)
```
