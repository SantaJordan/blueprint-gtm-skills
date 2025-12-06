# SMB Contact Discovery - Data Quality Analysis
## Yelp 940 Results - Garbage Detection Report

**Analysis Date:** 2025-12-01
**Dataset:** `/Users/jordancrawford/Desktop/Blueprint-GTM-Skills/evaluation/results/yelp_940_results.json`

---

## Executive Summary

**Data Quality Score: 28.6/100** (POOR - Major Issues Detected)

**Critical Findings:**
- 42.0% of contacts use company names instead of person names
- 34.2% of contacts have no name at all
- Only 23.9% of contacts have likely real person names
- 65.8% of contacts have no email address
- Of emails found, 43.1% are generic domains (gmail, yahoo) vs company domains

**Total Dataset:**
- Companies: 940
- Contacts Found: 1,182
- Contacts Validated: 865 (73.2%)
- Estimated Cost: $9.17

---

## 1. Company Names Used as Contact Names

### The Problem
**496 contacts (42.0%)** have company-like name patterns, with **194 (16.4%)** having names that exactly match the company name.

### Examples of Garbage Data

| Company Name | Contact "Name" | Title | Valid? | Issue |
|--------------|----------------|-------|--------|-------|
| Nickel Bros | Nickel Bros | Owner | ✅ True | Name = Company |
| Miller's Services | Miller's Services | Owner | ✅ True | Name = Company |
| Moover Dudes | Moover Dudes | Owner | ✅ True | Name = Company |
| Decook Excavating | DeCook Excavating | Owner | ✅ True | Name = Company |
| Alford Plumbing | Alford Plumbing | Owner | ✅ True | Name = Company |

**CRITICAL ISSUE:** These contacts are marked as VALID despite having no actual person name. This is a major validation failure.

### Why This Happens
The primary source is **google_maps_owner** (53% of all contacts), which appears to return the business name when it can't find an owner name.

### Impact
- **Unusable for personalized outreach** - Can't address a real person
- **High bounce rate expected** - Generic emails won't reach decision makers
- **Wasted validation credits** - Contacts shouldn't pass validation

---

## 2. Missing Names

**404 contacts (34.2%)** have no name field at all.

### Sources of Nameless Contacts
- **openweb_contacts**: Extracts emails from websites but often no associated name
- **serper_osint**: Finds company info but not always people

### Validation Status
Most nameless contacts are marked invalid, which is correct behavior. However, the system still spends resources extracting and processing them.

---

## 3. Real Person Names (The Good Data)

Only **282 contacts (23.9%)** have names that look like real people with 2+ words and no company indicators.

This means **less than 1 in 4 contacts** are potentially usable for personalized outreach.

---

## 4. Email Domain Matching Analysis

### Email Availability
- **Has Email:** 404 (34.2%)
- **No Email:** 778 (65.8%)

### Email Quality (of 404 emails found)
- **Domain Matched (company.com):** 154 (38.1%) ✅ Good
- **Generic Domain (gmail, yahoo):** 174 (43.1%) ⚠️ Poor
- **Other Domains:** 76 (18.8%)

### The Problem
**Generic email domains outnumber company email domains** (43.1% vs 38.1%). This suggests:
- Contacts are personal emails, not business emails
- Higher chance of outdated/incorrect contact info
- Lower deliverability for B2B outreach

---

## 5. Title Analysis

| Title | Count | Percentage | Notes |
|-------|-------|------------|-------|
| Owner | 776 | 65.7% | Most common (but many are company names) |
| None | 405 | 34.3% | No title extracted |
| President | 1 | 0.1% | Rare alternative |

**Issue:** Almost no title variation. Real SMBs would have Founder, CEO, Manager, Director, etc. The uniformity suggests the pipeline is defaulting to "Owner" when it can't determine the actual role.

---

## 6. Missing Essential Information

### Good News
- **0 contacts** are missing BOTH name and email
- **0 contacts** are missing name, email, AND phone

### Explanation
Every contact has at least:
- A name (company or person) OR
- An email OR
- A phone number

However, **this doesn't mean the data is useful**. Having "Nickel Bros" as a name and no email is technically "has name" but practically useless.

---

## 7. Validation Red Flags Analysis

Top issues flagged by the validation system:

| Red Flag | Count | Notes |
|----------|-------|-------|
| No email provided | 224 | Should auto-reject |
| Unknown name and title | 223 | Should auto-reject |
| Email source is discovery with no verification | 89 | Unverified data |
| No phone number provided | 47 | Less critical |
| Generic email address | 40 | Gmail/Yahoo/etc |
| No LinkedIn profile | 34 | Missing social verification |

**Critical Observation:** The validation system IS detecting these issues (red flags), but many contacts with red flags are still marked as valid. The validation threshold is too lenient.

---

## 8. Data Source Analysis

| Source | Contacts | % | Quality |
|--------|----------|---|---------|
| google_maps_owner | 627 | 53.0% | ⚠️ Returns company names |
| openweb_contacts | 397 | 33.6% | ⚠️ Often no name |
| social_links | 296 | 25.0% | ⚠️ LinkedIn URLs, not profiles |
| serper_osint | 144 | 12.2% | Mixed quality |
| schema_org | 8 | 0.7% | Rare but good |
| page_scrape | 6 | 0.5% | Rare |

**Key Insight:** The two primary sources (google_maps_owner and openweb_contacts) are the main contributors to garbage data.

---

## 9. Garbage Data Patterns Summary

### Pattern 1: Company-Name-as-Contact (42.0%)
- **Severity:** HIGH
- **Root Cause:** google_maps_owner defaults to business name when no owner found
- **Fix:** Reject contacts where name matches company_name (case-insensitive)

