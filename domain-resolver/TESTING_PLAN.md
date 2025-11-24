# Domain Resolver - Complete Testing Plan

**Status:** Kaggle dataset downloaded locally ✓
**Discolike:** ENABLED ✓
**Ollama:** Running on localhost:11434 ✓

---

## Quick Test (5 minutes)

### 1. Test with Example Data
```bash
cd /Users/jordancrawford/Desktop/Blueprint-GTM-Skills/domain-resolver

# Make sure Ollama is running
# In separate terminal: ollama serve

# Test with example companies
python domain_resolver.py example_input.csv

# Check results
cat output/resolved.csv
```

**Expected:** 5 companies resolved in ~30 seconds with 95%+ accuracy

---

## Full Diverse Industry Test (Complete Workflow)

### Step 1: Generate Test Dataset from Kaggle Data

```bash
# Locate your Kaggle download (adjust path if needed)
# Typical locations:
# - ~/Downloads/companies_sorted.csv
# - ~/kaggle/companies_sorted.csv

# Generate 250 test companies (50 per industry)
python build_test_dataset.py ~/Downloads/companies_sorted.csv 50

# OR for larger test (500 companies)
python build_test_dataset.py ~/Downloads/companies_sorted.csv 100
```

**Output files created:**
- `test/test_companies_diverse.csv` - Input for testing (domains stripped)
- `test/ground_truth_diverse.csv` - Expected domains for validation

**Industries selected automatically:**
1. Healthcare (hospitals, medical centers)
2. Manufacturing (chemical, industrial)
3. Food Service (restaurants, QSR)
4. Technology (SaaS, software)
5. Transportation (trucking, logistics)

---

### Step 2: Run Domain Resolver on Test Dataset

```bash
# Process all test companies
python domain_resolver.py test/test_companies_diverse.csv output/test_diverse_results.csv

# This will take 5-8 minutes for 250 companies (with 10 parallel workers)
# Watch for:
# - Stage 1: Serper Places hits (phone verification)
# - Stage 2: Knowledge Graph detections
# - Stage 3: Discolike verifications (ENABLED)
# - Stage 4: LLM deep scraping
```

**What to monitor:**
- Progress bar shows completion
- Log messages indicate which stage resolved each company
- High confidence (85+) auto-accepted
- Medium confidence (50-84) triggers Discolike or scraping
- Low confidence (<70) flagged for manual review

---

### Step 3: Validate Results & Analyze by Industry

```bash
# Run industry-specific analysis
python analyze_by_industry.py \
    output/test_diverse_results.csv \
    test/ground_truth_diverse.csv \
    test/test_companies_diverse.csv
```

**Console output includes:**
1. **Per-industry breakdown:**
   - Accuracy percentage
   - Coverage (domains found)
   - Average confidence
   - High-confidence accuracy (≥85)
   - Manual review rate

2. **Comparative summary** (all industries ranked)

3. **Failure analysis:**
   - Not found vs wrong domain
   - Sample failures per industry

4. **CSV export:** `output/industry_analysis.csv`

---

## Expected Results Benchmark

### Target Metrics (250 companies):

| Metric | Target | Action if Below Target |
|--------|--------|----------------------|
| **Overall Accuracy** | 87-93% | Check logs, adjust thresholds |
| **Technology** | 95-98% | Should always be highest |
| **Healthcare** | 90-95% | Phone verification helps |
| **Food Service** | 85-90% | Franchises perform better |
| **Manufacturing** | 85-92% | Complex domains are harder |
| **Transportation** | 80-88% | Expected to be lowest |
| **High Conf Accuracy** | 98%+ | Results with confidence ≥85 |
| **Cost** | $0.35-1.25 | Serper + Discolike + scraping |
| **Time** | 5-8 min | With 10 parallel workers |

---

## Interpreting Results

### ✅ GOOD Performance Indicators:

- Overall accuracy ≥90%
- Technology & Healthcare both >93%
- High-confidence accuracy ≥95%
- Manual review rate <10%
- Most resolutions via Stages 1-2 (Places/Search)

### ⚠️ Needs Tuning:

- Overall accuracy 85-90%
- Transportation <75%
- Manual review rate 10-15%
- High scraping usage (>20%)

**Actions:**
1. Lower `auto_accept` threshold from 85 to 80
2. Increase `needs_scraping` threshold to trigger earlier
3. Check fuzzy matching thresholds

### ❌ RED FLAGS:

- Overall accuracy <85%
- High false positive rate (wrong domains with high confidence)
- Technology <90% (should be easiest)
- Manual review >20%

**Actions:**
1. Check Ollama is running properly
2. Review parking domain detection
3. Examine logs: `tail -100 logs/domain_resolver.log`
4. Check API keys are valid
5. Review failed cases in console output

---

## Detailed Logs & Debugging

### Log Locations:

```bash
# Main log file
tail -f logs/domain_resolver.log

# Detailed lookup logs (JSONL format)
tail -20 logs/lookups.jsonl | jq .

# Filter only failures
cat logs/lookups.jsonl | jq 'select(.result.domain == null)'

# Filter by confidence range
cat logs/lookups.jsonl | jq 'select(.result.confidence < 70)'
```

### Check API Usage:

```bash
# Count Serper calls
grep "Serper" logs/domain_resolver.log | wc -l

# Count Discolike calls
grep "Discolike" logs/domain_resolver.log | wc -l

# Count LLM calls
grep "LLM judgment" logs/domain_resolver.log | wc -l
```

---

## Iteration Workflow

### Round 1: Initial Test
```bash
python build_test_dataset.py ~/Downloads/companies_sorted.csv 50
python domain_resolver.py test/test_companies_diverse.csv output/round1_results.csv
python analyze_by_industry.py output/round1_results.csv test/ground_truth_diverse.csv test/test_companies_diverse.csv
```

**Record:**
- Overall accuracy: ____%
- Technology accuracy: ____%
- Transportation accuracy: ____%
- Manual review rate: ____%

### Round 2: Tune Config

Edit `config.yaml` based on Round 1 results:

```yaml
# If accuracy is good but manual review high:
thresholds:
  auto_accept: 80  # Lower from 85 (accept more)
  manual_review: 65  # Lower from 70 (flag fewer)

# If false positives are high:
thresholds:
  auto_accept: 90  # Raise from 85 (be more strict)

# If Transportation is struggling:
stages:
  use_discolike: true  # Already enabled ✓
thresholds:
  needs_scraping: 60  # Trigger earlier (from 50)

# If too slow:
processing:
  max_workers: 15  # Increase from 10 (more parallel)

# If LLM errors:
llm:
  model: "qwen2.5:7b"  # Use smaller/faster model
  timeout: 45  # Increase timeout (from 30)
```

**Re-run:**
```bash
python domain_resolver.py test/test_companies_diverse.csv output/round2_results.csv
python analyze_by_industry.py output/round2_results.csv test/ground_truth_diverse.csv test/test_companies_diverse.csv
```

**Compare:**
```bash
diff <(cat output/round1_results.csv | head -5) <(cat output/round2_results.csv | head -5)
```

### Round 3: Production Config

Once you hit targets:
- Overall accuracy ≥90%
- High-confidence accuracy ≥95%
- Manual review <10%

**Save your config:**
```bash
cp config.yaml config_production.yaml
```

---

## Troubleshooting Common Issues

### Issue: "Ollama connection refused"
```bash
# In separate terminal:
ollama serve

# Verify it's running:
curl http://localhost:11434/api/generate
```

### Issue: "Serper API error 429 (Rate limit)"
```yaml
# Reduce parallel workers in config.yaml:
processing:
  max_workers: 5  # From 10
```

### Issue: Low accuracy for all industries (<80%)
```bash
# Check Ollama model is installed:
ollama list | grep qwen2.5:14b

# If not installed:
ollama pull qwen2.5:14b

# Check API keys are valid:
grep "api_keys" config.yaml
```

### Issue: "Dataset not found" when building test
```bash
# Find your Kaggle download:
find ~ -name "companies_sorted.csv" 2>/dev/null

# Use the full path:
python build_test_dataset.py /path/to/companies_sorted.csv
```

