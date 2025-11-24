# Internal Data Inference Framework

**Purpose:** Infer what internal operational data the sender company MUST have, and determine what can be ethically aggregated to create powerful PVPs.

**Key Insight:** Internal data creates PVPs that competitors can't replicate. If sender has 100+ customers, aggregated benchmarks become a unique competitive advantage.

---

## Core Principles

### 1. Operational Necessity
**If the business can't function without tracking it, they HAVE that data.**

Examples:
- SaaS company MUST track: user logins, feature usage, churn, MRR
- Marketplace MUST track: transactions, seller performance, buyer behavior
- Service business MUST track: job completion times, materials used, customer locations

### 2. Ethical Aggregation
**Data can be aggregated if it's impossible to identify any single customer.**

✅ **SAFE to aggregate:**
- Averages across 10+ customers
- Percentile rankings (top 10%, bottom 25%)
- Geographic trends (city/state level with 5+ customers)
- Time-based trends (month-over-month changes)
- Category benchmarks (by industry, company size, etc.)

❌ **UNSAFE to aggregate (identifying information):**
- Individual customer names, addresses, contact info
- Data from <5 customers in a segment
- Exact transaction amounts for specific customers
- Any PII (Personally Identifiable Information)

### 3. Persona Pain Mapping
**Internal data is only valuable if it addresses a specific persona pain.**

Process:
1. Identify persona pain from Wave 1 research
2. Determine what internal data would solve/quantify that pain
3. Verify sender would have that data (operational necessity)
4. Verify it can be aggregated ethically
5. Design PVP message format

---

## Business Model Analysis

Use sender's business model to infer data they MUST have:

### SaaS / Software Platform

**Operational Data They MUST Have:**
- Customer count & segmentation (by plan, industry, size)
- Feature usage metrics (which features used, frequency)
- User login/activity metrics (DAU/MAU)
- Churn rate & reasons
- Support ticket volume & resolution time
- NPS/CSAT scores
- Product adoption timeline (time to value)
- Integration usage (which tools customers connect)

**Aggregatable into PVPs:**
- ✅ "Top 10% of [persona type] users spend 4.2 hours/week in [feature] vs avg of 1.8 hours"
- ✅ "Companies that adopt [feature] within 30 days have 43% lower churn"
- ✅ "Average time-to-value in [industry] is 67 days, vs 45 days for top performers"
- ✅ "[Tool] integration users see 2.3x higher engagement"

**Maps to Common Pains:**
- Low feature adoption → Show benchmarks for successful users
- High churn → Show retention patterns of successful cohorts
- Slow time-to-value → Show adoption timelines by persona/industry

### Marketplace / Platform

**Operational Data They MUST Have:**
- Transaction volume & GMV (gross merchandise value)
- Seller/provider performance metrics (ratings, completion rates)
- Buyer/customer behavior (purchase frequency, cart size)
- Geographic distribution (where transactions happen)
- Category performance (which products/services sell best)
- Pricing data (what sellers charge, what buyers pay)
- Time-to-first-transaction (seller activation)
- Repeat transaction rates

**Aggregatable into PVPs:**
- ✅ "Top 20% of [seller type] in [city] charge $45-62 vs market avg of $38"
- ✅ "Sellers who respond within 2 hours book 3.8x more jobs"
- ✅ "[Service category] demand up 67% in [region] over last 90 days"
- ✅ "Average order value for [customer segment] is $127 in [season]"

**Maps to Common Pains:**
- Pricing uncertainty → Show market pricing benchmarks
- Low booking rate → Show response time benchmarks
- Market demand → Show regional/seasonal trends

### Service Business Software

**Operational Data They MUST Have:**
- Job/project count & status
- Service delivery times (scheduled vs actual)
- Materials/resource usage per job
- Customer locations (for routing/scheduling)
- Pricing per job type
- Technician/crew performance
- Customer satisfaction scores
- Repeat business rates
- Invoice amounts & payment timing

