---
description: Execute Blueprint GTM Intelligence System in 12-15 minutes using massive parallelization and live database discovery
allowed-tools: WebFetch, WebSearch, Read, Write, mcp__browser-mcp__chrome_navigate, mcp__browser-mcp__chrome_get_web_content, mcp__browser-mcp__get_windows_and_tabs, mcp__sequential-thinking__sequentialthinking
---

# Blueprint Turbo - Ultra-Fast GTM Intelligence System

Execute the complete Blueprint GTM methodology in **12-15 minutes** during a sales call using 4-wave parallel execution.

## Usage

```
/blueprint-turbo <company-url>
```

## Overview

This command orchestrates 4 waves of parallel execution:
- **Wave 1 (0-4 min):** 15-20 parallel company/market intelligence calls
- **Wave 2 (4-9 min):** Multi-modal data landscape scan (government + competitive + velocity)
- **Synthesis (9-11 min):** Sequential Thinking generates segments from AVAILABLE data
- **Wave 3 (11-14 min):** Message generation + calculation worksheets + buyer critique
- **Wave 4 (14-15 min):** HTML playbook assembly with data source citations

**Output:** `blueprint-gtm-playbook-[company-name].html` with 2 PQS + 2 PVP validated messages

**KEY CHANGE:** Data discovery now happens BEFORE segment generation (not after), ensuring segments are grounded in actually available data sources.

---

## Execution Flow

### WAVE 1: Explosive Intelligence Gathering (0-4 min)

**Objective:** Launch 15-20 parallel calls to gather ALL company/market/database intelligence

**Company Website Analysis (4-5 parallel WebFetch):**
$ARGUMENTS

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

**Market & ICP Research (6-8 parallel WebSearch):**

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

**Wave 1 Output:**
- Company context (offering, value prop, differentiators)
- ICP profile (industries, company scale, operational context)
- Target persona (title, responsibilities, KPIs, blind spots)
- Industry/vertical identified for Wave 2 data discovery

**Progress Hook:** "✅ Wave 1/4: Company intelligence gathered (15-20 parallel calls complete)"

---

### WAVE 2: Multi-Modal Data Landscape Scan (4-9 min)

**CRITICAL:** This wave executes BEFORE segment generation to ensure segments are grounded in actually available data.

**Objective:** Execute 15-20 parallel searches across ALL data categories to map what's available

**Data Discovery Categories:**

**CATEGORY A: Government/Regulatory Data (5-6 parallel searches)**

Execute these WebSearch queries IN PARALLEL:

1. WebSearch: "[industry] government database violations API"
2. WebSearch: "[industry] licensing board public records search"
3. WebSearch: "[industry] inspection records database field names"
4. WebSearch: "OSHA [industry] violation data downloadable"
5. WebSearch: "[industry] permit database API documentation"
6. WebSearch: "EPA [industry] compliance data public access"

Extract: Database URLs, API availability, field documentation links, update frequency

**CATEGORY B: Competitive Intelligence (4-5 parallel searches)**

Execute these WebSearch queries IN PARALLEL:

1. WebSearch: "[ICP industry] pricing data scraping tools"
2. WebSearch: "[competitive platform] review data extraction API"
3. WebSearch: "[ICP industry] menu pricing comparison API"
4. WebSearch: "scrape [platform] reviews [industry]"
5. WebSearch: "[industry] competitive analysis data sources"

Extract: Scraping methods, API availability, cost estimates, ToS restrictions

**CATEGORY C: Velocity Signals (4-5 parallel searches)**

Execute these WebSearch queries IN PARALLEL:

1. WebSearch: "Google Maps API review data documentation"
2. WebSearch: "review velocity tracking tools [industry]"
3. WebSearch: "website traffic estimation API affordable"
4. WebSearch: "[platform] review growth rate data"
5. WebSearch: "[industry] hiring velocity job posting data API"

Extract: API endpoints, rate limits, pricing, data freshness

**CATEGORY D: Tech/Operational Signals (3-4 parallel searches)**

Execute these WebSearch queries IN PARALLEL:

1. WebSearch: "BuiltWith API pricing technology detection"
2. WebSearch: "job posting API [industry] Indeed LinkedIn"
3. WebSearch: "[industry] tech stack data sources"
4. WebSearch: "DNS records API domain infrastructure"

Extract: API availability, coverage, pricing models

**Data Source Evaluation:**

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

**Feasibility Definitions:**

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

**Create Data Availability Report:**

Synthesize findings into structured report:

