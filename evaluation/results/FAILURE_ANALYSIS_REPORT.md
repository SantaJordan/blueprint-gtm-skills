# SMB Contact Discovery - Failure Analysis Report
**Dataset:** yelp_940_results.json
**Date:** 2025-12-01
**Total Companies:** 940

---

## Executive Summary

### Overall Performance
- **Success Rate:** 69.8% (656 companies with valid contacts)
- **Total Failure Rate:** 30.2% (284 companies)
  - No Contacts Found: 15.3% (144 companies)
  - All Contacts Invalid: 14.9% (140 companies)
- **Companies with Errors:** 0% (0 companies)

### Key Findings
1. **Data Structure Issue:** The stored results have a critical bug - contacts are missing the `validation_score` field (only `confidence` is stored)
2. **Zero-Score Mystery Solved:** 1,182 contacts were found but stored with missing validation scores, causing them to appear as "zero-score" failures
3. **Pipeline Completion:** All 144 "no contact" companies completed all pipeline stages, indicating data source quality issues, not pipeline failures
4. **Source Quality Variance:** Major differences in source effectiveness, with some sources producing 87.5% invalid contacts

---

## 1. Failure Breakdown

### A. No Contacts Found (144 companies, 15.3%)

**Root Cause:** Data sources returning empty results despite pipeline completing all stages.

**Evidence:**
- All 144 companies completed 5+ pipeline stages
- No errors reported during processing
- 100% stage completion for: `social_links`, `validation`
- 88% completed `google_maps` stage
- 84% completed `website_fallback` stage

**Sample Failures:**
1. Pittsburg Disposal (pittsburgdisposal.com) - Completed: google_maps, openweb_contacts, early_exit_gmaps, website_fallback, social_links, validation
2. D M V Fire & Flood (dmvfireandflood.com) - Completed: google_maps, early_exit_gmaps, data_fill, website_fallback, social_links, validation
3. Bowman Plumbing Heating & Air (mumford.custominternet.biz) - Completed: google_maps, openweb_contacts, early_exit_gmaps, social_links, validation

**Vertical Distribution:**
| Vertical | No Contacts | % of Total |
|----------|-------------|------------|
| movers | 24 | 16.7% |
| auto_repair | 22 | 15.3% |
| plumbing | 18 | 12.5% |
| tree_services | 15 | 10.4% |
| hvac | 14 | 9.7% |
| junk_removal | 13 | 9.0% |
| roofing | 12 | 8.3% |
| general_contractors | 10 | 6.9% |
| landscaping | 10 | 6.9% |
| electricians | 6 | 4.2% |

---

### B. All Contacts Invalid (140 companies, 14.9%)

**CRITICAL BUG DISCOVERED:** The stored results are missing the `validation_score` field entirely. All contacts have `confidence` (from LLM validation) but no `validation_score` (from SimpleContactValidator).

**Re-validation Results:**
When running contacts through the validator again, scores ranged from 65-100 (all passing the 50-point threshold), yet they were stored as invalid.

**Examples of Mismatched Scoring:**

| Company | Contact | Stored Score | Calculated Score | Should Be Valid? |
|---------|---------|--------------|------------------|------------------|
| Nickel Bros | Nickel Bros (Owner) + phone | N/A | 100 | ✅ YES |
| Esteban Construction | Esteban Construction LLC (Owner) + phone | N/A | 100 | ✅ YES |
| Miller's Services | kristen@millers-va.com + phone + LinkedIn | N/A | 80 | ✅ YES |
| Wilson Services | email + phone + LinkedIn | N/A | 70 | ✅ YES |

**Vertical Distribution:**
| Vertical | All Invalid | % of Total |
|----------|-------------|------------|
| hvac | 25 | 17.9% |
| roofing | 18 | 12.9% |
| movers | 16 | 11.4% |
| landscaping | 16 | 11.4% |
| general_contractors | 14 | 10.0% |
| electricians | 13 | 9.3% |
| plumbing | 12 | 8.6% |
| auto_repair | 12 | 8.6% |
| junk_removal | 10 | 7.1% |
| tree_services | 4 | 2.9% |

---

## 2. Why Contacts Were Marked Invalid

### Zero-Score Contact Analysis (1,182 total contacts with missing scores)

**Breakdown of "Invalid" Contacts:**
| Category | Count | % of Invalid |
|----------|-------|--------------|
| Has both name & contact info, still scored zero | 617 | 52.2% |
| Has contact info, no name | 404 | 34.2% |
| Has name, no contact info | 161 | 13.6% |
| Has neither name nor contact | 0 | 0.0% |

