#!/usr/bin/env python3
"""
Analyze data quality and garbage detection in SMB contact discovery results.
Focus on:
1. Company names used as contact names
2. Generic vs specific person names
3. Email domain matching
4. Missing essential info
5. Validation patterns indicating garbage data
"""

import json
import re
from collections import Counter, defaultdict
from typing import Dict, List, Any
import sys

def is_company_name_pattern(name: str) -> bool:
    """Detect if a name looks like a company name, not a person name."""
    if not name:
        return False

    name_lower = name.lower()

    # Company indicators
    company_indicators = [
        'inc', 'llc', 'ltd', 'corp', 'corporation', 'company', 'co.',
        'services', 'service', 'group', 'brothers', 'bros', 'enterprises',
        'construction', 'plumbing', 'electrical', 'hvac', 'roofing',
        'landscaping', 'painting', 'cleaning', 'repair', 'solutions',
        'systems', 'design', 'contractors', 'consulting', 'associates'
    ]

    for indicator in company_indicators:
        if indicator in name_lower:
            return True

    # Check if name contains '&' (e.g., "Smith & Associates")
    if '&' in name:
        return True

    return False

def is_generic_person_name(name: str) -> bool:
    """Detect generic/placeholder names."""
    if not name:
        return False

    name_lower = name.lower()
    generic_patterns = [
        'owner', 'manager', 'director', 'president', 'ceo',
        'admin', 'contact', 'info', 'general', 'support'
    ]

    return any(pattern in name_lower for pattern in generic_patterns)

def extract_domain(email: str) -> str:
    """Extract domain from email address."""
    if not email or '@' not in email:
        return None
    return email.split('@')[1].lower()

def analyze_contact_name(contact: Dict, company_name: str) -> Dict[str, Any]:
    """Analyze a single contact's name quality."""
    name = contact.get('name')

    analysis = {
        'has_name': bool(name),
        'is_company_name': False,
        'is_generic': False,
        'is_likely_person': False,
        'name_equals_company': False
    }

    if not name:
        return analysis

    # Check if name equals or is very similar to company name
    if name.lower() == company_name.lower():
        analysis['name_equals_company'] = True
        analysis['is_company_name'] = True
    elif is_company_name_pattern(name):
        analysis['is_company_name'] = True
    elif is_generic_person_name(name):
        analysis['is_generic'] = True
    else:
        # Check if it looks like a real person name (2+ words, no company indicators)
        words = name.split()
        if len(words) >= 2:
            analysis['is_likely_person'] = True

    return analysis

def analyze_email_domain(contact: Dict, company_domain: str) -> Dict[str, Any]:
    """Analyze email domain matching."""
    email = contact.get('email')

    analysis = {
        'has_email': bool(email),
        'domain_matched': False,
        'is_generic_domain': False,
        'domain': None
    }

    if not email:
        return analysis

    email_domain = extract_domain(email)
    analysis['domain'] = email_domain

    if not email_domain:
        return analysis

    # Generic email providers
    generic_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
                       'aol.com', 'icloud.com', 'me.com']

    if email_domain in generic_domains:
        analysis['is_generic_domain'] = True

    # Check domain matching
    if company_domain:
        company_domain_clean = company_domain.lower().replace('www.', '')
        if email_domain == company_domain_clean:
            analysis['domain_matched'] = True

    return analysis

