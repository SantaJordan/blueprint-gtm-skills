#!/usr/bin/env python3
"""
Check validation accuracy - are validated contacts actually good quality?
This reveals if the validation scoring is working correctly.
"""

import json
import sys

def is_company_name(name: str, company_name: str) -> bool:
    """Check if contact name is actually a company name."""
    if not name:
        return False
    return name.lower() == company_name.lower() or any(
        word in name.lower() for word in
        ['inc', 'llc', 'ltd', 'corp', 'bros', 'services', 'construction',
         'plumbing', 'roofing', 'electrical', 'hvac', 'landscaping']
    )

def is_person_name(name: str) -> bool:
    """Check if name looks like a real person."""
    if not name:
        return False
    words = name.split()
    return len(words) >= 2

def email_matches_domain(email: str, domain: str) -> bool:
    """Check if email domain matches company domain."""
    if not email or '@' not in email:
        return False
    email_domain = email.split('@')[1].lower()
    company_domain = domain.lower().replace('www.', '') if domain else ''
    return email_domain == company_domain

def is_generic_email(email: str) -> bool:
    """Check if email is a generic provider."""
    if not email or '@' not in email:
        return False
    domain = email.split('@')[1].lower()
    return domain in ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com']

def actual_quality_score(contact: dict, company_name: str, company_domain: str) -> int:
    """
    Calculate ACTUAL quality score based on real data quality checks.
    This is what the score SHOULD be.
    """
    score = 0
    issues = []

    name = contact.get('name')
    email = contact.get('email')
    phone = contact.get('phone')
    title = contact.get('title')

    # Name checks
    if not name:
        issues.append("No name (-40)")
        score -= 40
    elif is_company_name(name, company_name):
        issues.append("Company name as contact (-30)")
        score -= 30
    elif is_person_name(name):
        issues.append("Valid person name (+40)")
        score += 40
    else:
        issues.append("Questionable name (+10)")
        score += 10

    # Email checks
    if not email:
        issues.append("No email (-30)")
        score -= 30
    elif email_matches_domain(email, company_domain):
        issues.append("Domain-matched email (+40)")
        score += 40
    elif is_generic_email(email):
        issues.append("Generic email (+10)")
        score += 10
    else:
        issues.append("Other business email (+25)")
        score += 25

    # Phone check
    if phone:
        issues.append("Has phone (+15)")
        score += 15
    else:
        issues.append("No phone (-10)")
        score -= 10

    # Title check
    if not title:
        issues.append("No title (-10)")
        score -= 10
    elif title.lower() in ['owner', 'ceo', 'founder', 'president']:
        issues.append("Strong title (+20)")
        score += 20
    else:
        issues.append("Other title (+10)")
        score += 10

    return score, issues

