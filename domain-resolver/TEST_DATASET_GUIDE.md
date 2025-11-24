# Building Diverse Test Datasets

This guide explains how to build comprehensive test datasets across multiple industries to validate the domain resolver's performance.

---

## Overview

The test dataset system allows you to:
- **Generate test companies** from 5 wildly different industries
- **Strip domains** to create a realistic test scenario
- **Validate accuracy** against ground truth
- **Analyze performance** by industry

---

## Approach 1: People Data Labs (Recommended - FREE)

### Step 1: Download Dataset

**Option A: Kaggle** (Easiest)
1. Visit: https://www.kaggle.com/datasets/peopledatalabssf/free-7-million-company-dataset
2. Click "Download" (requires free Kaggle account)
3. Extract `companies_sorted.csv` to the `domain-resolver` directory

**Option B: AWS Marketplace**
1. Visit: https://aws.amazon.com/marketplace/pp/prodview-ryqp3ngwlywwg
2. Subscribe (free)
3. Download dataset

**Option C: Snowflake/Databricks**
- Available via free data sharing

**Dataset Size:** ~7-22 million companies
**Cost:** FREE
**Format:** CSV with columns: name, website, industry, locality, country, size, etc.

### Step 2: Build Test Dataset

```bash
# Basic usage (50 companies per industry = 250 total)
python build_test_dataset.py companies_sorted.csv

# Custom size (100 companies per industry = 500 total)
python build_test_dataset.py companies_sorted.csv 100
```

**What this does:**
1. Loads the full dataset
2. Filters companies by industry keywords
3. Samples N companies from each of 5 industries:
   - Healthcare (Hospitals & Medical)
   - Manufacturing (Chemical/Industrial)
   - Food Service (Restaurants/QSR)
   - Technology (SaaS/Software)
   - Transportation (Trucking/Logistics)
4. Creates TWO output files:
   - `test/test_companies_diverse.csv` (no domains - for testing)
   - `test/ground_truth_diverse.csv` (with domains - for validation)

### Step 3: Run Domain Resolver

```bash
# Resolve domains for test companies
python domain_resolver.py test/test_companies_diverse.csv output/test_diverse_results.csv
```

### Step 4: Analyze Results by Industry

```bash
# Generate industry-specific performance metrics
python analyze_by_industry.py \\
    output/test_diverse_results.csv \\
    test/ground_truth_diverse.csv \\
    test/test_companies_diverse.csv
```

**Output:**
- Console report with per-industry metrics
- `output/industry_analysis.csv` with detailed stats

---

## Approach 2: Apollo.io API (Alternative)

### When to Use:
- You prefer API-based approach
- You need NAICS-level precision
- You want fresh, real-time data

### Limitations:
- **Free tier:** Only 100 companies/month (vs 250+ with PDL)
- **Paid tier:** $49/month required for larger datasets

### Setup:

1. **Get API Key:**
   - Sign up at https://www.apollo.io
   - Go to Settings → API
   - Copy API key

2. **Create the script:**

```python
# build_test_dataset_apollo.py
import requests
import pandas as pd

APOLLO_API_KEY = "your_api_key_here"

def search_by_naics(naics_code, limit=20):
    """Search companies by NAICS code"""
    url = "https://api.apollo.io/v1/mixed_companies/search"

    data = {
        "api_key": APOLLO_API_KEY,
        "q_organization_keyword_tags": [naics_code],
        "page": 1,
        "per_page": limit
    }

    response = requests.post(url, json=data)
    return response.json()

# Example: Get 20 hospitals (NAICS 622)
hospitals = search_by_naics("622", 20)

# Extract domain, name, location
companies = []
for org in hospitals.get('accounts', []):
    companies.append({
        'name': org.get('name'),
        'domain': org.get('website_url'),
        'city': org.get('city'),
        'industry': 'Healthcare'
    })
```

---

## The 5 Selected Industries

### Why These Industries?

Each industry is **maximally different** across multiple dimensions:

| Industry | Regulatory Body | Business Model | Employee Type | Footprint |
|----------|----------------|----------------|---------------|-----------|
| Healthcare | CMS | Patient care | Medical professionals | Hospitals, clinics |
| Manufacturing | EPA, OSHA | Physical production | Factory workers | Plants, facilities |
| Food Service | Local health depts | Hospitality | Service workers | Restaurants, catering |
| Technology | None | Subscriptions | Engineers | Virtual/cloud |
| Transportation | DOT, FMCSA | Logistics | Drivers | Fleet operations |

### Industry Details:

**1. Healthcare - Hospitals & Medical Facilities**
- **NAICS Codes:** 622xxx (Hospitals), 621xxx (Ambulatory)
- **Keywords:** hospital, medical center, urgent care, clinic, healthcare
- **Characteristics:**
  - Heavily regulated (CMS, HIPAA)
  - Patient-focused operations
  - 10-5,000 employees
  - High Google Maps presence (phone verified)
- **Expected Accuracy:** 90-95% (strong Places API hits)

**2. Manufacturing - Chemical/Industrial**
- **NAICS Codes:** 325xxx (Chemical), 332xxx (Fabricated Metal), 333xxx (Machinery)
- **Keywords:** chemical, manufacturing, industrial, fabrication, factory
- **Characteristics:**
  - EPA/OSHA regulated
  - Physical production facilities
  - 50-1,000 employees
  - Environmental permits
- **Expected Accuracy:** 85-92% (medium online presence)

**3. Food Service - Restaurants/QSR**
- **NAICS Codes:** 722xxx (Food Services)
- **Keywords:** restaurant, food service, catering, dining, cafe
- **Characteristics:**
  - Local health department oversight
  - Consumer-facing
  - Multi-location/franchise models
  - 5-500 employees
- **Expected Accuracy:** 85-90% (franchises easier than independents)

**4. Technology - SaaS/Software**
- **NAICS Codes:** 511210 (Software Publishers), 518210 (Cloud)
- **Keywords:** software, saas, cloud, technology, platform
- **Characteristics:**
  - Zero regulatory footprint
  - Subscription business model
  - 10-500 employees
  - Strong online presence
- **Expected Accuracy:** 95-98% (best resolution, clean domains)

**5. Transportation - Trucking/Logistics**
- **NAICS Codes:** 484xxx (Truck Transportation), 493xxx (Warehousing)
- **Keywords:** trucking, logistics, freight, transportation, shipping
- **Characteristics:**
  - DOT/FMCSA regulated
  - Fleet-based operations
  - 10-200 employees
  - SAFER database available
- **Expected Accuracy:** 80-88% (smaller online footprint)

---

## Expected Performance

### Overall Metrics (250 companies)

| Metric | Expected | Notes |
|--------|----------|-------|
| Overall Accuracy | 87-93% | Weighted across 5 industries |
| High Confidence (≥85) | 85-90% | Auto-accepted results |
| Coverage | 95-98% | Domain found (correct or not) |
| Manual Review Rate | 5-10% | Low confidence flagged |
| Total Cost | $0.10-1.25 | Serper + Discolike + scraping |
| Total Time | 5-8 minutes | With 10 parallel workers |

### Per-Industry Predictions

| Industry | Accuracy | Coverage | Avg Confidence | Notes |
|----------|----------|----------|----------------|-------|
| Technology | 95-98% | 98% | 92 | Clean domains, strong presence |
| Healthcare | 90-95% | 96% | 88 | Phone verification helps |
| Food Service | 85-90% | 94% | 82 | Franchises better than independents |
| Manufacturing | 85-92% | 93% | 80 | Some complex corporate structures |
| Transportation | 80-88% | 90% | 75 | Smaller businesses, less presence |

---

## Analysis Outputs

### Console Report

```
================================================================================
INDUSTRY-SPECIFIC PERFORMANCE ANALYSIS
================================================================================

TECHNOLOGY
------------------------------------------------------------
  Total Companies:       50
  Domains Found:         49 (98.0% coverage)
  Correct Matches:       48 (96.0% accuracy)
  Average Confidence:    92.3
  High Confidence (≥85): 47 (97.9% accurate)
  Manual Review Needed:  2.0%

  Resolution Sources:
    - google_kg: 28 (56.0%)
    - google_places: 15 (30.0%)
    - serper_search: 6 (12.0%)
    - llm_verified: 1 (2.0%)
```

