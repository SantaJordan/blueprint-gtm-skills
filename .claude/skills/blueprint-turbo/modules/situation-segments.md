# Situation-Based Segment Generation

**Use when:** All vertical niches fail Criterion 5 (Product-Solution Alignment) - typically for horizontal products that serve any business.

**Purpose:** Generate TIMING-based plays that connect DATA → SITUATION → PAIN → PRODUCT instead of forcing irrelevant regulatory data.

---

## When to Trigger Situation-Based Generation

**Trigger conditions (ANY of these):**
- All evaluated verticals score <5 on Criterion 5 (Product-Solution Alignment)
- Product type is classified as "horizontal" (serves any B2B company)
- Product-Fit Triage rejects all data-rich verticals
- No regulated industry has pain that the product directly solves

**Do NOT use when:**
- At least one vertical scores ≥5 on Criterion 5
- Product has clear regulated vertical fit (compliance software, healthcare SaaS, etc.)
- Vertical-based segments pass Gate 5 (Product Connection)

---

## Situation Categories

### 1. Time Pressure (Events with Deadlines)

**Trigger:** External event creating time-bound urgency

**Examples:**
- Conference/trade show in [N] weeks
- Product launch date approaching
- Office move scheduled
- Merger announcement with rebrand deadline
- Regulatory deadline (if product solves it)

**Data Sources:**
- Event registration lists (if accessible)
- Conference attendee lists (LinkedIn, etc.)
- Press releases announcing events
- SEC filings (M&A announcements)
- State filings (address changes)

**Product-Fit Examples:**
| Product | Situation | Why It Works |
|---------|-----------|--------------|
| Digital business cards | Conference in 2 weeks | No time to print → digital is instant |
| Event management | Trade show next month | Need registration/badge system NOW |
| Marketing collateral | Product launch in 3 weeks | Need materials immediately |

---

### 2. Scale Pressure (Rapid Growth Creating Gaps)

**Trigger:** Volume increase overwhelming current processes

**Examples:**
- 10+ new hires per month
- 3x customer growth in 6 months
- Expanding to new locations
- Post-funding rapid scaling
- Seasonal volume spikes

**Data Sources:**
- LinkedIn hiring velocity
- Press releases (funding, expansion)
- Job postings volume
- Location filings (new offices)
- Glassdoor review velocity (hiring signal)

**Product-Fit Examples:**
| Product | Situation | Why It Works |
|---------|-----------|--------------|
| Digital business cards | Hiring 15 people/month | Can't print cards fast enough |
| Onboarding software | 20 new hires starting Monday | Need to onboard at scale |
| Scheduling software | Opening 5 new locations | Manual scheduling breaks at scale |

---

### 3. Change Pressure (Transitions Making Old Solutions Obsolete)

**Trigger:** Change event making current approach invalid

**Examples:**
- Company rebrand (name, logo, colors)
- Office relocation (address change)
- Post-M&A integration
- Leadership change (new C-suite)
- Market pivot (new positioning)

**Data Sources:**
- Press releases (rebrand, M&A)
- State filings (name change, address)
- LinkedIn company page changes
- Domain/website changes
- SEC filings (for public companies)

**Product-Fit Examples:**
| Product | Situation | Why It Works |
|---------|-----------|--------------|
| Digital business cards | Rebrand announced | All printed cards now obsolete |
| CRM | Post-merger integration | Need to consolidate systems |
| Marketing automation | New positioning | All content needs refresh |

---

## Situation Segment Format

For each situation-based segment, document:

```markdown
## Segment: [Situation Name]

**Category:** Time Pressure / Scale Pressure / Change Pressure

**Trigger Event:**
[What creates the urgency - be specific]

**Detection Method:**
[How we know this situation exists externally]

**Data Sources:**
1. [Source 1]: [Specific field/signal to extract]
   - API/Method: [How to access]
   - Confidence: [HIGH/MEDIUM/LOW]

2. [Source 2]: [Specific field/signal to extract]
   - API/Method: [How to access]
   - Confidence: [HIGH/MEDIUM/LOW]

**Pain Hypothesis:**
[Why they need the product NOW, not later - connect to urgency]

**Product-Fit Validation:**
- Does this situation create need for THIS product? [Y/N + explain]
- Is the product the DIRECT solution? [Y/N + explain]
- Would buying solve the immediate problem? [Y/N + explain]

**Gate 5 Check:**
"If they resolve this situation, would they NEED this product to do it?"
- Answer: [YES/NO/MAYBE]
- Rationale: [Why]

**Texada Test:**
- ✅/❌ Hyper-specific: [Can we name specific companies in this situation?]
- ✅/❌ Factually grounded: [Is the situation externally observable?]
- ✅/❌ Non-obvious: [Do they know they're in this situation AND its implications?]

**Message Type:** PQS / Situational PVP
**Confidence Level:** [%]
**Verdict:** PROCEED / REVISE / REJECT
```

---

## Example: Digital Business Cards (Blinq)

### Segment 1: Conference Urgency