def analyze_validation_accuracy(results_path: str):
    """Check if validation is accurately identifying quality contacts."""
    print(f"Loading: {results_path}\n")

    with open(results_path, 'r') as f:
        data = json.load(f)

    results = data.get('results', [])

    # Track validation accuracy
    validated_contacts = []
    rejected_contacts = []

    false_positives = []  # Validated but actually bad
    false_negatives = []  # Rejected but actually good
    true_positives = []   # Validated and actually good
    true_negatives = []   # Rejected and actually bad

    for result in results:
        company_name = result.get('company_name', '')
        company_domain = result.get('domain', '')

        for contact in result.get('contacts', []):
            is_valid = contact.get('is_valid', False)
            confidence = contact.get('confidence', 0)

            # Calculate actual quality
            actual_score, issues = actual_quality_score(contact, company_name, company_domain)

            contact_analysis = {
                'company': company_name,
                'name': contact.get('name'),
                'email': contact.get('email'),
                'phone': contact.get('phone'),
                'title': contact.get('title'),
                'validated': is_valid,
                'confidence': confidence,
                'actual_score': actual_score,
                'issues': issues,
                'sources': contact.get('sources', [])
            }

            # Determine if actually good (actual_score >= 60)
            actually_good = actual_score >= 60

            if is_valid:
                validated_contacts.append(contact_analysis)
                if actually_good:
                    true_positives.append(contact_analysis)
                else:
                    false_positives.append(contact_analysis)
            else:
                rejected_contacts.append(contact_analysis)
                if actually_good:
                    false_negatives.append(contact_analysis)
                else:
                    true_negatives.append(contact_analysis)

    total = len(validated_contacts) + len(rejected_contacts)

    print("="*80)
    print("VALIDATION ACCURACY ANALYSIS")
    print("="*80)
    print(f"\nTotal Contacts: {total}")
    print(f"Validated (is_valid=True): {len(validated_contacts)} ({len(validated_contacts)/total*100:.1f}%)")
    print(f"Rejected (is_valid=False): {len(rejected_contacts)} ({len(rejected_contacts)/total*100:.1f}%)")

    print(f"\n{'='*80}")
    print("CONFUSION MATRIX")
    print("="*80)
    print(f"\nTrue Positives (Validated + Good):     {len(true_positives):4d} ({len(true_positives)/total*100:5.1f}%)")
    print(f"False Positives (Validated + Bad):     {len(false_positives):4d} ({len(false_positives)/total*100:5.1f}%)")
    print(f"False Negatives (Rejected + Good):     {len(false_negatives):4d} ({len(false_negatives)/total*100:5.1f}%)")
    print(f"True Negatives (Rejected + Bad):       {len(true_negatives):4d} ({len(true_negatives)/total*100:5.1f}%)")

    if len(true_positives) + len(false_positives) > 0:
        precision = len(true_positives) / (len(true_positives) + len(false_positives))
    else:
        precision = 0

    if len(true_positives) + len(false_negatives) > 0:
        recall = len(true_positives) / (len(true_positives) + len(false_negatives))
    else:
        recall = 0

    if precision + recall > 0:
        f1 = 2 * (precision * recall) / (precision + recall)
    else:
        f1 = 0

    accuracy = (len(true_positives) + len(true_negatives)) / total

    print(f"\n{'='*80}")
    print("VALIDATION METRICS")
    print("="*80)
    print(f"Precision: {precision*100:.1f}% (of validated contacts, how many are actually good?)")
    print(f"Recall:    {recall*100:.1f}% (of good contacts, how many did we validate?)")
    print(f"F1 Score:  {f1*100:.1f}%")
    print(f"Accuracy:  {accuracy*100:.1f}% (overall correctness)")

    print(f"\n{'='*80}")
    print("FALSE POSITIVES - Validated But Actually Bad")
    print("="*80)
    print(f"\nCount: {len(false_positives)}")
    print(f"\nTop 10 False Positives (sorted by confidence):")
    for fp in sorted(false_positives, key=lambda x: x['confidence'], reverse=True)[:10]:
        print(f"\n  Company: {fp['company']}")
        print(f"  Name: {fp['name']}")
        print(f"  Email: {fp['email']}")
        print(f"  Phone: {fp['phone']}")
        print(f"  Title: {fp['title']}")
        print(f"  Confidence: {fp['confidence']}")
        print(f"  Actual Score: {fp['actual_score']}")
        print(f"  Issues: {', '.join(fp['issues'][:3])}")

    print(f"\n{'='*80}")
    print("FALSE NEGATIVES - Rejected But Actually Good")
    print("="*80)
    print(f"\nCount: {len(false_negatives)}")
    print(f"\nTop 10 False Negatives (sorted by actual score):")
    for fn in sorted(false_negatives, key=lambda x: x['actual_score'], reverse=True)[:10]:
        print(f"\n  Company: {fn['company']}")
        print(f"  Name: {fn['name']}")
        print(f"  Email: {fn['email']}")
        print(f"  Phone: {fn['phone']}")
        print(f"  Title: {fn['title']}")
        print(f"  Confidence: {fn['confidence']}")
        print(f"  Actual Score: {fn['actual_score']}")
        print(f"  Issues: {', '.join(fn['issues'][:3])}")

    print(f"\n{'='*80}")
    print("ACTUAL SCORE DISTRIBUTION")
    print("="*80)

    # Calculate score distribution for validated vs rejected
    validated_scores = [c['actual_score'] for c in validated_contacts]
    rejected_scores = [c['actual_score'] for c in rejected_contacts]

    print(f"\nValidated Contacts (is_valid=True):")
    print(f"  Mean Actual Score: {sum(validated_scores)/len(validated_scores):.1f}")
    print(f"  Min:  {min(validated_scores)}")
    print(f"  Max:  {max(validated_scores)}")
    print(f"  <0:   {sum(1 for s in validated_scores if s < 0):4d} ({sum(1 for s in validated_scores if s < 0)/len(validated_scores)*100:5.1f}%)")
    print(f"  0-40: {sum(1 for s in validated_scores if 0 <= s < 40):4d} ({sum(1 for s in validated_scores if 0 <= s < 40)/len(validated_scores)*100:5.1f}%)")
    print(f"  40-60: {sum(1 for s in validated_scores if 40 <= s < 60):4d} ({sum(1 for s in validated_scores if 40 <= s < 60)/len(validated_scores)*100:5.1f}%)")
    print(f"  60+:  {sum(1 for s in validated_scores if s >= 60):4d} ({sum(1 for s in validated_scores if s >= 60)/len(validated_scores)*100:5.1f}%)")

    print(f"\nRejected Contacts (is_valid=False):")
    print(f"  Mean Actual Score: {sum(rejected_scores)/len(rejected_scores):.1f}")
    print(f"  Min:  {min(rejected_scores)}")
    print(f"  Max:  {max(rejected_scores)}")
    print(f"  <0:   {sum(1 for s in rejected_scores if s < 0):4d} ({sum(1 for s in rejected_scores if s < 0)/len(rejected_scores)*100:5.1f}%)")
    print(f"  0-40: {sum(1 for s in rejected_scores if 0 <= s < 40):4d} ({sum(1 for s in rejected_scores if 0 <= s < 40)/len(rejected_scores)*100:5.1f}%)")
    print(f"  40-60: {sum(1 for s in rejected_scores if 40 <= s < 60):4d} ({sum(1 for s in rejected_scores if 40 <= s < 60)/len(rejected_scores)*100:5.1f}%)")
    print(f"  60+:  {sum(1 for s in rejected_scores if s >= 60):4d} ({sum(1 for s in rejected_scores if s >= 60)/len(rejected_scores)*100:5.1f}%)")

    print(f"\n{'='*80}")
    print("KEY INSIGHTS")
    print("="*80)

    if len(false_positives) > len(true_positives):
        print("\n⚠️  CRITICAL: More false positives than true positives!")
        print("   Validation is accepting too many bad contacts.")

    if precision < 0.5:
        print(f"\n⚠️  CRITICAL: Precision is only {precision*100:.1f}%")
        print("   Most validated contacts are actually bad quality.")

    if recall < 0.7:
        print(f"\n⚠️  WARNING: Recall is only {recall*100:.1f}%")
        print("   We're rejecting too many good contacts.")

    validated_avg = sum(validated_scores)/len(validated_scores)
    rejected_avg = sum(rejected_scores)/len(rejected_scores)

    if validated_avg < 60:
        print(f"\n⚠️  CRITICAL: Average validated score is {validated_avg:.1f}")
        print("   Validated contacts are below quality threshold.")

    if rejected_avg > 40:
        print(f"\n⚠️  WARNING: Average rejected score is {rejected_avg:.1f}")
        print("   Some rejected contacts might be salvageable.")

    print(f"\n{'='*80}")
    print("RECOMMENDATIONS")
    print("="*80)

    if precision < 0.5:
        print("\n1. RAISE VALIDATION THRESHOLD")
        print("   Current threshold allows too many bad contacts through.")
        print("   Recommend: threshold = 70 (from current ~50)")

    if len(false_positives) > 0:
        print("\n2. ADD NEGATIVE SCORING FOR RED FLAGS")
        print("   Company name as contact: -50 points")
        print("   Generic email domain: -20 points")
        print("   No person name: -40 points")

    if validated_avg < 60:
        print("\n3. REQUIRE MINIMUM QUALITY CRITERIA")
        print("   Must have: Real person name (not company)")
        print("   Must have: Email OR phone")
        print("   Bonus: Domain-matched email")

    print("\n")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python validation_accuracy_check.py <results.json>")
        sys.exit(1)

    analyze_validation_accuracy(sys.argv[1])