```
OWNER.COM EXAMPLE:

GOVERNMENT DATA:
- NYC DOHMH Restaurant Inspections (HIGH feasibility)
  URL: data.cityofnewyork.us/resource/43nn-pn8j.json
  Fields: CAMIS, DBA, BORO, INSPECTION_DATE, CRITICAL_FLAG, VIOLATION_CODE
  API: Free, daily updates
  Use case: Health violation triggers

COMPETITIVE INTELLIGENCE:
- Menu Pricing Scraping (MEDIUM feasibility)
  Method: Web scraping (restaurant site + DoorDash/Uber Eats)
  Cost: Manual free, Apify ~$200/mo for automation
  Fields: Item name, website price, platform price, markup %
  Use case: Commission pressure detection

VELOCITY SIGNALS:
- Google Maps Review Data (HIGH feasibility)
  API: maps.googleapis.com/maps/api/place/details/json
  Cost: Free tier generous, $X per 1000 requests after
  Fields: reviews[].time, reviews[].rating
  Use case: High-activity restaurant identification

TECH/OPERATIONAL:
- Website Tech Stack (MEDIUM feasibility)
  Method: Manual inspection or BuiltWith API
  Cost: Manual free, BuiltWith $295/mo
  Fields: Ordering system present/absent, tech platform
  Use case: Direct ordering infrastructure check
```

**Wave 2 Output:**
- 15-20 data sources evaluated across 4 categories
- Feasibility ratings for each source (HIGH/MEDIUM/LOW)
- Field documentation for HIGH feasibility sources
- Clear data availability report showing what's ACTUALLY accessible
- Cost and scalability constraints documented

**Progress Hook:** "🔍 Wave 2/4: Data landscape mapped (found [N] HIGH feasibility sources across government + competitive + velocity categories)"

---

### SYNTHESIS: Sequential Thinking MCP (9-11 min)

**CRITICAL CHANGE:** Sequential Thinking now receives the Data Availability Report from Wave 2 as INPUT.

**Objective:** Generate 2-3 segment hypotheses that COMBINE available data sources

**Execute Sequential Thinking:**

```
Invoke: mcp__sequential-thinking__sequentialthinking

Prompt: "I need to generate 2-3 pain-qualified segment hypotheses for [company name] using ONLY the data sources discovered in Wave 2.

CONTEXT FROM WAVE 1:
- Company: [name and core offering]
- ICP: [industries, company types, operational context]
- Target Persona: [job title, responsibilities, KPIs, blind spots]

DATA AVAILABILITY REPORT FROM WAVE 2:

GOVERNMENT DATA (HIGH feasibility sources):
[List discovered sources with fields]

COMPETITIVE INTELLIGENCE (HIGH/MEDIUM feasibility sources):
[List discovered methods with data points]

VELOCITY SIGNALS (HIGH feasibility sources):
[List discovered APIs with fields]

TECH/OPERATIONAL (discovered sources):
[List discovered methods]

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
- Whether inference is required (if yes, must be minimal and disclosed)"
```

**Synthesis Output:**
- 2-3 validated pain segment hypotheses
- Each segment uses ACTUAL data sources discovered in Wave 2
- Clear confidence levels based on data source types
- Texada Test validation for each segment
- Guidance on which should be PQS vs PVP messages

**Progress Hook:** "🧠 Synthesis: Generated [N] pain segments from available data sources (Sequential Thinking MCP complete)"

---

### WAVE 3: Message Generation + Buyer Critique (9-13 min)

**Objective:** Generate and validate 2 PQS + 2 PVP messages (≥7.0/10 for Strong PQS, ≥8.5/10 for TRUE PVP)

**Phase A: Message Generation + Calculation Worksheets**

For the TOP 2 HIGH feasibility segments, generate message variants:

**CRITICAL REQUIREMENT: Every message MUST include a Calculation Worksheet showing HOW data points were derived.**

**PQS Messages (Pain-Qualified Segment):**

Format requirements:
- **Subject:** 2-4 words only
- **Intro:** Exact data mirror with specific record numbers, dates, facility names
- **Insight:** Non-obvious synthesis the persona doesn't already know
- **Inquisition:** Low-effort question to spark reply
- **Length:** Under 75 words total
- **Data:** Must be PROVABLE (trace to actual database field)
- **Calculation Worksheet:** REQUIRED for every claim made in the message

Generate 2 PQS variants per HIGH segment (4 total PQS messages).

**Calculation Worksheet Format:**

For EVERY data claim in the message, document:

```
CLAIM: "[Exact claim from message]"

DATA SOURCE(S):
- Database: [name]
- Field(s): [exact field names]
- URL: [where to access]

CALCULATION:
- Raw data: [what you pull]
- Formula: [if any math/aggregation]
- Result: [what goes in message]

CONFIDENCE LEVEL:
- [90-95%] Pure government data, no inference
- [60-75%] Hybrid approach (gov + competitive + velocity)
- [50-70%] Velocity/competitive only

VERIFICATION:
"Prospect can verify by: [specific steps to check the data themselves]"
```

