# Quick Reference - SMB Contact Discovery Success Patterns

## At a Glance

| Metric | Value |
|--------|-------|
| Overall Success Rate | 69.8% |
| Best Source | google_maps_owner (90.1%) |
| Best Vertical | Tree Services (81.0%) |
| Best ROI | 306.8 valid contacts per $ |
| Avg Cost | $0.007 per company |

---

## Top 3 Data Sources

1. **google_maps_owner** - 90.1% success, 83.7 confidence
2. **social_links** - 83.1% success (LinkedIn verification)
3. **serper_osint** - 72.2% success (gap filler)

**AVOID:** schema_org (12.5% success)

---

## Top 5 Verticals

1. Tree Services - 81.0%
2. Junk Removal - 77.0%
3. General Contractors - 76.0%
4. Landscaping - 74.0%
5. Roofing - 70.0%

**AVOID:** HVAC (56.7%), Movers (60.0%)

---

## Best ROI Strategies

| Strategy | Cost | Success | Valid/$ |
|----------|------|---------|---------|
| GMaps + OpenWeb + Serper | $0.007 | 91.7% | 306.8 |
| OpenWeb + Serper | $0.006 | 100% | 281.7 |
| GMaps + OpenWeb | $0.006 | 94.3% | 238.5 |

---

## Validation Rules (What Works)

✅ **Title presence** - Strongest signal (+45.9%)
✅ **Phone + Title** - Best combination
✅ **Owner/CEO/Founder** - Highest confidence
✅ **LinkedIn verification** - Strong validation

**Generic emails are correctly rejected** (info@, contact@, sales@)

---

## 3 Pipeline Strategies

### Budget Play ($0.002/company)
```
Google Maps → Early Exit (if confidence ≥85)
Success: 91.9% | ROI: 459.5 valid/$
```

### Quality Play ($0.004/company)
```
Google Maps → Social Links → Validation
Success: 87.0% | ROI: 217.5 valid/$ + LinkedIn
```

### Premium Play ($0.015/company)
```
BBB → GMaps → OpenWeb → Social → Validation
Success: 100% (small sample) | Multiple contacts/company
```

---

## Quick Wins (Implement This Week)

1. Remove schema_org (12.5% success)
2. Early exit when GMaps confidence ≥85
3. Focus on tree services + junk removal

---

## Budget Examples

### $100 Budget
- **GMaps only:** ~50,000 companies = ~45,950 valid contacts
- **Tree services focus:** ~40,500 valid contacts (81% success)

### $1,000 Budget
- **GMaps + Social:** ~250,000 companies = ~190,000 valid (with LinkedIn)
- **General contractors:** Best ROI vertical

### $10,000 Budget
- Multi-tier: ~2.2M valid contacts across all strategies

---

## Success Pattern Example

**Company:** Alford Plumbing
- **Sources:** google_maps_owner + social_links + openweb_contacts
- **Result:** 2 valid contacts, 90.0 confidence
- **Contact 1:** Owner name, phone, LinkedIn verified
- **Contact 2:** Matching phone, domain email

**Why it worked:** Multiple sources corroborated same contact

---

## Red Flags (Failures)

- No name/title
- Generic email (info@, contact@)
- No phone number
- openweb_contacts as sole source

---

## Contact Characteristics

**Valid Contacts Have:**
- Title: 78%
- Phone: 84%
- Email: 22% (low = correct, rejects generic)

**Invalid Contacts Have:**
- Title: 32%
- Phone: 75%
- Email: 68% (high = generic emails)

---

## Next Steps

1. Test BBB discovery at scale (currently 11 runs, 100% success)
2. Build vertical-specific pipelines for home services
3. Optimize early exit thresholds (test 80, 85, 90)

---

**Full Analysis:** See EXECUTIVE_SUMMARY.md and SUCCESS_PATTERNS_SUMMARY.md