def analyze_results(results_path: str):
    """Main analysis function."""
    print(f"Loading results from: {results_path}")

    with open(results_path, 'r') as f:
        data = json.load(f)

    results = data.get('results', [])
    summary = data.get('summary', {})

    print(f"\n{'='*80}")
    print(f"DATASET SUMMARY")
    print(f"{'='*80}")
    print(f"Total companies: {summary.get('total_companies', 0)}")
    print(f"Companies processed: {summary.get('companies_processed', 0)}")
    print(f"Contacts found: {summary.get('contacts_found', 0)}")
    print(f"Contacts validated: {summary.get('contacts_validated', 0)}")

    # Analysis counters
    total_contacts = 0
    validated_contacts = 0

    name_stats = {
        'no_name': 0,
        'company_name_as_contact': 0,
        'name_equals_company': 0,
        'generic_name': 0,
        'likely_person_name': 0
    }

    email_stats = {
        'no_email': 0,
        'has_email': 0,
        'domain_matched': 0,
        'generic_domain': 0
    }

    phone_stats = {
        'no_phone': 0,
        'has_phone': 0
    }

    title_stats = Counter()
    missing_essentials = {
        'no_name_no_email': 0,
        'no_name_no_email_no_phone': 0
    }

    validation_reasons = Counter()
    red_flags = Counter()
    sources = Counter()

    # Examples for reporting
    company_name_examples = []
    generic_name_examples = []
    no_essentials_examples = []

    # Process each result
    for result in results:
        company_name = result.get('company_name', '')
        company_domain = result.get('domain', '')
        contacts = result.get('contacts', [])

        for contact in contacts:
            total_contacts += 1

            if contact.get('is_valid'):
                validated_contacts += 1

            # Name analysis
            name_analysis = analyze_contact_name(contact, company_name)
            if not name_analysis['has_name']:
                name_stats['no_name'] += 1
            if name_analysis['name_equals_company']:
                name_stats['name_equals_company'] += 1
                if len(company_name_examples) < 10:
                    company_name_examples.append({
                        'company': company_name,
                        'contact_name': contact.get('name'),
                        'title': contact.get('title'),
                        'is_valid': contact.get('is_valid')
                    })
            if name_analysis['is_company_name']:
                name_stats['company_name_as_contact'] += 1
            if name_analysis['is_generic']:
                name_stats['generic_name'] += 1
                if len(generic_name_examples) < 10:
                    generic_name_examples.append({
                        'company': company_name,
                        'contact_name': contact.get('name'),
                        'title': contact.get('title'),
                        'is_valid': contact.get('is_valid')
                    })
            if name_analysis['is_likely_person']:
                name_stats['likely_person_name'] += 1

            # Email analysis
            email_analysis = analyze_email_domain(contact, company_domain)
            if email_analysis['has_email']:
                email_stats['has_email'] += 1
                if email_analysis['domain_matched']:
                    email_stats['domain_matched'] += 1
                if email_analysis['is_generic_domain']:
                    email_stats['generic_domain'] += 1
            else:
                email_stats['no_email'] += 1

            # Phone analysis
            if contact.get('phone'):
                phone_stats['has_phone'] += 1
            else:
                phone_stats['no_phone'] += 1

            # Title analysis
            title = contact.get('title') or 'None'
            title_stats[title] += 1

            # Missing essentials
            if not contact.get('name') and not contact.get('email'):
                missing_essentials['no_name_no_email'] += 1
            if not contact.get('name') and not contact.get('email') and not contact.get('phone'):
                missing_essentials['no_name_no_email_no_phone'] += 1
                if len(no_essentials_examples) < 5:
                    no_essentials_examples.append({
                        'company': company_name,
                        'contact': contact
                    })

            # Validation reasons
            for reason in contact.get('validation_reasons', []):
                validation_reasons[reason] += 1
                if 'RED FLAG' in reason:
                    # Extract the flag
                    flag = reason.split('RED FLAG:')[1].strip() if 'RED FLAG:' in reason else reason
                    red_flags[flag] += 1

            # Sources
            for source in contact.get('sources', []):
                sources[source] += 1

    # Print detailed analysis
    print(f"\n{'='*80}")
    print(f"1. NAME QUALITY ANALYSIS")
    print(f"{'='*80}")
    print(f"\nTotal contacts analyzed: {total_contacts}")
    print(f"\nName Statistics:")
    print(f"  No name:                     {name_stats['no_name']:4d} ({name_stats['no_name']/total_contacts*100:5.1f}%)")
    print(f"  Name equals company name:    {name_stats['name_equals_company']:4d} ({name_stats['name_equals_company']/total_contacts*100:5.1f}%)")
    print(f"  Company-like name pattern:   {name_stats['company_name_as_contact']:4d} ({name_stats['company_name_as_contact']/total_contacts*100:5.1f}%)")
    print(f"  Generic/placeholder name:    {name_stats['generic_name']:4d} ({name_stats['generic_name']/total_contacts*100:5.1f}%)")
    print(f"  Likely real person name:     {name_stats['likely_person_name']:4d} ({name_stats['likely_person_name']/total_contacts*100:5.1f}%)")

    print(f"\nExamples of company name used as contact name:")
    for ex in company_name_examples[:5]:
        print(f"  - Company: '{ex['company']}' → Contact: '{ex['contact_name']}' ({ex['title']}) [Valid: {ex['is_valid']}]")

    print(f"\nExamples of generic names:")
    for ex in generic_name_examples[:5]:
        print(f"  - Company: '{ex['company']}' → Contact: '{ex['contact_name']}' ({ex['title']}) [Valid: {ex['is_valid']}]")

    print(f"\n{'='*80}")
    print(f"2. TITLE ANALYSIS")
    print(f"{'='*80}")
    print(f"\nTop 20 titles:")
    for title, count in title_stats.most_common(20):
        print(f"  {title:40s} {count:4d} ({count/total_contacts*100:5.1f}%)")

    print(f"\n{'='*80}")
    print(f"3. EMAIL DOMAIN MATCHING")
    print(f"{'='*80}")
    print(f"\nEmail Statistics:")
    print(f"  Has email:                   {email_stats['has_email']:4d} ({email_stats['has_email']/total_contacts*100:5.1f}%)")
    print(f"  No email:                    {email_stats['no_email']:4d} ({email_stats['no_email']/total_contacts*100:5.1f}%)")
    if email_stats['has_email'] > 0:
        print(f"  Domain matched:              {email_stats['domain_matched']:4d} ({email_stats['domain_matched']/email_stats['has_email']*100:5.1f}% of emails)")
        print(f"  Generic domain (gmail/etc):  {email_stats['generic_domain']:4d} ({email_stats['generic_domain']/email_stats['has_email']*100:5.1f}% of emails)")

    print(f"\n{'='*80}")
    print(f"4. MISSING ESSENTIAL INFO")
    print(f"{'='*80}")
    print(f"\nContacts missing essential information:")
    print(f"  No name AND no email:        {missing_essentials['no_name_no_email']:4d} ({missing_essentials['no_name_no_email']/total_contacts*100:5.1f}%)")
    print(f"  No name, email, or phone:    {missing_essentials['no_name_no_email_no_phone']:4d} ({missing_essentials['no_name_no_email_no_phone']/total_contacts*100:5.1f}%)")

    print(f"\nExamples of contacts with no essentials:")
    for ex in no_essentials_examples:
        print(f"  - Company: '{ex['company']}'")
        print(f"    Contact: {ex['contact']}")

    print(f"\n{'='*80}")
    print(f"5. VALIDATION PATTERNS (RED FLAGS)")
    print(f"{'='*80}")
    print(f"\nTop 20 validation red flags:")
    for flag, count in red_flags.most_common(20):
        print(f"  {flag:60s} {count:4d}")

    print(f"\n{'='*80}")
    print(f"6. DATA SOURCES")
    print(f"{'='*80}")
    print(f"\nContact sources:")
    for source, count in sources.most_common():
        print(f"  {source:40s} {count:4d} ({count/total_contacts*100:5.1f}%)")

    print(f"\n{'='*80}")
    print(f"7. GARBAGE DATA PATTERNS DETECTED")
    print(f"{'='*80}")

    garbage_score = 0
    max_score = 7

    # Pattern 1: High rate of company names as contact names
    company_name_rate = name_stats['company_name_as_contact'] / total_contacts
    if company_name_rate > 0.3:
        print(f"\n⚠️  HIGH: {company_name_rate*100:.1f}% of contacts use company name as contact name")
        garbage_score += 1
    elif company_name_rate > 0.15:
        print(f"\n⚠️  MEDIUM: {company_name_rate*100:.1f}% of contacts use company name as contact name")
        garbage_score += 0.5

    # Pattern 2: High rate of missing names
    no_name_rate = name_stats['no_name'] / total_contacts
    if no_name_rate > 0.3:
        print(f"⚠️  HIGH: {no_name_rate*100:.1f}% of contacts have no name")
        garbage_score += 1
    elif no_name_rate > 0.15:
        print(f"⚠️  MEDIUM: {no_name_rate*100:.1f}% of contacts have no name")
        garbage_score += 0.5

    # Pattern 3: Low rate of person names
    person_name_rate = name_stats['likely_person_name'] / total_contacts
    if person_name_rate < 0.3:
        print(f"⚠️  HIGH: Only {person_name_rate*100:.1f}% of contacts have likely person names")
        garbage_score += 1
    elif person_name_rate < 0.5:
        print(f"⚠️  MEDIUM: Only {person_name_rate*100:.1f}% of contacts have likely person names")
        garbage_score += 0.5

    # Pattern 4: Low email domain matching
    if email_stats['has_email'] > 0:
        domain_match_rate = email_stats['domain_matched'] / email_stats['has_email']
        if domain_match_rate < 0.4:
            print(f"⚠️  HIGH: Only {domain_match_rate*100:.1f}% of emails match company domain")
            garbage_score += 1
        elif domain_match_rate < 0.6:
            print(f"⚠️  MEDIUM: Only {domain_match_rate*100:.1f}% of emails match company domain")
            garbage_score += 0.5

    # Pattern 5: High rate of generic email domains
    if email_stats['has_email'] > 0:
        generic_domain_rate = email_stats['generic_domain'] / email_stats['has_email']
        if generic_domain_rate > 0.4:
            print(f"⚠️  HIGH: {generic_domain_rate*100:.1f}% of emails use generic domains (gmail, yahoo, etc)")
            garbage_score += 1
        elif generic_domain_rate > 0.25:
            print(f"⚠️  MEDIUM: {generic_domain_rate*100:.1f}% of emails use generic domains (gmail, yahoo, etc)")
            garbage_score += 0.5

    # Pattern 6: High rate of missing essential info
    no_essentials_rate = missing_essentials['no_name_no_email'] / total_contacts
    if no_essentials_rate > 0.2:
        print(f"⚠️  HIGH: {no_essentials_rate*100:.1f}% of contacts missing both name and email")
        garbage_score += 1
    elif no_essentials_rate > 0.1:
        print(f"⚠️  MEDIUM: {no_essentials_rate*100:.1f}% of contacts missing both name and email")
        garbage_score += 0.5

    # Pattern 7: Validation rate
    validation_rate = validated_contacts / total_contacts if total_contacts > 0 else 0
    if validation_rate < 0.5:
        print(f"⚠️  HIGH: Only {validation_rate*100:.1f}% of contacts passed validation")
        garbage_score += 1
    elif validation_rate < 0.7:
        print(f"⚠️  MEDIUM: Only {validation_rate*100:.1f}% of contacts passed validation")
        garbage_score += 0.5

    print(f"\n{'='*80}")
    print(f"8. RECOMMENDATIONS")
    print(f"{'='*80}")
    print(f"\nData Quality Score: {(1 - garbage_score/max_score)*100:.1f}/100")
    print(f"Garbage Indicators: {garbage_score:.1f}/{max_score}")

    print("\n📋 Recommended validation improvements:\n")

    if company_name_rate > 0.15:
        print("1. ✅ ADD NAME VALIDATION:")
        print("   - Reject contacts where name exactly matches company_name")
        print("   - Flag contacts with company indicators (Inc, LLC, Services, etc)")
        print("   - Require at least 2 words for person names")

    if person_name_rate < 0.5:
        print("\n2. ✅ IMPROVE PERSON NAME EXTRACTION:")
        print("   - Prioritize sources that provide actual person names")
        print("   - Use NER (Named Entity Recognition) to distinguish persons from companies")
        print("   - Parse 'About Us' or 'Team' pages for owner names")

    if email_stats['has_email'] > 0 and domain_match_rate < 0.6:
        print("\n3. ✅ ENFORCE EMAIL DOMAIN MATCHING:")
        print("   - Reject or downgrade contacts with non-matching email domains")
        print("   - Prioritize emails from company domain over generic domains")
        print("   - Score: +30 for domain match, -20 for generic domain")

    if no_essentials_rate > 0.1:
        print("\n4. ✅ REQUIRE MINIMUM CONTACT INFO:")
        print("   - Reject contacts with no name AND no email")
        print("   - Require at least 2 of: name, email, phone")
        print("   - Add completeness score to validation")

    if validation_rate < 0.7:
        print("\n5. ✅ TIGHTEN VALIDATION THRESHOLD:")
        print(f"   - Current validation rate: {validation_rate*100:.1f}%")
        print("   - Consider raising threshold from 50 to 60-70 points")
        print("   - Add penalties for red flags")

    print("\n6. ✅ SOURCE-SPECIFIC IMPROVEMENTS:")
    print("   - google_maps_owner: Validate name is not company name")
    print("   - openweb_contacts: Require name field, not just email")
    print("   - LinkedIn scraping: Verify person works at/owns company")

    print(f"\n{'='*80}")
    print(f"ANALYSIS COMPLETE")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python analyze_data_quality.py <results_json_path>")
        sys.exit(1)

    analyze_results(sys.argv[1])