Example (EPA ECHO):
```
Subject: March 15 EPA Citation

Your facility at 1234 Industrial Parkway received EPA ECHO violation #987654321 on March 15, 2025 for three Clean Water Act exceedances (parameters: pH 9.2, TSS 180 mg/L). The consent decree milestone deadline is June 30, 2025—89 days out. Are you tracking remediation progress against this deadline internally, or would a external milestone tracker help?
```

**Calculation Worksheet for EPA ECHO Example:**

```
CLAIM 1: "Your facility at 1234 Industrial Parkway received EPA ECHO violation #987654321 on March 15, 2025"

DATA SOURCE(S):
- Database: EPA ECHO (Enforcement and Compliance History Online)
- Fields: FACILITY_ADDRESS, VIOLATION_ID, VIOLATION_DATE
- URL: echo.epa.gov/detailed-facility-report?fid=110000012345

CALCULATION:
- Raw data: Direct field values from ECHO API
- Formula: None (direct lookup)
- Result: Facility address, violation number, exact date

CONFIDENCE LEVEL: 95% (pure government data, verifiable record)

VERIFICATION: "Go to echo.epa.gov, search facility ID 110000012345, view violations tab"

---

CLAIM 2: "three Clean Water Act exceedances (parameters: pH 9.2, TSS 180 mg/L)"

DATA SOURCE(S):
- Database: EPA ECHO
- Fields: POLLUTANT_DESC, POLLUTANT_VALUE, POLLUTANT_UNIT
- URL: Same facility report, violations detail section

CALCULATION:
- Raw data: 3 rows in violations table with POLLUTANT_DESC values
- Formula: None (direct field values)
- Result: pH=9.2, TSS=180 mg/L, BOD=220 mg/L

CONFIDENCE LEVEL: 95% (government data, exact field values)

VERIFICATION: "Same facility report, expand violation #987654321, see parameters table"

---

CLAIM 3: "consent decree milestone deadline is June 30, 2025—89 days out"

DATA SOURCE(S):
- Database: EPA ECHO
- Fields: CONSENT_DECREE_DATE, MILESTONE_DEADLINE
- Manual: Date calculation from today

CALCULATION:
- Raw data: MILESTONE_DEADLINE = 2025-06-30
- Formula: Days between 2025-03-15 and 2025-06-30 = 107 days (should be updated to current date)
- Result: "89 days out" (from message send date)

CONFIDENCE LEVEL: 95% (government deadline + simple date math)

VERIFICATION: "Facility report > Consent Decrees tab > Milestone deadlines table"
```

**PVP Messages (Permissionless Value Proposition):**

Format requirements:
- **Subject:** Specific value being offered
- **Intro:** What you're giving them (specific, concrete)
- **Insight:** Why this matters to them specifically
- **Inquisition:** Who should receive this? (route to right person)
- **Length:** Under 100 words total
- **Value:** Must be immediately usable (no meeting required)
- **Calculation Worksheet:** REQUIRED for every data claim

Generate 2 PVP variants per HIGH segment (4 total PVP messages).

Example (CMS Geographic Variation):
```
Subject: Your County Utilization Benchmark

I pulled the 2022 CMS geographic variation data for your county—18.4 post-acute visits per 1,000 Medicare beneficiaries vs. state average of 28.1. That's bottom 15th percentile, which means either (1) your population is healthier, or (2) there's unmet need your competitors are capturing. I'll send the full 5-year trend if useful. Should this go to you or your market analytics lead?
```

**Calculation Worksheet for CMS Example:**