**Aggregatable into PVPs:**
- ✅ "Top quartile [service pros] complete [job type] in 2.3 hours vs avg 3.8 hours"
- ✅ "Average [material] usage for [job type] is 4.2 lbs in [region]"
- ✅ "Optimal pricing for [service] in [zip code] is $145-180 based on 847 jobs"
- ✅ "[Customer segment] books repeat service every 42 days on average"

**Maps to Common Pains:**
- Pricing strategy → Show market pricing by region/job type
- Efficiency benchmarks → Show completion time leaders
- Resource planning → Show materials usage patterns

### E-commerce / Retail Software

**Operational Data They MUST Have:**
- Product catalog & SKUs
- Inventory levels & turnover
- Order volume & AOV (average order value)
- Customer purchase frequency
- Returns & refund rates
- Shipping times & costs
- Seasonal trends
- Product category performance
- Customer lifetime value

**Aggregatable into PVPs:**
- ✅ "Top 15% of [product category] sellers maintain 12-day inventory turns vs avg 28 days"
- ✅ "Average AOV for [customer segment] increased 34% after [strategy]"
- ✅ "[Product type] sales peak at 2.4x baseline during [season] in [region]"
- ✅ "Free shipping threshold of $75-85 optimal for [category] (data from 2,400 stores)"

**Maps to Common Pains:**
- Inventory management → Show turnover benchmarks
- Pricing/promotions → Show AOV optimization data
- Seasonal planning → Show demand trends

---

## Inference Process (Step-by-Step)

### Step 1: Analyze Sender's Business Model

From Wave 1 company research:
- What is their core product/service?
- How do they make money?
- Who are their customers?
- What operational processes must they track?

**Output:** Business model category (SaaS / Marketplace / Service / E-commerce / Other)

### Step 2: Map Operational Necessities

Ask: "What data MUST they collect for their business to function?"

Use the business model templates above as starting point.

**Output:** List of 10-15 operational data types sender definitely has

### Step 3: Cross-Reference with ICP Pains

From Wave 1 persona research, identify top 3-5 pains.

For each pain, ask:
- What internal data would quantify or solve this pain?
- Does that data appear in our operational necessities list?
- Can it be aggregated across customers?

**Output:** 5-10 internal data types that map to persona pains

### Step 4: Design Aggregation Approach

For each relevant data type:
- **Aggregation method:** Average / Median / Percentile / Trend / Comparison
- **Segmentation:** By industry / company size / geography / time period
- **Minimum n:** How many customers needed for ethical aggregation? (typically 10+)
- **Confidence level:** How certain are we sender has this data? (High / Medium / Low)

**Output:** Aggregation strategy for each internal data type

### Step 5: Construct PVP Concepts

For each aggregatable data type:
- **Data insight:** What the aggregated data shows
- **Persona pain:** Which pain it addresses
- **Message format:** How to deliver the insight
- **Value delivery:** What action recipient can take
- **Readiness:** NOW (if sender has customers) / FUTURE (once they have 100+ customers)

**Output:** 3-5 internal-data-driven PVP concepts

---

## Example: Skimmer (Pool Service Software)

### Step 1: Business Model Analysis

**Sender:** Skimmer
**Core Product:** Software for pool service companies (scheduling, routing, billing)
**Business Model:** SaaS - subscription software
**Customers:** Pool service professionals (sole proprietors to 50-employee companies)

### Step 2: Operational Necessities

**Data Skimmer MUST collect for product to function:**
1. Customer service routes & locations (zip codes, addresses)
2. Service visit frequency & duration
3. Chemical usage per visit (type, quantity)
4. Pricing per service type (flat rate, per-visit, chemical-inclusive)
5. Number of pools serviced per route
6. Technician/crew scheduling
7. Invoice amounts & payment rates
8. Customer acquisition & churn
9. Service types offered (residential, commercial, specialty)
10. Equipment used (probes, test kits, etc.)

### Step 3: Cross-Reference with Pains (Pool Service Pro Persona)

**Pain 1:** "Pricing competitively - Am I charging too much/little?"
→ Internal data: Pricing per service type by region

**Pain 2:** "Chemical efficiency - Controlling costs"
→ Internal data: Chemical usage per pool by type/region

