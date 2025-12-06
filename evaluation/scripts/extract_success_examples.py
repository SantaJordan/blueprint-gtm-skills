#!/usr/bin/env python3
"""
Extract specific examples of successful and unsuccessful contact discoveries
to illustrate patterns found in the analysis.
"""

import json
from typing import Dict, List, Any

def load_results(file_path: str) -> List[Dict[str, Any]]:
    """Load JSON results file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
        if isinstance(data, dict) and 'results' in data:
            return data['results']
        return data

def find_best_examples(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Find exemplary success and failure cases."""
    examples = {
        'perfect_cases': [],
        'google_maps_wins': [],
        'social_links_wins': [],
        'multi_source_wins': [],
        'openweb_failures': [],
        'vertical_winners': {}
    }

    for result in results:
        contacts = result.get('contacts', [])
        company = result.get('company_name', 'Unknown')
        domain = result.get('domain', '')
        vertical = result.get('vertical', 'unknown')

        # Perfect cases (multiple valid contacts, high confidence)
        valid_contacts = [c for c in contacts if c.get('is_valid', False)]
        if len(valid_contacts) >= 2:
            avg_confidence = sum(c.get('confidence', 0) for c in valid_contacts) / len(valid_contacts)
            if avg_confidence >= 85:
                examples['perfect_cases'].append({
                    'company': company,
                    'domain': domain,
                    'vertical': vertical,
                    'valid_contacts': len(valid_contacts),
                    'avg_confidence': avg_confidence,
                    'contacts': valid_contacts[:2]  # Top 2
                })

        # Google Maps owner wins
        for contact in contacts:
            sources = contact.get('sources', [])
            if 'google_maps_owner' in sources and contact.get('is_valid', False):
                if contact.get('confidence', 0) >= 90:
                    examples['google_maps_wins'].append({
                        'company': company,
                        'domain': domain,
                        'vertical': vertical,
                        'contact': contact
                    })
                    break

        # Social links wins
        for contact in contacts:
            sources = contact.get('sources', [])
            if 'social_links' in sources and contact.get('is_valid', False):
                examples['social_links_wins'].append({
                    'company': company,
                    'domain': domain,
                    'vertical': vertical,
                    'contact': contact
                })
                break

        # Multi-source wins
        for contact in contacts:
            sources = contact.get('sources', [])
            if len(sources) >= 2 and contact.get('is_valid', False):
                examples['multi_source_wins'].append({
                    'company': company,
                    'domain': domain,
                    'vertical': vertical,
                    'contact': contact
                })
                break

        # OpenWeb failures (generic emails)
        for contact in contacts:
            sources = contact.get('sources', [])
            if 'openweb_contacts' in sources and not contact.get('is_valid', False):
                email = contact.get('email', '')
                if email and any(x in email.lower() for x in ['info@', 'contact@', 'sales@', 'hello@']):
                    examples['openweb_failures'].append({
                        'company': company,
                        'domain': domain,
                        'contact': contact
                    })
                    break

        # Track best example per vertical
        if vertical not in examples['vertical_winners'] and valid_contacts:
            best_contact = max(valid_contacts, key=lambda c: c.get('confidence', 0))
            if best_contact.get('confidence', 0) >= 80:
                examples['vertical_winners'][vertical] = {
                    'company': company,
                    'domain': domain,
                    'contact': best_contact
                }

    # Limit examples
    examples['perfect_cases'] = sorted(examples['perfect_cases'],
                                       key=lambda x: x['avg_confidence'],
                                       reverse=True)[:5]
    examples['google_maps_wins'] = examples['google_maps_wins'][:10]
    examples['social_links_wins'] = examples['social_links_wins'][:5]
    examples['multi_source_wins'] = examples['multi_source_wins'][:5]
    examples['openweb_failures'] = examples['openweb_failures'][:10]

    return examples

