# Wave 2: Multi-Modal Data Landscape Scan

**Objective:** Execute 15-20 parallel searches across ALL data categories to map what's available

**Time:** 4-9 minutes

**Input:**
- Industry/vertical from Wave 1
- ICP profile and persona from Wave 1
- Pain points identified in Wave 1

**Output:** Comprehensive data source catalog with feasibility ratings

---

## CRITICAL

This wave executes BEFORE segment generation to ensure segments are grounded in actually available data.

---

## Data Discovery Categories

### CATEGORY A: Government/Regulatory Data (5-6 parallel searches)

Execute these WebSearch queries IN PARALLEL:

1. WebSearch: "[industry] government database violations API"
2. WebSearch: "[industry] licensing board public records search"
3. WebSearch: "[industry] inspection records database field names"
4. WebSearch: "OSHA [industry] violation data downloadable"
5. WebSearch: "[industry] permit database API documentation"
6. WebSearch: "EPA [industry] compliance data public access"

Extract: Database URLs, API availability, field documentation links, update frequency

### CATEGORY B: Competitive Intelligence (4-5 parallel searches)

Execute these WebSearch queries IN PARALLEL:

1. WebSearch: "[ICP industry] pricing data scraping tools"
2. WebSearch: "[competitive platform] review data extraction API"
3. WebSearch: "[ICP industry] menu pricing comparison API"
4. WebSearch: "scrape [platform] reviews [industry]"
5. WebSearch: "[industry] competitive analysis data sources"

Extract: Scraping methods, API availability, cost estimates, ToS restrictions

### CATEGORY C: Velocity Signals (4-5 parallel searches)

Execute these WebSearch queries IN PARALLEL:

1. WebSearch: "Google Maps API review data documentation"
2. WebSearch: "review velocity tracking tools [industry]"
3. WebSearch: "website traffic estimation API affordable"
4. WebSearch: "[platform] review growth rate data"
5. WebSearch: "[industry] hiring velocity job posting data API"

Extract: API endpoints, rate limits, pricing, data freshness

### CATEGORY D: Tech/Operational Signals (3-4 parallel searches)

Execute these WebSearch queries IN PARALLEL:

1. WebSearch: "BuiltWith API pricing technology detection"
2. WebSearch: "job posting API [industry] Indeed LinkedIn"
3. WebSearch: "[industry] tech stack data sources"
4. WebSearch: "DNS records API domain infrastructure"

Extract: API availability, coverage, pricing models

---

## Data Source Evaluation

For EACH discovered source, document:

```
Source Name: [e.g., "NYC DOHMH Restaurant Inspections"]
Category: [Government / Competitive / Velocity / Tech]
URL: [database or API endpoint]
API Available: [Yes/No/Via 3rd Party]
Cost: [Free / $X per month / Usage-based]
Update Frequency: [Real-time / Daily / Weekly / Monthly]
Key Fields: [List documented field names if found]
Reliability: [High/Medium/Low - based on source type]
Scalability: [High/Medium/Low - based on rate limits, ToS]
Feasibility Rating: [HIGH / MEDIUM / LOW / UNDETECTABLE]
```

### Feasibility Definitions

**HIGH Feasibility:**
- API exists OR stable web scraping target
- Free or <$500/month for target volume
- Documented field names available
- Daily or better update frequency
- No major ToS restrictions
- Specific data fields match segment needs

**MEDIUM Feasibility:**
- Manual access or expensive API ($500-2000/month)
- Field documentation sparse (need to reverse engineer)
- Weekly/monthly updates
- Some ToS gray areas
- Partial field match to segment needs

**LOW Feasibility:**
- Manual only, no automation possible
- Prohibitively expensive (>$2000/month)
- Poor/no documentation
- Rare updates (quarterly, annual)
- High ToS violation risk
- Fields don't match segment needs

---

## Output Format

Return a structured Data Availability Report:

```markdown
# Data Landscape Report for [Company Name]

## Summary
**Total Sources Discovered:** [N]
**HIGH Feasibility Sources:** [N]
**MEDIUM Feasibility Sources:** [N]
**LOW Feasibility Sources:** [N]

## GOVERNMENT/REGULATORY DATA

### Source 1: [Name]
**Feasibility:** HIGH / MEDIUM / LOW
**URL:** [Link to database or API docs]
**API Available:** Yes/No/Via 3rd Party ([platform name])
**Cost:** [Free / $X/month / Usage-based details]
**Update Frequency:** [Real-time / Daily / Weekly / Monthly]
**Key Fields:** [Field names if documented - e.g., "CAMIS, DBA, BORO, INSPECTION_DATE, CRITICAL_FLAG, VIOLATION_CODE"]
**Reliability:** [High/Medium/Low]
**Scalability:** [High/Medium/Low]
**Potential Use Cases:** [How this maps to persona pains from Wave 1]

[Repeat for each government source]

## COMPETITIVE INTELLIGENCE

### Source N: [Name]
**Feasibility:** HIGH / MEDIUM / LOW
**Method:** [API / Web Scraping / Manual]
**Platform:** [If scraping: Apify / Manual / Custom]
**Cost:** [Details]
**Data Points:** [What specific data can be extracted]
**ToS Considerations:** [Any restrictions or risks]
**Potential Use Cases:** [How this maps to persona pains]

[Repeat for each competitive source]

## VELOCITY SIGNALS

### Source N: [Name]
**Feasibility:** HIGH / MEDIUM / LOW
**API:** [Endpoint if available]
**Cost:** [Details, including free tier info]
**Fields:** [Available data fields]
**Rate Limits:** [Calls/day or calls/month]
**Potential Use Cases:** [How this maps to persona pains]

[Repeat for each velocity source]

## TECH/OPERATIONAL SIGNALS

### Source N: [Name]
**Feasibility:** HIGH / MEDIUM / LOW
**Method:** [API / Manual inspection / Other]
**Cost:** [Details]
**Coverage:** [What can be detected]
**Potential Use Cases:** [How this maps to persona pains]

[Repeat for each tech source]

## Data Source Recommendations

**Highest Priority Sources (HIGH feasibility + high relevance):**
1. [Source name] - [Why it's high priority for this ICP]
2. [Source name] - [Why it's high priority]
3. [Source name] - [Why it's high priority]

**Worth Investigating (MEDIUM feasibility but high value):**
1. [Source name] - [Why worth the investment]
2. [Source name] - [Why worth the investment]

**Not Recommended (LOW feasibility):**
1. [Source name] - [Why not feasible]

## Gap Analysis

**Missing Data Categories:**
- [Category 1] - [What we hoped to find but couldn't]
- [Category 2] - [What we hoped to find but couldn't]

**Recommendations for Additional Research:**
- [Specific area to research more deeply]
- [Alternative industry angle to explore]

## Data Landscape Quality Assessment

**Government Data Availability:** HIGH / MEDIUM / LOW
**Competitive Data Availability:** HIGH / MEDIUM / LOW
**Velocity Data Availability:** HIGH / MEDIUM / LOW
**Tech/Operational Data Availability:** HIGH / MEDIUM / LOW

**Overall Data Richness:** [EXCELLENT / GOOD / MODERATE / POOR]

**Readiness for PVP Generation:** [HIGH / MEDIUM / LOW]
- Justification: [Why this rating - what's available or missing]
```

---

## Error Handling

**Database Portal Down:**
- Primary: Extract live from portal
- Fallback 1: WebSearch for cached API docs, field references
- Fallback 2: Skip to alternative database for same segment
- Continue with available data

**Zero HIGH Feasibility Sources:**
- Primary: Reject, suggest alternative segments
- Fallback 1: Use top MEDIUM sources with disclaimer
- Fallback 2: Widen to adjacent industries, research 2 more databases (+3 min)
- Document limitations clearly in output

**Generic Industry (Hard to Categorize):**
- Primary: Focus on operational signals (hiring, tech stack, velocity)
- Fallback: Research multiple adjacent industries in parallel
- Minimum viable: At least 3 MEDIUM+ feasibility sources

---

## Success Criteria

- [ ] At least 15 data sources researched across all 4 categories
- [ ] At least 3 HIGH feasibility sources identified
- [ ] Field names documented for top sources
- [ ] Cost and API availability documented
- [ ] Sources mapped to specific persona pains from Wave 1
- [ ] Clear prioritization and recommendations provided
- [ ] Overall data landscape quality: GOOD or better

---

**Progress Output:**
```
🔍 Wave 2: Data landscape mapped (found [N] HIGH feasibility sources across government + competitive + velocity categories)
```