**Pain 3:** "Route efficiency - Time management"
→ Internal data: Pools per route, service duration, geographic density

**Pain 4:** "Finding new customers - Growth"
→ Internal data: New pool construction by zip code (could combine with permits data)

### Step 4: Aggregation Strategy

**Internal Data Type 1: Service Pricing**
- **Aggregation:** Median pricing by zip code (need 10+ customers per zip)
- **Segmentation:** By service type (flat rate, chemical-inclusive, commercial)
- **Minimum n:** 10 customers per zip code
- **Confidence:** HIGH - Skimmer definitely has pricing data

**Internal Data Type 2: Chemical Usage**
- **Aggregation:** Average lbs per pool per week, by pool type
- **Segmentation:** By region (climate affects chemical use)
- **Minimum n:** 50+ pools
- **Confidence:** HIGH - Core product feature is chemical tracking

**Internal Data Type 3: Route Efficiency**
- **Aggregation:** Percentile benchmarks (top 10% vs average)
- **Segmentation:** By market density (urban/suburban/rural)
- **Minimum n:** 100+ routes
- **Confidence:** HIGH - Route optimization is core value prop

### Step 5: PVP Concepts

**PVP #1: Pricing Benchmark**
```
Subject: Do you charge $169 for pool care?

We work with thousands of pool pros in CA and our data shows the optimal flat monthly rate including chemicals in 95125 is $169. How does your pricing compare?

The flat monthly rate including chemicals in 95125 typically ranges from $108 to $184.

At less than $169, you're potentially undervaluing your services.

Want me to show you how I know for sure on a call?
```
- **Data:** Aggregated pricing from 50+ pool pros in zip 95125
- **Pain:** Pricing competitively
- **Readiness:** NOW (if Skimmer has 50+ customers in that zip)
- **Aggregation:** Safe (no single customer identifiable)

**PVP #2: Chemical Efficiency**
```
Subject: You're 1.5 pounds too heavy

Analyzed chemical usage across 8,400 pool service companies nationwide - the top 10% most profitable use just 2.3 lbs chlorine per pool weekly versus the average 3.8 lbs, saving $1,840 per route monthly at current prices.

In Phoenix specifically, companies buying chlorine at $4.20/lb or less (from suppliers like Sunbelt or PoolCorp) while using under 2.5 lbs per pool maintain 47% gross margins versus the market average of 31%.

Want to see how your chemical usage per pool compares to the top performers in your market?
```
- **Data:** Aggregated chemical usage + supplier pricing
- **Pain:** Chemical efficiency / cost control
- **Readiness:** NOW (if Skimmer has 100+ customers)
- **Aggregation:** Safe (aggregated across thousands)

**PVP #3: Route Efficiency**
```
Subject: 11.2 pools per day

Top-performing pool service routes in Southern California average 11.2 pools per day (in a 6-hour service window) vs. the median of 7.4 pools. The difference? Geographic density of 0.8 miles between stops vs. 2.3 miles for average routes.

Companies optimizing for density (targeting neighborhoods with 5+ pools within 0.5 miles) increase daily capacity by 51% without working longer hours.

Want to see the density map for your service area?
```
- **Data:** Aggregated route metrics from hundreds of pros
- **Pain:** Route efficiency / time management
- **Readiness:** NOW (if Skimmer has 50+ customers with route data)
- **Aggregation:** Safe (benchmarks across many routes)

---

## Validation Checklist

For each internal data PVP concept:

### Data Confidence
- [ ] Sender MUST have this data (operational necessity)
- [ ] Confidence level: HIGH / MEDIUM / LOW
- [ ] If LOW: Consider marking as "Future PVP once sender has scale"

### Ethical Aggregation
- [ ] Minimum n satisfied (typically 10+ for aggregation)
- [ ] No individual customer identifiable
- [ ] No PII exposed
- [ ] Aggregation method appropriate (average/median/percentile)

### Persona Relevance
- [ ] Addresses specific pain from Wave 1 research
- [ ] Creates actionable insight (not just interesting)
- [ ] Recipient would find this valuable even without buying