```
CLAIM 1: "18.4 post-acute visits per 1,000 Medicare beneficiaries"

DATA SOURCE(S):
- Database: CMS Geographic Variation Public Use File
- Fields: Bene_Geo_Lvl, Bene_Geo_Desc, VISITS_PER_1000_BENES
- URL: data.cms.gov/summary-statistics-on-use-and-payments/geographic-variation

CALCULATION:
- Raw data: Filter to Bene_Geo_Lvl='County' AND Bene_Geo_Desc='[County Name]'
- Formula: Direct field value from VISITS_PER_1000_BENES
- Result: 18.4

CONFIDENCE LEVEL: 95% (pure CMS data, exact field value)

VERIFICATION: "Download CSV from data.cms.gov, filter to your county, see column R (VISITS_PER_1000_BENES)"

---

CLAIM 2: "state average of 28.1"

DATA SOURCE(S):
- Database: Same CMS file
- Fields: Bene_Geo_Lvl, Bene_Geo_Desc, VISITS_PER_1000_BENES
- URL: Same

CALCULATION:
- Raw data: Filter to Bene_Geo_Lvl='State' AND Bene_Geo_Desc='[State Name]'
- Formula: Direct field value from VISITS_PER_1000_BENES
- Result: 28.1

CONFIDENCE LEVEL: 95% (pure CMS data)

VERIFICATION: "Same CSV, filter to your state row, see same column"

---

CLAIM 3: "bottom 15th percentile"

DATA SOURCE(S):
- Database: Same CMS file
- Manual: Percentile calculation

CALCULATION:
- Raw data: All county rows for same state (assume 50 counties)
- Formula: Sort VISITS_PER_1000_BENES ascending, find position of 18.4
- Result: County ranks 7th out of 50 = 14th percentile ≈ "bottom 15th percentile"

CONFIDENCE LEVEL: 90% (CMS data + manual percentile calc)

VERIFICATION: "Download full state data, sort by visits column, count position"
```

**Example Hybrid Approach (Owner.com - Competitive Intelligence + Velocity):**

```
Subject: Your DoorDash Commission Analysis

I tracked your menu pricing across your website vs. DoorDash over the past 30 days—average markup is 28.3% on 47 items, costing you an estimated $4,200/month in platform fees based on your 142 reviews/month velocity. Your signature burger ($14 on-site, $18 on DoorDash) alone represents ~$890/month in commissions. Worth exploring direct ordering to capture that margin?
```

**Calculation Worksheet for Owner.com Example:**

```
CLAIM 1: "average markup is 28.3% on 47 items"

DATA SOURCE(S):
- Method: Web scraping (restaurant website + DoorDash menu)
- Tools: Playwright/Selenium for automated menu extraction
- Fields: Item name, website price, DoorDash price

CALCULATION:
- Raw data: 47 menu items scraped from both sources
- Formula: For each item: (DoorDash_Price - Website_Price) / Website_Price
- Result: Average of 47 markup percentages = 28.3%

CONFIDENCE LEVEL: 65% (hybrid - requires scraping, not government data)
DISCLOSURE IN MESSAGE: "I tracked" (implies research done, not guaranteed 100% accuracy)

VERIFICATION: "Manually compare 5-10 items on your website vs. DoorDash app"

---

CLAIM 2: "costing you an estimated $4,200/month in platform fees"

DATA SOURCE(S):
- Competitive: Menu pricing data (above)
- Velocity: Google Maps review rate (see below)
- Industry: Standard DoorDash commission rate (25-30%, public knowledge)

CALCULATION:
- Raw data: 142 reviews/month × industry avg 3% review rate = ~4,733 monthly orders
- Formula: 4,733 orders × avg ticket $18 × 28.3% markup ÷ 1.283 = $4,187/month
- Result: "estimated $4,200/month"

CONFIDENCE LEVEL: 60% (multiple inference layers - uses review velocity proxy + assumed ticket size)
DISCLOSURE IN MESSAGE: "estimated" (clear this is calculated, not exact)

VERIFICATION: "Compare your actual monthly DoorDash statement if available"

---

CLAIM 3: "142 reviews/month velocity"

DATA SOURCE(S):
- Database: Google Maps Places API
- Fields: reviews[].time (UNIX timestamp array)
- URL: maps.googleapis.com/maps/api/place/details/json?place_id=[ID]

CALCULATION:
- Raw data: Last 200 reviews with timestamps
- Formula: Filter to reviews in last 30 days, count unique reviews
- Result: 142 reviews in past 30 days

CONFIDENCE LEVEL: 85% (API data, but review rate ≠ order rate - proxy only)
DISCLOSURE IN MESSAGE: None needed - stating verifiable fact about review velocity

VERIFICATION: "Check your Google Business Profile > Reviews, filter to last 30 days"

---

CLAIM 4: "signature burger ($14 on-site, $18 on DoorDash)"

DATA SOURCE(S):
- Method: Manual menu comparison (specific example)
- Fields: Item name, prices from both sources

CALCULATION:
- Raw data: Direct observation of one menu item
- Formula: None (direct comparison)
- Result: $14 vs $18

CONFIDENCE LEVEL: 95% (directly verifiable right now)

VERIFICATION: "Open your website menu and DoorDash app side-by-side"

---

OVERALL MESSAGE CONFIDENCE: 60-70% (hybrid approach disclosed with "tracked," "estimated," "based on")
```

**Phase A.5: Action Extraction & Completeness Check (For PVP Classification)**

