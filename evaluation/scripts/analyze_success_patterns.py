#!/usr/bin/env python3
"""
Analyze success patterns from SMB contact discovery results.
Focus on what makes successful contact discoveries work.
"""

import json
from collections import defaultdict, Counter
from typing import Dict, List, Any
import statistics

def load_results(file_path: str) -> List[Dict[str, Any]]:
    """Load JSON results file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
        # Handle wrapped format with metadata and results
        if isinstance(data, dict) and 'results' in data:
            return data['results']
        return data

def analyze_source_effectiveness(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze which data sources produce the most valid contacts."""
    source_stats = defaultdict(lambda: {
        'total': 0,
        'valid': 0,
        'confidence_scores': []
    })

    for result in results:
        contacts = result.get('contacts', [])
        for contact in contacts:
            # Handle both 'source' and 'sources' fields
            sources = contact.get('sources', [])
            if not sources:
                sources = [contact.get('source', 'unknown')]

            is_valid = contact.get('is_valid', False)
            confidence = contact.get('confidence', 0)

            # Track stats for each source this contact came from
            for source in sources:
                source_stats[source]['total'] += 1
                if is_valid:
                    source_stats[source]['valid'] += 1
                source_stats[source]['confidence_scores'].append(confidence)

    # Calculate averages and success rates
    source_rankings = []
    for source, stats in source_stats.items():
        avg_confidence = statistics.mean(stats['confidence_scores']) if stats['confidence_scores'] else 0
        success_rate = (stats['valid'] / stats['total'] * 100) if stats['total'] > 0 else 0

        source_rankings.append({
            'source': source,
            'total_contacts': stats['total'],
            'valid_contacts': stats['valid'],
            'success_rate': success_rate,
            'avg_confidence': avg_confidence
        })

    # Sort by success rate
    source_rankings.sort(key=lambda x: x['success_rate'], reverse=True)
    return source_rankings

