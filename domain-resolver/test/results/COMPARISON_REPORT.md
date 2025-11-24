# API Comparison Test Report
Generated: 2025-11-23 18:21:35

## Summary

| Configuration | Accuracy | Precision | Recall | F1 | Coverage | High Conf Acc | Duration |
|--------------|----------|-----------|--------|----|---------|--------------|---------|
| Baseline (No B2B Enrichment) | 94.7% | 96.5% | 98.1% | 97.3% | 98.1% | 97.0% | 143.7s |
| Discolike Only | 94.8% | 96.4% | 98.3% | 97.3% | 98.3% | 96.5% | 135.6s |
| Ocean Only | 94.4% | 96.1% | 98.2% | 97.1% | 98.2% | 96.5% | 120.7s |
| Both (Discolike → Ocean) | 94.9% | 96.4% | 98.4% | 97.4% | 98.4% | 96.9% | 122.6s |

## Detailed Results

### Baseline (No B2B Enrichment)

**Overall Performance:**
- Total Companies: 1013
- Accuracy: 94.67%
- Precision: 96.48%
- Recall: 98.06%
- F1 Score: 97.26%
- Coverage: 98.12%

**Confusion Matrix:**
- True Positives: 959
- False Positives: 35
- False Negatives: 19
- True Negatives: 0

**Confidence Calibration:**
- High Confidence (≥85): 97.03% (976 companies)
- Medium Confidence (70-84): 85.71% (7 companies)

**Source Breakdown:**
- google_places: 97.9% accuracy (858/876)
- serper_search: 88.5% accuracy (85/96)
- llm_verified: 66.7% accuracy (16/24)

**Performance:**
- Duration: 143.7 seconds
- Throughput: 7.0 companies/second

---

### Discolike Only

**Overall Performance:**
- Total Companies: 1013
- Accuracy: 94.77%
- Precision: 96.39%
- Recall: 98.26%
- F1 Score: 97.31%
- Coverage: 98.32%

**Confusion Matrix:**
- True Positives: 960
- False Positives: 36
- False Negatives: 17
- True Negatives: 0

**Confidence Calibration:**
- High Confidence (≥85): 96.52% (977 companies)
- Medium Confidence (70-84): 90.00% (10 companies)

**Source Breakdown:**
- google_places: 98.0% accuracy (854/871)
- serper_search: 84.5% accuracy (87/103)
- llm_verified: 79.2% accuracy (19/24)

**Performance:**
- Duration: 135.6 seconds
- Throughput: 7.5 companies/second

---

### Ocean Only

**Overall Performance:**
- Total Companies: 1013
- Accuracy: 94.37%
- Precision: 96.08%
- Recall: 98.15%
- F1 Score: 97.11%
- Coverage: 98.22%

**Confusion Matrix:**
- True Positives: 956
- False Positives: 39
- False Negatives: 18
- True Negatives: 0

**Confidence Calibration:**
- High Confidence (≥85): 96.53% (980 companies)
- Medium Confidence (70-84): 71.43% (7 companies)

**Source Breakdown:**
- google_places: 98.0% accuracy (865/883)
- llm_verified: 84.4% accuracy (27/32)
- serper_search: 78.0% accuracy (64/82)

**Performance:**
- Duration: 120.7 seconds
- Throughput: 8.4 companies/second

---

### Both (Discolike → Ocean)

**Overall Performance:**
- Total Companies: 1013
- Accuracy: 94.87%
- Precision: 96.39%
- Recall: 98.36%
- F1 Score: 97.37%
- Coverage: 98.42%

**Confusion Matrix:**
- True Positives: 961
- False Positives: 36
- False Negatives: 16
- True Negatives: 0

**Confidence Calibration:**
- High Confidence (≥85): 96.92% (975 companies)
- Medium Confidence (70-84): 88.89% (9 companies)

**Source Breakdown:**
- google_places: 97.6% accuracy (862/883)
- serper_search: 90.8% accuracy (79/87)
- llm_verified: 74.1% accuracy (20/27)
- scraping: 0.0% accuracy (0/1)

**Performance:**
- Duration: 122.6 seconds
- Throughput: 8.2 companies/second

---

## Recommendations

- **Best Accuracy:** Both (Discolike → Ocean) (94.9%)
- **Fastest:** Ocean Only (120.7s)