### CSV Export

`output/industry_analysis.csv` contains:
- Industry
- Total companies
- Accuracy %
- Coverage %
- Average confidence
- High confidence count & accuracy
- Manual review rate

---

## Interpreting Results

### Good Performance Indicators:

✅ **Overall accuracy ≥90%**
✅ **High-confidence accuracy ≥95%** (results with confidence ≥85)
✅ **Manual review rate <10%**
✅ **Technology & Healthcare >90% accuracy**

### Red Flags:

❌ **Overall accuracy <85%** → Check fuzzy matching thresholds
❌ **High false positive rate** → Tighten parking detection
❌ **Transportation <75%** → Consider enabling Discolike
❌ **High manual review rate (>15%)** → Lower confidence thresholds

---

## Troubleshooting

### Low Accuracy in Specific Industry

**Problem:** Transportation only 70% accurate (expected 80-88%)

**Solutions:**
1. Enable Discolike for medium-confidence results
2. Lower auto-accept threshold from 85 to 80
3. Increase scraping trigger threshold
4. Check if test companies are very small businesses

### Not Enough Companies Found

**Problem:** Only 20 Manufacturing companies found (expected 50)

**Solutions:**
1. Expand keyword list in `build_test_dataset.py`
2. Use broader industry filters
3. Accept smaller sample size for that industry
4. Try Apollo.io API for NAICS-based search

### Dataset Download Issues

**Problem:** People Data Labs CSV not downloading

**Solutions:**
1. Create free Kaggle account first
2. Try AWS Marketplace approach
3. Use Apollo.io API instead (100 companies free)
4. Contact PDL support for Snowflake/Databricks access

---

## Advanced Usage

### Custom Industries

Edit `INDUSTRIES` dict in `build_test_dataset.py`:

```python
INDUSTRIES = {
    'Your Custom Industry': {
        'keywords': ['keyword1', 'keyword2', 'keyword3'],
        'naics_codes': ['123', '456'],
        'description': 'Industry description'
    }
}
```

### Larger Test Sets

```bash
# 100 companies per industry (500 total)
python build_test_dataset.py companies_sorted.csv 100

# 200 companies per industry (1,000 total)
python build_test_dataset.py companies_sorted.csv 200
```

**Note:** Larger test sets take longer to resolve but provide better statistical confidence.

### International Companies

Modify filter in `build_test_dataset.py`:

```python
# Change from:
(industry_df['country'] == 'united states')

# To:
(industry_df['country'].isin(['united states', 'canada', 'united kingdom']))
```

**Caveat:** International domains may have lower accuracy due to different business directory coverage.

---

## Files Generated

```
domain-resolver/
├── test/
│   ├── test_companies_diverse.csv      # Test input (no domains)
│   ├── ground_truth_diverse.csv        # Expected domains
│   └── test_results.csv                # (after testing)
│
└── output/
    ├── test_diverse_results.csv        # Resolver results
    └── industry_analysis.csv           # Per-industry stats
```

---

## Next Steps

1. ✅ Generate test dataset
2. ✅ Run domain resolver
3. ✅ Analyze by industry
4. 🔄 Iterate based on findings:
   - Adjust confidence thresholds
   - Enable/disable Discolike
   - Tune fuzzy matching
   - Enhance parking detection
5. 🎯 Deploy to production when accuracy targets met

---

## Support

**Questions?**
- Check main `README.md` for domain resolver usage
- Review logs in `logs/domain_resolver.log`
- Examine detailed lookups in `logs/lookups.jsonl`

**Accuracy Issues?**
- Run `analyze_by_industry.py` to identify problem industries
- Check failure patterns in console output
- Adjust thresholds in `config.yaml`

**Dataset Issues?**
- Verify People Data Labs CSV is complete
- Check keyword filters in `build_test_dataset.py`
- Try Apollo.io API as alternative