### Issue: Discolike errors
```bash
# Check if Discolike is actually being called:
grep "Discolike" logs/domain_resolver.log

# If no calls, check config:
grep "use_discolike" config.yaml

# Should show: use_discolike: true
```

### Issue: Out of memory (LLM)
```yaml
# Use smaller model in config.yaml:
llm:
  model: "qwen2.5:7b"  # Or qwen2.5:3b for even less memory
```

---

## Cost Tracking

### Estimate Costs:

**Serper.dev:**
- Free tier: 2,500 queries
- 250 companies ≈ 300-400 Serper calls
- Cost: $0 (within free tier) or ~$0.12

**Discolike:**
- Used for ~10-20% of companies (medium confidence)
- 250 companies × 15% = ~40 calls
- Estimated: $0.50-2.00

**ZenRows (optional):**
- Used for ~5% of companies (anti-bot sites)
- 250 companies × 5% = ~13 calls
- Cost: ~$0.04

**Total for 250 companies: $0.15-2.20**

---

## Advanced Testing

### Test Specific Industry Only:

Edit `build_test_dataset.py` to only include one industry:

```python
INDUSTRIES = {
    'Healthcare': {
        'keywords': ['hospital', 'medical center', 'urgent care'],
        'naics_codes': ['622'],
        'description': 'Testing healthcare only'
    }
}
```

Run: `python build_test_dataset.py ~/Downloads/companies_sorted.csv 100`

### Test with Different Company Sizes:

Add size filter in `build_test_dataset.py`:

```python
# Filter for large companies only (1000+ employees)
industry_df = industry_df[
    industry_df['size'].str.contains('1000', na=False)
]
```

### Test International Companies:

```python
# Change country filter
industry_df = industry_df[
    industry_df['country'].isin(['united states', 'canada', 'united kingdom'])
]
```

---

## Files You'll Generate

```
domain-resolver/
├── test/
│   ├── test_companies_diverse.csv      ← Generated by build script
│   └── ground_truth_diverse.csv        ← Generated by build script
│
├── output/
│   ├── test_diverse_results.csv        ← Resolver output
│   ├── industry_analysis.csv           ← Analysis output
│   ├── manual_review.csv               ← Low confidence cases
│   └── resolved.csv                    ← Quick test results
│
└── logs/
    ├── domain_resolver.log             ← Main log
    └── lookups.jsonl                   ← Detailed lookup logs
```

---

## Success Criteria Checklist

Before deploying to production:

- [ ] Overall accuracy ≥90%
- [ ] Technology industry ≥95%
- [ ] Healthcare industry ≥90%
- [ ] High-confidence accuracy ≥95%
- [ ] Manual review rate <10%
- [ ] False positive rate <5%
- [ ] No API errors in logs
- [ ] Ollama running stable
- [ ] Cost per 1,000 lookups <$5
- [ ] Speed: 1,000 companies in <15 minutes

---

## Quick Command Reference

```bash
# Full test workflow (copy-paste ready)
cd /Users/jordancrawford/Desktop/Blueprint-GTM-Skills/domain-resolver

# 1. Generate test data
python build_test_dataset.py ~/Downloads/companies_sorted.csv 50

# 2. Run resolver
python domain_resolver.py test/test_companies_diverse.csv output/test_results.csv

# 3. Analyze
python analyze_by_industry.py \
    output/test_results.csv \
    test/ground_truth_diverse.csv \
    test/test_companies_diverse.csv

# 4. Review logs
tail -50 logs/domain_resolver.log
cat output/industry_analysis.csv
```

---

## Next Steps After Testing

1. **If accuracy ≥90%:** Deploy to production, process real data
2. **If accuracy 85-90%:** Tune config, re-test
3. **If accuracy <85%:** Review logs, check for systematic issues
4. **Monitor costs:** Track actual API usage vs estimates
5. **Iterate:** Continuously improve based on real-world performance

---

**Last Updated:** 2025-11-23
**Ollama Status:** Running ✓
**Discolike:** Enabled ✓
**Dataset:** Kaggle downloaded ✓
**Ready to test!** 🚀
