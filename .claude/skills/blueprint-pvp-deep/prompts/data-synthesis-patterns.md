# Data Synthesis Patterns for Non-Obvious PVPs

**Purpose:** Strategic patterns for combining data sources to create non-obvious insights

**Use During:** Phase 1 (Deep Data Synthesis) with Sequential Thinking

---

## Pattern 1: Cross-Reference (Matching & Enrichment)

**Strategy:** Match entity in Database A with same entity in Database B to enrich understanding

**Example:** Equipment + Permits
- Database A: Company's idle equipment (no active permits)
- Database B: Building permits requiring that equipment
- Synthesis: "Your Liebherr crane is idle + Maxwell needs that crane model = $45K opportunity"

**When to Use:**
- Have unique identifier (address, company name, equipment ID)
- Both databases cover same geographic area or industry
- One shows availability, other shows need

**Persona Value:** Reveals hidden opportunities they can't see without cross-referencing

---

## Pattern 2: Temporal Correlation (Timing Signals)

**Strategy:** Detect patterns in WHEN things happen to predict or explain WHY

**Example:** Violations + Time
- Database A: EPA violations by facility
- Add temporal analysis: 87% occur 8pm-4am
- Synthesis: "Your violations cluster at night = training gap with night shift"

**When to Use:**
- Data has timestamps
- Persona cares about operational patterns
- Pattern suggests root cause

**Persona Value:** Transforms "what happened" into "why it happened"

---

## Pattern 3: Competitive Benchmarking (Position vs Market)

**Strategy:** Compare entity's metrics to aggregated market benchmarks

**Example:** Pricing + Market Average
- Internal Data: Company's prices (if available) OR scrape their prices
- Aggregate: Market average prices from 50+ competitors
- Synthesis: "You charge $38 vs market avg $45 = leaving $2.1K/month on table"

**When to Use:**
- Have data from multiple entities in same market
- Metric is comparable (pricing, efficiency, quality)
- Persona struggles with "am I competitive?"

**Persona Value:** Answers "how do I compare?" with specific numbers

---

## Pattern 4: Velocity Detection (Change Over Time)

**Strategy:** Measure RATE OF CHANGE to detect acceleration, deceleration, or inflection points

**Example:** Review Velocity
- Database: Google Maps reviews with timestamps
- Calculate: 142 reviews in last 30 days (up from 89 prior month)
- Synthesis: "Your review velocity jumped 60% = demand surge or quality improvement"

**When to Use:**
- Data has timestamps spanning multiple periods
- Persona cares about growth/decline trends
- Velocity itself is signal (not just absolute numbers)

**Persona Value:** Reveals momentum they might not be tracking

---

## Pattern 5: Geo-Clustering (Spatial Density)

**Strategy:** Find geographic concentrations to reveal untapped or oversaturated areas

**Example:** New Construction + Service Area
- Database A: Building permits with addresses
- Geocode: 186 pools in 1.2 sq mile area over next 45 days
- Synthesis: "Dense cluster = 2 complete routes in one neighborhood"

**When to Use:**
- Data has addresses or coordinates
- Persona's business is location-dependent
- Density creates operational advantage

**Persona Value:** Reveals geographic opportunities invisible without mapping

---

## Pattern 6: Cascade Detection (Upstream → Downstream)

**Strategy:** Connect event in Entity A's world to impact on Entity B (the persona)