**CRITICAL:** Before running buyer critique, check if PVP messages contain COMPLETE actionable information.

**Objective:** Classify messages as TRUE PVP (8.5+ target) vs Strong PQS (7.0-8.4 target) based on completeness.

**The "Independently Useful" Test:**

For EACH of the 4 PVP candidate messages, perform this check:

**Step 1: Identify the Intended Action**

Ask: "What specific action can the recipient take from this message ALONE (without replying)?"

Valid actions:
- Call a specific person (requires: name, phone/email)
- Contact a vendor (requires: company name, contact info, pricing)
- Visit/attend a location (requires: address, date/time)
- Change a process (requires: specific steps, benchmarks, tools/vendors)
- Purchase from supplier (requires: supplier name, product specs, price, contact)

NON-actions (pain description only):
- "Consider your challenges" → No action
- "Think about this issue" → No action
- "Be aware of this trend" → No action

**Step 2: Check Information Completeness**

For the identified action, verify the message contains:

**If action = Call specific person:**
- [ ] Person's name
- [ ] Phone number OR email address
- [ ] Context (why call them)

**If action = Contact vendor/supplier:**
- [ ] Vendor/company name
- [ ] Product/service specifics
- [ ] Price or pricing range
- [ ] Phone/email/website

**If action = Change process:**
- [ ] Current benchmark/metric
- [ ] Target benchmark/metric
- [ ] Specific steps to implement
- [ ] Tools/vendors with contacts (if needed)

**If action = Visit/attend location:**
- [ ] Specific address or addresses
- [ ] Date/time OR "starting when"
- [ ] What to do there

**Step 3: Classification Verdict**

**CLASSIFY AS TRUE PVP (Target score: 8.5+/10):**
- ✅ Clear action identified
- ✅ ALL required information present in message
- ✅ Recipient can act WITHOUT replying
- ✅ Passes "Independently Useful Test"
- Keep as PVP, critique with 8.5+ threshold

**RECLASSIFY AS STRONG PQS (Target score: 7.0-8.4/10):**
- ✅ Identifies pain with data
- ❌ Missing 1+ pieces of action information
- ❌ Recipient would need to reply for details
- ❌ Fails "Independently Useful Test"
- This is NOT a failure - strong PQS is valuable!
- Reclassify as PQS, critique with 7.0-8.4 threshold

**Examples:**

**PASSES as TRUE PVP (Floorzap):**
```
Subject: floor order

Did you see that 18904 Bajo Dr, Edmond, OK 73012 just sold on October 22nd?

The listing mentioned that the seller is offering a $2,000 flooring credit with an acceptable offer. This suggests there might be some flooring work needed in the home.

P.S. The listing agent was Sheila Gibbs. You can reach her at sheila@gibbshomesales.com or 405-532-3212.
```
✅ Action: Call agent about flooring work
✅ Complete info: Agent name, email, phone, property address
✅ Verdict: TRUE PVP (target 8.5+)

**FAILS as PVP, RECLASSIFY as PQS (Wingwork Mechanic Shortage):**
```
Subject: 5,338 Mechanic Shortage

ATEC's 2025 workforce report shows a 5,338 A&P mechanic shortage nationwide. Your 7-aircraft mixed-fleet operation across 4 manufacturer types compounds this—each new hire needs training across King Air, Citation, Pilatus, and Caravan systems vs. single-type operators.

How are you managing maintenance capacity with current staffing?
```
❌ Action: Describes hiring problem but provides no hiring solution
❌ Missing: WHO to recruit, WHERE to find them, HOW to contact them
✅ Strong pain identification with data
✅ Verdict: RECLASSIFY as STRONG PQS (target 7.5-8.0)

**How to Fix into TRUE PVP:**
Would need to add:
- Specific mechanic names/LinkedIn profiles
- Current employers
- Contact information
- Salary premium data with specific range

**Phase A.5 Output:**
- Each of 4 PVP candidates classified as TRUE PVP or RECLASSIFIED as Strong PQS
- Documented what action is/isn't available
- Documented what information is missing (if reclassified)
- Adjusted target scores: TRUE PVP = 8.5+, Strong PQS = 7.0-8.4

**Realistic Expectations:**
- Most verticals will generate 0-2 TRUE PVPs (8.5+)
- Generating 3-4 STRONG PQS (7.5-8.4) is excellent outcome
- Don't force PVPs - honest classification maintains methodology integrity

**Phase B: Buyer Critique (Extended Thinking Enabled)**

Load methodology.md buyer critique rubric.

**Formal Persona Adoption:**