### Pattern 2: Missing Names (34.2%)
- **Severity:** HIGH
- **Root Cause:** openweb_contacts extracts emails without names
- **Fix:** Require name field OR lower validation score significantly

### Pattern 3: Low Person Name Rate (23.9%)
- **Severity:** HIGH
- **Root Cause:** No NER (Named Entity Recognition) to distinguish persons from companies
- **Fix:** Implement name validation rules, parse "About/Team" pages

### Pattern 4: Low Email Domain Match (38.1%)
- **Severity:** MEDIUM
- **Root Cause:** Generic email domains prioritized over company domains
- **Fix:** Add +30 points for domain match, -20 for generic domains

### Pattern 5: Generic Email Overuse (43.1%)
- **Severity:** MEDIUM
- **Root Cause:** Personal emails scraped from websites
- **Fix:** Downgrade generic domains in scoring

### Pattern 6: High Validation Pass Rate Despite Issues (73.2%)
- **Severity:** HIGH
- **Root Cause:** Validation threshold too low (50 points)
- **Fix:** Raise threshold to 70, add penalties for red flags

---

## 10. Recommendations (Priority Order)

### CRITICAL (Fix Immediately)

#### 1. Add Name Validation Rules
```python
def is_valid_person_name(name: str, company_name: str) -> bool:
    """Reject company names, require person names."""
    if not name:
        return False

    # Exact match to company name
    if name.lower() == company_name.lower():
        return False

    # Contains company indicators
    company_words = ['inc', 'llc', 'ltd', 'corp', 'bros', 'services',
                     'construction', 'plumbing', 'roofing', 'electrical']
    name_lower = name.lower()
    if any(word in name_lower for word in company_words):
        return False

    # Require at least 2 words (first + last name)
    if len(name.split()) < 2:
        return False

    return True
```

**Impact:** Would reject 496 garbage contacts (42% reduction)

#### 2. Enforce Email Domain Matching
Update scoring:
```python
# Current
if contact.email:
    score += 15

# Proposed
if contact.email:
    email_domain = extract_domain(contact.email)
    company_domain = company.domain.replace('www.', '')

    if email_domain == company_domain:
        score += 40  # Strong signal
    elif email_domain in GENERIC_DOMAINS:
        score += 5   # Weak signal
    else:
        score += 20  # Other business domain
```

**Impact:** Would reduce validation rate from 73% to ~50%, eliminating weak contacts

#### 3. Raise Validation Threshold
```python
# Current
VALIDATION_THRESHOLD = 50

# Proposed
VALIDATION_THRESHOLD = 70
```

**Impact:** Would filter out borderline contacts, improve overall quality

### HIGH PRIORITY

#### 4. Improve google_maps_owner Source
Add post-processing to reject company names:
```python
if gmaps_owner_name:
    if not is_valid_person_name(gmaps_owner_name, company_name):
        # Discard this contact
        return None
```

**Impact:** Would eliminate the single biggest source of garbage (627 → ~300)

#### 5. Require Minimum Fields
Don't create contacts with:
- No name AND no email
- No name AND email with generic domain
- Name equals company AND no phone

**Impact:** Would reduce contact count but dramatically improve quality

### MEDIUM PRIORITY

#### 6. Add NER (Named Entity Recognition)
Use spaCy or similar to detect PERSON vs ORGANIZATION entities:
```python
import spacy
nlp = spacy.load("en_core_web_sm")

def extract_person_name(text: str) -> Optional[str]:
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    return None
```

#### 7. Parse "About Us" / "Team" Pages
Most SMB websites have owner names on these pages. Add dedicated scraper:
```python
async def scrape_team_page(domain: str) -> List[Contact]:
    """Look for /about, /team, /our-story pages"""
    # Implementation
```

---

## 11. Expected Impact of Fixes

| Metric | Current | After Fixes | Improvement |
|--------|---------|-------------|-------------|
| Contact Count | 1,182 | ~500 | -58% (quality over quantity) |
| Validation Rate | 73.2% | ~85% | +12% |
| Real Person Names | 23.9% | ~70% | +46% |
| Company-as-Name | 42.0% | <5% | -37% |
| Domain Match Rate | 38.1% | ~65% | +27% |
| Data Quality Score | 28.6/100 | ~75/100 | +46 points |

---

## 12. Cost-Benefit Analysis

### Current State
- **Cost:** $9.17 for 940 companies ($0.0098/company)
- **Usable Contacts:** ~282 (23.9% with real person names)
- **Cost per Usable Contact:** $0.033

### After Fixes (Estimated)
- **Cost:** $9.17 (same queries needed to assess quality)
- **Usable Contacts:** ~650 (70% with real person names)
- **Cost per Usable Contact:** $0.014

**Result: 2.3x improvement in cost efficiency**

---

## 13. Conclusion

The SMB pipeline is finding contacts, but **data quality is poor**. The main issues are:

1. **42% of contacts use company names instead of person names** (biggest issue)
2. **34% have no name at all**
3. **Only 24% are likely real people**
4. **Validation is too lenient** (73% pass rate despite issues)

**The validation system IS detecting problems** (red flags), but the scoring threshold allows too many low-quality contacts through.

**Recommended Action:** Implement the 3 critical fixes above, which would:
- Reject company-name-as-contact (saves validation on 496 contacts)
- Enforce email domain matching (prioritizes business emails)
- Raise validation threshold (blocks borderline contacts)

This would reduce the contact count from 1,182 to ~500, but **quality would improve from 28.6/100 to ~75/100**.

**Better to have 500 good contacts than 1,182 mostly-garbage contacts.**
