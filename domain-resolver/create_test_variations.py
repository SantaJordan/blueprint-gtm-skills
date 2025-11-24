#!/usr/bin/env python3
"""
Create test variations with different levels of data completeness
"""
import pandas as pd
from pathlib import Path

# Load the full test dataset
df = pd.read_csv('test/test_companies_fresh.csv')

print(f"Loaded {len(df)} companies")
print(f"Columns: {list(df.columns)}")

# Create output directory
Path("test/variations").mkdir(parents=True, exist_ok=True)

# Variation 1: Full data (baseline) - name, city, phone, context
variation1 = df.copy()
variation1.to_csv('test/variations/1_full_data.csv', index=False)
print(f"\n1. Full data: {len(variation1)} companies")
print(f"   Fields: name, city, phone, context")

# Variation 2: No phone - name, city, context
variation2 = df.copy()
variation2['phone'] = ''  # Remove phone
variation2.to_csv('test/variations/2_no_phone.csv', index=False)
print(f"\n2. No phone: {len(variation2)} companies")
print(f"   Fields: name, city, context")

# Variation 3: No city - name, phone, context
variation3 = df.copy()
variation3['city'] = ''  # Remove city
variation3.to_csv('test/variations/3_no_city.csv', index=False)
print(f"\n3. No city: {len(variation3)} companies")
print(f"   Fields: name, phone, context")

# Variation 4: Minimal - name, context only (no phone, no city)
variation4 = df.copy()
variation4['phone'] = ''
variation4['city'] = ''
variation4.to_csv('test/variations/4_minimal.csv', index=False)
print(f"\n4. Minimal: {len(variation4)} companies")
print(f"   Fields: name, context")

# Variation 5: Name only - just name (no phone, no city, no context)
variation5 = df.copy()
variation5['phone'] = ''
variation5['city'] = ''
variation5['context'] = ''
variation5.to_csv('test/variations/5_name_only.csv', index=False)
print(f"\n5. Name only: {len(variation5)} companies")
print(f"   Fields: name")

print(f"\n✓ Created 5 test variations in test/variations/")
print(f"\nNext: Run resolver on each variation and compare results")