```
"I am now [Job Title from persona research]. I work at [typical ICP company].

My responsibilities: [from persona research]
My KPIs: [from persona research]
My daily challenges: [from persona research]

I receive 50+ sales emails per day. I delete 95% without reading. I only respond to emails that:
1. Mirror an exact situation I'm in RIGHT NOW
2. Contain data I can verify and don't already have
3. Offer a non-obvious insight I haven't considered
4. Require minimal effort to reply

I am NOT a marketer evaluating this message. I AM THE BUYER. Would I reply to this? If 'maybe'—that's a NO."
```

**Score Each Message (0-10 on 5 Criteria):**

For each of the 8 generated messages:

1. **Situation Recognition (0-10):** Does this mirror my EXACT current situation with specific details? Generic = 0, Hyper-specific = 10

2. **Data Credibility (0-10):** Can I verify this data? Is it from a trusted source? Are field names/record numbers real? Assumed data = 0, Verified provable = 10

3. **Insight Value (0-10):** Is this a non-obvious synthesis I don't already know? Obvious = 0, Revelation = 10

4. **Effort to Reply (0-10):** How easy is it to respond? High friction = 0, One-word answer = 10

5. **Emotional Resonance (0-10):** Does this trigger urgency or curiosity? Meh = 0, Must investigate = 10

**Average Score:** Sum of 5 criteria ÷ 5 = Final Score

**Apply Texada Test:**

For each message, verify:
- ✅ **Hyper-specific:** Contains dates, record numbers, facility addresses, specific field values (not "recent," "many," "some")?
- ✅ **Factually grounded:** Every claim traces to a documented data source from Wave 2 (government database, competitive scrape, velocity API) with calculation worksheet showing HOW it was derived?
- ✅ **Non-obvious synthesis:** Insight the persona doesn't already have access to (not just repeating what they know)?

**Verdict (Adjusted for TRUE PVP vs Strong PQS):**

**For TRUE PVP messages (from Phase A.5):**
- **KEEP:** Average score ≥8.5 AND passes all 3 Texada Test criteria
- **REVISE:** Average score 7.0-8.4 OR fails 1-2 Texada criteria
- **DESTROY:** Average score <7.0 OR fails all Texada criteria OR contains soft signals

**For STRONG PQS messages (reclassified from Phase A.5 OR original PQS):**
- **KEEP:** Average score ≥7.0 AND passes all 3 Texada Test criteria
- **REVISE:** Average score 6.0-6.9 OR fails 1-2 Texada criteria
- **DESTROY:** Average score <6.0 OR fails all Texada criteria OR contains soft signals

**Important Notes:**
- TRUE PVPs have HIGHER bar (8.5+) because they deliver complete action
- Strong PQS messages (7.0-8.4) are EXCELLENT and valuable
- Don't force weak messages to be PVPs - honest classification is critical

**Phase C: Single Revision Cycle**

For messages rated REVISE:
1. Identify specific weaknesses (which criteria scored poorly? which Texada test failed?)
2. Generate ONE revised version addressing those weaknesses
3. Re-critique using same rubric
4. New verdict based on classification:
   - TRUE PVP: KEEP (≥8.5) or DESTROY (<7.0)
   - Strong PQS: KEEP (≥7.0) or DESTROY (<6.0)

**NO second revision.** Extended thinking should ensure high first-pass quality.

**Phase D: Final Selection**

**Realistic Target (Adjusted for TRUE PVP rarity):**

**Ideal Case (Data-Rich Verticals):**
- 1-2 TRUE PVPs (≥8.5/10, complete actionable info)
- 2-3 Strong PQS (≥7.0/10, excellent pain identification)

**Typical Case (Most Verticals):**
- 0-1 TRUE PVPs (≥8.5/10, if complete action data available)
- 3-4 Strong PQS (≥7.0/10, excellent pain identification)

**Challenging Case (Operational Pain Only):**
- 0 TRUE PVPs (no public action data available)
- 2-4 Strong PQS (≥7.0/10, best possible with available data)

**Selection Process:**

1. Count TRUE PVPs: How many messages scored ≥8.5 AND passed Independently Useful Test?
2. Count Strong PQS: How many messages scored 7.0-8.4?
3. Select best 4 messages total (any mix of TRUE PVP and Strong PQS)

**Minimum Quality Gate:**
- Must have at least 4 messages scoring ≥7.0/10
- At least 2 must be from different segments
- If <4 messages at 7.0+, generate 2 more variants and critique (add +2 min)

**Classification Labeling:**

In HTML output, clearly label each message:
- **"TRUE PVP" (8.5+):** Complete actionable information, independently useful
- **"Strong PQS" (7.5-8.4):** Excellent pain identification, seeks engagement
- **"Solid PQS" (7.0-7.4):** Good pain identification with disclosed limitations