**Category:** Time Pressure

**Trigger Event:**
Newly licensed professional attending industry conference within 30 days

**Detection Method:**
Cross-reference new license registrations with conference attendee signals

**Data Sources:**
1. State licensing databases (RE, Insurance, etc.): New license filings
   - API/Method: NIPR, state RE boards, web scraping
   - Confidence: HIGH (public record)

2. LinkedIn activity: Conference attendance signals
   - API/Method: Profile scraping, event pages
   - Confidence: MEDIUM (inferred from activity)

**Pain Hypothesis:**
"You just got your license 3 weeks ago and you're attending [Conference] in 12 days. You probably don't have business cards yet - and even if you rush-ordered them, they might not arrive in time. Your first big networking opportunity and you'll be the only one without cards."

**Product-Fit Validation:**
- Does this situation create need for THIS product? YES - need to share contact info at conference
- Is the product the DIRECT solution? YES - digital cards = instant, no printing needed
- Would buying solve the immediate problem? YES - sign up today, have cards tomorrow

**Gate 5 Check:**
"If they resolve this situation, would they NEED this product to do it?"
- Answer: YES
- Rationale: To have professional contact sharing at conference without printed cards, digital cards are the direct solution

**Texada Test:**
- ✅ Hyper-specific: Can identify specific people (new license + conference attendance)
- ✅ Factually grounded: License date is public record, conference dates are public
- ⚠️ Non-obvious: They know they're going to conference, but may not have thought about the card problem yet

**Message Type:** Situational PQS (situation-based, not regulatory pain)
**Confidence Level:** 65-75% (inference on conference attendance)
**Verdict:** PROCEED

---

### Segment 2: Rapid Onboarding Scale

**Category:** Scale Pressure

**Trigger Event:**
Company hiring 10+ professionals per month who need business cards

**Detection Method:**
LinkedIn hiring velocity + job postings for client-facing roles

**Data Sources:**
1. LinkedIn company data: Headcount growth, recent hires
   - API/Method: LinkedIn Sales Navigator or scraping
   - Confidence: MEDIUM (may lag actual hiring)

2. Job postings: Open client-facing roles (sales, account management)
   - API/Method: Indeed, LinkedIn Jobs, company careers page
   - Confidence: HIGH (publicly posted)

**Pain Hypothesis:**
"You've added 47 people in the last 3 months. If each of them needs business cards, that's 47 design requests, 47 print orders, 47 shipments to track. What happens when someone's cards arrive after their first client meeting? Digital cards onboard in 2 minutes, not 2 weeks."

**Product-Fit Validation:**
- Does this situation create need for THIS product? YES - scaling card provisioning
- Is the product the DIRECT solution? YES - digital cards eliminate print delays
- Would buying solve the immediate problem? YES - instant provisioning at scale

**Gate 5 Check:**
"If they resolve this situation, would they NEED this product to do it?"
- Answer: YES
- Rationale: To provision cards instantly at scale without print logistics, digital is the solution

**Texada Test:**
- ✅ Hyper-specific: Can identify companies with specific headcount growth numbers
- ✅ Factually grounded: Hiring data is observable on LinkedIn
- ✅ Non-obvious: They know they're hiring, but haven't calculated the card provisioning burden

**Message Type:** Situational PVP (includes their specific hiring data)
**Confidence Level:** 70-80% (LinkedIn data reliability varies)
**Verdict:** PROCEED

---

## Validation Criteria for Situation Segments

Each situation segment must pass:

### 1. Product Connection (Gate 5)
- [ ] Situation creates genuine need for this product
- [ ] Product is DIRECT solution (not tangential)
- [ ] Buying product resolves the immediate problem

### 2. Data Detectability
- [ ] At least one HIGH confidence data source
- [ ] Situation can be detected externally (not internal knowledge)
- [ ] Can name specific companies currently in this situation

### 3. Urgency Validity
- [ ] Time pressure is real (not manufactured)
- [ ] Waiting has clear cost/risk
- [ ] Urgency drives action, not just awareness

### 4. Message Viability
- [ ] Can write message that references specific situation
- [ ] Message is NOT generic ("companies like yours often...")
- [ ] Message includes THEIR data (not industry stats)

---

## Difference from Vertical Segments

| Aspect | Vertical Segment | Situation Segment |
|--------|-----------------|-------------------|
| **Basis** | Regulated industry pain | Time-bound situation |
| **Data** | Compliance/regulatory records | Event/change signals |
| **Pain type** | Ongoing operational pain | Momentary urgency |
| **Conversion** | Higher (pain is constant) | Lower (timing must align) |
| **Volume** | Smaller (specific vertical) | Larger (cross-industry) |
| **Confidence** | Higher (regulatory = certain) | Moderate (inference required) |

---

## When Situation Segments Also Fail

If no situation segments pass Gate 5 + Texada Test:
- **Do NOT force output**
- **Trigger Honest No-Fit Response** (see Wave 3 no-fit protocol)
- **Options:** Honest rejection, suggest pivots, acknowledge limitations