### Message Quality
- [ ] Specific numbers (not vague "many" or "most")
- [ ] Benchmarks/comparisons included
- [ ] Clear value proposition
- [ ] Low-effort CTA

### Feasibility
- [ ] Sender readiness: NOW / 6 MONTHS / 12 MONTHS
  - NOW: Sender has 100+ customers
  - 6 MONTHS: Sender has 20-100 customers
  - 12 MONTHS: Sender has <20 customers
- [ ] Data infrastructure: SIMPLE / MODERATE / COMPLEX
  - SIMPLE: Basic SQL query on existing data
  - MODERATE: Some data cleaning/normalization needed
  - COMPLEX: Requires ML or complex analysis

---

## Labeling Convention

Mark each internal-data PVP clearly:

**INTERNAL DATA - Ready NOW**
- Sender has scale (100+ customers)
- Data is operational necessity
- Aggregation is straightforward
- PVP can be deployed immediately

**INTERNAL DATA - Ready at SCALE**
- Sender has <100 customers currently
- Data exists but insufficient n for aggregation
- PVP is valid concept for future deployment
- Provides roadmap for sender's data strategy

**INTERNAL DATA + PUBLIC - Hybrid**
- Combines internal aggregated data with public data
- Example: Internal pricing + public permit data
- Creates unique synthesis competitors can't replicate

---

## Output Format

```markdown
## Internal Data PVP Opportunities

### Internal Data Analysis

**Sender Business Model:** [SaaS / Marketplace / Service / E-commerce]

**Operational Data They MUST Have:**
1. [Data type 1] - Confidence: HIGH/MEDIUM/LOW
2. [Data type 2] - Confidence: HIGH/MEDIUM/LOW
3. [Data type 3] - Confidence: HIGH/MEDIUM/LOW
[... list 10-15]

### Pain-to-Data Mapping

**Persona Pain 1:** [Pain from Wave 1]
→ **Internal Data:** [What data addresses this]
→ **Aggregation:** [How to aggregate ethically]
→ **Readiness:** NOW / 6 MONTHS / 12 MONTHS

[Repeat for each top pain]

### Internal Data PVP Concepts

#### PVP Concept 1: [Title]

**Data Required:**
- Internal: [Specific internal data needed]
- Minimum n: [How many customers/data points needed]
- Aggregation method: [Average / Median / Percentile / Trend]

**Persona Pain Addressed:** [Which pain from Wave 1]

**Message Concept:**
[Draft 3-paragraph PVP message using aggregated internal data]

**Readiness Assessment:**
- Sender Scale: [Current customer count if known]
- Data Availability: HIGH / MEDIUM / LOW
- Aggregation Complexity: SIMPLE / MODERATE / COMPLEX
- Deploy Timeline: NOW / 6 MONTHS / 12 MONTHS

**Ethical Check:**
- [ ] No individual customer identifiable
- [ ] Minimum n satisfied
- [ ] No PII exposed
- [ ] Aggregation method appropriate

**Labeling:** INTERNAL DATA - Ready [NOW / SCALE / HYBRID]

[Repeat for 3-5 internal data PVP concepts]
```

---

## Key Principles

1. **Operational necessity = Data exists** - Don't guess, infer from business model
2. **Aggregate, never expose** - Minimum 10+ customers, no individual identification
3. **Pain-driven, not data-driven** - Start with persona pain, not cool data
4. **Honest about readiness** - Label clearly if sender needs scale first
5. **Unique competitive advantage** - Internal data PVPs can't be copied by competitors

---

## Success Criteria

Internal data inference succeeds when:
- [ ] Business model analyzed and operational data inferred
- [ ] 10-15 operational data types identified with confidence levels
- [ ] 5-10 data types mapped to specific persona pains
- [ ] 3-5 internal data PVP concepts designed
- [ ] Ethical aggregation validated for each concept
- [ ] Readiness timeline documented (NOW / 6M / 12M)
- [ ] Clear labeling: INTERNAL DATA - Ready NOW/SCALE/HYBRID
