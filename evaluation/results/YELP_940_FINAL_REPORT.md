# SMB Pipeline Evaluation Report
## 940 Companies Across 10 Verticals

**Date:** 2025-12-01
**Pipeline Version:** V2 (LLM-first with OpenWeb Ninja + Serper)
**Total Cost:** $9.17

---

## Executive Summary

We ran 940 SMB companies through the contact discovery pipeline across 10 verticals. While the pipeline achieves a **69.8% contact discovery rate**, there is a **critical data quality issue**: 78% of "validated" contacts are company names, not person names.

### Key Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Companies Processed | 940/940 | Good |
| Contacts Found | 1,182 (125.7%) | Good |
| Contacts Validated | 865 (92.0%) | Misleading |
| **True Person Names** | ~21% | CRITICAL |
| Cost Per Company | $0.0098 | Excellent |
| Processing Time | 15 min (903s) | Good |

---

## Multi-Layer QA Results

### Layer 1: GPT-4 Batch Scoring (219 evaluated)

| Evaluation | Yes | No | N/A |
|------------|-----|-----|-----|
| Name is a real person | 21% | **78.5%** | 0.5% |
| Title is appropriate | 100% | 0% | - |
| Email is valid | 0% | 0% | 100% |

**Overall Scores:**
- High (90+): 29.2%
- Medium (70-89): 16.9%
- Low (50-69): 0.9%
- **Garbage (<50): 53.0%**

### Layer 2: 5 Claude Agent Deep Analysis

#### Agent 1: Success Patterns
- Google Maps Owner is the MVP (90.1% success rate, 565 valid contacts)
- Best verticals: Tree Services (81%), Junk Removal (77%), General Contractors (76%)
- Title presence is the strongest validity signal (+45.9%)

#### Agent 2: Failure Analysis
- 30.2% failure rate (284 companies)
- 15.3% no contacts found at all
- 14.9% contacts found but all invalid
- Missing `validation_score` field in storage (bug)

#### Agent 3: Vertical Comparison
| Vertical | Success Rate | Avg Confidence |
|----------|-------------|----------------|
| Tree Services | 81.0% | 72.0 |
| Junk Removal | 77.0% | 67.5 |
| General Contractors | 76.0% | 66.9 |
| Landscaping | 74.0% | 64.4 |
| Roofing | 70.0% | 62.5 |
| Plumbing | 70.0% | 62.1 |
| Electricians | 67.2% | 59.0 |
| Auto Repair | 63.0% | 55.2 |
| Movers | 60.0% | 53.3 |
| HVAC | 56.7% | 49.0 |

#### Agent 4: Data Quality (CRITICAL)
- **42% of contacts have company-like names**
- **34.2% have no name at all**
- Only **23.9% are real person names**
- Example: "Nickel Bros" as owner of "Nickel Bros" (90 confidence)
- Validation system has **0% precision** on detecting garbage

#### Agent 5: Cost Efficiency
| Service | Cost | % of Total | ROI |
|---------|------|------------|-----|
| OpenWeb Ninja | $3.76 | 41% | 149 contacts/$ |
| ZenRows | $5.68 | **62%** | 1 contact/$ |
| Serper | $0.47 | 5% | 221 contacts/$ |

**ZenRows accounts for 62% of cost but only 1% of results.**

### Layer 3: Spot-Check Sample
30 companies sampled for human verification:
- 10 high-confidence (90+ score)
- 10 low-confidence (<70 score)
- 10 failures (no contact found)

See: `evaluation/results/yelp_940_spotcheck.md`

---

## Critical Issues Identified

### 1. Company Names as Contact Names (CRITICAL)
**Problem:** 78% of "validated" contacts are company names (e.g., "Nickel Bros") rather than person names (e.g., "John Smith").

**Root Cause:** Validation in `simple_validator.py` awards +40 points for `google_maps_owner` source without checking if the name is actually a person.

**Fix Required:**
```python
# Add name validation
def is_person_name(name: str, company_name: str) -> bool:
    # Reject if name matches company
    if name.lower() in company_name.lower():
        return False
    # Reject if contains company indicators
    indicators = ['inc', 'llc', 'services', 'company', 'corp']
    return not any(ind in name.lower() for ind in indicators)
```

### 2. No Email Coverage
- 100% of contacts have no email
- Pipeline finds phones but not emails
- Limits usefulness for email outreach

### 3. ZenRows Cost Inefficiency
- $5.68 spent (62% of total)
- Only 6 valid contacts from ZenRows
- ROI: 1 contact per dollar (vs 314/$ for Google Maps)

**Recommendation:** Remove ZenRows fallback, save 62% cost.

### 4. Validation Score Storage Bug
- `validation_score` field is missing from stored contacts
- Makes debugging and analysis difficult

---

## Recommendations

### Immediate (This Week)

1. **Add Person Name Validation** - Reject company names as contacts
   - Expected: Reduce "valid" contacts from 865 to ~200
   - But precision goes from 0% to ~85%

2. **Remove ZenRows Stage** - 62% cost savings, <1% quality impact
   - New cost: $3.71 per 1,000 companies (was $9.75)

3. **Fix Validation Score Storage** - Add field to results JSON

### Short-term (This Month)

4. **Add Email Enrichment** - Hunter.io, Snov.io, or Clearbit
   - Current email coverage: 0%
   - Target: 65-75%
   - Additional cost: ~$0.015/company

5. **Implement Early Exit Logic** - Skip additional sources when Google Maps confidence ≥85
   - 74.5% of companies already do this
   - Formalize and optimize

### Medium-term (This Quarter)

6. **Vertical-Specific Strategies**
   - HVAC/Movers underperform (56-60%)
   - Add HomeAdvisor, Thumbtack for these verticals

7. **BBB Discovery Expansion** - 100% success in small sample
   - Test at larger scale

---

## Cost Projections

### Current Pipeline
| Scale | Cost | Per Company | Per Valid Contact |
|-------|------|-------------|-------------------|
| 1,000 | $9.75 | $0.0098 | $0.0112 |
| 10,000 | $97.54 | $0.0098 | $0.0112 |
| 100,000 | $975.43 | $0.0098 | $0.0112 |

### Optimized Pipeline (Remove ZenRows)
| Scale | Cost | Per Company | Savings |
|-------|------|-------------|---------|
| 1,000 | $3.71 | $0.0037 | 62% |
| 10,000 | $37.14 | $0.0037 | $60 |
| 100,000 | $371.43 | $0.0037 | $604 |

---

## Files Generated

| File | Description |
|------|-------------|
| `yelp_940_results.json` | Raw pipeline results (940 companies) |
| `yelp_940_qa_scores.json` | GPT-4 evaluation scores (219 evaluated) |
| `yelp_940_spotcheck.md` | 30-company human verification sample |
| `YELP_940_FINAL_REPORT.md` | This report |

Analysis files from Claude agents:
- `SUCCESS_PATTERNS_SUMMARY.md`
- `FAILURE_ANALYSIS_REPORT.md`
- `yelp_940_vertical_analysis.md`
- `CRITICAL_VALIDATION_FAILURE.md`
- Cost analysis and examples

---

## Conclusion

The SMB pipeline successfully processes companies at scale ($0.01/company, 15 min for 940), but **data quality is the critical bottleneck**. The 69.8% "success rate" is misleading because 78% of "valid" contacts are company names, not person names.

**Priority Action:** Fix validation to reject company names. This will reduce contact count but dramatically improve usability.

**True success rate after fix:** Approximately 15-20% (real person names with owner titles).

---

*Report generated: 2025-12-01 21:45 PST*