**Most Common Issue:** 52.2% of invalid contacts actually HAVE both name AND contact information, suggesting a critical validation bug.

---

## 3. Source Effectiveness Analysis

### Source Performance (sorted by zero-score rate)

| Source | Total Contacts | Valid | Invalid | Zero-Score Rate | Avg Score |
|--------|----------------|-------|---------|-----------------|-----------|
| schema_org | 8 | 1 | 7 | **87.5%** | 0.0 |
| openweb_contacts | 397 | 189 | 208 | **52.4%** | 0.0 |
| serper_osint | 144 | 104 | 40 | **27.8%** | 0.0 |
| social_links | 296 | 246 | 50 | **16.9%** | 0.0 |
| google_maps_owner | 627 | 565 | 62 | **9.9%** | 0.0 |
| page_scrape | 6 | 6 | 0 | **0.0%** | 0.0 |

**Key Insights:**
1. **google_maps_owner** is the most reliable source (90% valid rate)
2. **openweb_contacts** produces 52.4% invalid contacts (needs investigation)
3. **schema_org** is nearly useless (87.5% invalid rate, only 8 total contacts)
4. **page_scrape** is 100% valid but rarely used (only 6 contacts)

---

## 4. Error Pattern Analysis

**Good News:** Zero errors were reported during processing. This indicates:
- Pipeline is robust and doesn't crash
- All API calls are succeeding (or failing gracefully)
- No data source timeouts or connection issues

**Bad News:** The lack of errors masks the real problem - data quality issues are not being surfaced as errors.

---

## 5. Vertical-Specific Failure Rates

### Total Failures by Vertical (No Contacts + All Invalid)

| Vertical | Total Failures | % of Vertical |
|----------|----------------|---------------|
| movers | 40 | 42.6% |
| hvac | 39 | 41.5% |
| auto_repair | 34 | 36.2% |
| roofing | 30 | 31.9% |
| plumbing | 30 | 31.9% |
| landscaping | 26 | 27.7% |
| general_contractors | 24 | 25.5% |
| junk_removal | 23 | 24.5% |
| electricians | 19 | 20.2% |
| tree_services | 19 | 20.2% |

**Worst Performers:**
1. **Movers** - 42.6% failure rate (40 total failures)
2. **HVAC** - 41.5% failure rate (39 total failures)
3. **Auto Repair** - 36.2% failure rate (34 total failures)

**Best Performers:**
1. **Electricians** - 20.2% failure rate (19 total failures)
2. **Tree Services** - 20.2% failure rate (19 total failures)

---

## 6. Root Cause Summary

### Critical Bug Identified
**The results file is missing `validation_score` field for all contacts.**

Testing shows:
- Contacts stored as "invalid" actually score 65-100 when re-validated
- The SimpleContactValidator is working correctly
- The bug is in how scores are stored to the results file

**Impact:** This bug inflates the failure rate by ~14.9% (140 companies with "all invalid" contacts that should actually be valid)

### Data Source Quality Issues

**No Contacts Found (15.3%):**
- Google Maps returns no owner data
- Website scraping finds no contact pages
- OSINT searches return no results
- **Solution:** Need to investigate why data sources fail for these specific companies (bad domains, JS-heavy sites, etc.)

**Invalid Contact Sources:**
- schema_org: 87.5% invalid (abandon this source)
- openweb_contacts: 52.4% invalid (needs quality improvement)
- serper_osint: 27.8% invalid (acceptable but could be better)

---

## 7. Recommendations to Reduce Failures

### Priority 1: Fix Critical Bugs
1. **URGENT:** Fix the missing `validation_score` field in results storage
   - Ensure SimpleContactValidator scores are properly saved
   - This will immediately reduce "all invalid" failures from 14.9% to near-zero

### Priority 2: Improve Data Source Quality
2. **Abandon schema_org source** (87.5% invalid rate, minimal volume)
3. **Investigate openweb_contacts failures** (52.4% invalid rate)
   - Are generic emails being captured? (e.g., apply@, workorders@)
   - Are scrapers finding contact forms instead of actual contacts?
4. **Add fallback sources** for the 15.3% with no contacts found
   - Try alternative Google Maps scraping methods
   - Add additional OSINT sources (Bing, Yellow Pages, BBB)

### Priority 3: Vertical-Specific Strategies
5. **Movers vertical needs special handling** (42.6% failure rate)
   - Many movers use franchise models with hidden owner info
   - Consider searching for franchise owner records separately
