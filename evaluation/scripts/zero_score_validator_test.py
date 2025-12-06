#!/usr/bin/env python3
"""
Test validator logic on actual zero-score contacts from results.
"""
import json
from pathlib import Path
import sys

# Add contact-finder to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "contact-finder"))

from modules.validation.simple_validator import SimpleContactValidator, dict_to_candidate


def load_results(file_path: str):
    """Load results from JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
        if isinstance(data, dict) and 'results' in data:
            return data['results']
        return data


def test_zero_score_contacts():
    """Test validator on contacts that got zero score."""

    results_file = "/Users/jordancrawford/Desktop/Blueprint-GTM-Skills/evaluation/results/yelp_940_results.json"
    results = load_results(results_file)

    validator = SimpleContactValidator(min_confidence=50)

    print("=" * 80)
    print("TESTING VALIDATOR ON ZERO-SCORE CONTACTS")
    print("=" * 80)
    print()

    # Find contacts with zero score
    zero_score_samples = []
    for result in results:
        company_name = result.get('company_name', 'Unknown')
        domain = result.get('domain', '')
        contacts = result.get('contacts', [])

        for contact in contacts:
            if contact.get('validation_score', 0) == 0:
                zero_score_samples.append({
                    'company': company_name,
                    'domain': domain,
                    'contact': contact
                })

                if len(zero_score_samples) >= 20:  # Sample size
                    break

        if len(zero_score_samples) >= 20:
            break

    print(f"Testing {len(zero_score_samples)} zero-score contacts...\n")

    for i, sample in enumerate(zero_score_samples, 1):
        company = sample['company']
        domain = sample['domain']
        contact_data = sample['contact']

        print(f"\n{i}. {company} ({domain})")
        print(f"   Contact stored: {contact_data}")
        print()

        # Re-validate using validator
        candidate = dict_to_candidate(contact_data, company_domain=domain)
        result = validator.validate(candidate)

        print(f"   REVALIDATION RESULT:")
        print(f"   - Valid: {result.is_valid}")
        print(f"   - Score: {result.confidence}")
        print(f"   - Breakdown: {result.score_breakdown}")
        print(f"   - Reasons: {result.reasons}")
        print(f"   - Stored score was: {contact_data.get('validation_score', 'N/A')}")

        # Compare
        if result.confidence != contact_data.get('validation_score', 0):
            print(f"   ⚠️  MISMATCH: Stored={contact_data.get('validation_score')}, Calculated={result.confidence}")

        print("-" * 80)


if __name__ == "__main__":
    test_zero_score_contacts()
