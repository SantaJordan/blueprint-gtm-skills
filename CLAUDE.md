## Contact Finder - Quick Reference

See `contact-finder/README.md` for full documentation.

### SMB Pipeline (Active)

**Goal:** Find person names (first + last) who are decision-makers at small businesses.
- Primary: Person name
- Secondary: LinkedIn URL
- Tertiary: Email/phone (nice-to-have)

**Latest Results (v4):** 36.8% validation rate on 1,000 companies

```
Input (CSV/JSON)
    |
    v
1. Data Fill (Serper $0.001) -> domain, phone, owner name
    |
    v
2. Website Fallback (ZenRows ~$0.01) -> Schema.org, content
    |
    v
3. Serper OSINT ($0.001) -> owner name from search
    |
    v
4. Social Links (Serper $0.001) -> LinkedIn for names
    |
    v
5. LLM Validation (GPT-4o-mini) -> confidence, reasoning
    |
    v
Output (ContactResult[])
```

### Key Modules

| Module | Description |
|--------|-------------|
| `smb_pipeline.py` | Full SMB contact discovery |
| `serper_osint.py` | Google search OSINT |
| `serper_filler.py` | Fill missing data |
| `contact_judge.py` | LLM validation (primary) |
| `simple_validator.py` | Rule-based validation (fallback) |

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

## Validation Scoring

### LLM Validation (Primary)

Uses GPT-4o-mini with SMB-specific rules:
- Missing email/phone is NOT a red flag for SMBs
- REJECT if name looks like company name (LLC, Inc, etc.)
- Owner title from search = HIGH confidence

**Thresholds:** 50+ = valid, 70+ = high confidence

### Simple Validator (Fallback)

| Source | Points |
|--------|--------|
| google_maps_owner | +40 |
| google_maps | +35 |
| openweb_contacts | +25 |
| Strong owner title | +40 |
| Has LinkedIn | +20 |
| Has Facebook | +15 |
| Email matches domain | +10 |
| Has phone | +5 |

**Threshold: 50 points = valid contact**