**Wave 3 Output:**
- 0-2 TRUE PVP messages (≥8.5/10) - if complete action data available
- 2-4 Strong PQS messages (≥7.0/10) - pain identification
- Total: 4 messages minimum
- Calculation worksheets for ALL messages showing data sources, formulas, confidence levels
- All data claims verified PROVABLE (trace to specific sources from Wave 2)
- Buyer critique scores and rationale documented
- Honest classification: TRUE PVP vs Strong PQS vs Solid PQS

**Progress Hook:** "📝 Wave 3/4: Messages validated ([N] TRUE PVPs at 8.5+, [N] Strong PQS at 7.0-8.4)"

---

### WAVE 4: HTML Playbook Assembly (13-15 min)

**Objective:** Fast template population and output delivery

**Load Template:**

Read: `.claude/skills/blueprint-turbo/templates/html-template.html`

**Extract Company Data:**

From Wave 1 research:
- Company name
- Core offering (1-2 sentences)
- ICP description (industries, company types)
- Target persona (job title, responsibilities)

**Create "Old Way" Example:**

Generate a realistic bad SDR email example showing generic outreach:

```
Subject: Quick Question about [Company Name]

Hi [Persona First Name],

I noticed on LinkedIn that [Company Name] recently [generic event like expanded or hired]. Congrats on the growth!

I wanted to reach out because we work with companies like [Competitor 1] and [Competitor 2] to help with [generic pain point].

Our platform [feature 1], [feature 2], and [feature 3]. We've helped companies achieve [generic metric improvement].

Would you have 15 minutes next week to explore how we might be able to help [Company Name]?

Best,
Generic SDR
```

**Populate Template Sections:**

1. **Title & Bio:** Keep Jordan's bio unchanged (already in template)

2. **The Old Way:** Insert the bad SDR email example with explanation of why it fails

3. **The New Way:** Keep explanation of hard data vs soft signals, PQS vs PVP (already in template)

4. **PQS Plays Section:**
   - Insert 2 PQS play cards (one per segment)
   - For each card populate:
     - Play title (segment name)
     - Play explanation (what trigger event this targets)
     - Why it works (buyer critique insights—what score it received and why)
     - Data source (database/API/method name, key fields, confidence level)
     - Full message text (the actual PQS message)
     - Calculation worksheet summary (how each claim was derived)

5. **PVP Plays Section:**
   - Insert 2 PVP play cards (one per segment)
   - Same structure as PQS cards (including calculation worksheets)

6. **The Transformation:** Keep philosophical summary (already in template)

**Critical Formatting Rule:**

NO line breaks within sentences. Let browser wrap text naturally.

❌ Wrong:
```
Your facility at 1234 Industrial Parkway received
EPA violation #987654321 on March 15, 2025
for three violations.
```

✅ Right:
```
Your facility at 1234 Industrial Parkway received EPA violation #987654321 on March 15, 2025 for three violations.
```

**Write Output:**

Generate filename: `blueprint-gtm-playbook-[company-name-slug].html`

Example: `blueprint-gtm-playbook-constant-therapy.html`

Write complete HTML file with:
- All placeholders replaced
- 2 PQS + 2 PVP play cards fully populated
- Mobile-responsive Blueprint brand styling
- File size under 2MB
- Self-contained (inline CSS, no external dependencies)

**Wave 4 Output:**
- Complete HTML playbook with 2 PQS + 2 PVP plays
- Each play includes calculation worksheets showing data provenance
- Confidence levels disclosed for hybrid approaches (60-75%)
- File path returned to user
- Ready to send to prospect immediately

---

### Wave 4.5: Automatic GitHub Pages Publishing (1-2 min)

**Objective:** Automatically commit and push playbook to GitHub, generate shareable URL

**Important:** This step executes automatically after HTML write. If git operations fail, gracefully skip and output local file path only.

Execute these steps sequentially:

**Step 1: Verify Git Repository**
```bash
git rev-parse --git-dir 2>/dev/null
```

- If command succeeds → Continue to Step 2
- If command fails (not a git repo) → Skip publishing, output warning:
  ```
  ⚠️  No git repository detected. Skipping GitHub Pages publish.
  💾 Local file: [filename]

  To enable auto-publishing, initialize git:
  git init && gh repo create blueprint-gtm-playbooks --public --source=. --remote=origin
  ```
  Then end execution.

**Step 2: Extract GitHub Remote Information**
```bash
git config --get remote.origin.url
```

Parse the result to extract:
- GitHub username (e.g., "SantaJordan")
- Repository name (e.g., "blueprint-gtm-playbooks")

