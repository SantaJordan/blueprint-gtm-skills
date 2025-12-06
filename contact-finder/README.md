# Contact Finder

Multi-source contact discovery system for finding decision-makers at companies. **Optimized for SMB owner discovery.**

## Overview

| Pipeline | Status | Target | Validation | Cost/Contact |
|----------|--------|--------|------------|--------------|
| **SMB Pipeline** | **Active** | Small businesses (plumbers, bakeries, etc.) | LLM + Rules | $0.02-0.03 |
| Enterprise Pipeline | Deprecated | Fortune 1000 companies | LLM-based | $0.50-4.00 |

**Latest Results (v4):** 36.8% validation rate on 1,000 SMB companies

---

## Quick Start

### SMB Pipeline

```python
import asyncio
from contact_finder.modules.pipeline.smb_pipeline import SMBContactPipeline

async def find_smb_owners():
    pipeline = SMBContactPipeline(
        serper_api_key="your_serper_key",
        openai_api_key="your_openai_key",
        concurrency=10
    )

    try:
        result = await pipeline.run("companies.csv", limit=100)

        for company in result.results:
            if company.contacts:
                best = company.contacts[0]
                print(f"{company.company_name}: {best.name} ({best.title})")
    finally:
        await pipeline.close()

asyncio.run(find_smb_owners())
```

---

## SMB Pipeline Architecture

The pipeline finds **person names** (first + last) who are decision-makers, with LinkedIn URLs as a secondary goal. Email/phone are nice-to-have, not required.

```
INPUT (CSV/JSON)
    |
    v
+-------------------+
| 1. Input Analysis |  CSVExplorer: detect fields, map columns
+-------------------+
    |
    v
+-------------------+
| 2. Data Fill      |  Serper OSINT ($0.001)
|    (PRIMARY)      |  -> domain, phone, owner name
+-------------------+
    |
    v
+------------------------+
| 3. Website Fallback    |  ZenRows (~$0.01)
|    (IF NEEDED)         |  -> Schema.org, page content
+------------------------+
    |
    v
+-------------------+
| 4. Serper OSINT   |  Serper ($0.001)
|    (IF NEEDED)    |  -> owner name from search results
+-------------------+
    |
    v
+------------------------+
| 5. Social Links Search |  Serper ($0.001)
|                        |  -> LinkedIn URL for names found
+------------------------+
    |
    v
+------------------------+
| 6. LLM Validation      |  GPT-4o-mini ($0.001)
|    (PRIMARY)           |  -> confidence, reasoning
+------------------------+
    |
    v
+-------------------+
| 7. Simple Rules   |  No LLM (fallback)
|    (FALLBACK)     |  -> score-based validation
+-------------------+
    |
    v
OUTPUT (ContactResult[])
```

**Cost breakdown:**
- Serper queries: $0.001-0.003
- ZenRows (if needed): ~$0.01
- LLM validation: ~$0.001
- **Total: $0.02-0.03 per company**

---

## Validation

### LLM Validation (Primary)

The `ContactJudge` uses GPT-4o-mini with SMB-specific rules:

**Goals (in priority order):**
1. **Primary**: Find a real PERSON NAME (first + last name)
2. **Secondary**: Find LinkedIn URL if available
3. **Tertiary**: Email and phone are nice-to-have

**Key Rules:**
- Missing email is NOT a red flag for SMBs
- Missing phone is NOT a red flag for SMBs
- REJECT if name looks like a company name (LLC, Inc, Corp, etc.)
- Owner/Founder title from Google Maps = HIGH confidence

**Confidence Thresholds:**
- 70-100: Strong match - owner name from reliable source
- 50-69: Good match - name + owner title
- 30-49: Weak match - name found but no owner title
- 0-29: No match or company name instead of person

### Simple Validator (Fallback)

Rule-based scoring when LLM validation fails:

**Source Scores:**
| Source | Points |
|--------|--------|
| `google_maps_owner` | +40 |
| `google_maps` | +35 |
| `openweb_contacts` | +25 |
| `website_schema` | +25 |
| `input_csv` | +20 |
| `social_links` | +20 |
| `website_scrape` | +15 |
| `social_links_fb` | +15 |
| `serper_osint` | +10 |

**Title Scores:**
| Title Type | Points |
|------------|--------|
| Strong owner (Owner, CEO, Founder, President, Proprietor) | +40 |
| Owner-related (Director, Manager, GM, Principal) | +30 |
| Any title | +10 |

**Bonuses:**
| Condition | Points |
|-----------|--------|
| Has LinkedIn URL | +20 |
| Has Facebook URL | +15 |
| Google Maps 20+ reviews | +10 |
| Has social presence (FB/IG/Twitter) | +10 |
| Email matches domain | +10 |
| Full name (first + last) | +5 |
| Has phone | +5 |