def print_examples(examples: Dict[str, Any]):
    """Print examples in readable format."""
    print("=" * 80)
    print("SUCCESS PATTERN EXAMPLES - Real Cases from Dataset")
    print("=" * 80)

    # Perfect cases
    print("\n1. PERFECT CASES (Multiple valid contacts, high confidence)")
    print("=" * 80)
    for i, case in enumerate(examples['perfect_cases'], 1):
        print(f"\n{i}. {case['company']} ({case['vertical']})")
        print(f"   Domain: {case['domain']}")
        print(f"   Valid Contacts: {case['valid_contacts']}")
        print(f"   Avg Confidence: {case['avg_confidence']:.1f}")
        for j, contact in enumerate(case['contacts'], 1):
            print(f"\n   Contact {j}:")
            print(f"      Name: {contact.get('name', 'N/A')}")
            print(f"      Title: {contact.get('title', 'N/A')}")
            print(f"      Phone: {contact.get('phone', 'N/A')}")
            print(f"      Email: {contact.get('email', 'N/A')}")
            print(f"      Sources: {', '.join(contact.get('sources', []))}")
            print(f"      Confidence: {contact.get('confidence', 0)}")

    # Google Maps wins
    print("\n\n2. GOOGLE MAPS OWNER WINS (High confidence single-source)")
    print("=" * 80)
    for i, case in enumerate(examples['google_maps_wins'][:5], 1):
        contact = case['contact']
        print(f"\n{i}. {case['company']} ({case['vertical']})")
        print(f"   Name: {contact.get('name', 'N/A')}")
        print(f"   Title: {contact.get('title', 'N/A')}")
        print(f"   Phone: {contact.get('phone', 'N/A')}")
        print(f"   Confidence: {contact.get('confidence', 0)}")
        print(f"   Why Valid: {contact.get('validation_reasons', ['N/A'])[0][:100]}...")

    # Social links wins
    print("\n\n3. SOCIAL LINKS WINS (LinkedIn verification)")
    print("=" * 80)
    for i, case in enumerate(examples['social_links_wins'][:5], 1):
        contact = case['contact']
        print(f"\n{i}. {case['company']} ({case['vertical']})")
        print(f"   Name: {contact.get('name', 'N/A')}")
        print(f"   Title: {contact.get('title', 'N/A')}")
        print(f"   LinkedIn: {contact.get('linkedin_url', 'N/A')}")
        print(f"   Confidence: {contact.get('confidence', 0)}")

    # Multi-source wins
    print("\n\n4. MULTI-SOURCE WINS (Corroborated data)")
    print("=" * 80)
    for i, case in enumerate(examples['multi_source_wins'][:5], 1):
        contact = case['contact']
        print(f"\n{i}. {case['company']} ({case['vertical']})")
        print(f"   Name: {contact.get('name', 'N/A')}")
        print(f"   Title: {contact.get('title', 'N/A')}")
        print(f"   Sources: {', '.join(contact.get('sources', []))}")
        print(f"   Confidence: {contact.get('confidence', 0)}")

    # OpenWeb failures
    print("\n\n5. OPENWEB_CONTACTS FAILURES (Generic emails marked invalid)")
    print("=" * 80)
    print("These show correct validation - generic emails without names are rejected:")
    for i, case in enumerate(examples['openweb_failures'][:5], 1):
        contact = case['contact']
        print(f"\n{i}. {case['company']} ({case['domain']})")
        print(f"   Email: {contact.get('email', 'N/A')}")
        print(f"   Name: {contact.get('name', 'N/A')}")
        print(f"   Title: {contact.get('title', 'N/A')}")
        print(f"   Confidence: {contact.get('confidence', 0)}")
        reasons = contact.get('validation_reasons', [])
        red_flags = [r for r in reasons if 'RED FLAG' in r]
        if red_flags:
            print(f"   Red Flags:")
            for flag in red_flags[:3]:
                print(f"      - {flag.replace('RED FLAG: ', '')}")

    # Vertical winners
    print("\n\n6. TOP CONTACT BY VERTICAL")
    print("=" * 80)
    top_verticals = ['tree_services', 'junk_removal', 'general_contractors',
                     'landscaping', 'roofing', 'plumbing']
    for vertical in top_verticals:
        if vertical in examples['vertical_winners']:
            case = examples['vertical_winners'][vertical]
            contact = case['contact']
            print(f"\n{vertical.replace('_', ' ').title()}:")
            print(f"   Company: {case['company']}")
            print(f"   Name: {contact.get('name', 'N/A')}")
            print(f"   Title: {contact.get('title', 'N/A')}")
            print(f"   Phone: {contact.get('phone', 'N/A')}")
            print(f"   Sources: {', '.join(contact.get('sources', []))}")
            print(f"   Confidence: {contact.get('confidence', 0)}")

    print("\n" + "=" * 80)

def main():
    """Main execution."""
    results_file = "/Users/jordancrawford/Desktop/Blueprint-GTM-Skills/evaluation/results/yelp_940_results.json"

    print(f"Loading results from: {results_file}")
    results = load_results(results_file)

    print(f"Extracting best examples from {len(results)} companies...")
    examples = find_best_examples(results)

    print_examples(examples)

if __name__ == "__main__":
    main()
