# Product-Fit Triage Framework

**Purpose:** Map product types to valid and invalid pain domains BEFORE exploring niches. This prevents the system from finding data-rich verticals that have no connection to what the product actually solves.

---

## How to Use This Framework

1. **After company research, classify the product type**
2. **Look up valid and invalid pain domains for that type**
3. **During niche exploration, REJECT any niche whose primary pain falls into INVALID domain**
4. **Only score niches whose pain falls into VALID domain**

---

## Product Type Classifications

### 1. Contact & Networking Tools
**Examples:** Digital business cards, contact management, networking apps

| Valid Pain Domains | INVALID Pain Domains |
|-------------------|---------------------|
| Contact sharing speed | Compliance deadlines |
| Networking event preparation | License management |
| New employee onboarding | Carrier appointments |
| Rebranding/address changes | Regulatory violations |
| Remote/hybrid work coordination | Audit preparation |
| Conference/trade show attendance | Operational efficiency |

**Product-Fit Question:** Does the pain relate to sharing contact information, making connections, or managing professional identity?

---

### 2. Sales Engagement Platforms
**Examples:** Outreach.io, Salesloft, Apollo, Instantly

| Valid Pain Domains | INVALID Pain Domains |
|-------------------|---------------------|
| Outreach efficiency/volume | Compliance reporting |
| Sequence/cadence management | Operational workflows |
| Reply rate optimization | Supply chain management |
| CRM data enrichment | Clinical documentation |
| Pipeline velocity | License management |
| SDR productivity | Safety violations |

**Product-Fit Question:** Does the pain relate to sales outreach, pipeline management, or prospect engagement?

---

### 3. Compliance & Regulatory Software
**Examples:** Medtrainer, SimpleCompliance, Relias

| Valid Pain Domains | INVALID Pain Domains |
|-------------------|---------------------|
| Regulatory violations | General productivity |
| Audit preparation/tracking | Sales efficiency |
| Deadline management | Networking/contact sharing |
| Training compliance | Marketing automation |
| Certification tracking | Customer support |
| Inspection readiness | Project management |

**Product-Fit Question:** Does the pain relate to regulatory compliance, violations, audits, or mandatory requirements?

---

### 4. Healthcare/Clinical SaaS
**Examples:** EHR, practice management, telehealth, clinical workflows

| Valid Pain Domains | INVALID Pain Domains |
|-------------------|---------------------|
| Clinical documentation | Non-clinical operations |
| Patient data management | General office productivity |
| Care coordination | Sales/marketing |
| Billing/coding efficiency | Facility maintenance |
| Quality metrics (CMS stars) | General HR/payroll |
| Provider credentialing | Contact sharing |

**Product-Fit Question:** Does the pain relate to clinical workflows, patient care, or healthcare-specific operations?

---

### 5. Operations & Logistics
**Examples:** Fleet management, inventory, supply chain, field service

| Valid Pain Domains | INVALID Pain Domains |
|-------------------|---------------------|
| Fleet/vehicle management | Sales outreach |
| Route optimization | Marketing automation |
| Inventory accuracy | Clinical documentation |
| Supply chain visibility | Compliance training |
| Field service scheduling | Networking/events |
| Asset tracking | CRM management |

**Product-Fit Question:** Does the pain relate to physical operations, logistics, or resource management?

---

### 6. Marketing Automation
**Examples:** HubSpot, Marketo, Klaviyo

| Valid Pain Domains | INVALID Pain Domains |
|-------------------|---------------------|
| Lead generation/nurture | Regulatory compliance |
| Campaign management | Clinical workflows |
| Content/asset management | Fleet/logistics |
| Attribution tracking | Safety violations |
| Website optimization | License management |
| Email marketing efficiency | Inspection readiness |

**Product-Fit Question:** Does the pain relate to marketing campaigns, lead generation, or brand awareness?

---

### 7. Workforce/HR Tech
**Examples:** ATS, HRIS, workforce management, scheduling

| Valid Pain Domains | INVALID Pain Domains |
|-------------------|---------------------|
| Hiring velocity | Clinical documentation |
| Employee onboarding | Sales outreach |
| Scheduling/shift management | Supply chain |
| Workforce compliance | Marketing campaigns |
| Retention/turnover | Fleet management |
| Performance tracking | Patient care |

**Product-Fit Question:** Does the pain relate to hiring, managing, scheduling, or retaining employees?

---

## Decision Rules

### Rule 1: Domain Match Required
If the identified pain falls into an **INVALID** domain for this product type:
- **AUTO-REJECT** the segment
- Do NOT attempt to score it
- Do NOT attempt to generate messages for it

### Rule 2: Ambiguous Cases
If the pain doesn't clearly fit VALID or INVALID:
- Ask: "Would buying THIS product directly address this pain?"
- If answer requires >2 logical jumps → INVALID
- If answer is "maybe" or "partially" → INVALID

### Rule 3: Data Richness ≠ Product Fit
A niche can have:
- Excellent data availability (9/10)
- Strong regulatory pressure (9/10)
- Clear operational context (9/10)
- **BUT** if the pain domain doesn't match the product → REJECT

**Example:** Insurance agents have rich NIPR data, but digital business cards don't solve CE compliance. Data score: 9/10. Product-fit: 0/10. Result: REJECT.

---

## Examples

### Good Product-Fit Match

| Product | Niche | Pain | Domain Match | Result |
|---------|-------|------|--------------|--------|
| Compliance software | Nursing homes | CMS survey deficiencies | ✅ Regulatory violations | VALID |
| Fleet management | Trucking companies | FMCSA conditional ratings | ✅ Fleet/vehicle management | VALID |
| Digital business cards | Sales teams at conferences | No time to print before event | ✅ Networking events | VALID |

### Bad Product-Fit Match (REJECT)

| Product | Niche | Pain | Domain Match | Result |
|---------|-------|------|--------------|--------|
| Digital business cards | Insurance agents | CE deadline compliance | ❌ Compliance deadlines | REJECT |
| Sales engagement | Restaurants | Health inspection grades | ❌ Regulatory violations | REJECT |
| Marketing automation | Trucking companies | FMCSA safety violations | ❌ Fleet management | REJECT |

---

## Integration with Vertical Qualification

After a niche passes the Product-Fit Triage:
1. Proceed to full 5-criterion scoring
2. Criterion 5 (Product-Solution Alignment) provides granular 0-10 score
3. But Product-Fit Triage is the FIRST filter - wrong domain = don't even score

**Flow:**
```
Niche Identified
    ↓
Product-Fit Triage (Domain Check)
    ↓ PASS               ↓ FAIL
Full 5-Criterion     AUTO-REJECT
Scoring              (Don't score)
    ↓
Criterion 5 ≥ 5?
    ↓ YES            ↓ NO
Proceed to        REJECT
Synthesis         (Product mismatch)
```