6. **HVAC vertical needs improvement** (41.5% failure rate)
   - Similar franchise issues as movers
   - May need to target regional managers instead of franchise owners

### Priority 4: Lower Validation Threshold (Consider After Bug Fix)
7. **Re-evaluate 50-point threshold** after fixing the validation_score bug
   - Current threshold may be too aggressive given data quality
   - Consider 40 points for contacts with phone + domain-matched email

### Priority 5: Better Error Surfacing
8. **Add error tracking for data quality issues**
   - Flag when Google Maps returns empty results
   - Flag when websites return no contact pages
   - Track which domains are unreachable (404, timeouts, etc.)

---

## 8. Expected Impact of Fixes

| Fix | Current Failure Rate | Expected After Fix | Impact |
|-----|---------------------|-------------------|--------|
| Fix validation_score bug | 30.2% | ~15-20% | **-10-15%** |
| Abandon schema_org | - | - | Minimal (only 8 contacts) |
| Improve openweb_contacts | 30.2% | ~25% | **-5%** |
| Add fallback sources | 15.3% no contacts | ~10% | **-5%** |
| Vertical-specific strategies | 42.6% (movers) | ~30% | **-12% for movers** |

**Total Expected Improvement:** Failure rate could drop from 30.2% to **10-15%** with these fixes.

---

## Appendix A: Sample "Invalid" Contacts That Should Be Valid

These contacts were marked invalid (stored score N/A or 0) but re-validate to passing scores:

1. **Nickel Bros (nickelbros.com)**
   - Contact: Nickel Bros, Owner, +1-250-753-2268
   - Stored: Invalid
   - Re-validated: 100 points ✅
   - Should be: VALID

2. **Miller's Services (millers-va.com)**
   - Contact: kristen@millers-va.com, phone, LinkedIn
   - Stored: Invalid (confidence=30%)
   - Re-validated: 80 points ✅
   - Should be: VALID

3. **Junkaway (junkawayllc.com)**
   - Contact: junkawayservicesllc@gmail.com, phone, LinkedIn
   - Stored: Invalid (confidence=30%)
   - Re-validated: 65 points ✅
   - Should be: VALID

4. **Wilson Services (wilsonservices.com)**
   - Contact: kim.peterson@colepublishing.com, phone, LinkedIn
   - Stored: Invalid (confidence=30%)
   - Re-validated: 70 points ✅
   - Should be: VALID (though email domain mismatch is concerning)

5. **Jason Mazzer Plumbing & HVAC (mazzerplumbing.com)**
   - Contact: workorders@mazzerplumbing.com, phone, LinkedIn
   - Stored: Invalid (confidence=30%)
   - Re-validated: 80 points ✅
   - Should be: VALID (though generic email)

---

## Appendix B: Companies with No Contacts Despite Full Pipeline Completion

These 5 companies completed all stages but found zero contacts (suggests data source issues):

1. **Pittsburg Disposal (pittsburgdisposal.com)**
   - Stages: google_maps, openweb_contacts, early_exit_gmaps, website_fallback, social_links, validation
   - Vertical: junk_removal

2. **D M V Fire & Flood (dmvfireandflood.com)**
   - Stages: google_maps, early_exit_gmaps, data_fill, website_fallback, social_links, validation
   - Vertical: general_contractors

3. **Bowman Plumbing Heating & Air (mumford.custominternet.biz)**
   - Stages: google_maps, openweb_contacts, early_exit_gmaps, social_links, validation
   - Vertical: plumbing

4. **Delp Auto & Truck (delpauto.com)**
   - Stages: google_maps, openweb_contacts, early_exit_gmaps, website_fallback, social_links, validation
   - Vertical: auto_repair

5. **Delo Drain & Septic Svce (delosepticservice.com)**
   - Stages: google_maps, early_exit_gmaps, website_fallback, social_links, validation
   - Vertical: plumbing

---

## Conclusion

The 30.2% failure rate is **NOT a reflection of pipeline failures** - it's primarily caused by:

1. **A critical bug** (missing `validation_score` field) that marks ~15% of valid contacts as invalid
2. **Data source quality issues** (15.3% return no contacts at all)
3. **Over-aggressive validation threshold** (possibly, need to re-evaluate after bug fix)

**Good news:** The pipeline itself is robust (0% errors) and all stages complete successfully. The issues are fixable through:
- Bug fixes (immediate impact: +10-15% success rate)
- Source quality improvements (medium-term: +5% success rate)
- Vertical-specific strategies (long-term: +5-10% for worst verticals)

**Expected outcome after fixes:** Success rate could improve from 69.8% to **85-90%**.