Use this logic:
- If URL format is `https://github.com/[username]/[repo].git` → Extract username and repo
- If URL format is `git@github.com:[username]/[repo].git` → Extract username and repo
- If no remote found → Skip publishing, output warning and local file path

**Step 3: Commit and Push Playbook**

Execute these git commands sequentially:

```bash
# Add the HTML file
git add [filename]

# Create commit with timestamp
git commit -m "Publish playbook: [company-name] ($(date +"%Y-%m-%d %H:%M:%S"))"

# Push to GitHub (try main first, fallback to master)
git push origin main 2>/dev/null || git push origin master 2>/dev/null
```

**Error Handling:**
- If git add fails → Output error, skip to local file output
- If git commit fails (e.g., nothing to commit) → That's OK, continue (file was already committed in initial setup)
- If git push fails → Output error, but still generate and show the URL (might already be published)

**Step 4: Generate GitHub Pages URL**

Construct the URL:
```
https://[username].github.io/[repo-name]/[filename]
```

Example:
```
https://santajordan.github.io/blueprint-gtm-playbooks/blueprint-gtm-playbook-mirrorweb.html
```

**Step 5: Output Final Results**

**Success Case (git operations succeeded):**
```
✅ Wave 4/4: HTML playbook published!

📎 Shareable URL:
   https://[username].github.io/[repo-name]/[filename]

💾 Local file: [filename]

Note: GitHub Pages may take 1-2 minutes to build. If URL doesn't work immediately, wait a moment and refresh.
```

**Failure Case (git operations failed):**
```
✅ Wave 4/4: HTML playbook generated!

💾 Local file: [filename]

⚠️  GitHub Pages publishing failed. To publish manually:
   ./publish-playbook.sh [filename]
```

**Wave 4.5 Output:**
- HTML file committed to git repository
- Changes pushed to GitHub
- GitHub Pages URL generated and displayed
- User has instant shareable link

**Progress Hook:** See Step 5 above for dynamic output based on success/failure

---

## Error Handling & Fallbacks

**Website Requires JavaScript:**
- Primary: WebFetch fails on SPA
- Fallback: Use Browser MCP chrome_navigate + chrome_get_web_content
- Continue execution

**Zero HIGH Feasibility Segments:**
- Primary: Reject, suggest alternative segments
- Fallback 1: Use top MEDIUM segment with disclaimer in HTML
- Fallback 2: Widen to adjacent industries, research 2 more databases (+3 min)
- Hard failure: Cannot proceed to Wave 3 without data

**Browser MCP Unavailable:**
- Primary: Parallel browser tabs
- Fallback: Sequential WebFetch/WebSearch (slower but functional)
- Increases Wave 2 time from 3 min → 6 min (still faster than original)

**All Messages Score <7.0:**
- Primary: DESTROY segment, document why it failed
- Fallback: Generate 2 additional variants per segment, critique again (+2 min)
- Hard limit: If still failing after 2nd attempt, this segment is not viable with available data

**Database Portal Down:**
- Primary: Extract live from portal
- Fallback 1: WebSearch for cached API docs, field references
- Fallback 2: Skip to alternative database for same segment
- Continue with available data

---

## Execution Checklist

Before running `/blueprint-turbo <url>`:

- [ ] Browser MCP server configured and Chrome available
- [ ] Sequential Thinking MCP server installed
- [ ] Permission mode set to auto-accept OR tools pre-approved
- [ ] Company URL is valid and accessible
- [ ] 12-15 minutes available for uninterrupted execution

After completion, verify:

- [ ] HTML file exists at output path
- [ ] File contains 2 PQS + 2 PVP play cards
- [ ] All data claims trace to specific database fields
- [ ] All messages scored ≥7.0/10 in buyer critique (Strong PQS) or ≥8.5/10 (TRUE PVP)
- [ ] No placeholders remain in HTML
- [ ] File size <2MB

---

## Notes

**Performance:**
- Best case: 10-12 minutes (parallel calls complete quickly)
- Target case: 12-15 minutes (realistic with network latency)
- Worst case: 15-18 minutes (if fallbacks triggered)

**Quality vs Speed:**
- Core standards maintained (7.0+ for Strong PQS, 8.5+ for TRUE PVP, HIGH feasibility, actual fields)
- Acceptable trade-offs (2 segments vs 3-5, 1 revision vs 2)
- Extended thinking compensates for reduced iteration

**Sales Call Optimization:**
- Real-time progress hooks show wave completion
- No approval prompts during execution
- Predictable timing allows confident scheduling
- Immediate HTML deliverable to send prospect

$ARGUMENTS