**Example:** ICP's Customer Stress → ICP Opportunity
- Layer 1: Restaurant delivery fees rising (ICP's customer pain)
- Layer 2: Restaurants seeking direct ordering (ICP's opportunity)
- Synthesis: "Your prospects' DoorDash fees up 28% = urgency for your solution"

**When to Use:**
- Understand ICP's customers (second layer from Wave 1)
- Can connect external trigger to ICP pain
- Persona doesn't see the connection

**Persona Value:** Explains WHY now is the right time for outreach

---

## Pattern 7: Absence as Signal (What's Missing)

**Strategy:** The LACK of expected data is itself valuable information

**Example:** No Permit = Idle Asset
- Expected: Active DOT permit for equipment
- Reality: No permit found in last 60 days
- Synthesis: "$2M crane with no permit = likely idle = opportunity cost"

**When to Use:**
- Expected pattern is well-established
- Absence is unusual or costly
- Persona might not notice the absence

**Persona Value:** Highlights blind spots they're not monitoring

---

## Pattern 8: Threshold Crossing (Tipping Points)

**Strategy:** Detect when metric crosses critical threshold that changes meaning

**Example:** Inspection Scores + Closure Risk
- Data: NYC restaurant inspection score of 42 points
- Threshold: 28+ points = closure risk, 42 = high probability
- Synthesis: "Your 42-point violation = closure-level risk, avg is 18 points"

**When to Use:**
- Industry has known thresholds (regulatory, operational)
- Crossing threshold has severe consequences
- Persona might not know exact threshold

**Persona Value:** Quantifies severity vs just noting problem

---

## Pattern 9: Multi-Source Triangulation (Confidence Building)

**Strategy:** Use 3+ independent data sources pointing to same conclusion

**Example:** High Activity Restaurant
- Source 1: Google Maps reviews (142/month = high)
- Source 2: Yelp check-ins (320/month = very high)
- Source 3: OpenTable reservations (88% booked = high demand)
- Synthesis: "Three signals confirm you're high-volume = worth pursuing"

**When to Use:**
- Single source might not be convincing
- Multiple sources reduce uncertainty
- Persona needs confidence before acting

**Persona Value:** Reduces "but what if I'm wrong?" fear

---

## Pattern 10: Internal + Public Hybrid (Unique Advantage)

**Strategy:** Combine sender's internal data with public data for insights competitors can't replicate

**Example:** Internal Benchmark + Public Opportunity
- Internal: Top performers use 2.3 lbs chlorine/pool (from 1000s of customers)
- Public: This specific pool pro uses 3.8 lbs (scraped or inferred)
- Synthesis: "You're 1.5 lbs over optimal = $1,840/month waste vs top 10%"

**When to Use:**
- Sender has scale (100+ customers for benchmarks)
- Public data shows individual entity's metric
- Comparison creates actionable insight

**Persona Value:** Provides benchmark they can't get elsewhere

---

## Using Sequential Thinking for Synthesis

### Thought Process Template

**Thought 1-2:** Review available data sources and persona pains
- What data do I have access to?
- What pain am I trying to address?

**Thought 3-4:** Identify potential synthesis patterns
- Which patterns could apply here?
- What combinations make sense?

**Thought 5-7:** Explore specific combinations
- Try Pattern X with Sources A + B
- Does this create non-obvious insight?
- Does persona already know this?

**Thought 8-10:** Validate against criteria
- Is this hyper-specific (actual values, not vague)?
- Is this factually grounded (provable, not inferred)?
- Is this non-obvious (persona doesn't have this)?

**Thought 11-13:** Iterate or pivot
- If weak: Try different pattern or sources
- If promising: Refine the synthesis
- Reject if can't reach non-obvious insight

**Thought 14-15:** Finalize synthesis concepts
- Select top 3-5 synthesis insights
- Document data sources and pattern used
- Prepare for drafting

---

## Synthesis Quality Checklist

Each synthesis should pass:

- [ ] **Non-obvious:** Persona unlikely to discover without our analysis
- [ ] **Multi-source:** Combines 2+ data sources (not single source)
- [ ] **Specific:** Uses actual numbers, names, dates (not vague)
- [ ] **Verifiable:** Persona can check key claims if they want
- [ ] **Actionable:** Points toward a specific decision or action
- [ ] **Persona-relevant:** Addresses a pain from Wave 1 research

---

## Common Mistakes to Avoid

🚫 **Single-source "synthesis"** - Just restating one data point isn't synthesis

🚫 **Obvious conclusions** - If persona already knows this, it's not valuable

🚫 **Vague connections** - "This might relate to that" isn't strong enough

🚫 **Too much inference** - If 50%+ is guessing, it's not grounded

🚫 **Generic insights** - Applies to 1000s of companies = not specific enough

---

## Success Criteria

Synthesis succeeds when:
- [ ] Used Sequential Thinking to explore 5+ combinations
- [ ] Applied 2-3 synthesis patterns from this guide
- [ ] Generated 3-5 non-obvious insights
- [ ] Each insight passes quality checklist
- [ ] Each insight maps to specific persona pain
- [ ] Data sources documented for each insight
- [ ] Ready to draft PVP concepts in Phase 2