**Threshold: 50 points = valid contact**

---

## Modules Reference

### Active Modules

#### Discovery (`modules/discovery/`)

| Module | Description | Cost |
|--------|-------------|------|
| `serper_osint.py` | Google search OSINT for owner names | $0.001/query |
| `serper_filler.py` | Fill missing domain, phone, owner | $0.001/query |
| `website_extractor.py` | ZenRows-based contact extraction | ~$0.01/page |
| `openweb_ninja.py` | Google Maps + Website Contacts (RapidAPI) | $0.002/query |

#### Validation (`modules/validation/`)

| Module | Description |
|--------|-------------|
| `contact_judge.py` | LLM validation with GPT-4o-mini (primary) |
| `simple_validator.py` | Rule-based SMB validation (fallback) |
| `email_validator.py` | Email validation with catch-all detection |
| `linkedin_normalizer.py` | LinkedIn URL standardization |

#### Pipeline (`modules/pipeline/`)

| Module | Description |
|--------|-------------|
| `smb_pipeline.py` | Full SMB contact discovery pipeline |

#### Input (`modules/input/`)

| Module | Description |
|--------|-------------|
| `csv_explorer.py` | Dynamic CSV/JSON field detection and mapping |

#### LLM (`modules/llm/`)

| Module | Description |
|--------|-------------|
| `provider.py` | LLM provider factory |
| `openai_provider.py` | OpenAI GPT integration |

### Experimental Modules (Not Production Ready)

| Module | Description |
|--------|-------------|
| `pipeline/llm_controller.py` | LLM-first agent loop (future) |
| `pipeline/adaptive_controller.py` | Business type classification (future) |
| `pipeline/tool_wrappers.py` | Tool wrappers for LLM controller |
| `validation/incremental_validator.py` | Quick pre-validation checks |

### Deprecated Modules (Enterprise Pipeline)

| Module | Description |
|--------|-------------|
| `contact_finder.py` | Enterprise pipeline entry point |
| `discovery/multi_source_finder.py` | Serper + Blitz with LLM reconciliation |
| `discovery/linkedin_company.py` | Company LinkedIn URL discovery |
| `discovery/contact_search.py` | Enterprise search orchestration |
| `enrichment/blitz.py` | LinkedIn email/phone ($0.50-4/query) |
| `enrichment/scrapin.py` | LinkedIn profiles (FREE, 35% accuracy) |
| `enrichment/waterfall.py` | Multi-source enrichment |
| `enrichment/leadmagic.py` | Email finder (8.9% accuracy, not recommended) |
| `enrichment/exa.py` | Semantic search (unused) |

---

## Configuration

### Environment Variables

```bash
# Required (SMB Pipeline)
export SERPER_API_KEY="your_serper_key"
export OPENAI_API_KEY="your_openai_key"

# Optional
export ZENROWS_API_KEY="your_zenrows_key"    # Website scraping
export RAPIDAPI_KEY="your_rapidapi_key"      # OpenWeb Ninja (optional)
```

---

## Testing

### Run SMB Pipeline Test

```bash
SERPER_API_KEY="..." OPENAI_API_KEY="..." \
python -u -m evaluation.scripts.run_smb_v2_test \
  --input evaluation/data/smb_sample.json \
  --output evaluation/results/smb_test.json \
  --limit 100 \
  --concurrency 10
```

---

## Input Formats

### CSV Format
```csv
company_name,domain,city,state,vertical
"Joe's Plumbing","joesplumbing.com","Denver","CO","plumbing"
```

### JSON Format
```json
[
  {
    "company_name": "Joe's Plumbing",
    "domain": "joesplumbing.com",
    "city": "Denver",
    "state": "CO",
    "vertical": "plumbing"
  }
]
```

The `CSVExplorer` automatically detects and maps columns.

---

## Output Format

```python
@dataclass
class ContactResult:
    name: str | None           # Person's full name
    email: str | None          # Email address (optional)
    phone: str | None          # Phone number (optional)
    title: str | None          # Job title (Owner, CEO, etc.)
    linkedin_url: str | None   # LinkedIn profile URL
    sources: list[str]         # Where contact was found
    is_valid: bool             # Passed validation
    confidence: float          # 0-100 confidence score
    validation_reasons: list   # Human-readable explanations
```

---

## Performance Results

### SMB Pipeline v4 (December 2024)

| Metric | Value |
|--------|-------|
| Companies Tested | 1,000 |
| Contacts Found | 55.2% |
| Contacts Validated | **36.8%** |
| Cost per Company | ~$0.024 |
| Processing Time | ~5 sec/company |

**Improvements over v2:**
- Validation rate: 15.7% -> 36.8% (+134%)
- LLM prompt tuned for SMB context
- Company names correctly rejected