def analyze_vertical_success(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze success rates by business vertical."""
    vertical_stats = defaultdict(lambda: {
        'total': 0,
        'with_valid_contact': 0,
        'total_contacts': 0,
        'valid_contacts': 0,
        'confidence_scores': []
    })

    for result in results:
        vertical = result.get('vertical', 'unknown')
        contacts = result.get('contacts', [])

        vertical_stats[vertical]['total'] += 1

        has_valid = False
        for contact in contacts:
            vertical_stats[vertical]['total_contacts'] += 1
            if contact.get('is_valid', False):
                vertical_stats[vertical]['valid_contacts'] += 1
                has_valid = True
                vertical_stats[vertical]['confidence_scores'].append(
                    contact.get('confidence_score', 0)
                )

        if has_valid:
            vertical_stats[vertical]['with_valid_contact'] += 1

    # Calculate rates
    vertical_rankings = []
    for vertical, stats in vertical_stats.items():
        company_success_rate = (stats['with_valid_contact'] / stats['total'] * 100) if stats['total'] > 0 else 0
        contact_success_rate = (stats['valid_contacts'] / stats['total_contacts'] * 100) if stats['total_contacts'] > 0 else 0
        avg_confidence = statistics.mean(stats['confidence_scores']) if stats['confidence_scores'] else 0

        vertical_rankings.append({
            'vertical': vertical,
            'total_companies': stats['total'],
            'companies_with_valid_contact': stats['with_valid_contact'],
            'company_success_rate': company_success_rate,
            'total_contacts_found': stats['total_contacts'],
            'valid_contacts': stats['valid_contacts'],
            'contact_success_rate': contact_success_rate,
            'avg_confidence': avg_confidence
        })

    # Sort by company success rate
    vertical_rankings.sort(key=lambda x: x['company_success_rate'], reverse=True)
    return vertical_rankings

def analyze_stage_patterns(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze which stage combinations lead to better results."""
    stage_patterns = defaultdict(lambda: {
        'total': 0,
        'with_valid_contact': 0,
        'total_contacts': 0,
        'valid_contacts': 0
    })

    for result in results:
        stages = tuple(sorted(result.get('stages_completed', [])))
        stage_key = ' -> '.join(stages) if stages else 'none'

        contacts = result.get('contacts', [])
        has_valid = any(c.get('is_valid', False) for c in contacts)
        valid_count = sum(1 for c in contacts if c.get('is_valid', False))

        stage_patterns[stage_key]['total'] += 1
        stage_patterns[stage_key]['total_contacts'] += len(contacts)
        stage_patterns[stage_key]['valid_contacts'] += valid_count
        if has_valid:
            stage_patterns[stage_key]['with_valid_contact'] += 1

    # Calculate rates
    stage_rankings = []
    for stages, stats in stage_patterns.items():
        success_rate = (stats['with_valid_contact'] / stats['total'] * 100) if stats['total'] > 0 else 0
        contact_rate = (stats['valid_contacts'] / stats['total_contacts'] * 100) if stats['total_contacts'] > 0 else 0

        stage_rankings.append({
            'stages': stages,
            'total_runs': stats['total'],
            'successful_runs': stats['with_valid_contact'],
            'success_rate': success_rate,
            'total_contacts': stats['total_contacts'],
            'valid_contacts': stats['valid_contacts'],
            'contact_success_rate': contact_rate
        })

    # Sort by success rate
    stage_rankings.sort(key=lambda x: x['success_rate'], reverse=True)
    return stage_rankings

def analyze_domain_patterns(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze success patterns by domain characteristics."""
    domain_stats = {
        'has_domain': {'total': 0, 'valid_contact': 0},
        'no_domain': {'total': 0, 'valid_contact': 0},
        'by_tld': defaultdict(lambda: {'total': 0, 'valid_contact': 0})
    }

    for result in results:
        domain = result.get('domain', '')
        has_valid = any(c.get('is_valid', False) for c in result.get('contacts', []))

        if domain:
            domain_stats['has_domain']['total'] += 1
            if has_valid:
                domain_stats['has_domain']['valid_contact'] += 1

            # Extract TLD
            if '.' in domain:
                tld = domain.split('.')[-1]
                domain_stats['by_tld'][tld]['total'] += 1
                if has_valid:
                    domain_stats['by_tld'][tld]['valid_contact'] += 1
        else:
            domain_stats['no_domain']['total'] += 1
            if has_valid:
                domain_stats['no_domain']['valid_contact'] += 1

    # Calculate rates
    has_domain_rate = (domain_stats['has_domain']['valid_contact'] / domain_stats['has_domain']['total'] * 100) if domain_stats['has_domain']['total'] > 0 else 0
    no_domain_rate = (domain_stats['no_domain']['valid_contact'] / domain_stats['no_domain']['total'] * 100) if domain_stats['no_domain']['total'] > 0 else 0

    tld_rankings = []
    for tld, stats in domain_stats['by_tld'].items():
        if stats['total'] >= 5:  # Only TLDs with 5+ companies
            success_rate = (stats['valid_contact'] / stats['total'] * 100) if stats['total'] > 0 else 0
            tld_rankings.append({
                'tld': tld,
                'total': stats['total'],
                'with_valid_contact': stats['valid_contact'],
                'success_rate': success_rate
            })

    tld_rankings.sort(key=lambda x: x['success_rate'], reverse=True)

    return {
        'has_domain_rate': has_domain_rate,
        'no_domain_rate': no_domain_rate,
        'has_domain_total': domain_stats['has_domain']['total'],
        'no_domain_total': domain_stats['no_domain']['total'],
        'top_tlds': tld_rankings[:10]
    }

def analyze_contact_characteristics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze characteristics of valid vs invalid contacts."""
    characteristics = {
        'valid': {
            'has_phone': 0,
            'has_email': 0,
            'has_owner_name': 0,
            'has_title': 0,
            'total': 0
        },
        'invalid': {
            'has_phone': 0,
            'has_email': 0,
            'has_owner_name': 0,
            'has_title': 0,
            'total': 0
        }
    }

    for result in results:
        for contact in result.get('contacts', []):
            category = 'valid' if contact.get('is_valid', False) else 'invalid'
            characteristics[category]['total'] += 1

            if contact.get('phone'):
                characteristics[category]['has_phone'] += 1
            if contact.get('email'):
                characteristics[category]['has_email'] += 1
            if contact.get('owner_name'):
                characteristics[category]['has_owner_name'] += 1
            if contact.get('title'):
                characteristics[category]['has_title'] += 1

    # Calculate percentages
    for category in ['valid', 'invalid']:
        total = characteristics[category]['total']
        if total > 0:
            characteristics[category]['phone_pct'] = (characteristics[category]['has_phone'] / total * 100)
            characteristics[category]['email_pct'] = (characteristics[category]['has_email'] / total * 100)
            characteristics[category]['owner_name_pct'] = (characteristics[category]['has_owner_name'] / total * 100)
            characteristics[category]['title_pct'] = (characteristics[category]['has_title'] / total * 100)

    return characteristics

def analyze_source_combinations(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze which source combinations lead to best results."""
    combo_stats = defaultdict(lambda: {
        'total': 0,
        'valid': 0,
        'confidence_scores': []
    })

    for result in results:
        for contact in result.get('contacts', []):
            sources = tuple(sorted(contact.get('sources', [])))
            if not sources:
                continue

            is_valid = contact.get('is_valid', False)
            confidence = contact.get('confidence', 0)

            combo_key = ' + '.join(sources)
            combo_stats[combo_key]['total'] += 1
            if is_valid:
                combo_stats[combo_key]['valid'] += 1
            combo_stats[combo_key]['confidence_scores'].append(confidence)

    # Calculate rates
    combo_rankings = []
    for combo, stats in combo_stats.items():
        if stats['total'] >= 3:  # Only combos with 3+ instances
            success_rate = (stats['valid'] / stats['total'] * 100) if stats['total'] > 0 else 0
            avg_confidence = statistics.mean(stats['confidence_scores']) if stats['confidence_scores'] else 0

            combo_rankings.append({
                'combination': combo,
                'total': stats['total'],
                'valid': stats['valid'],
                'success_rate': success_rate,
                'avg_confidence': avg_confidence
            })

    combo_rankings.sort(key=lambda x: x['success_rate'], reverse=True)
    return combo_rankings[:15]  # Top 15

def generate_report(results: List[Dict[str, Any]]):
    """Generate comprehensive analysis report."""
    print("=" * 80)
    print("SMB CONTACT DISCOVERY - SUCCESS PATTERN ANALYSIS")
    print("=" * 80)
    print(f"\nTotal Companies Analyzed: {len(results)}")

    # Overall success metrics
    companies_with_valid = sum(1 for r in results if any(c.get('is_valid', False) for c in r.get('contacts', [])))
    total_contacts = sum(len(r.get('contacts', [])) for r in results)
    valid_contacts = sum(sum(1 for c in r.get('contacts', []) if c.get('is_valid', False)) for r in results)

    print(f"Companies with Valid Contact: {companies_with_valid} ({companies_with_valid/len(results)*100:.1f}%)")
    print(f"Total Contacts Found: {total_contacts}")
    print(f"Valid Contacts: {valid_contacts} ({valid_contacts/total_contacts*100:.1f}%)")
    print(f"Avg Contacts per Company: {total_contacts/len(results):.2f}")
    print(f"Avg Valid Contacts per Successful Company: {valid_contacts/companies_with_valid:.2f}")

    # Source effectiveness
    print("\n" + "=" * 80)
    print("1. DATA SOURCE EFFECTIVENESS")
    print("=" * 80)
    source_rankings = analyze_source_effectiveness(results)
    print(f"\n{'Source':<30} {'Total':<8} {'Valid':<8} {'Success%':<10} {'Avg Conf':<10}")
    print("-" * 80)
    for source in source_rankings:
        print(f"{source['source']:<30} {source['total_contacts']:<8} {source['valid_contacts']:<8} "
              f"{source['success_rate']:<10.1f} {source['avg_confidence']:<10.1f}")

    # Source combinations
    print("\n" + "=" * 80)
    print("1B. SOURCE COMBINATION PATTERNS")
    print("=" * 80)
    combo_rankings = analyze_source_combinations(results)
    print(f"\n{'Source Combination':<60} {'Total':<8} {'Valid':<8} {'Success%':<10}")
    print("-" * 100)
    for combo in combo_rankings:
        print(f"{combo['combination']:<60} {combo['total']:<8} {combo['valid']:<8} "
              f"{combo['success_rate']:<10.1f}")

    # Vertical success
    print("\n" + "=" * 80)
    print("2. BUSINESS VERTICAL SUCCESS RATES")
    print("=" * 80)
    vertical_rankings = analyze_vertical_success(results)
    print(f"\n{'Vertical':<25} {'Companies':<12} {'Success%':<12} {'Contacts':<12} {'Valid%':<12} {'Avg Conf':<10}")
    print("-" * 80)
    for vertical in vertical_rankings[:15]:  # Top 15
        print(f"{vertical['vertical']:<25} {vertical['total_companies']:<12} "
              f"{vertical['company_success_rate']:<12.1f} {vertical['total_contacts_found']:<12} "
              f"{vertical['contact_success_rate']:<12.1f} {vertical['avg_confidence']:<10.1f}")

    # Stage patterns
    print("\n" + "=" * 80)
    print("3. PIPELINE STAGE PATTERNS")
    print("=" * 80)
    stage_rankings = analyze_stage_patterns(results)
    print(f"\n{'Stages Completed':<60} {'Runs':<8} {'Success%':<10}")
    print("-" * 80)
    for stage in stage_rankings[:10]:  # Top 10
        print(f"{stage['stages']:<60} {stage['total_runs']:<8} {stage['success_rate']:<10.1f}")

    # Domain patterns
    print("\n" + "=" * 80)
    print("4. DOMAIN CHARACTERISTICS")
    print("=" * 80)
    domain_analysis = analyze_domain_patterns(results)
    print(f"\nHas Domain: {domain_analysis['has_domain_total']} companies, {domain_analysis['has_domain_rate']:.1f}% success")
    print(f"No Domain: {domain_analysis['no_domain_total']} companies, {domain_analysis['no_domain_rate']:.1f}% success")
    print(f"\nTop TLDs by Success Rate:")
    print(f"{'TLD':<15} {'Total':<10} {'Success%':<10}")
    print("-" * 40)
    for tld in domain_analysis['top_tlds'][:10]:
        print(f"{tld['tld']:<15} {tld['total']:<10} {tld['success_rate']:<10.1f}")

    # Contact characteristics
    print("\n" + "=" * 80)
    print("5. CONTACT CHARACTERISTICS (Valid vs Invalid)")
    print("=" * 80)
    char_analysis = analyze_contact_characteristics(results)
    print(f"\nValid Contacts (n={char_analysis['valid']['total']}):")
    print(f"  - Has Phone: {char_analysis['valid'].get('phone_pct', 0):.1f}%")
    print(f"  - Has Email: {char_analysis['valid'].get('email_pct', 0):.1f}%")
    print(f"  - Has Owner Name: {char_analysis['valid'].get('owner_name_pct', 0):.1f}%")
    print(f"  - Has Title: {char_analysis['valid'].get('title_pct', 0):.1f}%")

    print(f"\nInvalid Contacts (n={char_analysis['invalid']['total']}):")
    print(f"  - Has Phone: {char_analysis['invalid'].get('phone_pct', 0):.1f}%")
    print(f"  - Has Email: {char_analysis['invalid'].get('email_pct', 0):.1f}%")
    print(f"  - Has Owner Name: {char_analysis['invalid'].get('owner_name_pct', 0):.1f}%")
    print(f"  - Has Title: {char_analysis['invalid'].get('title_pct', 0):.1f}%")

    # Key findings and recommendations
    print("\n" + "=" * 80)
    print("6. KEY FINDINGS & RECOMMENDATIONS")
    print("=" * 80)

    print("\nKEY FINDINGS:")
    print("-" * 40)

    # Best source
    best_source = source_rankings[0]
    print(f"✓ Best performing source: {best_source['source']} ({best_source['success_rate']:.1f}% success)")

    # Best vertical
    best_vertical = vertical_rankings[0]
    print(f"✓ Best performing vertical: {best_vertical['vertical']} ({best_vertical['company_success_rate']:.1f}% success)")

    # Best stages
    best_stages = stage_rankings[0]
    print(f"✓ Most successful pipeline: {best_stages['stages']} ({best_stages['success_rate']:.1f}% success)")

    # Domain impact
    if domain_analysis['has_domain_rate'] > domain_analysis['no_domain_rate']:
        print(f"✓ Companies with domains have {domain_analysis['has_domain_rate'] - domain_analysis['no_domain_rate']:.1f}% higher success rate")
    else:
        print(f"✓ Companies without domains perform surprisingly well ({domain_analysis['no_domain_rate']:.1f}% success)")

    print("\nRECOMMENDATIONS:")
    print("-" * 40)

    # Source recommendations
    top_3_sources = source_rankings[:3]
    print("1. Prioritize these data sources:")
    for i, source in enumerate(top_3_sources, 1):
        print(f"   {i}. {source['source']} ({source['success_rate']:.1f}% success, {source['avg_confidence']:.1f} avg confidence)")

    # Vertical recommendations
    top_verticals = [v for v in vertical_rankings if v['total_companies'] >= 10][:5]
    if top_verticals:
        print("\n2. Focus on these high-success verticals:")
        for i, vertical in enumerate(top_verticals, 1):
            print(f"   {i}. {vertical['vertical']} ({vertical['company_success_rate']:.1f}% success, n={vertical['total_companies']})")

    # Stage recommendations
    print("\n3. Pipeline optimization:")
    best_complete_stages = [s for s in stage_rankings if len(s['stages'].split(' -> ')) >= 3][:3]
    if best_complete_stages:
        print("   Recommended stage sequences:")
        for stage in best_complete_stages:
            print(f"   - {stage['stages']} ({stage['success_rate']:.1f}% success)")

    # Data quality recommendations
    print("\n4. Data quality indicators:")
    phone_diff = char_analysis['valid'].get('phone_pct', 0) - char_analysis['invalid'].get('phone_pct', 0)
    email_diff = char_analysis['valid'].get('email_pct', 0) - char_analysis['invalid'].get('email_pct', 0)
    owner_diff = char_analysis['valid'].get('owner_name_pct', 0) - char_analysis['invalid'].get('owner_name_pct', 0)
    title_diff = char_analysis['valid'].get('title_pct', 0) - char_analysis['invalid'].get('title_pct', 0)

    if phone_diff > 5:
        print(f"   - Phone presence correlates with validity (+{phone_diff:.1f}%)")
    if abs(email_diff) > 5:
        if email_diff > 0:
            print(f"   - Email presence correlates with validity (+{email_diff:.1f}%)")
        else:
            print(f"   - WARNING: Valid contacts have FEWER emails than invalid ({email_diff:.1f}%)")
            print(f"     This suggests generic emails are being marked invalid (correct behavior)")
    if owner_diff > 5:
        print(f"   - Owner name presence correlates with validity (+{owner_diff:.1f}%)")
    if title_diff > 5:
        print(f"   - Title presence strongly correlates with validity (+{title_diff:.1f}%)")

    print("\n" + "=" * 80)

def main():
    """Main execution."""
    results_file = "/Users/jordancrawford/Desktop/Blueprint-GTM-Skills/evaluation/results/yelp_940_results.json"

    print(f"Loading results from: {results_file}")
    results = load_results(results_file)

    generate_report(results)

if __name__ == "__main__":
    main()
